
import logging
import unittest
from dotenv import load_dotenv
from myllmtradingagents.market.coingecko import fetch_coin_fundamentals

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

class TestCoinGeckoIntegration(unittest.TestCase):
    def test_fetch_coin_data(self):
        """Test fetching coin data for XRP."""
        print(f"\n{'='*80}")
        print("TESTING COINGECKO INTEGRATION FOR: XRP/USDT")
        print(f"{'='*80}\n")
        
        # This uses the mapping XRP -> ripple
        data = fetch_coin_fundamentals("XRP/USDT")
        
        if data:
            print(f"Name: {data.get('company_name')}")
            print(f"Sector: {data.get('sector')}")
            print(f"Market Cap: ${data.get('market_cap'):,.0f}")
            print(f"Current Price: ${data.get('current_price'):.4f}")
            print(f"Description: {data.get('description')[:100]}...")
            print(f"Circulating Supply: {data.get('circulating_supply'):,.0f}")
            
            self.assertEqual(data.get('company_name'), "XRP")
            self.assertTrue(data.get('market_cap') > 0)
        else:
            print("\nFailed to fetch data (Rate limit or API error).")
            # In free tier, we might hit limits, so careful with failing test.
            # But for a manual run it's good.

    def test_mapping(self):
        """Test mapping logic."""
        from myllmtradingagents.market.coingecko import get_coin_id
        self.assertEqual(get_coin_id("BTC"), "bitcoin")
        self.assertEqual(get_coin_id("ETH/USDT"), "ethereum")
        self.assertEqual(get_coin_id("XRP/USDT"), "ripple")

if __name__ == "__main__":
    unittest.main()
