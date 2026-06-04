"""
Fetch current index constituent lists and write them to CSV files.
Run once to populate; re-run after index rebalances (March / September for ASX).

Sources:
  S&P 500      -GitHub datasets project (raw CSV, no auth required)
  NASDAQ 100   -Wikipedia via pandas read_html + browser UA
  FTSE 100     -Wikipedia via pandas read_html + browser UA
  Russell 1000 -iShares IWB ETF holdings CSV (Blackrock)
  ASX 300      -marketindex.com.au or asx300list.com
"""

import sys
import time
import warnings
from io import StringIO
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import pandas as pd
    import requests
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install pandas requests lxml html5lib")
    sys.exit(1)

OUT_DIR = Path(__file__).parent

# Browser-like headers so Wikipedia doesn't 403 us
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _write(symbols: list, fname: str):
    path = OUT_DIR / fname
    pd.DataFrame({"symbol": symbols}).to_csv(path, index=False)
    print(f"  Wrote {len(symbols):>4} symbols -> {fname}")


def _read_html_url(url: str):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return pd.read_html(StringIO(r.text))


def fetch_sp500():
    print("S&P 500 (GitHub datasets) ...")
    # Raw CSV maintained at: github.com/datasets/s-and-p-500-companies
    url = (
        "https://raw.githubusercontent.com/datasets/s-and-p-500-companies"
        "/main/data/constituents.csv"
    )
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(StringIO(r.text))
    col = [c for c in df.columns if c.lower() in ("symbol", "ticker")][0]
    syms = df[col].astype(str).str.strip().str.replace(".", "-", regex=False).tolist()
    syms = sorted(set(s for s in syms if s and s != "nan"))
    _write(syms, "sp500_symbols.csv")


def fetch_nasdaq100():
    print("NASDAQ 100 (Wikipedia) ...")
    tables = _read_html_url("https://en.wikipedia.org/wiki/Nasdaq-100")
    for tbl in tables:
        for c in tbl.columns:
            if str(c).lower() in ("ticker", "symbol"):
                raw = tbl[c].astype(str).str.strip().tolist()
                syms = sorted(set(s for s in raw if s and s != "nan" and len(s) <= 5))
                if len(syms) >= 90:
                    _write(syms, "nasdaq100_symbols.csv")
                    return
    print("  WARNING: could not locate NASDAQ 100 ticker column; check table structure")


def fetch_ftse100():
    print("FTSE 100 (Wikipedia) ...")
    tables = _read_html_url("https://en.wikipedia.org/wiki/FTSE_100_Index")
    for tbl in tables:
        for c in tbl.columns:
            if str(c).lower() in ("ticker", "symbol", "epic", "tidm", "ftse 100 companies"):
                raw = tbl[c].astype(str).str.strip().tolist()
                syms = [s for s in raw if s and s != "nan" and 1 <= len(s) <= 6]
                if len(syms) >= 90:
                    # Yahoo Finance needs .L suffix for LSE stocks
                    syms = sorted(set(
                        s + ".L" if not s.endswith(".L") else s for s in syms
                    ))
                    _write(syms, "ftse100_symbols.csv")
                    return
    print("  WARNING: could not locate FTSE 100 ticker column")


def fetch_russell1000():
    print("Russell 1000 (iShares IWB holdings) ...")
    url = (
        "https://www.ishares.com/us/products/239707/ISHARES-RUSSELL-1000-ETF/"
        "1467271812596.ajax?fileType=csv&fileName=IWB_holdings&dataType=fund"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        lines = r.text.splitlines()
        # iShares CSVs have a multi-line preamble; find the header row
        start = 0
        for i, line in enumerate(lines):
            stripped = line.strip().strip('"')
            if stripped.startswith("Ticker") or stripped.startswith("ticker"):
                start = i
                break
        content = "\n".join(lines[start:])
        df = pd.read_csv(StringIO(content))
        ticker_col = next(c for c in df.columns if c.strip().lower() in ("ticker", "symbol"))
        syms = df[ticker_col].astype(str).str.strip().tolist()
        syms = sorted(set(
            s for s in syms
            if s and s != "nan" and not s.startswith("-") and len(s) <= 5
        ))
        if len(syms) >= 800:
            _write(syms, "russell1000_symbols.csv")
            return
        raise ValueError(f"only {len(syms)} symbols parsed -check iShares format")
    except Exception as e:
        print(f"  iShares fetch failed ({e}); falling back to Wikipedia ...")
        _fetch_russell1000_wikipedia()


def _fetch_russell1000_wikipedia():
    tables = _read_html_url("https://en.wikipedia.org/wiki/Russell_1000_Index")
    syms = []
    for tbl in tables:
        for c in tbl.columns:
            if str(c).lower() in ("ticker", "symbol"):
                chunk = tbl[c].astype(str).str.strip().tolist()
                syms.extend(s for s in chunk if s and s != "nan")
    syms = sorted(set(syms))
    if syms:
        _write(syms, "russell1000_symbols.csv")
    else:
        print("  WARNING: Wikipedia fallback also failed")


def fetch_asx300():
    print("ASX 300 (marketindex.com.au) ...")
    url = "https://www.marketindex.com.au/asx300"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        content = r.content.decode("utf-8", errors="replace")
        tables = pd.read_html(StringIO(content))
        for tbl in tables:
            for c in tbl.columns:
                if str(c).lower() in ("code", "ticker", "symbol", "asx code"):
                    raw = tbl[c].astype(str).str.strip().tolist()
                    syms = [s for s in raw if s and s != "nan" and len(s) <= 5]
                    if len(syms) >= 200:
                        syms = sorted(set(
                            s + ".AX" if not s.endswith(".AX") else s for s in syms
                        ))
                        _write(syms, "asx300_symbols.csv")
                        return
        raise ValueError("no table with 200+ code-column rows found")
    except Exception as e:
        print(f"  marketindex failed ({e}); trying asx300list.com ...")
        _fetch_asx300_fallback()


def _fetch_asx300_fallback():
    url = "https://www.asx300list.com/"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    content = r.content.decode("utf-8", errors="replace")
    tables = pd.read_html(StringIO(content))
    for tbl in tables:
        for c in tbl.columns:
            if str(c).lower() in ("code", "ticker", "symbol", "asx code"):
                raw = tbl[c].astype(str).str.strip().tolist()
                syms = [s for s in raw if s and s != "nan" and len(s) <= 5]
                if len(syms) >= 100:
                    syms = sorted(set(
                        s + ".AX" if not s.endswith(".AX") else s for s in syms
                    ))
                    _write(syms, "asx300_symbols.csv")
                    return
    print("  WARNING: could not locate ASX 300 ticker column")


def main():
    print(f"\nBuilding universe files in: {OUT_DIR}\n" + "=" * 50)
    for fn in (fetch_sp500, fetch_nasdaq100, fetch_ftse100, fetch_russell1000, fetch_asx300):
        try:
            fn()
        except Exception as e:
            print(f"  ERROR in {fn.__name__}: {e}")
        time.sleep(1)
    print("=" * 50)
    print("Done. Re-run after index rebalances to refresh.")


if __name__ == "__main__":
    main()
