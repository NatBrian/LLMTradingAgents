"""
Arena runner - orchestrates trading sessions for all competitors.

Main orchestration flow per session (3-Agent System):
1. Load config, initialize storage
2. Check gate (should_run?)
3. Fetch market data for all tickers (Data Aggregator - Python)
4. For each competitor:
   - Call #1: Strategist → StrategistProposal
   - Call #2: RiskGuard → TradePlan
   - Execute orders via SimBroker
   - Save snapshot + run_log
"""

import logging
import uuid
from datetime import datetime, date
from typing import Optional

from ..settings import ArenaConfig, CompetitorConfig
from ..schemas import (
    TradePlan,
    RunLog,
    LLMCall,
    Snapshot,
    TickerFeatures,
    get_trade_plan_schema,
    StrategistProposal,
    get_strategist_proposal_schema,
)
from ..llm import create_llm_client
from ..llm.prompts import build_repair_prompt
from ..agents import Strategist, RiskGuard
from ..market import create_market_adapter, compute_features
from ..market.news import fetch_headlines_batch
from ..market import (
    fetch_fundamentals,
    fetch_earnings_calendar,
    fetch_insider_transactions,
    fetch_price_history,
    build_market_briefing,
    MarketBriefing,
    fetch_news_sentiment,
)
from ..sim import SimBroker
from ..storage import SQLiteStorage

logger = logging.getLogger(__name__)


class ArenaRunner:
    """
    Main arena runner that orchestrates trading sessions.
    
    Uses the 3-Agent System:
    1. Strategist - analyzes market data and proposes trades
    2. RiskGuard - validates proposals against portfolio constraints
    """
    
    def __init__(self, config: ArenaConfig):
        """
        Initialize arena runner.
        
        Args:
            config: Arena configuration
        """
        self.config = config
        self.storage = SQLiteStorage(config.db_path)
        self.storage.initialize()
        
        # Initialize competitors in storage
        for comp in config.competitors:
            self.storage.save_competitor(
                competitor_id=comp.id,
                name=comp.name,
                provider=comp.provider,
                model=comp.model,
                config={
                    "initial_cash": comp.initial_cash,
                    "max_position_pct": comp.max_position_pct,
                    "max_orders_per_run": comp.max_orders_per_run,
                },
            )
        
        # Cache for brokers (one per competitor)
        self._brokers: dict[str, SimBroker] = {}
    
    def get_broker(self, competitor: CompetitorConfig) -> SimBroker:
        """Get or create broker for a competitor."""
        if competitor.id not in self._brokers:
            # Check for existing state
            latest = self.storage.get_latest_snapshot(competitor.id)
            
            broker = SimBroker(
                initial_cash=competitor.initial_cash,
                slippage_bps=self.config.simulation.slippage_bps,
                fee_bps=self.config.simulation.fee_bps,
                max_position_pct=competitor.max_position_pct,
            )
            
            if latest:
                # Restore state from snapshot
                broker.cash = latest.cash
                broker.realized_pnl = latest.realized_pnl
                broker.positions = {p.ticker: p for p in latest.positions}
            
            self._brokers[competitor.id] = broker
        
        return self._brokers[competitor.id]
    
    def run_session(
        self,
        session_type: str,  # "OPEN" or "CLOSE"
        session_date: Optional[date] = None,
        dry_run: bool = False,
    ) -> dict:
        """
        Run a trading session for all competitors.
        
        Args:
            session_type: "OPEN" or "CLOSE"
            session_date: Trading date (default: today)
            dry_run: If True, don't save to storage or execute trades
            
        Returns:
            Dict with results for each competitor
        """
        session_date = session_date or date.today()
        session_date_str = session_date.isoformat()
        
        logger.info(f"{'='*60}")
        logger.info(f"Running {session_type} session for {session_date_str}")
        logger.info(f"{'='*60}")
        
        results = {}
        
        # Gather all tickers from all markets
        all_tickers = []
        market_adapters = {}
        
        for market in self.config.markets:
            adapter = create_market_adapter(
                market.type,
                cache_dir=self.config.cache_dir,
            )
            market_adapters[market.type] = (adapter, market.tickers)
            all_tickers.extend(market.tickers)
        
        # Dedupe tickers
        all_tickers = list(set(all_tickers))
        
        # Fetch market data and compute features
        logger.info(f"Fetching market data for {len(all_tickers)} tickers...")
        ticker_features = self._fetch_features(market_adapters, all_tickers)
        
        # Build comprehensive briefings with fundamentals, earnings, insider, history
        logger.info(f"Building comprehensive market briefings...")
        briefings = self._build_briefings(ticker_features, session_date_str)
        
        # Get current prices for all tickers
        prices = self._get_prices(market_adapters, all_tickers, session_type, session_date)
        
        # Run each competitor
        for competitor in self.config.competitors:
            logger.info(f"--- Running competitor: {competitor.name} ({competitor.provider}/{competitor.model}) ---")
            
            try:
                result = self._run_competitor(
                    competitor=competitor,
                    session_type=session_type,
                    session_date_str=session_date_str,
                    ticker_features=ticker_features,
                    briefings=briefings,
                    prices=prices,
                    dry_run=dry_run,
                )
                results[competitor.id] = result
            except Exception as e:
                logger.error(f"Error running competitor {competitor.id}: {e}")
                results[competitor.id] = {"error": str(e)}
        
        return results
    
    def _fetch_features(
        self,
        market_adapters: dict,
        tickers: list[str],
    ) -> list[TickerFeatures]:
        """Fetch and compute features for all tickers."""
        features_list = []
        
        # Fetch news headlines (optional, fail-soft)
        try:
            news_dict = fetch_headlines_batch(tickers, max_per_ticker=3)
        except Exception:
            news_dict = {}
        
        for market_type, (adapter, market_tickers) in market_adapters.items():
            for ticker in market_tickers:
                try:
                    bars = adapter.get_daily_bars(ticker, days=90)
                    headlines = news_dict.get(ticker.upper(), [])
                    features = compute_features(ticker, bars, headlines)
                    features_list.append(features)
                except Exception as e:
                    logger.warning(f"Error fetching features for {ticker}: {e}")
                    features_list.append(TickerFeatures(ticker=ticker, date=""))
        
        return features_list
    
    def _build_briefings(
        self,
        ticker_features: list[TickerFeatures],
        session_date_str: str,
    ) -> list[MarketBriefing]:
        """
        Build comprehensive MarketBriefing objects from all data sources.
        
        This fetches additional data (fundamentals, earnings, insider, history)
        and combines it with the existing TickerFeatures into MarketBriefing objects.
        """
        briefings = []
        
        for features in ticker_features:
            ticker = features.ticker
            
            # Fetch additional data (fail-soft for each)
            fundamentals = None
            earnings = None
            insider = None
            price_history = None
            
            try:
                fundamentals = fetch_fundamentals(ticker)
            except Exception as e:
                logger.debug(f"  Warning: Could not fetch fundamentals for {ticker}: {e}")
            
            try:
                earnings = fetch_earnings_calendar(ticker)
            except Exception as e:
                logger.debug(f"  Warning: Could not fetch earnings for {ticker}: {e}")
            
            try:
                insider = fetch_insider_transactions(ticker)
            except Exception as e:
                logger.debug(f"  Warning: Could not fetch insider data for {ticker}: {e}")
            
            try:
                price_history = fetch_price_history(ticker, days=60)
            except Exception as e:
                logger.debug(f"  Warning: Could not fetch price history for {ticker}: {e}")
            
            # Fetch Alpha Vantage news sentiment (optional)
            news_sentiment = None
            try:
                # This automatically checks for API key and uses cache
                news_sentiment = fetch_news_sentiment(ticker)
            except Exception as e:
                logger.debug(f"  Warning: Could not fetch Alpha Vantage news for {ticker}: {e}")
            
            # Build the comprehensive briefing
            briefing = build_market_briefing(
                ticker=ticker,
                date=session_date_str,
                open_price=features.open,
                high_price=features.high,
                low_price=features.low,
                close_price=features.close,
                volume=int(features.volume),
                return_1d=features.return_1d,
                return_5d=features.return_5d,
                return_20d=features.return_20d,
                volatility_20d=features.volatility_20d,
                rsi_14=features.rsi_14,
                macd_line=features.macd_line,
                macd_signal=features.macd_signal,
                macd_histogram=features.macd_histogram,
                ma_20=features.ma_20,
                ma_50=features.ma_50,
                fundamentals=fundamentals,
                earnings=earnings,
                insider=insider,
                price_history=price_history,
                news_headlines=features.news_headlines,
            )
            
            # Add news sentiment if available
            if news_sentiment and news_sentiment.articles:
                briefing.news_sentiment = news_sentiment
            
            briefings.append(briefing)
        
        return briefings
    
    def _get_prices(
        self,
        market_adapters: dict,
        tickers: list[str],
        session_type: str,
        session_date: date,
    ) -> dict[str, float]:
        """Get execution prices for all tickers."""
        prices = {}
        
        for market_type, (adapter, market_tickers) in market_adapters.items():
            for ticker in market_tickers:
                try:
                    if session_type == "OPEN":
                        price = adapter.get_open_price(ticker, session_date)
                    else:
                        price = adapter.get_close_price(ticker, session_date)
                    
                    if price is None:
                        price = adapter.get_latest_price(ticker)
                    
                    if price:
                        prices[ticker.upper()] = price
                except Exception as e:
                    logger.warning(f"Error getting price for {ticker}: {e}")
        
        return prices
    
    def _run_competitor(
        self,
        competitor: CompetitorConfig,
        session_type: str,
        session_date_str: str,
        ticker_features: list[TickerFeatures],
        briefings: list[MarketBriefing],
        prices: dict[str, float],
        dry_run: bool,
    ) -> dict:
        """Run a single competitor through the trading flow."""
        run_id = str(uuid.uuid4())[:8]
        errors = []
        llm_calls = []
        
        # Check if already run today
        if not dry_run and self.storage.has_run_today(competitor.id, session_date_str, session_type):
            logger.info(f"  Already ran {session_type} session today, skipping")
            return {"skipped": True, "reason": "already_ran"}
        
        # Check call budget
        today_str = session_date_str
        current_count = self.storage.get_daily_call_count(competitor.provider, today_str)
        limit = self.config.daily_call_limits.get(competitor.provider, 100)
        
        if current_count + 2 > limit:
            logger.warning(f"  Daily call limit reached for {competitor.provider}, skipping")
            return {"skipped": True, "reason": "call_limit"}
        
        # Get broker and snapshot
        broker = self.get_broker(competitor)
        broker.update_prices(prices)
        snapshot_before = broker.get_snapshot()
        
        # Create LLM client
        try:
            llm_client = create_llm_client(
                provider=competitor.provider,
                model=competitor.model,
            )
        except Exception as e:
            errors.append(f"Failed to create LLM client: {e}")
            return {"error": str(e)}
        
        # Create agents
        strategist = Strategist(llm_client)
        risk_guard = RiskGuard(llm_client)
        
        # ====================================================================
        # Call #1: Strategist (with comprehensive briefings)
        # ====================================================================
        logger.info(f"  Call #1: Strategist (analyzing {len(briefings)} tickers)...")
        
        # Pass briefings (preferred) and ticker_features (fallback)
        strategist_result = strategist.invoke({
            "briefings": briefings,
            "ticker_features": ticker_features,  # Legacy fallback
            "session_date": session_date_str,
            "session_type": session_type,
        })
        
        llm_calls.append(LLMCall(
            call_type="strategist",
            provider=competitor.provider,
            model=competitor.model,
            prompt_tokens=strategist_result.prompt_tokens,
            completion_tokens=strategist_result.completion_tokens,
            latency_ms=strategist_result.latency_ms,
            success=strategist_result.success,
            error=strategist_result.error,
            raw_response=strategist_result.raw_response,
            prompt=strategist_result.prompt,
            system_prompt=strategist_result.system_prompt,
        ))
        
        # Handle strategist result
        strategist_proposal: Optional[StrategistProposal] = None
        if strategist_result.success:
            strategist_proposal = strategist_result.output
            logger.info(f"    ✓ Got {len(strategist_proposal.proposals)} proposals")
        else:
            errors.append(f"Strategist call failed: {strategist_result.error}")
            
            # Attempt repair if we got a response
            if strategist_result.raw_response:
                logger.info(f"  Attempting repair for Strategist...")
                strategist_proposal = self._repair_json_parse(
                    strategist_result.raw_response,
                    strategist_result.error or "Unknown error",
                    StrategistProposal,
                    get_strategist_proposal_schema(),
                    llm_client,
                    llm_calls,
                    competitor,
                )
        
        # ====================================================================
        # Call #2: RiskGuard
        # ====================================================================
        trade_plan = None
        
        if strategist_proposal:
            logger.info(f"  Call #2: RiskGuard...")
            
            risk_guard_result = risk_guard.invoke({
                "proposal": strategist_proposal,
                "snapshot": snapshot_before,
                "prices": prices,
                "max_orders": competitor.max_orders_per_run,
                "max_position_pct": competitor.max_position_pct * 100,
            })
            
            llm_calls.append(LLMCall(
                call_type="risk_guard",
                provider=competitor.provider,
                model=competitor.model,
                prompt_tokens=risk_guard_result.prompt_tokens,
                completion_tokens=risk_guard_result.completion_tokens,
                latency_ms=risk_guard_result.latency_ms,
                success=risk_guard_result.success,
                error=risk_guard_result.error,
                raw_response=risk_guard_result.raw_response,
                prompt=risk_guard_result.prompt,
                system_prompt=risk_guard_result.system_prompt,
            ))
            
            if risk_guard_result.success:
                trade_plan = risk_guard_result.output
                if trade_plan.orders:
                    logger.info(f"    ✓ Approved {len(trade_plan.orders)} orders")
                else:
                    logger.info(f"    ✓ HOLD decision (no orders)")
            else:
                errors.append(f"RiskGuard call failed: {risk_guard_result.error}")
                
                # Attempt repair
                if risk_guard_result.raw_response:
                    logger.info(f"  Attempting repair for RiskGuard...")
                    trade_plan = self._repair_json_parse(
                        risk_guard_result.raw_response,
                        risk_guard_result.error or "Unknown error",
                        TradePlan,
                        get_trade_plan_schema(),
                        llm_client,
                        llm_calls,
                        competitor,
                    )
        else:
            errors.append("Skipping RiskGuard: No strategist proposal available")
        
        # ====================================================================
        # Execute Orders
        # ====================================================================
        fills = []
        
        if trade_plan and trade_plan.orders and not dry_run:
            logger.info(f"  Executing {len(trade_plan.orders)} orders...")
            
            fills = broker.execute_orders(
                orders=trade_plan.orders,
                prices=prices,
                timestamp=datetime.utcnow(),
            )
            
            logger.info(f"  Filled {len(fills)} orders")
            
            # Save trades
            for fill in fills:
                self.storage.save_trade(competitor.id, fill)
        elif trade_plan:
            logger.info(f"  HOLD decision (no orders)")
        
        # Get snapshot after
        broker.update_prices(prices)
        snapshot_after = broker.get_snapshot()
        
        # ====================================================================
        # Save Results
        # ====================================================================
        if not dry_run:
            # Update call counter
            self.storage.increment_call_count(competitor.provider, today_str, 2)
            
            # Save snapshot
            self.storage.save_snapshot(competitor.id, snapshot_after)
            
            # Save run log
            run_log = RunLog(
                run_id=run_id,
                competitor_id=competitor.id,
                session_date=session_date_str,
                session_type=session_type,
                llm_calls=llm_calls,
                analyst_report=None,  # Legacy field, no longer used in 3-agent system
                strategist_proposal=strategist_proposal,
                trade_plan=trade_plan,
                fills=fills,
                errors=errors,
                snapshot_before=snapshot_before,
                snapshot_after=snapshot_after,
            )
            self.storage.save_run_log(run_log)
        
        return {
            "run_id": run_id,
            "strategist_proposal": strategist_proposal.model_dump() if strategist_proposal else None,
            "trade_plan": trade_plan.model_dump() if trade_plan else None,
            "fills": [f.model_dump() for f in fills],
            "errors": errors,
            "equity_before": snapshot_before.equity,
            "equity_after": snapshot_after.equity,
        }
    
    def _repair_json_parse(
        self,
        malformed: str,
        error: str,
        model_class,
        schema: dict,
        llm_client,
        llm_calls: list,
        competitor: CompetitorConfig,
    ):
        """
        Attempt to repair malformed JSON using an LLM call.
        
        This is used when the Strategist or RiskGuard returns invalid JSON.
        """
        logger.info(f"  Attempting JSON repair...")
        
        system_prompt, user_prompt = build_repair_prompt(malformed, error, schema)
        
        repair_response = llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.3,
        )
        
        # Log the repair attempt
        llm_calls.append(LLMCall(
            call_type="repair",
            provider=competitor.provider,
            model=competitor.model,
            prompt_tokens=repair_response.prompt_tokens,
            completion_tokens=repair_response.completion_tokens,
            latency_ms=repair_response.latency_ms,
            success=repair_response.success,
            error=repair_response.error,
            raw_response=repair_response.content,
            prompt=user_prompt,
            system_prompt=system_prompt,
        ))
        
        if repair_response.success:
            try:
                return model_class.model_validate_json(repair_response.content)
            except Exception as e:
                logger.warning(f"  Repair failed: {e}")
        
        return None

