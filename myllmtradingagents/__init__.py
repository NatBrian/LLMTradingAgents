"""
MyLLMTradingAgents - Minimal LLM Trading Arena

A simplified multi-LLM trading arena system that:
- Compares multiple LLM competitors (OpenRouter, Gemini, etc.)
- Uses real market data with simulated trades
- Uses 3-Agent System: Data Aggregator (Python) + Strategist (LLM) + Risk Guard (LLM)
- Designed for free-tier deployment on Oracle Cloud
"""

__version__ = "0.2.0"
__author__ = "MyLLMTradingAgents Contributors"

from .schemas import (
    # Core trading schemas
    Order,
    Fill,
    Position,
    Snapshot,
    TradePlan,
    RunLog,
    OrderSide,
    OrderType,
    Signal,
    # 3-Agent System schemas
    ProposedAction,
    TickerProposal,
    StrategistProposal,
    TickerFeatures,
    # Legacy (kept for backward compatibility with stored data)
    AnalystReport,
    TickerAnalysis,
)

__all__ = [
    # Core trading
    "Order",
    "Fill",
    "Position",
    "Snapshot",
    "TradePlan",
    "RunLog",
    "OrderSide",
    "OrderType",
    "Signal",
    # 3-Agent System
    "ProposedAction",
    "TickerProposal",
    "StrategistProposal",
    "TickerFeatures",
    # Legacy
    "AnalystReport",
    "TickerAnalysis",
]
