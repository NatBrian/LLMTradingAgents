"""
Alpha Vantage integration for enhanced news sentiment.

This is an OPTIONAL enhancement that provides:
- News articles with sentiment scores from Alpha Vantage's NLP
- Insider transactions with more detail

RATE LIMITS (Free Tier):
- 5 requests per minute
- 25 requests per day

We use caching to stay within limits:
- Cache news/sentiment for 24 hours
- Only fetch once per ticker per day
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, field
import requests
import logging

logger = logging.getLogger(__name__)


# Alpha Vantage API configuration
API_BASE_URL = "https://www.alphavantage.co/query"


@dataclass
class NewsSentimentData:
    """
    News with sentiment data from Alpha Vantage.
    
    The sentiment scores are computed by Alpha Vantage's NLP.
    """
    ticker: str
    articles: List[dict] = field(default_factory=list)
    overall_sentiment_score: Optional[float] = None  # -1.0 to 1.0
    overall_sentiment_label: Optional[str] = None  # Bearish, Bullish, Neutral
    
    # Counts
    total_articles: int = 0
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0


def get_api_key() -> Optional[str]:
    """Get Alpha Vantage API key from environment."""
    return os.getenv("ALPHA_VANTAGE_API_KEY")


def is_available() -> bool:
    """Check if Alpha Vantage is configured."""
    return get_api_key() is not None


def _get_cache_dir() -> Path:
    """Get or create the cache directory."""
    cache_dir = Path.home() / ".myllmtradingagents" / "cache" / "alphavantage"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_key(ticker: str, endpoint: str, date: str) -> str:
    """Generate a cache key for a request."""
    key = f"{ticker}_{endpoint}_{date}"
    return hashlib.md5(key.encode()).hexdigest()


def _get_cached(ticker: str, endpoint: str, date: str) -> Optional[dict]:
    """Get cached response if available and not expired (24 hours)."""
    cache_dir = _get_cache_dir()
    cache_key = _get_cache_key(ticker, endpoint, date)
    cache_file = cache_dir / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cached = json.load(f)
            
            # Check if cache is still valid (24 hours)
            cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now() - cached_time < timedelta(hours=24):
                return cached.get("data")
        except Exception:
            pass
    
    return None


def _save_to_cache(ticker: str, endpoint: str, date: str, data: dict) -> None:
    """Save response to cache."""
    cache_dir = _get_cache_dir()
    cache_key = _get_cache_key(ticker, endpoint, date)
    cache_file = cache_dir / f"{cache_key}.json"
    
    try:
        with open(cache_file, "w") as f:
            json.dump({
                "cached_at": datetime.now().isoformat(),
                "data": data,
            }, f)
    except Exception as e:
        logger.warning(f"Could not save cache: {e}", extra={"ticker": ticker, "endpoint": endpoint, "error": str(e)})


def _make_request(function: str, params: dict) -> Optional[dict]:
    """Make a request to Alpha Vantage API."""
    api_key = get_api_key()
    if not api_key:
        return None
    
    request_params = {
        "function": function,
        "apikey": api_key,
        **params,
    }
    
    try:
        response = requests.get(API_BASE_URL, params=request_params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for rate limit error
        if "Information" in data:
            info = data["Information"]
            if "rate limit" in info.lower():
                logger.warning(f"Alpha Vantage rate limit reached: {info}", extra={"info": info})
                return None
        
        # Check for error message
        if "Error Message" in data:
            logger.error(f"Alpha Vantage error: {data['Error Message']}", extra={"error": data['Error Message']})
            return None
        
        return data
        
    except Exception as e:
        logger.error(f"Alpha Vantage request failed: {e}", extra={"function": function, "error": str(e)})
        return None


def fetch_news_sentiment(
    ticker: str,
    date: Optional[str] = None,
    use_cache: bool = True,
) -> NewsSentimentData:
    """
    Fetch news with sentiment scores from Alpha Vantage.
    
    This uses the NEWS_SENTIMENT endpoint which provides:
    - News articles for the ticker
    - Sentiment scores computed by Alpha Vantage NLP
    - Overall sentiment aggregation
    
    Args:
        ticker: Stock ticker symbol
        date: Date for news (default: today)
        use_cache: Whether to use cached data (24h cache)
        
    Returns:
        NewsSentimentData with articles and sentiment scores
    """
    if not is_available():
        return NewsSentimentData(ticker=ticker)
    
    date = date or datetime.now().strftime("%Y-%m-%d")
    
    # Check cache first
    if use_cache:
        cached = _get_cached(ticker, "NEWS_SENTIMENT", date)
        if cached:
            logger.debug(f"Cache hit for Alpha Vantage news sentiment", extra={"ticker": ticker})
            return _parse_news_response(ticker, cached)
    
    # Calculate date range (last 7 days)
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    
    params = {
        "tickers": ticker,
        "time_from": start_date.strftime("%Y%m%dT0000"),
        "time_to": end_date.strftime("%Y%m%dT2359"),
        "sort": "LATEST",
        "limit": "20",
    }
    
    data = _make_request("NEWS_SENTIMENT", params)
    
    if data:
        logger.info(f"Fetched Alpha Vantage news sentiment", extra={"ticker": ticker, "articles": len(data.get("feed", []))})
        # Cache the response
        if use_cache:
            _save_to_cache(ticker, "NEWS_SENTIMENT", date, data)
        return _parse_news_response(ticker, data)
    
    return NewsSentimentData(ticker=ticker)


def _parse_news_response(ticker: str, data: dict) -> NewsSentimentData:
    """Parse Alpha Vantage news sentiment response."""
    articles = []
    total_sentiment = 0.0
    bullish_count = 0
    bearish_count = 0
    neutral_count = 0
    
    feed = data.get("feed", [])
    
    for item in feed[:20]:  # Limit to 20 articles
        # Find sentiment for this specific ticker
        ticker_sentiment = None
        for ts in item.get("ticker_sentiment", []):
            if ts.get("ticker", "").upper() == ticker.upper():
                ticker_sentiment = ts
                break
        
        sentiment_score = 0.0
        sentiment_label = "Neutral"
        
        if ticker_sentiment:
            try:
                sentiment_score = float(ticker_sentiment.get("ticker_sentiment_score", 0))
            except (ValueError, TypeError):
                sentiment_score = 0.0
            sentiment_label = ticker_sentiment.get("ticker_sentiment_label", "Neutral")
        
        article = {
            "title": item.get("title", ""),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "time_published": item.get("time_published", ""),
            "summary": item.get("summary", ""),
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
        }
        articles.append(article)
        
        total_sentiment += sentiment_score
        if sentiment_score > 0.15:
            bullish_count += 1
        elif sentiment_score < -0.15:
            bearish_count += 1
        else:
            neutral_count += 1
    
    # Calculate overall sentiment
    overall_score = total_sentiment / len(articles) if articles else 0.0
    
    if overall_score > 0.15:
        overall_label = "Bullish"
    elif overall_score < -0.15:
        overall_label = "Bearish"
    else:
        overall_label = "Neutral"
    
    return NewsSentimentData(
        ticker=ticker,
        articles=articles,
        overall_sentiment_score=overall_score,
        overall_sentiment_label=overall_label,
        total_articles=len(articles),
        bullish_count=bullish_count,
        bearish_count=bearish_count,
        neutral_count=neutral_count,
    )


def fetch_insider_transactions_av(
    ticker: str,
    use_cache: bool = True,
) -> Optional[dict]:
    """
    Fetch insider transactions from Alpha Vantage.
    
    Note: yfinance also provides insider data, but Alpha Vantage
    may have more detail in some cases.
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data (24h cache)
        
    Returns:
        Raw insider transaction data or None
    """
    if not is_available():
        return None
    
    date = datetime.now().strftime("%Y-%m-%d")
    
    # Check cache first
    if use_cache:
        cached = _get_cached(ticker, "INSIDER_TRANSACTIONS", date)
        if cached:
            return cached
    
    params = {
        "symbol": ticker,
    }
    
    data = _make_request("INSIDER_TRANSACTIONS", params)
    
    if data and use_cache:
        _save_to_cache(ticker, "INSIDER_TRANSACTIONS", date, data)
    
    return data


def format_news_for_prompt(news_data: NewsSentimentData) -> str:
    """
    Format news sentiment data for LLM prompt.
    
    Includes sentiment scores from Alpha Vantage NLP.
    """
    if not news_data.articles:
        return "No news data available from Alpha Vantage."
    
    lines = [
        f"Overall Sentiment: {news_data.overall_sentiment_label} "
        f"(score: {news_data.overall_sentiment_score:.2f})",
        f"Article Breakdown: {news_data.bullish_count} bullish, "
        f"{news_data.bearish_count} bearish, {news_data.neutral_count} neutral",
        "",
    ]
    
    for i, article in enumerate(news_data.articles[:10], 1):
        sent_str = f"[{article['sentiment_label']}: {article['sentiment_score']:+.2f}]"
        lines.append(f"[{i}] {article['source']} {sent_str}")
        lines.append(f"    \"{article['title']}\"")
        if article.get('summary'):
            # Truncate summary to 200 chars
            summary = article['summary'][:200]
            if len(article['summary']) > 200:
                summary += "..."
            lines.append(f"    {summary}")
        lines.append("")
    
    return "\n".join(lines)
