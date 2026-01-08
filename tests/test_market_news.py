"""Tests for market/news.py."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from myllmtradingagents.market.news import fetch_headlines, fetch_news_articles, fetch_headlines_batch


class TestNewsFetcher:
    """Tests for news fetching functions."""
    
    @patch("myllmtradingagents.market.news.yf.Ticker")
    def test_fetch_news_articles(self, mock_ticker_cls):
        """Test fetching news articles."""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # Mock news response
        mock_ticker.news = [
            {
                "title": "AAPL Hits Record High",
                "publisher": "Bloomberg",
                "providerPublishTime": 1704067200,  # 2024-01-01
                "link": "http://example.com/1",
            },
            {
                "title": "Tech Stocks Rally",
                "publisher": "Reuters",
                "providerPublishTime": 1704153600,  # 2024-01-02
                "link": "http://example.com/2",
            }
        ]
        
        articles = fetch_news_articles("AAPL", limit=2)
        
        assert len(articles) == 2
        assert articles[0]["headline"] == "AAPL Hits Record High"
        assert articles[0]["source"] == "Bloomberg"
        assert articles[0]["url"] == "http://example.com/1"
        assert "2024" in articles[0]["date"]
        
        mock_ticker_cls.assert_called_with("AAPL")
    
    @patch("myllmtradingagents.market.news.yf.Ticker")
    def test_fetch_headlines(self, mock_ticker_cls):
        """Test fetching just headlines."""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        mock_ticker.news = [
            {"title": "Headline 1", "providerPublishTime": 1000},
            {"title": "Headline 2", "providerPublishTime": 2000},
        ]
        
        headlines = fetch_headlines("AAPL", max_headlines=2)
        
        assert len(headlines) == 2
        assert headlines[0] == "Headline 1"
        assert headlines[1] == "Headline 2"
    
    @patch("myllmtradingagents.market.news.yf.Ticker")
    def test_fetch_error_handling(self, mock_ticker_cls):
        """Test error handling returns empty list."""
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # Simulate error on property access
        # We need to mock the class property to raise exception
        type(mock_ticker).news = PropertyMock(side_effect=Exception("API Error"))
        
        headlines = fetch_headlines("AAPL")
        assert headlines == []
        
        articles = fetch_news_articles("AAPL")
        assert articles == []
    
    @patch("myllmtradingagents.market.news.fetch_headlines")
    def test_fetch_headlines_batch(self, mock_fetch):
        """Test batch fetching."""
        # Mock return values for different tickers
        mock_fetch.side_effect = lambda ticker, *args, **kwargs: [f"News for {ticker}"]
        
        result = fetch_headlines_batch(["AAPL", "GOOGL"])
        
        assert len(result) == 2
        assert result["AAPL"] == ["News for AAPL"]
        assert result["GOOGL"] == ["News for GOOGL"]
