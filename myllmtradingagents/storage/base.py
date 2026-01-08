"""
Abstract storage interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import date

from ..schemas import Snapshot, RunLog, Fill


class Storage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize storage (create tables, etc.)."""
        pass
    
    # ========================================================================
    # Competitor Management
    # ========================================================================
    
    @abstractmethod
    def save_competitor(
        self,
        competitor_id: str,
        name: str,
        provider: str,
        model: str,
        config: Optional[dict] = None,
    ) -> None:
        """Save or update a competitor."""
        pass
    
    @abstractmethod
    def get_competitor(self, competitor_id: str) -> Optional[dict]:
        """Get competitor by ID."""
        pass
    
    @abstractmethod
    def list_competitors(self) -> List[dict]:
        """List all competitors."""
        pass
    
    # ========================================================================
    # Snapshots
    # ========================================================================
    
    @abstractmethod
    def save_snapshot(self, competitor_id: str, snapshot: Snapshot) -> None:
        """Save a portfolio snapshot."""
        pass
    
    @abstractmethod
    def get_latest_snapshot(self, competitor_id: str) -> Optional[Snapshot]:
        """Get the most recent snapshot for a competitor."""
        pass
    
    @abstractmethod
    def get_equity_curve(
        self,
        competitor_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Snapshot]:
        """Get equity curve (list of snapshots) for a competitor."""
        pass
    
    # ========================================================================
    # Run Logs
    # ========================================================================
    
    @abstractmethod
    def save_run_log(self, run_log: RunLog) -> None:
        """Save a run log."""
        pass
    
    @abstractmethod
    def get_run_log(self, run_id: str) -> Optional[RunLog]:
        """Get a run log by ID."""
        pass
    
    @abstractmethod
    def list_run_logs(
        self,
        competitor_id: Optional[str] = None,
        session_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[RunLog]:
        """List run logs with optional filters."""
        pass
    
    # ========================================================================
    # Trades
    # ========================================================================
    
    @abstractmethod
    def save_trade(
        self,
        competitor_id: str,
        fill: Fill,
    ) -> None:
        """Save a trade (fill)."""
        pass
    
    @abstractmethod
    def get_trades(
        self,
        competitor_id: Optional[str] = None,
        ticker: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[dict]:
        """Get trades with optional filters."""
        pass
    
    # ========================================================================
    # Leaderboard
    # ========================================================================
    
    @abstractmethod
    def get_leaderboard(self) -> List[dict]:
        """
        Get leaderboard with metrics for all competitors.
        
        Returns list of dicts with:
        - competitor_id, name, provider, model
        - total_return, max_drawdown, sharpe_ratio
        - num_trades, current_equity
        """
        pass
    
    # ========================================================================
    # Session Tracking
    # ========================================================================
    
    @abstractmethod
    def has_run_today(
        self,
        competitor_id: str,
        session_date: str,
        session_type: str,
    ) -> bool:
        """Check if a session has already run today."""
        pass
    
    # ========================================================================
    # Call Counters
    # ========================================================================
    
    @abstractmethod
    def get_daily_call_count(self, provider: str, date: str) -> int:
        """Get number of LLM calls for a provider on a date."""
        pass
    
    @abstractmethod
    def increment_call_count(self, provider: str, date: str, count: int = 1) -> None:
        """Increment call count for a provider on a date."""
        pass
