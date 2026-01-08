"""
Portfolio metrics computation.
"""

from dataclasses import dataclass
from typing import Optional, List
import numpy as np

from ..schemas import Snapshot
import logging

logger = logging.getLogger(__name__)


@dataclass
class EquityMetrics:
    """Portfolio performance metrics."""
    # Returns
    total_return: float = 0.0  # Percentage
    total_return_abs: float = 0.0  # Absolute dollars
    
    # Risk
    max_drawdown: float = 0.0  # Percentage (as positive number)
    volatility: float = 0.0  # Annualized
    
    # Risk-adjusted
    sharpe_ratio: Optional[float] = None  # Annualized
    
    # Activity
    num_trades: int = 0
    turnover: float = 0.0  # Total traded value / average equity
    
    # Starting/ending
    starting_equity: float = 0.0
    ending_equity: float = 0.0
    peak_equity: float = 0.0


def compute_metrics(
    equity_curve: List[float],
    initial_equity: float,
    num_trades: int = 0,
    total_traded_value: float = 0.0,
    risk_free_rate: float = 0.0,  # Annual rate
) -> EquityMetrics:
    """
    Compute portfolio metrics from equity curve.
    
    Args:
        equity_curve: List of equity values over time
        initial_equity: Starting equity
        num_trades: Number of trades executed
        total_traded_value: Sum of all trade notionals
        risk_free_rate: Annual risk-free rate for Sharpe calculation
        
    Returns:
        EquityMetrics object
    """
    if not equity_curve:
        return EquityMetrics(starting_equity=initial_equity)
    
    equity_array = np.array(equity_curve)
    
    # Basic return calculation
    starting = equity_curve[0] if equity_curve else initial_equity
    ending = equity_curve[-1] if equity_curve else initial_equity
    
    total_return_abs = ending - starting
    total_return = (total_return_abs / starting) if starting > 0 else 0.0
    
    # Peak equity
    peak_equity = float(np.max(equity_array))
    
    # Max drawdown
    max_dd = _compute_max_drawdown(equity_array)
    
    # Daily returns for volatility and Sharpe
    sharpe = None
    volatility = 0.0
    
    if len(equity_curve) > 1:
        returns = np.diff(equity_array) / equity_array[:-1]
        returns = returns[np.isfinite(returns)]
        
        if len(returns) > 0:
            # Annualized volatility (assuming daily data, 252 trading days)
            volatility = float(np.std(returns) * np.sqrt(252))
            
            # Sharpe ratio (annualized)
            if volatility > 0:
                mean_return = np.mean(returns) * 252  # Annualized return
                sharpe = (mean_return - risk_free_rate) / volatility
    
    # Turnover
    avg_equity = np.mean(equity_array) if len(equity_array) > 0 else initial_equity
    turnover = (total_traded_value / avg_equity) if avg_equity > 0 else 0.0
    
    logger.debug(f"Computed metrics: Return={total_return:.2%}, Sharpe={sharpe}, DD={max_dd:.2%}", extra={"total_return": total_return, "sharpe": sharpe, "max_drawdown": max_dd})
    
    return EquityMetrics(
        total_return=total_return,
        total_return_abs=total_return_abs,
        max_drawdown=max_dd,
        volatility=volatility,
        sharpe_ratio=sharpe,
        num_trades=num_trades,
        turnover=turnover,
        starting_equity=starting,
        ending_equity=ending,
        peak_equity=peak_equity,
    )


def _compute_max_drawdown(equity_array: np.ndarray) -> float:
    """
    Compute maximum drawdown from equity array.
    
    Returns drawdown as a positive percentage.
    """
    if len(equity_array) < 2:
        return 0.0
    
    # Running maximum
    running_max = np.maximum.accumulate(equity_array)
    
    # Drawdown at each point
    drawdowns = (running_max - equity_array) / running_max
    drawdowns = drawdowns[np.isfinite(drawdowns)]
    
    if len(drawdowns) == 0:
        return 0.0
    
    return float(np.max(drawdowns))


def compute_metrics_from_snapshots(
    snapshots: List[Snapshot],
    num_trades: int = 0,
    total_traded_value: float = 0.0,
) -> EquityMetrics:
    """
    Compute metrics from a list of snapshots.
    
    Args:
        snapshots: List of portfolio snapshots
        num_trades: Number of trades
        total_traded_value: Total traded notional
        
    Returns:
        EquityMetrics
    """
    if not snapshots:
        return EquityMetrics()
    
    equity_curve = [s.equity for s in snapshots]
    initial_equity = snapshots[0].equity
    
    return compute_metrics(
        equity_curve=equity_curve,
        initial_equity=initial_equity,
        num_trades=num_trades,
        total_traded_value=total_traded_value,
    )
