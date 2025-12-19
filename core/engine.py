# core/engine.py

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List
from datetime import datetime

from .models import (
    InventoryState,
    AnalysisContext,
    Alert,
    AlertSphere,
    AlertPersona,
    AlertPriority,
    ItemType,
    OperationMode,
    ReliabilityLevel,
)
from .forecast import get_item_demand_data
from .safety import calculate_safety_stock
from .ingredients import analyze_ingredients
from .production import analyze_production
from .stats import calculate_coefficient_of_variation, calculate_reliability_from_cv


def analyze_inventory(
    state: InventoryState,
    ctx: AnalysisContext,
    include_suppressed: bool = False,
) -> List[Alert]:

    alerts: List[Alert] = []

    alerts += _analyze_finished_products(state, ctx)
    alerts += analyze_ingredients(state, ctx)
    alerts += analyze_production(state, ctx)

    final: List[Alert] = []
    now = ctx.now

    for alert in alerts:
        suppressed_until = state.suppressed_alerts.get(alert.id)
        is_suppressed = suppressed_until is not None and (
            suppressed_until is None or suppressed_until > now
        )

        if is_suppressed:
            alert.is_suppressed = True
            if include_suppressed:
                final.append(alert)
        else:
            alert.is_suppressed = False
            final.append(alert)

    return final


def _analyze_finished_products(
    state: InventoryState,
    ctx: AnalysisContext,
) -> List[Alert]:

    alerts: List[Alert] = []
    stock_map = defaultdict(float)
    now = ctx.now

    for sl in state.stock_levels:
        stock_map[sl.item_id] += sl.quantity

    for item in state.items:
        if item.item_type != ItemType.FINISHED:
            continue

        current_stock = stock_map.get(item.id, 0.0)

        stats = get_item_demand_data(state, item.id, ctx)
        forecast = stats.wma_forecast
        avg = stats.avg_daily_demand
        max_d = stats.max_daily_demand

        # --- MELHORIA: Reliability baseada em CV e volume de dados ---
        cv = calculate_coefficient_of_variation(stats.raw_values)
        rel_score, rel_level = calculate_reliability_from_cv(cv, stats.n_samples)

        # Ajuste por última auditoria (mantém compatibilidade)
        if item.last_audit_date is None:
            rel_score = min(rel_score, 0.4)
            reliability = ReliabilityLevel.LOW
        else:
            days_since_audit = (now.date() - item.last_audit_date).days
            if days_since_audit > 15:
                rel_score = min(rel_score, 0.5)
                reliability = ReliabilityLevel.LOW
            elif days_since_audit > 3:
                reliability = ReliabilityLevel(rel_level)
            else:
                reliability = ReliabilityLevel.HIGH if rel_score >= 0.8 else ReliabilityLevel(rel_level)

        # --- Cálculo de dias de cobertura ---
        days_of_coverage = current_stock / forecast if forecast > 0 else float('inf')

        if current_stock < 0:
            alerts.append(Alert(
                id=f"neg_stock_{item.id}",
                sphere=AlertSphere.DATA_QUALITY,
                persona=AlertPersona.MANAGEMENT,
                priority=AlertPriority.URGENT,
                title=f"Estoque negativo – {item.name}",
                message=f"O estoque está negativo ({current_stock:.0f}). Ajuste o inventário.",
                created_at=now,
                reliability=reliability,
                reliability_score=rel_score,
                data_error=True,
                data={
                    "item_id": item.id,
                    "current_stock": current_stock,
                    "avg_daily_demand": round(avg, 2),
                },
            ))
            continue

        if forecast == 0 and current_stock > 0:
            alerts.append(Alert(
                id=f"stagnant_{item.id}",
                sphere=AlertSphere.PRODUCT,
                persona=AlertPersona.MANAGEMENT,
                priority=AlertPriority.INFO,
                title=f"Produto sem giro – {item.name}",
                message=f"Há estoque ({current_stock:.0f} {item.unit}), mas nenhuma demanda prevista.",
                created_at=now,
                reliability=reliability,
                reliability_score=rel_score,
                data={
                    "item_id": item.id,
                    "current_stock": current_stock,
                    "n_samples": stats.n_samples,
                },
            ))
            continue

        if forecast <= 0:
            continue

        avg_lt = item.lead_time_days
        max_lt = avg_lt * ctx.supplier_variability_finished
        safety = calculate_safety_stock(max_d, avg, max_lt, avg_lt, item.item_class)

        reorder_point = forecast * avg_lt + safety
        coverage_target = avg_lt + ctx.coverage_days_target_A
        target_stock = forecast * coverage_target + safety
        to_buy = max(0.0, target_stock - current_stock)

        op_mode = (
            OperationMode.DEMAND_ONLY
            if ctx.ignore_stock_balance
            else item.operation_mode
        )

        # --- MELHORIA: Mensagens com contexto de dias de cobertura ---
        if op_mode == OperationMode.DEMAND_ONLY:
            message = (
                f"Estoque cobre {days_of_coverage:.1f} dias (meta: {coverage_target:.0f} dias). "
                f"Sugestão: comprar {to_buy:.0f} {item.unit}."
            )
            alerts.append(Alert(
                id=f"base_zero_{item.id}",
                sphere=AlertSphere.PRODUCT,
                persona=AlertPersona.PURCHASING,
                priority=AlertPriority.PLAN,
                title=f"Planejar compra (Base Zero) – {item.name}",
                message=message,
                created_at=now,
                reliability=reliability,
                reliability_score=rel_score,
                data={
                    "item_id": item.id,
                    "to_buy": round(to_buy, 2),
                    "target_stock": round(target_stock, 2),
                    "days_of_coverage": round(days_of_coverage, 1),
                    "coverage_target_days": round(coverage_target, 0),
                    "avg_daily_demand": round(forecast, 2),
                    "safety_stock": round(safety, 2),
                    "lead_time_days": avg_lt,
                },
            ))
            continue

        if current_stock < reorder_point:
            priority = AlertPriority.URGENT
            title = f"Comprar agora – {item.name}"
            urgency_reason = "abaixo do ponto de ressuprimento"
        elif current_stock < target_stock:
            priority = AlertPriority.PLAN
            title = f"Planejar compra – {item.name}"
            urgency_reason = "abaixo da meta de cobertura"
        else:
            continue

        message = (
            f"Estoque cobre {days_of_coverage:.1f} dias ({urgency_reason}). "
            f"Comprar {to_buy:.0f} {item.unit} para atingir {coverage_target:.0f} dias."
        )

        alerts.append(Alert(
            id=f"buy_{item.id}",
            sphere=AlertSphere.PRODUCT,
            persona=AlertPersona.PURCHASING,
            priority=priority,
            title=title,
            message=message,
            created_at=now,
            reliability=reliability,
            reliability_score=rel_score,
            data={
                "item_id": item.id,
                "to_buy": round(to_buy, 2),
                "current_stock": current_stock,
                "target_stock": round(target_stock, 2),
                "reorder_point": round(reorder_point, 2),
                "days_of_coverage": round(days_of_coverage, 1),
                "coverage_target_days": round(coverage_target, 0),
                "avg_daily_demand": round(forecast, 2),
                "safety_stock": round(safety, 2),
                "lead_time_days": avg_lt,
            },
        ))

    return alerts
