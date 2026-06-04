"""
Phase 2 — Scorecard Ranking

Reads the bake-off scorecard and ranks candidates on RISK-ADJUSTED return,
not raw CAGR. Per PROJECT_PLAN.md section 5, Calmar and max drawdown matter
more than headline return for deciding what you can stomach with real money.

Ranking rule (default 'balanced'):
    score = z(calmar) + z(sharpe) + z(sortino) - z(max_drawdown_magnitude)
where z() is a z-score across the rows being ranked, so each metric
contributes comparably regardless of scale. Higher score = better.

You can rank the whole file, or per (universe, period) cohort so you compare
like with like. Buy-and-hold benchmark rows are kept and flagged so you can
see which strategies actually clear the bar.

Usage:
    python rank_scorecard.py
    python rank_scorecard.py --scorecard results/scorecard.csv
    python rank_scorecard.py --by-cohort           # rank within each universe+period
    python rank_scorecard.py --metric calmar       # single-metric sort
    python rank_scorecard.py --period full --universe sp500
    python rank_scorecard.py --out results/scorecard_ranked.csv

Author: Trading System
Date: 2026-06-03
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


RANK_COLUMNS = [
    'rank', 'strategy', 'universe', 'period',
    'cagr', 'benchmark_cagr', 'alpha',
    'calmar', 'sharpe', 'sortino',
    'max_drawdown_pct', 'win_rate', 'profit_factor',
    'exposure_pct', 'turnover', 'total_trades', 'score',
]


def _z(series: pd.Series) -> pd.Series:
    """Z-score; returns zeros if the column has no spread."""
    s = pd.to_numeric(series, errors='coerce').fillna(0.0)
    std = s.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std


def composite_score(df: pd.DataFrame) -> pd.Series:
    """Balanced risk-adjusted composite (see module docstring)."""
    dd_mag = pd.to_numeric(df['max_drawdown_pct'], errors='coerce').abs()
    return (
        _z(df['calmar'])
        + _z(df['sharpe'])
        + _z(df['sortino'])
        - _z(dd_mag)
    )


def is_benchmark(df: pd.DataFrame) -> pd.Series:
    return df['strategy'].astype(str).str.contains('Buy & Hold', case=False, na=False)


def rank_group(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    df = df.copy()
    if metric == 'composite':
        df['score'] = composite_score(df)
        df = df.sort_values('score', ascending=False)
    else:
        ascending = metric in ('max_drawdown_pct',)  # less negative DD is "more"; handle below
        if metric == 'max_drawdown_pct':
            # smaller magnitude drawdown is better
            df['score'] = -pd.to_numeric(df[metric], errors='coerce').abs()
            df = df.sort_values('score', ascending=False)
        else:
            df['score'] = pd.to_numeric(df[metric], errors='coerce')
            df = df.sort_values('score', ascending=False)
    df.insert(0, 'rank', range(1, len(df) + 1))
    return df


def fmt(df: pd.DataFrame) -> str:
    cols = [c for c in RANK_COLUMNS if c in df.columns]
    view = df[cols].copy()
    for c in view.columns:
        if c not in ('rank', 'strategy', 'universe', 'period', 'total_trades'):
            view[c] = pd.to_numeric(view[c], errors='coerce').round(2)
    return view.to_string(index=False)


def main():
    parser = argparse.ArgumentParser(description='Rank bake-off candidates on risk-adjusted return')
    parser.add_argument('--scorecard', default='results/scorecard.csv')
    parser.add_argument('--metric', default='composite',
                        choices=['composite', 'calmar', 'sharpe', 'sortino',
                                 'cagr', 'alpha', 'max_drawdown_pct'],
                        help='Ranking key (default: composite risk-adjusted score)')
    parser.add_argument('--by-cohort', action='store_true',
                        help='Rank within each (universe, period) cohort')
    parser.add_argument('--universe', help='Filter to one universe before ranking')
    parser.add_argument('--period', help='Filter to one period before ranking')
    parser.add_argument('--no-benchmark', action='store_true',
                        help='Exclude buy-and-hold rows from the ranking')
    parser.add_argument('--out', default='results/scorecard_ranked.csv',
                        help='Write the ranked table to this CSV')
    args = parser.parse_args()

    path = Path(args.scorecard)
    if not path.exists():
        print(f"ERROR: scorecard not found: {path}")
        print("Run the bake-off first:  python run_bakeoff.py")
        return

    df = pd.read_csv(path)
    if df.empty:
        print("Scorecard is empty — nothing to rank.")
        return

    # De-duplicate: keep the latest run per (strategy, universe, period).
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp').drop_duplicates(
            subset=['strategy', 'universe', 'period'], keep='last')

    if args.universe:
        df = df[df['universe'] == args.universe]
    if args.period:
        df = df[df['period'] == args.period]
    if args.no_benchmark:
        df = df[~is_benchmark(df)]

    if df.empty:
        print("No rows after filtering.")
        return

    ranked_frames = []
    if args.by_cohort:
        for (u, p), grp in df.groupby(['universe', 'period']):
            r = rank_group(grp, args.metric)
            ranked_frames.append(r)
            print("\n" + "=" * 80)
            print(f"COHORT: universe={u}  period={p}   (ranked by {args.metric})")
            print("=" * 80)
            print(fmt(r))
    else:
        r = rank_group(df, args.metric)
        ranked_frames.append(r)
        print("\n" + "=" * 80)
        print(f"BAKE-OFF RANKING — all rows, by {args.metric}")
        print("=" * 80)
        print(fmt(r))

    ranked = pd.concat(ranked_frames, ignore_index=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = [c for c in RANK_COLUMNS if c in ranked.columns]
    ranked[cols].to_csv(out, index=False)
    print(f"\nRanked table written to {out}")

    # Headline winner (non-benchmark) for the all-rows view.
    if not args.by_cohort:
        non_bench = ranked[~is_benchmark(ranked)]
        if not non_bench.empty:
            w = non_bench.iloc[0]
            print(f"\nTop strategy: {w['strategy']}  ({w['universe']}/{w['period']})  "
                  f"Calmar {pd.to_numeric(w.get('calmar'), errors='coerce'):.2f}, "
                  f"Sharpe {pd.to_numeric(w.get('sharpe'), errors='coerce'):.2f}, "
                  f"MaxDD {pd.to_numeric(w.get('max_drawdown_pct'), errors='coerce'):.1f}%")
        print("\nReminder: ranking is decision support, not a recommendation. "
              "The winner advances to PAPER trading first.")


if __name__ == "__main__":
    main()
