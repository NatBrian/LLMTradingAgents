"""
Equity market adapters using yfinance and exchange_calendars.
"""

import os
import logging
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Optional

import pandas as pd
import pytz

from .base import MarketAdapter

logger = logging.getLogger(__name__)


class BaseEquityAdapter(MarketAdapter):
    """
    Base class for Equity market adapters using yfinance.
    
    Handles:
    - yfinance data fetching
    - Caching
    - Dataframe cleaning (MultiIndex handling)
    - Exchange calendar integration (via subclasses)
    """
    
    EXCHANGE = ""  # To be defined by subclass
    TIMEZONE = "UTC"  # To be defined by subclass
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_days: int = 1,
    ):
        """
        Initialize Equity adapter.
        
        Args:
            cache_dir: Directory to cache data
            cache_days: Days to cache data before refreshing
        """
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.myllmtradingagents/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_days = cache_days
        self.tz = pytz.timezone(self.TIMEZONE)
        
        # Lazy load calendar
        self._calendar = None
        
    @property
    def calendar(self):
        """Lazy load exchange calendar."""
        if self._calendar is None:
            try:
                import exchange_calendars as xcals
                self._calendar = xcals.get_calendar(self.EXCHANGE)
            except ImportError:
                logger.warning("exchange-calendars not found. Calendar features will be limited.")
                self._calendar = None
            except Exception as e:
                logger.warning(f"Could not load calendar {self.EXCHANGE}: {e}")
                self._calendar = None
        return self._calendar

    def _format_ticker(self, ticker: str) -> str:
        """Format ticker for yfinance (e.g. append suffix). Override in subclasses."""
        return ticker.upper()

    def get_daily_bars(
        self,
        ticker: str,
        days: int = 90,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV bars using yfinance."""
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError("yfinance package required. Install with: pip install yfinance")
        
        ticker_formatted = self._format_ticker(ticker)
        end_date = end_date or date.today()
        
        # Calculate start date (add buffer for weekends/holidays)
        start_date = end_date - timedelta(days=int(days * 1.5) + 10)
        
        # Check cache
        # Use original ticker for filename to keep it clean, or formatted? 
        # Let's use formatted but sanitize it.
        safe_ticker = ticker_formatted.replace(".", "_").replace(":", "_")
        cache_file = self.cache_dir / f"{safe_ticker}_daily_{end_date.isoformat()}.parquet"
        
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age.days < self.cache_days:
                try:
                    return pd.read_parquet(cache_file)
                except Exception as e:
                    logger.warning(f"Failed to read cache for {ticker}: {e}")
        
        # Fetch from yfinance
        try:
            df = yf.download(
                ticker_formatted,
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                progress=False,
                auto_adjust=True,
            )
            
            if df.empty:
                return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
            
            # Handle MultiIndex columns (common in recent yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                # If the second level is the ticker, drop it
                if len(df.columns.levels) > 1:
                    df.columns = df.columns.droplevel(1)
            
            # Reset index to get Date as column
            df = df.reset_index()
            
            # Standardize column names
            df = df.rename(columns={"index": "Date"})
            if "Date" not in df.columns and "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "Date"})
            
            # Ensure Date is datetime
            df["Date"] = pd.to_datetime(df["Date"])
            
            # Select only needed columns
            cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
            available_cols = [c for c in cols if c in df.columns]
            df = df[available_cols]
            
            # Sort by date and take last N days
            df = df.sort_values("Date").tail(days).reset_index(drop=True)
            
            # Cache
            try:
                df.to_parquet(cache_file)
            except Exception as e:
                logger.warning(f"Failed to write cache for {ticker}: {e}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

    def get_session_times(self, date: date) -> Optional[tuple[datetime, datetime]]:
        """Get trading hours for a date."""
        if not self.is_trading_day(date):
            return None
        
        try:
            if self.calendar:
                # Get schedule for the date
                schedule = self.calendar.schedule.loc[date.isoformat()]
                open_time = schedule["open"].to_pydatetime()
                close_time = schedule["close"].to_pydatetime()
                return (open_time, close_time)
        except (KeyError, Exception):
            pass
            
        # Fallback to default hours if calendar fails or not available
        return self._get_default_session_times(date)

    def _get_default_session_times(self, date: date) -> tuple[datetime, datetime]:
        """Default session times (9:00 - 17:00 local). Override in subclasses."""
        open_time = self.tz.localize(datetime.combine(date, time(9, 0)))
        close_time = self.tz.localize(datetime.combine(date, time(17, 0)))
        return (open_time, close_time)

    def is_trading_day(self, date: date) -> bool:
        """Check if market is open on this date."""
        try:
            if self.calendar:
                return self.calendar.is_session(date.isoformat())
        except Exception:
            pass
            
        # Fallback: assume weekdays are trading days
        return date.weekday() < 5

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get latest available price."""
        bars = self.get_daily_bars(ticker, days=5)
        if bars.empty:
            return None
        return float(bars.iloc[-1]["Close"])


class USEquityAdapter(BaseEquityAdapter):
    """US Equity market adapter (NYSE/NASDAQ)."""
    
    EXCHANGE = "XNYS"
    TIMEZONE = "America/New_York"
    
    def get_market_type(self) -> str:
        return "us_equity"
        
    def _get_default_session_times(self, date: date) -> tuple[datetime, datetime]:
        # NYSE: 9:30 - 16:00
        open_time = self.tz.localize(datetime.combine(date, time(9, 30)))
        close_time = self.tz.localize(datetime.combine(date, time(16, 0)))
        return (open_time, close_time)


class SGEquityAdapter(BaseEquityAdapter):
    """Singapore Equity market adapter (SGX)."""
    
    EXCHANGE = "XSES"
    TIMEZONE = "Asia/Singapore"
    
    def get_market_type(self) -> str:
        return "sg_equity"

    def _format_ticker(self, ticker: str) -> str:
        """Ensure .SI suffix for Singapore tickers."""
        ticker = ticker.upper()
        if not ticker.endswith(".SI"):
            return f"{ticker}.SI"
        return ticker
        
    def _get_default_session_times(self, date: date) -> tuple[datetime, datetime]:
        # SGX: 9:00 - 17:00
        open_time = self.tz.localize(datetime.combine(date, time(9, 0)))
        close_time = self.tz.localize(datetime.combine(date, time(17, 0)))
        return (open_time, close_time)
