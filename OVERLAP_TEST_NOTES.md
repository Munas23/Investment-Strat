# Screen Overlap Test — Notes & How to Run

*Prepared for Ash. Date: 5 June 2026.*

## What was delivered

1. **`FUNDAMENTAL_SCREENS_REVIEW.md`** — review of every fundamental screen in the repo and the gap between the documented 150-point 5LC engine and the simplified filter the backtest actually used.
2. **`scans/backtesting/compare_screen_overlap.py`** — tool to quantify how differently the two gates pick stocks.
3. **`scans/backtesting/results/BAKEOFF_RESULTS.md`** — added a flagged caveat under Setup noting that `5lc`'s backtest gate was the simplified filter, not the full screen.

## What the overlap script does

Runs both gates over a universe and reports where they agree/disagree:

- **FULL** — the 150-pt `FundamentalScreener` (pass ≥ 90/150).
- **FILTER** — the simplified gate from `historical_screener._screen_as_of_date` (DDV >$20M, vol >500K, price >$5, 3-month momentum >20%, market cap >$300M, revenue YoY >10%, gross margin >20%).

Output: a confusion matrix, the size of each pass-list, the Jaccard overlap, and — the key number — the share of filter passes that the full screen would **reject**.

## How to run (on a machine with Yahoo access — the sandbox blocks yfinance)

```bash
# quick sanity run
python scans/backtesting/compare_screen_overlap.py --universe sp500 --limit 50

# full run, save per-symbol results
python scans/backtesting/compare_screen_overlap.py --universe sp500 --out results/overlap_sp500.csv

# other universes
python scans/backtesting/compare_screen_overlap.py --universe nasdaq100
python scans/backtesting/compare_screen_overlap.py --universe russell1000
```

The headline metric to watch: **"filter passes that FAIL the full screen"** — high values mean the backtest's fundamental gate is much looser than the documented strategy.

## Caveat

The script compares on **current** fundamentals, not point-in-time. It measures how differently the two gates pick *today* — a proxy for the historical divergence, not an exact replay of the 2020–2024 backtest. A true point-in-time comparison would require historical as-of fundamental data, which Yahoo does not cleanly provide.

## Next steps (open)

- Run the overlap test and record the numbers here.
- Decide intent: accept the simplified filter as the real strategy, or invest in point-in-time fundamentals so the full 5LC screen can be backtested.
- Consolidate the duplicate Minervini screen files into one source-of-truth module.
- Commit the three deliverable files (currently unstaged).
