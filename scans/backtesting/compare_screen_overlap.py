"""
Screen Overlap Test — Full 5LC engine vs. backtest's simplified filter
======================================================================

Quantifies how differently the two fundamental gates select stocks, on CURRENT
(non point-in-time) data. Run this on a machine with Yahoo access — the sandbox
blocks yfinance.

For each symbol in the chosen universe it computes:
  - FULL    : passes the 150-pt FundamentalScreener (score >= 90)
  - FILTER  : passes the simplified gate used by historical_screener._screen_as_of_date
Then reports a confusion matrix and the Jaccard overlap of the two pass-lists.

Usage:
    python scans/backtesting/compare_screen_overlap.py
    python scans/backtesting/compare_screen_overlap.py --universe nasdaq100 --limit 100
    python scans/backtesting/compare_screen_overlap.py --universe sp500 --out results/overlap_sp500.csv

Author: Trading System
Date: 2026-06-05
"""

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(REPO_ROOT))

from scans.fundamentals.fundamental_screener import FundamentalScreener  # noqa: E402

PASS_THRESHOLD = 90          # full 5LC engine: 90/150 to pass
DATA_DIR = REPO_ROOT / "backtesting" / "data"


# ----------------------------------------------------------------------
# Simplified gate — mirrors historical_screener._screen_as_of_date,
# but evaluated on the most recent ~13 months of data ("as of today").
# ----------------------------------------------------------------------
def passes_backtest_filter(symbol: str) -> bool:
    try:
        tk = yf.Ticker(symbol)
        df = tk.history(period="14mo", auto_adjust=False)
        if df is None or df.empty or len(df) < 60:
            return False

        df = df.rename(columns=str.lower)
        recent_vol = df["volume"].tail(63).mean()        # ~3-month avg volume
        recent_price = float(df["close"].iloc[-1])
        ddv = recent_vol * recent_price

        if ddv < 20_000_000:        # $20M minimum dollar volume
            return False
        if recent_vol < 500_000:    # 500K shares minimum
            return False
        if recent_price < 5:        # price floor
            return False

        # 3-month momentum
        price_3m_ago = float(df["close"].iloc[-63]) if len(df) >= 63 else float(df["close"].iloc[0])
        gain_3m = (recent_price - price_3m_ago) / price_3m_ago * 100
        if gain_3m < 20:            # minimum 20% gain in 3 months
            return False

        # Market cap
        mcap = (tk.fast_info.get("market_cap") if hasattr(tk, "fast_info") else None) or \
               tk.info.get("marketCap", 0)
        if not mcap or mcap < 300_000_000:
            return False

        # Quarterly revenue YoY growth + gross margin
        qi = tk.quarterly_income_stmt
        if qi is not None and not qi.empty:
            qi = qi.T  # rows = quarters
            rev_col = next((c for c in qi.columns if "Total Revenue" in str(c) or "Revenue" in str(c)), None)
            gp_col = next((c for c in qi.columns if "Gross Profit" in str(c)), None)

            if rev_col:
                rev = qi[rev_col].dropna().sort_index()
                if len(rev) >= 5 and rev.iloc[-5] > 0:
                    rev_growth = (rev.iloc[-1] / rev.iloc[-5] - 1) * 100
                    if rev_growth < 10:        # min 10% YoY revenue growth
                        return False
            if gp_col and rev_col:
                gp = qi[gp_col].dropna()
                rev_latest = qi[rev_col].dropna()
                if len(gp) and len(rev_latest) and rev_latest.iloc[-1] > 0:
                    gp_margin = gp.iloc[-1] / rev_latest.iloc[-1] * 100
                    if gp_margin < 20:         # min 20% gross margin
                        return False

        return True
    except Exception:
        return False


def passes_full_screen(screener: FundamentalScreener, symbol: str):
    """Returns (passed: bool, score: float, grade: str) or (None, None, None) on error."""
    data = screener.get_fundamental_data(symbol)
    if not data:
        return None, None, None
    score, _scores, grade = screener.calculate_fundamental_score(data)
    return score >= PASS_THRESHOLD, score, grade


def load_universe(name: str) -> list:
    path = DATA_DIR / f"{name}_symbols.csv"
    if not path.exists():
        sys.exit(f"Universe file not found: {path}")
    df = pd.read_csv(path)
    col = "symbol" if "symbol" in df.columns else df.columns[0]
    return df[col].dropna().astype(str).str.strip().tolist()


def main():
    ap = argparse.ArgumentParser(description="Compare full 5LC screen vs backtest filter pass-lists.")
    ap.add_argument("--universe", default="sp500",
                    help="Universe stem in backtesting/data (sp500, russell1000, nasdaq100, asx300, ftse100)")
    ap.add_argument("--limit", type=int, default=None, help="Cap number of symbols (for a quick run)")
    ap.add_argument("--out", default=None, help="Optional CSV path for per-symbol results")
    args = ap.parse_args()

    symbols = load_universe(args.universe)
    if args.limit:
        symbols = symbols[: args.limit]

    screener = FundamentalScreener()
    rows = []
    n = len(symbols)
    print(f"Screening {n} symbols from '{args.universe}'...\n")

    for i, sym in enumerate(symbols, 1):
        full_pass, score, grade = passes_full_screen(screener, sym)
        filt_pass = passes_backtest_filter(sym)
        rows.append({
            "symbol": sym,
            "full_5lc_pass": full_pass,
            "full_score": round(score, 1) if score is not None else None,
            "full_grade": grade,
            "backtest_filter_pass": filt_pass,
        })
        if i % 25 == 0 or i == n:
            print(f"  ...{i}/{n}")

    res = pd.DataFrame(rows)
    valid = res.dropna(subset=["full_5lc_pass"]).copy()
    valid["full_5lc_pass"] = valid["full_5lc_pass"].astype(bool)

    both = int((valid["full_5lc_pass"] & valid["backtest_filter_pass"]).sum())
    only_full = int((valid["full_5lc_pass"] & ~valid["backtest_filter_pass"]).sum())
    only_filt = int((~valid["full_5lc_pass"] & valid["backtest_filter_pass"]).sum())
    neither = int((~valid["full_5lc_pass"] & ~valid["backtest_filter_pass"]).sum())
    union = both + only_full + only_filt
    jaccard = both / union if union else float("nan")

    print("\n" + "=" * 52)
    print(f"OVERLAP REPORT — {args.universe}  ({len(valid)} symbols with valid fundamentals)")
    print("=" * 52)
    print(f"{'':22}| filter PASS | filter FAIL")
    print(f"{'full 5LC PASS':22}| {both:>11} | {only_full:>11}")
    print(f"{'full 5LC FAIL':22}| {only_filt:>11} | {neither:>11}")
    print("-" * 52)
    print(f"Full 5LC pass-list   : {both + only_full}")
    print(f"Filter pass-list     : {both + only_filt}")
    print(f"Agree on PASS (both) : {both}")
    print(f"Jaccard overlap      : {jaccard:.3f}")
    print(f"Filter passes that FAIL the full screen: {only_filt} "
          f"({(only_filt / (both + only_filt) * 100) if (both + only_filt) else 0:.1f}% of filter list)")

    if args.out:
        out_path = REPO_ROOT / args.out
        out_path.parent.mkdir(parents=True, exist_ok=True)
        res.to_csv(out_path, index=False)
        print(f"\nPer-symbol results written to {out_path}")


if __name__ == "__main__":
    main()
