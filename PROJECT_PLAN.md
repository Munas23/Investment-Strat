# Trading System — Clean-Up & Go-Live Plan

*Prepared 3 June 2026. Owner: Ash. Goal: turn years of accumulated strategy code into one trusted, runnable system and take the winning strategy to Interactive Brokers paper trading.*

---

## 1. The decision in one line

The code is already organised. What's missing is a **decision** — which single strategy you're committing to — and the **proof** to back it. So the plan is: standardise one fair test harness, run every candidate strategy through it on both US and ASX universes, pick the winner on risk-adjusted return, and wire only that winner to IB paper trading. Everything else gets archived, not deleted.

This matches the vision in *The Grand Plan*: backtest to find winners, make risk management central, track the portfolio, download EOD data daily, keep it in GitHub, then trade through Interactive Brokers — starting with paper.

---

## 2. Where things actually stand

**`Investment-Strat-clean` is the canonical repo.** It has a real git history including a commit titled *"Reorganise repository structure to eliminate duplication."* The loose `GitHub` root folder is the old workspace — the same code plus years of stray scripts, 548 MB of logs, one-off CSVs, and duplicate PDFs dumped at the top level. Work in the clean repo; treat the root as an attic.

**What you've built** is a momentum / breakout equity system rooted in Minervini's SEPA methodology, which evolved into several strategy families:

- **5LC (5 Level Conviction)** — your most developed strategy. Minervini fundamentals + technicals, with a SPY market-health overlay that *halves* position sizes in weak markets and *doubles* them in confirmed bull markets. Has both S&P 500 and ASX300 versions, and the most recent trade outputs (March 2026). This is the current front-runner.
- **Conviction** scanners — ASX300, S&P 500, and international (Germany, Hong Kong, UK).
- **Consolidation / VCP** variants of the conviction strategy.
- **Qullamaggie, Turtle, Multi-stock breakout, SPY-200MA** — earlier breakout/trend experiments with backtest logs from mid-2025.
- **A live trading system** (`scans/live/`) already wired to IB TWS: connects, syncs positions, manages chandelier trailing stops, places market-on-open entries, persists state, prints a daily report. This is your bridge to real trading and it already exists.

**The honest gaps:**

1. **No top-level README** and no single "this is the strategy I run and here's how" document. A newcomer (or you in six months) can't tell what's live vs. abandoned.
2. **The backtests can't be trusted yet.** The saved logs are raw equity curves with no comparable summary metrics (CAGR, Sharpe, max drawdown, win rate) computed side by side. Worse, several runs show **cash going negative** — e.g. the ASX300 consolidation run drops to roughly −$12,000 cash early in 2015 — which means the simulation was quietly using leverage and not enforcing a cash limit. Numbers from a backtest that can overdraw the account are not safe to size real money against.
3. **Heavy duplication of logic.** `testing/` alone holds ~50 experimental variants; `minervini_fundamentals.py` exists in at least three places; `_archive/Trading-sys-v2/` has `both.py`, `both2.py`, `both3.py`, etc. The *organisation* is clean but the *content* still has many near-identical files.
4. **No standard metrics layer.** Each strategy reports results its own way, so they can't be compared fairly — which is the whole point of a bake-off.

---

## 3. The clean goal

> **A single repository where one command runs any strategy through one identical, leak-free, cash-constrained backtest harness on the US and ASX universes; produces one comparable scorecard; and where the winning strategy runs end-to-end into IB paper trading with daily EOD data capture and portfolio/risk tracking.**

Concretely, "done" looks like:

- `README.md` at the repo root that explains the system and points to the live strategy.
- One backtest harness every strategy plugs into — no per-strategy backtest scripts.
- A `results/scorecard.csv` ranking every candidate on the same metrics over the same periods.
- The chosen strategy connected to IB **paper** trading, running daily, logging fills and positions.
- A daily EOD data download saving prices for all target universes.

---

## 4. Keep / Archive / Delete

Nothing is deleted outright — everything goes to `_archive/` or stays in git history. Suggested triage:

**Keep and promote (the spine of the system):**

- `strategies/minervini/5LC/` — front-runner strategy.
- `strategies/conviction-asx300/` — second candidate family.
- `scans/live/` — the IB live/paper trading runner.
- `backtesting/backtester.py` + `scans/backtesting/` — basis for the unified harness.
- `backtesting/data/*_symbols.csv` and `backtesting/config/*_config.json` — your universe and config definitions; these are assets.
- The risk-management framework docs in `scans/` (`RISK_MANAGEMENT_FRAMEWORK.md`, `qullamaggie_atr_risk_management.md`).

**Archive (valuable history, not the live path):**

- `testing/` — the ~50 experiments. Keep the README summaries; move the rest to `_archive/experiments/`.
- `backtesting/logs/` — 100s of old run artifacts. Keep nothing the harness can regenerate.
- Earlier breakout/turtle/qullamaggie strategy files once the bake-off confirms they don't win.
- All loose files in the `GitHub` root — sweep into `_archive/legacy-root/`.

**Delete safely (regenerable noise):**

- `__pycache__/`, `*.pyc`, the 548 MB of `.log` files (already git-ignored), duplicate PDFs.

---

## 5. The strategy bake-off (your "test them all and see")

This is the heart of the work and the thing that picks your winner objectively.

**Step 1 — Build one harness.** A single `run_backtest.py` that takes `--strategy`, `--universe {sp500,russell1000,asx300,ftse100,hk}`, and `--period`. It must:
- enforce a hard cash constraint (no negative cash — the bug found above),
- apply realistic costs (commission + slippage),
- screen point-in-time to avoid lookahead bias,
- and write standardised outputs.

**Step 2 — One metrics layer.** Every run emits the same row: CAGR, Sharpe, Sortino, max drawdown, Calmar, win rate, avg win/loss, exposure, number of trades, turnover. Append to `results/scorecard.csv`.

**Step 3 — The candidates.** 5LC, Conviction (Standard), Conviction (Consolidation/VCP), Qullamaggie breakout, Turtle, and a buy-and-hold index benchmark as the bar to beat.

**Step 4 — Both markets, same windows.** Run each candidate on US (S&P 500 + Russell 1000) and AU (ASX300) over identical periods, including a stress window (2022 bear) and a strong-bull window, so you see regime behaviour — your own SPY market-health analysis already shows the strategy does ~10× better in strong bull vs. weak bear markets.

**Step 5 — Pick on risk-adjusted return,** not raw return. Calmar and max drawdown matter more than CAGR for deciding what you can stomach with real money. The winner advances to paper trading; everything else is archived with its scorecard row as the record of why.

---

## 6. Phased roadmap to paper trading

**Phase 0 — Foundation (½ day).** Add root `README.md`, pin `requirements.txt`, confirm the venv reproduces, tidy `.gitignore`. Push to GitHub. *(You flagged you're new to GitHub — this phase includes a hand-held walkthrough of branch/commit/push.)*

**Phase 1 — Unified harness + metrics (the big lift).** Build `run_backtest.py` and the metrics layer. Fix the negative-cash / leverage bug. Validate on one known strategy.

**Phase 2 — Bake-off.** Run all candidates on both markets, generate `scorecard.csv`, review together, pick the winner.

**Phase 3 — Harden the winner.** Lock its parameters, write its strategy README, add a small test suite around its entry/exit/sizing logic.

**Phase 4 — EOD data pipeline.** Daily job that downloads and saves prices for all target universes (the "end of each day, download and save" requirement).

**Phase 5 — IB paper trading.** Point `scans/live/` at an IB **paper** account, run the winner daily, confirm orders/fills/stops behave. Watch it for several weeks before any real capital.

**Phase 6 — Portfolio & risk tracking.** A dashboard (live artifact or notebook) showing value, open risk, P/L, and current positions, refreshed from the paper account.

Real money comes only after Phase 5 has run clean for a meaningful stretch — and then at small size, per your stated preference.

---

## 7. Immediate next steps (pick one and I'll start)

1. **Execute Phase 0 now** — write the root README, clean `.gitignore`, archive the legacy root, and walk you through the GitHub push.
2. **Start Phase 1** — build the unified, cash-constrained backtest harness and metrics layer so the bake-off becomes possible.
3. **Quick-win preview** — run the existing 5LC backtest as-is and produce its scorecard row, so you see the format before we standardise everything.

Risk-management note: this plan is about engineering and process, not a recommendation to trade any particular strategy or size. All backtest figures must be treated as unverified until they come out of the corrected harness, and paper trading is the gate before real capital.
