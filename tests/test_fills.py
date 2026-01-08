"""Tests for FillEngine."""

import pytest

from myllmtradingagents.sim.fills import FillEngine
from myllmtradingagents.schemas import Order, OrderSide, OrderType


class TestFillEngine:
    """Test suite for FillEngine."""
    
    def test_no_slippage_no_fees(self):
        """Test fill with zero slippage and fees."""
        engine = FillEngine(slippage_bps=0, fee_bps=0)
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        fill = engine.fill_order(order, base_price=100.0)
        
        assert fill.fill_price == 100.0
        assert fill.fees == 0.0
        assert fill.slippage == 0.0
        assert fill.notional == 1000.0
    
    def test_slippage_buy(self):
        """Test slippage on buy order (price increases)."""
        engine = FillEngine(slippage_bps=10, fee_bps=0)  # 0.1%
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=100)
        fill = engine.fill_order(order, base_price=100.0)
        
        # Expected: 100 * (1 + 0.001) = 100.10
        assert fill.fill_price == pytest.approx(100.10, rel=1e-4)
        assert fill.slippage == pytest.approx(10.0, rel=1e-4)  # 100 * 0.10
    
    def test_slippage_sell(self):
        """Test slippage on sell order (price decreases)."""
        engine = FillEngine(slippage_bps=10, fee_bps=0)  # 0.1%
        
        order = Order(ticker="AAPL", side=OrderSide.SELL, qty=100)
        fill = engine.fill_order(order, base_price=100.0)
        
        # Expected: 100 * (1 - 0.001) = 99.90
        assert fill.fill_price == pytest.approx(99.90, rel=1e-4)
        assert fill.slippage == pytest.approx(-10.0, rel=1e-4)  # Negative for sell
    
    def test_fees(self):
        """Test fee calculation."""
        engine = FillEngine(slippage_bps=0, fee_bps=20)  # 0.2%
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=100)
        fill = engine.fill_order(order, base_price=100.0)
        
        # Notional: 100 * 100 = 10000
        # Fee: 10000 * 0.002 = 20
        assert fill.fees == pytest.approx(20.0, rel=1e-4)
    
    def test_combined_slippage_and_fees(self):
        """Test both slippage and fees together."""
        engine = FillEngine(slippage_bps=10, fee_bps=10)  # 0.1% each
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=100)
        fill = engine.fill_order(order, base_price=100.0)
        
        # Fill price: 100 * 1.001 = 100.10
        assert fill.fill_price == pytest.approx(100.10, rel=1e-4)
        
        # Notional: 100 * 100.10 = 10010
        # Fee: 10010 * 0.001 = 10.01
        assert fill.fees == pytest.approx(10.01, rel=1e-4)
    
    def test_fill_from_order(self):
        """Test creating fill from order object."""
        engine = FillEngine(slippage_bps=5, fee_bps=5)
        
        order = Order(
            ticker="GOOGL",
            side=OrderSide.SELL,
            qty=50,
            order_type=OrderType.MARKET,
        )
        
        fill = engine.fill_order(order, base_price=150.0)
        
        assert fill.ticker == "GOOGL"
        assert fill.side == OrderSide.SELL
        assert fill.qty == 50
        assert fill.order_type == OrderType.MARKET
    
    def test_simulate_fill(self):
        """Test fill simulation (preview)."""
        engine = FillEngine(slippage_bps=10, fee_bps=10)
        
        result = engine.simulate_fill(
            ticker="AAPL",
            side=OrderSide.BUY,
            qty=100,
            base_price=100.0,
        )
        
        assert result["ticker"] == "AAPL"
        assert result["side"] == "BUY"
        assert result["qty"] == 100
        assert result["base_price"] == 100.0
        assert result["fill_price"] == pytest.approx(100.10, rel=1e-4)
        assert result["total_cost"] > 0
        assert result["total_proceeds"] == 0
    
    def test_large_slippage(self):
        """Test with larger slippage value."""
        engine = FillEngine(slippage_bps=100, fee_bps=0)  # 1%
        
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        fill = engine.fill_order(order, base_price=100.0)
        
        # Expected: 100 * 1.01 = 101.0
        assert fill.fill_price == pytest.approx(101.0, rel=1e-4)
