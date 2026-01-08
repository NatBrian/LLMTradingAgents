#!/usr/bin/env python3
"""
Export arena.db data to JSON for the React dashboard.

This script extracts all trading data and writes it to frontend/public/data.json.
It's designed to be run by GitHub Actions after each trading session.

Usage:
    python scripts/export_data.py --db arena.db --output frontend/public/data.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def safe_json_loads(data: Any, default: Any = None) -> Any:
    """Safely parse JSON string, returning default on failure."""
    if data is None:
        return default
    if not isinstance(data, str):
        return data
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def fetch_competitors(conn: sqlite3.Connection) -> dict[str, dict]:
    """Fetch all competitors."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitors")
    
    competitors = {}
    for row in cursor.fetchall():
        competitors[row['id']] = {
            'id': row['id'],
            'name': row['name'],
            'provider': row['provider'],
            'model': row['model'],
        }
    
    return competitors


def fetch_leaderboard(conn: sqlite3.Connection, competitors: dict) -> list[dict]:
    """Fetch leaderboard data with latest equity and returns."""
    cursor = conn.cursor()
    
    leaderboard = []
    for comp_id, comp in competitors.items():
        # Get latest snapshot
        cursor.execute("""
            SELECT equity FROM snapshots 
            WHERE competitor_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (comp_id,))
        latest = cursor.fetchone()
        current_equity = latest['equity'] if latest else 100000.0
        
        # Get initial equity (first snapshot)
        cursor.execute("""
            SELECT equity FROM snapshots 
            WHERE competitor_id = ? 
            ORDER BY timestamp ASC 
            LIMIT 1
        """, (comp_id,))
        first = cursor.fetchone()
        initial_equity = first['equity'] if first else current_equity
        
        total_return = (current_equity - initial_equity) / initial_equity if initial_equity > 0 else 0
        
        # Calculate max drawdown from equity history
        cursor.execute("""
            SELECT equity FROM snapshots 
            WHERE competitor_id = ? 
            ORDER BY timestamp ASC
        """, (comp_id,))
        equities = [r['equity'] for r in cursor.fetchall() if r['equity']]
        max_dd = calculate_max_drawdown(equities)
        
        # Count trades
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM trades WHERE competitor_id = ?
        """, (comp_id,))
        trade_count = cursor.fetchone()['cnt']
        
        leaderboard.append({
            'competitor_id': comp_id,
            'name': comp['name'],
            'provider': comp['provider'],
            'model': comp['model'],
            'current_equity': round(current_equity, 2),
            'total_return': round(total_return, 6),
            'max_drawdown': round(max_dd, 4),
            'num_trades': trade_count,
        })
    
    # Sort by total return descending
    leaderboard.sort(key=lambda x: x['total_return'], reverse=True)
    return leaderboard


def calculate_max_drawdown(equities: list[float]) -> float:
    """Calculate maximum drawdown from equity series."""
    if not equities or len(equities) < 2:
        return 0.0
    
    peak = equities[0]
    max_dd = 0.0
    
    for equity in equities:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    
    return max_dd


def fetch_equity_curves(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Fetch equity history for all competitors."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT competitor_id, timestamp, equity, cash
        FROM snapshots
        WHERE equity IS NOT NULL
        ORDER BY competitor_id, timestamp
    """)
    
    curves: dict[str, list[dict]] = {}
    for row in cursor.fetchall():
        comp_id = row['competitor_id']
        if comp_id not in curves:
            curves[comp_id] = []
        curves[comp_id].append({
            'timestamp': row['timestamp'],
            'equity': round(row['equity'], 2),
            'cash': round(row['cash'], 2) if row['cash'] else None,
        })
    
    return curves


def fetch_run_logs(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    """Fetch recent run logs with LLM calls."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, competitor_id, session_date, session_type, timestamp,
            llm_calls_json, strategist_proposal_json, trade_plan_json, 
            fills_json, errors_json,
            snapshot_before_json, snapshot_after_json
        FROM run_logs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    runs = []
    for row in cursor.fetchall():
        # Parse LLM calls
        llm_calls = safe_json_loads(row['llm_calls_json'], [])
        
        # Parse strategist proposal
        data = safe_json_loads(row['strategist_proposal_json'])
        strategist_proposal = None
        if data and 'proposals' in data:
            strategist_proposal = data
            
        # Parse trade plan
        trade_plan = safe_json_loads(row['trade_plan_json'])
        
        run = {
            'run_id': row['id'],
            'competitor_id': row['competitor_id'],
            'session_date': row['session_date'],
            'session_type': row['session_type'],
            'timestamp': row['timestamp'],
            'llm_calls': llm_calls,
            'strategist_proposal': strategist_proposal,
            'trade_plan': trade_plan,
            'fills': safe_json_loads(row['fills_json'], []),
            'errors': safe_json_loads(row['errors_json'], []),
            'snapshot_before': safe_json_loads(row['snapshot_before_json']),
            'snapshot_after': safe_json_loads(row['snapshot_after_json']),
        }
        runs.append(run)
    
    return runs


def fetch_trades(conn: sqlite3.Connection, limit: int = 200) -> list[dict]:
    """Fetch recent trades."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            timestamp, competitor_id, ticker, side, qty, price, fees, slippage, notional
        FROM trades
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    trades = []
    for row in cursor.fetchall():
        trades.append({
            'timestamp': row['timestamp'],
            'competitor_id': row['competitor_id'],
            'ticker': row['ticker'],
            'side': row['side'],
            'qty': row['qty'],
            'price': round(row['price'], 2),
            'notional': round(row['notional'], 2),
            'fees': round(row['fees'], 4) if row['fees'] else 0,
        })
    
    return trades


def fetch_snapshots(conn: sqlite3.Connection) -> dict[str, dict]:
    """Fetch latest snapshot for each competitor."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.competitor_id,
            s.timestamp,
            s.cash,
            s.positions_json,
            s.realized_pnl,
            s.equity
        FROM snapshots s
        INNER JOIN (
            SELECT competitor_id, MAX(timestamp) as max_ts
            FROM snapshots
            GROUP BY competitor_id
        ) latest ON s.competitor_id = latest.competitor_id AND s.timestamp = latest.max_ts
    """)
    
    snapshots = {}
    for row in cursor.fetchall():
        positions = safe_json_loads(row['positions_json'], [])
        
        # Enhance positions with calculated fields
        positions_value = 0.0
        unrealized_pnl = 0.0
        for pos in positions:
            mv = pos.get('market_value') or (pos.get('qty', 0) * pos.get('current_price', 0))
            pos['market_value'] = round(mv, 2)
            
            pnl = pos.get('unrealized_pnl') or (
                (pos.get('current_price', 0) - pos.get('avg_cost', 0)) * pos.get('qty', 0)
            )
            pos['unrealized_pnl'] = round(pnl, 2)
            
            cost = pos.get('avg_cost', 0)
            if cost > 0:
                pos['unrealized_pnl_pct'] = round(((pos.get('current_price', 0) / cost) - 1) * 100, 2)
            else:
                pos['unrealized_pnl_pct'] = 0
            
            positions_value += mv
            unrealized_pnl += pnl
        
        cash = row['cash'] if row['cash'] else 0
        equity = row['equity'] if row['equity'] else (cash + positions_value)
        
        snapshots[row['competitor_id']] = {
            'timestamp': row['timestamp'],
            'cash': round(cash, 2),
            'positions': positions,
            'realized_pnl': round(row['realized_pnl'] or 0, 2),
            'positions_value': round(positions_value, 2),
            'equity': round(equity, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
        }
    
    return snapshots


def get_metadata(conn: sqlite3.Connection) -> dict:
    """Get dashboard metadata."""
    cursor = conn.cursor()
    
    # Count competitors
    cursor.execute("SELECT COUNT(*) as cnt FROM competitors")
    total_competitors = cursor.fetchone()['cnt']
    
    # Count runs
    cursor.execute("SELECT COUNT(*) as cnt FROM run_logs")
    total_runs = cursor.fetchone()['cnt']
    
    # Count trades
    cursor.execute("SELECT COUNT(*) as cnt FROM trades")
    total_trades = cursor.fetchone()['cnt']
    
    return {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'totalCompetitors': total_competitors,
        'totalRuns': total_runs,
        'totalTrades': total_trades,
    }


def export_data(db_path: str, output_path: str) -> None:
    """Export all data to JSON file."""
    conn = get_connection(db_path)
    
    try:
        competitors = fetch_competitors(conn)
        
        data = {
            'metadata': get_metadata(conn),
            'leaderboard': fetch_leaderboard(conn, competitors),
            'equityCurves': fetch_equity_curves(conn),
            'runLogs': fetch_run_logs(conn),
            'trades': fetch_trades(conn),
            'snapshots': fetch_snapshots(conn),
        }
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Exported data to {output_path}")
        print(f"  - Competitors: {data['metadata']['totalCompetitors']}")
        print(f"  - Runs: {data['metadata']['totalRuns']}")
        print(f"  - Trades: {data['metadata']['totalTrades']}")
        print(f"  - Equity curve points: {sum(len(v) for v in data['equityCurves'].values())}")
        
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Export arena.db to JSON for dashboard')
    parser.add_argument('--db', default='arena.db', help='Path to arena.db')
    parser.add_argument('--output', default='frontend/public/data.json', help='Output JSON path')
    args = parser.parse_args()
    
    if not Path(args.db).exists():
        print(f"Error: Database not found: {args.db}")
        return 1
    
    export_data(args.db, args.output)
    return 0


if __name__ == '__main__':
    exit(main())
