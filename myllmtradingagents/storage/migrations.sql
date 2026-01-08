-- MyLLMTradingAgents SQLite Schema
-- Version: 1.0.0

-- Competitors table
CREATE TABLE IF NOT EXISTS competitors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    config_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio snapshots
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    cash REAL NOT NULL,
    positions_json TEXT,
    realized_pnl REAL DEFAULT 0,
    equity REAL NOT NULL,
    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_competitor ON snapshots(competitor_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp);

-- Run logs
CREATE TABLE IF NOT EXISTS run_logs (
    id TEXT PRIMARY KEY,
    competitor_id TEXT NOT NULL,
    session_date TEXT NOT NULL,
    session_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    llm_calls_json TEXT,
    analyst_report_json TEXT,
    trade_plan_json TEXT,
    fills_json TEXT,
    errors_json TEXT,
    snapshot_before_json TEXT,
    snapshot_after_json TEXT,
    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
);
CREATE INDEX IF NOT EXISTS idx_run_logs_competitor ON run_logs(competitor_id);
CREATE INDEX IF NOT EXISTS idx_run_logs_date ON run_logs(session_date);

-- Trade history
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    price REAL NOT NULL,
    fees REAL DEFAULT 0,
    slippage REAL DEFAULT 0,
    notional REAL NOT NULL,
    FOREIGN KEY (competitor_id) REFERENCES competitors(id)
);
CREATE INDEX IF NOT EXISTS idx_trades_competitor ON trades(competitor_id);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);

-- Daily call counters (for budget enforcement)
CREATE TABLE IF NOT EXISTS call_counters (
    provider TEXT NOT NULL,
    date TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (provider, date)
);
