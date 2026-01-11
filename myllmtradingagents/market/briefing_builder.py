"""
Market Briefing Builder - Creates comprehensive LLM prompts from all data sources.

This module combines data from:
- Price history (exchange data)
- Technical indicators (computed)
- Fundamentals (SEC filings)
- Earnings calendar (company IR)
- Insider transactions (SEC Form 4)
- News (news sources)
- News sentiment (optional, from Alpha Vantage)

All data is authoritative or deterministically computed.
NO interpretive signals - the LLM does all analysis.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING, List, Dict

from .fundamentals import FundamentalsData
from .earnings import EarningsData
from .insider import InsiderData, InsiderTransaction
from .price_history import PriceHistoryData, PriceBar
from .alpha_vantage import NewsSentimentData

import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketBriefing:
    """
    Comprehensive market briefing for a single ticker.
    
    Combines all data sources into a professional format for LLM analysis.
    """
    ticker: str
    date: str
    
    # Company info
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Latest price data
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    
    # Returns (computed)
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None
    return_20d: Optional[float] = None
    return_60d: Optional[float] = None
    
    # Volatility
    volatility_20d: Optional[float] = None
    
    # Technical indicators (computed from standard formulas)
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None
    
    # 52-week range
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    
    # Price history
    price_history: List[PriceBar] = field(default_factory=list)
    
    # Fundamentals
    fundamentals: Optional[FundamentalsData] = None
    
    # Earnings
    earnings: Optional[EarningsData] = None
    
    # Insider transactions
    insider: Optional[InsiderData] = None
    
    # News
    news_headlines: List[str] = field(default_factory=list)
    news_articles: List[dict] = field(default_factory=list)
    news_sentiment: Optional[NewsSentimentData] = None
    
    def to_prompt_string(self, include_price_history: bool = True, max_history_rows: int = 30) -> str:
        """
        Generate a comprehensive market briefing for the LLM.
        
        Returns a Bloomberg-terminal style briefing with source attribution.
        """
        sections = []
        
        # Header
        header_parts = [f"{self.ticker}"]
        if self.company_name:
            header_parts.append(f"- {self.company_name}")
        if self.sector:
            header_parts.append(f"({self.sector})")
        
        sections.append("=" * 80)
        sections.append(f"MARKET BRIEFING: {' '.join(header_parts)}")
        sections.append(f"Session Date: {self.date}")
        sections.append("=" * 80)
        
        # Price Data Section
        sections.append("")
        sections.append("─" * 40)
        sections.append("PRICE DATA (Source: Exchange via yfinance)")
        sections.append("─" * 40)
        sections.append(f"Open: ${self.open:.2f} | High: ${self.high:.2f} | Low: ${self.low:.2f} | Close: ${self.close:.2f}")
        sections.append(f"Volume: {self.volume:,}")
        
        if self.high_52w and self.low_52w:
            pct_from_high = ((self.close - self.high_52w) / self.high_52w) * 100 if self.high_52w else 0
            sections.append(f"52-Week Range: ${self.low_52w:.2f} - ${self.high_52w:.2f} ({pct_from_high:+.1f}% from high)")
        
        # Returns Section
        if self.return_1d is not None:
            sections.append("")
            sections.append("─" * 40)
            sections.append("RETURNS (Computed from price data)")
            sections.append("─" * 40)
            returns_parts = [f"1-Day: {self.return_1d:+.2%}"]
            if self.return_5d is not None:
                returns_parts.append(f"5-Day: {self.return_5d:+.2%}")
            if self.return_20d is not None:
                returns_parts.append(f"20-Day: {self.return_20d:+.2%}")
            if self.return_60d is not None:
                returns_parts.append(f"60-Day: {self.return_60d:+.2%}")
            sections.append(" | ".join(returns_parts))
            
            if self.volatility_20d is not None:
                sections.append(f"Volatility (20-day annualized): {self.volatility_20d:.1%}")
        
        # Technical Indicators Section
        has_technicals = any(x is not None for x in [
            self.rsi_14, self.macd_line, self.ma_20, self.ma_50, self.ma_200
        ])
        
        if has_technicals:
            sections.append("")
            sections.append("─" * 40)
            sections.append("TECHNICAL INDICATORS (Computed using standard formulas)")
            sections.append("─" * 40)
        
        if self.rsi_14 is not None:
            sections.append(f"RSI (14-period): {self.rsi_14:.1f}")
        
        if self.macd_line is not None:
            sections.append(f"MACD: Line={self.macd_line:.3f}, Signal={self.macd_signal:.3f}, Histogram={self.macd_histogram:+.3f}")
        
        if self.ma_20 is not None:
            ma_parts = []
            if self.ma_20:
                pct_20 = ((self.close - self.ma_20) / self.ma_20) * 100
                ma_parts.append(f"MA(20): ${self.ma_20:.2f} ({pct_20:+.1f}%)")
            if self.ma_50:
                pct_50 = ((self.close - self.ma_50) / self.ma_50) * 100
                ma_parts.append(f"MA(50): ${self.ma_50:.2f} ({pct_50:+.1f}%)")
            if self.ma_200:
                pct_200 = ((self.close - self.ma_200) / self.ma_200) * 100
                ma_parts.append(f"MA(200): ${self.ma_200:.2f} ({pct_200:+.1f}%)")
            if ma_parts:
                sections.append("Moving Averages: " + " | ".join(ma_parts))
        
        # Fundamentals Section
        if self.fundamentals:
            f = self.fundamentals
            sections.append("")
            sections.append("─" * 40)
            
            # Change source label based on data type
            is_crypto = f.circulating_supply is not None
            source = "CoinGecko" if is_crypto else "SEC Filings via yfinance"
            sections.append(f"FUNDAMENTALS (Source: {source})")
            sections.append("─" * 40)
            
            # Crypto Description
            if f.description:
                sections.append(f"Description: {f.description}")
                sections.append("")
            
            # Valuation
            val_parts = []
            if f.market_cap:
                if f.market_cap >= 1e12:
                    val_parts.append(f"Market Cap: ${f.market_cap/1e12:.2f}T")
                elif f.market_cap >= 1e9:
                    val_parts.append(f"Market Cap: ${f.market_cap/1e9:.2f}B")
                else:
                    val_parts.append(f"Market Cap: ${f.market_cap/1e6:.0f}M")
            
            # Crypto Supply
            if f.circulating_supply:
                 val_parts.append(f"Circ. Supply: {f.circulating_supply:,.0f}")
            if f.total_supply:
                 val_parts.append(f"Total Supply: {f.total_supply:,.0f}")
                 
            # Stock Valuation Metrics
            if f.pe_ratio:
                val_parts.append(f"P/E (TTM): {f.pe_ratio:.1f}")
            if f.forward_pe:
                val_parts.append(f"Forward P/E: {f.forward_pe:.1f}")
            if f.peg_ratio:
                val_parts.append(f"PEG: {f.peg_ratio:.2f}")
                
            if val_parts:
                sections.append("Valuation & Supply: " + " | ".join(val_parts))
            
            # Crypto ATH/ATL
            if f.all_time_high:
                ath_parts = [f"All-Time High: ${f.all_time_high:.2f}"]
                if f.all_time_low:
                     ath_parts.append(f"All-Time Low: ${f.all_time_low:.2f}")
                sections.append(" | ".join(ath_parts))
            
            # Earnings
            earn_parts = []
            if f.eps_ttm:
                earn_parts.append(f"EPS (TTM): ${f.eps_ttm:.2f}")
            if f.eps_forward:
                earn_parts.append(f"EPS (Forward): ${f.eps_forward:.2f}")
            if earn_parts:
                sections.append("Earnings: " + " | ".join(earn_parts))
            
            # Profitability
            profit_parts = []
            if f.profit_margin:
                profit_parts.append(f"Profit Margin: {f.profit_margin:.1%}")
            if f.operating_margin:
                profit_parts.append(f"Operating Margin: {f.operating_margin:.1%}")
            if f.revenue_growth:
                profit_parts.append(f"Revenue Growth: {f.revenue_growth:.1%}")
            if profit_parts:
                sections.append("Profitability: " + " | ".join(profit_parts))
            
            # Financial Health
            health_parts = []
            if f.debt_to_equity:
                health_parts.append(f"Debt/Equity: {f.debt_to_equity:.2f}")
            if f.current_ratio:
                health_parts.append(f"Current Ratio: {f.current_ratio:.2f}")
            if f.dividend_yield:
                health_parts.append(f"Dividend Yield: {f.dividend_yield:.2%}")
            if health_parts:
                sections.append("Financial Health: " + " | ".join(health_parts))
        
        # Earnings Calendar Section
        if self.earnings and self.earnings.next_earnings_date:
            sections.append("")
            sections.append("─" * 40)
            sections.append("EARNINGS CALENDAR (Source: Company IR)")
            sections.append("─" * 40)
            
            days_str = f" ({self.earnings.days_to_earnings} days away)" if self.earnings.days_to_earnings else ""
            sections.append(f"Next Earnings: {self.earnings.next_earnings_date}{days_str}")
        
        # Insider Transactions Section
        if self.insider and self.insider.transactions:
            sections.append("")
            sections.append("─" * 40)
            sections.append("INSIDER TRANSACTIONS (Source: SEC Form 4)")
            sections.append("─" * 40)
            
            # Show summary
            sections.append(f"Recent Activity: {self.insider.total_buys_90d} buys, {self.insider.total_sells_90d} sells")
            
            # Show transaction table
            sections.append("")
            sections.append("Date       | Insider Name         | Title          | Type | Shares    | Value")
            sections.append("-----------|----------------------|----------------|------|-----------|------------")
            
            for t in self.insider.transactions[:10]:
                value_str = f"${t.value:,.0f}" if t.value else "N/A"
                sections.append(
                    f"{t.date[:10]:10} | {t.insider_name[:20]:20} | {t.title[:14]:14} | "
                    f"{t.transaction_type:4} | {t.shares:>9,} | {value_str}"
                )
        
        # News Section (Merged view for 360-degree coverage)
        if self.news_sentiment or self.news_headlines or self.news_articles:
            sections.append("")
            sections.append("─" * 40)
            sections.append("NEWS & NLP SENTIMENT (Source: Alpha Vantage & yfinance)")
            sections.append("─" * 40)
            
            seen_headlines = set()

            # 1. Show overall sentiment summary if available
            if self.news_sentiment:
                ns = self.news_sentiment
                if ns.overall_sentiment_score is not None:
                    sections.append(
                        f"Overall Sentiment: {ns.overall_sentiment_label} "
                        f"(score: {ns.overall_sentiment_score:+.2f})"
                    )
                    sections.append(
                        f"Article Breakdown: {ns.bullish_count} bullish, "
                        f"{ns.bearish_count} bearish, {ns.neutral_count} neutral"
                    )
                    sections.append("")
                
                # Show articles with sentiment and FULL summaries
                for article in ns.articles[:10]:
                    headline = article.get('title', '')
                    if headline and headline not in seen_headlines:
                        sent_label = article.get('sentiment_label', 'Neutral')
                        sections.append(f"* [{sent_label}] {headline}")
                        # Include full summary if available
                        if article.get('summary'):
                            sections.append(f"  Summary: {article.get('summary')}")
                        sections.append("")
                        seen_headlines.add(headline)
            
            # 2. Augment with general headlines/articles (Source: yfinance) if we have room or no AV data
            # Combine yfinance sources
            yf_sources = []
            if self.news_articles:
                # news_articles comes from fetch_news_articles which uses yfinance
                yf_sources.extend(self.news_articles)
            
            # Add simple headlines if we have them
            if self.news_headlines:
                yf_sources.extend([{'headline': h} for h in self.news_headlines])
                
            for item in yf_sources:
                headline = item.get('headline', item.get('title', ''))
                if headline and headline not in seen_headlines:
                    sections.append(f"* {headline}")
                    if item.get('summary'):
                         sections.append(f"  Summary: {item.get('summary')}")
                    seen_headlines.add(headline)
                    if len(seen_headlines) >= 15: # Overall cap for agent prompt
                        break
        
        # Price History Section
        if include_price_history and self.price_history:
            sections.append("")
            sections.append("─" * 40)
            sections.append("PRICE HISTORY (Source: Exchange via yfinance)")
            sections.append("─" * 40)
            sections.append("")
            sections.append("Date       | Open    | High    | Low     | Close   | Volume")
            sections.append("-----------|---------|---------|---------|---------|------------")
            
            for bar in self.price_history[:max_history_rows]:
                sections.append(
                    f"{bar.date} | {bar.open:7.2f} | {bar.high:7.2f} | {bar.low:7.2f} | "
                    f"{bar.close:7.2f} | {bar.volume:>10,}"
                )
            
            if len(self.price_history) > max_history_rows:
                sections.append(f"... ({len(self.price_history) - max_history_rows} more rows)")
        
        sections.append("")
        sections.append("=" * 80)
        
        return "\n".join(sections)


def build_market_briefing(
    ticker: str,
    date: str,
    *,
    # Technical data from existing TickerFeatures
    open_price: float = 0.0,
    high_price: float = 0.0,
    low_price: float = 0.0,
    close_price: float = 0.0,
    volume: int = 0,
    return_1d: float = None,
    return_5d: float = None,
    return_20d: float = None,
    return_60d: float = None,
    volatility_20d: float = None,
    rsi_14: float = None,
    macd_line: float = None,
    macd_signal: float = None,
    macd_histogram: float = None,
    ma_20: float = None,
    ma_50: float = None,
    ma_200: float = None,
    # Data from new modules
    fundamentals: FundamentalsData = None,
    earnings: EarningsData = None,
    insider: InsiderData = None,
    price_history: PriceHistoryData = None,
    news_headlines: List[str] = None,
    news_articles: List[dict] = None,
    news_sentiment: NewsSentimentData = None,
) -> MarketBriefing:
    """
    Build a comprehensive market briefing from all data sources.
    
    Args:
        ticker: Stock ticker symbol
        date: Session date (YYYY-MM-DD)
        ... (all other parameters from various data sources)
        
    Returns:
        MarketBriefing ready for to_prompt_string()
    """
    logger.debug(f"Building market briefing for {ticker}", extra={"ticker": ticker, "date": date})
    
    briefing = MarketBriefing(
        ticker=ticker.upper(),
        date=date,
        open=open_price,
        high=high_price,
        low=low_price,
        close=close_price,
        volume=volume,
        return_1d=return_1d,
        return_5d=return_5d,
        return_20d=return_20d,
        return_60d=return_60d,
        volatility_20d=volatility_20d,
        rsi_14=rsi_14,
        macd_line=macd_line,
        macd_signal=macd_signal,
        macd_histogram=macd_histogram,
        ma_20=ma_20,
        ma_50=ma_50,
        ma_200=ma_200,
        news_headlines=news_headlines or [],
        news_articles=news_articles or [],
        news_sentiment=news_sentiment,
    )
    
    # Add fundamentals data
    if fundamentals:
        briefing.fundamentals = fundamentals
        briefing.company_name = fundamentals.company_name
        briefing.sector = fundamentals.sector
        briefing.industry = fundamentals.industry
        briefing.high_52w = fundamentals.high_52w
        briefing.low_52w = fundamentals.low_52w
    
    # Add earnings data
    if earnings:
        briefing.earnings = earnings
    
    # Add insider data
    if insider:
        briefing.insider = insider
    
    # Add price history
    if price_history:
        briefing.price_history = price_history.bars
        # Use 52w from price history if not in fundamentals
        if not briefing.high_52w and price_history.high_52w:
            briefing.high_52w = price_history.high_52w
        if not briefing.low_52w and price_history.low_52w:
            briefing.low_52w = price_history.low_52w
    
    return briefing

