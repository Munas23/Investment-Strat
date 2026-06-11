# Investment Strategy Backtest — Progress Log

*Owner: Ash. Last updated: 4 June 2026.*

---

## Phase 0 — Repo Cleanup *(done)*

- Normalised line endings; added `.gitattributes`
- Added `requirements.txt` and top-level `README.md`
- Reorganised folder structure to eliminate duplicated scripts

---

## Phase 1 — Unified Backtest Harness *(committed: `81556a6`)*

**Location:** `scans/backtesting/`

Fixed core correctness issues in the engine:

- Mark-to-market equity curve (was using entry price, not daily close)
- Hard cash constraint — no negative cash / over-allocation
- Max drawdown calculated vs running peak (not just start)
- Added metrics: Calmar ratio, exposure %, turnover

Added the scorecard pipeline (`results/scorecard.csv`) so every run appends a comparable row.
Offline test suite at `scans/backtesting/tests/test_harness_offline.py` — all checks pass without network access.

---

## Phase 2 — Bake-Off Scaffolding + Real Strategy Families *(committed: `0878061`)*

### New files

| File | Purpose |
|---|---|
| `scans/backtesting/run_bakeoff.py` | Orchestrates the full candidate × universe × period matrix into one scorecard |
| `scans/backtesting/rank_scorecard.py` | Ranks results by composite risk-adjusted score: `z(Calmar) + z(Sharpe) + z(Sortino) − z(\|maxDD\|)`, with `--by-cohort` option |
| `backtesting/data/build_universes.py` | Fetches current index constituent lists; re-run after index rebalances |

### Expanded universe CSVs (`backtesting/data/`)

`sp500_symbols.csv`, `russell1000_symbols.csv`, `nasdaq100_symbols.csv`, `asx300_symbols.csv`, `ftse100_symbols.csv` — all expanded from stub size to full lists.

### Strategy families wired (systems 6–8)

The bake-off previously compared 5 sizing presets (systems 1–5). Three real strategy families have now been added alongside them.

| Slug | System | Entry Signal | Stops | Max Positions |
|---|---|---|---|---|
| `vcp` | 6 | Stage 2 + ATR contraction + within 10% of 52w high + volume drying in base then expanding on entry | ATR-based | 8 |
| `conviction` | 7 | Points composite: breakout (30) + volume surge (25) + momentum (25) + trend (20) → levels 1–5. No fundamental gate. | ATR-based | 15 |
| `5lc` | 8 | Same points engine as Conviction, gated to within 25% of 52w high. Fundamentals filtered upstream by quarterly screen. | 7% fixed | 12 |

### Files changed

- `scans/backtesting/utils/technical_scanner.py` — `_score_vcp`, `_score_conviction`, `_score_5lc` added; all 8 registered in `_SCORERS`
- `scans/backtesting/run_backtest.py` — system configs 6/7/8 added; `vcp`/`conviction`/`5lc` added to `STRATEGY_SLUGS`; `--system` and `--all` updated to cover 1–8
- `scans/backtesting/run_bakeoff.py` — `DEFAULT_STRATEGIES` auto-picks up all 8 slugs

Dry-run confirmed: 8 strategies × 3 US universes × 1 period = 24 runs print correctly.

---

## Phase 2 — Bake-Off Results *(completed: 4 June 2026)*

**120 runs, zero failures.** Full results in `scans/backtesting/results/BAKEOFF_RESULTS.md`.

### Engine fixes applied before running

- Exit methods (`scaled`, `time_trail`, `let_run`, `adaptive`) were config keys with no engine implementation — wired up and differentiated before the run
- `fetch_benchmark_data` missing tz-strip for non-SPY benchmarks (IWB, QQQ, ^AXJO) — fixed

### Winners by universe (full period, risk-adjusted composite)

| Universe | Winner | CAGR | Calmar | Sharpe | Max DD |
|---|---|---|---|---|---|
| sp500 | **Hybrid Balanced** | 14.5% | 1.69 | 1.06 | -8.6% |
| russell1000 | **Qullamaggie** | 15.5% | 2.10 | 1.37 | -7.4% |
| nasdaq100 | **Qullamaggie** | 7.9% | 1.64 | 0.89 | -4.8% |
| asx300 | **Minervini** (marginal) | 5.1% | 0.56 | 0.29 | -9.0% |

### Key findings

- **Qullamaggie** is the strongest all-weather US system — best bear-market alpha on every universe, lowest drawdowns, and #1 full-period on russell1000 + nasdaq100. The `time_trail` exit suits it well (high win rates 53–56%).
- **Hybrid** wins sp500 with the most consistent cross-period profile. The `adaptive` exit (scaled in bull, let_run in bear) contributes.
- **VCP** is starved of signals — too few trades to be reliable. The ATR contraction + proximity filters need loosening.
- **High Conviction Only** carries the biggest drawdowns (-14% to -24%) with no return premium. Eliminated.
- **ASX 300** needs recalibration — only 2–8 qualifying stocks per quarter with current filters. Qullamaggie completely fails on AU. Hold AU paper trading until filters are loosened.
- **5LC vs Conviction:** 5LC edges on nasdaq100, Conviction edges on sp500 — no universal winner from the fundamental gate.

### Advancement to paper trading

| Universe | Strategy |
|---|---|
| russell1000 | Qullamaggie (`time_trail`, ATR stops, max 15 positions) |
| sp500 | Hybrid (`adaptive`, ATR+cap stops, max 12 positions) |
| nasdaq100 | Qullamaggie (same config) |
| asx300 | Hold — recalibrate filters first |

---

## What's Next

---

## Phase 3 / 3a / 4 — Hardening, Recalibration, Pipeline *(5 June 2026, uncommitted)*

### Phase 3 — Harden the winners
- `scans/backtesting/STRATEGY_SPEC.md` — single source of truth locking the
  advancement parameters: Qullamaggie (system 3) for russell1000 + nasdaq100,
  Hybrid (system 4) for sp500, ASX held. Includes the bake-off numbers and two
  pre-paper-trading actions: confirm Qullamaggie's stop is ATR (config says
  `pattern`), and reconcile the live scanner's 55% fundamental gate with the
  harness `min_fundamental`. The live scanner currently implements 5LC, not the
  advancement winners — resolving that is Ash's call and gates Phase 5.

### Phase 3a — ASX + VCP recalibration *(validated offline)*
- `utils/historical_screener.py` — market-aware screening: `MARKET_THRESHOLDS`
  (us/au/uk) + `detect_market()`; AU profile is strictly looser on every axis so
  the ASX stops qualifying only 2-8 names/quarter. Wired through `run_backtest.py`
  (asx300→au, ftse100→uk).
- `utils/technical_scanner.py` — VCP (system 6) gate loosened: proximity 10%→15%,
  ATR contraction 0.85→0.92, base-volume contraction 0.85→0.92.
- `tests/test_recalibration_offline.py` — 4 new offline tests (all 8 pass).

### Phase 4 — EOD data pipeline *(scaffold ready, runs on Ash's machine)*
- `eod_pipeline.py` — idempotent, resumable daily OHLCV downloader → per-symbol
  parquet store + manifest. `EOD_PIPELINE.md` documents layout, cadence, and the
  open items (adjusted-vs-raw, delistings, survivorship, scanner integration).

### To commit (on Ash's machine — sandbox git is locked)
```bash
cd Investment-Strat-clean
rm -f .git/index.lock
git add scans/backtesting/backtest_engine.py scans/backtesting/run_backtest.py \
        scans/backtesting/utils/historical_screener.py \
        scans/backtesting/utils/technical_scanner.py \
        scans/backtesting/tests/test_recalibration_offline.py \
        scans/backtesting/STRATEGY_SPEC.md scans/backtesting/EOD_PIPELINE.md \
        scans/backtesting/eod_pipeline.py .gitignore PROGRESS.md
git commit -m "Phase 3/3a/4: strategy spec, market-aware + VCP recalibration, EOD pipeline"
git push
```
Then re-run the recalibrated bake-off (`python run_bakeoff.py --markets au` and
`--markets us`) and seed the store (`python eod_pipeline.py --all --full`).

---

## Remaining Phases (from PROJECT_PLAN.md)

| Phase | Work | Status |
|---|---|---|
| Phase 3 | Harden the winner — lock parameters, write strategy README, add test suite | Not started |
| Phase 3a | ASX recalibration — loosen conviction/fundamental filters, re-run AU bake-off | Not started |
| Phase 4 | EOD data pipeline — daily job to download and save prices for all universes | Not started |
| Phase 5 | IB paper trading — Qullamaggie (russell1000) + Hybrid (sp500), confirm fills | Not started |
| Phase 6 | Portfolio & risk tracking dashboard | Not started |
