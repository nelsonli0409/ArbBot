# Single-Exchange-ArbBot
This is a Python project that detects potential arbitrage opportunities on crypto spot markets (right now, I'm using Binance) by modeling exchange quotes as a directed graph and running Bellman-Ford on negative-log edge weights.

This project only performs paper trades, i.e. it doesn't place any live trades.

---

## How it works:
Given the best bid/ask quotes from Binance US, the project will:

1. Fetch market data (bookTicker) and symbol metadata (exchangeInfo)
2. Convert each trading pair into two directed conversion edges:
  - base -> quote at bid
  - quote -> base at 1/ask
3. Applies a trading fee and computes edge weight:
  - rate_effective = raw_rate * (1 - fee), where raw_rate is either bid or 1/ask
  - weight = -log(rate_effective)
4. Run Bellman-Ford to detect negative cycles
5. Simulate execution across the cycle with configurable slippage
6. Reports final amount and PnL (if there exists a negative cycle, and the profit/loss exceeds the minimum threshold)

A negative cycle in log-space implies multiplicative gain in normal price space.

---

## Features:
- Directed graph construction from real-time quotes
- Negative cycle detection with Bellman-Ford
- Execution simulation with:
  - fee per leg
  - buy/sell slippage in basis points (bps)
- CLI parameters for runtime tuning
- Human-readable and optional JSON output
- Unit tests with pytest

---

## Project Structure:
- `src/data_feed.py` - fetches and normalizes market data
- `src/graph.py` - validates market quotes then constructs and indexes edges
- `src/bellman_ford.py` - negative cycle detection and recovery
- `src/execution.py` - simulates a cycle then computes profit/loss
- `src/main.py` orchestration and CLI

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate           # macOS/Linux
# source .venv/Scripts/activate     # Windows

pip install -r requirements.txt
```

---

## Run

```bash
python -m src.main \
  --base-url https://api.binance.us \
  --timeout-sec 5 \
  --fee 0.001 \
  --start-currency USDT \
  --start-amount 1000 \
  --slippage-buy-bps 10 \
  --slippage-sell-bps 10 \
  --min-pnl-pct 0.2
```

Optional JSON output:

```bash
python -m src.main --json
```

---

## Testing

Run all tests:

```bash
pytest -q
```

---

## Example output (illustrative)

- Cycle: `USDT -> BTC -> ETH -> USDT`
- Start Currency: `USDT`
- Start Amount: `1000.00`
- Final Amount: `1002.85`
- PnL (absolute): `+2.85`
- PnL (percentage): `(+0.285%)`
- Slippage Buy: `10`
- Slippage Sell: `10`
- Orders: `...`

---

## Limitations

- Uses top-of-book prices only (no order book depth model)
- No latency/queue-position modeling
- No live order placement or exchange authentication
- Opportunity disappears before execution in real markets

---

## Future improvements

- Depth-aware slippage model
- Multi-cycle ranking and filtering
- Streaming/WebSocket data ingestion
- Historical replay/backtesting mode
- Risk controls and opportunity persistence checks
- Lower latency and multi-exchange arbitrage
