"""
EOD Data Pipeline (Phase 4 scaffold)

Daily end-of-day price downloader/store for all configured universes.
Runs on Ash's machine where Yahoo Finance is reachable (the Cowork sandbox
cannot reach yfinance). Designed to be idempotent and resumable: it only
fetches the gap between the last stored bar and today.

Store layout:
    backtesting/eod_store/
        prices/<SYMBOL>.parquet     # full OHLCV history per symbol
        manifest.json               # {symbol: last_date} + last run metadata

Usage:
    python eod_pipeline.py --universes sp500 russell1000 nasdaq100
    python eod_pipeline.py --all                 # every universe in run_backtest.UNIVERSES
    python eod_pipeline.py --all --full          # ignore store, re-download full history
    python eod_pipeline.py --universes asx300 --since 2020-01-01

Schedule (cron, after US close ~21:30 ET):
    30 22 * * 1-5  cd /path/to/scans/backtesting && python eod_pipeline.py --all
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

HERE = Path(__file__).parent
DATA_DIR = HERE.parent.parent / 'backtesting' / 'data'
STORE_DIR = HERE / 'eod_store'
PRICE_DIR = STORE_DIR / 'prices'
MANIFEST = STORE_DIR / 'manifest.json'

# Universe -> symbol CSV (mirrors run_backtest.UNIVERSES)
UNIVERSE_FILES = {
    'sp500':       'sp500_symbols.csv',
    'russell1000': 'russell1000_symbols.csv',
    'nasdaq100':   'nasdaq100_symbols.csv',
    'asx300':      'asx300_symbols.csv',
    'ftse100':     'ftse100_symbols.csv',
}
DEFAULT_HISTORY_START = '2018-01-01'   # first pull goes back this far


def load_symbols(universe: str) -> List[str]:
    fpath = DATA_DIR / UNIVERSE_FILES[universe]
    if not fpath.exists():
        print(f"  WARN: {fpath} not found — skipping {universe}")
        return []
    df = pd.read_csv(fpath)
    col = df.columns[0]
    return [str(s).strip() for s in df[col].dropna() if str(s).strip()]


def load_manifest() -> Dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text())
        except Exception:
            pass
    return {'symbols': {}, 'last_run': None}


def save_manifest(manifest: Dict) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    manifest['last_run'] = datetime.now().isoformat(timespec='seconds')
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df.dropna(subset=['close']) if 'close' in df.columns else df


def update_symbol(symbol: str, manifest: Dict, full: bool, since: str) -> str:
    """Fetch the gap for one symbol and merge into its parquet. Returns status."""
    pfile = PRICE_DIR / f"{symbol}.parquet"
    existing = None
    start = since or DEFAULT_HISTORY_START

    if pfile.exists() and not full:
        try:
            existing = pd.read_parquet(pfile)
            last = pd.to_datetime(existing.index.max())
            if last.date() >= (datetime.now().date() - timedelta(days=1)):
                return 'up-to-date'
            start = (last + timedelta(days=1)).strftime('%Y-%m-%d')
        except Exception:
            existing = None

    raw = yf.download(symbol, start=start, auto_adjust=True,
                      progress=False, threads=False)
    if raw is None or raw.empty:
        return 'no-data'
    new = _clean(raw)

    combined = new if existing is None else pd.concat([existing, new])
    combined = combined[~combined.index.duplicated(keep='last')].sort_index()

    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(pfile)
    manifest['symbols'][symbol] = str(combined.index.max().date())
    return 'ok'


def run(universes: List[str], full: bool, since: str) -> None:
    if yf is None:
        sys.exit("yfinance not installed. `pip install yfinance` and run on a "
                 "machine with Yahoo Finance access (not the Cowork sandbox).")

    manifest = load_manifest()
    symbols: List[str] = []
    for u in universes:
        s = load_symbols(u)
        print(f"{u}: {len(s)} symbols")
        symbols.extend(s)
    symbols = sorted(set(symbols))
    print(f"\nUpdating {len(symbols)} unique symbols "
          f"(full={full}, since={since or DEFAULT_HISTORY_START})\n")

    counts: Dict[str, int] = {}
    for i, sym in enumerate(symbols, 1):
        try:
            status = update_symbol(sym, manifest, full, since)
        except Exception as e:
            status = f'error:{type(e).__name__}'
        counts[status.split(':')[0]] = counts.get(status.split(':')[0], 0) + 1
        if i % 25 == 0 or i == len(symbols):
            print(f"  [{i}/{len(symbols)}] {dict(counts)}")
        save_manifest(manifest)   # checkpoint each symbol -> resumable

    print(f"\nDone. {dict(counts)}")
    print(f"Store: {PRICE_DIR}")


def main() -> None:
    ap = argparse.ArgumentParser(description="EOD price pipeline")
    ap.add_argument('--universes', nargs='+', choices=list(UNIVERSE_FILES),
                    help="universes to update")
    ap.add_argument('--all', action='store_true', help="update every universe")
    ap.add_argument('--full', action='store_true',
                    help="ignore the store and re-download full history")
    ap.add_argument('--since', default='', help="history start (YYYY-MM-DD)")
    args = ap.parse_args()

    universes = list(UNIVERSE_FILES) if args.all else (args.universes or [])
    if not universes:
        ap.error("specify --universes ... or --all")
    run(universes, args.full, args.since)


if __name__ == '__main__':
    main()
