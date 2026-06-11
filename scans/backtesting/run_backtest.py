"""
Master Backtesting Runner

Runs backtests for all 5 trading systems and generates comparison reports.

Usage:
    python run_backtest.py --system 1        # Run single system
    python run_backtest.py --all             # Run all systems
    python run_backtest.py --compare         # Compare results

Author: Trading System
Date: 2026-01-02
"""

import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backtest_engine import BacktestEngine, PerformanceMetrics
from utils.historical_screener import HistoricalScreener
from utils.technical_scanner import scan_universe, get_market_health
import pandas as pd
import json
from datetime import datetime
from typing import List


# System configurations from BACKTEST_SYSTEMS_PLAN.md
SYSTEMS = {
    1: {
        'name': 'Conservative Growth (Minervini)',
        'system_id': 1,
        'base_risk': 1.0,
        'conviction_multipliers': {5: 1.25, 4: 1.0, 3: 0.75},
        'min_conviction': 4,
        'max_positions': 10,
        'max_total_risk': 10.0,
        'stop_method': 'percentage',
        'stop_levels': {5: 3, 4: 5, 3: 7},
        'exit_method': 'scaled',
        'min_fundamental': 75,
    },
    2: {
        'name': 'Turtle ATR-Based',
        'system_id': 2,
        'base_risk': 1.5,
        'conviction_multipliers': {5: 1.5, 4: 1.25, 3: 1.0},
        'min_conviction': 3,
        'max_positions': 12,
        'max_total_risk': 20.0,
        'stop_method': 'atr',
        'atr_multipliers': {5: 1.5, 4: 2.0, 3: 2.5},
        'exit_method': 'scaled',
        'min_fundamental': 60,
        'pyramiding': True,
    },
    3: {
        'name': 'Qullamaggie Aggressive',
        'system_id': 3,
        'base_risk': 2.0,
        'conviction_multipliers': {5: 1.5, 4: 1.25, 3: 1.0},
        'min_conviction': 3,
        'max_positions': 15,
        'max_total_risk': 25.0,
        'stop_method': 'pattern',
        'exit_method': 'time_trail',
        'min_fundamental': 50,
        'prefer_breakouts': True,
    },
    4: {
        'name': 'Hybrid Balanced',
        'system_id': 4,
        'base_risk': 1.5,
        'conviction_multipliers': {5: 1.5, 4: 1.25, 3: 1.0},
        'min_conviction': 3,
        'max_positions': 12,
        'max_total_risk': 18.0,
        'stop_method': 'atr_with_cap',
        'atr_multipliers': {5: 1.5, 4: 2.0, 3: 2.5},
        'exit_method': 'adaptive',
        'min_fundamental': 60,
        'pyramiding': 'selective',
    },
    5: {
        'name': 'High Conviction Only',
        'system_id': 5,
        'base_risk': 2.5,
        'conviction_multipliers': {5: 1.0},
        'min_conviction': 5,
        'max_positions': 6,
        'max_total_risk': 15.0,
        'stop_method': 'tight',
        'stop_percent': 4,
        'exit_method': 'let_run',
        'min_fundamental': 75,
        'min_rs_rating': 90,
    },
    # ------------------------------------------------------------------
    # Real strategy families (the three canonical systems being compared)
    # ------------------------------------------------------------------
    6: {
        'name': 'VCP (Volatility Contraction Pattern)',
        'system_id': 6,
        'base_risk': 1.0,
        # VCP entries skew high-conviction; level 3 allowed as a catch-all
        'conviction_multipliers': {5: 1.5, 4: 1.0, 3: 0.75},
        'min_conviction': 3,
        'max_positions': 8,
        'max_total_risk': 12.0,
        # ATR-based stop placed below the VCP base low
        'stop_method': 'atr',
        'atr_multipliers': {5: 1.5, 4: 2.0, 3: 2.5},
        'exit_method': 'scaled',
        'min_fundamental': 65,
    },
    7: {
        'name': 'Conviction (Pure Technical)',
        'system_id': 7,
        'base_risk': 1.5,
        'conviction_multipliers': {5: 1.5, 4: 1.25, 3: 1.0, 2: 0.75},
        'min_conviction': 3,
        'max_positions': 15,
        'max_total_risk': 20.0,
        # Momentum strategy — trail out over time
        'stop_method': 'atr',
        'atr_multipliers': {5: 1.5, 4: 2.0, 3: 2.5},
        'exit_method': 'time_trail',
        'min_fundamental': 50,   # No fundamental gate in the scorer; harness still applies a minimum
    },
    8: {
        'name': '5LC (5-Level Conviction)',
        'system_id': 8,
        'base_risk': 1.5,
        # Wider sizing spread: high-conviction entries get proportionally more
        'conviction_multipliers': {5: 2.0, 4: 1.5, 3: 1.0, 2: 0.75},
        'min_conviction': 3,
        'max_positions': 12,
        'max_total_risk': 18.0,
        # 7% stop as per the 5LC strategy spec
        'stop_method': 'percentage',
        'stop_percent': 7,
        'exit_method': 'scaled',
        # Fundamental quality already enforced upstream; keep a sensible floor
        'min_fundamental': 65,
    },
}


# Map a universe name to its symbol file and buy-and-hold benchmark ticker.
# Symbol files live in ../../backtesting/data/. 'broad' is the default
# IVV+IJR (S&P 500 + S&P 600) universe loaded by load_initial_universe().
UNIVERSES = {
    'sp500':       {'file': 'sp500_symbols.csv',       'benchmark': 'SPY'},
    'russell1000': {'file': 'russell1000_symbols.csv', 'benchmark': 'IWB'},
    'nasdaq100':   {'file': 'nasdaq100_symbols.csv',   'benchmark': 'QQQ'},
    'asx300':      {'file': 'asx300_symbols.csv',      'benchmark': '^AXJO'},
    'ftse100':     {'file': 'ftse100_symbols.csv',     'benchmark': '^FTSE'},
}

# Named test windows (the plan asks for a 2022 bear stress window and a
# strong-bull window alongside the full period).
PERIODS = {
    'full':      ('2020-01-01', '2024-12-31'),
    'bear2022':  ('2022-01-01', '2022-12-31'),
    'bull2021':  ('2021-01-01', '2021-12-31'),
}

DATA_DIR = Path(__file__).parent.parent.parent / 'backtesting' / 'data'


def load_universe_symbols(universe: str) -> List[str]:
    """Load the symbol list for a named universe from backtesting/data/."""
    if universe == 'broad':
        return load_initial_universe()
    if universe not in UNIVERSES:
        print(f"ERROR: unknown universe '{universe}'. "
              f"Choices: {', '.join(['broad'] + list(UNIVERSES))}")
        return []
    fpath = DATA_DIR / UNIVERSES[universe]['file']
    if not fpath.exists():
        print(f"ERROR: symbol file not found: {fpath}")
        return []
    df = pd.read_csv(fpath)
    col = df.columns[0]
    symbols = [str(s).strip() for s in df[col].dropna() if str(s).strip()]
    print(f"Loaded {len(symbols)} symbols for universe '{universe}'")
    return symbols


def resolve_period(period: str) -> tuple:
    """Resolve a period name or 'START:END' string into (start, end) dates."""
    if period in PERIODS:
        return PERIODS[period]
    if ':' in period:
        start, end = period.split(':', 1)
        return start.strip(), end.strip()
    raise ValueError(
        f"Bad --period '{period}'. Use a name {list(PERIODS)} or 'YYYY-MM-DD:YYYY-MM-DD'."
    )


def load_initial_universe() -> List[str]:
    """
    Load the full broad universe from IVV (S&P 500) and IJR (S&P 600) holdings.

    These ETF symbol files live in downloads_2026-01-01 and give ~1,100 stocks.
    The historical screener filters this universe each quarter using only data
    available at each point in time — no lookahead bias.

    Returns:
        List of all symbols to consider each quarter
    """
    downloads_dir = Path(__file__).parent.parent / 'downloads_2026-01-01'

    symbols = set()
    for fname in ('IVV_symbols.csv', 'IJR_symbols.csv'):
        fpath = downloads_dir / fname
        if fpath.exists():
            df = pd.read_csv(fpath)
            col = df.columns[0]
            syms = df[col].dropna().astype(str).tolist()
            # Skip obvious non-equity rows (cash, futures placeholders like XTSLA)
            syms = [s.strip() for s in syms if s and not s.startswith('X') or len(s) <= 4]
            symbols.update(syms)
            print(f"  {fname}: {len(syms)} symbols")
        else:
            print(f"  Warning: {fpath} not found")

    if not symbols:
        print("ERROR: No IVV/IJR files found. Check downloads_2026-01-01 folder.")
        return []

    symbol_list = sorted(symbols)
    print(f"Loaded {len(symbol_list)} symbols (IVV S&P 500 + IJR S&P 600 universe)")
    return symbol_list


def run_simple_backtest(
    system_config: dict,
    symbols: List[str],
    start_date: str = '2020-01-01',
    end_date: str = '2024-12-31',
    universe_label: str = 'broad',
    period_label: str = 'full',
    benchmark_symbol: str = 'SPY',
    scorecard_path: str = 'results/scorecard.csv',
) -> PerformanceMetrics:
    """
    Run a backtest with PROPER HISTORICAL SCREENING (no lookahead bias).

    Args:
        system_config: System configuration
        symbols: List of symbols to consider
        start_date: Backtest start date
        end_date: Backtest end date

    Returns:
        PerformanceMetrics object
    """
    print(f"\nRunning backtest for: {system_config['name']}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial universe: {len(symbols)} symbols")
    print(f"Min conviction: {system_config['min_conviction']}")
    print(f"Base risk: {system_config['base_risk']}%")

    # Step 1: Run HISTORICAL SCREENING (quarterly rebalancing)
    # Market profile drives the liquidity/fundamental thresholds. AU/UK
    # universes need looser absolutes than the US default, else only a
    # handful of stocks clear each quarter. Inferred from ticker suffix
    # if not derivable from the universe label.
    market = {'asx300': 'au', 'ftse100': 'uk'}.get(universe_label, 'us')
    print("\n*** Running Historical Screening (No Lookahead Bias) ***")
    screener = HistoricalScreener(symbols, market=market)

    quarterly_universe = screener.run_quarterly_screening(
        start_date=start_date,
        end_date=end_date,
        rebalance_frequency='Q'  # Quarterly rebalancing
    )

    # Initialize engine
    engine = BacktestEngine(
        account_size=2_000_000,
        start_date=start_date,
        end_date=end_date,
        exit_method=system_config.get('exit_method', 'scaled'),
    )

    # Override position calculator parameters
    engine.position_calculator.base_risk_percent = system_config['base_risk']
    engine.position_calculator.conviction_multipliers = system_config['conviction_multipliers']
    engine.position_calculator.max_total_portfolio_risk = system_config['max_total_risk']
    engine.position_calculator.max_positions = system_config['max_positions']

    # Cap position size so all max_positions slots can be filled simultaneously.
    # e.g. 12 positions → 8% cap; 6 positions → 15% cap (hard ceiling at 15%).
    max_pos_pct = min(round(100 / system_config['max_positions'], 1), 15.0)
    engine.position_calculator.position_limits_by_tier = {
        'TIER 1 - EXCELLENT': max_pos_pct,
        'TIER 2 - GOOD':      max_pos_pct,
        'TIER 3 - ADEQUATE':  max_pos_pct,
    }

    # Step 2: Reuse price data already downloaded by the screener (no second API round)
    print(f"\n*** Processing Historical Data ***")
    price_data = {}
    for symbol, raw_df in screener._price_cache.items():
        df = engine.enrich_cached_data(symbol, raw_df)
        if df is not None:
            price_data[symbol] = df

    print(f"Loaded data for {len(price_data)} stocks")

    # Step 3: Simulate trading — quarterly fundamental rebalance + daily technical scan
    print(f"\n*** Running Simulation ***")

    trading_days = pd.date_range(start=start_date, end=end_date, freq='B')
    system_id    = system_config.get('system_id', 2)

    current_universe   = []
    last_rebalance_qtr = None   # tracks the last quarter-start date
    entries_today      = 0
    MAX_ENTRIES_PER_DAY = 3      # avoid piling in all at once

    for date in trading_days:

        # ── Quarterly fundamental rebalance ─────────────────────────────────
        # Rebalance when quarter changes (every ~63 business days / 90 calendar days)
        if last_rebalance_qtr is None or (date - last_rebalance_qtr).days >= 88:
            new_universe = screener.get_universe_for_date(date, quarterly_universe)
            if new_universe != current_universe:
                current_universe   = new_universe
                last_rebalance_qtr = date
                print(f"\n{date.date()}: Fundamental rebalance — "
                      f"{len(current_universe)} qualifying stocks")

        # ── Market health from SPY MAs ───────────────────────────────────────
        spy_df = engine._spy_data
        if spy_df is not None:
            market_health = get_market_health(spy_df, date)
        else:
            market_health = 'neutral'

        # Skip new entries in bear market (price below 200MA) for risk control
        if market_health == 'bear':
            engine.check_exits(date, price_data)
            engine.update_equity_curve(date, price_data)
            continue

        # ── Daily technical scan on the fundamental universe ─────────────────
        if current_universe and len(engine.open_trades) < engine.position_calculator.max_positions:
            signals = scan_universe(
                universe      = current_universe,
                price_data    = price_data,
                date          = date,
                system_id     = system_id,
                min_conviction= system_config['min_conviction'],
                market_health = market_health,
            )

            # Sort by conviction (highest first) so best setups get filled first
            entries_today = 0
            for symbol, conviction in sorted(signals.items(),
                                             key=lambda x: x[1], reverse=True):
                if entries_today >= MAX_ENTRIES_PER_DAY:
                    break
                if len(engine.open_trades) >= engine.position_calculator.max_positions:
                    break

                # Skip if already in position
                if any(t.symbol == symbol for t in engine.open_trades):
                    continue

                df = price_data.get(symbol)
                if df is None:
                    continue

                available = df.index[df.index <= date]
                if available.empty:
                    continue
                nearest = available[-1]

                entry_price = df.loc[nearest, 'close']
                atr         = df.loc[nearest, 'atr']

                if pd.isna(atr) or atr <= 0 or pd.isna(entry_price):
                    continue

                engine.enter_trade(
                    symbol         = symbol,
                    date           = date,
                    price          = entry_price,
                    atr            = atr,
                    conviction_level = conviction,
                    market_health  = market_health,
                    pattern_type   = 'breakout',
                )
                entries_today += 1

        # ── Daily exit management ────────────────────────────────────────────
        engine.check_exits(date, price_data)
        engine.update_equity_curve(date, price_data)

    # Close remaining open positions at end of period
    for trade in engine.open_trades[:]:
        last_date = trading_days[-1]
        if trade.symbol in price_data:
            df = price_data[trade.symbol]
            available = df.index[df.index <= last_date]
            if not available.empty:
                exit_price = df.loc[available[-1], 'close']
                engine.exit_trade(trade, last_date, exit_price, 'END_OF_PERIOD')

    # Calculate metrics
    metrics = engine.calculate_metrics()

    # Save results
    engine.save_results(system_config['name'].replace(' ', '_'))

    # Append a standardized row to the shared scorecard
    _, benchmark_cagr = engine.calculate_benchmark_return(benchmark_symbol)
    engine.append_scorecard(
        strategy=system_config['name'],
        universe=universe_label,
        period=f"{start_date}:{end_date}" if period_label == 'custom' else period_label,
        metrics=metrics,
        benchmark_cagr=benchmark_cagr,
        scorecard_path=scorecard_path,
    )

    return metrics


def print_metrics(system_name: str, metrics: PerformanceMetrics, benchmark_cagr: float = 0):
    """Print performance metrics in formatted table."""
    print(f"\n{'='*80}")
    print(f"RESULTS: {system_name}")
    print(f"{'='*80}")

    print(f"\nRETURNS:")
    print(f"  Total Return:        {metrics.total_return_pct:>10.2f}%")
    print(f"  Total $ Return:      ${metrics.total_return_dollars:>10,.0f}")
    print(f"  CAGR:                {metrics.cagr:>10.2f}%")

    if benchmark_cagr > 0:
        alpha = metrics.cagr - benchmark_cagr
        print(f"  Benchmark (SPY):     {benchmark_cagr:>10.2f}%")
        sign = '[+]' if alpha > 0 else '[-]'
        print(f"  Alpha vs SPY:        {alpha:>10.2f}%  {sign}")

    print(f"\nRISK:")
    print(f"  Max Drawdown:        {metrics.max_drawdown_pct:>10.2f}%")
    print(f"  Max DD $:            ${metrics.max_drawdown_dollars:>10,.0f}")
    print(f"  Sharpe Ratio:        {metrics.sharpe_ratio:>10.2f}")
    print(f"  Sortino Ratio:       {metrics.sortino_ratio:>10.2f}")

    print(f"\nTRADES:")
    print(f"  Total Trades:        {metrics.total_trades:>10}")
    print(f"  Win Rate:            {metrics.win_rate:>10.2f}%")
    print(f"  Profit Factor:       {metrics.profit_factor:>10.2f}")

    print(f"\nP&L:")
    print(f"  Avg Win:             {metrics.avg_win_pct:>10.2f}%")
    print(f"  Avg Loss:            {metrics.avg_loss_pct:>10.2f}%")
    print(f"  Largest Win:         {metrics.largest_win_pct:>10.2f}%")
    print(f"  Largest Loss:        {metrics.largest_loss_pct:>10.2f}%")

    print(f"\nR-MULTIPLES:")
    print(f"  Avg R-Multiple:      {metrics.avg_r_multiple:>10.2f}R")
    print(f"  Expectancy:          {metrics.expectancy:>10.2f}%")

    print(f"\nPOSITIONS:")
    print(f"  Avg Holding Days:    {metrics.avg_holding_days:>10.1f}")
    print(f"  Max Positions:       {metrics.max_positions_held:>10}")
    print(f"  Avg Position Size:   {metrics.avg_position_size_pct:>10.2f}%")

    print(f"{'='*80}\n")


# Map a strategy slug (for --strategy) to a system number.
STRATEGY_SLUGS = {
    # Original sizing presets (control group)
    'minervini':      1,
    'turtle':         2,
    'qullamaggie':    3,
    'hybrid':         4,
    'highconviction': 5,
    # Real strategy families
    'vcp':            6,
    'conviction':     7,
    '5lc':            8,
}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run trading system backtests')
    parser.add_argument('--system', type=int, choices=list(SYSTEMS),
                        help='System number to test (1-8)')
    parser.add_argument('--strategy', choices=list(STRATEGY_SLUGS),
                        help='Strategy by name (alias for --system)')
    parser.add_argument('--universe', default='broad',
                        choices=['broad'] + list(UNIVERSES),
                        help='Universe to trade (default: broad = IVV+IJR)')
    parser.add_argument('--period', default='full',
                        help="Named window (full, bear2022, bull2021) "
                             "or 'YYYY-MM-DD:YYYY-MM-DD'")
    parser.add_argument('--all', action='store_true', help='Run all systems')
    parser.add_argument('--compare', action='store_true', help='Compare existing results')

    args = parser.parse_args()

    if args.compare:
        print("Comparison feature coming soon...")
        return

    # Resolve period
    try:
        START_DATE, END_DATE = resolve_period(args.period)
    except ValueError as e:
        print(f"ERROR: {e}")
        return
    period_label = args.period if (args.period in PERIODS) else 'custom'

    # Resolve universe + benchmark
    universe_label = args.universe
    benchmark_symbol = UNIVERSES.get(universe_label, {}).get('benchmark', 'SPY')

    # Load symbol universe
    print(f"Loading universe '{universe_label}' ...")
    symbols = load_universe_symbols(universe_label)

    if not symbols:
        print("ERROR: No symbols loaded.")
        return

    # Calculate benchmark buy-and-hold
    print("\n" + "="*80)
    print(f"BENCHMARK: {benchmark_symbol} Buy-and-Hold ({START_DATE} to {END_DATE})")
    print("="*80)
    temp_engine = BacktestEngine(account_size=2_000_000, start_date=START_DATE, end_date=END_DATE)
    benchmark_return, benchmark_cagr = temp_engine.calculate_benchmark_return(benchmark_symbol)
    print(f"{benchmark_symbol} Total Return: {benchmark_return:.2f}%")
    print(f"{benchmark_symbol} CAGR:         {benchmark_cagr:.2f}%")
    print(f"\nYour systems need to beat {benchmark_cagr:.2f}% CAGR to outperform.")
    print("="*80)


    # Resolve --strategy slug into a system number
    if args.strategy and not args.system:
        args.system = STRATEGY_SLUGS[args.strategy]

    if args.all:
        # Run all systems
        results = {}
        for sys_num in list(SYSTEMS):
            config = SYSTEMS[sys_num]
            metrics = run_simple_backtest(
                config, symbols, START_DATE, END_DATE,
                universe_label, period_label, benchmark_symbol)
            results[config['name']] = metrics
            print_metrics(config['name'], metrics, benchmark_cagr)

        comparison_df = pd.DataFrame([
            {
                'System': name,
                'CAGR': m.cagr,
                'Alpha': m.cagr - benchmark_cagr,
                'Max DD': m.max_drawdown_pct,
                'Sharpe': m.sharpe_ratio,
                'Win Rate': m.win_rate,
                'Avg R': m.avg_r_multiple,
                'Trades': m.total_trades
            }
            for name, m in results.items()
        ])
        comparison_file = Path('backtesting/results/comparison.csv')
        comparison_df.to_csv(comparison_file, index=False)
        print(f"\nComparison saved to {comparison_file}")
        print("\n" + comparison_df.to_string(index=False))

    elif args.system:
        config = SYSTEMS[args.system]
        metrics = run_simple_backtest(
            config, symbols, START_DATE, END_DATE,
            universe_label, period_label, benchmark_symbol)
        print_metrics(config['name'], metrics, benchmark_cagr)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
