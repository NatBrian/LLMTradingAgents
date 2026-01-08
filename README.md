# MyLLMTradingAgents

🤖 **Minimal LLM Trading Arena** - Compare multiple LLM providers on simulated trading

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

MyLLMTradingAgents is a minimal, free-tier compatible LLM-based trading arena system that:

- 🏆 **Compares multiple LLM competitors** (OpenRouter vs Gemini) using identical market data
- 📊 **Uses real market data** with simulated trades (paper portfolio)
- ⚡ **Exactly 2 LLM calls per competitor per session** (UnifiedAnalyst + DecisionRiskPM)
- 🌐 **Supports multiple markets**: US equities, Singapore equities, and crypto
- 📈 **Streamlit dashboard** for visualization and analysis
- ☁️ **Designed for Oracle Cloud Free Tier** deployment

> ⚠️ **Disclaimer**: This is for educational and research purposes only. Not financial advice.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Arena Runner                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Market Data  │───▶│ LLM Call #1  │───▶│ LLM Call #2  │───┐   │
│  │  (yfinance)  │    │ Unified-     │    │ Decision-    │   │   │
│  │  (ccxt)      │    │ Analyst      │    │ RiskPM       │   │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │   │
│                             │                    │           │   │
│                             ▼                    ▼           │   │
│                      AnalystReport         TradePlan         │   │
│                        (JSON)              (JSON)            │   │
│                                                              │   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │   │
│  │  SimBroker   │◀───│    Orders    │◀───┘               │   │
│  │  (Portfolio) │    │    + Fills   │                       │   │
│  └──────────────┘    └──────────────┘                       │   │
│         │                                                    │   │
│         ▼                                                    │   │
│  ┌──────────────┐                                           │   │
│  │   SQLite     │                                           │   │
│  │   Storage    │                                           │   │
│  └──────────────┘                                           │   │
│                                                              │   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### LLM Providers
- **OpenRouter**: Access to free models (Mistral, Zephyr, etc.)
- **Google Gemini**: Free tier with generous limits

### Markets Supported
- **US Equities**: NYSE/NASDAQ with exchange_calendars
- **Singapore Equities**: SGX with configurable calendar
- **Crypto**: 24/7 via CCXT (Binance, etc.)

### Simulation
- Virtual broker with cash, positions, P&L
- Configurable slippage and fees
- Max position size constraints
- Trade history and equity curves

### Dashboard
- 🏆 Leaderboard with equity curves
- 📊 Run traces with LLM outputs
- 💼 Portfolio positions
- 📝 Trade history
- 📈 Market charts with trade markers

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/MyLLMTradingAgents.git
cd MyLLMTradingAgents

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

### 2. Configuration

Create `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

```env
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_API_KEY=your_google_key
```

### 3. Initialize Database

```bash
python -m myllmtradingagents.cli init-db --config config/arena.example.yaml
```

### 4. Run a Trading Session

```bash
# Dry run (no actual trades)
python -m myllmtradingagents.cli run \
    --config config/arena.example.yaml \
    --session OPEN \
    --dry-run

# Live run
python -m myllmtradingagents.cli run \
    --config config/arena.example.yaml \
    --session OPEN
```

### 5. Launch Dashboard

```bash
python -m myllmtradingagents.cli dashboard --port 8501
```

Open http://localhost:8501 in your browser.

## Configuration

See `config/arena.example.yaml` for a complete example. Key sections:

```yaml
# Markets
markets:
  - type: us_equity
    tickers: [AAPL, MSFT, GOOGL]

# Competitors
competitors:
  - id: openrouter_mistral
    name: "OpenRouter Mistral"
    provider: openrouter
    model: "mistralai/mistral-7b-instruct:free"

  - id: gemini_flash
    name: "Gemini Flash"
    provider: gemini
    model: "gemini-1.5-flash"

# Simulation
simulation:
  initial_cash: 100000
  slippage_bps: 10
  fee_bps: 10
  max_position_pct: 0.25
```

## CLI Commands

```bash
# Run trading session
python -m myllmtradingagents.cli run --config CONFIG --session OPEN|CLOSE

# Initialize database
python -m myllmtradingagents.cli init-db --config CONFIG

# Check status
python -m myllmtradingagents.cli status --config CONFIG

# Launch dashboard
python -m myllmtradingagents.cli dashboard --port 8501

# Show next session
python -m myllmtradingagents.cli next-session --config CONFIG
```

## Deployment

### Oracle Cloud Free Tier

See [deploy/oracle_free.md](deploy/oracle_free.md) for detailed instructions.

Quick setup:

```bash
# On Ubuntu VM
bash scripts/install_ubuntu.sh

# Set up systemd timers
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo cp deploy/systemd/*.timer /etc/systemd/system/
sudo systemctl enable myllmtradingagents-open.timer
sudo systemctl enable myllmtradingagents-close.timer
```

## Project Structure

```
MyLLMTradingAgents/
├── config/
│   └── arena.example.yaml    # Sample configuration
├── myllmtradingagents/
│   ├── llm/                  # LLM clients (OpenRouter, Gemini)
│   ├── market/               # Market data adapters
│   ├── sim/                  # Simulation broker
│   ├── storage/              # SQLite storage
│   ├── arena/                # Arena runner
│   ├── cli.py                # CLI entrypoint
│   └── schemas.py            # Pydantic schemas
├── dashboard/
│   └── pages/                # Streamlit pages
├── deploy/
│   └── systemd/              # Systemd service files
├── tests/                    # Unit tests
└── scripts/                  # Helper scripts
```

## How It Works

### Trading Flow (per session)

1. **Fetch Market Data**: Get OHLCV for all tickers (yfinance/ccxt)
2. **Compute Features**: RSI, MACD, MAs, returns, volatility
3. **For each competitor**:
   - **Call #1 (UnifiedAnalyst)**: Analyze market → JSON AnalystReport
   - **Call #2 (DecisionRiskPM)**: Make decision → JSON TradePlan
   - Execute orders via SimBroker
   - Save snapshot and run log
4. **Update leaderboard**

### Strict JSON Outputs

All LLM outputs must conform to Pydantic schemas:

```python
class AnalystReport(BaseModel):
    session_date: str
    session_type: str
    market_summary: str
    analyses: list[TickerAnalysis]

class TradePlan(BaseModel):
    reasoning: str
    risk_assessment: str
    orders: list[Order]  # Empty = HOLD
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_broker.py -v
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Inspired by [TradingAgents](https://github.com/TauricResearch/TradingAgents) by Tauric Research.
