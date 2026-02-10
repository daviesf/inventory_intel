
import random
from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from infra.db import SessionLocal
from infra.orm_models import ItemORM

from sqlalchemy import text

def seed_data():
    repo = SqlAlchemyInventoryRepository()
    session = SessionLocal()
    
    # 1. Schema Migration (Quick Fix)
    try:
        # Check if column exists by trying to select it. If fails, add it.
        # SQLite doesn't have "IF NOT EXISTS" for columns easily, so LBYL or EAFP.
        # EAFP is safer here.
        session.execute(text("SELECT price FROM items LIMIT 1"))
    except Exception:
        session.rollback()
        print("Migrating schema: Adding 'price' column...")
        session.execute(text("ALTER TABLE items ADD COLUMN price FLOAT DEFAULT 0"))
        session.commit()
        
    try:
        session.execute(text("SELECT cost FROM items LIMIT 1"))
    except Exception:
        session.rollback()
        print("Migrating schema: Adding 'cost' column...")
        session.execute(text("ALTER TABLE items ADD COLUMN cost FLOAT DEFAULT 0"))
        session.commit()

    try:
        state, _ = repo.load_inventory_state()
        print(f"Found {len(state.items)} items.")
        
        updated_count = 0
        for item in state.items:
            # Generate random realistic values if missing
            if not item.price or item.price <= 0:
                item.price = round(random.uniform(10.0, 150.0), 2)
            
            if not item.cost or item.cost <= 0:
                # Cost is roughly 40-70% of price
                item.cost = round(item.price * random.uniform(0.4, 0.7), 2)
            
            # Update in DB
            # Note: InventoryState items are detached objects usually, need to merge or query
            db_item = session.query(ItemORM).filter_by(id=item.id).first()
            if db_item:
                db_item.price = item.price
                db_item.cost = item.cost
                updated_count += 1
                
        session.commit()
        print(f"Successfully updated financial data for {updated_count} items.")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
