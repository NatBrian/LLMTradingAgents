"""Tests for ArenaRunner."""

import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import date

from myllmtradingagents.arena.runner import ArenaRunner
from myllmtradingagents.settings import ArenaConfig, CompetitorConfig, MarketConfig
from myllmtradingagents.llm.base import LLMResponse
from myllmtradingagents.schemas import StrategistProposal, TradePlan


class TestArenaRunner:
    """Tests for ArenaRunner."""
    
    @pytest.fixture
    def config(self):
        """Create sample arena config."""
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
    
    @patch("myllmtradingagents.arena.runner.SQLiteStorage")
    @patch("myllmtradingagents.arena.runner.create_market_adapter")
    @patch("myllmtradingagents.arena.runner.create_llm_client")
    def test_run_session_dry_run(self, mock_create_llm, mock_create_adapter, mock_storage_cls, config):
        """Test running a session in dry run mode."""
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage_cls.return_value = mock_storage
        # Mock has_run_today to False
        mock_storage.has_run_today.return_value = False
        mock_storage.get_daily_call_count.return_value = 0
        
        # Mock market adapter
        mock_adapter = MagicMock()
        mock_create_adapter.return_value = mock_adapter
        # Mock get_daily_bars to return empty df (handled gracefully)
        import pandas as pd
        mock_adapter.get_daily_bars.return_value = pd.DataFrame()
        # Mock prices
        mock_adapter.get_open_price.return_value = 150.0
        mock_adapter.get_latest_price.return_value = 150.0
        
        # Mock LLM client
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        
        # Mock LLM responses for Strategist and RiskGuard
        strategist_resp = {
            "session_date": "2024-01-01",
            "session_type": "OPEN",
            "proposals": [
                {"ticker": "AAPL", "action": "BUY", "confidence": 0.9}
            ]
        }
        
        risk_guard_resp = {
            "reasoning": "Approved",
            "orders": [
                {"ticker": "AAPL", "side": "BUY", "qty": 10}
            ]
        }
        
        mock_llm.generate.side_effect = [
            LLMResponse(content=json.dumps(strategist_resp)), # Strategist
            LLMResponse(content=json.dumps(risk_guard_resp))  # RiskGuard
        ]
        
        # Run session
        runner = ArenaRunner(config)
        results = runner.run_session(
            session_type="OPEN",
            session_date=date(2024, 1, 1),
            dry_run=True
        )
        
        assert "comp1" in results
        res = results["comp1"]
        assert "error" not in res
        assert res["strategist_proposal"] is not None
        assert res["trade_plan"] is not None
        
        # Verify calls
        mock_create_adapter.assert_called()
        mock_create_llm.assert_called()
        assert mock_llm.generate.call_count == 2
