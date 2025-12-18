# core/models.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
from typing import List, Dict, Optional, Union, Any


class ItemType(str, Enum):
    FINISHED = "finished"
    INGREDIENT = "ingredient"
    SEMI_FINISHED = "semi_finished"


class ItemClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class OperationMode(str, Enum):
    STRICT = "strict"
    DEMAND_ONLY = "demand_only"


class AlertSphere(str, Enum):
    PRODUCT = "product"
    INGREDIENT = "ingredient"
    PRODUCTION = "production"
    DATA_QUALITY = "data_quality"


class AlertPersona(str, Enum):
    KITCHEN = "kitchen"
    PURCHASING = "purchasing"
    MANAGEMENT = "management"


class AlertPriority(str, Enum):
    URGENT = "urgent"
    PLAN = "plan"
    INFO = "info"


class ReliabilityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Item:
    id: str
    name: str
    item_type: ItemType
    unit: str
    lead_time_days: float = 0.0
    shelf_life_days: Optional[float] = None
    item_class: ItemClass = ItemClass.B
    operation_mode: OperationMode = OperationMode.STRICT
    last_audit_date: Optional[date] = None


@dataclass
class Dish:
    id: str
    name: str
    prep_time_min: float = 0.0
    pre_prep_time_min: float = 0.0


@dataclass
class Recipe:
    parent_item_id: str
    child_item_id: str
    quantity: float


@dataclass
class StockLevel:
    item_id: str
    quantity: float
    lot_id: Optional[str] = None
    expires_at: Optional[date] = None
    updated_at: Optional[datetime] = None


@dataclass
class Sale:
    dish_id: str
    quantity: float
    timestamp: datetime


@dataclass
class Alert:
    id: str
    sphere: AlertSphere
    persona: AlertPersona
    priority: AlertPriority
    title: str
    message: str
    created_at: datetime

    estimated_impact: Optional[float] = None
    reliability_score: float = 1.0
    reliability: ReliabilityLevel = ReliabilityLevel.HIGH
    anomaly_flag: bool = False
    data_error: bool = False
    is_suppressed: bool = False

    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisContext:
    now: datetime
    coverage_days_target_A: float = 7.0
    coverage_days_target_B: float = 5.0
    coverage_days_target_C: float = 3.0
    perishable_risk_threshold_days: float = 2.0

    ignore_stock_balance: bool = False
    default_operation_mode: OperationMode = OperationMode.STRICT

    forecast_window_days: int = 30
    profile: str = "balanced"

    supplier_variability_finished: float = 1.5
    supplier_variability_ingredient: float = 1.3


@dataclass
class InventoryState:
    items: List[Item]
    dishes: List[Dish]
    recipes: List[Recipe]
    stock_levels: List[StockLevel]
    sales_history: List[Sale]
    today_sales: List[Sale]

    suppressed_alerts: Dict[str, Optional[datetime]] = field(default_factory=dict)
    alert_history: Dict[str, datetime] = field(default_factory=dict)
