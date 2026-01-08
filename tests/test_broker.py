"""Tests for SimBroker."""

import pytest
from datetime import datetime

from myllmtradingagents.sim.broker import SimBroker
from myllmtradingagents.schemas import Order, OrderSide, OrderType


class TestSimBroker:
    """Test suite for SimBroker."""
    
    def test_init(self):
        """Test broker initialization."""
        broker = SimBroker(initial_cash=100000)
        
        assert broker.cash == 100000
        assert broker.initial_cash == 100000
        assert len(broker.positions) == 0
        assert broker.realized_pnl == 0.0
    
    def test_get_snapshot(self):
        """Test portfolio snapshot."""
        broker = SimBroker(initial_cash=50000)
        snapshot = broker.get_snapshot()
        
        assert snapshot.cash == 50000
        assert snapshot.equity == 50000
        assert len(snapshot.positions) == 0
    
    def test_buy_order(self):
        """Test executing a buy order."""
        broker = SimBroker(initial_cash=100000, slippage_bps=0, fee_bps=0)
        
        order = Order(
            ticker="AAPL",
            side=OrderSide.BUY,
            qty=10,
            order_type=OrderType.MARKET,
        )
        
        fill = broker.execute_order(order, fill_price=150.0)
        
        assert fill is not None
        assert fill.ticker == "AAPL"
        assert fill.qty == 10
        assert fill.fill_price == 150.0
        
        # Check position created
        pos = broker.get_position("AAPL")
        assert pos is not None
        assert pos.qty == 10
        assert pos.avg_cost == 150.0
        
        # Check cash deducted
        assert broker.cash == 100000 - (10 * 150)
    
    def test_sell_order(self):
        """Test executing a sell order."""
        broker = SimBroker(initial_cash=100000, slippage_bps=0, fee_bps=0)
        
        # First buy
        buy_order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        broker.execute_order(buy_order, fill_price=100.0)
        
        # Then sell
        sell_order = Order(ticker="AAPL", side=OrderSide.SELL, qty=5)
        fill = broker.execute_order(sell_order, fill_price=120.0)
        
        assert fill is not None
        assert fill.qty == 5
        
        # Check position reduced
        pos = broker.get_position("AAPL")
        assert pos.qty == 5
        
        # Check realized P&L (sold 5 @ 120, cost 5 @ 100 = $100 profit)
        assert broker.realized_pnl == 100.0
    
    def test_sell_all_closes_position(self):
        """Test selling entire position removes it."""
        broker = SimBroker(initial_cash=100000, slippage_bps=0, fee_bps=0)
        
        buy_order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        broker.execute_order(buy_order, fill_price=100.0)
        
        sell_order = Order(ticker="AAPL", side=OrderSide.SELL, qty=10)
        broker.execute_order(sell_order, fill_price=110.0)
        
        assert broker.get_position("AAPL") is None
        assert broker.realized_pnl == 100.0  # 10 * (110 - 100)
    
    def test_insufficient_cash(self):
        """Test buy order fails with insufficient cash."""
        broker = SimBroker(initial_cash=1000, slippage_bps=0, fee_bps=0)
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=100)
        
        is_valid, error = broker.validate_order(order, reference_price=150.0)
        
        assert not is_valid
        assert "Insufficient cash" in error
    
    def test_insufficient_shares(self):
        """Test sell order fails with insufficient shares."""
        broker = SimBroker(initial_cash=100000)
        
        order = Order(ticker="AAPL", side=OrderSide.SELL, qty=10)
        
        is_valid, error = broker.validate_order(order, reference_price=150.0)
        
        assert not is_valid
        assert "Insufficient shares" in error
    
    def test_max_position_constraint(self):
        """Test max position percentage constraint."""
        broker = SimBroker(
            initial_cash=100000,
            max_position_pct=0.10,  # 10% max
            slippage_bps=0,
            fee_bps=0,
        )
        
        # Try to buy 20% of portfolio
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=200)  # 200 * 100 = 20000 = 20%
        
        is_valid, error = broker.validate_order(order, reference_price=100.0)
        
        assert not is_valid
        assert "exceed max" in error.lower()
    
    def test_averaging_into_position(self):
        """Test averaging into an existing position."""
        broker = SimBroker(initial_cash=100000, slippage_bps=0, fee_bps=0)
        
        # Buy 10 @ 100
        order1 = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        broker.execute_order(order1, fill_price=100.0)
        
        # Buy 10 more @ 120
        order2 = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        broker.execute_order(order2, fill_price=120.0)
        
        pos = broker.get_position("AAPL")
        assert pos.qty == 20
        assert pos.avg_cost == 110.0  # (10 * 100 + 10 * 120) / 20
    
    def test_multiple_positions(self):
        """Test holding multiple positions."""
        broker = SimBroker(initial_cash=100000, slippage_bps=0, fee_bps=0)
        
        order1 = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        order2 = Order(ticker="GOOGL", side=OrderSide.BUY, qty=5)
        
        broker.execute_order(order1, fill_price=150.0)
        broker.execute_order(order2, fill_price=200.0)
        
        assert len(broker.positions) == 2
        assert broker.get_position("AAPL").qty == 10
        assert broker.get_position("GOOGL").qty == 5
    
    def test_update_prices(self):
        """Test updating position prices."""
        broker = SimBroker(initial_cash=100000, slippage_bps=0, fee_bps=0)
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        broker.execute_order(order, fill_price=100.0)
        
        broker.update_prices({"AAPL": 110.0})
        
        pos = broker.get_position("AAPL")
        assert pos.current_price == 110.0
        assert pos.unrealized_pnl == 100.0  # 10 * (110 - 100)
    
    def test_reset(self):
        """Test broker reset."""
        broker = SimBroker(initial_cash=50000)
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        broker.execute_order(order, fill_price=100.0)
        
        broker.reset()
        
        assert broker.cash == 50000
        assert len(broker.positions) == 0
        assert broker.realized_pnl == 0.0
