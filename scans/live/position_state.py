"""
Persistent position state for the live trader.

Saves/loads a JSON file (state.json) that survives between daily runs.
Each position tracks: symbol, entry info, current stop, IB order IDs,
and the highest close since entry (needed for chandelier trailing stop).

Schema:
{
    "last_run_date":       "2026-03-20",
    "last_rebalance_date": "2026-01-01",
    "quarterly_universe":  ["AAPL", "MSFT", ...],
    "positions": [
        {
            "symbol":            "AAPL",
            "entry_date":        "2026-03-20",
            "entry_price":       215.50,
            "shares":            46,
            "initial_stop":      208.00,
            "stop_price":        208.00,
            "conviction":        4,
            "atr_at_entry":      3.20,
            "highest_close":     215.50,
            "ib_entry_order_id": 1001,
            "ib_stop_order_id":  1002,
            "status":            "pending_entry"  | "open" | "pending_exit"
        }
    ]
}
"""

import json
import logging
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)

_EMPTY_STATE = {
    'last_run_date':       None,
    'last_rebalance_date': None,
    'quarterly_universe':  [],
    'positions':           [],
}


def load(state_file: Path) -> dict:
    """Load state from disk. Returns empty state if file doesn't exist."""
    if not state_file.exists():
        log.info(f"No state file found at {state_file} — starting fresh")
        return deepcopy(_EMPTY_STATE)
    try:
        with open(state_file) as f:
            state = json.load(f)
        log.info(f"Loaded state: {len(state.get('positions', []))} open positions")
        return state
    except Exception as e:
        log.error(f"Failed to load state: {e} — starting fresh")
        return deepcopy(_EMPTY_STATE)


def save(state: dict, state_file: Path):
    """Persist state to disk atomically."""
    tmp = state_file.with_suffix('.json.tmp')
    try:
        with open(tmp, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        tmp.replace(state_file)
        log.info(f"State saved: {len(state.get('positions', []))} positions")
    except Exception as e:
        log.error(f"Failed to save state: {e}")
        if tmp.exists():
            tmp.unlink()


def open_positions(state: dict) -> List[dict]:
    """Return positions with status 'open' or 'pending_entry'."""
    return [p for p in state.get('positions', [])
            if p.get('status') in ('open', 'pending_entry')]


def open_symbols(state: dict) -> set:
    return {p['symbol'] for p in open_positions(state)}


def get_position(state: dict, symbol: str) -> Optional[dict]:
    for p in state.get('positions', []):
        if p['symbol'] == symbol and p.get('status') in ('open', 'pending_entry'):
            return p
    return None


def add_position(state: dict, symbol: str, entry_date: str,
                 entry_price: float, shares: int, stop_price: float,
                 conviction: int, atr: float,
                 ib_entry_order_id: Optional[int],
                 ib_stop_order_id:  Optional[int]):
    """Add a new pending position to state."""
    pos = {
        'symbol':            symbol,
        'entry_date':        entry_date,
        'entry_price':       entry_price,
        'shares':            shares,
        'initial_stop':      stop_price,
        'stop_price':        stop_price,
        'conviction':        conviction,
        'atr_at_entry':      atr,
        'highest_close':     entry_price,
        'ib_entry_order_id': ib_entry_order_id,
        'ib_stop_order_id':  ib_stop_order_id,
        'status':            'pending_entry',  # becomes 'open' after MOO fills
    }
    state.setdefault('positions', []).append(pos)
    log.info(f"Position added to state: {symbol} {shares}sh @ {entry_price:.2f}  stop={stop_price:.2f}")


def update_stop(state: dict, symbol: str, new_stop: float, highest_close: float):
    """Update the trailing stop and highest close for a position."""
    pos = get_position(state, symbol)
    if pos:
        pos['stop_price']    = new_stop
        pos['highest_close'] = highest_close


def confirm_entry(state: dict, symbol: str):
    """Mark a pending_entry position as open (called after MOO order confirms)."""
    pos = get_position(state, symbol)
    if pos and pos['status'] == 'pending_entry':
        pos['status'] = 'open'


def remove_position(state: dict, symbol: str):
    """Remove a position from state (after exit fills)."""
    before = len(state.get('positions', []))
    state['positions'] = [p for p in state.get('positions', [])
                          if not (p['symbol'] == symbol
                                  and p.get('status') in ('open', 'pending_entry', 'pending_exit'))]
    after = len(state.get('positions', []))
    if before != after:
        log.info(f"Position removed from state: {symbol}")


def needs_rebalance(state: dict, today: str, interval_days: int = 88) -> bool:
    """Return True if a quarterly fundamental rebalance is due."""
    last = state.get('last_rebalance_date')
    if not last:
        return True
    from datetime import datetime
    last_dt  = datetime.strptime(last,  '%Y-%m-%d').date()
    today_dt = datetime.strptime(today, '%Y-%m-%d').date()
    return (today_dt - last_dt).days >= interval_days
