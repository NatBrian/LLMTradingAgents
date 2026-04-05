#!/usr/bin/env python3
"""
Backtest trading agents over a date range using historical market data.

Example:
  python scripts/backtest_range.py --config config/arena.yaml --start 2026-03-01 --end 2026-04-01
"""

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import sys

# Ensure the package root is importable when running from the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from myllmtradingagents.settings import load_config
from myllmtradingagents.arena import ArenaRunner
from myllmtradingagents.market import create_market_adapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest agents over a date range.")
    parser.add_argument("--config", "-c", required=True, help="Path to arena config YAML")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--sessions",
        default="OPEN,CLOSE",
        help="Comma-separated sessions to run: OPEN,CLOSE (default: OPEN,CLOSE)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving to database or executing trades",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force run even if session already exists in DB",
    )
    return parser.parse_args()


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {value}. Use YYYY-MM-DD")


def should_run_for_date(market_adapters, session_date: date) -> bool:
    """Check if we should run for a given date.
    
    We need at least one equity market to be open (crypto is always open).
    Runs only 1 time a week (Monday) to conserve API calls.
    """
    # Only run on Monday (0)
    if session_date.weekday() != 0:
        return False

    has_equity_open = False
    for adapter in market_adapters:
        try:
            market_type = adapter.get_market_type()
            is_open = adapter.is_trading_day(session_date)
            # Equity markets must be open (crypto is always open)
            if market_type in ("us_equity", "sg_equity") and is_open:
                has_equity_open = True
        except Exception:
            continue
    return has_equity_open


def main() -> int:
    args = parse_args()

    try:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    if end_date < start_date:
        print("End date must be >= start date", file=sys.stderr)
        return 1

    sessions = [s.strip().upper() for s in args.sessions.split(",") if s.strip()]
    for s in sessions:
        if s not in ("OPEN", "CLOSE"):
            print(f"Invalid session: {s}. Use OPEN and/or CLOSE", file=sys.stderr)
            return 1

    arena_config = load_config(args.config)
    runner = ArenaRunner(arena_config)

    # Create adapters for trading-day checks
    market_adapters = []
    for market in arena_config.markets:
        try:
            adapter = create_market_adapter(market.type, cache_dir=arena_config.cache_dir)
            market_adapters.append(adapter)
        except Exception:
            continue

    current = start_date
    total_runs = 0
    total_skipped_days = 0

    while current <= end_date:
        if not should_run_for_date(market_adapters, current):
            total_skipped_days += 1
            current += timedelta(days=1)
            continue

        for session in sessions:
            print(f"Running {session} session for {current.isoformat()}...")
            results = runner.run_session(
                session_type=session,
                session_date=current,
                dry_run=args.dry_run,
                force=args.force,
            )

            # Compact summary per competitor
            for competitor_id, result in results.items():
                if "error" in result:
                    print(f"  {competitor_id}: ERROR: {result['error']}")
                elif result.get("skipped"):
                    print(f"  {competitor_id}: SKIPPED: {result.get('reason', 'unknown')}")
                else:
                    trades = len(result.get("fills", []))
                    before = result.get("equity_before", 0)
                    after = result.get("equity_after", 0)
                    print(f"  {competitor_id}: equity ${before:,.2f} -> ${after:,.2f}, trades={trades}")

            total_runs += 1

        current += timedelta(days=1)

    print(f"Done. Sessions run: {total_runs}, skipped days: {total_skipped_days}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
