# core/production.py

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .models import (
    Alert,
    AlertPersona,
    AlertPriority,
    AlertSphere,
    ItemType,
    ReliabilityLevel,
)
from .forecast import get_item_demand_data


def analyze_production(state, ctx) -> List[Alert]:
    alerts: List[Alert] = []

    # -------------------------------
    # Produção REATIVA (vendas do dia)
    # -------------------------------
    dish_today = defaultdict(float)
    for sale in state.today_sales:
        dish_today[sale.dish_id] += sale.quantity

    alerts += _analyze_reactive_production(state, ctx, dish_today)

    # -------------------------------
    # Produção PLANEJADA (forecast)
    # -------------------------------
    alerts += _analyze_planned_production(state, ctx)

    return alerts


def _analyze_reactive_production(state, ctx, dish_demand_today) -> List[Alert]:
    alerts = []

    semi_demand = _explode_to_semi(state, dish_demand_today)
    stock = defaultdict(float)

    for sl in state.stock_levels:
        stock[sl.item_id] += sl.quantity

    for semi_id, required in semi_demand.items():
        current = stock.get(semi_id, 0.0)
        if current >= required:
            continue

        item = next((i for i in state.items if i.id == semi_id), None)
        if not item:
            continue

        to_produce = round(required - current, 2)

        alerts.append(Alert(
            id=f"prod_reactive_{semi_id}",
            sphere=AlertSphere.PRODUCTION,
            persona=AlertPersona.KITCHEN,
            priority=AlertPriority.URGENT,
            title=f"Produzir agora – {item.name}",
            message=f"Produzir {to_produce} {item.unit} imediatamente.",
            created_at=ctx.now,
            reliability=ReliabilityLevel.HIGH,
            reliability_score=0.95,
            data={"to_produce": to_produce},
        ))

    return alerts


def _analyze_planned_production(state, ctx) -> List[Alert]:
    alerts = []
    stock = defaultdict(float)

    for sl in state.stock_levels:
        stock[sl.item_id] += sl.quantity

    for item in state.items:
        if item.item_type != ItemType.SEMI_FINISHED:
            continue

        stats = get_item_demand_data(state, item.id, ctx)
        forecast = stats.wma_forecast
        if forecast <= 0:
            continue

        target_stock = forecast * ctx.coverage_days_target_B
        current = stock.get(item.id, 0.0)

        if current >= target_stock:
            continue

        to_produce = round(target_stock - current, 2)

        alerts.append(Alert(
            id=f"prod_plan_{item.id}",
            sphere=AlertSphere.PRODUCTION,
            persona=AlertPersona.KITCHEN,
            priority=AlertPriority.PLAN,
            title=f"Planejar produção – {item.name}",
            message=f"Produzir {to_produce} {item.unit} para o próximo ciclo.",
            created_at=ctx.now,
            reliability=ReliabilityLevel.MEDIUM,
            reliability_score=0.7,
            data={"to_produce": to_produce},
        ))

    return alerts


def _explode_to_semi(state, dish_demand: Dict[str, float]) -> Dict[str, float]:
    recipes = defaultdict(list)
    for r in state.recipes:
        recipes[r.parent_item_id].append(r)

    semi_demand = defaultdict(float)
    visited = set()

    def recurse(pid, qty):
        if pid in visited:
            return
        visited.add(pid)

        for r in recipes.get(pid, []):
            child = r.child_item_id
            needed = qty * r.quantity
            item = next((i for i in state.items if i.id == child), None)
            if not item:
                continue
            if item.item_type == ItemType.SEMI_FINISHED:
                semi_demand[child] += needed
                recurse(child, needed)

    for d, q in dish_demand.items():
        recurse(d, q)

    return semi_demand
