# scripts/check_prices.py
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository

def check_prices():
    repo = SqlAlchemyInventoryRepository()
    state, ctx = repo.load_inventory_state()
    
    total_items = len(state.items)
    items_with_price = sum(1 for i in state.items if (getattr(i, 'price', 0) or 0) > 0)
    items_with_cost = sum(1 for i in state.items if (getattr(i, 'cost', 0) or 0) > 0)
    
    print(f"Total Items: {total_items}")
    print(f"Items with Price > 0: {items_with_price}")
    print(f"Items with Cost > 0: {items_with_cost}")
    
    if items_with_price == 0 and items_with_cost == 0:
        print("WARNING: No financial data found. Feature will remain hidden.")
    else:
        print("OK: Financial data exists.")

if __name__ == "__main__":
    check_prices()
