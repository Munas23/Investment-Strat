# Fundamental Screens — Review & Backtest Gate Analysis

*Prepared for Ash. Date: 5 June 2026.*

## Summary

The repo contains **seven distinct fundamental-screen files** (plus duplicates) built on the same Minervini / O'Neil growth philosophy, branded as a 150-point "5LC" scoring engine that passes stocks at ≥90/150 (60%).

**The Phase-2 bake-off did not use any of them.** The backtest used a separate, much simpler point-in-time filter inside `scans/backtesting/utils/historical_screener.py`. This creates a gap: the test results reward a far looser fundamental gate than the project's documented live screening logic.

---

## The screen files

| File | Market | Role | Notes |
|---|---|---|---|
| `scans/fundamentals/fundamental_screener.py` | US | **Canonical 150-pt 5LC engine** | The one the README documents. 5 weighted buckets (Market 20, Profitability 35, Growth 50, Financial Strength 25, Institutional 20); pass ≥90/150. |
| `strategies/minervini/5LC/minervini_fundamentals.py` | US | Strict Minervini screen | EPS 25%+, ROE 15%+, D/E <0.3, vol >500K, price >$15. |
| `strategies/minervini/Complete/minervini_fundamentals.py` | US | **Identical copy** of the 5LC file | Byte-for-byte same md5 — a duplicate. |
| `testing/minervini_fundamentals.py` | US | Near-identical copy | Minor edits vs the above (different md5); lives in `testing/`. |
| `strategies/minervini/ASX300/minervini_fundamentals.py` | ASX | AU-adapted Minervini | AUD caps, vol >100K, price >$5. |
| `strategies/conviction-asx300/Standard/quality_fundamentals.py` | ASX | AU "quality-first" variant | Essentially the ASX Minervini screen relabeled; differs slightly. |
| `testing/enhanced_growth_screener.py` | US | Richer growth engine | Multi-timeframe sales-growth (Q/1y/3y), acceleration detection, margin quality. Looser thresholds (15% rev, 10% quarterly). Not wired into the bake-off. |
| `scanners/conviction-daily/debug_fundamentals.py` | — | **Not a screen** | 45-line debug harness that prints one stock's score breakdown via the 5lc daily scanner. |

Duplicate note: the two US Minervini files (`5LC`, `Complete`) are identical; the `testing/` copy diverges slightly. The two ASX files are close but not identical. Consolidating these into one source-of-truth module would remove drift risk.

---

## What the backtest actually used

`scans/backtesting/utils/historical_screener.py`, method `_screen_as_of_date()`. It imports **none** of the 150-point engines (verified: zero imports of them anywhere under `scans/backtesting/`). It implements its own inline filter, designed for point-in-time correctness (no lookahead bias), applied quarterly:

- Liquidity: dollar volume >$20M, volume >500K shares, price >$5
- Momentum: 3-month gain >20%
- Market cap >$300M
- Revenue growth >10% YoY (only quarters reported ≥45 days before the test date)
- Gross margin >20%

That is the entire "fundamental gate" behind the `5lc` strategy in the bake-off.

---

## The strictness gap

| Criterion | Full 150-pt 5LC (live) | Backtest filter | Divergence |
|---|---|---|---|
| Revenue growth | 20% to pass, 25–30% for full points | **10% YoY** | Backtest accepts half the growth |
| Earnings / EPS growth | 25% to pass, 40%+ excellent | **Not checked** | Dropped entirely |
| ROE | 15%+ | **Not checked** | Dropped |
| Debt-to-equity | ≤0.50 pass, ≤0.20 excellent | **Not checked** | Dropped |
| Profit margin | scored | gross margin >20% only | Partial |
| Institutional ownership | 20 pts (40–80%) | **Not checked** | Dropped |
| Pass mechanism | composite ≥90/150 (60%) | all-or-nothing hard filters | Different shape entirely |

The backtest gate checks roughly two of the five scoring buckets, at relaxed thresholds, and as binary cut-offs rather than a weighted composite. A stock that scores 50/150 on the real screen (a clear fail) could still pass the backtest filter if it clears the liquidity, 10% revenue, and 20% margin bars.

**Implication:** the bake-off's reported edge for the fundamentally-gated `5lc` system reflects this loose filter, not the documented 5LC methodology. Whatever advantage (or lack of one) the real fundamental screen provides has not been tested historically.

---

## Why the gap exists (likely)

Point-in-time fundamentals are hard to reconstruct from Yahoo — earnings-revision history, institutional-ownership history, and historical ROE aren't cleanly available as-of past dates. The simplified filter uses only what can be sliced safely from cached quarterly income statements and prices. That's a reasonable engineering compromise, but it should be stated explicitly in the results so the backtest isn't read as validating the full screen.

---

## Recommendations

1. **Label the gap in `BAKEOFF_RESULTS.md`** — note that `5lc`'s fundamental gate in testing is the simplified filter, not the 150-pt engine.
2. **Consolidate duplicates** — collapse the 3–4 near-identical Minervini files into one module to stop silent drift.
3. **Decide the intent** — either (a) accept the simplified filter as the real strategy and retire the 150-pt screen as aspirational, or (b) invest in point-in-time fundamental data so the full screen can actually be backtested.
4. **Optional overlap test** — on current (non-historical) data, run both the full 5LC screen and the backtest filter over the S&P 500 and measure pass-list overlap, to quantify how different the two gates really are.
