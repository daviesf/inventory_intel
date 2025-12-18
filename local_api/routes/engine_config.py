# local_api/routes/engine_config.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from infra.db import SessionLocal
from infra.orm_models import EngineConfigORM
from local_api.schemas import EngineConfigResponse, EngineConfigUpdate, EngineProfileRequest

router = APIRouter(prefix="/config/engine", tags=["config"])

def _apply_profile_defaults(cfg: EngineConfigORM, profile: str) -> None:
    profile = profile.lower()
    if profile == "conservative":
        cfg.profile = "conservative"
        cfg.coverage_days_target_A = 10.0
        cfg.coverage_days_target_B = 7.0
        cfg.coverage_days_target_C = 5.0
        cfg.perishable_risk_threshold_days = 1.0
        cfg.supplier_variability_finished = 1.7
        cfg.supplier_variability_ingredient = 1.5
        cfg.forecast_window_days = 60
    elif profile == "aggressive":
        cfg.profile = "aggressive"
        cfg.coverage_days_target_A = 5.0
        cfg.coverage_days_target_B = 3.0
        cfg.coverage_days_target_C = 2.0
        cfg.perishable_risk_threshold_days = 3.0
        cfg.supplier_variability_finished = 1.3
        cfg.supplier_variability_ingredient = 1.2
        cfg.forecast_window_days = 30
    else:  # balanced
        cfg.profile = "balanced"
        cfg.coverage_days_target_A = 7.0
        cfg.coverage_days_target_B = 5.0
        cfg.coverage_days_target_C = 3.0
        cfg.perishable_risk_threshold_days = 2.0
        cfg.supplier_variability_finished = 1.5
        cfg.supplier_variability_ingredient = 1.3
        cfg.forecast_window_days = 45

def _get_singleton_config(session) -> EngineConfigORM:
    cfg = session.get(EngineConfigORM, 1)
    if cfg is None:
        cfg = EngineConfigORM(id=1)
        session.add(cfg)
        session.commit()
        session.refresh(cfg)
    return cfg

@router.get("", response_model=EngineConfigResponse)
async def get_engine_config() -> EngineConfigResponse:
    with SessionLocal() as session:
        cfg = _get_singleton_config(session)
        return EngineConfigResponse(
            profile=cfg.profile,
            coverage_days_target_A=cfg.coverage_days_target_A,
            coverage_days_target_B=cfg.coverage_days_target_B,
            coverage_days_target_C=cfg.coverage_days_target_C,
            perishable_risk_threshold_days=cfg.perishable_risk_threshold_days,
            supplier_variability_finished=cfg.supplier_variability_finished,
            supplier_variability_ingredient=cfg.supplier_variability_ingredient,
            forecast_window_days=cfg.forecast_window_days,
        )

@router.put("/profile", response_model=EngineConfigResponse)
async def set_engine_profile(body: EngineProfileRequest) -> EngineConfigResponse:
    with SessionLocal() as session:
        cfg = _get_singleton_config(session)
        try:
            _apply_profile_defaults(cfg, body.profile)
            session.add(cfg)
            session.commit()
            session.refresh(cfg)
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        return EngineConfigResponse(
            profile=cfg.profile,
            coverage_days_target_A=cfg.coverage_days_target_A,
            coverage_days_target_B=cfg.coverage_days_target_B,
            coverage_days_target_C=cfg.coverage_days_target_C,
            perishable_risk_threshold_days=cfg.perishable_risk_threshold_days,
            supplier_variability_finished=cfg.supplier_variability_finished,
            supplier_variability_ingredient=cfg.supplier_variability_ingredient,
            forecast_window_days=cfg.forecast_window_days,
        )

@router.patch("", response_model=EngineConfigResponse)
async def update_engine_config(payload: EngineConfigUpdate) -> EngineConfigResponse:
    with SessionLocal() as session:
        cfg = _get_singleton_config(session)
        if payload.profile is not None:
            cfg.profile = payload.profile.lower()
        for field_name, value in payload.model_dump(exclude_unset=True).items():
            if field_name == "profile": continue
            setattr(cfg, field_name, value)
        try:
            session.add(cfg)
            session.commit()
            session.refresh(cfg)
        except SQLAlchemyError as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        return EngineConfigResponse(
            profile=cfg.profile,
            coverage_days_target_A=cfg.coverage_days_target_A,
            coverage_days_target_B=cfg.coverage_days_target_B,
            coverage_days_target_C=cfg.coverage_days_target_C,
            perishable_risk_threshold_days=cfg.perishable_risk_threshold_days,
            supplier_variability_finished=cfg.supplier_variability_finished,
            supplier_variability_ingredient=cfg.supplier_variability_ingredient,
            forecast_window_days=cfg.forecast_window_days,
        )