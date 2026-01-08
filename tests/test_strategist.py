"""Tests for Strategist agent."""

import pytest
import json
from unittest.mock import MagicMock

from myllmtradingagents.agents.strategist import Strategist
from myllmtradingagents.llm.base import LLMClient, LLMResponse
from myllmtradingagents.schemas import StrategistProposal, ProposedAction


class TestStrategist:
    """Tests for Strategist agent."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        return MagicMock(spec=LLMClient)
    
    @pytest.fixture
    def strategist(self, mock_llm):
        """Create Strategist agent."""
        return Strategist(llm_client=mock_llm)
    
    def test_invoke_valid_response(self, strategist, mock_llm):
        """Test invoking strategist with valid LLM response."""
        # Mock LLM response
        proposal_data = {
            "session_date": "2024-01-15",
            "session_type": "OPEN",
            "market_summary": "Bullish market",
            "proposals": [
                {
                    "ticker": "AAPL",
                    "action": "BUY",
                    "confidence": 0.9,
                    "rationale": "Strong signals",
                    "target_allocation_pct": 10.0
                }
            ]
        }
        
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps(proposal_data),
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=500
        )
        
        # Invoke
        context = {
            "session_date": "2024-01-15",
            "session_type": "OPEN",
            "briefings": []  # Can be empty for this test
        }
        result = strategist.invoke(context)
        
        assert result.success
        assert isinstance(result.output, StrategistProposal)
        assert len(result.output.proposals) == 1
        assert result.output.proposals[0].ticker == "AAPL"
        assert result.output.proposals[0].action == ProposedAction.BUY
        
        # Verify LLM called
        mock_llm.generate.assert_called_once()
    
    def test_invoke_json_cleaning(self, strategist, mock_llm):
        """Test that markdown code blocks are cleaned."""
        proposal_data = {
            "session_date": "2024-01-15",
            "session_type": "OPEN",
            "proposals": []
        }
        
        # Wrap in markdown
        content = f"```json\n{json.dumps(proposal_data)}\n```"
        
        mock_llm.generate.return_value = LLMResponse(
            content=content,
        )
        
        result = strategist.invoke({"session_date": "2024-01-15"})
        
        assert result.success
        assert isinstance(result.output, StrategistProposal)
    
    def test_invoke_failure(self, strategist, mock_llm):
        """Test handling of LLM failure."""
        mock_llm.generate.return_value = LLMResponse(
            content="",
            error="API Error"
        )
        
        result = strategist.invoke({"session_date": "2024-01-15"})
        
        assert not result.success
        assert result.error == "API Error"
        assert result.output is None
    
    def test_invoke_invalid_json(self, strategist, mock_llm):
        """Test handling of invalid JSON."""
        mock_llm.generate.return_value = LLMResponse(
            content="Not JSON"
        )
        
        result = strategist.invoke({"session_date": "2024-01-15"})
        
        assert not result.success
        assert "JSON parse error" in result.error
