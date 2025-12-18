# demo_repo_sqlalchemy.py

from __future__ import annotations

from core.repository_sqlalchemy import SqlAlchemyInventoryRepository
from core import analyze_inventory


def main():
    repo = SqlAlchemyInventoryRepository()
    state, ctx = repo.load_inventory_state()

    print("=== STATE (resumido) ===")
    print(f"Itens:       {len(state.items)}")
    print(f"Estoque:     {len(state.stock_levels)} registros")
    print(f"Sales hist.: {len(state.sales_history)} vendas")

    alerts = analyze_inventory(state, ctx)

    print("\n=== ALERTAS GERADOS ===")
    for a in alerts:
        print("-" * 60)
        print(f"{a.id} | {a.priority.value} | {a.title}")

if __name__ == "__main__":
    main()
