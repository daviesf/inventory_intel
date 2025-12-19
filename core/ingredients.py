# core/ingredients.py

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta, date, datetime
from typing import Dict, List, Set, Optional

from .models import (
    InventoryState,
    AnalysisContext,
    Alert,
    AlertSphere,
    AlertPersona,
    AlertPriority,
    ItemType,
    ItemClass,
    ReliabilityLevel,
    Item,
    StockLevel,
)
from .forecast import get_item_demand_data
from .safety import calculate_safety_stock
from .stats import calculate_coefficient_of_variation, calculate_reliability_from_cv


@dataclass
class IngredientDemandStats:
    avg_daily_demand: float
    max_daily_demand: float
    drivers: Dict[str, float]  # parent_item_id -> avg demand


def analyze_ingredients(state: InventoryState, ctx: AnalysisContext) -> List[Alert]:
    alerts: List[Alert] = []

    parent_ids = {r.parent_item_id for r in state.recipes}
    if not parent_ids:
        return alerts

    parent_demand: Dict[str, IngredientDemandStats] = {}

    for pid in parent_ids:
        stats = get_item_demand_data(state, pid, ctx)
        if stats.wma_forecast <= 0 and stats.max_daily_demand <= 0:
            continue

        parent_demand[pid] = IngredientDemandStats(
            avg_daily_demand=stats.wma_forecast,
            max_daily_demand=stats.max_daily_demand,
            drivers={pid: stats.wma_forecast},
        )

    ingredient_requirements = _explode_requirements(state, parent_demand)

    stock_map: Dict[str, List[StockLevel]] = defaultdict(list)
    for sl in state.stock_levels:
        stock_map[sl.item_id].append(sl)

    ingredients = [i for i in state.items if i.item_type == ItemType.INGREDIENT]

    for ing in ingredients:
        req = ingredient_requirements.get(ing.id)
        avg_demand = req.avg_daily_demand if req else 0.0
        max_demand = req.max_daily_demand if req else 0.0
        drivers = req.drivers if req else {}

        stock_levels = stock_map.get(ing.id, [])
        effective_stock, risk_qty = _calculate_effective_stock(
            stock_levels, ctx, int(ctx.perishable_risk_threshold_days)
        )

        if avg_demand == 0 and effective_stock == 0:
            continue

        avg_lt = ing.lead_time_days
        max_lt = avg_lt * ctx.supplier_variability_ingredient

        safety = calculate_safety_stock(
            max_demand, avg_demand, max_lt, avg_lt, ing.item_class
        )

        reorder_point = avg_demand * avg_lt + safety

        coverage_days = (
            ctx.coverage_days_target_A if ing.item_class == ItemClass.A
            else ctx.coverage_days_target_B if ing.item_class == ItemClass.B
            else ctx.coverage_days_target_C
        )

        target_stock = avg_demand * (avg_lt + coverage_days) + safety

        # --- MELHORIA: Reliability baseada em CV dos drivers ---
        # Coletamos os raw_values dos drivers para calcular volatilidade agregada
        all_driver_values = []
        for driver_id in drivers.keys():
            driver_stats = get_item_demand_data(state, driver_id, ctx)
            all_driver_values.extend(driver_stats.raw_values)

        if all_driver_values:
            cv = calculate_coefficient_of_variation(all_driver_values)
            rel_score, rel_level = calculate_reliability_from_cv(cv, len(all_driver_values))
            reliability = ReliabilityLevel(rel_level)
        else:
            reliability = ReliabilityLevel.LOW
            rel_score = 0.4

        # Ajuste por número de drivers (mais drivers = mais confiável)
        n_drivers = len(drivers)
        if n_drivers >= 3:
            rel_score = min(1.0, rel_score + 0.1)

        # --- MELHORIA: Calcular pratos afetados (estimated_impact) ---
        # Precisa seguir a cadeia: ingrediente -> semi -> prato
        affected_dishes = _find_affected_dishes(state, ing.id)
        estimated_impact = len(affected_dishes) if affected_dishes else None

        alert = _evaluate_ingredient_status(
            ctx, ing, effective_stock, risk_qty, reorder_point,
            target_stock, safety, avg_demand, avg_lt, coverage_days,
            reliability, rel_score, drivers, estimated_impact
        )

        if alert:
            alerts.append(alert)

    return alerts


def _find_affected_dishes(state: InventoryState, ingredient_id: str) -> Set[str]:
    """
    Encontra todos os pratos (dishes) que podem ser afetados pela falta de um ingrediente.
    Segue a cadeia: ingrediente -> semi-acabado -> prato.
    """
    # Mapeia child -> list of parents
    reverse_recipes = defaultdict(set)
    for r in state.recipes:
        reverse_recipes[r.child_item_id].add(r.parent_item_id)

    # Identifica tipos de itens
    item_type_map = {i.id: i.item_type for i in state.items}

    affected = set()
    visited = set()

    def trace_up(item_id: str):
        if item_id in visited:
            return
        visited.add(item_id)

        for parent_id in reverse_recipes.get(item_id, []):
            parent_type = item_type_map.get(parent_id)

            # Se é um prato (dish_*), adiciona ao resultado
            if parent_id.startswith("dish_"):
                affected.add(parent_id)
            # Se é semi-acabado, continua subindo
            elif parent_type == ItemType.SEMI_FINISHED:
                trace_up(parent_id)
            # Se é finished mas não é dish, trata como prato também
            elif parent_type == ItemType.FINISHED:
                affected.add(parent_id)

    trace_up(ingredient_id)
    return affected


def _explode_requirements(
    state: InventoryState,
    parent_plan: Dict[str, IngredientDemandStats],
) -> Dict[str, IngredientDemandStats]:

    recipes_map = defaultdict(list)
    for r in state.recipes:
        recipes_map[r.parent_item_id].append(r)

    item_type_map = {i.id: i.item_type for i in state.items}

    result: Dict[str, IngredientDemandStats] = defaultdict(
        lambda: IngredientDemandStats(0.0, 0.0, defaultdict(float))
    )

    def propagate(item_id: str, avg_qty: float, max_qty: float, visited: Set[str]):
        if item_id in visited:
            return

        visited = visited | {item_id}

        for r in recipes_map.get(item_id, []):
            child = r.child_item_id
            req_avg = avg_qty * r.quantity
            req_max = max_qty * r.quantity

            if item_type_map.get(child) == ItemType.INGREDIENT:
                stats = result[child]
                stats.avg_daily_demand += req_avg
                stats.max_daily_demand += req_max
                stats.drivers[item_id] += req_avg
            elif item_type_map.get(child) == ItemType.SEMI_FINISHED:
                propagate(child, req_avg, req_max, visited)

    for pid, stats in parent_plan.items():
        propagate(pid, stats.avg_daily_demand, stats.max_daily_demand, set())

    return result


def _calculate_effective_stock(
    stock_levels: List[StockLevel],
    ctx: AnalysisContext,
    days_threshold: int,
) -> tuple[float, float]:

    effective = 0.0
    risk = 0.0
    cutoff = ctx.now.date() + timedelta(days=days_threshold)

    for sl in stock_levels:
        qty = float(sl.quantity)
        if sl.expires_at is None:
            effective += qty
            continue

        exp = sl.expires_at.date() if isinstance(sl.expires_at, datetime) else sl.expires_at
        if exp <= cutoff:
            risk += qty
        else:
            effective += qty

    return effective, risk


def _evaluate_ingredient_status(
    ctx: AnalysisContext,
    item: Item,
    effective_stock: float,
    risk_qty: float,
    reorder_point: float,
    target_stock: float,
    safety_stock: float,
    avg_demand: float,
    lead_time_days: float,
    coverage_days: float,
    reliability: ReliabilityLevel,
    rel_score: float,
    drivers: Dict[str, float],
    estimated_impact: Optional[int],
) -> Optional[Alert]:

    now = ctx.now

    # Calcular dias de cobertura
    days_of_coverage = effective_stock / avg_demand if avg_demand > 0 else float('inf')
    coverage_target = lead_time_days + coverage_days

    if avg_demand == 0 and effective_stock > 0:
        return Alert(
            id=f"ingredient_stagnant_{item.id}",
            sphere=AlertSphere.INGREDIENT,
            persona=AlertPersona.MANAGEMENT,
            priority=AlertPriority.INFO,
            title=f"Ingrediente sem giro – {item.name}",
            message=f"Há estoque ({effective_stock:.2f} {item.unit}), mas nenhuma demanda prevista.",
            created_at=now,
            reliability=reliability,
            reliability_score=rel_score,
            data={
                "item_id": item.id,
                "drivers": drivers,
                "current_stock": effective_stock,
            },
        )

    if avg_demand == 0:
        return None

    to_buy = max(0.0, target_stock - effective_stock)

    if effective_stock < safety_stock:
        priority = AlertPriority.URGENT
        title = f"Crítico – {item.name}"
        urgency_reason = "abaixo do estoque de segurança"
    elif effective_stock < reorder_point:
        priority = AlertPriority.URGENT
        title = f"Repor imediatamente – {item.name}"
        urgency_reason = "abaixo do ponto de ressuprimento"
    elif effective_stock < target_stock:
        priority = AlertPriority.PLAN
        title = f"Planejar compra – {item.name}"
        urgency_reason = "abaixo da meta de cobertura"
    else:
        return None

    # Mensagem melhorada com contexto
    message = (
        f"Estoque cobre {days_of_coverage:.1f} dias ({urgency_reason}). "
        f"Comprar {to_buy:.2f} {item.unit} para atingir {coverage_target:.0f} dias."
    )

    return Alert(
        id=f"ingredient_{item.id}",
        sphere=AlertSphere.INGREDIENT,
        persona=AlertPersona.PURCHASING,
        priority=priority,
        title=title,
        message=message,
        created_at=now,
        reliability=reliability,
        reliability_score=rel_score,
        estimated_impact=estimated_impact,
        data={
            "item_id": item.id,
            "to_buy": round(to_buy, 2),
            "current_stock": round(effective_stock, 2),
            "risk_qty": round(risk_qty, 2),
            "days_of_coverage": round(days_of_coverage, 1),
            "coverage_target_days": round(coverage_target, 0),
            "avg_daily_demand": round(avg_demand, 2),
            "safety_stock": round(safety_stock, 2),
            "lead_time_days": lead_time_days,
            "drivers": drivers,
        },
    )
