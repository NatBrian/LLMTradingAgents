"""Tests for RiskGuard agent."""

import pytest
import json
from unittest.mock import MagicMock

from myllmtradingagents.agents.risk_guard import RiskGuard
from myllmtradingagents.llm.base import LLMClient, LLMResponse
from myllmtradingagents.schemas import (
    StrategistProposal,
    Snapshot,
    TradePlan,
    OrderSide,
    TickerProposal,
    ProposedAction
)


class TestRiskGuard:
    """Tests for RiskGuard agent."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        return MagicMock(spec=LLMClient)
    
    @pytest.fixture
    def risk_guard(self, mock_llm):
        """Create RiskGuard agent."""
        return RiskGuard(llm_client=mock_llm)
    
    @pytest.fixture
    def sample_context(self):
        """Create sample input context."""
        proposal = StrategistProposal(
            session_date="2024-01-15",
            session_type="OPEN",
            proposals=[
                TickerProposal(ticker="AAPL", action=ProposedAction.BUY, confidence=0.9)
            ]
        )
        
        snapshot = Snapshot(cash=100000)
        
        return {
            "proposal": proposal,
            "snapshot": snapshot,
            "prices": {"AAPL": 150.0}
        }
    
    def test_invoke_approve_trade(self, risk_guard, mock_llm, sample_context):
        """Test approving a trade."""
        # Mock LLM response
        plan_data = {
            "reasoning": "Approved AAPL buy",
            "risk_assessment": "Low risk",
            "orders": [
                {
                    "ticker": "AAPL",
                    "side": "BUY",
                    "qty": 10,
                    "order_type": "MARKET"
                }
            ]
        }
        
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps(plan_data)
        )
        
        result = risk_guard.invoke(sample_context)
        
        assert result.success
        assert isinstance(result.output, TradePlan)
        assert not result.output.is_hold
        assert len(result.output.orders) == 1
        assert result.output.orders[0].ticker == "AAPL"
    
    def test_invoke_veto_trade(self, risk_guard, mock_llm, sample_context):
        """Test vetoing a trade (returning empty orders)."""
        plan_data = {
            "reasoning": "Vetoed AAPL due to risk",
            "risk_assessment": "High volatility",
            "orders": []
        }
        
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps(plan_data)
        )
        
        result = risk_guard.invoke(sample_context)
        
        assert result.success
        assert result.output.is_hold
        assert len(result.output.orders) == 0
