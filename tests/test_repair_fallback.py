"""Tests for JSON repair fallback."""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import date

from myllmtradingagents.arena.runner import ArenaRunner
from myllmtradingagents.settings import ArenaConfig, CompetitorConfig, MarketConfig
from myllmtradingagents.llm.base import LLMResponse

class TestRepairFallback:
    
    @pytest.fixture
    def config(self):
        return ArenaConfig(
            db_path=":memory:",
            competitors=[
                CompetitorConfig(
                    id="comp1",
                    name="Test Competitor",
                    provider="mock",
                    model="mock-model",
                    initial_cash=100000,
                )
            ],
            markets=[
                MarketConfig(
                    type="us_equity",
                    tickers=["AAPL"]
                )
            ]
        )
    
    @patch("myllmtradingagents.arena.runner.ArenaRunner._build_briefings")
    @patch("myllmtradingagents.arena.runner.SQLiteStorage")
    @patch("myllmtradingagents.arena.runner.create_market_adapter")
    @patch("myllmtradingagents.arena.runner.create_llm_client")
    def test_risk_guard_empty_response_repair(
        self, 
        mock_create_llm, 
        mock_create_adapter, 
        mock_storage_cls, 
        mock_build_briefings,
        config
    ):
        """Test that empty response from RiskGuard triggers repair."""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage
        mock_storage.has_run_today.return_value = False
        mock_storage.get_daily_call_count.return_value = 0
        mock_storage.get_latest_snapshot.return_value = None
        
        mock_adapter = MagicMock()
        mock_create_adapter.return_value = mock_adapter
        import pandas as pd
        mock_adapter.get_daily_bars.return_value = pd.DataFrame()
        mock_adapter.get_open_price.return_value = 150.0
        mock_adapter.get_latest_price.return_value = 150.0
        
        # Mock briefings
        mock_briefing = MagicMock()
        mock_briefing.to_prompt_string.return_value = "Mock Briefing Data"
        mock_build_briefings.return_value = [mock_briefing]
        
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        
        # 1. Strategist Response (Valid)
        strategist_resp = {
            "session_date": "2024-01-01",
            "session_type": "OPEN",
            "proposals": [
                {"ticker": "AAPL", "action": "BUY", "confidence": 0.9, "rationale": "Test"}
            ]
        }
        
        # 2. RiskGuard Response (Empty/Invalid) - Attempt 1
        risk_guard_resp_empty = ""
        
        # 3. RiskGuard Response (Valid) - Attempt 2 (Retry)
        risk_guard_resp_valid = {
            "reasoning": "Approved on retry",
            "risk_assessment": "Safe",
            "orders": [
                {"ticker": "AAPL", "side": "BUY", "qty": 10}
            ]
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(strategist_resp)), # Strategist
            LLMResponse(content=risk_guard_resp_empty),       # RiskGuard (Attempt 1 - Fail)
            LLMResponse(content=json.dumps(risk_guard_resp_valid)) # RiskGuard (Attempt 2 - Success)
        ]
        
        # Run session (dry_run=False to trigger storage calls)
        runner = ArenaRunner(config)
        results = runner.run_session(
            session_type="OPEN",
            session_date=date(2024, 1, 1),
            dry_run=False
        )
        
        assert "comp1" in results
        res = results["comp1"]
        
        # Verify that we got a trade plan (from retry)
        assert res["trade_plan"] is not None
        assert res["trade_plan"]["reasoning"] == "Approved on retry"
        assert len(res["trade_plan"]["orders"]) == 1
        
        # Verify calls
        # Should be 3 calls: Strategist, RiskGuard (Fail), RiskGuard (Retry)
        assert mock_llm.generate.call_count == 3
        
        # Verify call accounting
        # increment_call_count should be called with 3 (len(llm_calls))
        mock_storage.increment_call_count.assert_called_with("mock", "2024-01-01", 3)
