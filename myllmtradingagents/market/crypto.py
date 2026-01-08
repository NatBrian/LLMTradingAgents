"""
Crypto market adapter using ccxt for data fetching.
"""

import os
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Optional

import pandas as pd
import pytz

from .base import MarketAdapter


class CryptoAdapter(MarketAdapter):
    """Crypto market adapter using ccxt (Binance by default)."""
    
    EXCHANGE = "binance"
    TIMEZONE = "UTC"
    
    # Default session times (UTC) - crypto trades 24/7 but we pick 2 times
    DEFAULT_SESSION_TIMES = ["00:00", "12:00"]
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_days: int = 1,
        exchange: str = "binance",
        session_times: Optional[list[str]] = None,  # ["HH:MM", "HH:MM"]
        timezone: str = "UTC",
    ):
        """
        Initialize Crypto adapter.
        
        Args:
            cache_dir: Directory to cache data
            cache_days: Days to cache data before refreshing
            exchange: CCXT exchange name (default: binance)
            session_times: Two daily session times ["HH:MM", "HH:MM"]
            timezone: Timezone for session times
        """
        self.cache_dir = Path(cache_dir or os.path.expanduser("~/.myllmtradingagents/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_days = cache_days
        self.exchange_name = exchange
        self.tz = pytz.timezone(timezone)
        
        # Parse session times
        self.session_times = []
        times = session_times or self.DEFAULT_SESSION_TIMES
        for t in times:
            parts = t.split(":")
            self.session_times.append(time(int(parts[0]), int(parts[1])))
        
        # Lazy load exchange
        self._exchange = None
    
    @property
    def exchange(self):
        """Lazy load CCXT exchange."""
        if self._exchange is None:
            try:
                import ccxt
                exchange_class = getattr(ccxt, self.exchange_name)
                self._exchange = exchange_class({
                    "enableRateLimit": True,
                })
            except ImportError:
                raise ImportError("ccxt package required. Install with: pip install ccxt")
            except AttributeError:
                raise ValueError(f"Unknown exchange: {self.exchange_name}")
        return self._exchange
    
    def get_market_type(self) -> str:
        return "crypto"
    
    def _normalize_symbol(self, ticker: str) -> str:
        """Convert ticker to CCXT symbol format."""
        ticker = ticker.upper()
        
        # Common conversions
        if "/" in ticker:
            return ticker  # Already in format BTC/USDT
        
        # Try to add /USDT if not present
        if not ticker.endswith("USDT") and not ticker.endswith("/USDT"):
            return f"{ticker}/USDT"
        
        if ticker.endswith("USDT"):
            base = ticker[:-4]
            return f"{base}/USDT"
        
        return ticker
    
    def get_daily_bars(
        self,
        ticker: str,
        days: int = 90,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV bars using CCXT."""
        symbol = self._normalize_symbol(ticker)
        end_date = end_date or date.today()
        
        # Check cache
        cache_key = symbol.replace("/", "_")
        cache_file = self.cache_dir / f"crypto_{cache_key}_daily_{end_date.isoformat()}.parquet"
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age.days < self.cache_days:
                try:
                    return pd.read_parquet(cache_file)
                except Exception:
                    pass
        
        # Fetch from CCXT
        try:
            # Calculate since timestamp
            since_date = end_date - timedelta(days=days + 5)
            since_ts = int(datetime.combine(since_date, datetime.min.time()).timestamp() * 1000)
            
            # Fetch OHLCV
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe="1d",
                since=since_ts,
                limit=days + 5,
            )
            
            if not ohlcv:
                return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"]
            )
            
            df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
            df = df.drop(columns=["Timestamp"])
            
            # Take last N days
            df = df.sort_values("Date").tail(days).reset_index(drop=True)
            
            # Cache
            try:
                df.to_parquet(cache_file)
            except Exception:
                pass
            
            return df
            
        except Exception as e:
            print(f"Error fetching crypto data for {symbol}: {e}")
            return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    
    def get_session_times(self, date: date) -> Optional[tuple[datetime, datetime]]:
        """
        Get "session" times for crypto (always trading).
        
        Returns first and second configured session times.
        For crypto we treat these as two trading windows per day.
        """
        if len(self.session_times) >= 2:
            open_dt = self.tz.localize(datetime.combine(date, self.session_times[0]))
            close_dt = self.tz.localize(datetime.combine(date, self.session_times[1]))
            return (open_dt, close_dt)
        elif len(self.session_times) == 1:
            open_dt = self.tz.localize(datetime.combine(date, self.session_times[0]))
            close_dt = open_dt + timedelta(hours=12)
            return (open_dt, close_dt)
        else:
            # Default 00:00 and 12:00 UTC
            open_dt = self.tz.localize(datetime.combine(date, time(0, 0)))
            close_dt = self.tz.localize(datetime.combine(date, time(12, 0)))
            return (open_dt, close_dt)
    
    def is_trading_day(self, date: date) -> bool:
        """Crypto trades 24/7, always returns True."""
        return True
    
    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get latest price using ticker endpoint."""
        symbol = self._normalize_symbol(ticker)
        
        try:
            ticker_data = self.exchange.fetch_ticker(symbol)
            return float(ticker_data.get("last") or ticker_data.get("close", 0))
        except Exception:
            # Fallback to last daily bar
            bars = self.get_daily_bars(ticker, days=2)
            if bars.empty:
                return None
            return float(bars.iloc[-1]["Close"])
