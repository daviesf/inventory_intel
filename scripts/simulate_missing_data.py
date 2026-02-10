from infra.db import SessionLocal
from sqlalchemy import text

def simulate_missing_data():
    session = SessionLocal()
    try:
        # Set price to 0 for Coca Cola KS to test "Rupture Risk" missing price
        # Set cost to 0 for Alho to test "Idle Capital" missing cost
        print("Simulating missing data...")
        session.execute(text("UPDATE items SET price = 0 WHERE id = 'item_coca_ks'"))
        session.execute(text("UPDATE items SET cost = 0 WHERE id = 'ing_alho'"))
        session.commit()
        print("Price for 'item_coca_ks' set to 0.")
        print("Cost for 'ing_alho' set to 0.")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    simulate_missing_data()
