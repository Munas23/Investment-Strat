"""
Daily Technical Scanner

Runs every trading day on the quarterly-filtered fundamental universe.
Returns conviction-scored signals per system.

Market health is determined from SPY moving averages:
  Bull:    SPY > 200MA AND 50MA > 200MA
  Uptrend: SPY > 50MA
  Neutral: SPY between 50MA and 200MA
  Choppy:  SPY < 50MA but > 200MA
  Bear:    SPY < 200MA

Each system has its own entry logic:
  1 - Minervini: Stage 2 MA alignment, VCP proxy (ATR contraction)
  2 - Turtle:    20-day high breakout (classic Donchian)
  3 - Qullamaggie: Explosive volume breakout on a momentum day
  4 - Hybrid:    MA trend + 20-day high, adaptive to market
  5 - High Conviction: All Minervini + new 52-week high + top RS
  6 - VCP:        Full Volatility Contraction Pattern (Stage 2 + ATR squeeze + volume)
  7 - Conviction: Pure-technical points-based composite (no fundamental gate)
  8 - 5LC:        5-Level Conviction (conviction points + proximity-to-high gate)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Market health
# ---------------------------------------------------------------------------

def get_market_health(spy_df: pd.DataFrame, date: pd.Timestamp) -> str:
    """Classify market regime from SPY moving averages."""
    available = spy_df.index[spy_df.index <= date]
    if len(available) < 200:
        return 'neutral'

    row = spy_df.loc[available[-1]]
    price = row['close']

    ma50  = row.get('ma_50')
    ma200 = row.get('ma_200')
    if pd.isna(ma50) or pd.isna(ma200):
        slice_df = spy_df.loc[spy_df.index <= available[-1]]
        ma50  = slice_df['close'].tail(50).mean()
        ma200 = slice_df['close'].tail(200).mean()

    above_200 = price > ma200
    above_50  = price > ma50
    ma50_above_ma200 = ma50 > ma200

    if above_200 and above_50 and ma50_above_ma200:
        return 'bull'
    elif above_50:
        return 'uptrend'
    elif above_200:
        return 'choppy'
    else:
        return 'bear'


# ---------------------------------------------------------------------------
# Per-stock signal helpers
# ---------------------------------------------------------------------------

def _get_slice(df: pd.DataFrame, date: pd.Timestamp) -> Optional[pd.DataFrame]:
    """Return df sliced up to and including date (nearest trading day)."""
    available = df.index[df.index <= date]
    if len(available) < 60:
        return None
    return df.loc[available]


def _stage2_alignment(row: pd.Series) -> bool:
    """Minervini Stage 2: price above all MAs, MAs in proper order."""
    price  = row['close']
    ma50   = row.get('ma_50')
    ma150  = row.get('ma_150')
    ma200  = row.get('ma_200')
    if any(pd.isna(x) for x in [ma50, ma150, ma200]):
        return False
    return price > ma50 > ma150 > ma200


def _near_52w_high(sl: pd.DataFrame, pct_within: float = 0.25) -> bool:
    """Price is within pct_within of the 52-week high."""
    high_52w = sl['close'].tail(252).max()
    current  = sl['close'].iloc[-1]
    return current >= high_52w * (1 - pct_within)


def _volume_ratio(sl: pd.DataFrame, window: int = 20) -> float:
    """Today's volume relative to the N-day average."""
    avg_vol = sl['volume'].iloc[-(window + 1):-1].mean()
    if avg_vol == 0:
        return 1.0
    return sl['volume'].iloc[-1] / avg_vol


def _atr_contraction(sl: pd.DataFrame, multiplier: float = 0.85) -> bool:
    """ATR over last 5 days is lower than ATR over prior 15 days (VCP proxy).

    `multiplier` sets how much tighter recent ATR must be vs the prior window.
    Lower = stricter. VCP (system 6) passes a looser value than the default
    because the 0.85 gate starved it of signals in the bake-off.
    """
    if 'atr' not in sl.columns or len(sl) < 25:
        return False
    recent_atr = sl['atr'].iloc[-5:].mean()
    prior_atr  = sl['atr'].iloc[-20:-5].mean()
    return recent_atr < prior_atr * multiplier if prior_atr > 0 else False


def _donchian_breakout(sl: pd.DataFrame, period: int = 20) -> bool:
    """Today's close is the highest close over the last `period` days."""
    if len(sl) < period + 1:
        return False
    today_close = sl['close'].iloc[-1]
    prior_high  = sl['close'].iloc[-(period + 1):-1].max()
    return today_close >= prior_high


def _new_52w_high(sl: pd.DataFrame) -> bool:
    """Today's close is a new 52-week high."""
    if len(sl) < 252:
        return False
    today_close = sl['close'].iloc[-1]
    prior_high  = sl['close'].iloc[-252:-1].max()
    return today_close >= prior_high


def _rs_rank(sl: pd.DataFrame) -> float:
    """Relative strength: stock 3-month return vs SPY 3-month return."""
    rs = sl['relative_strength'].iloc[-1] if 'relative_strength' in sl.columns else 0
    return 0 if pd.isna(rs) else rs


def _day_return(sl: pd.DataFrame) -> float:
    """Today's percentage change."""
    if len(sl) < 2:
        return 0.0
    prev = sl['close'].iloc[-2]
    curr = sl['close'].iloc[-1]
    return ((curr - prev) / prev) * 100 if prev > 0 else 0.0


# ---------------------------------------------------------------------------
# Per-system entry scoring (original presets, systems 1-5)
# ---------------------------------------------------------------------------

def _score_system1(sl: pd.DataFrame) -> Optional[int]:
    """System 1: Minervini Conservative."""
    if not _stage2_alignment(sl.iloc[-1]):
        return None
    if not _near_52w_high(sl, pct_within=0.15):
        return None

    conviction = 4
    if _atr_contraction(sl) and _rs_rank(sl) > 15 and _volume_ratio(sl) > 1.2:
        conviction = 5
    return conviction


def _score_system2(sl: pd.DataFrame) -> Optional[int]:
    """System 2: Turtle ATR-Based (Donchian 20-day breakout)."""
    row = sl.iloc[-1]
    if pd.isna(row.get('ma_50')) or row['close'] < row['ma_50']:
        return None
    if not _donchian_breakout(sl, period=20):
        return None

    above_200 = not pd.isna(row.get('ma_200')) and row['close'] > row['ma_200']
    rs = _rs_rank(sl)
    vol = _volume_ratio(sl)

    if above_200 and rs > 10 and vol > 1.5:
        return 5
    elif above_200 or rs > 5:
        return 4
    return 3


def _score_system3(sl: pd.DataFrame) -> Optional[int]:
    """System 3: Qullamaggie Aggressive (explosive volume breakout)."""
    if not _donchian_breakout(sl, period=20):
        return None
    if not _near_52w_high(sl, pct_within=0.10):
        return None

    day_ret = _day_return(sl)
    vol_ratio = _volume_ratio(sl)

    if day_ret < 3.0 or vol_ratio < 1.5:
        return None

    if vol_ratio >= 3.0 and day_ret >= 8.0:
        return 5
    elif vol_ratio >= 2.0 and day_ret >= 5.0:
        return 4
    return 3


def _score_system4(sl: pd.DataFrame) -> Optional[int]:
    """System 4: Hybrid Balanced."""
    row = sl.iloc[-1]
    if pd.isna(row.get('ma_50')) or row['close'] < row['ma_50']:
        return None
    if not _near_52w_high(sl, pct_within=0.20):
        return None
    if not _donchian_breakout(sl, period=20):
        return None

    if _stage2_alignment(row) and _rs_rank(sl) > 10:
        conviction = 5
    elif not pd.isna(row.get('ma_200')) and row['close'] > row['ma_200']:
        conviction = 4
    else:
        conviction = 3
    return conviction


def _score_system5(sl: pd.DataFrame) -> Optional[int]:
    """System 5: High Conviction Only."""
    if not _stage2_alignment(sl.iloc[-1]):
        return None
    if not _new_52w_high(sl):
        return None
    if _rs_rank(sl) < 20:
        return None
    if _volume_ratio(sl) < 1.2:
        return None
    return 5


# ---------------------------------------------------------------------------
# Real strategy families (systems 6-8)
# ---------------------------------------------------------------------------

def _conviction_points(sl: pd.DataFrame) -> float:
    """Shared conviction-points engine used by Conviction (7) and 5LC (8)."""
    points = 0.0

    if _donchian_breakout(sl, period=20):
        points += 30

    vol = _volume_ratio(sl)
    if vol >= 3.0:
        points += 25
    elif vol >= 2.0:
        points += 20
    elif vol >= 1.5:
        points += 15
    elif vol >= 1.2:
        points += 8

    day_ret = _day_return(sl)
    if day_ret >= 5.0:
        points += 25
    elif day_ret >= 3.0:
        points += 15
    elif day_ret >= 1.0:
        points += 8

    row = sl.iloc[-1]
    if _stage2_alignment(row):
        points += 20
    elif not pd.isna(row.get('ma_200')) and row['close'] > row.get('ma_200', 0):
        points += 10

    return points


def _points_to_level(points: float) -> Optional[int]:
    """Map raw conviction points (0-100) to levels 1-5."""
    if points >= 85:
        return 5
    elif points >= 70:
        return 4
    elif points >= 55:
        return 3
    elif points >= 40:
        return 2
    elif points >= 25:
        return 1
    return None


def _score_vcp(sl: pd.DataFrame) -> Optional[int]:
    """
    System 6: VCP (Volatility Contraction Pattern)
    Full Minervini VCP: Stage 2 + progressive ATR contraction + volume
    drying up in the base, then expanding on the entry day.
    Proximity-to-high gate within 15% (recalibrated from 10% - the tighter
    gate combined with the ATR/volume filters left VCP starved of trades in
    the Phase 2 bake-off).

    Conviction:
      5 - volume contracted in base AND today's volume >= 1.5x AND RS > 20
      4 - volume contracted in base AND today's volume >= 1.2x AND RS > 10
      3 - ATR contracting + today's volume >= 1.0x + RS > 0
    """
    if not _stage2_alignment(sl.iloc[-1]):
        return None
    if not _near_52w_high(sl, pct_within=0.15):
        return None
    # Looser contraction gate (0.92 vs default 0.85) so shallower VCP bases qualify
    if not _atr_contraction(sl, multiplier=0.92):
        return None

    base_vol  = sl['volume'].iloc[-10:-1].mean()
    prior_vol = sl['volume'].iloc[-30:-10].mean()
    vol_contracting = (base_vol < prior_vol * 0.92) if prior_vol > 0 else False

    vol_today = _volume_ratio(sl)
    rs = _rs_rank(sl)

    if vol_contracting and vol_today >= 1.5 and rs > 20:
        return 5
    elif vol_contracting and vol_today >= 1.2 and rs > 10:
        return 4
    elif vol_today >= 1.0 and rs > 0:
        return 3
    return None


def _score_conviction(sl: pd.DataFrame) -> Optional[int]:
    """System 7: Conviction (pure technical) - points composite, no fundamental gate."""
    return _points_to_level(_conviction_points(sl))


def _score_5lc(sl: pd.DataFrame) -> Optional[int]:
    """System 8: 5LC - conviction points + proximity-to-52w-high gate (within 25%)."""
    if not _near_52w_high(sl, pct_within=0.25):
        return None
    return _points_to_level(_conviction_points(sl))


_SCORERS = {
    1: _score_system1,
    2: _score_system2,
    3: _score_system3,
    4: _score_system4,
    5: _score_system5,
    6: _score_vcp,
    7: _score_conviction,
    8: _score_5lc,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_universe(
    universe: List[str],
    price_data: Dict[str, pd.DataFrame],
    date: pd.Timestamp,
    system_id: int,
    min_conviction: int = 3,
    market_health: str = 'neutral',
) -> Dict[str, int]:
    """Scan every stock in the fundamental universe for today's technical signal."""
    scorer = _SCORERS.get(system_id)
    if scorer is None:
        return {}

    signals = {}
    for symbol in universe:
        df = price_data.get(symbol)
        if df is None:
            continue

        sl = _get_slice(df, date)
        if sl is None or len(sl) < 60:
            continue

        if sl['volume'].iloc[-1] < 200_000:
            continue
        if sl['close'].iloc[-1] < 5:
            continue

        try:
            conviction = scorer(sl)
        except Exception:
            conviction = None

        if conviction is not None and conviction >= min_conviction:
            signals[symbol] = conviction

    return signals
