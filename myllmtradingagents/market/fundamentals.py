"""
Fundamentals data fetching from yfinance.

All data comes from SEC filings (10-K, 10-Q) via yfinance.
Returns raw authoritative data - no interpretations.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass

import os
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# Configure yfinance cache to avoid permission issues
try:
    cache_dir = os.path.expanduser("~/.myllmtradingagents/cache/yfinance")
    os.makedirs(cache_dir, exist_ok=True)
    yf.set_tz_cache_location(cache_dir)
except Exception as e:
    logger.warning(f"Failed to set yfinance cache dir: {e}")


@dataclass
class FundamentalsData:
    """
    Fundamental data for a ticker.
    
    All data is authoritative from SEC filings via yfinance.
    """
    # Company info
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Valuation metrics
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None         # Trailing P/E
    forward_pe: Optional[float] = None       # Forward P/E
    peg_ratio: Optional[float] = None        # P/E to Growth
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    
    # Earnings
    eps_ttm: Optional[float] = None          # Trailing 12-month EPS
    eps_forward: Optional[float] = None      # Forward EPS estimate
    
    # Revenue and profitability
    revenue_ttm: Optional[float] = None
    revenue_growth: Optional[float] = None   # YoY revenue growth
    profit_margin: Optional[float] = None    # Net profit margin
    operating_margin: Optional[float] = None # Operating margin
    gross_margin: Optional[float] = None     # Gross margin
    
    # Financial health
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    
    # Dividends
    dividend_yield: Optional[float] = None
    dividend_rate: Optional[float] = None
    
    # 52-week range
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    
    # Beta (volatility vs market)
    beta: Optional[float] = None


def fetch_fundamentals(ticker: str) -> FundamentalsData:
    """
    Fetch fundamental data for a ticker from yfinance.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        FundamentalsData with all available metrics
    """
    try:
        logger.debug(f"Fetching fundamentals for {ticker}...", extra={"ticker": ticker})
        stock = yf.Ticker(ticker)
        
        # 1. Try to get full info
        info = None
        try:
            info = stock.info
            if info:
                logger.debug(f"Successfully fetched info for {ticker}", extra={"ticker": ticker, "keys_count": len(info)})
            else:
                logger.warning(f"yfinance returned empty info for {ticker}", extra={"ticker": ticker})
        except Exception as e:
            # Check for specific curl error related to writing output
            if "curl" in str(e) and "Failure writing output" in str(e):
                logger.warning(f"yfinance cache write error for {ticker}: {e}")
            else:
                logger.warning(f"Yahoo Finance API error for {ticker} info: {e}")

        # 2. If info is available, use it
        if info:
            logger.debug(f"Parsing fundamentals for {ticker}", extra={"ticker": ticker, "market_cap": info.get("marketCap")})
            return FundamentalsData(
                # Company info
                company_name=info.get("longName") or info.get("shortName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                
                # Valuation
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                forward_pe=info.get("forwardPE"),
                peg_ratio=info.get("pegRatio"),
                price_to_book=info.get("priceToBook"),
                price_to_sales=info.get("priceToSalesTrailing12Months"),
                
                # Earnings
                eps_ttm=info.get("trailingEps"),
                eps_forward=info.get("forwardEps"),
                
                # Revenue and profitability
                revenue_ttm=info.get("totalRevenue"),
                revenue_growth=info.get("revenueGrowth"),
                profit_margin=info.get("profitMargins"),
                operating_margin=info.get("operatingMargins"),
                gross_margin=info.get("grossMargins"),
                
                # Financial health
                debt_to_equity=info.get("debtToEquity"),
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                
                # Dividends
                dividend_yield=info.get("dividendYield"),
                dividend_rate=info.get("dividendRate"),
                
                # 52-week range
                high_52w=info.get("fiftyTwoWeekHigh"),
                low_52w=info.get("fiftyTwoWeekLow"),
                
                # Beta
                beta=info.get("beta"),
            )
            
        # 3. Fallback to fast_info if info failed
        logger.info(f"Falling back to fast_info for {ticker} fundamentals")
        try:
            fast_info = stock.fast_info
            if fast_info:
                logger.debug(f"Successfully fetched fast_info for {ticker}", extra={"ticker": ticker})
                # fast_info has limited data but better than nothing
                return FundamentalsData(
                    market_cap=fast_info.get("market_cap"),
                    high_52w=fast_info.get("year_high"),
                    low_52w=fast_info.get("year_low"),
                    # We can't get P/E, Sector, etc. from fast_info easily
                )
            else:
                logger.warning(f"yfinance returned empty fast_info for {ticker}", extra={"ticker": ticker})
        except Exception as e:
            logger.warning(f"Failed to fetch fast_info for {ticker}: {e}")

        return FundamentalsData()
        
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}", extra={"ticker": ticker, "error": str(e)})
        return FundamentalsData()


def fetch_fundamentals_batch(tickers: List[str]) -> Dict[str, FundamentalsData]:
    """
    Fetch fundamentals for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dict mapping ticker -> FundamentalsData
    """
    result = {}
    for ticker in tickers:
        result[ticker.upper()] = fetch_fundamentals(ticker)
    return result
