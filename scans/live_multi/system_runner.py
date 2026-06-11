"""
Per-system daily runner.

Given a SystemConfig, a (shared) price_data dict, a fundamental universe,
the account value and market health, this runs ONE system's daily cycle:

  1. Reconcile this system's own orders (entry fills, stop fills) — by orderId,
     NOT by net account position (which is summed across systems).
  2. Update trailing stops on open positions.
  3. Scan for new entries (skipped in a bear market).
  4. Place orders in IB (tagged with the system's orderRef).
  5. Persist this system's state.

Stop methods supported:
  * 'atr'        — initial stop = entry - atr_mult x ATR; trail = chandelier.
  * 'percentage' — initial stop = entry x (1 - stop_percent/100);
                   trail = highest_close x (1 - stop_percent/100).
Stops only ever ratchet UP, never down.
"""

import logging
from typing import Optional, Tuple

import pandas as pd

import config
import position_state as ps
from systems import SystemConfig

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'backtesting'))
from utils.technical_scanner import scan_universe   # noqa: E402

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sizing & stops
# ---------------------------------------------------------------------------

def _initial_stop(system: SystemConfig, entry_price: float, atr: float,
                  conviction: int) -> Optional[float]:
    if system.stop_method in ('atr', 'atr_with_cap'):
        atr_mult = (system.atr_multipliers or {}).get(conviction, 2.5)
        stop = entry_price - atr_mult * atr
        if system.stop_method == 'atr_with_cap' and system.stop_cap_pct:
            cap_pct = system.stop_cap_pct.get(conviction, 8.0) / 100.0
            stop_cap = entry_price * (1.0 - cap_pct)
            stop = max(stop, stop_cap)   # use the tighter (higher) of the two
    elif system.stop_method == 'percentage':
        stop = entry_price * (1 - (system.stop_percent or 7.0) / 100.0)
    else:
        stop = entry_price - 2.5 * atr   # safe fallback
    return round(stop, 2) if stop > 0 else None


def calc_position(system: SystemConfig, account_value: float, entry_price: float,
                  atr: float, conviction: int) -> Tuple[int, Optional[float], float]:
    """Returns (shares, stop_price, position_value)."""
    stop_price = _initial_stop(system, entry_price, atr, conviction)
    if stop_price is None:
        return 0, None, 0.0
    stop_dist = entry_price - stop_price
    if stop_dist <= 0:
        return 0, stop_price, 0.0

    mult = system.conviction_multipliers.get(conviction, 1.0)
    dollar_risk = account_value * (system.base_risk / 100.0) * mult
    shares = int(dollar_risk / stop_dist)

    # Cap any single position so all max_positions slots can co-exist.
    max_pos_pct = 100.0 / system.max_positions
    max_value = account_value * (max_pos_pct / 100.0)
    if shares * entry_price > max_value:
        shares = int(max_value / entry_price)

    return shares, stop_price, shares * entry_price


def _trailing_stop(system: SystemConfig, pos: dict, df: pd.DataFrame,
                   today: pd.Timestamp) -> Tuple[float, float]:
    """Return (new_stop, highest_close). Only raises the stop."""
    entry_dt = pd.Timestamp(pos['entry_date'])
    since = df.loc[(df.index >= entry_dt) & (df.index <= today)]
    if since.empty:
        return pos['stop_price'], pos['highest_close']
    highest_close = float(since['close'].max())

    if system.stop_method == 'percentage':
        candidate = highest_close * (1 - (system.stop_percent or 7.0) / 100.0)
    else:
        # ATR chandelier — used by both 'atr' and 'atr_with_cap'
        atr_series = df.loc[df.index <= today, 'atr']
        current_atr = atr_series.iloc[-1] if not atr_series.empty else None
        if current_atr is None or pd.isna(current_atr) or current_atr <= 0:
            return pos['stop_price'], highest_close

        # time_trail: tighten chandelier multiplier after N holding days
        atr_mult = system.chandelier_atr_mult
        if system.time_trail_days is not None:
            holding_days = (today - entry_dt).days
            if holding_days >= system.time_trail_days:
                atr_mult = system.time_trail_tight_mult

        candidate = highest_close - atr_mult * current_atr

    new_stop = max(candidate, pos['initial_stop'], pos['stop_price'])
    return round(new_stop, 2), highest_close


# ---------------------------------------------------------------------------
# Reconciliation (per-system, by orderId)
# ---------------------------------------------------------------------------

def reconcile(state: dict, system: SystemConfig, ib, dry_run: bool):
    if dry_run or ib is None:
        return
    for pos in list(state.get('positions', [])):
        sym = pos['symbol']
        status = pos.get('status')

        if status == 'pending_entry':
            oid = pos.get('ib_entry_order_id')
            fill = ib.get_fill(oid) if oid else None
            if fill:
                pos['status'] = 'open'
                pos['shares'] = fill['shares'] or pos['shares']
                if fill['avg_price']:
                    pos['entry_price'] = fill['avg_price']
                log.info(f"[{system.tag}] Entry filled: {sym} "
                         f"{pos['shares']}sh @ {pos['entry_price']:.2f}")

        elif status == 'open':
            stop_oid = pos.get('ib_stop_order_id')
            st = ib.get_order_status(stop_oid) if stop_oid else None
            if st == 'Filled':
                log.info(f"[{system.tag}] Stop filled: {sym} — closing in state")
                ps.remove_position(state, sym)


# ---------------------------------------------------------------------------
# Daily cycle for one system
# ---------------------------------------------------------------------------

def run_system(system: SystemConfig, price_data: dict, fundamental_universe: list,
               account_value: float, market_health: str, today_ts: pd.Timestamp,
               ib=None, dry_run: bool = False) -> dict:
    """Run one system's daily cycle. Returns a summary dict for the report."""
    today_str = today_ts.strftime('%Y-%m-%d')
    state = ps.load(system.state_file, system.system_id, system.name)
    state['system_name'] = system.name

    reconcile(state, system, ib, dry_run)

    exits, entries = [], []

    # ── Exit management / trailing stops ──────────────────────────────────
    for pos in list(ps.open_positions(state)):
        sym = pos['symbol']
        df = price_data.get(sym)
        if df is None:
            continue
        avail = df.index[df.index <= today_ts]
        if avail.empty:
            continue
        current_price = float(df.loc[avail[-1], 'close'])

        new_stop, highest_close = _trailing_stop(system, pos, df, today_ts)
        if new_stop > pos['stop_price']:
            if not dry_run and ib is not None and pos.get('ib_stop_order_id'):
                ib.update_stop_order(pos['ib_stop_order_id'], sym, pos['shares'],
                                     new_stop, system.order_ref)
            pos['stop_price'] = new_stop
        pos['highest_close'] = max(pos['highest_close'], highest_close)

        # EOD stop check (intraday GTC stop in IB may already have fired)
        if current_price <= pos['stop_price']:
            log.info(f"[{system.tag}] Exit: {sym} {current_price:.2f} <= stop {pos['stop_price']:.2f}")
            if not dry_run and ib is not None:
                if pos.get('ib_stop_order_id'):
                    ib.cancel_order(pos['ib_stop_order_id'], sym, system.order_ref)
                ib.place_market_sell(sym, pos['shares'], system.order_ref)
            exits.append((sym, 'STOP'))
            ps.remove_position(state, sym)

    # ── Entry signals ─────────────────────────────────────────────────────
    open_syms = ps.open_symbols(state)
    slots = system.max_positions - len(open_syms)
    skip = config.SKIP_ENTRIES_IN_BEAR and market_health == 'bear'

    if skip:
        log.info(f"[{system.tag}] Bear market — no new entries")
    elif slots > 0 and fundamental_universe:
        signals = scan_universe(
            universe=fundamental_universe,
            price_data=price_data,
            date=today_ts,
            system_id=system.system_id,
            min_conviction=system.min_conviction,
            market_health=market_health,
        )
        entered = 0
        for sym, conviction in sorted(signals.items(), key=lambda x: x[1], reverse=True):
            if entered >= system.max_entries_per_day or len(open_syms) >= system.max_positions:
                break
            if sym in open_syms:
                continue
            df = price_data.get(sym)
            if df is None:
                continue
            avail = df.index[df.index <= today_ts]
            if avail.empty:
                continue
            entry_price = float(df.loc[avail[-1], 'close'])
            atr = df.loc[avail[-1], 'atr']
            if pd.isna(atr) or atr <= 0:
                continue

            shares, stop_price, value = calc_position(
                system, account_value, entry_price, float(atr), conviction)
            if shares <= 0 or stop_price is None:
                continue

            log.info(f"[{system.tag}] Entry signal: {sym} conv={conviction} "
                     f"{shares}sh @ ~{entry_price:.2f} stop={stop_price:.2f} (${value:,.0f})")

            entry_oid = stop_oid = None
            if not dry_run and ib is not None:
                entry_oid = ib.place_entry_order(sym, shares, system.order_ref)
                stop_oid = ib.place_stop_order(sym, shares, stop_price, system.order_ref)

            ps.add_position(state, sym, today_str, entry_price, shares, stop_price,
                            conviction, float(atr), entry_oid, stop_oid)
            entries.append((sym, shares, entry_price, conviction))
            open_syms.add(sym)
            entered += 1

    # ── Persist ───────────────────────────────────────────────────────────
    state['last_run_date'] = today_str
    ps.save(state, system.state_file)

    return {
        'system': system,
        'open': ps.open_positions(state),
        'exits': exits,
        'entries': entries,
    }
