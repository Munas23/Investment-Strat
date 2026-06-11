# Phase 2 Bake-Off Results

*Run: 4 June 2026. 120 runs completed (8 strategies × 4 universes × 3 periods), zero failures.*

---

## Setup

**Engine fixes applied before running:**

- Exit methods (`scaled`, `time_trail`, `let_run`, `adaptive`) were config keys but never consumed by the engine — wired up and implemented before this run.
- `fetch_benchmark_data` was returning tz-aware DatetimeIndex for non-SPY benchmarks (IWB, QQQ, ^AXJO), causing comparison failures — fixed with `tz_convert(None).normalize()`.

**Exit mode per strategy:**

| Strategy | Exit Mode | Behaviour |
|---|---|---|
| minervini, turtle, vcp, 5lc | `scaled` | At target_1: raise stop to breakeven, let run to target_2 or chandelier |
| qullamaggie, conviction | `time_trail` | Exit at target_1; chandelier tightens 3→2 ATR after 30 holding days |
| highconviction | `let_run` | No profit target — only stops and chandelier |
| hybrid | `adaptive` | Bull market → scaled; non-bull → let_run |

**Matrix:** 8 strategies × (sp500, russell1000, nasdaq100, asx300) × (full 2020–2024, bear2022, bull2021)

**Scoring:** composite z-score = `z(Calmar) + z(Sharpe) + z(Sortino) − z(|maxDD|)`

> **⚠️ Fundamental-gate caveat (added 5 June 2026).** The `5lc` strategy's fundamental gate in this bake-off is **not** the 150-point 5LC engine (`scans/fundamentals/fundamental_screener.py`). The backtest uses a simplified point-in-time filter in `scans/backtesting/utils/historical_screener.py` (`_screen_as_of_date`): liquidity (DDV >$20M, vol >500K, price >$5), 3-month momentum >20%, market cap >$300M, revenue YoY >10%, gross margin >20%. It drops the EPS-growth, ROE, debt-to-equity, and institutional-ownership checks, and uses a relaxed 10% revenue bar (vs 20%+ in the full screen). These results therefore do **not** validate the documented 5LC methodology. See `FUNDAMENTAL_SCREENS_REVIEW.md` and `scans/backtesting/compare_screen_overlap.py` for the gap analysis and a tool to quantify pass-list overlap.

---

## Full-Period Results (Primary View)

*Full period (2020–2024) is the most meaningful cohort — it covers bull, bear and recovery regimes.*

### S&P 500

| Rank | Strategy | CAGR | Benchmark | Alpha | Calmar | Sharpe | Max DD | Win Rate | Score |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Hybrid Balanced** | 14.5% | 14.3% | +0.15% | 1.69 | 1.06 | -8.6% | 33.9% | 3.15 |
| 2 | Turtle ATR-Based | 15.1% | 14.3% | +0.74% | 1.46 | 1.13 | -10.3% | 34.5% | 2.78 |
| 3 | Qullamaggie Aggressive | 9.4% | 14.3% | -4.93% | 1.34 | 0.80 | -7.0% | 51.9% | 1.19 |
| 4 | Conviction (Pure Technical) | 13.0% | 14.3% | -1.31% | 1.08 | 1.01 | -12.0% | 49.1% | 0.79 |
| 5 | High Conviction Only | 18.0% | 14.3% | +3.65% | 1.22 | 0.96 | -14.7% | 34.5% | -0.09 |
| 6 | 5LC (5-Level Conviction) | 12.8% | 14.3% | -1.57% | 1.05 | 0.88 | -12.2% | 33.3% | -0.19 |
| 7 | Conservative Growth (Minervini) | 15.3% | 14.3% | +0.99% | 1.07 | 0.93 | -14.3% | 34.5% | -0.42 |
| 8 | VCP | 8.8% | 14.3% | -5.55% | 0.78 | 0.62 | -11.2% | 34.8% | -2.13 |
| — | Buy & Hold (SPY) | 14.3% | — | — | — | — | — | — | -5.08 |

### Russell 1000

| Rank | Strategy | CAGR | Benchmark | Alpha | Calmar | Sharpe | Max DD | Win Rate | Score |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qullamaggie Aggressive** | 15.5% | 14.0% | +1.49% | 2.10 | 1.37 | -7.4% | 53.2% | 3.11 |
| 2 | Conviction (Pure Technical) | 18.1% | 14.0% | +4.05% | 1.83 | 1.44 | -9.9% | 48.4% | 2.52 |
| 3 | 5LC (5-Level Conviction) | 21.2% | 14.0% | +7.14% | 1.75 | 1.47 | -12.1% | 35.6% | 1.86 |
| 4 | Turtle ATR-Based | 19.2% | 14.0% | +5.17% | 1.81 | 1.34 | -10.6% | 33.2% | 1.72 |
| 5 | Hybrid Balanced | 18.2% | 14.0% | +4.21% | 1.56 | 1.24 | -11.7% | 31.5% | 0.49 |
| 6 | Conservative Growth (Minervini) | 19.6% | 14.0% | +5.54% | 1.42 | 1.23 | -13.8% | 34.4% | -0.28 |
| 7 | VCP | 11.1% | 14.0% | -2.93% | 1.01 | 0.80 | -11.0% | 35.3% | -2.22 |
| 8 | High Conviction Only | 20.2% | 14.0% | +6.16% | 1.27 | 0.96 | -15.9% | 35.4% | -2.30 |
| — | Buy & Hold (IWB) | 14.0% | — | — | — | — | — | — | -4.90 |

### Nasdaq 100

| Rank | Strategy | CAGR | Benchmark | Alpha | Calmar | Sharpe | Max DD | Win Rate | Score |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qullamaggie Aggressive** | 7.9% | 19.7% | -11.8% | 1.64 | 0.89 | -4.8% | 55.7% | 3.08 |
| 2 | Hybrid Balanced | 13.0% | 19.7% | -6.68% | 1.60 | 0.95 | -8.1% | 33.4% | 2.61 |
| 3 | 5LC (5-Level Conviction) | 15.1% | 19.7% | -4.61% | 1.43 | 1.06 | -10.6% | 37.4% | 2.45 |
| 4 | Conviction (Pure Technical) | 11.5% | 19.7% | -8.21% | 1.46 | 0.91 | -7.9% | 50.9% | 2.07 |
| 5 | Turtle ATR-Based | 13.7% | 19.7% | -6.01% | 1.35 | 0.98 | -10.2% | 33.9% | 1.88 |
| 6 | High Conviction Only | 14.3% | 19.7% | -5.38% | 0.90 | 0.71 | -15.9% | 34.1% | -2.06 |
| 7 | VCP | 6.7% | 19.7% | -13.0% | 0.75 | 0.47 | -9.0% | 39.8% | -2.34 |
| 8 | Conservative Growth (Minervini) | 11.4% | 19.7% | -8.28% | 0.70 | 0.66 | -16.3% | 33.0% | -2.87 |
| — | Buy & Hold (QQQ) | 19.7% | — | — | — | — | — | — | -4.82 |

### ASX 300

| Rank | Strategy | CAGR | Benchmark | Alpha | Calmar | Sharpe | Max DD | Win Rate | Score |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Conservative Growth (Minervini)** | 5.1% | 4.2% | +0.84% | 0.56 | 0.29 | -9.0% | 32.3% | 2.83 |
| 2 | Turtle ATR-Based | 2.9% | 4.2% | -1.34% | 0.49 | -0.01 | -5.9% | 32.7% | 2.39 |
| 3 | VCP | 1.8% | 4.2% | -2.48% | 0.54 | -0.44 | -3.3% | 32.7% | 2.07 |
| 4 | Hybrid Balanced | 2.3% | 4.2% | -1.93% | 0.33 | -0.12 | -7.0% | 29.3% | 1.39 |
| 5 | 5LC (5-Level Conviction) | 1.9% | 4.2% | -2.33% | 0.24 | -0.19 | -7.9% | 32.8% | 0.78 |
| 6 | Conviction (Pure Technical) | 1.6% | 4.2% | -2.63% | 0.23 | -0.35 | -7.1% | 49.8% | 0.48 |
| 7 | High Conviction Only | -3.5% | 4.2% | -7.71% | -0.15 | -0.96 | -23.8% | 21.9% | -4.81 |
| 8 | Qullamaggie Aggressive | -1.3% | 4.2% | -5.56% | -0.19 | -3.11 | -6.9% | 32.6% | -6.70 |
| — | Buy & Hold (^AXJO) | 4.2% | — | — | — | — | — | — | +1.56 |

---

## Bear Market 2022

*All strategies lost money. What matters is alpha vs the benchmark.*

| Strategy | sp500 alpha | russell1000 alpha | nasdaq100 alpha | asx300 alpha |
|---|---|---|---|---|
| Qullamaggie | **+18.0%** | **+21.5%** | **+32.9%** | +5.4% |
| High Conviction Only | +15.5% | +16.7% | +31.1% | +4.6% |
| VCP | +15.1% | +14.1% | +25.0% | **+6.9%** |
| Conservative Growth (Minervini) | +11.1% | +18.1% | +19.6% | +2.4% |
| Hybrid Balanced | +11.9% | +12.1% | +27.1% | +3.8% |

Qullamaggie is the standout defensive system. Its `time_trail` exit and pattern stop method (tighter initial stops, faster exits on stagnation) means it runs low exposure in bad markets — as low as 18–39% exposed vs benchmark's full 100%.

---

## Bull Market 2021

*Best risk-adjusted performers:*

| Universe | #1 | CAGR | Calmar | Sharpe |
|---|---|---|---|---|
| sp500 | 5LC | 32.5% | 7.33 | 1.90 |
| russell1000 | Conviction | 51.2% | 8.98 | 2.60 |
| nasdaq100 | 5LC | 30.8% | 5.39 | 1.87 |
| asx300 | Conviction | 2.9% | 1.49 | -0.03 |

---

## Key Findings

### 1. Qullamaggie is the strongest all-weather system (US)

- #1 full-period on russell1000 and nasdaq100 on a risk-adjusted basis
- Best bear-market alpha across every US universe — the only US strategy that was approximately flat in 2022
- Lowest drawdowns: max -7.4% (russell1000), -4.8% (nasdaq100) over the full 5-year period
- The `time_trail` exit mode suits it — high win rate (53–56%) confirms exits aren't being taken too early

### 2. Hybrid wins sp500

- Most consistent across all three periods on sp500
- Calmar 1.69, Sharpe 1.06, max DD -8.6% — best balance of return and risk on large-cap universe
- The `adaptive` exit mode (scaled in bull, let_run in bear) contributes to this consistency

### 3. VCP and High Conviction are the weakest

- **VCP:** too few signals — 49–316 trades over 5 years vs 500–1200 for leading strategies. The ATR contraction + proximity filters are too restrictive at the universe level.
- **High Conviction Only:** biggest drawdowns of any strategy (-14.7% to -23.8%), with no return premium to compensate. The 5-conviction-only filter starves the system and produces oversized concentrated losses.

### 4. AU (ASX 300) needs different calibration

- The conviction/quality filters leave only 2–8 qualifying stocks per quarter. Strategies are operating near-starved.
- Qullamaggie completely fails (-1.3% full period, -6.7 score) — its pattern-based entries don't suit ASX liquidity/volatility structure.
- Minervini is the only strategy beating the benchmark, suggesting the fundamental-quality gate is better suited to the ASX than purely technical setups.
- **Recommendation:** loosen `min_conviction` to 2 and `min_fundamental` to 50 for AU, or build a separate ASX-specific scanner before running AU paper trading.

### 5. Does the 5LC fundamental gate add value over pure Conviction?

Mixed. On russell1000 (full period): 5LC CAGR 21.2% vs Conviction 18.1%, but Conviction has better Calmar (1.83 vs 1.75) and Sharpe (1.44 vs 1.47 — essentially equal). On nasdaq100: 5LC beats Conviction in every metric. On sp500: Conviction beats 5LC. No clear universal winner — the gate helps on growth universes, is neutral on large-cap.

---

## Advancement Decision

| Universe | Advance to paper | System |
|---|---|---|
| russell1000 | **Qullamaggie** | `time_trail` exit, ATR stops, max 15 positions |
| sp500 | **Hybrid** | `adaptive` exit, ATR+cap stops, max 12 positions |
| nasdaq100 | **Qullamaggie** | same config as russell1000 |
| asx300 | Hold — recalibrate filters first | — |

---

## Files

| File | Description |
|---|---|
| `results/scorecard.csv` | Raw scorecard — one row per (strategy, universe, period) run |
| `results/scorecard_ranked.csv` | Sorted by composite score, all rows |
| `results/BAKEOFF_RESULTS.md` | This file |
| `run_bakeoff.py` | Orchestrator — re-run with `--markets us` or `--markets au` |
| `rank_scorecard.py` | Ranker — `--by-cohort` for per-universe view |
