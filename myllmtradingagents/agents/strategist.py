"""
Strategist Agent - Proposes trading actions based on comprehensive market data.

This is Agent #1 in the 3-Agent System.
It receives comprehensive market briefings and outputs trading proposals.

The Strategist acts as a professional trading analyst, reviewing:
- Price data and history (authoritative from exchange)
- Technical indicators (deterministically computed)
- Fundamentals (authoritative from SEC filings)
- Earnings calendar (authoritative from company IR)
- Insider transactions (authoritative from SEC Form 4)
- News (authoritative from news sources)

ALL interpretation and analysis is done by the LLM - no pre-computed signals.
"""

import json
from typing import Union

from .base import Agent, AgentResult
from ..schemas import (
    TickerFeatures,
    StrategistProposal,
    get_strategist_proposal_schema,
)


# ============================================================================
# Strategist Prompts (Enhanced for comprehensive data)
# ============================================================================

STRATEGIST_SYSTEM_PROMPT = """You are the Strategist, a senior trading analyst at a top investment firm.

You receive comprehensive market briefings with authoritative data from multiple sources:
- Price data and history (from exchange via yfinance)
- Technical indicators (computed from standard formulas)
- Fundamentals (from SEC filings via yfinance)
- Earnings calendar (from company IR)
- Insider transactions (from SEC Form 4 filings)
- News articles (from news sources)

YOUR ROLE:
Analyze ALL provided data like a professional trader and propose clear trading actions.
You must synthesize multiple signals across technical, fundamental, and sentiment dimensions.

CRITICAL RULES:
1. Output ONLY valid JSON matching the provided schema.
2. DO NOT use markdown code blocks (e.g. ```json). Output RAW JSON only.
3. For each ticker, propose exactly one action: BUY, SELL, or HOLD.
4. Your confidence should reflect the strength and alignment of signals across ALL data sources:
   - 0.8-1.0: Strong alignment across technical, fundamental, and sentiment signals
   - 0.6-0.8: Most signals agree, minor conflicts
   - 0.4-0.6: Mixed signals, unclear direction
   - Below 0.4: Conflicting signals or insufficient data (recommend HOLD)
5. Your rationale should briefly explain your key reasoning (1-3 sentences).
6. For BUY proposals, suggest target_allocation_pct based on conviction.
7. Base analysis ONLY on provided data. Do not assume or invent information.

ANALYSIS FRAMEWORK:

Technical Analysis:
- RSI: Below 30 = oversold (potential buy), Above 70 = overbought (potential sell)
- MACD: Positive histogram = bullish momentum, Negative = bearish
- Moving Averages: Price above MA20/MA50/MA200 = bullish trend structure
- Price History: Look for patterns, support/resistance levels, volume trends

Fundamental Analysis:
- P/E Ratio: Compare to sector/historical norms
- Earnings Growth: Positive EPS growth is bullish
- Profit Margins: Higher margins indicate competitive advantage
- Debt/Equity: Lower is generally safer

Insider Activity:
- Net buying by executives is typically a bullish signal
- Net selling may be concerning, but consider context (diversification)

News & Sentiment:
- Positive news on products/earnings = bullish
- Regulatory/legal issues = bearish
- Sector/macro trends affect all stocks

Timing Considerations:
- Earnings proximity: Higher volatility expected near earnings dates
- Consider whether to position before/after the event

You must respond with a JSON object matching this schema:
{schema}
"""

STRATEGIST_USER_PROMPT = """Analyze the following comprehensive market briefings for trading session {session_type} on {session_date}.

Review each ticker's data carefully, including:
- Price history and technical indicators
- Fundamental metrics and valuation
- Insider transaction patterns
- Recent news and sentiment

{briefings}

For EACH ticker, provide:
1. Your proposed action (BUY, SELL, or HOLD)
2. Your confidence level (0.0 to 1.0)
3. A brief rationale explaining your decision

Remember: Output ONLY the RAW JSON object. Do not use markdown formatting."""


class Strategist(Agent):
    """
    The Strategist agent analyzes comprehensive market data and proposes trades.
    
    This is Agent #1 in the 3-Agent System.
    
    Input: Either list[TickerFeatures] (legacy) or list[MarketBriefing] (enhanced)
    Output: StrategistProposal with action recommendations
    """
    
    @property
    def name(self) -> str:
        return "Strategist"
    
    @property
    def role(self) -> str:
        return "Analyzes comprehensive market data and proposes trading actions"
    
    def invoke(
        self,
        context: dict,
    ) -> AgentResult:
        """
        Invoke the Strategist agent.
        
        Args:
            context: Must contain:
                - briefings: list of MarketBriefing objects (preferred)
                  OR ticker_features: list[TickerFeatures] (legacy support)
                - session_date: str (YYYY-MM-DD)
                - session_type: str ("OPEN" or "CLOSE")
                
        Returns:
            AgentResult with StrategistProposal output
        """
        session_date: str = context.get("session_date", "")
        session_type: str = context.get("session_type", "OPEN")
        
        # Support both new MarketBriefing and legacy TickerFeatures
        briefings = context.get("briefings", [])
        
        # Build the data string
        if briefings:
            # New format: MarketBriefing objects
            data_parts = []
            for briefing in briefings:
                if hasattr(briefing, 'to_prompt_string'):
                    data_parts.append(briefing.to_prompt_string())
                else:
                    data_parts.append(str(briefing))
            briefings_str = "\n\n".join(data_parts)
        else:
            briefings_str = "No market data provided."
        
        # Get schema
        schema = json.dumps(get_strategist_proposal_schema(), indent=2)
        
        # Build prompts
        system_prompt = STRATEGIST_SYSTEM_PROMPT.format(schema=schema)
        user_prompt = STRATEGIST_USER_PROMPT.format(
            session_date=session_date,
            session_type=session_type,
            briefings=briefings_str,
        )
        
        # Call LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.7,
        )
        
        # Parse and return
        return self._parse_response(response, StrategistProposal, prompt=user_prompt, system_prompt=system_prompt)
