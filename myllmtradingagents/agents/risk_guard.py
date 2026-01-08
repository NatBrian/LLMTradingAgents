"""
Risk Guard Agent - Validates trading proposals against portfolio constraints.

This is Agent #2 in the 3-Agent System.
It receives proposals from the Strategist and validates them before execution.
"""

import json

from .base import Agent, AgentResult
from ..schemas import (
    StrategistProposal,
    Snapshot,
    TradePlan,
    get_trade_plan_schema,
)


# ============================================================================
# Risk Guard Prompts
# ============================================================================

RISK_GUARD_SYSTEM_PROMPT = """You are the Risk Guard, a conservative portfolio risk manager who validates trading proposals.

Your job is to review the Strategist's proposals and decide which trades to APPROVE or VETO.
You then output a final TradePlan with orders to execute.

CRITICAL RULES:
1. Output ONLY valid JSON matching the provided schema.
2. DO NOT use markdown code blocks (e.g. ```json). Output RAW JSON only.
3. VETO any proposal that violates constraints:
   - BUY orders must have sufficient cash (qty * price < available_cash)
   - SELL orders must have sufficient shares (qty <= current_position)
   - No single position should exceed {max_position_pct}% of portfolio
4. VETO low-confidence proposals (confidence < 0.5).
5. VETO if the Strategist seems to hallucinate (proposes trade for unknown ticker).
6. Convert APPROVED proposals to Order objects with concrete quantities.
7. Empty orders list = HOLD (no trades this session).
8. Long-only trading: You cannot short sell. Only SELL what you own.

POSITION SIZING GUIDE:
- For BUY: Calculate qty as (cash * target_allocation_pct / 100) / estimated_price
- Round down to whole shares
- Ensure total position value does not exceed max_position_pct of equity

Current Portfolio:
{portfolio_summary}

Trading Constraints:
- Maximum orders this session: {max_orders}
- Maximum position size: {max_position_pct}% of portfolio
- Available cash: ${available_cash:,.2f}
- Current equity: ${equity:,.2f}

Current Prices (for sizing):
{prices_summary}

You must respond with a JSON object matching this schema:
{schema}
"""

RISK_GUARD_USER_PROMPT = """Review the following Strategist proposals and decide what trades to execute.

=== STRATEGIST PROPOSALS ===
{proposals_json}

=== CURRENT POSITIONS ===
{positions_summary}

For each proposal, decide:
1. APPROVE → Convert to an Order with specific quantity
2. VETO → Do not include in orders (explain in reasoning)

Output your TradePlan as JSON with:
- reasoning: Explain your decisions (which proposals approved/vetoed and why)
- risk_assessment: Key risks in executing these trades
- orders: List of approved Order objects (or empty list for HOLD)

Remember: Output ONLY the RAW JSON object. Do not use markdown formatting."""


class RiskGuard(Agent):
    """
    The Risk Guard agent validates proposals against portfolio constraints.
    
    This is Agent #2 in the 3-Agent System.
    
    Input: StrategistProposal + Current portfolio Snapshot
    Output: TradePlan with approved orders (or empty for HOLD)
    """
    
    @property
    def name(self) -> str:
        return "RiskGuard"
    
    @property
    def role(self) -> str:
        return "Validates proposals against portfolio constraints"
    
    def invoke(
        self,
        context: dict,
    ) -> AgentResult:
        """
        Invoke the Risk Guard agent.
        
        Args:
            context: Must contain:
                - proposal: StrategistProposal
                - snapshot: Snapshot (current portfolio state)
                - prices: dict[str, float] (current prices for sizing)
                - max_orders: int (optional, default 3)
                - max_position_pct: float (optional, default 25.0)
                
        Returns:
            AgentResult with TradePlan output
        """
        proposal: StrategistProposal = context["proposal"]
        snapshot: Snapshot = context["snapshot"]
        prices: dict[str, float] = context.get("prices", {})
        max_orders: int = context.get("max_orders", 3)
        max_position_pct: float = context.get("max_position_pct", 25.0)
        
        # Build portfolio summary
        portfolio_lines = [
            f"Cash: ${snapshot.cash:,.2f}",
            f"Positions Value: ${snapshot.positions_value:,.2f}",
            f"Total Equity: ${snapshot.equity:,.2f}",
            f"Unrealized P&L: ${snapshot.unrealized_pnl:,.2f}",
        ]
        portfolio_summary = "\n".join(portfolio_lines)
        
        # Build positions summary
        if snapshot.positions:
            positions_lines = []
            for pos in snapshot.positions:
                line = (
                    f"- {pos.ticker}: {pos.qty} shares @ ${pos.avg_cost:.2f} avg cost, "
                    f"current ${pos.current_price:.2f}, P&L ${pos.unrealized_pnl:,.2f}"
                )
                positions_lines.append(line)
            positions_summary = "\n".join(positions_lines)
        else:
            positions_summary = "No current positions."
        
        # Build prices summary
        if prices:
            prices_lines = [f"- {ticker}: ${price:.2f}" for ticker, price in prices.items()]
            prices_summary = "\n".join(prices_lines)
        else:
            prices_summary = "No prices available."
        
        # Get schema
        schema = json.dumps(get_trade_plan_schema(), indent=2)
        
        # Build prompts
        system_prompt = RISK_GUARD_SYSTEM_PROMPT.format(
            max_position_pct=max_position_pct,
            portfolio_summary=portfolio_summary,
            max_orders=max_orders,
            available_cash=snapshot.cash,
            equity=snapshot.equity,
            prices_summary=prices_summary,
            schema=schema,
        )
        
        # Format proposals
        proposals_json = proposal.model_dump_json(indent=2)
        
        user_prompt = RISK_GUARD_USER_PROMPT.format(
            proposals_json=proposals_json,
            positions_summary=positions_summary,
        )
        
        # Call LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.5,  # Lower temp for more conservative decisions
        )
        
        # Parse and return
        return self._parse_response(response, TradePlan, prompt=user_prompt, system_prompt=system_prompt)

