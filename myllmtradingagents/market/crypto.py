"""
Crypto market adapter using ccxt for data fetching.
"""

import os
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd
import pytz

from .base import MarketAdapter
import logging

logger = logging.getLogger(__name__)


class CryptoAdapter(MarketAdapter):
    """Crypto market adapter using ccxt with multi-exchange fallback."""
    
    EXCHANGE = "binance"
    TIMEZONE = "UTC"
    
    # Fallback exchanges to try if primary fails (in order of preference)
    FALLBACK_EXCHANGES = ["kraken", "kucoin", "coinbase", "bitstamp"]
    
    # Default session times (UTC) - crypto trades 24/7 but we pick 2 times
    DEFAULT_SESSION_TIMES = ["00:00", "12:00"]
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_days: int = 1,
        exchange: str = "binance",
        session_times: Optional[List[str]] = None,  # ["HH:MM", "HH:MM"]
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
        
        # Lazy load exchanges (primary + fallbacks)
        self._exchanges: dict = {}
        self._working_exchange: Optional[str] = None
    
    def _get_exchange(self, exchange_name: str):
        """Get or create a CCXT exchange instance."""
        if exchange_name not in self._exchanges:
            try:
                import ccxt
                exchange_class = getattr(ccxt, exchange_name)
                self._exchanges[exchange_name] = exchange_class({
                    "enableRateLimit": True,
                })
            except ImportError:
                raise ImportError("ccxt package required. Install with: pip install ccxt")
            except AttributeError:
                logger.warning(f"Unknown exchange: {exchange_name}")
                return None
        return self._exchanges.get(exchange_name)
    
    @property
    def exchange(self):
        """Get the primary or last working exchange."""
        if self._working_exchange:
            return self._get_exchange(self._working_exchange)
        return self._get_exchange(self.exchange_name)
    
    def _get_exchange_order(self) -> List[str]:
        """Get list of exchanges to try, with working one first."""
        exchanges = [self.exchange_name] + [e for e in self.FALLBACK_EXCHANGES if e != self.exchange_name]
        if self._working_exchange and self._working_exchange != self.exchange_name:
            # Move working exchange to front
            exchanges = [self._working_exchange] + [e for e in exchanges if e != self._working_exchange]
        return exchanges
    
    def _normalize_symbol_for_exchange(self, ticker: str, exchange_name: str) -> str:
        """Normalize symbol for specific exchange format."""
        ticker = ticker.upper()
        
        # Standard format: BTC/USDT
        if "/" in ticker:
            base, quote = ticker.split("/")
        elif ticker.endswith("USDT"):
            base = ticker[:-4]
            quote = "USDT"
        else:
            base = ticker
            quote = "USDT"
        
        # Exchange-specific adjustments
        if exchange_name == "kraken":
            # Kraken uses XBT instead of BTC, and USD instead of USDT for some pairs
            if base == "BTC":
                base = "XBT"
            if quote == "USDT":
                # Try USDT first, but some pairs only have USD
                quote = "USDT"
        elif exchange_name == "coinbase":
            # Coinbase uses USD, not USDT
            if quote == "USDT":
                quote = "USD"
        
        return f"{base}/{quote}"
    
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
        """Fetch daily OHLCV bars using CCXT with multi-exchange fallback."""
        end_date = end_date or date.today()
        
        # Check cache first (use original ticker for cache key)
        cache_key = ticker.upper().replace("/", "_")
        cache_file = self.cache_dir / f"crypto_{cache_key}_daily_{end_date.isoformat()}.parquet"
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age.days < self.cache_days:
                try:
                    logger.debug(f"Cache hit for {ticker}", extra={"symbol": ticker, "cache_age_days": cache_age.days})
                    return pd.read_parquet(cache_file)
                except Exception as e:
                    logger.warning(f"Failed to read cache for {ticker}: {e}", extra={"symbol": ticker, "error": str(e)})
        
        # Calculate since timestamp
        since_date = end_date - timedelta(days=days + 5)
        since_ts = int(datetime.combine(since_date, datetime.min.time()).timestamp() * 1000)
        
        # Try each exchange in order
        exchanges_to_try = self._get_exchange_order()
        last_error = None
        
        for exchange_name in exchanges_to_try:
            exchange = self._get_exchange(exchange_name)
            if exchange is None:
                continue
            
            # Normalize symbol for this specific exchange
            symbol = self._normalize_symbol_for_exchange(ticker, exchange_name)
            
            try:
                logger.info(
                    f"Fetching crypto data for {ticker} from {exchange_name}",
                    extra={"symbol": symbol, "exchange": exchange_name, "since": since_date.isoformat()}
                )
                
                # Fetch OHLCV
                ohlcv = exchange.fetch_ohlcv(
                    symbol,
                    timeframe="1d",
                    since=since_ts,
                    limit=days + 5,
                )
                
                if not ohlcv:
                    logger.warning(f"No data returned from {exchange_name} for {symbol}")
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"]
                )
                
                df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
                df = df.drop(columns=["Timestamp"])
                
                # Take last N days
                df = df.sort_values("Date").tail(days).reset_index(drop=True)
                
                # Mark this exchange as working
                self._working_exchange = exchange_name
                logger.info(
                    f"Successfully fetched {len(df)} bars for {ticker} from {exchange_name}",
                    extra={"symbol": symbol, "exchange": exchange_name, "rows": len(df)}
                )
                
                # Cache
                try:
                    df.to_parquet(cache_file)
                    logger.debug(f"Cache written for {ticker}", extra={"symbol": ticker, "rows": len(df)})
                except Exception as e:
                    logger.warning(f"Failed to write cache for {ticker}: {e}", extra={"symbol": ticker, "error": str(e)})
                
                return df
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Failed to fetch {ticker} from {exchange_name}: {e}",
                    extra={"symbol": symbol, "exchange": exchange_name, "error": str(e)}
                )
                continue
        
        # All exchanges failed
        logger.error(
            f"All exchanges failed for {ticker}. Last error: {last_error}",
            extra={"symbol": ticker, "exchanges_tried": exchanges_to_try}
        )
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    
    def get_session_times(self, date: date) -> Optional[Tuple[datetime, datetime]]:
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
        """Get latest price using ticker endpoint with multi-exchange fallback."""
        exchanges_to_try = self._get_exchange_order()
        
        for exchange_name in exchanges_to_try:
            exchange = self._get_exchange(exchange_name)
            if exchange is None:
                continue
            
            symbol = self._normalize_symbol_for_exchange(ticker, exchange_name)
            
            try:
                ticker_data = exchange.fetch_ticker(symbol)
                price = float(ticker_data.get("last") or ticker_data.get("close", 0))
                if price > 0:
                    self._working_exchange = exchange_name
                    return price
            except Exception as e:
                logger.warning(
                    f"Error fetching ticker for {ticker} from {exchange_name}: {e}",
                    extra={"symbol": symbol, "exchange": exchange_name, "error": str(e)}
                )
                continue
        
        # All ticker endpoints failed, fallback to last daily bar
        logger.warning(f"All ticker endpoints failed for {ticker}, trying daily bars")
        bars = self.get_daily_bars(ticker, days=2)
        if bars.empty:
            return None
        return float(bars.iloc[-1]["Close"])

