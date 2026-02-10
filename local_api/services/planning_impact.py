# local_api/services/planning_impact.py
from datetime import date
from typing import List, Dict, Any, Optional
import copy

from core.models import InventoryState, Item, ItemType, AnalysisContext
from core.forecast import _build_daily_series_for_item, _forecast_wma_for_weekday
from core.temporal_adjustments import apply_temporal_adjustments, TemporalBreakdown
from local_api.services.day_context import _get_event_on_date

class PlanningImpactService:
    @staticmethod
    def calculate_impacts(state: InventoryState, ctx: AnalysisContext, target_date: date) -> List[Dict[str, Any]]:
        """
        Simula impacto operacional para uma data futura específica.
        Retorna lista de itens com delta relevante (Impacto da ocasião).
        """
        impacts = []
        
        # Filtrar apenas itens Finished
        finished_items = [i for i in state.items if i.item_type == ItemType.FINISHED]
        
        for item in finished_items:
            # 2. Obter Forecast Base (WMA puro do dia da semana) - Cenário "Dia Normal"
            series = _build_daily_series_for_item(state, item.id, ctx)
            target_weekday = target_date.weekday()
            
            # WMA forecast for the target weekday based on history
            wma_base = _forecast_wma_for_weekday(series, target_weekday)
            
            if wma_base <= 0.1:
                continue
                
            # 3. Cenário COM Evento (Real)
            adj_real = apply_temporal_adjustments(item.id, target_date, wma_base, state)
            qty_real = adj_real.forecast_final
            
            # 4. Cenário SEM Evento (Simulado) - "Se fosse um dia normal"
            state_no_event = copy.copy(state)
            state_no_event.events = [e for e in state.events if e.date != target_date]
            state_no_event.payday_rules = [] 
            state_no_event.bridge_rules = []
            
            adj_base = apply_temporal_adjustments(item.id, target_date, wma_base, state_no_event)
            qty_base = adj_base.forecast_final
            
            delta = qty_real - qty_base
            
            # Threshold de relevância: > 5 un e > 5% variação
            if abs(delta) >= 5 and abs(delta / (qty_base + 0.01)) > 0.05:
                direction = "increase" if delta > 0 else "decrease"
                impacts.append({
                    "item_name": item.name,
                    "base_quantity": round(qty_base, 1),
                    "adjusted_quantity": round(qty_real, 1),
                    "delta_quantity": round(delta, 1),
                    "delta_direction": direction,
                    "message": PlanningImpactService._generate_message(item.name, delta)
                })
                
        # Ordenar por maior impacto absoluto
        impacts.sort(key=lambda x: abs(x['delta_quantity']), reverse=True)
        return impacts[:10] # Top 10 impactos
        
    @staticmethod
    def _generate_message(item_name: str, delta: float) -> str:
        abs_delta = abs(int(delta))
        if delta > 0:
            return f"A necessidade estimada de {item_name} aumenta em {abs_delta} unidades."
        else:
            return f"A necessidade estimada de {item_name} reduz em {abs_delta} unidades."
