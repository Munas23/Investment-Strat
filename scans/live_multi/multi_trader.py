"""
Multi-System Paper Trader — Orchestrator

Runs the bake-off's Phase-2 advancement winners (Qullamaggie, Hybrid Balanced)
concurrently against ONE Interactive Brokers paper account. The expensive
shared work (price download, market-health check, quarterly fundamental screen)
is done ONCE, then each system runs its own scan / sizing / exit / order logic
and keeps its own state file.

Usage:
    python multi_trader.py --dry-run     # logic only, no IB, no orders
    python multi_trader.py               # one live pass now (paper account)
    python multi_trader.py --schedule    # run every weekday at DAILY_RUN_TIME
    python multi_trader.py --status       # print all systems' positions and exit
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

# Python 3.10+ no longer auto-creates an event loop — ib_insync needs one
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import pandas as pd

# Make sibling backtesting package importable
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'backtesting'))

import config
import systems as systems_mod
import system_runner
from utils.technical_scanner import get_market_health
from utils.historical_screener import HistoricalScreener
from backtest_engine import BacktestEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

SHARED_META_FILE = config.STATE_DIR / 'shared_meta.json'


# ---------------------------------------------------------------------------
# Universe loading
# ---------------------------------------------------------------------------

def load_universe() -> list:
    symbols = set()
    for fpath in (config.RUSSELL1000_FILE, config.SP500_FILE):
        if fpath.exists():
            df = pd.read_csv(fpath)
            col = df.columns[0]
            raw = df[col].dropna().astype(str).tolist()
            symbols.update(s.strip() for s in raw
                           if s and (not s.startswith('X') or len(s) <= 4))
    return sorted(symbols)


def download_prices(symbols: list):
    end_dt = datetime.today()
    start_dt = pd.Timestamp(end_dt) - pd.Timedelta(days=config.PRICE_LOOKBACK_DAYS)
    log.info(f"Downloading prices for {len(symbols)} symbols "
             f"({start_dt.date()} -> {end_dt.date()})...")

    screener = HistoricalScreener(symbols)
    screener._prefetch_all_data(
        start_date=start_dt.strftime('%Y-%m-%d'),
        end_date=end_dt.strftime('%Y-%m-%d'),
    )
    engine = BacktestEngine(account_size=1,
                            start_date=start_dt.strftime('%Y-%m-%d'),
                            end_date=end_dt.strftime('%Y-%m-%d'))
    price_data = {}
    for sym, raw_df in screener._price_cache.items():
        enriched = engine.enrich_cached_data(sym, raw_df)
        if enriched is not None:
            price_data[sym] = enriched
    log.info(f"Price data ready for {len(price_data)} symbols")
    return price_data, screener


# ---------------------------------------------------------------------------
# Shared quarterly fundamental screen (identical gate for all systems)
# ---------------------------------------------------------------------------

def _load_meta() -> dict:
    if SHARED_META_FILE.exists():
        try:
            return json.loads(SHARED_META_FILE.read_text())
        except Exception:
            pass
    return {'last_rebalance_date': None, 'quarterly_universe': []}


def _save_meta(meta: dict):
    SHARED_META_FILE.write_text(json.dumps(meta, indent=2, default=str))


def _needs_rebalance(last: str, today: str, interval_days: int = 88) -> bool:
    if not last:
        return True
    last_dt = datetime.strptime(last, '%Y-%m-%d').date()
    today_dt = datetime.strptime(today, '%Y-%m-%d').date()
    return (today_dt - last_dt).days >= interval_days


def get_fundamental_universe(screener, today_ts: pd.Timestamp) -> list:
    today_str = today_ts.strftime('%Y-%m-%d')
    meta = _load_meta()
    if _needs_rebalance(meta.get('last_rebalance_date'), today_str):
        log.info("Running shared quarterly fundamental screen...")
        screen_start = (today_ts - pd.Timedelta(days=400)).strftime('%Y-%m-%d')
        quarterly = screener.run_quarterly_screening(
            start_date=screen_start, end_date=today_str, rebalance_frequency='Q')
        universe = screener.get_universe_for_date(today_ts, quarterly)
        meta['quarterly_universe'] = universe
        meta['last_rebalance_date'] = today_str
        _save_meta(meta)
        log.info(f"Fundamental screen: {len(universe)} qualifying stocks")
    else:
        universe = meta.get('quarterly_universe', [])
        log.info(f"Using cached fundamental universe: {len(universe)} stocks")
    return universe


# ---------------------------------------------------------------------------
# Safety check on IB port
# ---------------------------------------------------------------------------

PAPER_PORTS = {7497, 4002}

def _check_port():
    if config.IB_PORT not in PAPER_PORTS and not config.ALLOW_LIVE_PORT:
        raise SystemExit(
            f"Refusing to connect: IB_PORT={config.IB_PORT} is not a known paper "
            f"port {PAPER_PORTS}. Set ALLOW_LIVE_PORT=True in config.py to override."
        )


# ---------------------------------------------------------------------------
# Combined report
# ---------------------------------------------------------------------------

def print_report(results: list, market_health: str, account_value: float):
    today = datetime.now().strftime('%Y-%m-%d')
    log.info("")
    log.info("=" * 74)
    log.info(f"  MULTI-SYSTEM DAILY REPORT  {today}  |  Account: ${account_value:,.0f}")
    log.info(f"  Market: {market_health.upper()}  |  Capital model: {config.CAPITAL_MODEL}")
    log.info("=" * 74)
    for r in results:
        s = r['system']
        log.info(f"\n  ── {s.name}  (id {s.system_id}, ref {s.order_ref}) ──")
        log.info(f"     Open: {len(r['open'])}/{s.max_positions}")
        for p in r['open']:
            log.info(f"       {p['symbol']:<6} {p['shares']}sh  entry={p['entry_price']:.2f}"
                     f"  stop={p['stop_price']:.2f}  conv={p['conviction']}  [{p['status']}]")
        if r['exits']:
            log.info(f"     Exits: " + ", ".join(f"{sym}({why})" for sym, why in r['exits']))
        if r['entries']:
            log.info(f"     New entries: "
                     + ", ".join(f"{sym} {sh}sh@{px:.2f}(c{c})"
                                 for sym, sh, px, c in r['entries']))
        else:
            log.info("     New entries: none")
    log.info("\n" + "=" * 74 + "\n")


# ---------------------------------------------------------------------------
# Core daily pass
# ---------------------------------------------------------------------------

def run_daily(dry_run: bool = False):
    today_str = date.today().strftime('%Y-%m-%d')
    today_ts = pd.Timestamp(today_str)
    active = systems_mod.active_systems()
    log.info(f"--- Multi-trader starting {today_str}  dry_run={dry_run}  "
             f"systems={[s.tag for s in active]} ---")

    # 1. Connect once (shared connection)
    ib = None
    if not dry_run:
        _check_port()
        from ib_connector import IBConnector
        ib = IBConnector(config.IB_HOST, config.IB_PORT, config.IB_CLIENT_ID)
        if not ib.connect():
            log.error("Cannot connect to IB TWS/Gateway. Is it running with API enabled?")
            return
        account_value = ib.get_account_value()
        log.info(f"Account value: ${account_value:,.0f}")
    else:
        account_value = 100_000.0
        log.info(f"[DRY RUN] dummy account value ${account_value:,.0f}")

    # 2. Shared price download
    universe_all = load_universe()
    if not universe_all:
        log.error("Universe symbol files not found — check config.IVV_FILE / IJR_FILE.")
        if ib:
            ib.disconnect()
        return
    price_data, screener = download_prices(universe_all)
    if not price_data:
        log.error("No price data available. Aborting.")
        if ib:
            ib.disconnect()
        return

    # 3. Market health (shared)
    spy_df = price_data.get('SPY')
    market_health = get_market_health(spy_df, today_ts) if spy_df is not None else 'neutral'
    log.info(f"Market health: {market_health.upper()}")

    # 4. Shared fundamental universe
    fundamental_universe = get_fundamental_universe(screener, today_ts)

    # 5. Per-system capital
    if config.CAPITAL_MODEL == 'split_equity':
        per_system_equity = account_value / len(active)
    else:
        per_system_equity = account_value   # full_equity

    # 6. Run each system
    results = []
    for system in active:
        log.info(f"\n>>> Running system: {system.name} ({system.tag})")
        results.append(system_runner.run_system(
            system=system,
            price_data=price_data,
            fundamental_universe=fundamental_universe,
            account_value=per_system_equity,
            market_health=market_health,
            today_ts=today_ts,
            ib=ib,
            dry_run=dry_run,
        ))

    # 7. Report
    print_report(results, market_health, account_value)

    if ib:
        ib.disconnect()


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def print_status():
    import position_state as ps
    print("\nMulti-System Paper Trader — Status")
    print("=" * 60)
    for system in systems_mod.active_systems():
        state = ps.load(system.state_file, system.system_id, system.name)
        positions = ps.open_positions(state)
        print(f"\n{system.name}  (id {system.system_id})  "
              f"last run: {state.get('last_run_date', 'never')}")
        print(f"  Open: {len(positions)}/{system.max_positions}")
        for p in positions:
            print(f"    {p['symbol']:<6} {p['shares']}sh  entry={p['entry_price']:.2f}"
                  f"  stop={p['stop_price']:.2f}  conv={p['conviction']}  [{p['status']}]")
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

    rt = config.DAILY_RUN_TIME
    log.info(f"Scheduler started — running every weekday at {rt}")
    for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday'):
        getattr(schedule.every(), day).at(rt).do(run_daily, dry_run=dry_run)

    log.info("Running an initial pass now...")
    run_daily(dry_run=dry_run)
    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description='Multi-system paper trader (IB)')
    parser.add_argument('--schedule', action='store_true',
                        help=f'Stay running, trigger weekdays at {config.DAILY_RUN_TIME}')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run logic but do not connect to IB or place orders')
    parser.add_argument('--status', action='store_true',
                        help='Print all systems\' positions and exit')
    args = parser.parse_args()

    if args.status:
        print_status()
    elif args.schedule:
        run_scheduled(dry_run=args.dry_run)
    else:
        run_daily(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
