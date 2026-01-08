"""
Simulated broker for paper trading.

Handles portfolio state, order validation, and position tracking.
"""

from datetime import datetime
from typing import Optional, List, Dict, Tuple
from copy import deepcopy

from ..schemas import Order, Fill, Position, Snapshot, OrderSide
from .fills import FillEngine
import logging

logger = logging.getLogger(__name__)


class SimBroker:
    """
    Simulated broker for paper trading.
    
    Manages portfolio state with cash and positions.
    Long-only, no leverage.
    """
    
    def __init__(
        self,
        initial_cash: float = 100000.0,
        slippage_bps: float = 10.0,
        fee_bps: float = 10.0,
        max_position_pct: float = 0.25,
    ):
        """
        Initialize broker.
        
        Args:
            initial_cash: Starting cash balance
            slippage_bps: Slippage in basis points
            fee_bps: Transaction fee in basis points
            max_position_pct: Max position size as fraction of portfolio
        """
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.realized_pnl = 0.0
        self.max_position_pct = max_position_pct
        
        self.fill_engine = FillEngine(
            slippage_bps=slippage_bps,
            fee_bps=fee_bps,
        )
        
        # Track all fills
        self.fill_history: List[Fill] = []
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """Get position for a ticker, or None if not held."""
        return self.positions.get(ticker.upper())
    
    def get_position_qty(self, ticker: str) -> int:
        """Get position quantity for a ticker."""
        pos = self.get_position(ticker)
        return pos.qty if pos else 0
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update current prices for all positions.
        
        Args:
            prices: Dict mapping ticker -> current price
        """
        for ticker, price in prices.items():
            ticker = ticker.upper()
            if ticker in self.positions:
                self.positions[ticker].current_price = price
    
    def get_snapshot(self, timestamp: Optional[datetime] = None) -> Snapshot:
        """Get current portfolio snapshot."""
        return Snapshot(
            timestamp=timestamp or datetime.utcnow(),
            cash=self.cash,
            positions=list(self.positions.values()),
            realized_pnl=self.realized_pnl,
        )
    
    def validate_order(
        self,
        order: Order,
        reference_price: float,
    ) -> Tuple[bool, str]:
        """
        Validate an order before execution.
        
        Args:
            order: Order to validate
            reference_price: Expected execution price
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        ticker = order.ticker.upper()
        
        if order.qty <= 0:
            return False, "Order quantity must be positive"
        
        if reference_price <= 0:
            return False, f"Invalid reference price: {reference_price}"
        
        if order.side == OrderSide.BUY:
            # Check cash sufficiency
            estimated_cost = order.qty * reference_price
            # Add buffer for fees and slippage
            estimated_cost *= 1.005  # 0.5% buffer
            
            if estimated_cost > self.cash:
                return False, f"Insufficient cash: need ${estimated_cost:.2f}, have ${self.cash:.2f}"
            
            # Check max position size
            current_equity = self.get_snapshot().equity
            if current_equity > 0:
                new_position_value = order.qty * reference_price
                current_position = self.get_position(ticker)
                if current_position:
                    new_position_value += current_position.market_value
                
                position_pct = new_position_value / (current_equity + estimated_cost)
                if position_pct > self.max_position_pct:
                    return False, f"Position would exceed max {self.max_position_pct:.0%}: {position_pct:.1%}"
        
        elif order.side == OrderSide.SELL:
            # Check position exists
            position = self.get_position(ticker)
            if not position or position.qty < order.qty:
                current_qty = position.qty if position else 0
                return False, f"Insufficient shares: need {order.qty}, have {current_qty}"
        
        return True, ""
    
    def execute_order(
        self,
        order: Order,
        fill_price: float,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Fill]:
        """
        Execute an order at the given price.
        
        Applies slippage and fees via FillEngine.
        
        Args:
            order: Order to execute
            fill_price: Base execution price (before slippage)
            timestamp: Execution timestamp
            
        Returns:
            Fill object if successful, None if failed
        """
        ticker = order.ticker.upper()
        timestamp = timestamp or datetime.utcnow()
        
        # Validate first
        is_valid, error = self.validate_order(order, fill_price)
        if not is_valid:
            logger.warning(f"Order validation failed: {error}", extra={"ticker": ticker, "order": order.model_dump(), "error": error})
            return None
        
        # Apply slippage and compute fill
        fill = self.fill_engine.fill_order(order, fill_price, timestamp)
        
        if order.side == OrderSide.BUY:
            self._process_buy(ticker, fill)
        else:
            self._process_sell(ticker, fill)
        
        self.fill_history.append(fill)
        return fill
    
    def _process_buy(self, ticker: str, fill: Fill) -> None:
        """Process a buy fill."""
        total_cost = fill.notional + fill.fees
        
        if ticker in self.positions:
            # Average into existing position
            pos = self.positions[ticker]
            new_qty = pos.qty + fill.qty
            new_cost = (pos.avg_cost * pos.qty + fill.fill_price * fill.qty) / new_qty
            pos.qty = new_qty
            pos.avg_cost = new_cost
            pos.current_price = fill.fill_price
        else:
            # New position
            self.positions[ticker] = Position(
                ticker=ticker,
                qty=fill.qty,
                avg_cost=fill.fill_price,
                current_price=fill.fill_price,
            )
        
        self.cash -= total_cost
    
    def _process_sell(self, ticker: str, fill: Fill) -> None:
        """Process a sell fill."""
        pos = self.positions[ticker]
        
        # Calculate realized P&L
        proceeds = fill.notional - fill.fees
        cost_basis = pos.avg_cost * fill.qty
        realized = proceeds - cost_basis
        
        self.realized_pnl += realized
        self.cash += proceeds
        
        # Update position
        pos.qty -= fill.qty
        pos.current_price = fill.fill_price
        
        # Remove position if fully closed
        if pos.qty <= 0:
            del self.positions[ticker]
    
    def execute_orders(
        self,
        orders: List[Order],
        prices: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> List[Fill]:
        """
        Execute multiple orders.
        
        Args:
            orders: List of orders to execute
            prices: Dict mapping ticker -> fill price
            timestamp: Execution timestamp
            
        Returns:
            List of successful fills
        """
        fills = []
        
        for order in orders:
            ticker = order.ticker.upper()
            price = prices.get(ticker)
            
            if price is None:
                logger.warning(f"No price available for {ticker}, skipping order", extra={"ticker": ticker})
                continue
            
            fill = self.execute_order(order, price, timestamp)
            if fill:
                fills.append(fill)
        
        return fills
    
    def reset(self) -> None:
        """Reset broker to initial state."""
        self.cash = self.initial_cash
        self.positions = {}
        self.realized_pnl = 0.0
        self.fill_history = []
    
    def get_state_dict(self) -> Dict:
        """Get broker state as dict for serialization."""
        return {
            "cash": self.cash,
            "positions": {
                ticker: pos.model_dump() for ticker, pos in self.positions.items()
            },
            "realized_pnl": self.realized_pnl,
        }
    
    def load_state_dict(self, state: Dict) -> None:
        """Load broker state from dict."""
        self.cash = state.get("cash", self.initial_cash)
        self.realized_pnl = state.get("realized_pnl", 0.0)
        
        self.positions = {}
        for ticker, pos_dict in state.get("positions", {}).items():
            self.positions[ticker] = Position(**pos_dict)
