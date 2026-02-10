import sqlite3
from pathlib import Path
import sys

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "inventory.db"
MIGRATION_FILE = BASE_DIR / "migrations" / "001_add_temporal_tables.sql"

def main():
    print(f"Applying migration from {MIGRATION_FILE} to {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)
        
    if not MIGRATION_FILE.exists():
        print(f"Migration file not found at {MIGRATION_FILE}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(DB_PATH)
        with open(MIGRATION_FILE, 'r') as f:
            sql_script = f.read()
            
        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
