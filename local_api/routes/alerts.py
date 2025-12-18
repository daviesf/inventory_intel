# local_api/routes/alerts.py

from __future__ import annotations
from typing import List, Literal, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel
from core import analyze_inventory
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from core.serialization import alert_to_dict

router = APIRouter(prefix="/alerts", tags=["alerts"])


class SuppressRequest(BaseModel):
    action: Literal["tomorrow", "week", "forever"]


@router.get("", response_model=List[Dict[str, Any]])
async def get_alerts(
        ignore_stock_balance: bool = Query(False),
        include_suppressed: bool = Query(False)
):
    repo = SqlAlchemyInventoryRepository()
    state, ctx = repo.load_inventory_state()

    if ignore_stock_balance:
        ctx.ignore_stock_balance = True

    # Passa o flag para a engine
    alerts = analyze_inventory(state, ctx, include_suppressed=include_suppressed)

    results = []
    for a in alerts:
        d = alert_to_dict(a)
        results.append(d)

    return results


@router.post("/{alert_id}/suppress")
async def suppress_alert(alert_id: str, body: SuppressRequest):
    repo = SqlAlchemyInventoryRepository()
    now = datetime.now()
    until = None
    if body.action == "tomorrow":
        until = now + timedelta(days=1)
    elif body.action == "week":
        until = now + timedelta(days=7)
    elif body.action == "forever":
        until = None

    try:
        repo.suppress_alert(alert_id, until)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


@router.delete("/{alert_id}/suppress")
async def restore_alert(alert_id: str):
    repo = SqlAlchemyInventoryRepository()
    try:
        repo.remove_suppression(alert_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "restored"}