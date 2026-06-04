"""
Offline validation for the unified backtest harness (Phase 1).

Runs WITHOUT any network access by feeding the engine synthetic, deterministic
price data. Proves the three Phase 1 guarantees:

  1. Cash is never negative (no implicit leverage / overdraft).
  2. The equity curve is marked to market (open positions revalue with price).
  3. Calmar, exposure and turnover are computed correctly.

Run:  python tests/test_harness_offline.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from backtest_engine import BacktestEngine, Trade, PerformanceMetrics


def _make_price_df(dates, closes):
    """Build an OHLCV+indicator DataFrame the engine can consume."""
    closes = np.asarray(closes, dtype=float)
    df = pd.DataFrame(
        {
            'open': closes,
            'high': closes * 1.01,
            'low': closes * 0.99,
            'close': closes,
            'volume': 1_000_000,
            'atr': closes * 0.02,          # 2% ATR
            'ma_10': closes,
            'ma_20': closes,
            'ma_50': closes,
            'ma_150': closes,
            'ma_200': closes,
            'relative_strength': 5.0,
        },
        index=dates,
    )
    return df


def test_cash_never_negative():
    """Fire many entry attempts; cash must stay >= 0 and overdraft is rejected."""
    engine = BacktestEngine(account_size=100_000, start_date='2022-01-03',
                            end_date='2022-02-28')
    engine._spy_data = None  # force offline, no market filter dependency

    dates = pd.date_range('2022-01-03', '2022-02-28', freq='B')
    price_data = {}
    # 30 symbols all flashing buy signals — far more than cash can fund
    for i in range(30):
        sym = f"S{i:02d}"
        price_data[sym] = _make_price_df(dates, np.full(len(dates), 100.0))

    first = dates[0]
    for sym, df in price_data.items():
        engine.enter_trade(
            symbol=sym, date=first, price=100.0,
            atr=2.0, conviction_level=5, market_health='bull',
            pattern_type='breakout',
        )
        # Cash must never go below zero at any point
        assert engine.current_capital >= -1e-6, \
            f"Cash went negative after entering {sym}: {engine.current_capital}"

    # Mark to market on day 1 — assertion inside also guards cash
    engine.update_equity_curve(first, price_data)

    # Sum of open position cost must not exceed starting capital
    invested = sum(t.position_value for t in engine.open_trades)
    assert invested <= engine.initial_capital + 1e-6, \
        f"Invested {invested} exceeds capital {engine.initial_capital}"
    print(f"  [PASS] cash_never_negative — {len(engine.open_trades)} positions, "
          f"cash ${engine.current_capital:,.0f}, invested ${invested:,.0f}")


def test_mark_to_market():
    """Equity must rise when an open position's price rises (not stay flat)."""
    engine = BacktestEngine(account_size=100_000, start_date='2022-01-03',
                            end_date='2022-01-31')
    engine._spy_data = None

    dates = pd.date_range('2022-01-03', '2022-01-31', freq='B')
    # Price ramps 100 -> 150 over the window
    closes = np.linspace(100, 150, len(dates))
    df = _make_price_df(dates, closes)
    price_data = {'RAMP': df}

    engine.enter_trade(symbol='RAMP', date=dates[0], price=100.0, atr=2.0,
                       conviction_level=5, market_health='bull',
                       pattern_type='breakout')

    # Equity on entry day vs a later day (price much higher, still holding)
    engine.update_equity_curve(dates[0], price_data)
    eq_start = engine.equity_curve[-1]['equity']

    engine.update_equity_curve(dates[-1], price_data)
    eq_end = engine.equity_curve[-1]['equity']

    assert eq_end > eq_start + 1.0, \
        f"Equity did not mark to market: start {eq_start}, end {eq_end}"

    # Sanity: gain roughly equals shares * price change
    shares = engine.open_trades[0].shares
    expected_gain = shares * (closes[-1] - closes[0])
    actual_gain = eq_end - eq_start
    assert abs(actual_gain - expected_gain) < 1.0, \
        f"MTM gain {actual_gain} != expected {expected_gain}"
    print(f"  [PASS] mark_to_market — equity ${eq_start:,.0f} -> ${eq_end:,.0f} "
          f"(+${actual_gain:,.0f}, {shares} shares)")


def test_metrics_math():
    """Calmar / exposure / turnover computed on a hand-built engine state."""
    engine = BacktestEngine(account_size=100_000, start_date='2022-01-01',
                            end_date='2022-12-31')
    engine._spy_data = None

    # Hand-built equity curve: 100k -> 80k (drawdown) -> 120k
    dates = pd.date_range('2022-01-01', periods=4, freq='90D')
    equities = [100_000, 80_000, 110_000, 120_000]
    open_pos = [1, 1, 0, 1]   # exposure = 3/4 days = 75%
    engine.equity_curve = [
        {'date': d, 'equity': e, 'cash': e, 'positions_value': 0,
         'open_positions': p}
        for d, e, p in zip(dates, equities, open_pos)
    ]

    # Two closed trades: one win, one loss
    engine.closed_trades = [
        Trade(symbol='A', entry_date='2022-01-01', entry_price=100, shares=100,
              position_value=10_000, conviction_level=5, stop_price=95,
              stop_percent=5, target_1_price=120, target_2_price=130,
              target_3_price=140, position_risk_pct=1.0, dollar_risk=500,
              exit_date='2022-03-01', exit_price=120, exit_reason='PROFIT_TARGET_1',
              pnl_dollars=2_000, pnl_percent=20, r_multiple=2.0, holding_days=59),
        Trade(symbol='B', entry_date='2022-04-01', entry_price=50, shares=200,
              position_value=10_000, conviction_level=4, stop_price=47,
              stop_percent=6, target_1_price=60, target_2_price=65,
              target_3_price=70, position_risk_pct=1.0, dollar_risk=600,
              exit_date='2022-05-01', exit_price=45, exit_reason='STOP_LOSS',
              pnl_dollars=-1_000, pnl_percent=-10, r_multiple=-1.0, holding_days=30),
    ]

    m = engine.calculate_metrics()

    # CAGR over ~270 days from 100k -> 120k
    years = (engine.end_date - engine.start_date).days / 365.25
    expected_cagr = ((120_000 / 100_000) ** (1 / years) - 1) * 100
    # Max drawdown: 100k -> 80k = -20%
    expected_maxdd = -20.0
    expected_calmar = expected_cagr / abs(expected_maxdd)

    assert abs(m.cagr - round(expected_cagr, 2)) < 0.5, (m.cagr, expected_cagr)
    assert abs(m.max_drawdown_pct - expected_maxdd) < 0.5, m.max_drawdown_pct
    assert abs(m.calmar_ratio - round(expected_calmar, 2)) < 0.1, \
        (m.calmar_ratio, expected_calmar)

    # Exposure = 3 of 4 days = 75%
    assert abs(m.exposure_pct - 75.0) < 0.01, m.exposure_pct

    # Turnover = (entries 20k) + (exits: A 100*120=12k, B 200*45=9k) = 41k / 100k
    expected_turnover = (10_000 + 10_000 + 12_000 + 9_000) / 100_000
    assert abs(m.turnover - round(expected_turnover, 2)) < 0.01, \
        (m.turnover, expected_turnover)

    print(f"  [PASS] metrics_math — CAGR {m.cagr}%, MaxDD {m.max_drawdown_pct}%, "
          f"Calmar {m.calmar_ratio}, exposure {m.exposure_pct}%, "
          f"turnover {m.turnover}")


def test_scorecard_written(tmp_path='results/_test_scorecard.csv'):
    """append_scorecard writes a one-row standardized file."""
    engine = BacktestEngine(account_size=100_000, start_date='2022-01-01',
                            end_date='2022-12-31')
    engine._spy_data = None
    # minimal state so calculate_metrics returns the empty-metrics object
    engine.append_scorecard(strategy='UnitTest', universe='sp500',
                            period='full', benchmark_cagr=8.0,
                            scorecard_path=tmp_path)
    df = pd.read_csv(tmp_path)
    assert list(df.columns)[:4] == ['timestamp', 'strategy', 'universe', 'period']
    assert df.iloc[-1]['strategy'] == 'UnitTest'
    try:
        Path(tmp_path).unlink()  # clean up (best effort)
    except OSError:
        pass
    print(f"  [PASS] scorecard_written — {len(df.columns)} columns")


if __name__ == '__main__':
    print("Offline harness validation")
    print("-" * 50)
    test_cash_never_negative()
    test_mark_to_market()
    test_metrics_math()
    test_scorecard_written()
    print("-" * 50)
    print("ALL OFFLINE CHECKS PASSED")
