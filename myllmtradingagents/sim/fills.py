"""
Fill engine for order execution with slippage and fees.
"""

from datetime import datetime
from typing import Optional

from ..schemas import Order, Fill, OrderSide
import logging

logger = logging.getLogger(__name__)


class FillEngine:
    """
    Engine for computing order fills with slippage and fees.
    """
    
    def __init__(
        self,
        slippage_bps: float = 10.0,
        fee_bps: float = 10.0,
    ):
        """
        Initialize fill engine.
        
        Args:
            slippage_bps: Slippage in basis points (10 = 0.1%)
            fee_bps: Transaction fee in basis points (10 = 0.1%)
        """
        self.slippage_bps = slippage_bps
        self.fee_bps = fee_bps
    
    def compute_slippage(self, base_price: float, side: OrderSide) -> float:
        """
        Compute slippage amount.
        
        For BUY: slippage is positive (you pay more)
        For SELL: slippage is negative (you receive less)
        
        Args:
            base_price: Base execution price
            side: Order side (BUY or SELL)
            
        Returns:
            Slippage amount (can be positive or negative)
        """
        slippage_pct = self.slippage_bps / 10000.0
        slippage_amount = base_price * slippage_pct
        
        if side == OrderSide.BUY:
            return slippage_amount  # Pay more
        else:
            return -slippage_amount  # Receive less
    
    def compute_fill_price(self, base_price: float, side: OrderSide) -> float:
        """
        Compute fill price after slippage.
        
        Args:
            base_price: Base execution price
            side: Order side
            
        Returns:
            Fill price including slippage
        """
        slippage = self.compute_slippage(base_price, side)
        return base_price + slippage
    
    def compute_fees(self, notional: float) -> float:
        """
        Compute transaction fees.
        
        Args:
            notional: Transaction value (qty * price)
            
        Returns:
            Fee amount
        """
        return notional * (self.fee_bps / 10000.0)
    
    def fill_order(
        self,
        order: Order,
        base_price: float,
        timestamp: Optional[datetime] = None,
    ) -> Fill:
        """
        Create a fill for an order.
        
        Args:
            order: Order to fill
            base_price: Base execution price (e.g., open or close price)
            timestamp: Fill timestamp
            
        Returns:
            Fill object with computed prices and fees
        """
        # Compute fill price with slippage
        fill_price = self.compute_fill_price(base_price, order.side)
        
        # Compute notional value
        notional = order.qty * fill_price
        
        # Compute fees
        fees = self.compute_fees(notional)
        
        # Compute slippage amount for record keeping
        slippage = self.compute_slippage(base_price, order.side) * order.qty
        
        logger.debug(f"Computed fill for {order.ticker}", extra={"ticker": order.ticker, "side": order.side, "qty": order.qty, "base_price": base_price, "fill_price": fill_price, "fees": fees})
        
        return Fill.from_order(
            order=order,
            fill_price=fill_price,
            fees=fees,
            slippage=slippage,
            timestamp=timestamp or datetime.utcnow(),
        )
    
    def simulate_fill(
        self,
        ticker: str,
        side: OrderSide,
        qty: int,
        base_price: float,
    ) -> dict:
        """
        Simulate a fill without creating an order.
        
        Useful for previewing order costs.
        
        Args:
            ticker: Ticker symbol
            side: BUY or SELL
            qty: Quantity
            base_price: Base price
            
        Returns:
            Dict with fill simulation details
        """
        fill_price = self.compute_fill_price(base_price, side)
        notional = qty * fill_price
        fees = self.compute_fees(notional)
        slippage = self.compute_slippage(base_price, side) * qty
        
        if side == OrderSide.BUY:
            total_cost = notional + fees
            total_proceeds = 0.0
        else:
            total_cost = 0.0
            total_proceeds = notional - fees
        
        return {
            "ticker": ticker,
            "side": side.value,
            "qty": qty,
            "base_price": base_price,
            "fill_price": fill_price,
            "slippage": slippage,
            "notional": notional,
            "fees": fees,
            "total_cost": total_cost,
            "total_proceeds": total_proceeds,
        }
