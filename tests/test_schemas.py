"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime

from myllmtradingagents.schemas import (
    Order,
    Fill,
    Position,
    Snapshot,
    TradePlan,
    OrderSide,
    OrderType,
)


class TestOrderSchema:
    """Tests for Order schema."""
    
    def test_valid_order(self):
        """Test creating a valid order."""
        order = Order(
            ticker="AAPL",
            side=OrderSide.BUY,
            qty=10,
        )
        
        assert order.ticker == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.qty == 10
        assert order.order_type == OrderType.MARKET
    
    def test_ticker_uppercase(self):
        """Test ticker is converted to uppercase."""
        order = Order(ticker="aapl", side=OrderSide.BUY, qty=10)
        assert order.ticker == "AAPL"
    
    def test_invalid_qty(self):
        """Test invalid quantity raises error."""
        with pytest.raises(ValueError):
            Order(ticker="AAPL", side=OrderSide.BUY, qty=0)
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        order = Order(ticker="AAPL", side=OrderSide.BUY, qty=10)
        json_str = order.model_dump_json()
        
        assert "AAPL" in json_str
        assert "BUY" in json_str
        
        # Deserialize
        parsed = Order.model_validate_json(json_str)
        assert parsed.ticker == "AAPL"


class TestPositionSchema:
    """Tests for Position schema."""
    
    def test_position_metrics(self):
        """Test position computed properties."""
        pos = Position(
            ticker="AAPL",
            qty=100,
            avg_cost=100.0,
            current_price=110.0,
        )
        
        assert pos.market_value == 11000.0
        assert pos.unrealized_pnl == 1000.0
        assert pos.unrealized_pnl_pct == pytest.approx(10.0, rel=1e-4)
    
    def test_empty_position(self):
        """Test empty position metrics."""
        pos = Position(ticker="AAPL", qty=0)
        
        assert pos.market_value == 0
        assert pos.unrealized_pnl == 0
        assert pos.unrealized_pnl_pct == 0


class TestSnapshotSchema:
    """Tests for Snapshot schema."""
    
    def test_snapshot_equity(self):
        """Test snapshot equity calculation."""
        snapshot = Snapshot(
            cash=50000,
            positions=[
                Position(ticker="AAPL", qty=100, avg_cost=100, current_price=110),
                Position(ticker="GOOGL", qty=50, avg_cost=150, current_price=160),
            ],
        )
        
        # Equity = cash + positions value
        # = 50000 + (100 * 110) + (50 * 160)
        # = 50000 + 11000 + 8000 = 69000
        assert snapshot.equity == 69000
        assert snapshot.positions_value == 19000
    
    def test_unrealized_pnl(self):
        """Test snapshot unrealized P&L."""
        snapshot = Snapshot(
            cash=50000,
            positions=[
                Position(ticker="AAPL", qty=100, avg_cost=100, current_price=110),
            ],
        )
        
        assert snapshot.unrealized_pnl == 1000.0


class TestTradePlanSchema:
    """Tests for TradePlan schema."""
    
    def test_hold_decision(self):
        """Test HOLD decision (empty orders)."""
        plan = TradePlan(
            reasoning="Market conditions uncertain",
            orders=[],
        )
        
        assert plan.is_hold is True
        assert len(plan.orders) == 0
    
    def test_trade_decision(self):
        """Test trade decision with orders."""
        plan = TradePlan(
            reasoning="Strong buy signal",
            risk_assessment="Limited downside",
            orders=[
                Order(ticker="AAPL", side=OrderSide.BUY, qty=50),
                Order(ticker="GOOGL", side=OrderSide.SELL, qty=25),
            ],
        )
        
        assert plan.is_hold is False
        assert len(plan.orders) == 2
    
    def test_json_roundtrip(self):
        """Test JSON parsing from LLM output."""
        json_str = '''
        {
            "reasoning": "Buy AAPL on strength",
            "risk_assessment": "Normal risk",
            "orders": [
                {"ticker": "aapl", "side": "BUY", "qty": 10, "order_type": "MARKET"}
            ]
        }
        '''
        
        plan = TradePlan.model_validate_json(json_str)
        
        assert "AAPL" in plan.reasoning or plan.orders[0].ticker == "AAPL"
        assert plan.orders[0].side == OrderSide.BUY


# ============================================================================
# 3-Agent System Schema Tests
# ============================================================================

class TestProposedActionEnum:
    """Tests for ProposedAction enum (3-Agent System)."""
    
    def test_all_actions(self):
        """Test all proposed action values."""
        from myllmtradingagents.schemas import ProposedAction
        
        actions = [ProposedAction.BUY, ProposedAction.SELL, ProposedAction.HOLD]
        assert len(actions) == 3
    
    def test_from_string(self):
        """Test creating action from string."""
        from myllmtradingagents.schemas import ProposedAction
        
        action = ProposedAction("HOLD")
        assert action == ProposedAction.HOLD


class TestTickerProposalSchema:
    """Tests for TickerProposal schema (3-Agent System)."""
    
    def test_valid_proposal(self):
        """Test creating a valid ticker proposal."""
        from myllmtradingagents.schemas import TickerProposal, ProposedAction
        
        proposal = TickerProposal(
            ticker="AAPL",
            action=ProposedAction.BUY,
            confidence=0.85,
            rationale="Strong technical breakout",
            target_allocation_pct=10.0,
        )
        
        assert proposal.ticker == "AAPL"
        assert proposal.action == ProposedAction.BUY
        assert proposal.confidence == 0.85
    
    def test_ticker_uppercase(self):
        """Test ticker is converted to uppercase."""
        from myllmtradingagents.schemas import TickerProposal, ProposedAction
        
        proposal = TickerProposal(ticker="aapl", action=ProposedAction.HOLD, confidence=0.5)
        assert proposal.ticker == "AAPL"
    
    def test_confidence_bounds(self):
        """Test confidence must be 0-1."""
        from myllmtradingagents.schemas import TickerProposal, ProposedAction
        
        with pytest.raises(ValueError):
            TickerProposal(ticker="AAPL", action=ProposedAction.BUY, confidence=1.5)


class TestStrategistProposalSchema:
    """Tests for StrategistProposal schema (3-Agent System)."""
    
    def test_valid_proposal(self):
        """Test creating a valid strategist proposal."""
        from myllmtradingagents.schemas import StrategistProposal, TickerProposal, ProposedAction
        
        proposal = StrategistProposal(
            session_date="2024-01-15",
            session_type="OPEN",
            market_summary="Markets showing bullish momentum",
            proposals=[
                TickerProposal(
                    ticker="AAPL",
                    action=ProposedAction.BUY,
                    confidence=0.8,
                    rationale="RSI oversold, MACD crossover",
                ),
                TickerProposal(
                    ticker="GOOGL",
                    action=ProposedAction.HOLD,
                    confidence=0.6,
                    rationale="Mixed signals",
                ),
            ],
        )
        
        assert proposal.session_date == "2024-01-15"
        assert len(proposal.proposals) == 2
    
    def test_get_actionable_proposals(self):
        """Test filtering to actionable proposals only."""
        from myllmtradingagents.schemas import StrategistProposal, TickerProposal, ProposedAction
        
        proposal = StrategistProposal(
            session_date="2024-01-15",
            session_type="CLOSE",
            proposals=[
                TickerProposal(ticker="AAPL", action=ProposedAction.BUY, confidence=0.8),
                TickerProposal(ticker="GOOGL", action=ProposedAction.HOLD, confidence=0.5),
                TickerProposal(ticker="MSFT", action=ProposedAction.SELL, confidence=0.7),
            ],
        )
        
        actionable = proposal.get_actionable_proposals()
        assert len(actionable) == 2  # BUY and SELL only
        assert all(p.action != ProposedAction.HOLD for p in actionable)
    
    def test_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        from myllmtradingagents.schemas import StrategistProposal, TickerProposal, ProposedAction
        
        proposal = StrategistProposal(
            session_date="2024-01-15",
            session_type="OPEN",
            proposals=[
                TickerProposal(ticker="AAPL", action=ProposedAction.BUY, confidence=0.8),
            ],
        )
        
        json_str = proposal.model_dump_json()
        parsed = StrategistProposal.model_validate_json(json_str)
        
        assert parsed.session_date == "2024-01-15"
        assert parsed.proposals[0].ticker == "AAPL"
        assert parsed.proposals[0].action == ProposedAction.BUY
