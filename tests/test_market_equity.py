"""Tests for market/equity.py."""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from myllmtradingagents.market.equity import USEquityAdapter


class TestUSEquityAdapter:
    """Tests for USEquityAdapter."""
    
    @pytest.fixture
    def adapter(self, tmp_path):
        """Create adapter with temporary cache dir."""
        return USEquityAdapter(cache_dir=str(tmp_path), cache_days=1)
    
    @patch("yfinance.Ticker")
    def test_get_daily_bars_fetch(self, mock_ticker_cls, adapter):
        """Test fetching daily bars from yfinance."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # Mock history return
        dates = pd.date_range(start="2024-01-01", periods=5)
        df = pd.DataFrame({
            "Open": [100.0] * 5,
            "High": [105.0] * 5,
            "Low": [95.0] * 5,
            "Close": [102.0] * 5,
            "Volume": [1000] * 5,
        }, index=dates)
        # yfinance returns index as DatetimeIndex named "Date" or "Datetime"
        df.index.name = "Date"
        
        mock_ticker.history.return_value = df
        
        # Call method
        bars = adapter.get_daily_bars("AAPL", days=5, end_date=date(2024, 1, 10))
        
        assert not bars.empty
        assert len(bars) == 5
        assert "Date" in bars.columns
        assert bars.iloc[0]["Close"] == 102.0
        
        # Verify yfinance call
        mock_ticker_cls.assert_called_with("AAPL")
        mock_ticker.history.assert_called_once()
    
    @patch("yfinance.Ticker")
    def test_get_daily_bars_cache(self, mock_ticker_cls, adapter):
        """Test caching of daily bars."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        dates = pd.date_range(start="2024-01-01", periods=5)
        df = pd.DataFrame({
            "Open": [100.0] * 5,
            "High": [105.0] * 5,
            "Low": [95.0] * 5,
            "Close": [102.0] * 5,
            "Volume": [1000] * 5,
        }, index=dates)
        df.index.name = "Date"
        mock_ticker.history.return_value = df
        
        # First call - should fetch
        adapter.get_daily_bars("AAPL", days=5, end_date=date(2024, 1, 10))
        assert mock_ticker.history.call_count == 1
        
        # Second call - should hit cache
        adapter.get_daily_bars("AAPL", days=5, end_date=date(2024, 1, 10))
        assert mock_ticker.history.call_count == 1  # Still 1
    
    @patch("yfinance.Ticker")
    def test_get_latest_price(self, mock_ticker_cls, adapter):
        """Test getting latest price via fast_info."""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # Mock fast_info as a dict-like object
        mock_ticker.fast_info = {"last_price": 150.50}
        
        price = adapter.get_latest_price("AAPL")
        
        assert price == 150.50
        mock_ticker_cls.assert_called_with("AAPL")
    
    @patch("yfinance.Ticker")
    def test_get_latest_price_fallback(self, mock_ticker_cls, adapter):
        """Test fallback when fast_info fails."""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # fast_info empty or raises
        mock_ticker.fast_info = {}
        
        # Mock history for fallback
        dates = pd.date_range(start="2024-01-01", periods=1)
        df = pd.DataFrame({
            "Open": [100.0],
            "High": [105.0],
            "Low": [95.0],
            "Close": [145.0],
            "Volume": [1000],
        }, index=dates)
        df.index.name = "Date"
        mock_ticker.history.return_value = df
        
        price = adapter.get_latest_price("AAPL")
        
        assert price == 145.0
    
    @patch("yfinance.Ticker")
    def test_get_open_price_realtime(self, mock_ticker_cls, adapter):
        """Test getting real-time open price."""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # Mock fast_info
        mock_ticker.fast_info = {"open": 155.0}
        
        # Request for today
        price = adapter.get_open_price("AAPL", date.today())
        
        assert price == 155.0
