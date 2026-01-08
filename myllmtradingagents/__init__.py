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
    LLMCall,
    # 3-Agent System schemas
    ProposedAction,
    StrategistProposal,
    TickerProposal,
    TickerFeatures,
    get_trade_plan_schema,
    get_strategist_proposal_schema,
)

__all__ = [
    "OrderSide",
    "OrderType",
    "ProposedAction",
    "Order",
    "Fill",
    "Position",
    "Snapshot",
    "TickerFeatures",
    "StrategistProposal",
    "TickerProposal",
    "TradePlan",
    "LLMCall",
    "RunLog",
    "get_trade_plan_schema",
    "get_strategist_proposal_schema",
]
