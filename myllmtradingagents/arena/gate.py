"""
Session gate - determines if a trading session should run.

Checks:
- Is it a trading day for the market?
- Has this session already run today?
- Is it within the session time window?
"""

from datetime import datetime, date, timedelta
from typing import Optional

from ..settings import ArenaConfig, MarketConfig
from ..market import create_market_adapter
from ..storage import SQLiteStorage


class SessionGate:
    """
    Gate logic for determining if a session should run.
    """
    
    def __init__(
        self,
        config: ArenaConfig,
        storage: Optional[SQLiteStorage] = None,
    ):
        """
        Initialize session gate.
        
        Args:
            config: Arena configuration
            storage: Storage instance (for checking if already ran)
        """
        self.config = config
        self.storage = storage or SQLiteStorage(config.db_path)
    
    def should_run(
        self,
        market: MarketConfig,
        session_type: str,  # "OPEN" or "CLOSE"
        now: Optional[datetime] = None,
    ) -> tuple[bool, str]:
        """
        Check if a session should run.
        
        Args:
            market: Market configuration
            session_type: "OPEN" or "CLOSE"
            now: Current datetime (default: now)
            
        Returns:
            Tuple of (should_run, reason)
        """
        now = now or datetime.now()
        today = now.date()
        today_str = today.isoformat()
        
        # Create market adapter
        adapter = create_market_adapter(market.type, cache_dir=self.config.cache_dir)
        
        # Check if trading day (except crypto which trades 24/7)
        if market.type != "crypto":
            if not adapter.is_trading_day(today):
                return False, f"Not a trading day for {market.type}"
        
        # Get session times
        session_times = adapter.get_session_times(today)
        
        if session_times is None and market.type != "crypto":
            return False, "Could not determine session times"
        
        # For crypto, check if we're near configured session times
        if market.type == "crypto":
            return self._check_crypto_session(market, session_type, now, today_str)
        
        # For equities, check session time window
        open_time, close_time = session_times
        
        if session_type == "OPEN":
            # Run within 30 minutes of market open
            window_start = open_time - timedelta(minutes=5)
            window_end = open_time + timedelta(minutes=30)
            
            if not (window_start <= now <= window_end):
                return False, f"Outside OPEN window ({open_time})"
        
        elif session_type == "CLOSE":
            # Run within 30 minutes before market close
            window_start = close_time - timedelta(minutes=30)
            window_end = close_time + timedelta(minutes=5)
            
            if not (window_start <= now <= window_end):
                return False, f"Outside CLOSE window ({close_time})"
        
        # Check if already ran today for any competitor
        for comp in self.config.competitors:
            if self.storage.has_run_today(comp.id, today_str, session_type):
                return False, f"Already ran {session_type} for {comp.id} today"
        
        return True, "OK"
    
    def _check_crypto_session(
        self,
        market: MarketConfig,
        session_type: str,
        now: datetime,
        today_str: str,
    ) -> tuple[bool, str]:
        """Check if we should run a crypto session."""
        from datetime import time
        import pytz
        
        tz = pytz.timezone(market.timezone)
        now_local = now.astimezone(tz) if now.tzinfo else tz.localize(now)
        
        # Parse session times
        session_idx = 0 if session_type == "OPEN" else 1
        if session_idx >= len(market.session_times):
            session_idx = 0
        
        time_str = market.session_times[session_idx]
        parts = time_str.split(":")
        target_time = time(int(parts[0]), int(parts[1]))
        
        # Create target datetime
        target_dt = tz.localize(datetime.combine(now_local.date(), target_time))
        
        # Check if within 10 minutes of target
        diff = abs((now_local - target_dt).total_seconds())
        
        if diff > 600:  # 10 minutes
            return False, f"Outside crypto {session_type} window ({time_str})"
        
        # Check if already ran
        for comp in self.config.competitors:
            if self.storage.has_run_today(comp.id, today_str, session_type):
                return False, f"Already ran {session_type} for {comp.id} today"
        
        return True, "OK"
    
    def get_next_session(
        self,
        now: Optional[datetime] = None,
    ) -> Optional[tuple[str, str, datetime]]:
        """
        Get the next session that should run.
        
        Returns:
            Tuple of (market_type, session_type, session_time) or None
        """
        now = now or datetime.now()
        today = now.date()
        
        next_sessions = []
        
        for market in self.config.markets:
            adapter = create_market_adapter(market.type, cache_dir=self.config.cache_dir)
            
            # Check today
            if market.type == "crypto" or adapter.is_trading_day(today):
                session_times = adapter.get_session_times(today)
                
                if session_times:
                    open_time, close_time = session_times
                    
                    # Check OPEN
                    if now < open_time:
                        next_sessions.append((market.type, "OPEN", open_time))
                    
                    # Check CLOSE
                    if now < close_time:
                        next_sessions.append((market.type, "CLOSE", close_time))
            
            # Check tomorrow
            tomorrow = today + timedelta(days=1)
            for _ in range(7):  # Look up to a week ahead
                if market.type == "crypto" or adapter.is_trading_day(tomorrow):
                    session_times = adapter.get_session_times(tomorrow)
                    if session_times:
                        open_time, close_time = session_times
                        next_sessions.append((market.type, "OPEN", open_time))
                        break
                tomorrow += timedelta(days=1)
        
        if not next_sessions:
            return None
        
        # Return soonest session
        next_sessions.sort(key=lambda x: x[2])
        return next_sessions[0]
