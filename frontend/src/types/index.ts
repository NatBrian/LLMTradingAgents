/**
 * TypeScript types for LLM Trading Arena Dashboard
 * Mirrors the Python Pydantic schemas in myllmtradingagents/schemas.py
 */

// ============================================
// Enums
// ============================================

export type OrderSide = 'BUY' | 'SELL';
export type OrderType = 'MARKET' | 'LIMIT' | 'STOP';
export type ProposedAction = 'BUY' | 'SELL' | 'HOLD';

// ============================================
// Trading Schemas
// ============================================

export interface Order {
    ticker: string;
    side: OrderSide;
    qty: number;
    order_type: OrderType;
}

export interface Fill {
    ticker: string;
    side: OrderSide;
    qty: number;
    order_type: OrderType;
    fill_price: number;
    fees: number;
    slippage: number;
    timestamp: string;
    notional: number;
}

export interface Position {
    ticker: string;
    qty: number;
    avg_cost: number;
    current_price: number;
    market_value?: number;
    unrealized_pnl?: number;
    unrealized_pnl_pct?: number;
}

export interface Snapshot {
    timestamp: string;
    cash: number;
    positions: Position[];
    realized_pnl: number;
    positions_value?: number;
    equity?: number;
    unrealized_pnl?: number;
}

// ============================================
// LLM Output Schemas
// ============================================

export interface TickerProposal {
    ticker: string;
    action: ProposedAction;
    confidence: number;
    rationale: string;
    target_allocation_pct?: number;
}

export interface StrategistProposal {
    session_date: string;
    session_type: string;
    market_summary: string;
    proposals: TickerProposal[];
}

export interface TradePlan {
    reasoning: string;
    risk_assessment: string;
    orders: Order[];
}

// ============================================
// LLM Call Tracking
// ============================================

export interface LLMCall {
    call_type: 'strategist' | 'risk_guard' | 'repair';
    provider: string;
    model: string;
    prompt_tokens: number;
    completion_tokens: number;
    latency_ms: number;
    success: boolean;
    error?: string;
    prompt?: string;
    system_prompt?: string;
    raw_response?: string;
    parsed_response?: string;
}

// ============================================
// Run Log
// ============================================

export interface RunLog {
    run_id: string;
    competitor_id: string;
    session_date: string;
    session_type: 'OPEN' | 'CLOSE';
    timestamp: string;
    llm_calls: LLMCall[];
    strategist_proposal?: StrategistProposal;
    trade_plan?: TradePlan;
    fills: Fill[];
    errors: string[];
    snapshot_before?: Snapshot;
    snapshot_after?: Snapshot;
}

// ============================================
// Leaderboard
// ============================================

export interface LeaderboardEntry {
    competitor_id: string;
    name: string;
    provider: string;
    model: string;
    current_equity: number;
    total_return: number;
    max_drawdown: number;
    num_trades: number;
}

// ============================================
// Equity Curve
// ============================================

export interface EquityPoint {
    timestamp: string;
    equity: number;
    cash?: number;
}

// ============================================
// Trade Record (flattened for table display)
// ============================================

export interface TradeRecord {
    timestamp: string;
    competitor_id: string;
    ticker: string;
    side: OrderSide;
    qty: number;
    price: number;
    notional: number;
    fees: number;
}

// ============================================
// Market Data (OHLCV for charts)
// ============================================

export interface OHLCVBar {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

// ============================================
// Dashboard Data (exported from arena.db)
// ============================================

export interface DashboardData {
    metadata: {
        lastUpdated: string;
        totalCompetitors: number;
        totalRuns: number;
        totalTrades: number;
    };
    leaderboard: LeaderboardEntry[];
    equityCurves: Record<string, EquityPoint[]>;
    runLogs: RunLog[];
    trades: TradeRecord[];
    snapshots: Record<string, Snapshot>;
    marketData?: Record<string, OHLCVBar[]>;
}

// ============================================
// Competitor Info
// ============================================

export interface Competitor {
    id: string;
    name: string;
    provider: string;
    model: string;
}
