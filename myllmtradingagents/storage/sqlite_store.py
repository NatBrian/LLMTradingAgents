"""
SQLite storage implementation.
"""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .base import Storage
from ..schemas import Snapshot, RunLog, Fill, Position


class SQLiteStorage(Storage):
    """SQLite storage implementation."""
    
    def __init__(self, db_path: str = "arena.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
    
    @property
    def conn(self) -> sqlite3.Connection:
        """Get database connection (lazy initialization)."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def initialize(self) -> None:
        """Create database tables."""
        schema = self._get_schema()
        self.conn.executescript(schema)
        self.conn.commit()
    
    def _get_schema(self) -> str:
        """Get SQL schema."""
        return """
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
        
        -- Daily call counters
        CREATE TABLE IF NOT EXISTS call_counters (
            provider TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (provider, date)
        );
        """
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    # ========================================================================
    # Competitor Management
    # ========================================================================
    
    def save_competitor(
        self,
        competitor_id: str,
        name: str,
        provider: str,
        model: str,
        config: Optional[dict] = None,
    ) -> None:
        """Save or update a competitor."""
        config_json = json.dumps(config) if config else None
        
        self.conn.execute("""
            INSERT OR REPLACE INTO competitors (id, name, provider, model, config_json)
            VALUES (?, ?, ?, ?, ?)
        """, (competitor_id, name, provider, model, config_json))
        self.conn.commit()
    
    def get_competitor(self, competitor_id: str) -> Optional[dict]:
        """Get competitor by ID."""
        row = self.conn.execute(
            "SELECT * FROM competitors WHERE id = ?",
            (competitor_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return dict(row)
    
    def list_competitors(self) -> list[dict]:
        """List all competitors."""
        rows = self.conn.execute("SELECT * FROM competitors").fetchall()
        return [dict(row) for row in rows]
    
    # ========================================================================
    # Snapshots
    # ========================================================================
    
    def save_snapshot(self, competitor_id: str, snapshot: Snapshot) -> None:
        """Save a portfolio snapshot."""
        positions_json = json.dumps([p.model_dump() for p in snapshot.positions])
        
        self.conn.execute("""
            INSERT INTO snapshots (competitor_id, timestamp, cash, positions_json, realized_pnl, equity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            competitor_id,
            snapshot.timestamp.isoformat(),
            snapshot.cash,
            positions_json,
            snapshot.realized_pnl,
            snapshot.equity,
        ))
        self.conn.commit()
    
    def get_latest_snapshot(self, competitor_id: str) -> Optional[Snapshot]:
        """Get the most recent snapshot for a competitor."""
        row = self.conn.execute("""
            SELECT * FROM snapshots
            WHERE competitor_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (competitor_id,)).fetchone()
        
        if not row:
            return None
        
        return self._row_to_snapshot(row)
    
    def get_equity_curve(
        self,
        competitor_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[Snapshot]:
        """Get equity curve for a competitor."""
        query = "SELECT * FROM snapshots WHERE competitor_id = ?"
        params = [competitor_id]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat() + "T23:59:59")
        
        query += " ORDER BY timestamp ASC"
        
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_snapshot(row) for row in rows]
    
    def _row_to_snapshot(self, row: sqlite3.Row) -> Snapshot:
        """Convert database row to Snapshot."""
        positions = []
        if row["positions_json"]:
            for p in json.loads(row["positions_json"]):
                positions.append(Position(**p))
        
        return Snapshot(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            cash=row["cash"],
            positions=positions,
            realized_pnl=row["realized_pnl"],
        )
    
    # ========================================================================
    # Run Logs
    # ========================================================================
    
    def save_run_log(self, run_log: RunLog) -> None:
        """Save a run log."""
        self.conn.execute("""
            INSERT OR REPLACE INTO run_logs (
                id, competitor_id, session_date, session_type, timestamp,
                llm_calls_json, analyst_report_json, trade_plan_json,
                fills_json, errors_json, snapshot_before_json, snapshot_after_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_log.run_id,
            run_log.competitor_id,
            run_log.session_date,
            run_log.session_type,
            run_log.timestamp.isoformat(),
            json.dumps([c.model_dump(mode='json') for c in run_log.llm_calls]),
            run_log.analyst_report.model_dump_json() if run_log.analyst_report else None,
            run_log.trade_plan.model_dump_json() if run_log.trade_plan else None,
            json.dumps([f.model_dump(mode='json') for f in run_log.fills]),
            json.dumps(run_log.errors),
            run_log.snapshot_before.model_dump_json() if run_log.snapshot_before else None,
            run_log.snapshot_after.model_dump_json() if run_log.snapshot_after else None,
        ))
        self.conn.commit()
    
    def get_run_log(self, run_id: str) -> Optional[RunLog]:
        """Get a run log by ID."""
        row = self.conn.execute(
            "SELECT * FROM run_logs WHERE id = ?",
            (run_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return self._row_to_run_log(row)
    
    def list_run_logs(
        self,
        competitor_id: Optional[str] = None,
        session_date: Optional[str] = None,
        limit: int = 100,
    ) -> list[RunLog]:
        """List run logs with optional filters."""
        query = "SELECT * FROM run_logs WHERE 1=1"
        params = []
        
        if competitor_id:
            query += " AND competitor_id = ?"
            params.append(competitor_id)
        
        if session_date:
            query += " AND session_date = ?"
            params.append(session_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_run_log(row) for row in rows]
    
    def _row_to_run_log(self, row: sqlite3.Row) -> RunLog:
        """Convert database row to RunLog."""
        from ..schemas import LLMCall, AnalystReport, TradePlan
        
        llm_calls = []
        if row["llm_calls_json"]:
            for c in json.loads(row["llm_calls_json"]):
                llm_calls.append(LLMCall(**c))
        
        analyst_report = None
        if row["analyst_report_json"]:
            analyst_report = AnalystReport.model_validate_json(row["analyst_report_json"])
        
        trade_plan = None
        if row["trade_plan_json"]:
            trade_plan = TradePlan.model_validate_json(row["trade_plan_json"])
        
        fills = []
        if row["fills_json"]:
            for f in json.loads(row["fills_json"]):
                # Handle datetime deserialization
                if "timestamp" in f and isinstance(f["timestamp"], str):
                    f["timestamp"] = datetime.fromisoformat(f["timestamp"])
                fills.append(Fill(**f))
        
        errors = json.loads(row["errors_json"]) if row["errors_json"] else []
        
        snapshot_before = None
        if row["snapshot_before_json"]:
            snapshot_before = Snapshot.model_validate_json(row["snapshot_before_json"])
        
        snapshot_after = None
        if row["snapshot_after_json"]:
            snapshot_after = Snapshot.model_validate_json(row["snapshot_after_json"])
        
        return RunLog(
            run_id=row["id"],
            competitor_id=row["competitor_id"],
            session_date=row["session_date"],
            session_type=row["session_type"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            llm_calls=llm_calls,
            analyst_report=analyst_report,
            trade_plan=trade_plan,
            fills=fills,
            errors=errors,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
        )
    
    # ========================================================================
    # Trades
    # ========================================================================
    
    def save_trade(self, competitor_id: str, fill: Fill) -> None:
        """Save a trade."""
        self.conn.execute("""
            INSERT INTO trades (
                competitor_id, timestamp, ticker, side, qty, price, fees, slippage, notional
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            competitor_id,
            fill.timestamp.isoformat(),
            fill.ticker,
            fill.side.value,
            fill.qty,
            fill.fill_price,
            fill.fees,
            fill.slippage,
            fill.notional,
        ))
        self.conn.commit()
    
    def get_trades(
        self,
        competitor_id: Optional[str] = None,
        ticker: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """Get trades with optional filters."""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if competitor_id:
            query += " AND competitor_id = ?"
            params.append(competitor_id)
        
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker.upper())
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat() + "T23:59:59")
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    # ========================================================================
    # Leaderboard
    # ========================================================================
    
    def get_leaderboard(self) -> list[dict]:
        """Get leaderboard with metrics for all competitors."""
        competitors = self.list_competitors()
        leaderboard = []
        
        for comp in competitors:
            competitor_id = comp["id"]
            
            # Get latest snapshot
            latest = self.get_latest_snapshot(competitor_id)
            current_equity = latest.equity if latest else 0.0
            
            # Get first snapshot for return calculation
            first_snap = self.conn.execute("""
                SELECT equity FROM snapshots
                WHERE competitor_id = ?
                ORDER BY timestamp ASC
                LIMIT 1
            """, (competitor_id,)).fetchone()
            
            starting_equity = first_snap["equity"] if first_snap else current_equity
            total_return = (current_equity - starting_equity) / starting_equity if starting_equity > 0 else 0.0
            
            # Get trade count
            trade_count = self.conn.execute(
                "SELECT COUNT(*) as cnt FROM trades WHERE competitor_id = ?",
                (competitor_id,)
            ).fetchone()["cnt"]
            
            # Calculate max drawdown from equity curve
            snapshots = self.get_equity_curve(competitor_id)
            max_dd = 0.0
            if snapshots:
                import numpy as np
                equity_array = np.array([s.equity for s in snapshots])
                if len(equity_array) > 1:
                    running_max = np.maximum.accumulate(equity_array)
                    drawdowns = (running_max - equity_array) / running_max
                    max_dd = float(np.max(drawdowns[np.isfinite(drawdowns)]))
            
            leaderboard.append({
                "competitor_id": competitor_id,
                "name": comp["name"],
                "provider": comp["provider"],
                "model": comp["model"],
                "current_equity": current_equity,
                "total_return": total_return,
                "max_drawdown": max_dd,
                "num_trades": trade_count,
            })
        
        # Sort by total return descending
        leaderboard.sort(key=lambda x: x["total_return"], reverse=True)
        
        return leaderboard
    
    # ========================================================================
    # Session Tracking
    # ========================================================================
    
    def has_run_today(
        self,
        competitor_id: str,
        session_date: str,
        session_type: str,
    ) -> bool:
        """Check if a session has already run today."""
        row = self.conn.execute("""
            SELECT COUNT(*) as cnt FROM run_logs
            WHERE competitor_id = ? AND session_date = ? AND session_type = ?
        """, (competitor_id, session_date, session_type)).fetchone()
        
        return row["cnt"] > 0
    
    # ========================================================================
    # Call Counters
    # ========================================================================
    
    def get_daily_call_count(self, provider: str, date: str) -> int:
        """Get number of LLM calls for a provider on a date."""
        row = self.conn.execute(
            "SELECT count FROM call_counters WHERE provider = ? AND date = ?",
            (provider, date)
        ).fetchone()
        
        return row["count"] if row else 0
    
    def increment_call_count(self, provider: str, date: str, count: int = 1) -> None:
        """Increment call count for a provider on a date."""
        self.conn.execute("""
            INSERT INTO call_counters (provider, date, count)
            VALUES (?, ?, ?)
            ON CONFLICT(provider, date) DO UPDATE SET count = count + ?
        """, (provider, date, count, count))
        self.conn.commit()
