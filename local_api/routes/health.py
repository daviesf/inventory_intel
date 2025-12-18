# local_api/routes/health.py

from __future__ import annotations

from fastapi import APIRouter

from local_api.config import settings
from local_api.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.api_version,
        message="Inventory Intel local API is running.",
    )
