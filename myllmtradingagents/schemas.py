"""
Pydantic schemas for MyLLMTradingAgents.

All LLM outputs must conform to these schemas for strict JSON validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OrderSide(str, Enum):
    """Order side: BUY or SELL."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type: MARKET only for MVP."""
    MARKET = "MARKET"


class Signal(str, Enum):
    """Trading signal from analyst."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class Sentiment(str, Enum):
    """Market sentiment."""
    VERY_BULLISH = "VERY_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    VERY_BEARISH = "VERY_BEARISH"


class ProposedAction(str, Enum):
    """
    Proposed trading action from the Strategist.
    
    Unlike OrderSide (BUY/SELL), this includes HOLD as an explicit option.
    """
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ============================================================================
# Trading Schemas
# ============================================================================

class Order(BaseModel):
    """A trading order."""
    ticker: str = Field(..., description="Ticker symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    qty: int = Field(..., ge=1, description="Number of shares/units")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        return v.upper().strip()


class Fill(BaseModel):
    """A filled order with execution details."""
    ticker: str
    side: OrderSide
    qty: int
    order_type: OrderType
    fill_price: float = Field(..., ge=0, description="Execution price")
    fees: float = Field(default=0.0, ge=0, description="Transaction fees")
    slippage: float = Field(default=0.0, description="Slippage amount")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notional: float = Field(default=0.0, description="Total transaction value")
    
    @classmethod
    def from_order(
        cls,
        order: Order,
        fill_price: float,
        fees: float,
        slippage: float,
        timestamp: Optional[datetime] = None,
    ) -> "Fill":
        """Create a Fill from an Order."""
        notional = order.qty * fill_price
        return cls(
            ticker=order.ticker,
            side=order.side,
            qty=order.qty,
            order_type=order.order_type,
            fill_price=fill_price,
            fees=fees,
            slippage=slippage,
            timestamp=timestamp or datetime.utcnow(),
            notional=notional,
        )


class Position(BaseModel):
    """A position in a single security."""
    ticker: str
    qty: int = Field(default=0, ge=0, description="Number of shares held")
    avg_cost: float = Field(default=0.0, ge=0, description="Average cost basis")
    current_price: float = Field(default=0.0, ge=0, description="Current market price")
    
    @property
    def market_value(self) -> float:
        """Current market value of position."""
        return self.qty * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        if self.qty == 0:
            return 0.0
        return (self.current_price - self.avg_cost) * self.qty
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P&L as percentage."""
        if self.qty == 0 or self.avg_cost == 0:
            return 0.0
        return ((self.current_price / self.avg_cost) - 1) * 100


class Snapshot(BaseModel):
    """Portfolio snapshot at a point in time."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cash: float = Field(..., ge=0, description="Available cash")
    positions: list[Position] = Field(default_factory=list)
    realized_pnl: float = Field(default=0.0, description="Total realized P&L")
    
    @property
    def positions_value(self) -> float:
        """Total value of all positions."""
        return sum(p.market_value for p in self.positions)
    
    @property
    def equity(self) -> float:
        """Total portfolio equity (cash + positions)."""
        return self.cash + self.positions_value
    
    @property
    def unrealized_pnl(self) -> float:
        """Total unrealized P&L."""
        return sum(p.unrealized_pnl for p in self.positions)


# ============================================================================
# LLM Output Schemas
# ============================================================================

class TickerAnalysis(BaseModel):
    """Analysis for a single ticker from UnifiedAnalyst."""
    ticker: str = Field(..., description="Ticker symbol")
    signal: Signal = Field(..., description="Trading signal")
    sentiment: Sentiment = Field(default=Sentiment.NEUTRAL, description="Market sentiment")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence 0-1")
    rationale: list[str] = Field(
        default_factory=list,
        description="Bullet points explaining the analysis",
        max_length=5,
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Key risks to watch",
        max_length=3,
    )
    invalidators: list[str] = Field(
        default_factory=list,
        description="Conditions that would invalidate this analysis",
        max_length=2,
    )
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        return v.upper().strip()


class AnalystReport(BaseModel):
    """
    [DEPRECATED] Output from UnifiedAnalyst (LLM Call #1).
    
    This class is legacy and will be removed in future versions.
    Use StrategistProposal instead.
    
    Combines market, fundamental, sentiment, and news analysis into one report.
    """
    session_date: str = Field(..., description="Trading session date YYYY-MM-DD")
    session_type: str = Field(..., description="OPEN or CLOSE")
    market_summary: str = Field(
        default="",
        description="Brief overall market conditions",
        max_length=500,
    )
    analyses: list[TickerAnalysis] = Field(
        default_factory=list,
        description="Analysis for each ticker",
    )


# ============================================================================
# Strategist Agent Output (NEW 3-Agent System)
# ============================================================================

class TickerProposal(BaseModel):
    """
    A trading proposal for a single ticker from the Strategist agent.
    
    This is a simpler, more actionable output than TickerAnalysis.
    It focuses on WHAT to do rather than detailed analysis.
    """
    ticker: str = Field(..., description="Ticker symbol")
    action: ProposedAction = Field(..., description="Proposed action: BUY, SELL, or HOLD")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this proposal (0.0 = no confidence, 1.0 = very confident)",
    )
    rationale: str = Field(
        default="",
        description="Brief explanation for the proposed action",
        max_length=1000,
    )
    target_allocation_pct: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Suggested portfolio allocation percentage (e.g., 10.0 means 10% of portfolio)",
    )
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        return v.upper().strip()


class StrategistProposal(BaseModel):
    """
    Output from the Strategist agent (LLM Call #1 in 3-Agent System).
    
    The Strategist analyzes market data and proposes trading actions.
    This output is then reviewed by the Risk Guard agent.
    """
    session_date: str = Field(..., description="Trading session date YYYY-MM-DD")
    session_type: str = Field(..., description="OPEN or CLOSE")
    market_summary: str = Field(
        default="",
        description="Brief overall market assessment",
        max_length=1000,
    )
    proposals: list[TickerProposal] = Field(
        default_factory=list,
        description="Proposed actions for each analyzed ticker",
    )
    
    def get_actionable_proposals(self) -> list[TickerProposal]:
        """Get proposals that are BUY or SELL (not HOLD)."""
        return [p for p in self.proposals if p.action != ProposedAction.HOLD]


class TradePlan(BaseModel):
    """
    Output from DecisionRiskPM (LLM Call #2).
    
    Final trading decision with orders to execute.
    """
    reasoning: str = Field(
        ...,
        description="Brief explanation of trading decisions",
        max_length=3000,
    )
    risk_assessment: str = Field(
        default="",
        description="Risk considerations",
        max_length=1500,
    )
    orders: list[Order] = Field(
        default_factory=list,
        description="Orders to execute. Empty list means HOLD.",
    )
    
    @property
    def is_hold(self) -> bool:
        """Check if this is a HOLD decision (no orders)."""
        return len(self.orders) == 0


# ============================================================================
# Run Logging
# ============================================================================

class LLMCall(BaseModel):
    """Record of a single LLM API call."""
    call_type: str = Field(..., description="analyst or decision")
    provider: str = Field(..., description="openrouter or gemini")
    model: str = Field(..., description="Model name")
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)
    prompt: Optional[str] = Field(default=None, description="Input prompt sent to LLM")
    system_prompt: Optional[str] = Field(default=None, description="System prompt sent to LLM")
    raw_response: Optional[str] = Field(default=None, description="Raw LLM output")
    parsed_response: Optional[str] = Field(default=None, description="Parsed JSON string")


class RunLog(BaseModel):
    """Complete log of a single arena run for a competitor."""
    run_id: str = Field(..., description="Unique run identifier")
    competitor_id: str = Field(..., description="Competitor identifier")
    session_date: str = Field(..., description="Trading date YYYY-MM-DD")
    session_type: str = Field(..., description="OPEN or CLOSE")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # LLM interactions
    llm_calls: list[LLMCall] = Field(default_factory=list)
    
    # Outputs
    analyst_report: Optional[AnalystReport] = Field(default=None)
    strategist_proposal: Optional[StrategistProposal] = Field(default=None)
    trade_plan: Optional[TradePlan] = Field(default=None)
    
    # Execution
    fills: list[Fill] = Field(default_factory=list)
    
    # Errors
    errors: list[str] = Field(default_factory=list)
    
    # Final state
    snapshot_before: Optional[Snapshot] = Field(default=None)
    snapshot_after: Optional[Snapshot] = Field(default=None)


# ============================================================================
# Feature Schemas (for market data)
# ============================================================================

class TickerFeatures(BaseModel):
    """Computed features for a ticker (deterministic preprocessing)."""
    ticker: str
    date: str  # YYYY-MM-DD
    
    # Latest OHLCV
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    
    # Returns
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None
    return_20d: Optional[float] = None
    
    # Volatility
    volatility_20d: Optional[float] = None
    
    # Technical indicators
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_20_distance_pct: Optional[float] = None
    ma_50_distance_pct: Optional[float] = None
    
    # Recent news headlines (optional)
    news_headlines: list[str] = Field(default_factory=list)
    
    def to_prompt_string(self) -> str:
        """Format features for LLM prompt."""
        lines = [
            f"Ticker: {self.ticker}",
            f"Date: {self.date}",
            f"Price: Open={self.open:.2f}, High={self.high:.2f}, Low={self.low:.2f}, Close={self.close:.2f}",
            f"Volume: {self.volume:,.0f}",
        ]
        
        if self.return_1d is not None:
            lines.append(f"Returns: 1D={self.return_1d:+.2%}, 5D={self.return_5d:+.2%}, 20D={self.return_20d:+.2%}")
        
        if self.volatility_20d is not None:
            lines.append(f"Volatility (20D): {self.volatility_20d:.2%}")
        
        if self.rsi_14 is not None:
            lines.append(f"RSI(14): {self.rsi_14:.1f}")
        
        if self.macd_line is not None:
            lines.append(f"MACD: Line={self.macd_line:.3f}, Signal={self.macd_signal:.3f}, Hist={self.macd_histogram:.3f}")
        
        if self.ma_20 is not None:
            lines.append(f"MA20: {self.ma_20:.2f} ({self.ma_20_distance_pct:+.2%} from close)")
        
        if self.ma_50 is not None:
            lines.append(f"MA50: {self.ma_50:.2f} ({self.ma_50_distance_pct:+.2%} from close)")
        
        if self.news_headlines:
            lines.append("Recent Headlines:")
            for headline in self.news_headlines[:5]:
                lines.append(f"  - {headline}")
        
        return "\n".join(lines)


# JSON Schema exports for LLM prompting
def get_analyst_report_schema() -> dict:
    """Get JSON schema for AnalystReport."""
    return AnalystReport.model_json_schema()


def get_trade_plan_schema() -> dict:
    """Get JSON schema for TradePlan."""
    return TradePlan.model_json_schema()


def get_strategist_proposal_schema() -> dict:
    """Get JSON schema for StrategistProposal (3-Agent System)."""
    return StrategistProposal.model_json_schema()

