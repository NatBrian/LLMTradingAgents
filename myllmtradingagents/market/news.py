"""
Optional news headline fetcher (fail-soft).

Provides basic news scraping for ticker context.
Falls back gracefully if unavailable.
"""

from datetime import datetime
from typing import Optional, List, Dict
import logging
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_headlines(
    ticker: str,
    max_headlines: int = 5,
    days_back: int = 3,
) -> List[str]:
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
    except Exception as e:
        logger.debug(f"Failed to fetch yfinance news for {ticker}: {e}", extra={"ticker": ticker})
        pass
    
    return headlines[:max_headlines]


def fetch_news_articles(
    ticker: str,
    limit: int = 5,
) -> List[Dict]:
    """
    Fetch news articles with metadata from yfinance.
    
    Args:
        ticker: Ticker symbol
        limit: Max articles to return
        
    Returns:
        List of dicts with: source, date, headline, summary, url
    """
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        logger.debug(f"Fetching news for {ticker}...", extra={"ticker": ticker})
        news = ticker_obj.news
        logger.debug(f"Fetched {len(news) if news else 0} news items for {ticker}", extra={"ticker": ticker, "count": len(news) if news else 0})
        
        if not news or not isinstance(news, list):
            return []
        
        articles = []
        for item in news[:limit]:
            # Extract timestamp
            ts = item.get("providerPublishTime", 0)
            date_str = ""
            if ts:
                date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            
            article = {
                "source": item.get("publisher", "Yahoo Finance"),
                "date": date_str,
                "headline": item.get("title", ""),
                "summary": "",  # yfinance often doesn't provide summary in the main list
                "url": item.get("link", ""),
            }
            
            if article["headline"]:
                articles.append(article)
        
        return articles
        
    except Exception as e:
        logger.warning(f"Error fetching news articles for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        return []


def _fetch_yfinance_news(ticker: str, max_headlines: int = 5) -> List[str]:
    """Fetch news headlines from yfinance (legacy helper)."""
    articles = fetch_news_articles(ticker, limit=max_headlines)
    return [a["headline"] for a in articles]


def fetch_headlines_batch(
    tickers: List[str],
    max_per_ticker: int = 5,
) -> Dict[str, List[str]]:
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
        except Exception as e:
            logger.warning(f"Error fetching headlines for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
            result[ticker.upper()] = []
    
    return result
