"""
Settings and configuration loader for MyLLMTradingAgents.

Loads configuration from:
1. Environment variables (.env file)
2. YAML config file (arena config)
"""

import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv


# Load .env file from project root or current directory
load_dotenv()


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""
    provider: str  # "openrouter" or "gemini"
    model: str
    api_key: str = ""
    base_url: str = ""
    
    def __post_init__(self):
        if self.provider == "openrouter":
            self.api_key = self.api_key or os.getenv("OPENROUTER_API_KEY", "")
            self.base_url = self.base_url or "https://openrouter.ai/api/v1"
        elif self.provider == "gemini":
            self.api_key = self.api_key or os.getenv("GOOGLE_API_KEY", "")


@dataclass
class CompetitorConfig:
    """Configuration for a competitor in the arena."""
    id: str
    name: str
    provider: str
    model: str
    initial_cash: float = 100000.0
    max_position_pct: float = 0.25
    max_orders_per_run: int = 3


@dataclass
class MarketConfig:
    """Configuration for a market."""
    type: str  # "us_equity", "sg_equity", "crypto"
    tickers: list[str] = field(default_factory=list)
    timezone: str = "UTC"
    # For crypto: session times as HH:MM strings
    session_times: list[str] = field(default_factory=lambda: ["00:00", "12:00"])
    # For equities: optional manual open/close times
    open_time: str = ""
    close_time: str = ""


@dataclass
class SimulationConfig:
    """Simulation parameters."""
    slippage_bps: float = 10.0  # 10 basis points = 0.1%
    fee_bps: float = 10.0  # 10 basis points = 0.1%
    initial_cash: float = 100000.0
    max_position_pct: float = 0.25  # Max 25% of portfolio in single position
    max_orders_per_run: int = 3


@dataclass
class ArenaConfig:
    """Full arena configuration."""
    name: str = "MyLLMTradingAgents Arena"
    timezone: str = "UTC"
    db_path: str = "arena.db"
    cache_dir: str = "~/.myllmtradingagents/cache"
    markets: list[MarketConfig] = field(default_factory=list)
    competitors: list[CompetitorConfig] = field(default_factory=list)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    
    # Per-provider daily call limits (for budget control)
    daily_call_limits: dict[str, int] = field(default_factory=lambda: {
        "openrouter": 100,
        "gemini": 100,
    })

    def __post_init__(self):
        # Expand ~ in paths
        self.cache_dir = str(Path(self.cache_dir).expanduser())
        if not Path(self.db_path).is_absolute():
            # Keep relative db_path as-is
            pass


def load_config(config_path: str | Path) -> ArenaConfig:
    """Load arena configuration from YAML file."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)
    
    return parse_config(raw)


def parse_config(raw: dict[str, Any]) -> ArenaConfig:
    """Parse raw YAML dict into ArenaConfig."""
    # Parse markets
    markets = []
    for m in raw.get("markets", []):
        markets.append(MarketConfig(
            type=m.get("type", "us_equity"),
            tickers=m.get("tickers", []),
            timezone=m.get("timezone", "UTC"),
            session_times=m.get("session_times", ["00:00", "12:00"]),
            open_time=m.get("open_time", ""),
            close_time=m.get("close_time", ""),
        ))
    
    # Parse competitors
    competitors = []
    for c in raw.get("competitors", []):
        competitors.append(CompetitorConfig(
            id=c.get("id", c.get("name", "unknown").lower().replace(" ", "_")),
            name=c.get("name", "Unknown"),
            provider=c.get("provider", "openrouter"),
            model=c.get("model", ""),
            initial_cash=c.get("initial_cash", raw.get("simulation", {}).get("initial_cash", 100000.0)),
            max_position_pct=c.get("max_position_pct", raw.get("simulation", {}).get("max_position_pct", 0.25)),
            max_orders_per_run=c.get("max_orders_per_run", raw.get("simulation", {}).get("max_orders_per_run", 3)),
        ))
    
    # Parse simulation settings
    sim_raw = raw.get("simulation", {})
    simulation = SimulationConfig(
        slippage_bps=sim_raw.get("slippage_bps", 10.0),
        fee_bps=sim_raw.get("fee_bps", 10.0),
        initial_cash=sim_raw.get("initial_cash", 100000.0),
        max_position_pct=sim_raw.get("max_position_pct", 0.25),
        max_orders_per_run=sim_raw.get("max_orders_per_run", 3),
    )
    
    return ArenaConfig(
        name=raw.get("name", "MyLLMTradingAgents Arena"),
        timezone=raw.get("timezone", "UTC"),
        db_path=raw.get("db_path", "arena.db"),
        cache_dir=raw.get("cache_dir", "~/.myllmtradingagents/cache"),
        markets=markets,
        competitors=competitors,
        simulation=simulation,
        daily_call_limits=raw.get("daily_call_limits", {"openrouter": 100, "gemini": 100}),
    )


# Environment variable helpers
def get_openrouter_api_key() -> str:
    """Get OpenRouter API key from environment."""
    return os.getenv("OPENROUTER_API_KEY", "")


def get_google_api_key() -> str:
    """Get Google API key for Gemini from environment."""
    return os.getenv("GOOGLE_API_KEY", "")


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.getenv(key, default)
