# Handoff — Multi-System Paper Trader (Interactive Brokers)

**Prepared for:** Ash's assistant
**Goal:** finish, deploy, and run the paper-trading package that runs the
bake-off's **top three systems** concurrently on one Interactive Brokers
**paper** account.
**Location:** `Investment-Strat-clean/scans/live_multi/`
**Status:** code complete and offline-tested; needs a real run on a machine
where TWS/IB Gateway is installed and Yahoo Finance is reachable.

> Paper-trading results are hypothetical and not indicative of future
> performance. Not investment advice.

---

## 1. What this is

Three systems, run side-by-side against a single IBKR **paper** account so
their live signals can be compared:

| id | System | Stop method | Exit style | orderRef tag |
|----|--------|-------------|------------|--------------|
| 2  | Turtle ATR-Based | ATR (chandelier trail) | scaled | `LM_TURTLE` |
| 7  | Conviction (Pure Technical) | ATR (chandelier trail) | time-trail | `LM_CONVICTION` |
| 8  | 5LC (5-Level Conviction) | 7% percentage (trailed) | scaled | `LM_5LC` |

These three were chosen as the report's recommended **top 3** (see
`../../../Investments/Trading_Systems_Bakeoff_Report.md`, "All 12 cohorts" and
"Full period" rankings).

### Capital model (important)
Each system sizes off the **full account equity** (`CAPITAL_MODEL = 'full_equity'`
in `config.py`). That means combined exposure across the three systems can
exceed 100% — this is intentional. It's a **signal comparison**, not one
blended portfolio. To instead split the account into thirds, set
`CAPITAL_MODEL = 'split_equity'`.

Because systems can independently hold the same symbol, the net IBKR position
for a ticker may be the **sum** across systems. So each system reconciles
against **its own orders by orderId / orderRef**, never against the net account
position. Every order is tagged with the system's `orderRef`.

---

## 2. Files

All in `scans/live_multi/`:

| File | Purpose |
|------|---------|
| `config.py` | IB connection, active systems, capital model, scheduling, paths. Paper-port safety rail. |
| `systems.py` | The three `SystemConfig` objects — sizing, conviction multipliers, stop method, tags. |
| `ib_connector.py` | `ib_insync` wrapper. Tags every order with `orderRef`; exposes per-order fill/status queries for reconciliation. |
| `position_state.py` | Per-system JSON state (`state/state_<TAG>.json`). |
| `system_runner.py` | One system's daily cycle: reconcile → trail stops → scan → size → place orders → save. |
| `multi_trader.py` | Orchestrator. Does shared work once (prices, market health, fundamental screen), runs all three, prints a combined report. CLI entry point. |
| `README.md` | User-facing quickstart. |
| `HANDOFF.md` | This document. |
| `state/` | Runtime state, created on first run. Currently holds empty starter files. |

**Reused from the existing repo (do not duplicate):**
- `../backtesting/utils/technical_scanner.py` — the per-system entry scans (`scan_universe`, `get_market_health`).
- `../backtesting/utils/historical_screener.py` — the quarterly fundamental gate + price cache.
- `../backtesting/backtest_engine.py` — ATR / moving-average enrichment of price data.

The design mirrors the existing single-system trader in `../live/` (which runs
only one `SYSTEM_ID` at a time); `live_multi` generalises it to N systems.

---

## 3. Setup (one-time, on the trading machine)

1. **Python deps** (from repo root):
   ```bash
   pip install -r requirements.txt        # pandas, numpy, yfinance, ib_insync, schedule, TA-Lib, ...
   pip install ib_insync schedule         # belt-and-braces if not already present
   ```
   TA-Lib needs its C library first — see `https://github.com/TA-Lib/ta-lib-python`.

2. **Install & launch TWS or IB Gateway**, log in to the **paper** account.

3. **Enable the API:** TWS → Global Configuration → API → Settings →
   tick *Enable ActiveX and Socket Clients*. Note the socket port:
   - TWS paper = **7497**
   - IB Gateway paper = **4002**
   Add `127.0.0.1` to *Trusted IPs* if prompted.

4. **Match the port in `config.py`** (`IB_PORT`). The script **refuses to run on
   non-paper ports** unless `ALLOW_LIVE_PORT = True` — leave that `False`.

5. **Confirm the universe files exist** (referenced in `config.py`):
   - `scans/downloads_2026-01-01/IVV_symbols.csv`
   - `scans/downloads_2026-01-01/IJR_symbols.csv`
   If they live elsewhere, update `IVV_FILE` / `IJR_FILE` in `config.py`.

---

## 4. How to run

```bash
cd scans/live_multi

python multi_trader.py --dry-run     # SAFE FIRST RUN: logic only, no IB, no orders
python multi_trader.py               # one pass now against the paper account
python multi_trader.py --schedule    # stay running; fire every weekday at DAILY_RUN_TIME
python multi_trader.py --status      # print every system's open positions and exit
```

- Run **after the US close** (default `DAILY_RUN_TIME = '16:30'` local) so EOD
  prices are available from yfinance (~30 min lag).
- Entries are submitted as **Market-On-Open** for the next session.
- Protective **GTC stops** are placed immediately, so positions stay covered
  even when the script is offline.
- In a **bear** market (SPY < 200-day MA) no new entries open; existing
  positions keep trailing their stops.

### A daily pass, step by step
1. Connect once to IB; read NetLiquidation.
2. Download EOD prices for the IVV+IJR universe (cached).
3. Compute market health from SPY 50/200-day MAs.
4. Run the quarterly fundamental screen if due (shared gate → `state/shared_meta.json`).
5. For each system: reconcile its own orders → trail stops → scan entries →
   place tagged MOO entries + GTC stops → save its state file.
6. Print one combined report.

---

## 5. What's already verified

Done offline in the dev sandbox (Yahoo is blocked there, so no live data):
- All six modules compile (`python -m py_compile`).
- `systems.active_systems()` returns the three configs with correct tags,
  stop methods, orderRefs, and state filenames.
- Position sizing: risk-% sizing with the per-position value cap, for both
  ATR (Turtle/Conviction) and percentage (5LC) stops.
- Initial stops: ATR = `entry − mult×ATR`; percentage = `entry × (1 − 7%)`.
- Trailing stops ratchet **up only** (chandelier for ATR; trailed % for 5LC).
- End-to-end dry run of `run_system`: entries respect the daily cap, no
  duplicate entries on re-run, bear market blocks entries, state persists.

---

## 6. TODO for the assistant (to finish)

Ordered by priority.

1. **First real dry run, then live paper run.**
   - `python multi_trader.py --dry-run` on the trading machine; confirm the
     log shows a sane universe size, market health, and candidate entries.
   - Start TWS paper, then `python multi_trader.py`; confirm in TWS that three
     sets of orders appear, each stamped with its `orderRef`
     (`LM_TURTLE` / `LM_CONVICTION` / `LM_5LC`).

2. **Verify fill attribution end-to-end.** After the next open fills the MOO
   orders, run `python multi_trader.py --status` and confirm each system's
   state file reflects only its own fills (check `reconcile()` in
   `system_runner.py` is matching by orderId correctly).

3. **Decide on scheduling.** Either leave a terminal running with
   `--schedule`, or wrap a single `python multi_trader.py` call in Windows
   Task Scheduler / cron at 16:30 local on weekdays. (The repo already has a
   `schedule` dependency for the in-process option.)

4. **Confirm universe file paths** (Setup step 5). If the `downloads_*` folder
   has been re-dated, point `config.py` at the current CSVs.

5. **Optional polish (ask Ash before doing):**
   - Add `state/` to `.gitignore` so runtime JSON isn't committed.
   - Add fill/stop **alerts** (email via the existing Gmail connector, or
     Slack) — hook into `print_report()` in `multi_trader.py`.
   - If Ash later wires richer per-system **exit logic** into the backtester
     (`run_backtest.py` / `backtest_engine.py`), mirror it in
     `system_runner.py` so paper and backtest stay consistent.

---

## 7. Caveats / gotchas

- **Yahoo Finance must be reachable** on the trading machine. The dev sandbox
  blocks it, so the package was only tested offline there — the first real run
  happens on Ash's machine.
- **Paper port only.** `config.py` blocks non-paper ports by default. Do not
  set `ALLOW_LIVE_PORT = True` unless real-money trading is genuinely intended.
- **`IB_CLIENT_ID` must be unique** per connected API client. `live_multi` uses
  one connection (id 20). If the single-system `../live/` trader (id 10) is
  ever run at the same time, keep the ids distinct.
- **Entry scans for systems 7 & 8** come straight from the bake-off harness;
  their **stop methods** (ATR vs 7%) are honoured here even though the harness
  itself didn't fully wire per-system stops. Treat the per-system exit *styles*
  as approximations of the strategy specs, not exact replicas.
- **Combined exposure can exceed 100%** under `full_equity` — by design (see §1).

---

## 8. Quick reference — key settings in `config.py`

```python
IB_HOST = '127.0.0.1'
IB_PORT = 7497            # TWS paper. (IB Gateway paper = 4002)
IB_CLIENT_ID = 20
ALLOW_LIVE_PORT = False   # safety rail

ACTIVE_SYSTEM_IDS = [2, 7, 8]      # Turtle, Conviction, 5LC
CAPITAL_MODEL = 'full_equity'      # or 'split_equity'

SKIP_ENTRIES_IN_BEAR = True
MAX_ENTRIES_PER_DAY = 3            # per system, per day
CHANDELIER_ATR_MULT = 3.0
DAILY_RUN_TIME = '16:30'           # local time
```
