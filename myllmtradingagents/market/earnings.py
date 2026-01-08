"""
Earnings calendar data fetching from yfinance.

Returns raw authoritative data from company investor relations.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, date

import yfinance as yf


@dataclass
class EarningsData:
    """
    Earnings calendar data for a ticker.
    
    All data is authoritative from company announcements via yfinance.
    """
    next_earnings_date: Optional[str] = None  # YYYY-MM-DD format
    days_to_earnings: Optional[int] = None    # Calendar days until earnings
    
    # Historical earnings dates (recent)
    recent_earnings_dates: list[str] = None   # List of recent earnings dates
    
    def __post_init__(self):
        if self.recent_earnings_dates is None:
            self.recent_earnings_dates = []


def fetch_earnings_calendar(ticker: str) -> EarningsData:
    """
    Fetch earnings calendar data for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        EarningsData with next earnings date info
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Try to get earnings dates
        calendar = None
        try:
            calendar = stock.calendar
        except Exception:
            pass
        
        next_earnings_date = None
        days_to_earnings = None
        
        # Extract next earnings date from calendar
        if calendar is not None:
            # yfinance calendar can return different formats
            if isinstance(calendar, dict):
                # Check for 'Earnings Date' key
                earnings_dates = calendar.get('Earnings Date')
                if earnings_dates is not None and len(earnings_dates) > 0:
                    next_date = earnings_dates[0]
                    if hasattr(next_date, 'strftime'):
                        next_earnings_date = next_date.strftime('%Y-%m-%d')
                        days_to_earnings = (next_date.date() - date.today()).days
                    elif isinstance(next_date, str):
                        next_earnings_date = next_date[:10]
        
        # Try to get recent earnings history
        recent_dates = []
        try:
            earnings_history = stock.earnings_dates
            if earnings_history is not None and len(earnings_history) > 0:
                # Get up to 4 recent dates
                for dt in earnings_history.index[:4]:
                    if hasattr(dt, 'strftime'):
                        recent_dates.append(dt.strftime('%Y-%m-%d'))
        except Exception:
            pass
        
        return EarningsData(
            next_earnings_date=next_earnings_date,
            days_to_earnings=days_to_earnings,
            recent_earnings_dates=recent_dates,
        )
        
    except Exception as e:
        print(f"Error fetching earnings calendar for {ticker}: {e}")
        return EarningsData()


def fetch_earnings_calendar_batch(tickers: list[str]) -> dict[str, EarningsData]:
    """
    Fetch earnings calendar for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dict mapping ticker -> EarningsData
    """
    result = {}
    for ticker in tickers:
        result[ticker.upper()] = fetch_earnings_calendar(ticker)
    return result
