"""
Streamlit Dashboard for MyLLMTradingAgents.

Main entry point that sets up navigation to all pages.
"""

import os
import sys
from pathlib import Path

import streamlit as st
from utils import get_config_path, get_storage

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Page config
st.set_page_config(
    page_title="MyLLMTradingAgents Arena",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Sidebar
st.sidebar.title("🤖 LLM Trading Arena")
st.sidebar.markdown("---")

# Initialize storage
storage, config = get_storage()

# Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "🏆 Leaderboard",
        "📜 Run Trace",
        "💼 Portfolio",
        "📝 Trades",
        "📈 Market View",
    ],
    key="main_navigation"
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**DB:** `{config.db_path}`")

# Main content
if page == "🏆 Leaderboard":
    from pages._1_Leaderboard import render_leaderboard
    render_leaderboard()

elif page == "📜 Run Trace":
    from pages._2_Run_Trace import render_run_trace
    render_run_trace()

elif page == "💼 Portfolio":
    from pages._3_Portfolio import render_portfolio
    render_portfolio()

elif page == "📝 Trades":
    from pages._4_Trades import render_trades
    render_trades()

elif page == "📈 Market View":
    from pages._5_Market_View import render_market_view
    render_market_view()