# local_api/app.py

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from local_api.config import settings
from local_api.routes import health, alerts, ingest, todo, metrics, dashboard, engine_config, stock, events, planning
from local_api.schemas import ErrorResponse
from core.errors import InventoryEngineError

BASE_DIR = Path(__file__).resolve().parent
STATIC = BASE_DIR / "templates"


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        description="API local do motor de inteligência de estoque/produção.",
    )

    # Routers
    app.include_router(health.router)
    app.include_router(alerts.router)
    app.include_router(ingest.router)
    app.include_router(todo.router)
    app.include_router(metrics.router)
    app.include_router(dashboard.router)
    app.include_router(engine_config.router)
    app.include_router(stock.router)
    app.include_router(events.router)
    app.include_router(planning.router)

    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    # Handlers globais de erro
    @app.exception_handler(InventoryEngineError)
    async def inventory_engine_exception_handler(
        request: Request, exc: InventoryEngineError
    ):
        content = ErrorResponse(
            error_code="ENGINE_ERROR",
            detail="Ocorreu um erro ao processar a análise de estoque.",
        ).model_dump()
        return JSONResponse(status_code=500, content=content)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        content = ErrorResponse(
            error_code="INTERNAL_ERROR",
            detail="Erro interno inesperado.",
        ).model_dump()
        return JSONResponse(status_code=500, content=content)

    return app


app = create_app()
