# core/engine.py
# SPHERES 1–3 FROZEN: behavior consolidated and must not be altered without explicit review.

from __future__ import annotations
from typing import Dict, List, Tuple, Optional
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
)
from .demand_cache import DemandCache
from .safety import calculate_safety_stock
from .ingredients import analyze_ingredients
from .production import analyze_production
from .reliability import calculate_item_reliability
from .perishability import analyze_perishability_sphere


def analyze_inventory(
    state: InventoryState,
    ctx: AnalysisContext,
    include_suppressed: bool = False,
) -> List[Alert]:
    """
    Função principal de análise de inventário.
    
    Orquestra a execução das 3 esferas:
    - Esfera 1: Produtos Prontos (FINISHED) → compra
    - Esfera 2: Ingredientes (INGREDIENT) → MRP/BOM
    - Esfera 3: Produção (SEMI_FINISHED) → pré-preparo
    
    Cria DemandCache uma vez e passa para todos os módulos,
    evitando recálculos O(n²).
    
    Alertas de perecibilidade são INFORMATIVOS nesta fase.
    Decisão de bloquear compra por risco futuro pertence à Esfera 4.
    """
    # Cache criado UMA VEZ - evita N+1 queries
    cache = DemandCache(state, ctx)
    
    alerts: List[Alert] = []
    
    # Análises de compra/reposição por esfera
    # NOTA: Perecibilidade NÃO bloqueia compras nesta fase (responsabilidade da Esfera 4)
    alerts += _analyze_finished_products(state, ctx, cache)
    alerts += analyze_ingredients(state, ctx, cache)
    alerts += analyze_production(state, ctx, cache)
    
    # ESFERA 4: Perecibilidade Inteligente
    # Roda DEPOIS para analisar contexto das sugestões de compra
    alerts += analyze_perishability_sphere(state, ctx, cache, alerts)

    final: List[Alert] = []
    now = ctx.now

    for alert in alerts:
        suppressed_until = state.suppressed_alerts.get(alert.id)
        is_suppressed = suppressed_until is not None and suppressed_until > now

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
    cache: DemandCache,
) -> List[Alert]:
    """
    Esfera 1: Análise de produtos prontos (FINISHED).
    
    Gera alertas de compra/reposição baseados em:
    - Ponto de reposição (reorder_point)
    - Estoque alvo (target_stock)
    - Estoque de segurança (safety_stock)
    
    REGRAS CANÔNICAS:
    - forecast = 0 + estoque > 0 → alerta 'sem giro'
    - forecast = 0 + estoque = 0 → silêncio válido
    - lead_time = 0 → comportamento agressivo (safety=0), MAS gera alertas
    - Perecibilidade NÃO bloqueia compra (Esfera 4)
    """
    alerts: List[Alert] = []
    now = ctx.now

    for item in state.items:
        if item.item_type != ItemType.FINISHED:
            continue

        # Usa cache ao invés de recalcular
        current_stock = cache.get_stock(item.id)
        stats = cache.get_demand_stats(item.id)
        
        forecast = stats.wma_forecast
        avg = stats.avg_daily_demand
        max_d = stats.max_daily_demand

        # Reliability via módulo consolidado
        rel_score, reliability = calculate_item_reliability(
            item=item,
            raw_values=stats.raw_values,
            n_samples=stats.n_samples,
            now=now,
        )

        # Cálculo de dias de cobertura
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

        # NOTA: lead_time = 0 resulta em safety = 0 e reorder_point = 0
        # Isso é intencional: comportamento mais agressivo, mas SEMPRE gera alertas
        # quando estoque < target (que será > 0 se coverage_days_target > 0)
        reorder_point = forecast * avg_lt + safety
        coverage_target = avg_lt + ctx.coverage_days_target_A
        target_stock = forecast * coverage_target + safety
        to_buy = max(0.0, target_stock - current_stock)

        op_mode = (
            OperationMode.DEMAND_ONLY
            if ctx.ignore_stock_balance
            else item.operation_mode
        )

        if op_mode == OperationMode.DEMAND_ONLY:
            message = (
                f"Estoque cobre {days_of_coverage:.1f} dias (meta: {coverage_target:.0f} dias). "
                f"Sugestão: comprar {to_buy:.0f} {item.unit}."
            )
            alert_data = {
                "item_id": item.id,
                "to_buy": round(to_buy, 2),
                "target_stock": round(target_stock, 2),
                "days_of_coverage": round(days_of_coverage, 1),
                "coverage_target_days": round(coverage_target, 0),
                "avg_daily_demand": round(forecast, 2),
                "safety_stock": round(safety, 2),
                "lead_time_days": avg_lt,
            }
            if stats.temporal_breakdown:
                alert_data["temporal_breakdown"] = stats.temporal_breakdown.components
                alert_data["temporal_explanation"] = stats.temporal_breakdown.explanation
                alert_data["temporal_confidence"] = stats.temporal_breakdown.confidence

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
                data=alert_data,
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

        alert_data = {
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
        }
        if stats.temporal_breakdown:
            alert_data["temporal_breakdown"] = stats.temporal_breakdown.components
            alert_data["temporal_explanation"] = stats.temporal_breakdown.explanation
            alert_data["temporal_confidence"] = stats.temporal_breakdown.confidence

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
            data=alert_data,
        ))

    return alerts
