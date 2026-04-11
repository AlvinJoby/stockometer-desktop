# Stockometer

A Flask web app for analyzing stocks. Enter any ticker symbol and get a full technical breakdown — interactive charts, RSI and MACD indicators, moving averages, buy/sell signals, periodic returns, key company stats, and a comparison against the stock's home market index.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Features](#features)
- [How It Works](#how-it-works)
- [Technical Indicators](#technical-indicators)
- [Index Benchmarking](#index-benchmarking)
- [Ticker Autocomplete](#ticker-autocomplete)
- [Local Setup](#local-setup)
- [Running Tests](#running-tests)
- [Requirements](#requirements)
- [Notes & Limitations](#notes--limitations)

---

## Overview

Stockometer fetches one year of daily OHLCV data for any stock via `yfinance`, runs a set of technical indicators and performance metrics over it, and renders the results as an interactive Plotly chart alongside a panel of company stats and returns.

The landing page has a ticker search input with live autocomplete. Type a company name or symbol and the app suggests matching tickers from Yahoo Finance before you even submit.

---

## Project Structure

```
stockometer/
│
├── app.py                      # Flask app, routes, and analysis orchestration
├── config.py                   # Shared module-level state (symbol, data)
├── retrieveData.py             # yfinance data fetching and column normalization
├── validation.py               # Input validation
├── graph.py                    # Plotly chart assembly and HTML export
├── symbol_search.py            # Ticker autocomplete backed by yfinance.Search
│
├── analysis/
│   ├── buysell_marker.py       # Buy/sell signal generation (RSI + EMA trend)
│   ├── company_data.py         # Company metadata extraction and number formatting
│   ├── daily_returns.py        # Price change and daily return computation
│   ├── ma_indicator.py         # SMA and EMA calculations
│   ├── macd_indicator.py       # MACD line, signal line, and histogram
│   ├── periodic_returns.py     # 1D / 1W / 1M / 6M return snapshots
│   └── rsi_indicator.py        # RSI (Wilder's smoothing) + buy/sell markers
│
├── charts/
│   ├── price_chart.py          # Candlestick chart trace
│   ├── ma_chart.py             # SMA / EMA overlay traces
│   ├── rsi_chart.py            # RSI panel with overbought/oversold lines
│   └── macd_chart.py           # MACD histogram + line + signal panel
│
├── stockIndex/
│   ├── getIndex.py             # Maps exchange codes to benchmark index tickers
│   └── indexPerformance.py     # Alpha, relative strength, and CAGR computation
│
├── templates/
│   ├── index.html              # Landing page with ticker input and autocomplete
│   └── main.html               # Analysis results page
│
├── static/
│   ├── index.css               # Landing page styles + autocomplete dropdown
│   ├── index.js                # Autocomplete fetch, keyboard nav, debounce logic
│   ├── main.css                # Results page styles (dark theme, responsive)
│   └── main.js                 # Drag-to-resize chart/side-panel divider
│
├── tests/
│   ├── __init__.py
│   ├── test_app.py             # Route-level tests for /analyze and /api/symbols
│   ├── test_graph.py           # Chart generation smoke tests
│   └── test_symbol_search.py  # Unit tests for normalize_quote and search_symbols
│
├── requirements.txt
└── .gitignore
```

---

## Features

- **Interactive candlestick chart** — One year of daily OHLCV data rendered with Plotly. Defaults to the last 6 months on load. A draggable divider lets you resize the chart panel against the side stats panel.
- **Technical indicators** — RSI, SMA (20), EMA (20/50/100), and MACD rendered in stacked subpanels below the price chart.
- **Buy/sell signals** — RSI crossover signals marked on the RSI panel across the full history. A combined RSI + EMA trend signal is also generated for the most recent bar.
- **Periodic returns** — 1D, 1W, 1M, and 6M return percentages shown in the side panel.
- **Key stats** — Day high/low, 50-day MA, 52-week high/low, P/E ratio, and dividend yield.
- **Company overview** — Market cap, revenue, net income, profit margin, beta, price-to-book, and 52-week range in a metrics panel below the chart.
- **Index benchmarking** — The stock is automatically compared against its home market index (e.g. Nifty 50 for NSE stocks, S&P 500 for US exchanges). Alpha, CAGR, relative strength, information ratio, and outperformance statistics are computed and surfaced on the results page.
- **Ticker autocomplete** — Live symbol suggestions while typing, with keyboard navigation and mouse selection.
- **Responsive UI** — Layout adapts for mobile: panels stack vertically, the stat grid goes two-column, and typography scales down.

---

## How It Works

### Request flow

1. User visits `/` and types a ticker into the search input.
2. As they type, `index.js` debounces calls to `GET /api/symbols?q=<query>` and renders a dropdown of matching tickers from Yahoo Finance.
3. User submits the form to `POST /analyze`.
4. `app.py` validates the symbol, fetches one year of daily OHLCV data via `yfinance`, and runs the full indicator pipeline.
5. The stock's exchange is resolved to a benchmark index ticker via `stockIndex/getIndex.py`. Index data is fetched and the performance comparison is computed.
6. `graph.py` assembles all chart traces into a multi-panel Plotly figure and exports it as an embedded HTML fragment.
7. The results are rendered into `main.html` and returned to the browser.

### Analysis pipeline (in order)

```
retrieve_data()              → fetch 1y daily OHLCV from yfinance
normalize_columns()          → flatten MultiIndex columns produced by yfinance
price_change()               → Close.diff() → priceChange column
dailyReturns()               → pct_change * 100 → dailyReturns column
calculate_rsi()              → Wilder's 14-period RSI
calculate_sma(20)            → 20-period simple moving average
calculate_ema(20/50/100)     → exponential moving averages
calculate_macd()             → MACD(12,26,9): line, signal, histogram
marking_bs()                 → latest-bar buy/sell signal (RSI + EMA trend)
mark_signals()               → RSI crossover markers across full history
periodic_returns()           → 1D / 1W / 1M / 6M return snapshots
index_performance_pipeline() → benchmark comparison (if index available)
generate_graph()             → assemble and export Plotly chart as HTML
```

---

## Technical Indicators

### RSI (`analysis/rsi_indicator.py`)

14-period RSI using Wilder's smoothing. The initial average is a simple 14-period mean; subsequent values apply the recursive formula `(prev_avg * 13 + current) / 14`. Buy markers appear where RSI crosses up through 30 (oversold recovery); sell markers where it crosses down through 70 (overbought drop). Reference lines are drawn at 30, 50, and 70.

### Moving Averages (`analysis/ma_indicator.py`)

- `calculate_sma(data, period)` — rolling mean over `Close`, stored as `sma_indicator`
- `calculate_ema(data, period)` — EMA over `Close`, stored as `ema_<period>`
- `custom_ema(data, period, column, cname)` — EMA over any column with a custom output name (used internally by MACD)

### MACD (`analysis/macd_indicator.py`)

Standard MACD(12, 26, 9). MACD line is EMA(12) minus EMA(26). Signal line is a 9-period EMA of the MACD line. Histogram is MACD line minus signal line. Green bars are positive, red bars are negative.

### Buy/Sell Signal (`analysis/buysell_marker.py`)

Evaluates only the most recent bar. A buy signal fires when RSI crosses up through 30 and close is above EMA(20). A sell signal fires when RSI crosses down through 70 and close is below EMA(20). The signal value (1, -1, or 0) and a plain-text reason are written into the last row of the DataFrame.

### Periodic Returns (`analysis/periodic_returns.py`)

Returns `pct_change(n) * 100` for the final row across four lookback windows:

| Label | Trading Days |
|-------|-------------|
| 1D    | 1           |
| 1W    | 5           |
| 1M    | 21          |
| 6M    | 126         |

---

## Index Benchmarking

When a stock is analyzed, its exchange code (from `yfinance` ticker info) is mapped to a benchmark index by `stockIndex/getIndex.py`. Index data is then fetched and fed into `stockIndex/indexPerformance.py` alongside the stock data.

### Supported exchanges

| Exchange | Benchmark Index | Market |
|----------|----------------|--------|
| NSE | ^NSEI | Nifty 50, India |
| BSE | ^BSESN | BSE Sensex, India |
| NMS / NYQ / ASE | ^GSPC | S&P 500, US |
| LSE | ^FTSE | FTSE 100, UK |
| TYO | ^N225 | Nikkei 225, Japan |
| HKG | ^HSI | Hang Seng, HK |
| SHH | 000001.SS | SSE Composite, China |
| SHE | 399001.SZ | SZSE Component, China |
| FRA | ^GDAXI | DAX, Germany |
| PAR | ^FCHI | CAC 40, France |
| TOR | ^GSPTSE | S&P/TSX, Canada |
| ASX | ^AXJO | ASX 200, Australia |
| KSC | ^KS11 | KOSPI, South Korea |
| SAO | ^BVSP | Bovespa, Brazil |
| JNB | ^JN0U.JO | FTSE JSE, South Africa |

### Computed metrics

Both series are normalized to 100 at the start of the period and compared on every overlapping trading day. The summary includes: total return and CAGR for stock and index, cumulative alpha, percentage of days outperformed/underperformed, maximum and minimum cumulative alpha, annualized volatility for both, information ratio (annualized mean daily alpha divided by its standard deviation), relative strength and 20-day trend, and the worst drawdown in cumulative alpha from its peak.

If the exchange is unrecognized, the index fetch fails, or fewer than 30 overlapping trading days exist, benchmarking is silently skipped and the rest of the page renders normally.

---

## Ticker Autocomplete

The landing page calls `GET /api/symbols?q=<query>` as the user types. The backend uses `yfinance.Search` and returns up to 8 normalized results filtered to equities, ETFs, and mutual funds.

**Backend (`symbol_search.py`):**
- Queries shorter than 2 characters return an empty list immediately
- Results are deduplicated by symbol
- Items missing a symbol or with a disallowed `quoteType` are dropped
- Any upstream Yahoo Finance error returns an empty list (fail-closed, no 500s)

**Frontend (`static/index.js`):**
- Input changes are debounced by 250ms
- Stale responses from slower in-flight requests are discarded via a request counter
- Keyboard: `↑`/`↓` to navigate, `Enter` to select, `Escape` to close
- Mouse: hover highlights a row, click selects it
- Selection writes only the ticker symbol into the input; the existing form submit flow is unchanged

---

## Local Setup

1. Clone the repo and create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the development server:
   ```bash
   python app.py
   ```

4. Open `http://127.0.0.1:5000` in your browser.

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers:

- `POST /analyze` — missing symbol (400), empty data response (502), successful full render (200), missing company fields rendering as N/A, chart generation failure (500)
- `GET /api/symbols` — empty query, valid JSON response shape
- `generate_graph` — Plotly HTML output with all supported indicators
- `normalize_quote` — field normalization, type filtering, missing symbol handling
- `search_symbols` — short-query short-circuit, deduplication, type filtering, upstream failure fallback

All Yahoo Finance calls are mocked; no internet connection is needed to run the test suite.

---

## Requirements

```
Flask>=3.0,<3.2
pandas>=2.2,<2.4
plotly>=5.24,<6.1
yfinance>=0.2.54,<0.3
```

Python 3.9 or later is required.

---

## Notes & Limitations

- **Live data only.** All market data is fetched at request time via `yfinance`. There is no caching layer, so each analysis hits Yahoo Finance fresh and requires an internet connection.
- **One year of history.** `retrieve_data` always fetches `period="1y"` at daily intervals. The RSI warmup period consumes the first ~14 bars, and the 100-period EMA needs ~100 bars before stabilizing, so early values for those indicators will be `NaN`.
- **Index benchmarking is best-effort.** Silently skipped if the exchange is unrecognized, the index fetch fails, or fewer than 30 overlapping trading days are available. The rest of the analysis and page render are unaffected.
- **Buy/sell signal is point-in-time.** `marking_bs` only evaluates the most recent bar using a simplified RSI crossover + EMA trend rule. It is not a trading recommendation.
- **Not safe for concurrent users in production.** `config.py` holds the last analyzed symbol and DataFrame at module level. This is fine for local single-user use but would cause data races under concurrent requests.
- **Single symbol per request.** The app analyzes one ticker at a time. Portfolio-level or multi-ticker comparison is not supported.