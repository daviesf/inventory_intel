# local_api/routes/metrics.py

from __future__ import annotations

from collections import Counter
from typing import Dict, Any, Literal

from fastapi import APIRouter, Query

from core import analyze_inventory
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=dict)
async def get_metrics(
    ignore_stock_balance: bool = Query(False),
    status: Literal["active", "suppressed"] = Query("active"),
) -> Dict[str, Any]:
    """
    Retorna métricas agregadas sobre os alertas gerados.

    - Distribuição por prioridade (urgent/plan/info)
    - Distribuição por esfera (product/data_quality/etc)
    - Distribuição por persona (purchasing/kitchen/management)
    - Contagem de itens com estoque negativo, sem histórico, etc.

    O parâmetro `status` espelha o comportamento do /todo:

    - status = "active"     -> considera apenas alertas ativos (não suprimidos)
    - status = "suppressed" -> considera ativos + suprimidos (Ghost Mode)
    """
    repo = SqlAlchemyInventoryRepository()
    state, ctx = repo.load_inventory_state()

    if ignore_stock_balance:
        ctx.ignore_stock_balance = True

    include_suppressed = status == "suppressed"

    # Se include_suppressed = True, a engine devolve ativos + suprimidos,
    # com Alert.is_suppressed devidamente marcado.
    alerts = analyze_inventory(state, ctx, include_suppressed=include_suppressed)

    by_priority = Counter(a.priority.value for a in alerts)
    by_sphere = Counter(a.sphere.value for a in alerts)
    by_persona = Counter(a.persona.value for a in alerts)

    negative_stock_count = sum(
        1 for a in alerts if a.data_error and "negative_stock" in a.id
    )
    data_error_count = sum(1 for a in alerts if a.data_error)
    no_demand_count = sum(1 for a in alerts if a.id.startswith("no_demand_history_"))

    metrics: Dict[str, Any] = {
        "totals": {
            # Aqui o total já respeita o status (active vs suppressed)
            "alerts": len(alerts),
            "items": len(state.items),
            "stock_records": len(state.stock_levels),
            "sales_records": len(state.sales_history),
        },
        "by_priority": dict(by_priority),
        "by_sphere": dict(by_sphere),
        "by_persona": dict(by_persona),
        "data_quality": {
            "negative_stock": negative_stock_count,
            "data_error_alerts": data_error_count,
            "no_demand_items": no_demand_count,
        },
    }

    return metrics
