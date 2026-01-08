"""
Earnings calendar data fetching from yfinance.

Returns raw authoritative data from company investor relations.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, date

import yfinance as yf
import logging

logger = logging.getLogger(__name__)


@dataclass
class EarningsData:
    """
    Earnings calendar data for a ticker.
    
    All data is authoritative from company announcements via yfinance.
    """
    next_earnings_date: Optional[str] = None  # YYYY-MM-DD format
    days_to_earnings: Optional[int] = None    # Calendar days until earnings
    
    # Historical earnings dates (recent)
    recent_earnings_dates: List[str] = None   # List of recent earnings dates
    
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
            logger.debug(f"Fetching earnings calendar for {ticker}...", extra={"ticker": ticker})
            calendar = stock.calendar
            if calendar is not None:
                logger.debug(f"Fetched earnings calendar for {ticker}", extra={"ticker": ticker, "type": type(calendar)})
            else:
                logger.debug(f"Earnings calendar is None for {ticker}", extra={"ticker": ticker})
        except Exception as e:
            logger.debug(f"Could not fetch earnings calendar for {ticker}: {e}", extra={"ticker": ticker})
        
        next_earnings_date = None
        days_to_earnings = None
        
        # Extract next earnings date from calendar
        if calendar is not None:
            try:
                # yfinance calendar can return different formats (dict or DataFrame)
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
                elif hasattr(calendar, 'get'): # DataFrame-like
                     # Try to access as if it were a dataframe or series
                     pass
            except Exception as e:
                logger.warning(f"Error parsing earnings calendar for {ticker}: {e}", extra={"ticker": ticker})
        
        # Try to get recent earnings history
        recent_dates = []
        try:
            earnings_history = stock.earnings_dates
            if earnings_history is not None and not earnings_history.empty:
                # Get up to 4 recent dates
                for dt in earnings_history.index[:4]:
                    if hasattr(dt, 'strftime'):
                        recent_dates.append(dt.strftime('%Y-%m-%d'))
        except Exception as e:
            logger.debug(f"Could not fetch recent earnings history for {ticker}: {e}", extra={"ticker": ticker})
        
        logger.debug(f"Fetched earnings data for {ticker}", extra={"ticker": ticker, "next_date": next_earnings_date})
        
        return EarningsData(
            next_earnings_date=next_earnings_date,
            days_to_earnings=days_to_earnings,
            recent_earnings_dates=recent_dates,
        )
        
    except Exception as e:
        logger.error(f"Error fetching earnings calendar for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        return EarningsData()


def fetch_earnings_calendar_batch(tickers: List[str]) -> Dict[str, EarningsData]:
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
