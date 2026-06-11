# Multi-System Paper Trader (Interactive Brokers)

Runs the bake-off report's **top three systems** concurrently against one
Interactive Brokers **paper** account:

| id | System | Stop method | Exit style |
|----|--------|-------------|------------|
| 2  | Turtle ATR-Based | ATR (chandelier trail) | scaled |
| 7  | Conviction (Pure Technical) | ATR (chandelier trail) | time-trail |
| 8  | 5LC (5-Level Conviction) | 7% percentage (trailed) | scaled |

Each system sizes off the **full account equity** (capital model
`full_equity`), keeps its **own state file**, and tags every order with a
per-system `orderRef` (`LM_TURTLE`, `LM_CONVICTION`, `LM_5LC`) so fills are
attributed correctly even when two systems hold the same symbol. Because of
this, combined exposure can exceed 100% — this is a signal-comparison paper
run, not one blended portfolio.

## Files

- `config.py` — IB connection, active systems, capital model, scheduling, paths.
- `systems.py` — the three `SystemConfig`s (sizing, stops, tags).
- `ib_connector.py` — `ib_insync` wrapper; orderRef tagging + per-order fill/status queries.
- `position_state.py` — per-system JSON state (`state/state_<TAG>.json`).
- `system_runner.py` — one system's daily scan / size / exit / order cycle.
- `multi_trader.py` — orchestrator: shared price+screen once, runs all three, combined report.

Reuses the backtest harness for signals: `backtesting/utils/technical_scanner.py`
(entry scans), `historical_screener.py` (fundamental gate), `backtest_engine.py`
(ATR/MA enrichment).

## Setup

1. Install deps (from repo root): `pip install ib_insync pandas yfinance schedule`
   plus the repo's `requirements.txt` (TA-Lib, etc.).
2. Launch **TWS** or **IB Gateway**, log into the **paper** account.
3. Enable the API: TWS → Global Configuration → API → Settings →
   *Enable ActiveX and Socket Clients*; confirm the **paper** socket port
   (TWS paper = **7497**, IB Gateway paper = **4002**). Match it in `config.py`.
4. `config.py` refuses non-paper ports unless `ALLOW_LIVE_PORT=True`.

## Run

```bash
cd scans/live_multi

python multi_trader.py --dry-run    # logic only — no IB, no orders (safe first run)
python multi_trader.py              # one pass now against the paper account
python multi_trader.py --schedule   # stay running; fire every weekday at DAILY_RUN_TIME
python multi_trader.py --status     # print every system's open positions
```

Run **after the close** (default `DAILY_RUN_TIME = 16:30` local) so EOD prices
are available from yfinance. Entries are placed as **Market-On-Open** for the
next session; protective **GTC stops** are placed immediately so positions are
covered even when the script is offline.

## How a daily pass works

1. Connect once to IB; read account value.
2. Download EOD prices for the IVV+IJR universe (shared, cached).
3. Compute market health from SPY's 50/200-day MAs (shared).
4. Quarterly fundamental screen if due (shared gate — `state/shared_meta.json`).
5. For each system: reconcile its own orders → trail stops → scan entries →
   place MOO entries + GTC stops (tagged) → save its state.
6. Print one combined report.

In a **bear** market (SPY < 200-day MA) no new entries are opened; existing
positions keep trailing their stops.

## Notes / caveats

- **Yahoo Finance must be reachable** on the machine running this (the dev
  sandbox blocks it). Run on your own machine.
- Reconciliation is **per-order, not per-net-position** — required because the
  full-equity model means the net IB position for a symbol can be the sum of
  several systems.
- The entry *scans* for systems 7/8 come straight from the bake-off harness;
  their **stop methods** are honoured here (ATR vs 7%) even though the harness
  didn't fully wire per-system stops. If you later wire richer per-system exit
  logic into the harness, mirror it in `system_runner.py`.
- Switch to `CAPITAL_MODEL = 'split_equity'` in `config.py` to size each
  system off `account_value / 3` instead.

> Paper-trading results are hypothetical and not indicative of future
> performance. Not investment advice.
