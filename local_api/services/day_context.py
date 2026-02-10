# local_api/services/day_context.py
"""
Serviço de Contexto do Dia - Camada de Enriquecimento (Read-Only).

Deriva um contexto legível a partir de dados temporais existentes no InventoryState,
sem recalcular demanda ou alterar decisões da engine.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

from core.models import InventoryState, Event, BridgeRule, PaydayRule


# Day of week names in Portuguese
DOW_NAMES = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}

DOW_FLAGS = {
    0: "MONDAY",
    1: "TUESDAY",
    2: "WEDNESDAY",
    3: "THURSDAY",
    4: "FRIDAY",
    5: "SATURDAY",
    6: "SUNDAY",
}


@dataclass
class DayContext:
    """Contexto derivado do dia atual."""
    summary: str
    flags: List[str] = field(default_factory=list)


def get_day_context(state: InventoryState, target_date: date) -> DayContext:
    """
    Deriva o contexto do dia a partir de dados existentes no InventoryState.
    
    Verifica:
    - Dia da semana (SEMPRE presente)
    - Eventos cadastrados na data
    - Bridge days (véspera ou posterior a feriado)
    - Dias de pagamento (Regra Canônica: Dia 5 ou 5º dia útil)
    
    Retorna sempre um contexto composto, nunca vazio.
    """
    flags: List[str] = []
    labels: List[str] = []
    
    weekday = target_date.weekday()
    
    # 1. Dia da Semana (Fallback Obrigatório)
    dow_name = DOW_NAMES.get(weekday, "Dia")
    labels.append(dow_name)
    flags.append(DOW_FLAGS.get(weekday, "UNKNOWN_DAY"))
    
    # 2. Evento na data
    event = _get_event_on_date(target_date, state.events)
    if event:
        flags.append("EVENT")
        safe_name = event.name.upper().replace(' ', '_')
        flags.append(f"EVENT_{safe_name}")
        # Evita duplicação se o nome do evento for igual ao dia (pouco provável, mas...)
        if event.name not in labels:
            labels.append(event.name)
    
    # 3. Bridge day (véspera ou pós-feriado)
    bridge_info = _check_bridge_day(target_date, state.events, state.bridge_rules)
    if bridge_info:
        flags.append("BRIDGE_DAY")
        labels.append(bridge_info)
    
    # 4. Payday (Regra Canônica)
    payday_info = _check_payday(target_date, state.payday_rules, state.events)
    if payday_info:
        flags.append("PAYDAY")
        labels.append(payday_info)
    
    # Build summary
    # Garante que não retorna vazio
    if not labels:
        summary = dow_name
    else:
        summary = " + ".join(labels)
    
    return DayContext(summary=summary, flags=flags)


def _get_event_on_date(target_date: date, events: List[Event]) -> Optional[Event]:
    """Retorna o evento agendado para a data, se houver."""
    for e in events:
        if e.date == target_date:
            return e
    return None


def _check_bridge_day(
    target_date: date, 
    events: List[Event], 
    rules: List[BridgeRule]
) -> Optional[str]:
    """
    Verifica se é um dia de 'ponte' (véspera ou dia seguinte a feriado).
    Retorna descrição ou None.
    """
    if not rules:
        return None
    
    # Verifica se há regra ativa
    active_rule = next((r for r in rules if r.enabled), None)
    if not active_rule:
        return None
    
    # Verifica dia seguinte (véspera de feriado)
    next_day = target_date + timedelta(days=1)
    event_next = _get_event_on_date(next_day, events)
    if event_next:
        return f"Véspera de {event_next.name}"
    
    # Verifica dia anterior (pós-feriado)
    if active_rule.lookback_days >= 1:
        prev_day = target_date - timedelta(days=1)
        event_prev = _get_event_on_date(prev_day, events)
        if event_prev:
            return f"Pós-{event_prev.name}"
    
    return None


def _is_business_day(d: date, events: List[Event] = None) -> bool:
    """
    Retorna True se é dia útil (seg-sex).
    Ignora feriados cadastrados (eventos com factor < 1.0).
    """
    # 1. Fim de semana
    if d.weekday() >= 5:
        return False
        
    # 2. Feriados (Events)
    if events:
        for e in events:
            if e.date == d:
                # Assumindo feriado se factor < 1 (reduz capacidade)
                # Se for promoção (factor > 1), ainda é dia útil
                if e.factor < 1.0:
                    return False
    
    return True


def _get_fifth_business_day(year: int, month: int, events: List[Event] = None) -> date:
    """Retorna o 5º dia útil do mês, ignorando feriados."""
    d = date(year, month, 1)
    business_days = 0
    while business_days < 5:
        if _is_business_day(d, events):
            business_days += 1
        if business_days == 5:
            return d
        d += timedelta(days=1)
        # Safety break para evitar loop infinito em meses absurdos
        if d.month != month and d.year != year and d.month != (month % 12 + 1):
             return d # Should not happen
    return d


def _get_last_business_day(year: int, month: int, events: List[Event] = None) -> date:
    """Retorna o último dia útil do mês."""
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    
    while not _is_business_day(d, events):
        d -= timedelta(days=1)
    return d


def _check_payday(target_date: date, rules: List[PaydayRule], events: List[Event] = None) -> Optional[str]:
    """
    Verifica se é dia de pagamento conforme REGRA CANÔNICA + Regras Customizadas.
    
    REGRA CANÔNICA:
    Se houver PELO MENOS UMA regra de pagamento ativa, consideramos 'Dia de Pagamento' se:
    1. Dia correte == 5
    OR
    2. Dia corrente == 5º Dia Útil
    
    ALÉM DISSO:
    Respeita configurações específicas que caiam em outros dias (ex: dia fixo 20).
    
    Retorna o nome da regra (ex: "Salário") se atender às condições.
    """
    if not rules:
        return None
    
    # Coleta regras habilitadas
    enabled_rules = [r for r in rules if r.enabled]
    if not enabled_rules:
        return None

    # Pre-calcula condições canônicas
    is_day_5 = (target_date.day == 5)
    fifth_bd = _get_fifth_business_day(target_date.year, target_date.month, events)
    is_fifth_bd = (target_date == fifth_bd)
    
    # Cache para last_business_day (evitar recalcular para cada regra se houver múltiplas)
    last_bd = None 
    
    for r in enabled_rules:
        triggered = False
        
        # 1. Trigger Canônico (Global para qualquer regra de pagamento)
        # Se é dia 5 ou 5º dia útil, consideramos pagamento (fallback seguro)
        if is_day_5 or is_fifth_bd:
            triggered = True
            
        # 2. Trigger Específico da Regra
        if r.rule_type == 'fixed_day' and r.day_of_month == target_date.day:
            triggered = True
        elif r.rule_type == 'fifth_business_day' and is_fifth_bd:
            triggered = True
        elif r.rule_type == 'last_business_day':
            if last_bd is None:
                last_bd = _get_last_business_day(target_date.year, target_date.month, events)
            if target_date == last_bd:
                triggered = True
                
        if triggered:
            return r.name or "Pagamento"
            
    return None
