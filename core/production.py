# core/production.py
# SPHERES 1–3 FROZEN: behavior consolidated and must not be altered without explicit review.

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import (
    InventoryState,
    AnalysisContext,
    Alert,
    AlertPersona,
    AlertPriority,
    AlertSphere,
    ItemType,
    ReliabilityLevel,
)
from .demand_cache import DemandCache


def analyze_production(
    state: InventoryState,
    ctx: AnalysisContext,
    cache: DemandCache,
) -> List[Alert]:
    """
    Esfera 3: Análise de produção (semi-acabados).
    
    Dois modos:
    - REATIVO: baseado nas vendas do dia (demanda real)
    - PLANEJADO: baseado no forecast (demanda projetada)
    
    REGRAS CANÔNICAS:
    - Produção tem precedência sobre compra de ingredientes
    - Se há alerta REATIVO para um item, NÃO gerar também alerta PLANEJADO
    - Evitar duplicação de alertas para o mesmo semi-acabado
    """
    alerts: List[Alert] = []

    # -------------------------------
    # Produção REATIVA (vendas do dia)
    # WARNING [INFRA-001]: Considera TODAS as vendas do dia (00:00-23:59).
    # Se rodar no meio do dia, pode sugerir produção já realizada se o estoque não tiver sido baixado.
    # Idealmente, comparar com 'Last Audit' ou 'Updated At' do estoque, mas complexo para MVP.
    # Mantido comportamento: Required Today - Current Stock.
    # -------------------------------
    dish_today = defaultdict(float)
    for sale in state.today_sales:
        dish_today[sale.dish_id] += sale.quantity

    reactive_alerts, reactive_item_ids = _analyze_reactive_production(state, ctx, cache, dish_today)
    alerts += reactive_alerts

    # -------------------------------
    # Produção PLANEJADA (forecast)
    # Pula itens que já têm alerta reativo
    # -------------------------------
    alerts += _analyze_planned_production(state, ctx, cache, reactive_item_ids)

    return alerts


def _analyze_reactive_production(
    state: InventoryState,
    ctx: AnalysisContext,
    cache: DemandCache,
    dish_demand_today: Dict[str, float],
) -> tuple[List[Alert], set[str]]:
    """
    Produção reativa: baseada nas vendas reais do dia.
    
    Retorna:
    - Lista de alertas
    - Set de item_ids que receberam alerta (para evitar duplicação)
    """
    alerts = []
    alerted_items: set[str] = set()

    semi_demand = _explode_to_semi(state, cache, dish_demand_today)

    for semi_id, required in semi_demand.items():
        current = cache.get_stock(semi_id)
        if current >= required:
            continue

        # O(1) lookup ao invés de next() O(n)
        item = cache.get_item(semi_id)
        if not item:
            continue

        to_produce = round(required - current, 2)
        shortfall = round(required - current, 2)

        message = (
            f"Demanda do dia: {required:.2f} {item.unit}, estoque: {current:.2f}. "
            f"Produzir {to_produce} {item.unit} imediatamente."
        )

        alerts.append(Alert(
            id=f"prod_reactive_{semi_id}",
            sphere=AlertSphere.PRODUCTION,
            persona=AlertPersona.KITCHEN,
            priority=AlertPriority.URGENT,
            title=f"Produzir agora – {item.name}",
            message=message,
            created_at=ctx.now,
            reliability=ReliabilityLevel.HIGH,
            reliability_score=0.95,
            data={
                "item_id": semi_id,
                "to_produce": to_produce,
                "current_stock": round(current, 2),
                "today_demand": round(required, 2),
                "shortfall": shortfall,
            },
        ))
        alerted_items.add(semi_id)

    return alerts, alerted_items


def _analyze_planned_production(
    state: InventoryState,
    ctx: AnalysisContext,
    cache: DemandCache,
    skip_items: set[str] = None,
) -> List[Alert]:
    """
    Produção planejada: baseada no forecast.
    
    Args:
        skip_items: IDs de itens que já têm alerta reativo (não duplicar)
    """
    alerts = []
    skip_items = skip_items or set()

    for item in state.items:
        if item.item_type != ItemType.SEMI_FINISHED:
            continue
        
        # FIX [BUG-003]: Removida supressão de Planejado quando existe Reativo.
        # "Cegueira de Planejamento": Resolver uma ruptura HOJE não elimina a necessidade de mise-en-place para AMANHÃ.
        # Os alertas devem coexistir com prioridades diferentes.
        # if item.id in skip_items:
        #     continue

        # Usa cache
        stats = cache.get_demand_stats(item.id)
        forecast = stats.wma_forecast
        if forecast <= 0:
            continue

        target_stock = forecast * ctx.coverage_days_target_B
        current = cache.get_stock(item.id)

        if current >= target_stock:
            continue

        to_produce = round(target_stock - current, 2)
        days_of_coverage = current / forecast if forecast > 0 else 0

        message = (
            f"Estoque cobre {days_of_coverage:.1f} dias (meta: {ctx.coverage_days_target_B:.0f}). "
            f"Produzir {to_produce} {item.unit} para o próximo ciclo."
        )

        alerts.append(Alert(
            id=f"prod_plan_{item.id}",
            sphere=AlertSphere.PRODUCTION,
            persona=AlertPersona.KITCHEN,
            priority=AlertPriority.PLAN,
            title=f"Planejar produção – {item.name}",
            message=message,
            created_at=ctx.now,
            reliability=ReliabilityLevel.MEDIUM,
            reliability_score=0.7,
            data={
                "item_id": item.id,
                "to_produce": to_produce,
                "current_stock": round(current, 2),
                "target_stock": round(target_stock, 2),
                "days_of_coverage": round(days_of_coverage, 1),
                "avg_daily_demand": round(forecast, 2),
            },
        ))

    return alerts


def _explode_to_semi(
    state: InventoryState,
    cache: DemandCache,
    dish_demand: Dict[str, float],
) -> Dict[str, float]:
    """Explode demanda de pratos para semi-acabados."""
    recipes = defaultdict(list)
    for r in state.recipes:
        recipes[r.parent_item_id].append(r)

    semi_demand = defaultdict(float)
    visited = set()

    def recurse(pid: str, qty: float) -> None:
        if pid in visited:
            return
        visited.add(pid)

        for r in recipes.get(pid, []):
            child = r.child_item_id
            needed = qty * r.quantity
            # O(1) lookup
            item = cache.get_item(child)
            if not item:
                continue
            if item.item_type == ItemType.SEMI_FINISHED:
                semi_demand[child] += needed
                recurse(child, needed)

    for d, q in dish_demand.items():
        visited.clear()  # Reset per dish
        recurse(d, q)

    return semi_demand
