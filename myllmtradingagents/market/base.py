"""
Abstract base class for market data adapters.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

import pandas as pd


class MarketAdapter(ABC):
    """Abstract base class for market data adapters."""
    
    @abstractmethod
    def get_daily_bars(
        self,
        ticker: str,
        days: int = 90,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars for a ticker.
        
        Args:
            ticker: Ticker symbol
            days: Number of trading days to fetch
            end_date: End date (default: today)
            
        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume
            Sorted by Date ascending.
        """
        pass
    
    @abstractmethod
    def get_session_times(self, date: date) -> Optional[tuple[datetime, datetime]]:
        """
        Get market open and close times for a given date.
        
        Args:
            date: The trading date
            
        Returns:
            Tuple of (open_time, close_time) as timezone-aware datetimes,
            or None if not a trading day.
        """
        pass
    
    @abstractmethod
    def is_trading_day(self, date: date) -> bool:
        """
        Check if a given date is a trading day.
        
        Args:
            date: The date to check
            
        Returns:
            True if market is open on this date
        """
        pass
    
    @abstractmethod
    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the latest available price for a ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Latest close price, or None if unavailable
        """
        pass
    
    def get_open_price(self, ticker: str, date: date) -> Optional[float]:
        """
        Get the opening price for a ticker on a given date.
        
        Args:
            ticker: Ticker symbol
            date: The trading date
            
        Returns:
            Opening price, or None if unavailable
        """
        bars = self.get_daily_bars(ticker, days=5, end_date=date)
        if bars.empty:
            return None
        
        date_str = date.strftime("%Y-%m-%d")
        if "Date" in bars.columns:
            bars["Date"] = pd.to_datetime(bars["Date"]).dt.strftime("%Y-%m-%d")
            row = bars[bars["Date"] == date_str]
            if not row.empty:
                return float(row.iloc[0]["Open"])
        
        return None
    
    def get_close_price(self, ticker: str, date: date) -> Optional[float]:
        """
        Get the closing price for a ticker on a given date.
        
        Args:
            ticker: Ticker symbol
            date: The trading date
            
        Returns:
            Closing price, or None if unavailable
        """
        bars = self.get_daily_bars(ticker, days=5, end_date=date)
        if bars.empty:
            return None
        
        date_str = date.strftime("%Y-%m-%d")
        if "Date" in bars.columns:
            bars["Date"] = pd.to_datetime(bars["Date"]).dt.strftime("%Y-%m-%d")
            row = bars[bars["Date"] == date_str]
            if not row.empty:
                return float(row.iloc[0]["Close"])
        
        return None
    
    def get_market_type(self) -> str:
        """Return the market type identifier."""
        return "unknown"
