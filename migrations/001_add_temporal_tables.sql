-- Migration: Add Temporal Adjustment Tables
-- Date: 2024-01-03
-- Purpose: Support DOW, Month, Events, Bridge Days, and Payday logic.

-- 1. Day of Week Factors
CREATE TABLE IF NOT EXISTS dow_factors (
    item_id TEXT NOT NULL,
    weekday INTEGER NOT NULL, -- 0=Monday, 6=Sunday
    factor REAL NOT NULL DEFAULT 1.0,
    n_samples INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id, weekday),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 2. Month Factors
CREATE TABLE IF NOT EXISTS month_factors (
    item_id TEXT NOT NULL,
    month INTEGER NOT NULL, -- 1=Jan, 12=Dec
    factor REAL NOT NULL DEFAULT 1.0,
    n_samples INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id, month),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 3. Events Calendar
CREATE TABLE IF NOT EXISTS events_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date DATE NOT NULL,
    factor REAL NOT NULL DEFAULT 1.0,
    applies_to TEXT, -- JSON or null (e.g. {"category": "ABC"} or ["item1", "item2"])
    note TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_date ON events_calendar(date);

-- 4. Bridge Rules
-- Rules for "enforcado" / prolonged holidays
CREATE TABLE IF NOT EXISTS bridge_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    multiplier REAL DEFAULT 0.5, -- Impact on the bridge day
    lookback_days INTEGER DEFAULT 1, -- How many days before/after event to check
    enabled INTEGER DEFAULT 1 -- Boolean 0/1
);

-- 5. Payday Rules
-- Configurable rules for payday spikes
CREATE TABLE IF NOT EXISTS payday_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    day_of_month INTEGER, -- Specific day (e.g. 5, 30) or null if dynamic
    rule_type TEXT NOT NULL, -- 'fixed_day', 'last_business_day', 'fifth_business_day'
    multiplier REAL DEFAULT 1.10,
    enabled INTEGER DEFAULT 1 -- Boolean 0/1
);

-- 6. Factor Confidence
-- Store confidence level for audit/display
CREATE TABLE IF NOT EXISTS factor_confidence (
    item_id TEXT NOT NULL,
    factor_type TEXT NOT NULL, -- 'dow', 'month'
    confidence TEXT NOT NULL, -- 'HIGH', 'MEDIUM', 'LOW'
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id, factor_type),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- Seed Default Rules
INSERT OR IGNORE INTO bridge_rules (name, multiplier, lookback_days, enabled)
VALUES ('Default Bridge Day', 0.5, 1, 1);

INSERT OR IGNORE INTO payday_rules (name, day_of_month, rule_type, multiplier, enabled)
VALUES ('Fifth Business Day', NULL, 'fifth_business_day', 1.10, 0); 
-- Default disabled, user must enable
