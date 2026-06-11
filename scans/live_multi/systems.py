"""
System definitions for the multi-system paper trader.

These mirror the Phase-2 bake-off advancement winners
(scans/backtesting/STRATEGY_SPEC.md):

    3  Qullamaggie Aggressive  — ATR stops, time-trail exit
                                 (chandelier tightens 3→2 ATR after 30 days)
    4  Hybrid Balanced         — ATR-with-cap stops, adaptive exit
                                 (bull: scaled; non-bull: let-run)

Each system carries everything the runner needs: scan id, sizing,
stop method, and a short `tag` used for orderRef + state filenames.

Stop-method note (STRATEGY_SPEC): system 3's backtest config declares
`stop_method: 'pattern'` but the advancement decision confirmed ATR-based
stops. We use 'atr' here to match the backtest that produced the numbers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import config


@dataclass
class SystemConfig:
    system_id: int
    name: str
    tag: str                       # short, filesystem/orderRef safe
    base_risk: float               # % of (allocated) equity risked at conviction 3
    conviction_multipliers: Dict[int, float]
    min_conviction: int
    max_positions: int
    max_total_risk: float          # % open-risk budget across all positions
    stop_method: str               # 'atr' | 'percentage'
    atr_multipliers: Optional[Dict[int, float]] = None
    stop_percent: Optional[float] = None
    exit_method: str = 'scaled'
    max_entries_per_day: int = config.MAX_ENTRIES_PER_DAY
    chandelier_atr_mult: float = config.CHANDELIER_ATR_MULT
    # atr_with_cap: per-conviction max stop-loss % (e.g. {5: 5, 4: 7, 3: 8})
    stop_cap_pct: Optional[Dict[int, float]] = None
    # time_trail: tighten chandelier to this ATR mult after N holding days
    time_trail_days: Optional[int] = None
    time_trail_tight_mult: float = 2.0

    # Derived per-system resources
    @property
    def state_file(self) -> Path:
        return config.STATE_DIR / f'state_{self.tag}.json'

    @property
    def order_ref(self) -> str:
        # Tag attached to every IB order so fills can be attributed per system.
        return f'LM_{self.tag}'      # e.g. LM_TURTLE


# ---------------------------------------------------------------------------
# The two bake-off Phase-2 advancement winners
# ---------------------------------------------------------------------------
_DEFINITIONS = {
    3: SystemConfig(
        system_id=3,
        name='Qullamaggie Aggressive',
        tag='QULL',
        base_risk=2.0,
        conviction_multipliers={5: 1.5, 4: 1.25, 3: 1.0},
        min_conviction=3,
        max_positions=15,
        max_total_risk=25.0,
        # STRATEGY_SPEC confirms ATR stops (backtest config said 'pattern')
        stop_method='atr',
        atr_multipliers={5: 1.5, 4: 2.0, 3: 2.5},
        exit_method='time_trail',
        # Tighten chandelier from 3→2 ATR after 30 holding days
        time_trail_days=30,
        time_trail_tight_mult=2.0,
    ),
    4: SystemConfig(
        system_id=4,
        name='Hybrid Balanced',
        tag='HYBRID',
        base_risk=1.5,
        conviction_multipliers={5: 1.5, 4: 1.25, 3: 1.0},
        min_conviction=3,
        max_positions=12,
        max_total_risk=18.0,
        stop_method='atr_with_cap',
        atr_multipliers={5: 1.5, 4: 2.0, 3: 2.5},
        # Per-conviction max stop width (tighter of ATR vs this %)
        stop_cap_pct={5: 5.0, 4: 7.0, 3: 8.0},
        exit_method='adaptive',
    ),
}


def active_systems() -> list:
    """Return SystemConfig objects for the IDs listed in config.ACTIVE_SYSTEM_IDS."""
    out = []
    for sid in config.ACTIVE_SYSTEM_IDS:
        if sid not in _DEFINITIONS:
            raise KeyError(f'System id {sid} is not defined in systems.py')
        out.append(_DEFINITIONS[sid])
    return out


def get_system(system_id: int) -> SystemConfig:
    return _DEFINITIONS[system_id]
