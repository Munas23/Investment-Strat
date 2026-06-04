"""
Phase 2 — Strategy Bake-Off Orchestrator

Runs every candidate strategy through the unified harness over the same
universes and windows, accumulating one comparable row per run into a single
scorecard. After it finishes, rank the field with:

    python rank_scorecard.py

Each (strategy, universe, period) combination is run independently so a single
failure (e.g. a missing universe file or a data-fetch error) is logged and
skipped rather than aborting the whole bake-off.

Usage:
    python run_bakeoff.py                      # full matrix (all candidates x markets x windows)
    python run_bakeoff.py --markets us         # US universes only
    python run_bakeoff.py --markets au         # ASX only
    python run_bakeoff.py --periods full       # one window only
    python run_bakeoff.py --strategies minervini turtle
    python run_bakeoff.py --scorecard results/scorecard.csv
    python run_bakeoff.py --dry-run            # print the matrix, run nothing

NOTE: real runs require reachable market data (Yahoo Finance). The Cowork
sandbox blocks Yahoo, so run this on a machine with network access to Yahoo.

Author: Trading System
Date: 2026-06-03
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from run_backtest import (
    SYSTEMS,
    STRATEGY_SLUGS,
    UNIVERSES,
    PERIODS,
    resolve_period,
    load_universe_symbols,
    run_simple_backtest,
)
from backtest_engine import BacktestEngine


# Default candidate field: all registered strategies (presets + real families).
# Slugs map to system numbers via STRATEGY_SLUGS in run_backtest.py.
# Presets (1-5): minervini, turtle, qullamaggie, hybrid, highconviction
# Real families (6-8): vcp, conviction, 5lc
DEFAULT_STRATEGIES = list(STRATEGY_SLUGS)

# Market groupings. The plan asks for both US and AU coverage.
MARKET_UNIVERSES = {
    'us': ['sp500', 'russell1000', 'nasdaq100'],
    'au': ['asx300'],
    'uk': ['ftse100'],
}

# Default windows: full period + the 2022 bear stress window + 2021 strong bull.
DEFAULT_PERIODS = list(PERIODS)                    # full, bear2022, bull2021


def build_matrix(strategies, universes, periods):
    """Cartesian product of the chosen candidates, universes and windows."""
    return [(s, u, p) for s in strategies for u in universes for p in periods]


def resolve_universes(markets):
    """Expand a list of market keys (us/au/uk) into universe names."""
    universes = []
    for m in markets:
        if m not in MARKET_UNIVERSES:
            print(f"WARNING: unknown market '{m}'. Known: {list(MARKET_UNIVERSES)}")
            continue
        universes.extend(MARKET_UNIVERSES[m])
    # de-dup while preserving order
    seen, ordered = set(), []
    for u in universes:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


def benchmark_row_once(universe, period, scorecard_path):
    """
    Emit a buy-and-hold benchmark scorecard row for a universe/period so the
    bar-to-beat appears in the ranking alongside the strategies. Best-effort:
    skipped quietly if benchmark data can't be fetched.
    """
    try:
        start, end = resolve_period(period)
        bench = UNIVERSES.get(universe, {}).get('benchmark', 'SPY')
        engine = BacktestEngine(account_size=2_000_000, start_date=start, end_date=end)
        _, bench_cagr = engine.calculate_benchmark_return(bench)
        # A benchmark has no trades; emit a row with CAGR only via append_scorecard
        # using a zeroed metrics object.
        metrics = engine.calculate_metrics()   # empty -> zeros
        metrics.cagr = round(bench_cagr, 2)
        engine.append_scorecard(
            strategy=f'Buy & Hold ({bench})',
            universe=universe,
            period=period,
            metrics=metrics,
            benchmark_cagr=bench_cagr,
            scorecard_path=scorecard_path,
        )
        return True
    except Exception as e:
        print(f"  (benchmark for {universe}/{period} skipped: {e})")
        return False


def main():
    parser = argparse.ArgumentParser(description='Phase 2 strategy bake-off runner')
    parser.add_argument('--strategies', nargs='+', default=DEFAULT_STRATEGIES,
                        choices=list(STRATEGY_SLUGS),
                        help='Candidate strategies (default: all presets)')
    parser.add_argument('--markets', nargs='+', default=['us', 'au'],
                        choices=list(MARKET_UNIVERSES),
                        help='Market groups to cover (default: us au)')
    parser.add_argument('--universes', nargs='+', default=None,
                        choices=['broad'] + list(UNIVERSES),
                        help='Explicit universe list (overrides --markets)')
    parser.add_argument('--periods', nargs='+', default=DEFAULT_PERIODS,
                        help="Windows (names from PERIODS or 'START:END')")
    parser.add_argument('--scorecard', default='results/scorecard.csv',
                        help='Scorecard CSV to append to')
    parser.add_argument('--no-benchmark', action='store_true',
                        help='Skip emitting buy-and-hold benchmark rows')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print the run matrix and exit without running')
    args = parser.parse_args()

    universes = args.universes if args.universes else resolve_universes(args.markets)
    if not universes:
        print("ERROR: no universes resolved. Check --markets / --universes.")
        return

    matrix = build_matrix(args.strategies, universes, args.periods)

    print("=" * 80)
    print("PHASE 2 BAKE-OFF")
    print("=" * 80)
    print(f"Strategies : {', '.join(args.strategies)}")
    print(f"Universes  : {', '.join(universes)}")
    print(f"Periods    : {', '.join(args.periods)}")
    print(f"Scorecard  : {args.scorecard}")
    print(f"Total runs : {len(matrix)}"
          f"{' (+ benchmarks)' if not args.no_benchmark else ''}")
    print("=" * 80)

    if args.dry_run:
        for i, (s, u, p) in enumerate(matrix, 1):
            print(f"  {i:>3}. {s:<14} {u:<12} {p}")
        return

    # Benchmark rows: once per (universe, period).
    if not args.no_benchmark:
        print("\nEmitting buy-and-hold benchmark rows...")
        for u in universes:
            for p in args.periods:
                benchmark_row_once(u, p, args.scorecard)

    succeeded, failed = [], []
    t0 = time.time()

    for i, (slug, universe, period) in enumerate(matrix, 1):
        sys_num = STRATEGY_SLUGS[slug]
        config = SYSTEMS[sys_num]
        print("\n" + "#" * 80)
        print(f"# RUN {i}/{len(matrix)}: {slug} | {universe} | {period}")
        print("#" * 80)
        try:
            start, end = resolve_period(period)
            period_label = period if period in PERIODS else 'custom'
            benchmark_symbol = UNIVERSES.get(universe, {}).get('benchmark', 'SPY')

            symbols = load_universe_symbols(universe)
            if not symbols:
                raise RuntimeError(f"no symbols loaded for universe '{universe}'")

            run_simple_backtest(
                config, symbols, start, end,
                universe_label=universe,
                period_label=period_label,
                benchmark_symbol=benchmark_symbol,
                scorecard_path=args.scorecard,
            )
            succeeded.append((slug, universe, period))
        except Exception as e:
            print(f"\n!! RUN FAILED: {slug}/{universe}/{period}: {e}")
            traceback.print_exc()
            failed.append((slug, universe, period, str(e)))

    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print("BAKE-OFF COMPLETE")
    print("=" * 80)
    print(f"Succeeded: {len(succeeded)}/{len(matrix)}   Failed: {len(failed)}")
    print(f"Elapsed:   {elapsed/60:.1f} min")
    if failed:
        print("\nFailures:")
        for slug, u, p, err in failed:
            print(f"  - {slug}/{u}/{p}: {err}")
    print(f"\nScorecard: {args.scorecard}")
    print("Rank the field with:  python rank_scorecard.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
