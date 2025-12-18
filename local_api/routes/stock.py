# local_api/routes/stock.py

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from collections import defaultdict
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from infra.orm_models import ItemORM, StockLevelORM, SaleORM, ItemType

router = APIRouter(prefix="/stock", tags=["stock"])


class UpdateStockRequest(BaseModel):
    quantity: float


class StockItemResponse(BaseModel):
    id: str
    name: str
    unit: str
    category: str
    current_stock: float
    last_audit: str | None


@router.get("/items", response_model=List[StockItemResponse])
async def get_all_stock_items():
    """
    Retorna todos os itens (produtos e ingredientes) com o estoque calculado atual.
    Calcula: (Última Contagem Manual) - (Vendas posteriores a essa contagem).
    """
    repo = SqlAlchemyInventoryRepository()
    # Carrega estado bruto
    state, ctx = repo.load_inventory_state()

    # Lógica de cálculo de estoque (replicada da engine para consistência)
    # 1. Mapear vendas por item
    sales_after_map = defaultdict(list)
    all_sales = state.sales_history + state.today_sales
    for s in all_sales:
        sales_after_map[s.dish_id].append(s)

    # 2. Mapear estoque base
    stock_map = {}
    for sl in state.stock_levels:
        stock_map[sl.item_id] = sl

    results = []

    for item in state.items:
        # Pula itens que não têm estoque físico direto (ex: serviços, se houver)
        # Mas vamos listar tudo que é tangible

        # Pega nível de estoque base
        sl = stock_map.get(item.id)

        current_qty = 0.0
        last_audit_str = None

        if sl:
            base_qty = sl.quantity
            current_qty = base_qty

            # Se tiver data de atualização, abate vendas posteriores
            if sl.updated_at:
                relevant_sales = [
                    s for s in sales_after_map[item.id]
                    if s.timestamp > sl.updated_at
                ]
                total_sold = sum(s.quantity for s in relevant_sales)
                current_qty = max(0.0, base_qty - total_sold)
                last_audit_str = sl.updated_at.isoformat()

        # Categorização simples para o front
        cat = "Outros"
        if item.item_type.value == "finished":
            cat = "Produto (Venda)"
        elif item.item_type.value == "ingredient":
            cat = "Ingrediente"
        elif item.item_type.value == "semi_finished":
            cat = "Pré-Preparo"

        results.append(StockItemResponse(
            id=item.id,
            name=item.name,
            unit=item.unit,
            category=cat,
            current_stock=round(current_qty, 2),
            last_audit=last_audit_str
        ))

    # Ordena por nome
    results.sort(key=lambda x: x.name)
    return results


@router.post("/{item_id}")
async def update_stock_manual(item_id: str, body: UpdateStockRequest):
    """
    Atualiza o estoque manualmente (override).
    """
    repo = SqlAlchemyInventoryRepository()
    try:
        repo.update_manual_stock(item_id, body.quantity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "updated", "item_id": item_id, "new_quantity": body.quantity}