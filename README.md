# Mini Analyst 📉
https://antigravity-equity-analyst-mini.onrender.com/
##### A **minimal** stock analysis tool designed for resource-constrained environments.

- **Python-only** (no Node.js)
- **On-demand analysis** (no auto-scanning)
- **Minimal Dark UI** (High contrast, Green/Red indicators)

## Features

- **Real-time Indices**: NIFTY 50 and S&P 500 at a glance
- **Global Lookup**: Analyze any Indian (add `.NS`) or US stock
- **Technical Analysis**: 200 DMA, RSI, Volatility, 1y Return
- **Fundamental Analysis**: P/E, ROE, D/E, Margins, Growth
- **Combined Signal**: Weighted BUY/SELL recommendation
- **Low Footprint**: Idle memory ~100MB

## Quick Start

```bash
# Enter directory
cd mini_analyst

# Install dependencies
pip install -r requirements.txt

# Run locally
python3 app.py

# Open http://localhost:5000
```

## Run with Docker Compose

```bash
# Build and run
docker-compose up -d --build

# Stop
docker-compose down
```


## Tech Stack

- **Flask** - Lightweight web framework
- **yfinance** - Stock data (robust 2y fetch)
- **Gunicorn** - Production WSGI server

## Architecture & Optimization

- **Separate Agents**: Subprocess-based architecture (same as pro version)
- **No Database**: Completely stateless
- **On-demand**: Resources used only when analyzing
- **1 worker, 2 threads**: Optimized Gunicorn config
- **Slim Python Docker image**: Minimal container size
