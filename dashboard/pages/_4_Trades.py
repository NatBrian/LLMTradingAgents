"""Trades page - trade history with filters."""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta


def render_trades():
    """Render the trades page."""
    st.title("📝 Trades")
    st.markdown("View trade history across all competitors")
    
    from utils import get_storage
    storage, config = get_storage()
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    competitors = storage.list_competitors()
    competitor_names = {c["id"]: c["name"] for c in competitors}
    
    with col1:
        selected_competitor = st.selectbox(
            "Competitor",
            options=["All"] + list(competitor_names.keys()),
            format_func=lambda x: "All" if x == "All" else competitor_names.get(x, x),
        )
    
    with col2:
        # Get all unique tickers from trades
        all_trades = storage.get_trades(limit=10000)
        tickers = sorted(set(t["ticker"] for t in all_trades))
        
        selected_ticker = st.selectbox(
            "Ticker",
            options=["All"] + tickers,
        )
    
    with col3:
        side_filter = st.selectbox(
            "Side",
            options=["All", "BUY", "SELL"],
        )
    
    with col4:
        limit = st.number_input("Max Results", min_value=50, max_value=5000, value=500)
    
    # Get trades
    comp_filter = None if selected_competitor == "All" else selected_competitor
    ticker_filter = None if selected_ticker == "All" else selected_ticker
    
    trades = storage.get_trades(
        competitor_id=comp_filter,
        ticker=ticker_filter,
        limit=limit,
    )
    
    if side_filter != "All":
        trades = [t for t in trades if t["side"] == side_filter]
    
    if not trades:
        st.info("No trades found matching filters.")
        return
    
    st.markdown("---")
    
    # Summary metrics
    df = pd.DataFrame(trades)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", len(df))
    
    with col2:
        total_volume = df["notional"].sum()
        st.metric("Total Volume", f"${total_volume:,.0f}")
    
    with col3:
        buys = len(df[df["side"] == "BUY"])
        st.metric("Buys", buys)
    
    with col4:
        sells = len(df[df["side"] == "SELL"])
        st.metric("Sells", sells)
    
    st.markdown("---")
    
    # Trade table
    st.subheader("Trade History")
    
    # Format for display
    display_df = df.copy()
    display_df["timestamp"] = pd.to_datetime(display_df["timestamp"])
    display_df = display_df.sort_values("timestamp", ascending=False)
    
    # Add competitor name
    display_df["Competitor"] = display_df["competitor_id"].map(competitor_names)
    
    # Format columns
    display_df = display_df[[
        "timestamp", "Competitor", "ticker", "side", "qty", "price", "notional", "fees"
    ]]
    display_df.columns = ["Time", "Competitor", "Ticker", "Side", "Qty", "Price", "Notional", "Fees"]
    
    display_df["Price"] = display_df["Price"].apply(lambda x: f"${x:.2f}")
    display_df["Notional"] = display_df["Notional"].apply(lambda x: f"${x:,.2f}")
    display_df["Fees"] = display_df["Fees"].apply(lambda x: f"${x:.2f}")
    display_df["Time"] = display_df["Time"].dt.strftime("%Y-%m-%d %H:%M")
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trade Count by Ticker")
        
        ticker_counts = df.groupby("ticker").size().reset_index(name="count")
        ticker_counts = ticker_counts.sort_values("count", ascending=False).head(10)
        
        fig = px.bar(
            ticker_counts,
            x="ticker",
            y="count",
            title="Top 10 Most Traded Tickers",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Buy vs Sell Distribution")
        
        side_counts = df.groupby("side").size().reset_index(name="count")
        
        fig = px.pie(
            side_counts,
            values="count",
            names="side",
            title="Buy/Sell Ratio",
            color="side",
            color_discrete_map={"BUY": "green", "SELL": "red"},
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Volume over time
    st.subheader("Trading Volume Over Time")
    
    df_time = df.copy()
    df_time["date"] = pd.to_datetime(df_time["timestamp"]).dt.date
    daily_volume = df_time.groupby("date")["notional"].sum().reset_index()
    
    fig = px.bar(
        daily_volume,
        x="date",
        y="notional",
        title="Daily Trading Volume",
        labels={"date": "Date", "notional": "Volume ($)"},
    )
    st.plotly_chart(fig, use_container_width=True)
