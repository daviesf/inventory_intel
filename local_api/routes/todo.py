# local_api/routes/todo.py

from __future__ import annotations
from typing import Dict, Any, List, Literal
from fastapi import APIRouter, Query
from core import analyze_inventory
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from local_api.services.day_context import get_day_context
from local_api.services.business_translator import translate_alert
from local_api.services.financial_impact_estimator import enrich_with_financial_impact

router = APIRouter(prefix="/todo", tags=["todo"])


def _priority_weight(priority: str) -> int:
    if priority == "urgent": return 1
    if priority == "plan": return 2
    return 3


@router.get("", response_model=dict)
async def get_todo(
        ignore_stock_balance: bool = Query(False),
        status: Literal["active", "suppressed"] = Query("active")
) -> Dict[str, List[Dict[str, Any]]]:
    repo = SqlAlchemyInventoryRepository()
    state, ctx = repo.load_inventory_state()

    if ignore_stock_balance:
        ctx.ignore_stock_balance = True

    # Se status == suppressed, ativamos o "Include Suppressed" na engine
    # Isso faz a engine retornar (Ativos + Suprimidos)
    include_suppressed = (status == "suppressed")
    alerts = analyze_inventory(state, ctx, include_suppressed=include_suppressed)

    todos = {"purchasing": [], "kitchen": [], "management": []}

    for a in alerts:
        is_suppressed = getattr(a, 'is_suppressed', False)

        # LÓGICA DE FILTRO (Ghost Mode vs Standard)

        # 1. Se o modo é 'active' (padrão), escondemos os suprimidos.
        if status == "active" and is_suppressed:
            continue

        # 2. Se o modo é 'suppressed', mostramos APENAS os suprimidos (FIX API-001)
        # O comportamento anterior ("suppressed" = "show all") era confuso.
        # Agora: status="suppressed" -> returns ONLY suppressed items.
        if status == "suppressed" and not is_suppressed:
            continue

        task = {
            "alert_id": a.id,
            "title": a.title,
            "description": a.message,
            "priority": a.priority.value,
            "sphere": a.sphere.value,
            "created_at": a.created_at.isoformat(),
            "reliability": a.reliability.value,
            "reliability_score": a.reliability_score,
            "data_error": a.data_error,
            "anomaly": a.anomaly_flag,
            "meta": a.data or {},
            "is_suppressed": is_suppressed
        }
        
        # Traduzir termos técnicos para linguagem de negócio
        task = translate_alert(task)
        
        # Enriquecer com Impacto Financeiro (Novo)
        task = enrich_with_financial_impact(task, state)
        
        persona_key = a.persona.value
        if persona_key not in todos:
            todos[persona_key] = []
        todos[persona_key].append(task)

    for persona, tasks in todos.items():
        # Ordenação: Prioridade > Suprimidos por último
        # Damos um peso extra para jogar os suprimidos para o final da lista visualmente
        tasks.sort(key=lambda t: (_priority_weight(t["priority"]) + (10 if t["is_suppressed"] else 0)))

    # Enriquecer com contexto do dia (camada de leitura, não altera engine)
    day_ctx = get_day_context(state, ctx.now.date())

    return {
        "context": {
            "summary": day_ctx.summary,
            "flags": day_ctx.flags
        },
        "purchasing": todos.get("purchasing", []),
        "kitchen": todos.get("kitchen", []),
        "management": todos.get("management", [])
    }