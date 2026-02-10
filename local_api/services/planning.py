# local_api/services/planning.py
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from core.models import InventoryState, Event, AnalysisContext
from local_api.services.day_context import _get_event_on_date, _check_bridge_day, _check_payday
from local_api.services.planning_impact import PlanningImpactService

class PlanningService:
    @staticmethod
    def get_planning_preview(state: InventoryState, ctx: AnalysisContext, start_date: date, window_days: int = 7) -> Dict[str, Any]:
        """
        Gera uma previsão de planejamento para os próximos dias.
        Foco em eventos qualitativos, feriados e alertas de calendário.
        Agora inclui ANÁLISE QUANTITATIVA DE IMPACTO (Shadow Run).
        """
        events_found = []
        
        for i in range(window_days):
            target_date = start_date + timedelta(days=i)
            days_distance = (target_date - start_date).days
            
            # Detectar triggers
            event_obj = _get_event_on_date(target_date, state.events)
            bridge = _check_bridge_day(target_date, state.events, state.bridge_rules)
            payday = _check_payday(target_date, state.payday_rules, state.events)
            
            # Se houver qualquer "ocasião especial", calcula impacto
            impacts = []
            event_type = None
            label = None
            
            if event_obj:
                event_type = "EVENT"
                label = event_obj.name
            elif payday:
                event_type = "PAYDAY"
                label = f"Dia de Pagamento ({payday})"
            elif bridge:
                event_type = "BRIDGE"
                label = bridge
            
            if event_type:
                # Executa Simulação Operacional (Shadow Run)
                try:
                    impacts = PlanningImpactService.calculate_impacts(state, ctx, target_date)
                    
                    if impacts:
                        total_delta = sum(i['delta_quantity'] for i in impacts)
                        items_count = len(impacts)
                        if total_delta > 0:
                            summary = f"Previsão de maior consumo em {items_count} itens principais."
                        elif total_delta < 0:
                            summary = f"Previsão de menor movimento para {items_count} itens."
                        else:
                            summary = "Variações mistas esperadas no mix de produtos."
                    else:
                        summary = "Sem impacto operacional relevante identificado nos itens monitorados."
                        
                except Exception as e:
                    print(f"Erro ao calcular impacto para {target_date}: {e}")
                    impacts = []
                    summary = "Análise de impacto indisponível."
                
                events_found.append({
                    "date": target_date.isoformat(),
                    "type": event_type,
                    "label": label,
                    "days_away": days_distance,
                    "impact_summary": summary,
                    "impacted_items": impacts
                })
                
        return {
            "window_days": window_days,
            "events": events_found
        }


