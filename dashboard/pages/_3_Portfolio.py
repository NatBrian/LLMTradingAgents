"""Portfolio page - current holdings and positions."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render_portfolio():
    """Render the portfolio page."""
    st.title("💼 Portfolio")
    st.markdown("View current holdings for each competitor")
    
    from utils import get_storage
    storage, config = get_storage()
    
    competitors = storage.list_competitors()
    
    if not competitors:
        st.warning("No competitors found.")
        return
    
    # Competitor selector
    competitor_names = {c["id"]: c["name"] for c in competitors}
    
    selected = st.selectbox(
        "Select Competitor",
        options=list(competitor_names.keys()),
        format_func=lambda x: competitor_names.get(x, x),
    )
    
    # Get latest snapshot
    snapshot = storage.get_latest_snapshot(selected)
    
    if not snapshot:
        st.info("No portfolio data yet. Run some trading sessions first!")
        return
    
    st.markdown("---")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Equity", f"${snapshot.equity:,.2f}")
    
    with col2:
        st.metric("Cash", f"${snapshot.cash:,.2f}")
    
    with col3:
        st.metric("Positions Value", f"${snapshot.positions_value:,.2f}")
    
    with col4:
        st.metric("Unrealized P&L", f"${snapshot.unrealized_pnl:,.2f}")
    
    st.markdown("---")
    
    # Allocation chart
    if snapshot.positions:
        st.subheader("Portfolio Allocation")
        
        allocation_data = [{"Asset": "Cash", "Value": snapshot.cash}]
        for pos in snapshot.positions:
            allocation_data.append({"Asset": pos.ticker, "Value": pos.market_value})
        
        df_alloc = pd.DataFrame(allocation_data)
        
        fig = px.pie(
            df_alloc,
            values="Value",
            names="Asset",
            title="Asset Allocation",
            hole=0.4,
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Positions table
        st.subheader("Current Positions")
        
        positions_data = []
        for pos in snapshot.positions:
            positions_data.append({
                "Ticker": pos.ticker,
                "Qty": pos.qty,
                "Avg Cost": f"${pos.avg_cost:.2f}",
                "Current": f"${pos.current_price:.2f}",
                "Market Value": f"${pos.market_value:,.2f}",
                "P&L": f"${pos.unrealized_pnl:,.2f}",
                "P&L %": f"{pos.unrealized_pnl_pct:+.2f}%",
            })
        
        df_pos = pd.DataFrame(positions_data)
        st.dataframe(df_pos, use_container_width=True)
        
        # P&L by position
        st.subheader("P&L by Position")
        
        pnl_data = [{"Ticker": pos.ticker, "P&L": pos.unrealized_pnl} for pos in snapshot.positions]
        df_pnl = pd.DataFrame(pnl_data)
        
        colors = ["green" if x >= 0 else "red" for x in df_pnl["P&L"]]
        
        fig_pnl = go.Figure(data=[
            go.Bar(
                x=df_pnl["Ticker"],
                y=df_pnl["P&L"],
                marker_color=colors,
            )
        ])
        fig_pnl.update_layout(
            title="Unrealized P&L by Position",
            xaxis_title="Ticker",
            yaxis_title="P&L ($)",
        )
        
        st.plotly_chart(fig_pnl, use_container_width=True)
    
    else:
        st.info("No open positions. Portfolio is 100% cash.")
    
    st.markdown("---")
    
    # Equity history
    st.subheader("Equity History")
    
    snapshots = storage.get_equity_curve(selected)
    
    if snapshots:
        dates = [s.timestamp for s in snapshots]
        equities = [s.equity for s in snapshots]
        cash_values = [s.cash for s in snapshots]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=equities,
            mode="lines",
            name="Total Equity",
            fill="tozeroy",
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=cash_values,
            mode="lines",
            name="Cash",
            line=dict(dash="dash"),
        ))
        
        fig.update_layout(
            title="Equity Over Time",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            hovermode="x unified",
        )
        
        st.plotly_chart(fig, use_container_width=True)
