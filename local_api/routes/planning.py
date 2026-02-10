# local_api/routes/planning.py
from fastapi import APIRouter, Query, Request
from dataclasses import asdict
from datetime import date

from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from local_api.services.planning import PlanningService

router = APIRouter(prefix="/planning", tags=["planning"])

@router.get("/preview")
def get_planning_preview(
    window: int = Query(7, ge=1, le=30, description="Janela de dias para análise")
):
    """
    Retorna previsão qualitativa de eventos futuros (Planejamento Próximo).
    Read-only. Não afeta engine.
    """
    repo = SqlAlchemyInventoryRepository()
    # Carrega estado atual (necessário para ter acesso a eventos e regras configuradas)
    # Note: load_inventory_state carrega tudo. Poderia ser otimizado, mas para MVP ok.
    # O foco é consistência com o motor.
    state, ctx = repo.load_inventory_state()
    
    # Usa a data atual do contexto (que vem do servidor/sistema)
    # Se ctx.now for datetime, pegamos .date()
    current_date = ctx.now.date() if hasattr(ctx.now, "date") else ctx.now

    result = PlanningService.get_planning_preview(state, ctx, current_date, window_days=window)
    return result
