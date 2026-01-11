"""
Price history data fetching from yfinance.

Returns raw OHLCV data from exchanges - authoritative market data.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
import logging
from .utils import normalize_yahoo_ticker

logger = logging.getLogger(__name__)


@dataclass
class PriceBar:
    """A single OHLCV bar."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class PriceHistoryData:
    """
    Price history data for a ticker.
    
    All data is authoritative from exchange via yfinance.
    """
    ticker: str
    bars: List[PriceBar] = field(default_factory=list)
    
    # 52-week range
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    
    def to_table_string(self, max_rows: int = 30) -> str:
        """Format price history as a table for LLM prompt."""
        if not self.bars:
            return "No price history available."
        
        lines = [
            "Date       | Open    | High    | Low     | Close   | Volume",
            "-----------|---------|---------|---------|---------|------------",
        ]
        
        for bar in self.bars[:max_rows]:
            lines.append(
                f"{bar.date} | {bar.open:7.2f} | {bar.high:7.2f} | {bar.low:7.2f} | "
                f"{bar.close:7.2f} | {bar.volume:>10,}"
            )
        
        if len(self.bars) > max_rows:
            lines.append(f"... ({len(self.bars) - max_rows} more rows)")
        
        return "\n".join(lines)


def fetch_price_history(
    ticker: str,
    days: int = 60,
) -> PriceHistoryData:
    """
    Fetch price history for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days of history to fetch
        
    Returns:
        PriceHistoryData with OHLCV bars
    """
    # Normalize ticker (e.g. XRP/USDT -> XRP-USD)
    y_ticker = normalize_yahoo_ticker(ticker)
    
    try:
        stock = yf.Ticker(y_ticker)
        
        # Fetch history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # Extra buffer for weekends
        
        df = stock.history(start=start_date, end=end_date)
        logger.debug(f"yfinance history returned {len(df)} rows for {ticker}", extra={"ticker": ticker, "rows": len(df)})
        
        if df.empty:
            logger.warning(f"No price history found for {ticker}", extra={"ticker": ticker})
            return PriceHistoryData(ticker=ticker.upper())
        
        logger.debug(f"Fetched {len(df)} price bars for {ticker}", extra={"ticker": ticker, "rows": len(df)})
        
        # Convert to list of PriceBar
        bars = []
        for idx, row in df.iterrows():
            date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
            
            bar = PriceBar(
                date=date_str,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row.get('Volume', 0)),
            )
            bars.append(bar)
        
        # Sort by date descending (most recent first)
        bars.sort(key=lambda x: x.date, reverse=True)
        
        # Limit to requested days
        bars = bars[:days]
        
        # Get 52-week high/low (fail-soft)
        high_52w = None
        low_52w = None
        
        # 1. Try info
        try:
            info = stock.info
            if info:
                high_52w = info.get('fiftyTwoWeekHigh')
                low_52w = info.get('fiftyTwoWeekLow')
        except Exception:
            pass
            
        # 2. Try fast_info if info failed
        if high_52w is None or low_52w is None:
            try:
                fast_info = stock.fast_info
                if fast_info:
                    high_52w = fast_info.get('year_high')
                    low_52w = fast_info.get('year_low')
            except Exception:
                pass
        
        # 3. Fallback: Calculate from history (if we have enough data)
        if (high_52w is None or low_52w is None) and bars:
            # Note: This is only based on the fetched window (e.g. 60 days), 
            # so it's not a true 52-week range, but better than nothing.
            high_52w = max(b.high for b in bars)
            low_52w = min(b.low for b in bars)
        
        return PriceHistoryData(
            ticker=ticker.upper(),
            bars=bars,
            high_52w=high_52w,
            low_52w=low_52w,
        )
        
    except Exception as e:
        logger.error(f"Error fetching price history for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        return PriceHistoryData(ticker=ticker.upper())


def fetch_price_history_batch(
    tickers: List[str],
    days: int = 60,
) -> Dict[str, PriceHistoryData]:
    """
    Fetch price history for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        days: Number of days of history
        
    Returns:
        Dict mapping ticker -> PriceHistoryData
    """
    result = {}
    for ticker in tickers:
        result[ticker.upper()] = fetch_price_history(ticker, days)
    return result
