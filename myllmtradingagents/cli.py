"""
CLI entrypoint for MyLLMTradingAgents.

Usage:
    python -m myllmtradingagents.cli run --config config/arena.yaml --session OPEN
    python -m myllmtradingagents.cli run --config config/arena.yaml --session CLOSE
    python -m myllmtradingagents.cli dashboard --port 8501
    python -m myllmtradingagents.cli init-db --config config/arena.yaml
    python -m myllmtradingagents.cli status --config config/arena.yaml
"""

import sys
from datetime import date, datetime
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="myllmtradingagents")
def main():
    """MyLLMTradingAgents - Minimal LLM Trading Arena"""
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    
    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


@main.command()
@click.option(
    "--config", "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to arena config YAML file",
)
@click.option(
    "--session", "-s",
    required=True,
    type=click.Choice(["OPEN", "CLOSE"], case_sensitive=False),
    help="Session type: OPEN or CLOSE",
)
@click.option(
    "--date", "-d",
    default=None,
    help="Trading date (YYYY-MM-DD), defaults to today",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run without saving to database or executing trades",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force run even if session already ran today",
)
def run(config: str, session: str, date: str, dry_run: bool, force: bool):
    """Run a trading session for all competitors."""
    from .settings import load_config
    from .arena import ArenaRunner
    
    # Load config
    arena_config = load_config(config)
    
    # Parse date
    session_date = None
    if date:
        try:
            session_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            click.echo(f"Invalid date format: {date}. Use YYYY-MM-DD", err=True)
            sys.exit(1)
    
    # Create runner
    runner = ArenaRunner(arena_config)
    
    # Run session
    click.echo(f"Running {session.upper()} session...")
    
    if dry_run:
        click.echo("(DRY RUN - no trades will be executed or saved)")
    
    results = runner.run_session(
        session_type=session.upper(),
        session_date=session_date,
        dry_run=dry_run,
    )
    
    # Print results
    click.echo("\n" + "="*60)
    click.echo("RESULTS")
    click.echo("="*60)
    
    for competitor_id, result in results.items():
        click.echo(f"\n{competitor_id}:")
        
        if "error" in result:
            click.echo(f"  ERROR: {result['error']}")
        elif result.get("skipped"):
            click.echo(f"  SKIPPED: {result.get('reason', 'unknown')}")
        else:
            click.echo(f"  Run ID: {result.get('run_id', 'N/A')}")
            click.echo(f"  Equity: ${result.get('equity_before', 0):,.2f} -> ${result.get('equity_after', 0):,.2f}")
            click.echo(f"  Trades: {len(result.get('fills', []))}")
            
            if result.get("errors"):
                click.echo(f"  Errors: {result['errors']}")


@main.command()
@click.option(
    "--config", "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to arena config YAML file",
)
def init_db(config: str):
    """Initialize the database with schema."""
    from .settings import load_config
    from .storage import SQLiteStorage
    
    arena_config = load_config(config)
    
    storage = SQLiteStorage(arena_config.db_path)
    storage.initialize()
    
    click.echo(f"Database initialized: {arena_config.db_path}")
    
    # Initialize competitors
    for comp in arena_config.competitors:
        storage.save_competitor(
            competitor_id=comp.id,
            name=comp.name,
            provider=comp.provider,
            model=comp.model,
            config={
                "initial_cash": comp.initial_cash,
                "max_position_pct": comp.max_position_pct,
            },
        )
        click.echo(f"  Added competitor: {comp.name}")
    
    click.echo("Done!")


@main.command()
@click.option(
    "--config", "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to arena config YAML file",
)
def status(config: str):
    """Show current arena status."""
    from .settings import load_config
    from .storage import SQLiteStorage
    
    arena_config = load_config(config)
    
    storage = SQLiteStorage(arena_config.db_path)
    storage.initialize()
    
    click.echo(f"\nArena: {arena_config.name}")
    click.echo(f"Database: {arena_config.db_path}")
    click.echo(f"Timezone: {arena_config.timezone}")
    
    click.echo(f"\nMarkets ({len(arena_config.markets)}):")
    for market in arena_config.markets:
        click.echo(f"  - {market.type}: {len(market.tickers)} tickers")
    
    click.echo(f"\nCompetitors ({len(arena_config.competitors)}):")
    
    leaderboard = storage.get_leaderboard()
    
    if leaderboard:
        click.echo("\n{:<20} {:<15} {:>12} {:>10} {:>8}".format(
            "Name", "Model", "Equity", "Return", "Trades"
        ))
        click.echo("-" * 70)
        
        for entry in leaderboard:
            click.echo("{:<20} {:<15} ${:>10,.0f} {:>+9.2%} {:>8}".format(
                entry["name"][:20],
                entry["model"][:15],
                entry["current_equity"],
                entry["total_return"],
                entry["num_trades"],
            ))
    else:
        for comp in arena_config.competitors:
            click.echo(f"  - {comp.name} ({comp.provider}/{comp.model})")


@main.command()
@click.option(
    "--port", "-p",
    default=8501,
    type=int,
    help="Port for dashboard (default: 8501)",
)
@click.option(
    "--config", "-c",
    default="config/arena.yaml",
    help="Path to arena config YAML file",
)
def dashboard(port: int, config: str):
    """Launch the Streamlit dashboard."""
    import subprocess
    
    dashboard_path = Path(__file__).parent.parent / "dashboard" / "streamlit_app.py"
    
    if not dashboard_path.exists():
        click.echo(f"Dashboard not found at: {dashboard_path}", err=True)
        sys.exit(1)
    
    click.echo(f"Launching dashboard on port {port}...")
    click.echo(f"Open http://localhost:{port} in your browser")
    
    # Set config path as environment variable
    import os
    os.environ["MYLLM_CONFIG_PATH"] = str(config)
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", str(port),
        "--server.headless", "true",
    ])


@main.command()
@click.option(
    "--config", "-c",
    required=True,
    type=click.Path(exists=True),
    help="Path to arena config YAML file",
)
def next_session(config: str):
    """Show when the next trading session will run."""
    from .settings import load_config
    from .arena import SessionGate
    
    arena_config = load_config(config)
    gate = SessionGate(arena_config)
    
    result = gate.get_next_session()
    
    if result:
        market_type, session_type, session_time = result
        click.echo(f"\nNext session:")
        click.echo(f"  Market: {market_type}")
        click.echo(f"  Type: {session_type}")
        click.echo(f"  Time: {session_time}")
    else:
        click.echo("No upcoming sessions found")


if __name__ == "__main__":
    main()
