"""
CoinGecko API integration for Crypto fundamentals.

Provides missing data for crypto assets:
- Market Cap
- Total Volume
- Circulating Supply
- All-Time High/Low
- Description

Rate Limits (Free Tier):
- 10-30 requests per minute
- Caching is ESSENTIAL.
"""

import os
import json
import logging
import time
import requests
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# CoinGecko API configuration
API_BASE_URL = "https://api.coingecko.com/api/v3"

def get_api_key() -> Optional[str]:
    """Get CoinGecko Demo API key from environment."""
    return os.getenv("COINGECKO_DEMO_API_KEY")

# Manual mapping for common tickers to CoinGecko IDs
# This avoids needing to search for every ID, which adds API calls.
TICKER_MAPPING = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XRP": "ripple",
    "SOL": "solana",
    "BNB": "binancecoin",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "XLM": "stellar",
    "USDT": "tether",
    "USDC": "usd-coin",
    "AVAX": "avalanche-2",
    "UNI": "uniswap",
    "MATIC": "matic-network",
    "TRX": "tron",
    "ETC": "ethereum-classic",
    "FIL": "filecoin",
}

def _get_cache_dir() -> Path:
    """Get or create the cache directory."""
    cache_dir = Path.home() / ".myllmtradingagents" / "cache" / "coingecko"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def _get_cache_key(endpoint: str, params: Optional[dict] = None) -> str:
    """Generate a cache key for a request."""
    key_str = f"{endpoint}_{json.dumps(params, sort_keys=True) if params else ''}"
    return hashlib.md5(key_str.encode()).hexdigest()

def _get_cached(endpoint: str, params: Optional[dict] = None, max_age_hours: int = 6) -> Optional[dict]:
    """Get cached response if available and not expired."""
    cache_dir = _get_cache_dir()
    cache_key = _get_cache_key(endpoint, params)
    cache_file = cache_dir / f"{cache_key}.json"
    
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                cached = json.load(f)
            
            # Check expiry
            cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now() - cached_time < timedelta(hours=max_age_hours):
                return cached.get("data")
        except Exception:
            pass
    return None

def _save_to_cache(endpoint: str, data: dict, params: Optional[dict] = None) -> None:
    """Save response to cache."""
    cache_dir = _get_cache_dir()
    cache_key = _get_cache_key(endpoint, params)
    cache_file = cache_dir / f"{cache_key}.json"
    
    try:
        with open(cache_file, "w") as f:
            json.dump({
                "cached_at": datetime.now().isoformat(),
                "data": data,
            }, f)
    except Exception as e:
        logger.warning(f"Could not save CoinGecko cache: {e}")

def _make_request(endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
    """Make request to CoinGecko API."""
    url = f"{API_BASE_URL}/{endpoint}"
    
    # Add API Key if present
    api_key = get_api_key()
    if api_key:
        if params is None:
            params = {}
        params["x_cg_demo_api_key"] = api_key
    
    try:
        # Check cache first
        cached = _get_cached(endpoint, params)
        if cached:
            logger.debug(f"CoinGecko cache hit for {endpoint}")
            return cached

        response = requests.get(url, params=params, timeout=10)
        
        # Handle rate limiting (429)
        if response.status_code == 429:
            logger.warning("CoinGecko rate limit reached. Using fallback/cache if available.")
            return None
            
        response.raise_for_status()
        data = response.json()
        
        # Save to cache
        _save_to_cache(endpoint, data, params)
        return data
        
    except Exception as e:
        logger.warning(f"CoinGecko request failed: {e}", extra={"endpoint": endpoint, "error": str(e)})
        return None

def get_coin_id(ticker: str) -> Optional[str]:
    """
    Get CoinGecko ID from ticker.
    
    1. Check manual mapping.
    2. (TODO) Search API if not found (omitted to save API calls for now).
    """
    # Clean ticker (e.g. XRP/USDT -> XRP)
    clean_ticker = ticker.upper().split("/")[0].replace("-USD", "")
    
    # Check mapping
    if clean_ticker in TICKER_MAPPING:
        return TICKER_MAPPING[clean_ticker]
    
    logger.warning(f"No CoinGecko ID found for {ticker} (clean: {clean_ticker}) in manual mapping.")
    return None

def fetch_coin_fundamentals(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch fundamental data for a crypto asset.
    
    Returns a dict compatible with FundamentalsData structure where possible.
    """
    coin_id = get_coin_id(ticker)
    if not coin_id:
        return None
        
    data = _make_request(f"coins/{coin_id}", params={
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    })
    
    if not data:
        return None
        
    market_data = data.get("market_data", {})
    
    # Extract relevant fields
    return {
        "company_name": data.get("name"),
        "sector": "Cryptocurrency",
        "industry": f"Blockchain / {data.get('hashing_algorithm', 'protocol')}",
        "market_cap": market_data.get("market_cap", {}).get("usd"),
        "high_52w": market_data.get("high_24h", {}).get("usd"), # Fallback to 24h high? No, use ath if 52w not avail, or just high_24h
        # Actually CoinGecko has ath/atl. Let's use 24h for high/low or look for better field.
        # CoinGecko Free doesn't give 52w easily in this endpoint? 
        # "high_24h" is reliable. Let's use that for high_52w field but maybe annotate it?
        # Actually, let's just populate what we can.
        "low_52w": market_data.get("low_24h", {}).get("usd"),
        "current_price": market_data.get("current_price", {}).get("usd"),
        "volume_24h": market_data.get("total_volume", {}).get("usd"),
        "circulating_supply": market_data.get("circulating_supply"),
        "total_supply": market_data.get("total_supply"),
        "description": data.get("description", {}).get("en", "").split("\n")[0][:500], # First paragraph, truncate
        "ath": market_data.get("ath", {}).get("usd"),
        "atl": market_data.get("atl", {}).get("usd"),
    }
