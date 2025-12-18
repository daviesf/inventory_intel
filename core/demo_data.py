# core/demo_data.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple

from .models import (
    Item,
    ItemType,
    ItemClass,
    OperationMode,
    InventoryState,
    Dish,
    Recipe,
    StockLevel,
    Sale,
    AnalysisContext,
)


def build_complex_demo_state() -> Tuple[InventoryState, AnalysisContext, AnalysisContext]:
    """
    Cenário "rico" de demonstração com vários comportamentos:
    - Coca (classe A): alta demanda, estoque baixo -> URGENT
    - Itubaína (classe C): baixa demanda, estoque alto -> INFO
    - Água (classe B, Base Zero): demanda moderada, DEMAND_ONLY por item
    - Cerveja (classe A): estoque negativo -> DATA_QUALITY
    - Suco (classe B): sem histórico -> INFO "sem demanda"
    """
    now = datetime.now()

    # 1) Itens
    coca = Item(
        id="item_coca_ks",
        name="Coca-Cola KS",
        item_type=ItemType.FINISHED,
        unit="un",
        lead_time_days=3.0,
        shelf_life_days=180.0,
        item_class=ItemClass.A,
        operation_mode=OperationMode.STRICT,
        last_audit_date=now.date(),
    )

    itubaina = Item(
        id="item_itubaina_ks",
        name="Itubaína KS",
        item_type=ItemType.FINISHED,
        unit="un",
        lead_time_days=3.0,
        shelf_life_days=365.0,
        item_class=ItemClass.C,
        operation_mode=OperationMode.STRICT,
        last_audit_date=None,
    )

    agua = Item(
        id="item_agua_500",
        name="Água Mineral 500ml",
        item_type=ItemType.FINISHED,
        unit="un",
        lead_time_days=2.0,
        shelf_life_days=365.0,
        item_class=ItemClass.B,
        operation_mode=OperationMode.DEMAND_ONLY,
        last_audit_date=None,
    )

    cerveja = Item(
        id="item_cerveja_long_neck",
        name="Cerveja Long Neck",
        item_type=ItemType.FINISHED,
        unit="un",
        lead_time_days=5.0,
        shelf_life_days=180.0,
        item_class=ItemClass.A,
        operation_mode=OperationMode.STRICT,
        last_audit_date=now.date(),
    )

    suco = Item(
        id="item_suco_lata",
        name="Suco em Lata",
        item_type=ItemType.FINISHED,
        unit="un",
        lead_time_days=4.0,
        shelf_life_days=365.0,
        item_class=ItemClass.B,
        operation_mode=OperationMode.STRICT,
        last_audit_date=now.date(),
    )

    items: List[Item] = [coca, itubaina, agua, cerveja, suco]

    # 2) Nenhum prato/receita ainda
    dishes: List[Dish] = []
    recipes: List[Recipe] = []

    # 3) Estoque
    stock_levels: List[StockLevel] = [
        StockLevel(item_id="item_coca_ks", quantity=120),
        StockLevel(item_id="item_itubaina_ks", quantity=80),
        StockLevel(item_id="item_agua_500", quantity=50),
        StockLevel(item_id="item_cerveja_long_neck", quantity=-10),
        StockLevel(item_id="item_suco_lata", quantity=40),
    ]

    # 4) Vendas últimos 14 dias
    sales_history: List[Sale] = []
    base_date = now - timedelta(days=14)

    coca_daily = [60, 65, 70, 80, 75, 70, 68, 72, 69, 71, 73, 74, 76, 70]
    for i, qty in enumerate(coca_daily):
        ts = base_date + timedelta(days=i)
        sales_history.append(Sale(dish_id="item_coca_ks", quantity=qty, timestamp=ts))

    for i in range(14):
        ts = base_date + timedelta(days=i)
        sales_history.append(
            Sale(dish_id="item_itubaina_ks", quantity=5, timestamp=ts)
        )

    agua_daily = [18, 22, 19, 20, 21, 23, 17, 20, 19, 22, 21, 20, 18, 19]
    for i, qty in enumerate(agua_daily):
        ts = base_date + timedelta(days=i)
        sales_history.append(Sale(dish_id="item_agua_500", quantity=qty, timestamp=ts))

    cerveja_daily = [28, 30, 32, 31, 29, 30, 30, 31, 32, 29, 28, 30, 31, 30]
    for i, qty in enumerate(cerveja_daily):
        ts = base_date + timedelta(days=i)
        sales_history.append(
            Sale(dish_id="item_cerveja_long_neck", quantity=qty, timestamp=ts)
        )

    # Suco sem vendas propositalmente

    today_sales: List[Sale] = []

    state = InventoryState(
        items=items,
        dishes=dishes,
        recipes=recipes,
        stock_levels=stock_levels,
        sales_history=sales_history,
        today_sales=today_sales,
    )

    ctx_normal = AnalysisContext(now=now)
    ctx_ignore_stock = AnalysisContext(now=now, ignore_stock_balance=True)

    return state, ctx_normal, ctx_ignore_stock
