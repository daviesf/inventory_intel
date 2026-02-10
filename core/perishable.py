# core/perishable.py
"""
Módulo de análise inteligente de perecibilidade.

Lógica principal:
1. Identifica itens com lotes próximos do vencimento
2. BLOQUEIA sugestões de compra se o estoque atual vai vencer antes de ser consumido
3. Prioriza uso de lotes antigos (FIFO)
4. Gera alertas de uso prioritário ou perda iminente
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple

from .models import (
    Alert,
    AlertSphere,
    AlertPersona,
    AlertPriority,
    ReliabilityLevel,
    InventoryState,
    AnalysisContext,
    StockLevel,
    Item,
)


@dataclass
class PerishabilityAnalysis:
    """Resultado da análise de perecibilidade para um item."""
    item_id: str
    item_name: str
    unit: str
    total_stock: float
    expiring_soon: float  # Quantidade que vence em <= threshold dias
    expired: float  # Quantidade já vencida
    days_until_first_expiry: Optional[int]
    daily_consumption: float
    can_consume_before_expiry: bool  # Se consegue consumir antes de vencer
    surplus_at_risk: float  # Quantidade que não será consumida a tempo
    batches: List[Dict]  # Lista de lotes ordenados por validade (FIFO)


def analyze_perishables(
    state: InventoryState,
    ctx: AnalysisContext,
    demand_rates: Dict[str, float],  # item_id -> avg daily demand
) -> Tuple[List[Alert], Dict[str, PerishabilityAnalysis]]:
    """
    Analisa todos os itens com data de validade e gera alertas inteligentes.
    
    Retorna:
        - Lista de alertas de perecibilidade
        - Dicionário com análises detalhadas por item (para modificar sugestões de compra)
    """
    alerts: List[Alert] = []
    analyses: Dict[str, PerishabilityAnalysis] = {}
    
    # Agrupar stock_levels por item
    stock_by_item: Dict[str, List[StockLevel]] = defaultdict(list)
    for sl in state.stock_levels:
        stock_by_item[sl.item_id].append(sl)
    
    today = ctx.now.date() if isinstance(ctx.now, datetime) else ctx.now
    threshold_days = int(ctx.perishable_risk_threshold_days)
    
    for item in state.items:
        levels = stock_by_item.get(item.id, [])
        if not levels:
            continue
        
        analysis = _analyze_item_perishability(
            item=item,
            levels=levels,
            today=today,
            threshold_days=threshold_days,
            daily_demand=demand_rates.get(item.id, 0.0),
        )
        
        if analysis.expiring_soon > 0 or analysis.expired > 0:
            analyses[item.id] = analysis
            
            # Gerar alertas baseados na análise
            item_alerts = _generate_perishability_alerts(analysis, item, ctx)
            alerts.extend(item_alerts)
    
    return alerts, analyses


def _analyze_item_perishability(
    item: Item,
    levels: List[StockLevel],
    today: date,
    threshold_days: int,
    daily_demand: float,
) -> PerishabilityAnalysis:
    """Analisa a situação de perecibilidade de um item específico."""
    
    # Separar e ordenar lotes por validade (FIFO)
    batches = []
    total_stock = 0.0
    expiring_soon = 0.0
    expired = 0.0
    first_expiry_days: Optional[int] = None
    
    for sl in sorted(levels, key=lambda x: x.expires_at or datetime.max):
        qty = float(sl.quantity)
        total_stock += qty
        
        if sl.expires_at is None:
            batches.append({
                "quantity": qty,
                "expires_at": None,
                "days_until_expiry": None,
                "status": "no_expiry",
            })
            continue
        
        exp_date = sl.expires_at.date() if isinstance(sl.expires_at, datetime) else sl.expires_at
        days_left = (exp_date - today).days
        
        batch_status = "ok"
        if days_left < 0:
            expired += qty
            batch_status = "expired"
        elif days_left <= threshold_days:
            expiring_soon += qty
            batch_status = "expiring_soon"
        elif days_left <= threshold_days * 2:
            batch_status = "warning"
        
        if first_expiry_days is None or (days_left >= 0 and days_left < first_expiry_days):
            first_expiry_days = days_left
        
        batches.append({
            "quantity": qty,
            "expires_at": exp_date.isoformat() if exp_date else None,
            "days_until_expiry": days_left,
            "status": batch_status,
        })
    
    # Calcular se consegue consumir antes de vencer
    can_consume = True
    surplus_at_risk = 0.0
    
    if daily_demand > 0 and first_expiry_days is not None and first_expiry_days >= 0:
        # Simular consumo FIFO
        remaining_qty = 0.0
        for batch in batches:
            if batch["status"] == "expired":
                surplus_at_risk += batch["quantity"]
                continue
            
            days = batch.get("days_until_expiry")
            if days is None:
                continue  # Sem validade, ok
            
            qty = batch["quantity"]
            consumption_possible = daily_demand * max(0, days)
            
            if remaining_qty + qty > consumption_possible:
                # Não vai consumir tudo a tempo
                batch_surplus = (remaining_qty + qty) - consumption_possible
                surplus_at_risk += min(batch_surplus, qty)
                can_consume = False
            
            remaining_qty += qty
    
    return PerishabilityAnalysis(
        item_id=item.id,
        item_name=item.name,
        unit=item.unit,
        total_stock=total_stock,
        expiring_soon=expiring_soon,
        expired=expired,
        days_until_first_expiry=first_expiry_days if first_expiry_days and first_expiry_days >= 0 else None,
        daily_consumption=daily_demand,
        can_consume_before_expiry=can_consume,
        surplus_at_risk=surplus_at_risk,
        batches=batches,
    )


def _generate_perishability_alerts(
    analysis: PerishabilityAnalysis,
    item: Item,
    ctx: AnalysisContext,
) -> List[Alert]:
    """Gera alertas baseados na análise de perecibilidade."""
    alerts = []
    
    # Alerta de produto VENCIDO
    if analysis.expired > 0:
        alerts.append(Alert(
            id=f"perishable_expired_{item.id}",
            sphere=AlertSphere.PERISHABLE,
            persona=AlertPersona.MANAGEMENT,
            priority=AlertPriority.URGENT,
            title=f"⚠️ {analysis.expired:.0f} {analysis.unit} de {item.name} VENCIDOS",
            message=f"Produto vencido em estoque. Descartar imediatamente para evitar risco sanitário.",
            created_at=ctx.now,
            reliability=ReliabilityLevel.HIGH,
            reliability_score=1.0,
            data={
                "item_id": item.id,
                "item_name": item.name,
                "quantity_expired": analysis.expired,
                "unit": analysis.unit,
                "action": "discard",
            }
        ))
    
    # Alerta de risco de perda (não vai consumir a tempo)
    if analysis.surplus_at_risk > 0 and not analysis.can_consume_before_expiry:
        priority = AlertPriority.URGENT if analysis.days_until_first_expiry and analysis.days_until_first_expiry <= 1 else AlertPriority.PLAN
        
        suggestion = _get_usage_suggestion(item, analysis)
        
        alerts.append(Alert(
            id=f"perishable_risk_{item.id}",
            sphere=AlertSphere.PERISHABLE,
            persona=AlertPersona.KITCHEN,
            priority=priority,
            title=f"🕐 {analysis.surplus_at_risk:.0f} {analysis.unit} de {item.name} em risco",
            message=f"Consumo atual ({analysis.daily_consumption:.1f}/dia) insuficiente. {suggestion}",
            created_at=ctx.now,
            reliability=ReliabilityLevel.HIGH,
            reliability_score=0.9,
            data={
                "item_id": item.id,
                "item_name": item.name,
                "quantity_at_risk": analysis.surplus_at_risk,
                "days_until_expiry": analysis.days_until_first_expiry,
                "daily_consumption": analysis.daily_consumption,
                "unit": analysis.unit,
                "suggestion": suggestion,
                "action": "prioritize_usage",
            }
        ))
    
    # Alerta informativo de vencimento próximo (sem risco de perda)
    elif analysis.expiring_soon > 0 and analysis.can_consume_before_expiry:
        alerts.append(Alert(
            id=f"perishable_info_{item.id}",
            sphere=AlertSphere.PERISHABLE,
            persona=AlertPersona.KITCHEN,
            priority=AlertPriority.INFO,
            title=f"📦 {analysis.expiring_soon:.0f} {analysis.unit} de {item.name} vence em breve",
            message=f"Vence em {analysis.days_until_first_expiry} dias. Consumo projetado OK.",
            created_at=ctx.now,
            reliability=ReliabilityLevel.HIGH,
            reliability_score=0.95,
            data={
                "item_id": item.id,
                "item_name": item.name,
                "quantity_expiring": analysis.expiring_soon,
                "days_until_expiry": analysis.days_until_first_expiry,
                "unit": analysis.unit,
                "action": "info",
            }
        ))
    
    return alerts


def _get_usage_suggestion(item: Item, analysis: PerishabilityAnalysis) -> str:
    """Gera sugestão de uso para evitar perda."""
    if analysis.days_until_first_expiry == 0:
        return "Usar TODO o estoque HOJE."
    elif analysis.days_until_first_expiry == 1:
        return "Priorizar uso amanhã. Considere promoção ou doação."
    else:
        needed_daily = analysis.surplus_at_risk / max(1, analysis.days_until_first_expiry)
        return f"Aumentar consumo para {analysis.daily_consumption + needed_daily:.1f}/dia ou realizar promoção."


def should_block_purchase(
    item_id: str,
    analyses: Dict[str, PerishabilityAnalysis],
) -> Tuple[bool, Optional[str]]:
    """
    Verifica se a compra de um item deve ser BLOQUEADA devido a perecibilidade.
    
    Retorna:
        - (True, motivo) se deve bloquear
        - (False, None) se pode comprar
    """
    if item_id not in analyses:
        return False, None
    
    analysis = analyses[item_id]
    
    # Bloquear se tem estoque vencido não descartado
    if analysis.expired > 0:
        return True, f"Descarte {analysis.expired:.0f} {analysis.unit} vencidos antes de comprar mais."
    
    # Bloquear se não vai consumir o estoque atual a tempo
    if not analysis.can_consume_before_expiry and analysis.surplus_at_risk > 0:
        return True, f"Consuma {analysis.surplus_at_risk:.0f} {analysis.unit} em risco antes de comprar mais."
    
    return False, None
