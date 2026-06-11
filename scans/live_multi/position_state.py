"""
Per-system persistent position state.

Each system gets its OWN state file (state/state_<TAG>.json) so the three
systems never clobber each other and can be inspected independently.

Schema (per file):
{
    "system_id":           7,
    "system_name":         "Conviction (Pure Technical)",
    "last_run_date":       "2026-06-05",
    "last_rebalance_date": "2026-04-01",
    "quarterly_universe":  ["AAPL", ...],
    "positions": [
        {
            "symbol", "entry_date", "entry_price", "shares",
            "initial_stop", "stop_price", "conviction", "atr_at_entry",
            "highest_close", "ib_entry_order_id", "ib_stop_order_id",
            "status": "pending_entry" | "open"
        }
    ]
}
"""

import json
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


def _empty_state(system_id: int, system_name: str) -> dict:
    return {
        'system_id': system_id,
        'system_name': system_name,
        'last_run_date': None,
        'last_rebalance_date': None,
        'quarterly_universe': [],
        'positions': [],
    }


def load(state_file: Path, system_id: int, system_name: str) -> dict:
    if not state_file.exists():
        log.info(f"[{system_name}] No state file — starting fresh")
        return _empty_state(system_id, system_name)
    try:
        with open(state_file) as f:
            state = json.load(f)
        log.info(f"[{system_name}] Loaded {len(state.get('positions', []))} positions")
        return state
    except Exception as e:
        log.error(f"[{system_name}] Failed to load state: {e} — starting fresh")
        return _empty_state(system_id, system_name)


def save(state: dict, state_file: Path):
    tmp = state_file.with_suffix('.json.tmp')
    try:
        with open(tmp, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        tmp.replace(state_file)
    except Exception as e:
        log.error(f"Failed to save state {state_file}: {e}")
        if tmp.exists():
            tmp.unlink()


def open_positions(state: dict) -> List[dict]:
    return [p for p in state.get('positions', [])
            if p.get('status') in ('open', 'pending_entry')]


def open_symbols(state: dict) -> set:
    return {p['symbol'] for p in open_positions(state)}


def get_position(state: dict, symbol: str) -> Optional[dict]:
    for p in state.get('positions', []):
        if p['symbol'] == symbol and p.get('status') in ('open', 'pending_entry'):
            return p
    return None


def add_position(state: dict, symbol: str, entry_date: str, entry_price: float,
                 shares: int, stop_price: float, conviction: int, atr: float,
                 ib_entry_order_id: Optional[int], ib_stop_order_id: Optional[int]):
    state.setdefault('positions', []).append({
        'symbol': symbol,
        'entry_date': entry_date,
        'entry_price': entry_price,
        'shares': shares,
        'initial_stop': stop_price,
        'stop_price': stop_price,
        'conviction': conviction,
        'atr_at_entry': atr,
        'highest_close': entry_price,
        'ib_entry_order_id': ib_entry_order_id,
        'ib_stop_order_id': ib_stop_order_id,
        'status': 'pending_entry',
    })


def remove_position(state: dict, symbol: str):
    before = len(state.get('positions', []))
    state['positions'] = [p for p in state.get('positions', [])
                          if not (p['symbol'] == symbol
                                  and p.get('status') in ('open', 'pending_entry'))]
    if len(state.get('positions', [])) != before:
        log.info(f"Position removed from state: {symbol}")


def needs_rebalance(state: dict, today: str, interval_days: int = 88) -> bool:
    last = state.get('last_rebalance_date')
    if not last:
        return True
    last_dt = datetime.strptime(last, '%Y-%m-%d').date()
    today_dt = datetime.strptime(today, '%Y-%m-%d').date()
    return (today_dt - last_dt).days >= interval_days
