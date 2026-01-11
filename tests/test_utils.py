
import unittest
from myllmtradingagents.market.utils import normalize_alpha_vantage_ticker, normalize_yahoo_ticker

class TestTickerNormalization(unittest.TestCase):
    def test_alpha_vantage_normalization(self):
        self.assertEqual(normalize_alpha_vantage_ticker("XRP/USDT"), "CRYPTO:XRP")
        self.assertEqual(normalize_alpha_vantage_ticker("BTC/USDT"), "CRYPTO:BTC")
        self.assertEqual(normalize_alpha_vantage_ticker("BTCUSDT"), "CRYPTO:BTC")
        self.assertEqual(normalize_alpha_vantage_ticker("AAPL"), "AAPL")
        print("Alpha Vantage Normalization: ALL PASS")

    def test_yahoo_normalization(self):
        self.assertEqual(normalize_yahoo_ticker("XRP/USDT"), "XRP-USD")
        self.assertEqual(normalize_yahoo_ticker("BTC/USDT"), "BTC-USD")
        self.assertEqual(normalize_yahoo_ticker("AAPL"), "AAPL")
        print("Yahoo Normalization: ALL PASS")

if __name__ == "__main__":
    unittest.main()
