"""
Market data utilities.
"""

def normalize_yahoo_ticker(ticker: str) -> str:
    """
    Normalize a ticker symbol for use with Yahoo Finance (yfinance).
    
    Handles Crypto pair conversion:
    - BTC/USDT -> BTC-USD
    - ETH/USDT -> ETH-USD
    - XRP/USDT -> XRP-USD
    
    Args:
        ticker: The internal ticker symbol (e.g. "BTC/USDT", "AAPL")
        
    Returns:
        The yfinance-compatible ticker symbol (e.g. "BTC-USD", "AAPL")
    """
    ticker = ticker.upper()
    
    # Check for crypto pairs
    if "/" in ticker:
        base, quote = ticker.split("/")
        
        # yfinance typically uses -USD for crypto (e.g., BTC-USD, ETH-USD)
        # It rarely uses USDT pairs, and volume/liquidity is best on USD pairs for general data
        if result_quote := "USD":
            return f"{base}-{result_quote}"
            
    # Also handle "BTCUSDT" format if it appears without slash
    if ticker.endswith("USDT") and "/" not in ticker and len(ticker) > 4:
        base = ticker[:-4]
        return f"{base}-USD"
        
    return ticker


def normalize_alpha_vantage_ticker(ticker: str) -> str:
    """
    Normalize a ticker symbol for Alpha Vantage API.
    
    Handles Crypto pair conversion:
    - BTC/USDT -> CRYPTO:BTC
    - AAPL -> AAPL
    """
    ticker = ticker.upper()
    
    # Check for crypto pairs
    if "/" in ticker:
        base, _ = ticker.split("/")
        return f"CRYPTO:{base}"
            
    # Also handle "BTCUSDT" format
    if ticker.endswith("USDT") and "/" not in ticker and len(ticker) > 4:
        base = ticker[:-4]
        return f"CRYPTO:{base}"
        
    return ticker
