import { useState, useEffect, useCallback } from 'react';
import type { DashboardData } from '../types';

const DATA_URL = '/data.json';

interface UseDataReturn {
    data: DashboardData | null;
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

export function useData(): UseDataReturn {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(DATA_URL);
            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.statusText}`);
            }
            const json = await response.json();
            setData(json);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            // If fetch fails, try to load sample data in development
            if (import.meta.env.DEV) {
                console.warn('Using sample data for development');
                setData(getSampleData());
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    return { data, loading, error, refetch: fetchData };
}

// Sample data for development/demo purposes
function getSampleData(): DashboardData {
    const now = new Date().toISOString();
    const yesterday = new Date(Date.now() - 86400000).toISOString();

    return {
        metadata: {
            lastUpdated: now,
            totalCompetitors: 2,
            totalRuns: 8,
            totalTrades: 12,
        },
        leaderboard: [
            {
                competitor_id: 'gemini_flash',
                name: 'Gemini 2.5 Flash',
                provider: 'gemini',
                model: 'gemini-2.5-flash',
                current_equity: 102450.00,
                total_return: 0.0245,
                max_drawdown: 0.015,
                num_trades: 7,
            },
            {
                competitor_id: 'openrouter_mimo',
                name: 'OpenRouter Mimo',
                provider: 'openrouter',
                model: 'xiaomi/mimo-v2-flash:free',
                current_equity: 99850.00,
                total_return: -0.0015,
                max_drawdown: 0.025,
                num_trades: 5,
            },
        ],
        equityCurves: {
            gemini_flash: [
                { timestamp: '2026-01-01T14:30:00Z', equity: 100000 },
                { timestamp: '2026-01-02T14:30:00Z', equity: 100250 },
                { timestamp: '2026-01-02T21:00:00Z', equity: 100500 },
                { timestamp: '2026-01-03T14:30:00Z', equity: 101200 },
                { timestamp: '2026-01-03T21:00:00Z', equity: 101800 },
                { timestamp: '2026-01-06T14:30:00Z', equity: 102100 },
                { timestamp: '2026-01-06T21:00:00Z', equity: 102450 },
            ],
            openrouter_mimo: [
                { timestamp: '2026-01-01T14:30:00Z', equity: 100000 },
                { timestamp: '2026-01-02T14:30:00Z', equity: 100100 },
                { timestamp: '2026-01-02T21:00:00Z', equity: 99800 },
                { timestamp: '2026-01-03T14:30:00Z', equity: 99600 },
                { timestamp: '2026-01-03T21:00:00Z', equity: 99750 },
                { timestamp: '2026-01-06T14:30:00Z', equity: 99900 },
                { timestamp: '2026-01-06T21:00:00Z', equity: 99850 },
            ],
        },
        runLogs: [
            {
                run_id: 'abc123',
                competitor_id: 'gemini_flash',
                session_date: '2026-01-08',
                session_type: 'OPEN',
                timestamp: now,
                llm_calls: [
                    {
                        call_type: 'strategist',
                        provider: 'gemini',
                        model: 'gemini-2.5-flash',
                        latency_ms: 2340,
                        prompt_tokens: 1854,
                        completion_tokens: 467,
                        success: true,
                        system_prompt: `You are the Strategist, a senior trading analyst at a top investment firm.

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
2. For each ticker, propose exactly one action: BUY, SELL, or HOLD.
3. Your confidence should reflect the strength and alignment of signals.`,
                        prompt: `Analyze the following comprehensive market briefings for trading session OPEN on 2026-01-08.

================================================================================
MARKET BRIEFING: AAPL - Apple Inc. (Technology)
Session Date: 2026-01-08
================================================================================

────────────────────────────────────────
PRICE DATA (Source: Exchange via yfinance)
────────────────────────────────────────
Open: $178.50 | High: $180.20 | Low: $177.80 | Close: $179.90
Volume: 45,234,567
52-Week Range: $142.00 - $199.62 (-9.9% from high)

────────────────────────────────────────
RETURNS (Computed from price data)
────────────────────────────────────────
1-Day: +1.25% | 5-Day: +3.45% | 20-Day: +8.12%
Volatility (20-day annualized): 24.5%

────────────────────────────────────────
TECHNICAL INDICATORS (Computed using standard formulas)
────────────────────────────────────────
RSI (14-period): 58.3
MACD: Line=1.234, Signal=0.987, Histogram=+0.247
Moving Averages: MA(20): $175.50 (+2.5%) | MA(50): $172.30 (+4.4%)

────────────────────────────────────────
FUNDAMENTALS (Source: SEC Filings via yfinance)
────────────────────────────────────────
Valuation: Market Cap: $2.85T | P/E (TTM): 28.5 | Forward P/E: 26.2
Earnings: EPS (TTM): $6.31 | EPS (Forward): $6.87
Profitability: Profit Margin: 25.3% | Operating Margin: 29.8%

For EACH ticker, provide:
1. Your proposed action (BUY, SELL, or HOLD)
2. Your confidence level (0.0 to 1.0)
3. A brief rationale explaining your decision`,
                        raw_response: `{
  "session_date": "2026-01-08",
  "session_type": "OPEN",
  "market_summary": "Tech sector showing strength with AAPL displaying bullish momentum. RSI in neutral zone with positive MACD histogram indicating upward momentum.",
  "proposals": [
    {
      "ticker": "AAPL",
      "action": "BUY",
      "confidence": 0.75,
      "rationale": "Strong technical setup with price above both MA20 and MA50, positive MACD histogram, and RSI in healthy range. Fundamentals remain solid with growing EPS.",
      "target_allocation_pct": 15.0
    },
    {
      "ticker": "MSFT",
      "action": "HOLD",
      "confidence": 0.55,
      "rationale": "Mixed signals - price consolidating near resistance. Waiting for clearer direction before adding position.",
      "target_allocation_pct": null
    }
  ]
}`,
                    },
                    {
                        call_type: 'risk_guard',
                        provider: 'gemini',
                        model: 'gemini-2.5-flash',
                        latency_ms: 1890,
                        prompt_tokens: 1234,
                        completion_tokens: 356,
                        success: true,
                        system_prompt: `You are the Risk Guard, a conservative portfolio risk manager who validates trading proposals.

Your job is to review the Strategist's proposals and decide which trades to APPROVE or VETO.
You then output a final TradePlan with orders to execute.

CRITICAL RULES:
1. VETO any proposal that violates constraints
2. VETO low-confidence proposals (confidence < 0.5)
3. Convert APPROVED proposals to Order objects with concrete quantities
4. Empty orders list = HOLD (no trades this session)

Current Portfolio:
Cash: $91,005.00
Positions Value: $8,995.00
Total Equity: $100,000.00`,
                        prompt: `Review the following Strategist proposals and decide what trades to execute.

=== STRATEGIST PROPOSALS ===
{
  "proposals": [
    {"ticker": "AAPL", "action": "BUY", "confidence": 0.75, "rationale": "Strong technical setup..."},
    {"ticker": "MSFT", "action": "HOLD", "confidence": 0.55, "rationale": "Mixed signals..."}
  ]
}

=== CURRENT POSITIONS ===
- AAPL: 50 shares @ $175.00 avg cost, current $179.90, P&L $245.00

For each proposal, decide:
1. APPROVE → Convert to an Order with specific quantity
2. VETO → Do not include in orders`,
                        raw_response: `{
  "reasoning": "Approving AAPL BUY as confidence is above threshold (0.75) and position size would remain within 25% max limit. MSFT HOLD requires no action. Current AAPL position at ~9% of portfolio with room to add.",
  "risk_assessment": "Adding 30 shares of AAPL would bring total position to ~15% of portfolio, well within 25% limit. No concentration risk concerns.",
  "orders": [
    {
      "ticker": "AAPL",
      "side": "BUY",
      "qty": 30,
      "order_type": "MARKET"
    }
  ]
}`,
                    },
                ],
                strategist_proposal: {
                    session_date: '2026-01-08',
                    session_type: 'OPEN',
                    market_summary: 'Tech sector showing strength with AAPL displaying bullish momentum.',
                    proposals: [
                        {
                            ticker: 'AAPL',
                            action: 'BUY',
                            confidence: 0.75,
                            rationale: 'Strong technical setup with price above both MA20 and MA50.',
                            target_allocation_pct: 15.0,
                        },
                        {
                            ticker: 'MSFT',
                            action: 'HOLD',
                            confidence: 0.55,
                            rationale: 'Mixed signals - waiting for clearer direction.',
                        },
                    ],
                },
                trade_plan: {
                    reasoning: 'Approving AAPL BUY as confidence is above threshold.',
                    risk_assessment: 'Position would remain within limits.',
                    orders: [{ ticker: 'AAPL', side: 'BUY', qty: 30, order_type: 'MARKET' }],
                },
                fills: [
                    {
                        ticker: 'AAPL',
                        side: 'BUY',
                        qty: 30,
                        order_type: 'MARKET',
                        fill_price: 179.95,
                        fees: 0.54,
                        slippage: 0.05,
                        timestamp: now,
                        notional: 5398.50,
                    },
                ],
                errors: [],
                snapshot_before: {
                    timestamp: yesterday,
                    cash: 91005.00,
                    positions: [{ ticker: 'AAPL', qty: 50, avg_cost: 175.00, current_price: 179.90 }],
                    realized_pnl: 0,
                },
                snapshot_after: {
                    timestamp: now,
                    cash: 85606.50,
                    positions: [{ ticker: 'AAPL', qty: 80, avg_cost: 176.84, current_price: 179.90 }],
                    realized_pnl: 0,
                },
            },
        ],
        trades: [
            {
                timestamp: now,
                competitor_id: 'gemini_flash',
                ticker: 'AAPL',
                side: 'BUY',
                qty: 30,
                price: 179.95,
                notional: 5398.50,
                fees: 0.54,
            },
            {
                timestamp: yesterday,
                competitor_id: 'gemini_flash',
                ticker: 'AAPL',
                side: 'BUY',
                qty: 50,
                price: 175.00,
                notional: 8750.00,
                fees: 0.88,
            },
        ],
        snapshots: {
            gemini_flash: {
                timestamp: now,
                cash: 85606.50,
                positions: [
                    {
                        ticker: 'AAPL',
                        qty: 80,
                        avg_cost: 176.84,
                        current_price: 179.90,
                        market_value: 14392.00,
                        unrealized_pnl: 244.80,
                        unrealized_pnl_pct: 1.73,
                    },
                ],
                realized_pnl: 0,
                positions_value: 14392.00,
                equity: 99998.50,
                unrealized_pnl: 244.80,
            },
            openrouter_mimo: {
                timestamp: now,
                cash: 99850.00,
                positions: [],
                realized_pnl: -150.00,
                positions_value: 0,
                equity: 99850.00,
                unrealized_pnl: 0,
            },
        },
    };
}
