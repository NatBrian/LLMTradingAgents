"""Run Trace page - inspect individual run details."""

import json
import streamlit as st
import pandas as pd


def render_run_trace():
    """Render the run trace page."""
    st.title("📊 Run Trace")
    st.markdown("Inspect LLM outputs and decisions for each run")
    
    from utils import get_storage
    storage, config = get_storage()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    competitors = storage.list_competitors()
    competitor_names = {c["id"]: c["name"] for c in competitors}
    
    with col1:
        selected_competitor = st.selectbox(
            "Competitor",
            options=["All"] + list(competitor_names.keys()),
            format_func=lambda x: "All Competitors" if x == "All" else competitor_names.get(x, x),
        )
    
    with col2:
        session_type = st.selectbox(
            "Session Type",
            options=["All", "OPEN", "CLOSE"],
        )
    
    with col3:
        limit = st.number_input("Max Results", min_value=10, max_value=500, value=50)
    
    # Get run logs
    comp_filter = None if selected_competitor == "All" else selected_competitor
    
    run_logs = storage.list_run_logs(
        competitor_id=comp_filter,
        limit=limit,
    )
    
    if session_type != "All":
        run_logs = [r for r in run_logs if r.session_type == session_type]
    
    if not run_logs:
        st.info("No run logs found. Run some trading sessions first!")
        return
    
    st.markdown("---")
    
    # Run selector
    run_options = {
        r.run_id: f"{r.session_date} {r.session_type} - {competitor_names.get(r.competitor_id, r.competitor_id)}"
        for r in run_logs
    }
    
    selected_run_id = st.selectbox(
        "Select Run",
        options=list(run_options.keys()),
        format_func=lambda x: run_options.get(x, x),
    )
    
    # Get selected run
    selected_run = next((r for r in run_logs if r.run_id == selected_run_id), None)
    
    if not selected_run:
        return
    
    st.markdown("---")
    
    # Run details
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Date", selected_run.session_date)
    with col2:
        st.metric("Session", selected_run.session_type)
    with col3:
        st.metric("Competitor", competitor_names.get(selected_run.competitor_id, selected_run.competitor_id))
    with col4:
        num_fills = len(selected_run.fills)
        st.metric("Trades", num_fills)
    
    # Errors
    if selected_run.errors:
        st.error("**Errors:**\n" + "\n".join(f"- {e}" for e in selected_run.errors))
    
    st.markdown("---")
    
    # LLM Calls
    st.subheader("🤖 LLM Calls")
    
    for i, call in enumerate(selected_run.llm_calls):
        call_title = f"Call {i+1}: {call.call_type.upper()} ({call.provider}/{call.model})"
        
        with st.expander(call_title, expanded=(i < 2)):
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Latency", f"{call.latency_ms}ms")
            with col2:
                st.metric("Prompt Tokens", call.prompt_tokens)
            with col3:
                st.metric("Completion Tokens", call.completion_tokens)
            with col4:
                status = "✅ Success" if call.success else "❌ Failed"
                st.metric("Status", status)
            
            if call.error:
                st.error(f"Error: {call.error}")
            
            # Tabs for Input/Output
            tab_system, tab_input, tab_output, tab_parsed = st.tabs(["⚙️ System Prompt", "📥 User Prompt", "📤 Raw Output", "🧩 Parsed Result"])
            
            with tab_system:
                if hasattr(call, 'system_prompt') and call.system_prompt:
                    st.code(call.system_prompt, language="text")
                else:
                    st.info("No system prompt recorded for this call.")

            with tab_input:
                if hasattr(call, 'prompt') and call.prompt:
                    st.code(call.prompt, language="text")
                else:
                    st.info("No prompt recorded for this call (legacy run).")
            
            with tab_output:
                if call.raw_response:
                    try:
                        parsed = json.loads(call.raw_response)
                        st.json(parsed)
                    except:
                        st.code(call.raw_response, language="json")
                else:
                    st.info("No raw response recorded.")
            
            with tab_parsed:
                # Try to link to the parsed object based on call type
                # Use getattr for safety with legacy runs/schemas
                strategist_prop = getattr(selected_run, 'strategist_proposal', None)
                trade_plan = getattr(selected_run, 'trade_plan', None)
                
                if call.call_type == "strategist" and strategist_prop:
                    st.json(strategist_prop)
                elif call.call_type == "risk_guard" and trade_plan:
                    st.json(trade_plan)
                elif hasattr(call, 'parsed_response') and call.parsed_response:
                     try:
                        st.json(json.loads(call.parsed_response))
                     except:
                        st.code(call.parsed_response)
                elif call.raw_response:
                    # Fallback for legacy runs: try to parse raw response on the fly
                    try:
                        st.json(json.loads(call.raw_response))
                    except:
                        st.info("Could not parse raw response as JSON.")
                else:
                    st.info("Parsed result not directly linked to this call record.")
    
    st.markdown("---")
    
    # Analyst Report
    if selected_run.analyst_report:
        st.subheader("📝 Analyst Report")
        
        report = selected_run.analyst_report
        
        if report.market_summary:
            st.info(f"**Market Summary:** {report.market_summary}")
        
        for analysis in report.analyses:
            with st.expander(f"{analysis.ticker} - {analysis.signal.value} ({analysis.sentiment.value})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Confidence", f"{analysis.confidence:.0%}")
                
                with col2:
                    st.metric("Signal", analysis.signal.value)
                
                if analysis.rationale:
                    st.markdown("**Rationale:**")
                    for point in analysis.rationale:
                        st.markdown(f"- {point}")
                
                if analysis.risks:
                    st.markdown("**Risks:**")
                    for risk in analysis.risks:
                        st.markdown(f"- ⚠️ {risk}")
                
                if analysis.invalidators:
                    st.markdown("**Invalidators:**")
                    for inv in analysis.invalidators:
                        st.markdown(f"- ❌ {inv}")
    
    st.markdown("---")
    
    # Trade Plan
    if selected_run.trade_plan:
        st.subheader("📋 Trade Plan")
        
        plan = selected_run.trade_plan
        
        st.markdown(f"**Reasoning:** {plan.reasoning}")
        
        if plan.risk_assessment:
            st.warning(f"**Risk Assessment:** {plan.risk_assessment}")
        
        if plan.orders:
            st.markdown("**Orders:**")
            orders_data = []
            for order in plan.orders:
                orders_data.append({
                    "Ticker": order.ticker,
                    "Side": order.side.value,
                    "Qty": order.qty,
                    "Type": order.order_type.value,
                })
            st.dataframe(pd.DataFrame(orders_data), use_container_width=True)
        else:
            st.info("Decision: **HOLD** (no orders)")
    
    st.markdown("---")
    
    # Fills
    if selected_run.fills:
        st.subheader("✅ Executed Trades")
        
        fills_data = []
        for fill in selected_run.fills:
            fills_data.append({
                "Ticker": fill.ticker,
                "Side": fill.side.value,
                "Qty": fill.qty,
                "Price": f"${fill.fill_price:.2f}",
                "Notional": f"${fill.notional:,.2f}",
                "Fees": f"${fill.fees:.2f}",
            })
        
        st.dataframe(pd.DataFrame(fills_data), use_container_width=True)
    
    # Portfolio snapshots
    st.markdown("---")
    st.subheader("💰 Portfolio Change")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Before:**")
        if selected_run.snapshot_before:
            st.metric("Equity", f"${selected_run.snapshot_before.equity:,.2f}")
            st.metric("Cash", f"${selected_run.snapshot_before.cash:,.2f}")
    
    with col2:
        st.markdown("**After:**")
        if selected_run.snapshot_after:
            change = selected_run.snapshot_after.equity - (selected_run.snapshot_before.equity if selected_run.snapshot_before else 0)
            st.metric("Equity", f"${selected_run.snapshot_after.equity:,.2f}", delta=f"${change:,.2f}")
            st.metric("Cash", f"${selected_run.snapshot_after.cash:,.2f}")
