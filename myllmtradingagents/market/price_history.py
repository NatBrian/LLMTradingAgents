"""
Price history data fetching from yfinance.

Returns raw OHLCV data from exchanges - authoritative market data.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


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
    bars: list[PriceBar] = field(default_factory=list)
    
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
    try:
        stock = yf.Ticker(ticker)
        
        # Fetch history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 10)  # Extra buffer for weekends
        
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return PriceHistoryData(ticker=ticker.upper())
        
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
        
        # Get 52-week high/low from info
        info = stock.info or {}
        high_52w = info.get('fiftyTwoWeekHigh')
        low_52w = info.get('fiftyTwoWeekLow')
        
        return PriceHistoryData(
            ticker=ticker.upper(),
            bars=bars,
            high_52w=high_52w,
            low_52w=low_52w,
        )
        
    except Exception as e:
        print(f"Error fetching price history for {ticker}: {e}")
        return PriceHistoryData(ticker=ticker.upper())


def fetch_price_history_batch(
    tickers: list[str],
    days: int = 60,
) -> dict[str, PriceHistoryData]:
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
