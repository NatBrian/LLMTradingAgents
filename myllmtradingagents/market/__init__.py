"""Market data adapters for MyLLMTradingAgents."""

from .base import MarketAdapter
from .equity import USEquityAdapter, SGEquityAdapter
from .crypto import CryptoAdapter
from .features import compute_features

# New data modules
from .fundamentals import FundamentalsData, fetch_fundamentals, fetch_fundamentals_batch
from .earnings import EarningsData, fetch_earnings_calendar, fetch_earnings_calendar_batch
from .insider import InsiderData, InsiderTransaction, fetch_insider_transactions, fetch_insider_transactions_batch
from .price_history import PriceHistoryData, PriceBar, fetch_price_history, fetch_price_history_batch
from .briefing_builder import MarketBriefing, build_market_briefing

# Optional Alpha Vantage integration (requires ALPHA_VANTAGE_API_KEY)
from .alpha_vantage import (
    NewsSentimentData,
    fetch_news_sentiment,
    format_news_for_prompt,
    is_available as is_alpha_vantage_available,
)

__all__ = [
    # Market adapters
    "MarketAdapter",
    "USEquityAdapter",
    "SGEquityAdapter",
    "CryptoAdapter",
    "create_market_adapter",
    "compute_features",
    
    # Fundamentals
    "FundamentalsData",
    "fetch_fundamentals",
    "fetch_fundamentals_batch",
    
    # Earnings
    "EarningsData",
    "fetch_earnings_calendar",
    "fetch_earnings_calendar_batch",
    
    # Insider transactions
    "InsiderData",
    "InsiderTransaction",
    "fetch_insider_transactions",
    "fetch_insider_transactions_batch",
    
    # Price history
    "PriceHistoryData",
    "PriceBar",
    "fetch_price_history",
    "fetch_price_history_batch",
    
    # Briefing builder
    "MarketBriefing",
    "build_market_briefing",
    
    # Alpha Vantage (optional)
    "NewsSentimentData",
    "fetch_news_sentiment",
    "format_news_for_prompt",
    "is_alpha_vantage_available",
]


def create_market_adapter(market_type: str, **kwargs) -> MarketAdapter:
    """Factory function to create market adapter by type."""
    market_type = market_type.lower()
    
    if market_type == "us_equity":
        return USEquityAdapter(**kwargs)
    elif market_type == "sg_equity":
        return SGEquityAdapter(**kwargs)
    elif market_type == "crypto":
        return CryptoAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown market type: {market_type}. Supported: us_equity, sg_equity, crypto")

