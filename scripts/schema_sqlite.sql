-- scripts/schema_sqlite.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    item_type TEXT NOT NULL,
    unit TEXT NOT NULL,
    lead_time_days REAL NOT NULL,
    shelf_life_days REAL,
    item_class TEXT NOT NULL,
    operation_mode TEXT NOT NULL,
    last_audit_date TEXT
);

CREATE TABLE IF NOT EXISTS stock_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    lot_id TEXT,
    expires_at TEXT,
    updated_at TEXT,  -- NOVO: Data da última contagem/atualização manual
    FOREIGN KEY (item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dish_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dishes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    prep_time_min REAL DEFAULT 0,
    pre_prep_time_min REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_item_id TEXT NOT NULL,
    child_item_id TEXT NOT NULL,
    quantity REAL NOT NULL,
    FOREIGN KEY (child_item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS alert_suppressions (
    alert_id TEXT PRIMARY KEY,
    suppress_until TEXT,
    created_at TEXT NOT NULL
);

-- NOVA TABELA: Histórico de quando o alerta foi visto pela primeira vez
CREATE TABLE IF NOT EXISTS alert_history (
    alert_id TEXT PRIMARY KEY,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS engine_config (
    id INTEGER PRIMARY KEY,
    profile TEXT DEFAULT 'balanced',
    coverage_days_target_A REAL DEFAULT 7.0,
    coverage_days_target_B REAL DEFAULT 5.0,
    coverage_days_target_C REAL DEFAULT 3.0,
    perishable_risk_threshold_days REAL DEFAULT 2.0,
    supplier_variability_finished REAL DEFAULT 1.5,
    supplier_variability_ingredient REAL DEFAULT 1.3,
    forecast_window_days INTEGER DEFAULT 30
);