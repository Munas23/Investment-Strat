"""
Offline regression tests for the Phase 3a recalibration.

No network required — validates the market-aware screening profiles and the
loosened VCP entry gate purely from synthetic data / constants.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.historical_screener import detect_market, MARKET_THRESHOLDS  # noqa: E402
from utils.technical_scanner import _atr_contraction, _score_vcp        # noqa: E402


def test_market_detection_by_suffix():
    assert detect_market(['BHP.AX', 'CBA.AX', 'WBC.AX']) == 'au'
    assert detect_market(['BP.L', 'HSBA.L']) == 'uk'
    assert detect_market(['AAPL', 'MSFT', 'NVDA']) == 'us'
    assert detect_market([]) == 'us'           # empty -> safe default
    assert detect_market(['AAPL', 'MSFT', 'BHP.AX']) == 'us'  # AU minority -> us


def test_au_profile_strictly_looser_than_us():
    # Every AU threshold must be looser (lower) than the US default, otherwise
    # the ASX universe stays starved of qualifying names.
    for key in MARKET_THRESHOLDS['us']:
        assert MARKET_THRESHOLDS['au'][key] < MARKET_THRESHOLDS['us'][key], key
        assert MARKET_THRESHOLDS['uk'][key] <= MARKET_THRESHOLDS['us'][key], key


def _vcp_fixture():
    n = 300
    idx = pd.date_range('2023-01-01', periods=n, freq='B')
    close = np.linspace(50, 100, n) + np.random.RandomState(1).normal(0, 0.2, n)
    df = pd.DataFrame({'close': close, 'volume': 500000.0}, index=idx)
    df['ma_50'] = df['close'].rolling(50).mean()
    df['ma_150'] = df['close'].rolling(150).mean()
    df['ma_200'] = df['close'].rolling(200).mean()
    atr = np.ones(n)
    atr[-5:] = 0.88                       # recent ATR between old (0.85) and new (0.92) gate
    df['atr'] = atr
    df['relative_strength'] = 5.0
    df.loc[df.index[-10:-1], 'volume'] = 450000.0
    df.loc[df.index[-30:-10], 'volume'] = 500000.0
    df.loc[df.index[-1], 'volume'] = 550000.0
    return df


def test_atr_gate_loosened():
    df = _vcp_fixture()
    assert bool(_atr_contraction(df, multiplier=0.85)) is False   # old gate rejects
    assert bool(_atr_contraction(df, multiplier=0.92)) is True    # new gate accepts


def test_vcp_now_produces_signal():
    # The loosened VCP must emit a signal on a base the old gate would skip.
    assert _score_vcp(_vcp_fixture()) is not None
