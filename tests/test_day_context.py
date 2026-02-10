# tests/test_day_context.py
"""
Testes unitários para o serviço de Contexto do Dia.
Valida que o contexto é derivado corretamente dos dados temporais.
"""

import pytest
from datetime import date
from core.models import InventoryState, Event, BridgeRule, PaydayRule
from local_api.services.day_context import get_day_context, DayContext


def _empty_state() -> InventoryState:
    """Cria um InventoryState mínimo para testes."""
    return InventoryState(
        items=[],
        dishes=[],
        recipes=[],
        stock_levels=[],
        sales_history=[],
        today_sales=[],
        lots=[],
        suppressed_alerts={},
        alert_history={},
        dow_factors={},
        month_factors={},
        events=[],
        bridge_rules=[],
        payday_rules=[]
    )


class TestDayContextNormal:
    """Testes para dias normais."""
    
    def test_normal_weekday_returns_weekday_name(self):
        """Segunda deve retornar 'Segunda-feira' (não Dia normal)."""
        state = _empty_state()
        # 2026-01-05 é uma segunda-feira
        result = get_day_context(state, date(2026, 1, 5))
        
        # Agora o comportamento padrão é sempre mostrar o dia
        assert "Segunda-feira" in result.summary
    
    def test_wednesday_without_events(self):
        """Quarta-feira sem eventos = Quarta-feira."""
        state = _empty_state()
        # 2026-01-07 é quarta-feira
        result = get_day_context(state, date(2026, 1, 7))
        
        assert "Quarta-feira" in result.summary


class TestDayContextWeekend:
    """Testes para fins de semana e sexta-feira."""
    
    def test_friday_returns_sexta_feira(self):
        """Sexta-feira deve aparecer no contexto."""
        state = _empty_state()
        # 2026-01-09 é sexta-feira
        result = get_day_context(state, date(2026, 1, 9))
        
        assert "Sexta-feira" in result.summary
        assert "FRIDAY" in result.flags
    
    def test_saturday_returns_sabado(self):
        """Sábado deve aparecer no contexto."""
        state = _empty_state()
        # 2026-01-10 é sábado
        result = get_day_context(state, date(2026, 1, 10))
        
        assert "Sábado" in result.summary
        assert "SATURDAY" in result.flags
    
    def test_sunday_returns_domingo(self):
        """Domingo deve aparecer no contexto."""
        state = _empty_state()
        # 2026-01-11 é domingo
        result = get_day_context(state, date(2026, 1, 11))
        
        assert "Domingo" in result.summary
        assert "SUNDAY" in result.flags


class TestDayContextEvents:
    """Testes para eventos cadastrados."""
    
    def test_event_on_date(self):
        """Evento na data deve aparecer no contexto."""
        state = _empty_state()
        state.events = [
            Event(id=1, name="Natal", date=date(2026, 12, 25), factor=0.5)
        ]
        
        result = get_day_context(state, date(2026, 12, 25))
        
        assert "Natal" in result.summary
        assert "EVENT" in result.flags
    
    def test_friday_plus_event(self):
        """Sexta-feira com evento deve combinar ambos."""
        state = _empty_state()
        # 2026-01-09 é sexta-feira
        state.events = [
            Event(id=1, name="Feriado Local", date=date(2026, 1, 9), factor=0.3)
        ]
        
        result = get_day_context(state, date(2026, 1, 9))
        
        assert "Sexta-feira" in result.summary
        assert "Feriado Local" in result.summary
        assert "FRIDAY" in result.flags
        assert "EVENT" in result.flags


class TestDayContextBridgeDays:
    """Testes para dias de ponte (véspera/pós-feriado)."""
    
    def test_bridge_day_before_holiday(self):
        """Véspera de feriado deve indicar bridge day."""
        state = _empty_state()
        state.events = [
            Event(id=1, name="Feriado", date=date(2026, 1, 10), factor=0.2)
        ]
        state.bridge_rules = [
            BridgeRule(id=1, name="Bridge Rule", multiplier=0.5, lookback_days=1, enabled=True)
        ]
        
        # 2026-01-09 é véspera do feriado
        result = get_day_context(state, date(2026, 1, 9))
        
        assert "Véspera de Feriado" in result.summary
        assert "BRIDGE_DAY" in result.flags
    
    def test_bridge_day_after_holiday(self):
        """Dia após feriado deve indicar bridge day (pós)."""
        state = _empty_state()
        state.events = [
            Event(id=1, name="Feriado", date=date(2026, 1, 10), factor=0.2)
        ]
        state.bridge_rules = [
            BridgeRule(id=1, name="Bridge", multiplier=0.5, lookback_days=1, enabled=True)
        ]
        
        # 2026-01-11 é pós-feriado
        result = get_day_context(state, date(2026, 1, 11))
        
        assert "Pós-Feriado" in result.summary
        assert "BRIDGE_DAY" in result.flags
    
    def test_no_bridge_if_rule_disabled(self):
        """Regra de bridge desabilitada não deve gerar contexto."""
        state = _empty_state()
        state.events = [
            Event(id=1, name="Feriado", date=date(2026, 1, 10), factor=0.2)
        ]
        state.bridge_rules = [
            BridgeRule(id=1, name="Bridge", multiplier=0.5, lookback_days=1, enabled=False)
        ]
        
        result = get_day_context(state, date(2026, 1, 9))
        
        assert "BRIDGE_DAY" not in result.flags


class TestDayContextPayday:
    """Testes para dias de pagamento."""
    
    def test_fixed_day_payday(self):
        """Dia fixo de pagamento deve aparecer no contexto."""
        state = _empty_state()
        state.payday_rules = [
            PaydayRule(id=1, name="Pagamento", day_of_month=5, rule_type="fixed_day", multiplier=1.1, enabled=True)
        ]
        
        result = get_day_context(state, date(2026, 1, 5))
        
        assert "Pagamento" in result.summary
        assert "PAYDAY" in result.flags
    
    def test_fifth_business_day_payday(self):
        """5º dia útil como payday."""
        state = _empty_state()
        state.payday_rules = [
            PaydayRule(id=1, name="5º Dia Útil", day_of_month=None, rule_type="fifth_business_day", multiplier=1.1, enabled=True)
        ]
        
        # Janeiro 2026: 1=Qui (não é feriado aqui), 2=Sex, 5=Seg, 6=Ter, 7=Qua (5º útil)
        result = get_day_context(state, date(2026, 1, 7))
        
        assert "5º Dia Útil" in result.summary
        assert "PAYDAY" in result.flags

    def test_smart_canonical_payday_both_conditions(self):
        """
        Nova regra canônica: Dia 5 OU 5º dia útil devem funcionar.
        Mesmo se a regra for 'fifth_business_day', o dia 5 também deve triggar.
        """
        state = _empty_state()
        state.payday_rules = [
             # Regra configurada para 5th business day
             PaydayRule(id=1, name="Salário", day_of_month=None, rule_type="fifth_business_day", multiplier=1.0, enabled=True)
        ]
        
        # Teste Dia 5 (Segunda) -> Deve ativar canonical match dia 5
        res5 = get_day_context(state, date(2026, 1, 5))
        assert "Salário" in res5.summary
        
        # Teste 5º Dia Útil (no feriado)
        # Jan 7 (Qua) é 5º útil (sem event)
        res7 = get_day_context(state, date(2026, 1, 7))
        assert "Salário" in res7.summary

    
    def test_payday_disabled_rule(self):
        """Regra desabilitada não deve gerar contexto."""
        state = _empty_state()
        state.payday_rules = [
            PaydayRule(id=1, name="Pagamento", day_of_month=5, rule_type="fixed_day", multiplier=1.1, enabled=False)
        ]
        
        result = get_day_context(state, date(2026, 1, 5))
        
        assert "PAYDAY" not in result.flags


class TestDayContextCombined:
    """Testes para combinações de contextos."""
    
    def test_friday_bridge_payday(self):
        """Múltiplos contextos devem ser combinados."""
        state = _empty_state()
        # 2026-01-09 é sexta-feira
        state.events = [
            Event(id=1, name="Feriado", date=date(2026, 1, 10), factor=0.2)
        ]
        state.bridge_rules = [
            BridgeRule(id=1, name="Bridge", multiplier=0.5, lookback_days=1, enabled=True)
        ]
        state.payday_rules = [
            PaydayRule(id=1, name="Pagamento", day_of_month=9, rule_type="fixed_day", multiplier=1.1, enabled=True)
        ]
        
        result = get_day_context(state, date(2026, 1, 9))
        
        assert "Sexta-feira" in result.summary
        assert "Véspera de Feriado" in result.summary
        assert "Pagamento" in result.summary
        assert "FRIDAY" in result.flags
        assert "BRIDGE_DAY" in result.flags
        assert "PAYDAY" in result.flags
