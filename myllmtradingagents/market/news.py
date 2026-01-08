"""
Optional news headline fetcher (fail-soft).

Provides basic news scraping for ticker context.
Falls back gracefully if unavailable.
"""

from datetime import datetime
from typing import Optional
import os


def fetch_headlines(
    ticker: str,
    max_headlines: int = 5,
    days_back: int = 3,
) -> list[str]:
    """
    Fetch recent news headlines for a ticker.
    
    This is a fail-soft function - returns empty list on any error.
    
    Args:
        ticker: Ticker symbol
        max_headlines: Maximum headlines to return
        days_back: How many days back to search
        
    Returns:
        List of headline strings (may be empty)
    """
    headlines = []
    
    # Try yfinance news first (most reliable)
    try:
        headlines = _fetch_yfinance_news(ticker, max_headlines)
        if headlines:
            return headlines[:max_headlines]
    except Exception:
        pass
    
    return headlines[:max_headlines]


def _fetch_yfinance_news(ticker: str, max_headlines: int = 5) -> list[str]:
    """Fetch news from yfinance."""
    try:
        import yfinance as yf
        
        ticker_obj = yf.Ticker(ticker.upper())
        news = ticker_obj.news
        
        if not news:
            return []
        
        headlines = []
        for item in news[:max_headlines]:
            title = item.get("title", "")
            if title:
                headlines.append(title)
        
        return headlines
        
    except Exception:
        return []


def fetch_headlines_batch(
    tickers: list[str],
    max_per_ticker: int = 5,
) -> dict[str, list[str]]:
    """
    Fetch headlines for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        max_per_ticker: Max headlines per ticker
        
    Returns:
        Dict mapping ticker -> list of headlines
    """
    result = {}
    
    for ticker in tickers:
        try:
            headlines = fetch_headlines(ticker, max_per_ticker)
            result[ticker.upper()] = headlines
        except Exception:
            result[ticker.upper()] = []
    
    return result
