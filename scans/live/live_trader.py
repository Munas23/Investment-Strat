"""
Live Trader — Daily Runner

Connects to IB TWS (paper or live), runs the daily scan, and manages orders.

Flow (runs once after market close each trading day):
  1. Connect to IB, get account value
  2. Load persisted position state
  3. Sync state with IB (confirm filled MOO entries, catch stop fills)
  4. Download EOD prices via yfinance
  5. Quarterly fundamental rebalance if due
  6. Check market health (SPY MAs)
  7. Update chandelier trailing stops for open positions
  8. Scan for new entry signals (skipped in bear market)
  9. Place orders in IB: stop updates + new MOO entries
 10. Save state, print daily report

Usage:
    python live_trader.py              # Run once now
    python live_trader.py --schedule   # Run daily at DAILY_RUN_TIME in config.py
    python live_trader.py --dry-run    # Simulate without placing any IB orders
    python live_trader.py --status     # Print current positions and exit
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, date
from pathlib import Path

# Python 3.10+ no longer auto-creates an event loop — ib_insync needs one
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import pandas as pd
import yfinance as yf

# Add parent to path so we can import from backtesting/
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'backtesting'))

from backtesting.utils.technical_scanner import scan_universe, get_market_health
from backtesting.utils.historical_screener import HistoricalScreener
from backtesting.backtest_engine import BacktestEngine

import config
import position_state as ps
from ib_connector import IBConnector

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Universe loading (same as run_backtest.py)
# ---------------------------------------------------------------------------

def load_universe() -> list:
    symbols = set()
    for fpath in (config.IVV_FILE, config.IJR_FILE):
        if fpath.exists():
            df  = pd.read_csv(fpath)
            col = df.columns[0]
            raw = df[col].dropna().astype(str).tolist()
            symbols.update(
                s.strip() for s in raw
                if s and (not s.startswith('X') or len(s) <= 4)
            )
    return sorted(symbols)


# ---------------------------------------------------------------------------
# Price data (yfinance EOD)
# ---------------------------------------------------------------------------

PRICE_LOOKBACK_DAYS = 400   # enough for 200-day MA + ATR history

def download_prices(symbols: list) -> dict:
    """
    Download EOD price history for all symbols via yfinance.
    Returns {symbol: enriched_df} reusing the backtesting cache where available.
    """
    end_dt   = datetime.today()
    start_dt = pd.Timestamp(end_dt) - pd.Timedelta(days=PRICE_LOOKBACK_DAYS)

    log.info(f"Downloading prices for {len(symbols)} symbols "
             f"({start_dt.date()} to {end_dt.date()})...")

    # Reuse backtesting screener cache infrastructure
    screener = HistoricalScreener(symbols)
    # This loads from disk cache and only downloads what's missing
    screener._prefetch_all_data(
        start_date=start_dt.strftime('%Y-%m-%d'),
        end_date=end_dt.strftime('%Y-%m-%d'),
    )

    # Enrich with ATR, MAs, RS using backtest engine helper
    engine     = BacktestEngine(account_size=1, start_date=start_dt.strftime('%Y-%m-%d'),
                                end_date=end_dt.strftime('%Y-%m-%d'))
    price_data = {}
    for sym, raw_df in screener._price_cache.items():
        enriched = engine.enrich_cached_data(sym, raw_df)
        if enriched is not None:
            price_data[sym] = enriched

    log.info(f"Price data ready for {len(price_data)} symbols")
    return price_data, screener


# ---------------------------------------------------------------------------
# Position sizing (System 2 Turtle)
# ---------------------------------------------------------------------------

def calc_position(account_value: float, entry_price: float,
                  atr: float, conviction: int) -> tuple:
    """
    Returns (shares, stop_price, position_value).
    Uses ATR-based stop and risk-percent position sizing.
    """
    mult      = config.CONVICTION_MULTIPLIERS.get(conviction, 1.0)
    atr_mult  = config.ATR_MULTIPLIERS.get(conviction, 2.5)

    stop_price  = entry_price - atr_mult * atr
    stop_dist   = entry_price - stop_price
    if stop_dist <= 0:
        return 0, stop_price, 0

    dollar_risk = account_value * (config.BASE_RISK_PCT / 100) * mult
    shares      = int(dollar_risk / stop_dist)

    # Cap position size
    max_value = account_value * (config.MAX_POS_SIZE_PCT / 100)
    if shares * entry_price > max_value:
        shares = int(max_value / entry_price)

    return shares, round(stop_price, 2), shares * entry_price


# ---------------------------------------------------------------------------
# Trailing stop update
# ---------------------------------------------------------------------------

def calc_chandelier_stop(pos: dict, price_data: dict, today: pd.Timestamp) -> float:
    """
    Chandelier trailing stop: highest_close_since_entry - CHANDELIER_ATR_MULT × ATR.
    Returns the new stop price (never lower than the initial stop).
    """
    symbol = pos['symbol']
    df     = price_data.get(symbol)
    if df is None:
        return pos['stop_price']

    entry_dt = pd.Timestamp(pos['entry_date'])
    since    = df.loc[(df.index >= entry_dt) & (df.index <= today)]
    if since.empty:
        return pos['stop_price']

    highest_close = since['close'].max()
    current_atr   = df.loc[df.index <= today, 'atr'].iloc[-1]
    if pd.isna(current_atr) or current_atr <= 0:
        return pos['stop_price']

    chandelier = highest_close - config.CHANDELIER_ATR_MULT * current_atr
    # Only ever raise the stop, never lower it
    new_stop = max(chandelier, pos['initial_stop'])
    return round(new_stop, 2), highest_close


# ---------------------------------------------------------------------------
# State / IB reconciliation
# ---------------------------------------------------------------------------

def reconcile_with_ib(state: dict, ib: IBConnector):
    """
    Cross-check our state against IB's actual positions.
    - pending_entry positions: if IB now shows shares, mark as 'open'
    - open positions: if IB shows zero shares (stop filled), remove from state
    """
    ib_positions = ib.get_positions()   # {symbol: shares}

    for pos in list(state.get('positions', [])):
        sym    = pos['symbol']
        status = pos.get('status')

        if status == 'pending_entry':
            if ib_positions.get(sym, 0) >= pos['shares']:
                log.info(f"MOO entry confirmed by IB: {sym}")
                pos['status'] = 'open'
            # else: still waiting (could be pre-open or rejected)

        elif status == 'open':
            if ib_positions.get(sym, 0) == 0:
                log.info(f"IB shows zero shares for {sym} — stop order likely filled, removing from state")
                ps.remove_position(state, sym)


# ---------------------------------------------------------------------------
# Daily report
# ---------------------------------------------------------------------------

def print_report(state: dict, market_health: str, exits: list,
                 entries: list, account_value: float):
    today = datetime.now().strftime('%Y-%m-%d')
    log.info("")
    log.info("=" * 70)
    log.info(f"  DAILY REPORT  {today}  |  Account: ${account_value:,.0f}")
    log.info(f"  Market: {market_health.upper()}")
    log.info("=" * 70)

    positions = ps.open_positions(state)
    log.info(f"  Open positions: {len(positions)} / {config.MAX_POSITIONS}")
    for p in positions:
        log.info(f"    {p['symbol']:<6}  {p['shares']}sh  entry={p['entry_price']:.2f}"
                 f"  stop={p['stop_price']:.2f}  [{p['status']}]")

    if exits:
        log.info(f"\n  Exits triggered today ({len(exits)}):")
        for sym, reason in exits:
            log.info(f"    {sym:<6}  {reason}")

    if entries:
        log.info(f"\n  New entries submitted ({len(entries)}):")
        for sym, shares, price, conviction in entries:
            log.info(f"    {sym:<6}  {shares}sh  ~${price:.2f}  conviction={conviction}")
    else:
        log.info(f"\n  No new entries today")

    log.info("=" * 70)
    log.info("")


# ---------------------------------------------------------------------------
# Core daily logic
# ---------------------------------------------------------------------------

def run_daily(dry_run: bool = False):
    today_str = date.today().strftime('%Y-%m-%d')
    today_ts  = pd.Timestamp(today_str)
    log.info(f"--- Live trader starting  {today_str}  dry_run={dry_run} ---")

    # ── 1. Connect to IB ──────────────────────────────────────────────────
    ib = IBConnector(config.IB_HOST, config.IB_PORT, config.IB_CLIENT_ID)
    if not dry_run:
        if not ib.connect():
            log.error("Cannot connect to IB TWS. Is TWS running with API enabled?")
            return

    # ── 2. Account value ──────────────────────────────────────────────────
    if dry_run:
        account_value = 100_000.0
        log.info(f"[DRY RUN] Using dummy account value: ${account_value:,.0f}")
    else:
        account_value = ib.get_account_value()
        log.info(f"Account value: ${account_value:,.0f}")

    # ── 3. Load state ─────────────────────────────────────────────────────
    state = ps.load(config.STATE_FILE)

    # ── 4. Reconcile with IB (confirm MOO fills, catch stop fills) ────────
    if not dry_run:
        reconcile_with_ib(state, ib)

    # ── 5. Download prices ────────────────────────────────────────────────
    universe_all = load_universe()
    price_data, screener = download_prices(universe_all)

    if not price_data:
        log.error("No price data available. Aborting.")
        ib.disconnect()
        return

    spy_df = price_data.get('SPY')

    # ── 6. Quarterly fundamental rebalance ────────────────────────────────
    if ps.needs_rebalance(state, today_str):
        log.info("Running quarterly fundamental screen...")
        # Run screening from 1 year back so we get the current quarter
        screen_start = (today_ts - pd.Timedelta(days=400)).strftime('%Y-%m-%d')
        quarterly_universe = screener.run_quarterly_screening(
            start_date=screen_start,
            end_date=today_str,
            rebalance_frequency='Q',
        )
        current_universe = screener.get_universe_for_date(today_ts, quarterly_universe)
        state['quarterly_universe']  = current_universe
        state['last_rebalance_date'] = today_str
        log.info(f"Fundamental screen: {len(current_universe)} qualifying stocks")
    else:
        current_universe = state.get('quarterly_universe', [])
        log.info(f"Using cached universe: {len(current_universe)} stocks "
                 f"(next rebalance in "
                 f"{88 - (today_ts - pd.Timestamp(state['last_rebalance_date'])).days} days)")

    if not current_universe:
        log.warning("Fundamental universe is empty — no entries possible today")

    # ── 7. Market health ──────────────────────────────────────────────────
    if spy_df is not None:
        market_health = get_market_health(spy_df, today_ts)
    else:
        market_health = 'neutral'
    log.info(f"Market health: {market_health.upper()}")

    # ── 8. Exit management ────────────────────────────────────────────────
    exits = []
    for pos in list(ps.open_positions(state)):
        sym    = pos['symbol']
        df     = price_data.get(sym)
        if df is None:
            continue

        available = df.index[df.index <= today_ts]
        if available.empty:
            continue
        current_price = df.loc[available[-1], 'close']

        # Update chandelier trailing stop
        result = calc_chandelier_stop(pos, price_data, today_ts)
        if isinstance(result, tuple):
            new_stop, highest_close = result
        else:
            new_stop, highest_close = result, pos['highest_close']

        stop_raised = new_stop > pos['stop_price']

        # Update IB stop order if stop moved up
        if stop_raised and not dry_run:
            stop_oid = pos.get('ib_stop_order_id')
            if stop_oid:
                ib.update_stop_order(stop_oid, sym, pos['shares'], new_stop)
            pos['stop_price']    = new_stop
            pos['highest_close'] = highest_close

        # Check if price is below stop (intraday stop may have already fired in IB,
        # but we also check EOD price to clean up state)
        if current_price <= pos['stop_price']:
            log.info(f"Exit signal: {sym}  price={current_price:.2f} <= stop={pos['stop_price']:.2f}")
            if not dry_run:
                # Cancel the IB stop order (it may have already filled — ib handles duplicates)
                stop_oid = pos.get('ib_stop_order_id')
                if stop_oid:
                    ib.cancel_order(stop_oid, sym)
                # Place market sell for any remaining shares
                ib.place_market_sell(sym, pos['shares'])
            exits.append((sym, 'CHANDELIER_STOP'))
            ps.remove_position(state, sym)

    # ── 9. Entry signals ──────────────────────────────────────────────────
    entries = []
    open_syms   = ps.open_symbols(state)
    open_count  = len(open_syms)
    slots_avail = config.MAX_POSITIONS - open_count

    skip_entries = (config.SKIP_ENTRIES_IN_BEAR and market_health == 'bear')
    if skip_entries:
        log.info("Bear market — skipping new entries")

    if not skip_entries and slots_avail > 0 and current_universe:
        signals = scan_universe(
            universe      = current_universe,
            price_data    = price_data,
            date          = today_ts,
            system_id     = config.SYSTEM_ID,
            min_conviction= config.MIN_CONVICTION,
            market_health = market_health,
        )

        entered_today = 0
        for symbol, conviction in sorted(signals.items(), key=lambda x: x[1], reverse=True):
            if entered_today >= config.MAX_ENTRIES_PER_DAY:
                break
            if open_count >= config.MAX_POSITIONS:
                break
            if symbol in open_syms:
                continue   # already in this position

            df = price_data.get(symbol)
            if df is None:
                continue

            available = df.index[df.index <= today_ts]
            if available.empty:
                continue

            entry_price = df.loc[available[-1], 'close']
            atr         = df.loc[available[-1], 'atr']
            if pd.isna(atr) or atr <= 0:
                continue

            shares, stop_price, position_value = calc_position(
                account_value, entry_price, atr, conviction)
            if shares <= 0:
                continue

            log.info(f"Entry signal: {symbol}  conviction={conviction}  "
                     f"{shares}sh @ ~{entry_price:.2f}  stop={stop_price:.2f}  "
                     f"value=${position_value:,.0f}")

            entry_oid = stop_oid = None
            if not dry_run:
                # Place MOO order for next morning
                entry_oid = ib.place_entry_order(symbol, shares)
                # Place GTC stop order immediately (protects even if script is offline)
                stop_oid  = ib.place_stop_order(symbol, shares, stop_price)

            ps.add_position(
                state, symbol, today_str, entry_price, shares,
                stop_price, conviction, float(atr),
                entry_oid, stop_oid,
            )

            entries.append((symbol, shares, entry_price, conviction))
            open_syms.add(symbol)
            open_count  += 1
            entered_today += 1

    # ── 10. Save state ────────────────────────────────────────────────────
    state['last_run_date'] = today_str
    ps.save(state, config.STATE_FILE)

    # ── 11. Report ────────────────────────────────────────────────────────
    print_report(state, market_health, exits, entries, account_value)

    if not dry_run:
        ib.disconnect()


# ---------------------------------------------------------------------------
# Status-only mode
# ---------------------------------------------------------------------------

def print_status():
    state = ps.load(config.STATE_FILE)
    positions = ps.open_positions(state)
    print(f"\nLive Trader Status  ({state.get('last_run_date', 'never run')})")
    print(f"Market universe: {len(state.get('quarterly_universe', []))} stocks  "
          f"(last rebalance: {state.get('last_rebalance_date', 'never')})")
    print(f"Open positions: {len(positions)} / {config.MAX_POSITIONS}")
    print("-" * 60)
    for p in positions:
        print(f"  {p['symbol']:<6}  {p['shares']}sh  "
              f"entry={p['entry_price']:.2f}  stop={p['stop_price']:.2f}  "
              f"conviction={p['conviction']}  [{p['status']}]")
    print()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def run_scheduled(dry_run: bool):
    try:
        import schedule
        import time
    except ImportError:
        print("ERROR: 'schedule' not installed. Run: pip install schedule")
        sys.exit(1)

    run_time = config.DAILY_RUN_TIME
    log.info(f"Scheduler started — will run daily at {run_time}")
    schedule.every().monday.at(run_time).do(run_daily, dry_run=dry_run)
    schedule.every().tuesday.at(run_time).do(run_daily, dry_run=dry_run)
    schedule.every().wednesday.at(run_time).do(run_daily, dry_run=dry_run)
    schedule.every().thursday.at(run_time).do(run_daily, dry_run=dry_run)
    schedule.every().friday.at(run_time).do(run_daily, dry_run=dry_run)

    log.info("Running initial scan now...")
    run_daily(dry_run=dry_run)

    while True:
        schedule.run_pending()
        time.sleep(30)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Live Trader — Daily runner for IB paper/live')
    parser.add_argument('--schedule', action='store_true',
                        help=f'Stay running and trigger at {config.DAILY_RUN_TIME} each weekday')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run logic but do not connect to IB or place orders')
    parser.add_argument('--status', action='store_true',
                        help='Print current positions from state file and exit')
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.schedule:
        run_scheduled(dry_run=args.dry_run)
    else:
        run_daily(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
