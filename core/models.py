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
    PERISHABLE = "perishable"  # Legacy/Specific
    PERISHABILITY = "perishability"  # Actions/Management Sphere 4


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
    price: float = 0.0
    cost: float = 0.0
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
class StockLot:
    """Representação canônica de um lote (Esfera 4)."""
    lot_id: str
    item_id: str
    quantity: float
    expires_at: date


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
    
    lots: List[StockLot] = field(default_factory=list)

    suppressed_alerts: Dict[str, Optional[datetime]] = field(default_factory=dict)
    alert_history: Dict[str, datetime] = field(default_factory=dict)

    # TEMPORAL CACHES (Loaded on demand or init)
    dow_factors: Dict[str, Dict[int, float]] = field(default_factory=dict) # item_id -> {weekday: factor}
    month_factors: Dict[str, Dict[int, float]] = field(default_factory=dict) # item_id -> {month: factor}
    events: List[Event] = field(default_factory=list)
    bridge_rules: List[BridgeRule] = field(default_factory=list)
    payday_rules: List[PaydayRule] = field(default_factory=list)

@dataclass
class DowFactor:
    item_id: str
    weekday: int
    factor: float
    n_samples: int
    last_updated: datetime

@dataclass
class MonthFactor:
    item_id: str
    month: int
    factor: float
    n_samples: int
    last_updated: datetime

@dataclass
class Event:
    id: int
    name: str
    date: date
    factor: float
    applies_to: Optional[str] = None
    note: Optional[str] = None

@dataclass
class BridgeRule:
    id: int
    name: str
    multiplier: float
    lookback_days: int
    enabled: bool

@dataclass
class PaydayRule:
    id: int
    name: str
    day_of_month: Optional[int]
    rule_type: str
    multiplier: float
    enabled: bool

@dataclass
class FactorConfidence:
    item_id: str
    factor_type: str
    confidence: str
    computed_at: datetime

@dataclass
class TemporalBreakdown:
    item_id: str
    base_forecast: float
    forecast_final: float
    total_factor: float
    components: List[Dict[str, Any]]
    explanation: str
    confidence: str = "MEDIUM"
