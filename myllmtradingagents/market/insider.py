"""
Insider transactions data fetching.

Data comes from SEC Form 4 filings.
Returns raw transaction data - no signal interpretations.
"""

from typing import Optional
from dataclasses import dataclass, field

import yfinance as yf


@dataclass
class InsiderTransaction:
    """A single insider transaction from SEC Form 4."""
    date: str                    # Transaction date YYYY-MM-DD
    insider_name: str            # Name of the insider
    title: str                   # Position/title (CEO, CFO, Director, etc.)
    transaction_type: str        # "Buy" or "Sell"
    shares: int                  # Number of shares
    price: Optional[float]       # Price per share (if available)
    value: Optional[float]       # Total transaction value


@dataclass
class InsiderData:
    """
    Insider transaction data for a ticker.
    
    All data is authoritative from SEC Form 4 filings via yfinance.
    NO INTERPRETATIONS - just raw transaction data.
    """
    transactions: list[InsiderTransaction] = field(default_factory=list)
    
    # Summary counts (for convenience, but LLM interprets meaning)
    total_buys_90d: int = 0
    total_sells_90d: int = 0
    buy_value_90d: float = 0.0
    sell_value_90d: float = 0.0


def fetch_insider_transactions(ticker: str) -> InsiderData:
    """
    Fetch insider transaction data for a ticker from yfinance.
    
    Note: yfinance provides insider transaction data from SEC filings.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        InsiderData with recent transactions
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get insider transactions
        insider_df = None
        try:
            insider_df = stock.insider_transactions
        except Exception:
            pass
        
        transactions = []
        total_buys = 0
        total_sells = 0
        buy_value = 0.0
        sell_value = 0.0
        
        if insider_df is not None and len(insider_df) > 0:
            # Process the DataFrame
            for idx, row in insider_df.head(20).iterrows():
                # Extract transaction details
                trans_date = ""
                if hasattr(idx, 'strftime'):
                    trans_date = idx.strftime('%Y-%m-%d')
                elif 'Start Date' in insider_df.columns:
                    date_val = row.get('Start Date')
                    if date_val and hasattr(date_val, 'strftime'):
                        trans_date = date_val.strftime('%Y-%m-%d')
                
                # Get transaction type
                trans_type = "Unknown"
                if 'Transaction' in insider_df.columns:
                    trans_raw = str(row.get('Transaction', '')).lower()
                    if 'buy' in trans_raw or 'purchase' in trans_raw:
                        trans_type = "Buy"
                    elif 'sell' in trans_raw or 'sale' in trans_raw:
                        trans_type = "Sell"
                    else:
                        trans_type = str(row.get('Transaction', 'Unknown'))
                
                # Get shares and value
                shares = 0
                if 'Shares' in insider_df.columns:
                    shares_val = row.get('Shares')
                    if shares_val is not None:
                        try:
                            shares = int(abs(float(shares_val)))
                        except (ValueError, TypeError):
                            pass
                
                value = None
                if 'Value' in insider_df.columns:
                    value_val = row.get('Value')
                    if value_val is not None:
                        try:
                            value = float(value_val)
                        except (ValueError, TypeError):
                            pass
                
                # Get insider info
                insider_name = str(row.get('Insider', 'Unknown'))
                title = str(row.get('Position', row.get('Title', 'Unknown')))
                
                # Calculate price if we have value and shares
                price = None
                if value and shares > 0:
                    price = abs(value) / shares
                
                transaction = InsiderTransaction(
                    date=trans_date,
                    insider_name=insider_name,
                    title=title,
                    transaction_type=trans_type,
                    shares=shares,
                    price=price,
                    value=abs(value) if value else None,
                )
                transactions.append(transaction)
                
                # Accumulate totals
                if trans_type == "Buy":
                    total_buys += 1
                    if value:
                        buy_value += abs(value)
                elif trans_type == "Sell":
                    total_sells += 1
                    if value:
                        sell_value += abs(value)
        
        return InsiderData(
            transactions=transactions,
            total_buys_90d=total_buys,
            total_sells_90d=total_sells,
            buy_value_90d=buy_value,
            sell_value_90d=sell_value,
        )
        
    except Exception as e:
        print(f"Error fetching insider transactions for {ticker}: {e}")
        return InsiderData()


def fetch_insider_transactions_batch(tickers: list[str]) -> dict[str, InsiderData]:
    """
    Fetch insider transactions for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dict mapping ticker -> InsiderData
    """
    result = {}
    for ticker in tickers:
        result[ticker.upper()] = fetch_insider_transactions(ticker)
    return result
