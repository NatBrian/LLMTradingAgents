"""Leaderboard page - compare all competitors."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render_leaderboard():
    """Render the leaderboard page."""
    st.title("🏆 Leaderboard")
    st.markdown("Compare performance across all LLM competitors")
    
    # Get data
    from utils import get_storage
    storage, config = get_storage()
    
    leaderboard = storage.get_leaderboard()
    
    if not leaderboard:
        st.warning("No competitors found. Run some trading sessions first!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(leaderboard)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Competitors", len(df))
    
    with col2:
        best = df.iloc[0] if not df.empty else None
        if best is not None:
            st.metric("Leader", best["name"], f"{best['total_return']:+.2%}")
    
    with col3:
        total_equity = df["current_equity"].sum()
        st.metric("Total AUM", f"${total_equity:,.0f}")
    
    with col4:
        total_trades = df["num_trades"].sum()
        st.metric("Total Trades", total_trades)
    
    st.markdown("---")
    
    # Leaderboard table
    st.subheader("Rankings")
    
    # Format DataFrame for display
    display_df = df[["name", "provider", "model", "current_equity", "total_return", "max_drawdown", "num_trades"]].copy()
    display_df.columns = ["Name", "Provider", "Model", "Equity", "Return", "Max DD", "Trades"]
    display_df["Equity"] = display_df["Equity"].apply(lambda x: f"${x:,.0f}")
    display_df["Return"] = display_df["Return"].apply(lambda x: f"{x:+.2%}")
    display_df["Max DD"] = display_df["Max DD"].apply(lambda x: f"{x:.2%}")
    display_df.index = range(1, len(display_df) + 1)
    display_df.index.name = "Rank"
    
    st.dataframe(display_df, use_container_width=True)
    
    st.markdown("---")
    
    # Equity curves chart
    st.subheader("Equity Curves")
    
    fig = go.Figure()
    
    for comp_id in df["competitor_id"]:
        snapshots = storage.get_equity_curve(comp_id)
        if snapshots:
            dates = [s.timestamp for s in snapshots]
            equities = [s.equity for s in snapshots]
            
            name = df[df["competitor_id"] == comp_id]["name"].iloc[0]
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=equities,
                mode="lines",
                name=name,
                hovertemplate="%{y:$,.0f}<extra>%{fullData.name}</extra>",
            ))
    
    fig.update_layout(
        title="Portfolio Equity Over Time",
        xaxis_title="Date",
        yaxis_title="Equity ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Returns comparison bar chart
    st.subheader("Returns Comparison")
    
    fig_bar = px.bar(
        df,
        x="name",
        y="total_return",
        color="provider",
        title="Total Return by Competitor",
        labels={"name": "Competitor", "total_return": "Return", "provider": "Provider"},
    )
    fig_bar.update_yaxes(tickformat=".1%")
    
    st.plotly_chart(fig_bar, use_container_width=True)
