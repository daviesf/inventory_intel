# local_api/schemas_ingest.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ItemIn(BaseModel):
    external_id: str
    name: str
    type: str               # 'finished', 'raw', etc
    unit: str
    item_class: str         # 'A', 'B', 'C'
    lead_time_days: float
    shelf_life_days: Optional[float] = None


class StockLevelIn(BaseModel):
    external_item_id: str
    quantity: float
    lot_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class StockLotIn(BaseModel):
    item_id: str
    lot_id: str
    quantity: float
    expires_at: datetime


class StockSnapshotIn(BaseModel):
    generated_at: datetime
    levels: List[StockLevelIn]


class SaleIn(BaseModel):
    external_sale_id: str
    dish_code: str
    quantity: float
    timestamp: datetime


class SalesBatchIn(BaseModel):
    source: str
    sales: List[SaleIn]


class DishIn(BaseModel):
    external_id: str
    name: str
    prep_time_min: float = 0
    pre_prep_time_min: float = 0


class RecipeIn(BaseModel):
    parent_item_id: str
    child_item_id: str
    quantity: float

