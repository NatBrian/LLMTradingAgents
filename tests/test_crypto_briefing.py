import unittest
import logging
import json
from datetime import date
from dotenv import load_dotenv

from myllmtradingagents.market.fundamentals import fetch_fundamentals
from myllmtradingagents.market.price_history import fetch_price_history
from myllmtradingagents.market.briefing_builder import build_market_briefing
from myllmtradingagents.market.alpha_vantage import NewsSentimentData
from myllmtradingagents.agents.strategist import STRATEGIST_SYSTEM_PROMPT, STRATEGIST_USER_PROMPT
from myllmtradingagents.schemas import get_strategist_proposal_schema

# Configure logging
logging.basicConfig(level=logging.WARNING)
load_dotenv()

class TestCryptoBriefing(unittest.TestCase):
    def test_strategist_input(self):
        """Output the exact input provided to the Strategist agent for Crypto."""
        ticker = "XRP/USDT"
        
        # 1. Fetch live data (using the recently integrated CoinGecko & Alpha Vantage fixes)
        print(f"Fetching live data for {ticker}...")
        fundamentals = fetch_fundamentals(ticker)
        price_history = fetch_price_history(ticker)
        
        # 2. Build the MarketBriefing object
        # We manually add some news headlines for the test
        briefing = build_market_briefing(
            ticker=ticker,
            date=date.today().isoformat(),
            open_price=2.05,
            high_price=2.15,
            low_price=2.00,
            close_price=2.10,
            volume=1500000000,
            return_1d=0.024,
            volatility_20d=0.45,
            rsi_14=58.2,
            macd_line=0.05,
            macd_signal=0.03,
            macd_histogram=0.02,
            ma_20=2.02,
            ma_50=1.85,
            ma_200=1.20,
            fundamentals=fundamentals,
            price_history=price_history,
            news_headlines=[
                "XRP volume surges as adoption increases",
                "SEC vs Ripple: Final judgment expectations",
                "Major exchange relists XRP"
            ],
            news_sentiment=NewsSentimentData(
                ticker="XRP",
                overall_sentiment_score=0.45,
                overall_sentiment_label="Bullish",
                bullish_count=8,
                bearish_count=2,
                total_articles=10,
                articles=[
                    {
                        "title": "Global adoption of XRP grows", 
                        "sentiment_label": "Bullish", 
                        "sentiment_score": 0.8,
                        "summary": "The global adoption of Ripple's XRP is seeing a significant uptick as more financial institutions leverage its speed and low transaction costs for cross-border payments. Analysts predict this trend will continue."
                    },
                    {
                        "title": "Regulatory clarity for Ripple", 
                        "sentiment_label": "Neutral", 
                        "sentiment_score": 0.1,
                        "summary": "While recent court rulings have provided some clarity, the regulatory landscape remains complex. Market participants are cautiously optimistic about future developments in the SEC vs Ripple case."
                    }
                ]
            )
        )
        
        # 3. Emulate Strategist.invoke prompt construction
        briefing_str = briefing.to_prompt_string()
        schema_json = json.dumps(get_strategist_proposal_schema(), indent=2)
        
        system_prompt = STRATEGIST_SYSTEM_PROMPT.format(schema=schema_json)
        user_prompt = STRATEGIST_USER_PROMPT.format(
            session_date=date.today().isoformat(),
            session_type="OPEN",
            briefings=briefing_str
        )
        
        # 4. Output the exact strings
        print("\n" + "="*80)
        print("STRATEGIST SYSTEM PROMPT")
        print("="*80)
        print(system_prompt)
        
        print("\n" + "="*80)
        print("STRATEGIST USER PROMPT (Agent Input)")
        print("="*80)
        try:
            print(user_prompt)
        except UnicodeEncodeError:
            # Fallback for terminals with limited encoding support
            clean_prompt = user_prompt.replace("─", "-").replace("•", "*")
            print(clean_prompt)
        
        print("\n" + "="*80)

if __name__ == '__main__':
    unittest.main()
