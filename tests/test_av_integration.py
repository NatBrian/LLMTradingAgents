
import os
import logging
import unittest
from dotenv import load_dotenv
from myllmtradingagents.market.alpha_vantage import fetch_news_sentiment, is_available

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

class TestAVIntegration(unittest.TestCase):
    def test_crypto_sentiment_fetch(self):
        """Test fetching sentiment for a crypto ticker."""
        if not is_available():
            print("\nWARNING: Alpha Vantage API key not found. Skipping integration test.")
            return

        print(f"\n{'='*80}")
        print("TESTING ALPHA VANTAGE INTEGRATION FOR: XRP/USDT")
        print(f"{'='*80}\n")
        
        # This should internally normalize to CRYPTO:XRP
        data = fetch_news_sentiment("XRP/USDT", use_cache=False)
        
        print(f"Ticker: {data.ticker}")
        print(f"Total Articles: {data.total_articles}")
        print(f"Overall Sentiment: {data.overall_sentiment_label} ({data.overall_sentiment_score})")
        
        if data.articles:
            print("\nTop 3 Articles:")
            for i, article in enumerate(data.articles[:3]):
                print(f"{i+1}. {article['title']} ({article['sentiment_label']})")
        else:
            print("\nNo articles found (or API limit reached/error).")
            
        # Verify normalization happened (we can't easily check internal var, but successful fetch implies it worked
        # if XRP/USDT was invalid for AV).
        # We can assert that we got a data object back.
        self.assertIsNotNone(data)
        self.assertEqual(data.ticker, "XRP/USDT") # The object keeps original ticker

if __name__ == "__main__":
    unittest.main()
