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
                logger.warning("exchange-calendars not found. Calendar features will be limited.", extra={"exchange": self.EXCHANGE})
                self._calendar = None
            except Exception as e:
                logger.warning(f"Could not load calendar {self.EXCHANGE}: {e}", extra={"exchange": self.EXCHANGE, "error": str(e)})
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
                    logger.debug(f"Cache hit for {ticker}", extra={"ticker": ticker, "cache_age_days": cache_age.days})
                    return pd.read_parquet(cache_file)
                except Exception as e:
                    logger.warning(f"Failed to read cache for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        
        # Fetch from yfinance
        try:
            logger.info(f"Fetching data for {ticker} from yfinance", extra={"ticker": ticker, "start_date": start_date.isoformat(), "end_date": end_date.isoformat()})
            
            # Use Ticker.history as per reference implementation
            t = yf.Ticker(ticker_formatted)
            logger.debug(f"Calling yf.Ticker.history for {ticker}", extra={"ticker": ticker, "start": start_date.isoformat(), "end": (end_date + timedelta(days=1)).isoformat()})
            df = t.history(
                start=start_date.isoformat(),
                end=(end_date + timedelta(days=1)).isoformat(),
                auto_adjust=True
            )
            logger.debug(f"yfinance history returned {len(df)} rows for {ticker}", extra={"ticker": ticker, "rows": len(df)})
            
            if df.empty:
                return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
            
            # Reset index to get Date as column
            df = df.reset_index()
            
            # Standardize column names
            # history() usually returns 'Date' (or 'Datetime'), 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'
            if "Date" not in df.columns and "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "Date"})
            
            # Ensure Date is datetime and tz-naive
            df["Date"] = pd.to_datetime(df["Date"])
            if df["Date"].dt.tz is not None:
                df["Date"] = df["Date"].dt.tz_localize(None)
            
            # Select only needed columns
            cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
            # Ensure all cols exist
            for c in cols:
                if c not in df.columns:
                    # If Volume is missing (sometimes happens), fill 0
                    if c == "Volume":
                        df[c] = 0
                    else:
                        # Should not happen for OHLC
                        pass

            available_cols = [c for c in cols if c in df.columns]
            df = df[available_cols]
            
            # Sort by date and take last N days
            df = df.sort_values("Date").tail(days).reset_index(drop=True)
            
            # Cache
            try:
                df.to_parquet(cache_file)
                logger.debug(f"Cache written for {ticker}", extra={"ticker": ticker, "rows": len(df)})
            except Exception as e:
                logger.warning(f"Failed to write cache for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
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
        # Try fast info first for real-time price
        try:
            import yfinance as yf
            t = yf.Ticker(self._format_ticker(ticker))
            # fast_info is faster and more reliable for latest price
            price = t.fast_info.get("last_price")
            if price:
                logger.debug(f"Fetched latest price for {ticker} from fast_info: {price}", extra={"ticker": ticker, "price": price})
                return float(price)
            else:
                logger.debug(f"fast_info.last_price is None for {ticker}", extra={"ticker": ticker})
        except Exception:
            pass
            
        # Fallback to daily bars
        bars = self.get_daily_bars(ticker, days=5)
        if bars.empty:
            return None
        return float(bars.iloc[-1]["Close"])

    def get_open_price(self, ticker: str, date: date) -> Optional[float]:
        """Get open price with real-time fallback."""
        # Try historical data first
        price = super().get_open_price(ticker, date)
        if price is not None:
            return price
            
        # If requesting today's open and it's missing from history (common during trading day),
        # try to get it from real-time info
        if date == date.today():
            try:
                import yfinance as yf
                logger.info(f"Fetching real-time open price for {ticker}", extra={"ticker": ticker})
                t = yf.Ticker(self._format_ticker(ticker))
                # Try fast_info first
                open_price = t.fast_info.get("open")
                if open_price:
                    logger.debug(f"Fetched real-time open for {ticker} from fast_info: {open_price}", extra={"ticker": ticker, "price": open_price})
                    return float(open_price)
                
                # Fallback to regular info
                info = t.info
                if info and info.get("open"):
                    logger.debug(f"Fetched real-time open for {ticker} from info: {info['open']}", extra={"ticker": ticker, "price": info['open']})
                    return float(info["open"])
                
                # If market is open, 'regularMarketOpen' might be available
                if info and info.get("regularMarketOpen"):
                    logger.debug(f"Fetched real-time open for {ticker} from regularMarketOpen: {info['regularMarketOpen']}", extra={"ticker": ticker, "price": info['regularMarketOpen']})
                    return float(info["regularMarketOpen"])
                    
            except Exception as e:
                logger.warning(f"Failed to fetch real-time open for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        
        return None

    def get_close_price(self, ticker: str, date: date) -> Optional[float]:
        """Get close price with real-time fallback."""
        # Try historical data first
        price = super().get_close_price(ticker, date)
        if price is not None:
            return price
            
        # If requesting today's close (and market might be closed but data not in history yet),
        # try to get it from real-time info
        if date == date.today():
            try:
                import yfinance as yf
                logger.info(f"Fetching real-time close price for {ticker}", extra={"ticker": ticker})
                t = yf.Ticker(self._format_ticker(ticker))
                # Try fast_info first (last_price is often close if market closed)
                last_price = t.fast_info.get("last_price")
                if last_price:
                    logger.debug(f"Fetched real-time close for {ticker} from fast_info: {last_price}", extra={"ticker": ticker, "price": last_price})
                    return float(last_price)
                
                # Fallback to regular info
                info = t.info
                if info and info.get("previousClose"):
                     # If we are strictly looking for today's close, previousClose is WRONG if today is a trading day.
                     # But if we are in 'CLOSE' session, we want the latest price.
                     pass
                
                if info and info.get("currentPrice"):
                    logger.debug(f"Fetched real-time close for {ticker} from currentPrice: {info['currentPrice']}", extra={"ticker": ticker, "price": info['currentPrice']})
                    return float(info["currentPrice"])
                    
            except Exception as e:
                logger.warning(f"Failed to fetch real-time close for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        
        return None


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
