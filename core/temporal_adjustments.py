# core/temporal_adjustments.py
"""
Módulo de Ajustes Temporais (Seasonality & Events) - Esfera 1
Determinístico e Explicável.

Responsável por calcular fatores multiplicativos para o forecast base:
Forecast Final = Forecast Base * DOW * Month * Event * Bridge * Payday
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Optional, Any
import math
from core.models import Event, BridgeRule, PaydayRule, InventoryState, DowFactor, MonthFactor, TemporalBreakdown

# Removed local TemporalBreakdown

def compute_dow_factor(item_id: str, target_date: date, state: InventoryState) -> float:
    """Calcula fator de Dia da Semana (DOW) baseado em dados históricos."""
    # MVP: Retorna 1.0 se não houver fatores pré-calculados.
    # Em produção, usaria state.dow_factors cache.
    weekday = target_date.weekday()
    if item_id in state.dow_factors and weekday in state.dow_factors[item_id]:
         return state.dow_factors[item_id][weekday]
    return 1.0

def compute_month_factor(item_id: str, target_date: date, state: InventoryState) -> float:
    """Calcula fator de Mês (Sazonaliade Anual)."""
    month = target_date.month
    if item_id in state.month_factors and month in state.month_factors[item_id]:
        return state.month_factors[item_id][month]
    return 1.0

def get_event_on_date(target_date: date, events: List[Event]) -> Optional[Event]:
    """Retorna o evento agendado para a data, se houver."""
    for e in events:
        if e.date == target_date:
            return e
    return None

def compute_bridge_factor(target_date: date, events: List[Event], rules: List[BridgeRule]) -> float:
    """
    Se há feriado/evento próximo, aplica regra de Bridge Day.
    Prompt: "Se há evento no dia seguinte (next) e bridge_rule.enabled".
    
    Implementação:
    - Verifica dia seguinte (D+1). Se houve evento e regra ativa, aplica.
    - Opcional: Verificar dia anterior (D-1).    
    """
    if not rules:
        return 1.0
        
    rule = next((r for r in rules if r.enabled), None)
    if not rule:
        return 1.0

    # Look forward (Monday before Tuesday Holiday)
    next_day = target_date + timedelta(days=1)
    event_next = get_event_on_date(next_day, events)
    
    if event_next:
        # Híbrido discutido: demand_bridge = 0.3 * normal + 0.7 * event
        # Como estamos retornando um FATOR multiplicativo sobre o Normal:
        # bridge_demand = 0.3*Base + 0.7*(Base * EventFactor)
        # bridge_demand = Base * (0.3 + 0.7 * EventFactor)
        # FactorBridge = 0.3 + 0.7 * EventFactor
        
        # Mas o prompt menciona também: bridge_multiplier default 0.5.
        # "bridge_factor = 1 + (event.factor - 1) * bridge_multiplier" -> interpolação simples.
        # Se event.factor = 1.2 (20% up), bridge_multiplier=0.5 -> 1 + 0.2*0.5 = 1.1 (10% up).
        
        # Vamos usar a lógica de interpolação pelo multiplier da regra
        # Se o evento reduz demanda (0.1), bridge_multiplier 0.5 -> 0.55.
        
        impact = event_next.factor - 1.0
        return 1.0 + (impact * rule.multiplier)

    # Look backward (Friday after Thursday Holiday)
    # Se a regra lookback permitir
    if rule.lookback_days >= 1:
        prev_day = target_date - timedelta(days=1)
        event_prev = get_event_on_date(prev_day, events)
        if event_prev:
            impact = event_prev.factor - 1.0
            return 1.0 + (impact * rule.multiplier)
            
    return 1.0

def _is_business_day(d: date) -> bool:
    return d.weekday() < 5 # 0-4 = Mon-Fri

def _get_fifth_business_day(year: int, month: int) -> date:
    d = date(year, month, 1)
    business_days = 0
    while business_days < 5:
        if _is_business_day(d):
            business_days += 1
        if business_days == 5:
            return d
        d += timedelta(days=1)
    return d # Should not reach

def _get_last_business_day(year: int, month: int) -> date:
    # Start from first day of next month - 1 day
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
        
    while not _is_business_day(d):
        d -= timedelta(days=1)
    return d

def compute_payday_factor(target_date: date, rules: List[PaydayRule]) -> float:
    """Aplica regra de Payday se coincidir com a data."""
    if not rules:
        return 1.0
    
    # Aplica a primeira regra ativa encontrada (ou maior impacto?)
    # Assumindo uma regra ativa por vez para simplificar
    rule = next((r for r in rules if r.enabled), None)
    if not rule:
        return 1.0
        
    is_payday = False
    
    if rule.rule_type == 'fixed_day':
        if rule.day_of_month and target_date.day == rule.day_of_month:
            is_payday = True
            
    elif rule.rule_type == 'fifth_business_day':
        fifth = _get_fifth_business_day(target_date.year, target_date.month)
        if target_date == fifth:
            is_payday = True
            
    elif rule.rule_type == 'last_business_day':
        last = _get_last_business_day(target_date.year, target_date.month)
        if target_date == last:
            is_payday = True
            
    return rule.multiplier if is_payday else 1.0

def apply_temporal_adjustments(
    item_id: str,
    target_date: date,
    forecast_base: float,
    state: InventoryState
) -> TemporalBreakdown:
    """Orquestrador principal de ajustes temporais."""
    
    # 1. DOW (Day of Week)
    dow = compute_dow_factor(item_id, target_date, state)
    
    # 2. Month
    month = compute_month_factor(item_id, target_date, state)
    
    # 3. Events
    event_obj = get_event_on_date(target_date, state.events)
    # Filtro de applicable_to poderia ser aqui, mas assumindo global por enquanto ou pré-filtrado
    event_factor = event_obj.factor if event_obj else 1.0
    
    # 4. Bridge
    bridge = compute_bridge_factor(target_date, state.events, state.bridge_rules)
    
    # 5. Payday
    payday = compute_payday_factor(target_date, state.payday_rules)
    
    # Combinação Multiplicativa
    # FIX [BUG-002]: O forecast base já é calculado usando WMA específico por Dia da Semana (core/forecast.py).
    # Reaplicar o fator DOW aqui geraria dupla contagem (inflação da demanda).
    # Mantemos 'dow' apenas para exibição/explicação, mas usamos 1.0 no cálculo final.
    relevant_dow_factor = 1.0
    
    total_factor = relevant_dow_factor * month * event_factor * bridge * payday
    
    # Clamp (Segurança) - 0.5x a 3.0x (configurável, mas hardcoded por enquanto conforme prompt)
    # prompt: clamp_max_multiplier = 3.0, clamp_min = 0.0 (mas 0.0 é perigoso, melhor 0.1)
    total_factor = max(0.1, min(total_factor, 3.0))
    
    final_value = forecast_base * total_factor
    
    # Explanations
    explanation_lines = []
    if abs(dow - 1.0) > 0.01: explanation_lines.append(f"DOW: {dow:.2f}x")
    if abs(month - 1.0) > 0.01: explanation_lines.append(f"Month: {month:.2f}x")
    if event_obj: explanation_lines.append(f"Event: {event_obj.name} ({event_factor:.2f}x)")
    if abs(bridge - 1.0) > 0.01: explanation_lines.append(f"Bridge Day ({bridge:.2f}x)")
    if abs(payday - 1.0) > 0.01: explanation_lines.append(f"Payday ({payday:.2f}x)")
    
    return TemporalBreakdown(
        item_id=item_id,
        base_forecast=forecast_base,
        forecast_final=final_value,
        total_factor=total_factor,
        components=[
            {"label": "DOW", "factor": dow},
            {"label": "Month", "factor": month},
            {"label": "Event", "factor": event_factor},
            {"label": "Bridge", "factor": bridge},
            {"label": "Payday", "factor": payday}
        ],
        explanation="; ".join(explanation_lines) if explanation_lines else "No major factors.",
        confidence="MEDIUM" # TODO: Implement logic based on n_samples
    )
