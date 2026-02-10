# local_api/routes/dashboard.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_OLD = BASE_DIR / "templates" / "dashboard" / "index.html"
STOCK_PAGE_OLD = BASE_DIR / "templates" / "dashboard" / "stock.html"
SPA_INDEX = BASE_DIR / "templates" / "spa_prototype" / "index.html"


# --- SPA Routes (Clean URLs) ---
# These serve the Vue.js SPA for history mode routing

@router.get("/spa", response_class=HTMLResponse)
@router.get("/spa/{path:path}", response_class=HTMLResponse)
async def spa_catchall(path: str = ""):
    """Serve SPA for all routes (history mode support)."""
    return SPA_INDEX.read_text(encoding="utf-8")


# --- Legacy MPA Routes (kept for backwards compatibility) ---

@router.get("/dashboard-old", response_class=HTMLResponse)
async def dashboard_old():
    """Old MPA dashboard (for comparison)."""
    return DASHBOARD_OLD.read_text(encoding="utf-8")


@router.get("/estoque-old", response_class=HTMLResponse)
async def stock_management_old():
    """Old MPA stock page (for comparison)."""
    return STOCK_PAGE_OLD.read_text(encoding="utf-8")


# --- Main Routes (now using SPA) ---

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard - SPA version."""
    return SPA_INDEX.read_text(encoding="utf-8")


@router.get("/estoque", response_class=HTMLResponse)
async def stock_management():
    """Stock management - SPA version."""
    return SPA_INDEX.read_text(encoding="utf-8")