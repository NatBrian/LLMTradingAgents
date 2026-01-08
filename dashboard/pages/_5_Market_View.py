"""Market View page - charts with trade markers."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta


def render_market_view():
    """Render the market view page."""
    st.title("📈 Market View")
    st.markdown("View market charts with trade markers")
    
    from utils import get_storage
    storage, config = get_storage()
    
    # Get all tickers from config
    all_tickers = []
    for market in config.markets:
        all_tickers.extend(market.tickers)
    all_tickers = sorted(set(all_tickers))
    
    if not all_tickers:
        st.warning("No tickers configured in arena config.")
        return
    
    # Ticker selector
    col1, col2 = st.columns(2)
    
    with col1:
        selected_ticker = st.selectbox("Select Ticker", options=all_tickers)
    
    with col2:
        days = st.slider("Days of History", min_value=30, max_value=365, value=90)
    
    # Determine market type for the ticker
    market_type = "us_equity"  # Default
    for market in config.markets:
        if selected_ticker in market.tickers:
            market_type = market.type
            break
    
    # Fetch market data
    from myllmtradingagents.market import create_market_adapter
    
    try:
        adapter = create_market_adapter(market_type, cache_dir=config.cache_dir)
        bars = adapter.get_daily_bars(selected_ticker, days=days)
    except Exception as e:
        st.error(f"Error fetching market data: {e}")
        return
    
    if bars.empty:
        st.warning(f"No market data available for {selected_ticker}")
        return
    
    st.markdown("---")
    
    # Get trades for this ticker
    trades = storage.get_trades(ticker=selected_ticker, limit=1000)
    
    # Latest price info
    latest = bars.iloc[-1]
    prev = bars.iloc[-2] if len(bars) > 1 else latest
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change = latest["Close"] - prev["Close"]
        change_pct = change / prev["Close"] if prev["Close"] > 0 else 0
        st.metric(
            "Close",
            f"${latest['Close']:.2f}",
            delta=f"{change:+.2f} ({change_pct:+.2%})",
        )
    
    with col2:
        st.metric("High", f"${latest['High']:.2f}")
    
    with col3:
        st.metric("Low", f"${latest['Low']:.2f}")
    
    with col4:
        st.metric("Volume", f"{latest['Volume']:,.0f}")
    
    st.markdown("---")
    
    # Candlestick chart
    st.subheader(f"{selected_ticker} Price Chart")
    
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=bars["Date"],
        open=bars["Open"],
        high=bars["High"],
        low=bars["Low"],
        close=bars["Close"],
        name="OHLC",
    ))
    
    # Add trade markers
    if trades:
        df_trades = pd.DataFrame(trades)
        df_trades["timestamp"] = pd.to_datetime(df_trades["timestamp"])
        
        # Buy markers
        buys = df_trades[df_trades["side"] == "BUY"]
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys["timestamp"],
                y=buys["price"],
                mode="markers",
                marker=dict(
                    symbol="triangle-up",
                    size=15,
                    color="green",
                ),
                name="BUY",
                hovertemplate="BUY %{y:.2f}<br>Qty: %{customdata}<extra></extra>",
                customdata=buys["qty"],
            ))
        
        # Sell markers
        sells = df_trades[df_trades["side"] == "SELL"]
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells["timestamp"],
                y=sells["price"],
                mode="markers",
                marker=dict(
                    symbol="triangle-down",
                    size=15,
                    color="red",
                ),
                name="SELL",
                hovertemplate="SELL %{y:.2f}<br>Qty: %{customdata}<extra></extra>",
                customdata=sells["qty"],
            ))
    
    fig.update_layout(
        title=f"{selected_ticker} Price with Trade Markers",
        yaxis_title="Price ($)",
        xaxis_title="Date",
        xaxis_rangeslider_visible=False,
        height=500,
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Volume chart
    st.subheader("Volume")
    
    colors = ["green" if bars.iloc[i]["Close"] >= bars.iloc[i]["Open"] else "red" 
              for i in range(len(bars))]
    
    fig_vol = go.Figure(data=[
        go.Bar(
            x=bars["Date"],
            y=bars["Volume"],
            marker_color=colors,
        )
    ])
    fig_vol.update_layout(
        title="Daily Volume",
        yaxis_title="Volume",
        height=250,
    )
    
    st.plotly_chart(fig_vol, use_container_width=True)
    
    # Feature summary
    st.markdown("---")
    st.subheader("Technical Indicators")
    
    from myllmtradingagents.market.features import compute_features
    
    features = compute_features(selected_ticker, bars)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Returns**")
        st.write(f"1D: {features.return_1d:+.2%}" if features.return_1d else "1D: N/A")
        st.write(f"5D: {features.return_5d:+.2%}" if features.return_5d else "5D: N/A")
        st.write(f"20D: {features.return_20d:+.2%}" if features.return_20d else "20D: N/A")
    
    with col2:
        st.markdown("**Momentum**")
        if features.rsi_14:
            rsi_color = "🟢" if 30 < features.rsi_14 < 70 else "🔴"
            st.write(f"RSI(14): {features.rsi_14:.1f} {rsi_color}")
        if features.macd_line:
            macd_signal = "🟢 Bullish" if features.macd_histogram > 0 else "🔴 Bearish"
            st.write(f"MACD: {macd_signal}")
    
    with col3:
        st.markdown("**Trend**")
        if features.ma_20:
            st.write(f"MA20: ${features.ma_20:.2f} ({features.ma_20_distance_pct:+.1%})")
        if features.ma_50:
            st.write(f"MA50: ${features.ma_50:.2f} ({features.ma_50_distance_pct:+.1%})")
    
    # Trade summary for this ticker
    if trades:
        st.markdown("---")
        st.subheader(f"Trades in {selected_ticker}")
        
        df_trades = pd.DataFrame(trades)
        df_trades["timestamp"] = pd.to_datetime(df_trades["timestamp"])
        
        # Add competitor names
        competitors = storage.list_competitors()
        comp_names = {c["id"]: c["name"] for c in competitors}
        df_trades["Competitor"] = df_trades["competitor_id"].map(comp_names)
        
        display_df = df_trades[["timestamp", "Competitor", "side", "qty", "price", "notional"]].copy()
        display_df.columns = ["Time", "Competitor", "Side", "Qty", "Price", "Notional"]
        display_df["Price"] = display_df["Price"].apply(lambda x: f"${x:.2f}")
        display_df["Notional"] = display_df["Notional"].apply(lambda x: f"${x:,.2f}")
        display_df["Time"] = display_df["Time"].dt.strftime("%Y-%m-%d %H:%M")
        
        st.dataframe(display_df.head(20), use_container_width=True)
