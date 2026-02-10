# infra/orm_models.py

from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infra.db import Base

class ItemORM(Base):
    __tablename__ = "items"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    item_type: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    lead_time_days: Mapped[float] = mapped_column(Float, nullable=False)
    shelf_life_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    item_class: Mapped[str] = mapped_column(String, nullable=False)
    operation_mode: Mapped[str] = mapped_column(String, nullable=False)
    last_audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    stock_levels: Mapped[list["StockLevelORM"]] = relationship(back_populates="item", cascade="all, delete-orphan")

class StockLevelORM(Base):
    __tablename__ = "stock_levels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, ForeignKey("items.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    lot_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # NOVO: Data da atualização manual
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=datetime.now)
    item: Mapped[ItemORM] = relationship(back_populates="stock_levels")

class StockLotORM(Base):
    """Tabela de lotes (Esfera 4)."""
    __tablename__ = "stock_lots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, ForeignKey("items.id"), nullable=False, index=True)
    lot_id: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class SaleORM(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dish_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

class DishORM(Base):
    __tablename__ = "dishes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    prep_time_min: Mapped[float] = mapped_column(Float, default=0)
    pre_prep_time_min: Mapped[float] = mapped_column(Float, default=0)

class RecipeORM(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_item_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    child_item_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

class AlertSuppressionORM(Base):
    __tablename__ = "alert_suppressions"
    alert_id: Mapped[str] = mapped_column(String, primary_key=True)
    suppress_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

# NOVO MODELO
class AlertHistoryORM(Base):
    __tablename__ = "alert_history"
    alert_id: Mapped[str] = mapped_column(String, primary_key=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class EngineConfigORM(Base):
    __tablename__ = "engine_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False, default=1)
    profile: Mapped[str] = mapped_column(String, default="balanced")
    coverage_days_target_A: Mapped[float] = mapped_column(Float, default=7.0)
    coverage_days_target_B: Mapped[float] = mapped_column(Float, default=5.0)
    coverage_days_target_C: Mapped[float] = mapped_column(Float, default=3.0)
    perishable_risk_threshold_days: Mapped[float] = mapped_column(Float, default=2.0)
    supplier_variability_finished: Mapped[float] = mapped_column(Float, default=1.5)
    supplier_variability_ingredient: Mapped[float] = mapped_column(Float, default=1.3)
    forecast_window_days: Mapped[int] = mapped_column(Integer, default=30)


class StockAuditHistoryORM(Base):
    """Histórico de contagens manuais de estoque."""
    __tablename__ = "stock_audit_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, ForeignKey("items.id"), nullable=False, index=True)
    old_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    new_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    audited_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)

# --- TEMPORAL ADJUSTMENTS ---

class DowFactorORM(Base):
    __tablename__ = "dow_factors"
    item_id: Mapped[str] = mapped_column(String, ForeignKey("items.id"), primary_key=True)
    weekday: Mapped[int] = mapped_column(Integer, primary_key=True)
    factor: Mapped[float] = mapped_column(Float, default=1.0)
    n_samples: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class MonthFactorORM(Base):
    __tablename__ = "month_factors"
    item_id: Mapped[str] = mapped_column(String, ForeignKey("items.id"), primary_key=True)
    month: Mapped[int] = mapped_column(Integer, primary_key=True)
    factor: Mapped[float] = mapped_column(Float, default=1.0)
    n_samples: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class EventCalendarORM(Base):
    __tablename__ = "events_calendar"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    factor: Mapped[float] = mapped_column(Float, default=1.0)
    applies_to: Mapped[Optional[str]] = mapped_column(String, nullable=True) # JSON
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class BridgeRuleORM(Base):
    __tablename__ = "bridge_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    multiplier: Mapped[float] = mapped_column(Float, default=0.5)
    lookback_days: Mapped[int] = mapped_column(Integer, default=1)
    enabled: Mapped[int] = mapped_column(Integer, default=1)

class PaydayRuleORM(Base):
    __tablename__ = "payday_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rule_type: Mapped[str] = mapped_column(String, nullable=False) # 'fixed_day', 'last_business_day', 'fifth_business_day'
    multiplier: Mapped[float] = mapped_column(Float, default=1.10)
    enabled: Mapped[int] = mapped_column(Integer, default=1)

class FactorConfidenceORM(Base):
    __tablename__ = "factor_confidence"
    item_id: Mapped[str] = mapped_column(String, ForeignKey("items.id"), primary_key=True)
    factor_type: Mapped[str] = mapped_column(String, primary_key=True)
    confidence: Mapped[str] = mapped_column(String, nullable=False) # HIGH, MEDIUM, LOW
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)