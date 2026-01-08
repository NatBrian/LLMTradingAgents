"""
Deterministic feature computation for market data.

Computes technical indicators and returns for LLM prompts.
"""

from typing import Optional
import pandas as pd
import numpy as np

from ..schemas import TickerFeatures


def compute_features(
    ticker: str,
    bars: pd.DataFrame,
    news_headlines: Optional[list[str]] = None,
) -> TickerFeatures:
    """
    Compute features from OHLCV data.
    
    Args:
        ticker: Ticker symbol
        bars: DataFrame with Date, Open, High, Low, Close, Volume
        news_headlines: Optional list of recent headlines
        
    Returns:
        TickerFeatures with computed indicators
    """
    if bars.empty or len(bars) < 2:
        return TickerFeatures(
            ticker=ticker,
            date="",
            news_headlines=news_headlines or [],
        )
    
    # Ensure we have the right columns
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in bars.columns:
            return TickerFeatures(ticker=ticker, date="")
    
    # Sort by date
    if "Date" in bars.columns:
        bars = bars.sort_values("Date").copy()
    
    # Get latest bar
    latest = bars.iloc[-1]
    
    # Get date string
    date_str = ""
    if "Date" in bars.columns:
        date_val = latest["Date"]
        if hasattr(date_val, "strftime"):
            date_str = date_val.strftime("%Y-%m-%d")
        else:
            date_str = str(date_val)[:10]
    
    # Create features object
    features = TickerFeatures(
        ticker=ticker.upper(),
        date=date_str,
        open=float(latest["Open"]),
        high=float(latest["High"]),
        low=float(latest["Low"]),
        close=float(latest["Close"]),
        volume=float(latest.get("Volume", 0)),
        news_headlines=news_headlines or [],
    )
    
    close_series = bars["Close"].astype(float)
    
    # Compute returns
    features.return_1d = _compute_return(close_series, 1)
    features.return_5d = _compute_return(close_series, 5)
    features.return_20d = _compute_return(close_series, 20)
    
    # Compute volatility (20-day)
    if len(close_series) >= 21:
        returns = close_series.pct_change().dropna()
        features.volatility_20d = float(returns.tail(20).std() * np.sqrt(252))
    
    # Compute RSI(14)
    features.rsi_14 = _compute_rsi(close_series, 14)
    
    # Compute MACD
    macd_line, macd_signal, macd_hist = _compute_macd(close_series)
    features.macd_line = macd_line
    features.macd_signal = macd_signal
    features.macd_histogram = macd_hist
    
    # Compute Moving Averages
    if len(close_series) >= 20:
        features.ma_20 = float(close_series.tail(20).mean())
        features.ma_20_distance_pct = (features.close - features.ma_20) / features.ma_20
    
    if len(close_series) >= 50:
        features.ma_50 = float(close_series.tail(50).mean())
        features.ma_50_distance_pct = (features.close - features.ma_50) / features.ma_50
    
    # NOTE: We do NOT compute ma_trend interpretation.
    # The LLM will analyze the relationship between close, MA20, and MA50.
    
    return features


def _compute_return(close: pd.Series, days: int) -> Optional[float]:
    """Compute return over N days."""
    if len(close) < days + 1:
        return None
    
    current = float(close.iloc[-1])
    past = float(close.iloc[-(days + 1)])
    
    if past == 0:
        return None
    
    return (current - past) / past


def _compute_rsi(close: pd.Series, period: int = 14) -> Optional[float]:
    """Compute RSI indicator."""
    if len(close) < period + 1:
        return None
    
    try:
        from ta.momentum import RSIIndicator
        rsi = RSIIndicator(close, window=period)
        values = rsi.rsi()
        if values is not None and len(values) > 0:
            val = values.iloc[-1]
            if pd.notna(val):
                return float(val)
    except ImportError:
        # Fallback: manual RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        if loss.iloc[-1] == 0:
            return 100.0 if gain.iloc[-1] > 0 else 50.0
        
        rs = gain.iloc[-1] / loss.iloc[-1]
        return float(100 - (100 / (1 + rs)))
    except Exception:
        pass
    
    return None


def _compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Compute MACD indicator."""
    if len(close) < slow + signal:
        return None, None, None
    
    try:
        from ta.trend import MACD
        macd = MACD(close, window_fast=fast, window_slow=slow, window_sign=signal)
        
        macd_line = macd.macd()
        macd_signal = macd.macd_signal()
        macd_hist = macd.macd_diff()
        
        if macd_line is not None and len(macd_line) > 0:
            line_val = macd_line.iloc[-1]
            sig_val = macd_signal.iloc[-1] if macd_signal is not None else None
            hist_val = macd_hist.iloc[-1] if macd_hist is not None else None
            
            return (
                float(line_val) if pd.notna(line_val) else None,
                float(sig_val) if sig_val is not None and pd.notna(sig_val) else None,
                float(hist_val) if hist_val is not None and pd.notna(hist_val) else None,
            )
    except ImportError:
        # Fallback: manual MACD calculation
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        macd_signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        macd_hist = macd_line - macd_signal_line
        
        return (
            float(macd_line.iloc[-1]),
            float(macd_signal_line.iloc[-1]),
            float(macd_hist.iloc[-1]),
        )
    except Exception:
        pass
    
    return None, None, None


def compute_features_batch(
    tickers: list[str],
    bars_dict: dict[str, pd.DataFrame],
    news_dict: Optional[dict[str, list[str]]] = None,
) -> list[TickerFeatures]:
    """
    Compute features for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        bars_dict: Dict mapping ticker -> DataFrame
        news_dict: Optional dict mapping ticker -> headlines list
        
    Returns:
        List of TickerFeatures
    """
    news_dict = news_dict or {}
    
    features_list = []
    for ticker in tickers:
        bars = bars_dict.get(ticker.upper(), pd.DataFrame())
        headlines = news_dict.get(ticker.upper(), [])
        
        features = compute_features(ticker, bars, headlines)
        features_list.append(features)
    
    return features_list
