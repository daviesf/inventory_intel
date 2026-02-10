# core/ingredients.py
# SPHERES 1–3 FROZEN: behavior consolidated and must not be altered without explicit review.

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta, datetime
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
from .demand_cache import DemandCache
from .safety import calculate_safety_stock
from .reliability import calculate_ingredient_reliability

# Limite de profundidade para explosão de BOM (proteção contra loops)
MAX_BOM_DEPTH = 10


@dataclass
class IngredientDemandStats:
    avg_daily_demand: float
    max_daily_demand: float
    drivers: Dict[str, float]  # parent_item_id -> avg demand


def analyze_ingredients(
    state: InventoryState,
    ctx: AnalysisContext,
    cache: DemandCache,
) -> List[Alert]:
    """
    Esfera 2: Análise de ingredientes (MRP).
    
    Responsabilidades:
    - Explosão de BOM (receitas) para calcular demanda derivada
    - Cálculo de estoque efetivo vs risco por lote
    - Geração de alertas de compra para ingredientes
    
    REGRAS CANÔNICAS:
    - Semi-acabados NÃO são tratados como ingredientes (são produzidos, não comprados)
    - Ingrediente sem driver (sem prato associado) → alerta de gestão, não operacional
    - Proteção contra loops de BOM via limite de profundidade
    """
    alerts: List[Alert] = []

    parent_ids = {r.parent_item_id for r in state.recipes}
    if not parent_ids:
        return alerts

    parent_demand: Dict[str, IngredientDemandStats] = {}

    for pid in parent_ids:
        # Usa cache O(1)
        stats = cache.get_demand_stats(pid)
        if stats.wma_forecast <= 0 and stats.max_daily_demand <= 0:
            continue

        parent_demand[pid] = IngredientDemandStats(
            avg_daily_demand=stats.wma_forecast,
            max_daily_demand=stats.max_daily_demand,
            drivers={pid: stats.wma_forecast},
        )

    ingredient_requirements = _explode_requirements(state, cache, parent_demand)

    # Mapeia stock levels por item para calcular effective stock
    stock_levels_map: Dict[str, List[StockLevel]] = defaultdict(list)
    for sl in state.stock_levels:
        stock_levels_map[sl.item_id].append(sl)

    ingredients = [i for i in state.items if i.item_type == ItemType.INGREDIENT]

    for ing in ingredients:
        req = ingredient_requirements.get(ing.id)
        avg_demand = req.avg_daily_demand if req else 0.0
        max_demand = req.max_daily_demand if req else 0.0
        drivers = req.drivers if req else {}

        stock_levels = stock_levels_map.get(ing.id, [])
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

        # Reliability via módulo consolidado - usa valores dos drivers do cache
        all_driver_values = []
        for driver_id in drivers.keys():
            driver_stats = cache.get_demand_stats(driver_id)  # O(1)
            all_driver_values.extend(driver_stats.raw_values)

        rel_score, reliability = calculate_ingredient_reliability(
            all_driver_values=all_driver_values,
            n_drivers=len(drivers),
        )

        # Calcular pratos afetados (estimated_impact)
        affected_dishes = _find_affected_dishes(state, cache, ing.id)
        estimated_impact = len(affected_dishes) if affected_dishes else None

        alert = _evaluate_ingredient_status(
            ctx, ing, effective_stock, risk_qty, reorder_point,
            target_stock, safety, avg_demand, avg_lt, coverage_days,
            reliability, rel_score, drivers, estimated_impact
        )

        if alert:
            alerts.append(alert)

    return alerts


def _find_affected_dishes(
    state: InventoryState,
    cache: DemandCache,
    ingredient_id: str,
) -> Set[str]:
    """
    Encontra todos os pratos (dishes) que podem ser afetados pela falta de um ingrediente.
    Segue a cadeia: ingrediente -> semi-acabado -> prato.
    """
    # Mapeia child -> list of parents
    reverse_recipes = defaultdict(set)
    for r in state.recipes:
        reverse_recipes[r.child_item_id].add(r.parent_item_id)

    affected = set()
    visited = set()

    def trace_up(item_id: str) -> None:
        if item_id in visited:
            return
        visited.add(item_id)

        for parent_id in reverse_recipes.get(item_id, []):
            item = cache.get_item(parent_id)  # O(1)
            parent_type = item.item_type if item else None

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
    cache: DemandCache,
    parent_plan: Dict[str, IngredientDemandStats],
) -> Dict[str, IngredientDemandStats]:
    """
    Explode demanda de pratos/produtos em necessidades de ingredientes.
    
    REGRAS:
    - Semi-acabados são RECURSADOS (expandidos), não adicionados ao resultado
    - Apenas INGREDIENTS entram no resultado final
    - Proteção contra loops via limite de profundidade (MAX_BOM_DEPTH)
    
    A lógica de visited.add/discard permite que o mesmo ingrediente seja
    alcançado por múltiplos caminhos na BOM, acumulando demanda corretamente.
    """
    recipes_map = defaultdict(list)
    for r in state.recipes:
        recipes_map[r.parent_item_id].append(r)

    result: Dict[str, IngredientDemandStats] = defaultdict(
        lambda: IngredientDemandStats(0.0, 0.0, defaultdict(float))
    )

    def propagate(item_id: str, avg_qty: float, max_qty: float, visited: Set[str], depth: int = 0) -> None:
        # Proteção contra loops infinitos
        if depth > MAX_BOM_DEPTH:
            return
        if item_id in visited:
            return

        visited.add(item_id)

        for r in recipes_map.get(item_id, []):
            child = r.child_item_id
            req_avg = avg_qty * r.quantity
            req_max = max_qty * r.quantity

            item = cache.get_item(child)
            if not item:
                continue

            if item.item_type == ItemType.INGREDIENT:
                # INGREDIENTE: acumula no resultado (será comprado)
                stats = result[child]
                stats.avg_daily_demand += req_avg
                stats.max_daily_demand += req_max
                stats.drivers[item_id] += req_avg
            elif item.item_type == ItemType.SEMI_FINISHED:
                # SEMI-ACABADO: recursa para encontrar ingredientes base
                # NÃO adiciona ao resultado (será produzido, não comprado)
                propagate(child, req_avg, req_max, visited, depth + 1)

        # Remove após processar para permitir caminhos alternativos na BOM
        visited.discard(item_id)

    for pid, stats in parent_plan.items():
        propagate(pid, stats.avg_daily_demand, stats.max_daily_demand, set(), 0)

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
