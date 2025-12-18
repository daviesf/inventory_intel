# infra/db.py

from __future__ import annotations
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


# Caminho absoluto e fixo do projeto
BASE_DIR = Path(__file__).resolve().parent.parent  # inventory_intel/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "inventory.db"

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db() -> None:
    # importa aqui, só quando a função for chamada
    from infra.orm_models import ItemORM, StockLevelORM, SaleORM, DishORM, RecipeORM, AlertSuppressionORM, EngineConfigORM

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print(f"Banco inicializado em: {DB_PATH}")
