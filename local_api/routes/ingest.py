# local_api/routes/ingest.py

from __future__ import annotations

from fastapi import APIRouter

from infra.db import SessionLocal
from infra.orm_models import ItemORM, StockLevelORM, SaleORM, RecipeORM, DishORM, StockLotORM
from local_api.schemas_ingest import (
    ItemIn,
    StockSnapshotIn,
    SalesBatchIn,
    DishIn,
    RecipeIn,
    StockLotIn,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/items")
async def ingest_items(items: list[ItemIn]):
    """
    Recebe o cadastro de itens (produtos) normalizados.

    Faz um upsert: se o item já existir pelo ID externo, atualiza; senão, insere.
    """
    with SessionLocal() as session:
        for i in items:
            existing = session.get(ItemORM, i.external_id)
            if existing:
                existing.name = i.name
                existing.item_type = i.type
                existing.unit = i.unit
                existing.item_class = i.item_class
                existing.lead_time_days = i.lead_time_days
                existing.shelf_life_days = i.shelf_life_days
            else:
                session.add(
                    ItemORM(
                        id=i.external_id,
                        name=i.name,
                        item_type=i.type,
                        unit=i.unit,
                        item_class=i.item_class,
                        lead_time_days=i.lead_time_days,
                        shelf_life_days=i.shelf_life_days,
                        operation_mode="strict",  # default inicial
                        last_audit_date=None,
                    )
                )
        session.commit()

    return {"status": "ok", "count": len(items)}


@router.post("/stock_snapshot")
async def ingest_stock_snapshot(snapshot: StockSnapshotIn):
    """
    Recebe um snapshot completo de estoque.

    Estratégia simples: limpa os registros anteriores e insere o snapshot.
    """
    with SessionLocal() as session:
        session.query(StockLevelORM).delete()
        for lvl in snapshot.levels:
            session.add(
                StockLevelORM(
                    item_id=lvl.external_item_id,
                    quantity=lvl.quantity,
                    lot_id=lvl.lot_id,
                    expires_at=lvl.expires_at,
                )
            )
        session.commit()

    return {"status": "ok", "count": len(snapshot.levels)}


@router.post("/sales_batch")
async def ingest_sales_batch(batch: SalesBatchIn):
    """
    Recebe um lote de vendas já consolidadas.

    No futuro o conector vai mandar isso a partir do banco do PDV.
    """
    with SessionLocal() as session:
        for s in batch.sales:
            session.add(
                SaleORM(
                    dish_id=s.dish_code,
                    quantity=s.quantity,
                    timestamp=s.timestamp,
                )
            )
        session.commit()

    return {"status": "ok", "count": len(batch.sales)}


@router.post("/dishes")
async def ingest_dishes(dishes: list[DishIn]):
    with SessionLocal() as session:
        for d in dishes:
            obj = session.get(DishORM, d.external_id)
            if obj:
                obj.name = d.name
                obj.prep_time_min = d.prep_time_min
                obj.pre_prep_time_min = d.pre_prep_time_min
            else:
                session.add(
                    DishORM(
                        id=d.external_id,
                        name=d.name,
                        prep_time_min=d.prep_time_min,
                        pre_prep_time_min=d.pre_prep_time_min,
                    )
                )
        session.commit()

    return {"status": "ok", "count": len(dishes)}


@router.post("/recipes")
async def ingest_recipes(recipes: list[RecipeIn]):
    with SessionLocal() as session:
        for r in recipes:
            session.add(
                RecipeORM(
                    parent_item_id=r.parent_item_id,
                    child_item_id=r.child_item_id,
                    quantity=r.quantity,
                )
            )
        session.commit()

    return {"status": "ok", "count": len(recipes)}


@router.post("/lots")
async def ingest_lots(lots: list[StockLotIn]):
    """Recebe carga de lotes (ingestão automática)."""
    with SessionLocal() as session:
        # Opcional: Limpar lotes anteriores ou fazer append?
        # Regra do prompt: "Alimentar state.lots". Geralmente ingest é full snapshot ou delta.
        # Vamos assumir append/upsert simplificado. Como lot_id não é PK única global (pode repetir?),
        # mas StockLotORM tem ID auto.
        # Vamos limpar lotes desse item ou tudo? Prompt não especifica.
        # "Opção A: ingest automática via connector". Connector geralmente manda tudo ou manda updates.
        # Pela simplicidade e para evitar duplicatas infinitas, vamos assumir que é um snapshot de lotes válidos
        # OU fazer check se já existe.
        # Melhor abordagem segura: Ver se lote existe (item_id + lot_id) e atualizar qtd.
        
        for l in lots:
            # Tentar achar lote existente
            existing = session.query(StockLotORM).filter(
                StockLotORM.item_id == l.item_id,
                StockLotORM.lot_id == l.lot_id
            ).first()
            
            if existing:
                existing.quantity = l.quantity
                existing.expires_at = l.expires_at.date() # Converte datetime do pydantic para date
            else:
                session.add(StockLotORM(
                    item_id=l.item_id,
                    lot_id=l.lot_id,
                    quantity=l.quantity,
                    expires_at=l.expires_at.date()
                ))
        session.commit()

    return {"status": "ok", "count": len(lots)}
