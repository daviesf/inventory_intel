# local_api/routes/dashboard.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD = BASE_DIR / "templates" / "dashboard" / "index.html"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD.read_text(encoding="utf-8")