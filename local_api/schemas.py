# local_api/schemas.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from datetime import date, datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    message: str


class AlertData(BaseModel):
    item_id: Optional[str] = None
    avg_daily_demand: Optional[float] = None
    current_stock: Optional[float] = None
    days_of_cover: Optional[float] = None
    lead_time_days: Optional[float] = None
    coverage_target_days: Optional[float] = None
    required_coverage_days: Optional[float] = None
    operation_mode: Optional[str] = None


# --- SEASONALITY / EVENTS ---
class EventBase(BaseModel):
    name: str
    date: date
    factor: float = 1.0
    applies_to: Optional[str] = None
    note: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: str
    sphere: str
    persona: str
    priority: str
    title: str
    message: str
    created_at: str
    estimated_impact: Optional[float] = None
    reliability_score: float
    reliability: str
    anomaly_flag: bool
    data_error: bool
    data: Dict[str, Any]


class ErrorResponse(BaseModel):
    error_code: str
    detail: str


class EngineConfigResponse(BaseModel):
    profile: str
    coverage_days_target_A: float
    coverage_days_target_B: float
    coverage_days_target_C: float
    perishable_risk_threshold_days: float
    supplier_variability_finished: float
    supplier_variability_ingredient: float
    forecast_window_days: int


class EngineProfileRequest(BaseModel):
    # Define o formato do JSON esperado: { "profile": "..." }
    profile: Literal["conservative", "balanced", "aggressive"]


class EngineConfigUpdate(BaseModel):
    profile: Optional[str] = None
    coverage_days_target_A: Optional[float] = None
    coverage_days_target_B: Optional[float] = None
    coverage_days_target_C: Optional[float] = None
    perishable_risk_threshold_days: Optional[float] = None
    supplier_variability_finished: Optional[float] = None
    supplier_variability_ingredient: Optional[float] = None
    forecast_window_days: Optional[int] = None