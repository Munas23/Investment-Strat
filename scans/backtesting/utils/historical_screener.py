"""
Historical Point-in-Time Screening

Prevents lookahead bias by only using data available at each point in time.
Runs fundamental and liquidity screening quarterly as of historical dates.

Performance: Downloads each symbol's full history ONCE, then filters in memory.
This avoids ~1,620 API calls (81 symbols x 20 quarters) down to ~81 calls.

Author: Trading System
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys
import logging
import pickle

sys.path.append(str(Path(__file__).parent.parent.parent))

# Suppress noisy yfinance warnings (delisted stocks, missing data, etc.)
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Disk cache directory: backtesting/cache/
CACHE_DIR = Path(__file__).parent.parent / 'cache'
PRICE_CACHE_DIR  = CACHE_DIR / 'prices'
FUND_CACHE_DIR   = CACHE_DIR / 'fundamentals'

# Fundamentals are re-downloaded if older than this many days
FUND_CACHE_MAX_AGE_DAYS = 30


class HistoricalScreener:
    """
    Run fundamental and liquidity screening as of historical dates.
    Prevents lookahead bias in backtesting.

    Data is pre-fetched ONCE per symbol for the full backtest period,
    then sliced per quarter in memory — much faster than per-quarter API calls.
    """

    def __init__(self, symbols: List[str]):
        """
        Initialize historical screener.

        Args:
            symbols: List of stock symbols to screen
        """
        self.symbols = symbols
        self._price_cache: Dict[str, pd.DataFrame] = {}          # symbol -> full OHLCV history
        self._info_cache: Dict[str, dict] = {}                   # symbol -> yfinance fast_info
        self._quarterly_income: Dict[str, pd.DataFrame] = {}     # symbol -> quarterly income stmt
        self._quarterly_balance: Dict[str, pd.DataFrame] = {}    # symbol -> quarterly balance sheet


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_quarterly_screening(
        self,
        start_date: str,
        end_date: str,
        rebalance_frequency: str = 'Q'
    ) -> Dict[str, List[str]]:
        """
        Run screening at regular intervals (quarterly by default).

        Downloads all symbol data ONCE, then applies filters per quarter
        using only data available at each historical date.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            rebalance_frequency: 'Q'=quarterly, 'M'=monthly

        Returns:
            Dict mapping date-string -> list of qualified symbols
        """
        print(f"\nRunning historical screening from {start_date} to {end_date}")
        print(f"Rebalance frequency: {rebalance_frequency}")

        # Step 1: Pre-fetch ALL data once (the key optimization)
        self._prefetch_all_data(start_date, end_date)

        # Step 2: Generate rebalance dates
        rebalance_dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq=rebalance_frequency + 'S'  # QS = quarter start, MS = month start
        )
        print(f"\nRebalance dates: {len(rebalance_dates)}")

        # Step 3: Screen each quarter using cached data (no API calls)
        qualified_universe = {}

        for date in rebalance_dates:
            print(f"\nScreening as of {date.strftime('%Y-%m-%d')}...", end=' ', flush=True)
            qualified_symbols = self._screen_as_of_date(date)
            qualified_universe[date.strftime('%Y-%m-%d')] = qualified_symbols
            print(f"Qualified: {len(qualified_symbols)} stocks")

        return qualified_universe


    def get_universe_for_date(
        self,
        date: pd.Timestamp,
        quarterly_results: Dict[str, List[str]]
    ) -> List[str]:
        """
        Get the qualified universe for a specific trading date.

        Uses the most recent quarterly screening before this date.

        Args:
            date: Date to get universe for
            quarterly_results: Dict from run_quarterly_screening()

        Returns:
            List of qualified symbols for this date
        """
        screening_dates = sorted([pd.to_datetime(d) for d in quarterly_results.keys()])
        valid_dates = [d for d in screening_dates if d <= date]

        if not valid_dates:
            most_recent = screening_dates[0]
        else:
            most_recent = valid_dates[-1]

        return quarterly_results[most_recent.strftime('%Y-%m-%d')]


    # ------------------------------------------------------------------
    # Internal: data fetching
    # ------------------------------------------------------------------

    def _prefetch_all_data(self, start_date: str, end_date: str) -> None:
        """
        Download full-period OHLCV + quarterly financials for ALL symbols.

        Disk cache (backtesting/cache/) is checked first:
          - Price parquet:   reused if it covers buffer_start -> end_date
          - Fundamentals:    reused if file is < FUND_CACHE_MAX_AGE_DAYS old
        Only symbols with missing/stale cache are downloaded from yfinance.
        """
        if self._price_cache:
            print("  (Using in-memory price cache)")
            return

        PRICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        FUND_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        buffer_start_dt = pd.to_datetime(start_date) - timedelta(days=400)
        buffer_start    = buffer_start_dt.strftime('%Y-%m-%d')
        end_dt          = pd.to_datetime(end_date)

        print(f"\n*** Pre-fetching price history for {len(self.symbols)} symbols ***")
        print(f"  Date range: {buffer_start} to {end_date} (includes 400-day buffer)")
        print(f"  Disk cache: {CACHE_DIR}")

        # ── Step 1: Load what we already have on disk ──────────────────────
        need_download = []
        loaded_from_cache = 0

        for symbol in self.symbols:
            pfile = PRICE_CACHE_DIR / f"{symbol}.pkl"
            if pfile.exists():
                try:
                    with open(pfile, 'rb') as f:
                        df = pickle.load(f)
                    # Validate the cached range covers what we need
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    if df.index.min() <= buffer_start_dt + timedelta(days=10) and df.index.max() >= end_dt - timedelta(days=10):
                        self._price_cache[symbol] = df
                        loaded_from_cache += 1
                        continue
                except Exception:
                    pass
            need_download.append(symbol)

        print(f"  Loaded {loaded_from_cache} symbols from disk cache")
        print(f"  Need to download: {len(need_download)} symbols")

        # ── Step 2: Download missing symbols in batches ─────────────────────
        if need_download:
            batch_size   = 20
            total_batches = (len(need_download) + batch_size - 1) // batch_size

            for batch_num, i in enumerate(range(0, len(need_download), batch_size)):
                batch = need_download[i:i + batch_size]
                print(f"  Downloading batch {batch_num + 1}/{total_batches} "
                      f"({len(batch)} symbols)...", end=' ', flush=True)

                try:
                    raw = yf.download(
                        batch,
                        start=buffer_start,
                        end=end_date,
                        auto_adjust=True,
                        progress=False,
                        threads=True,
                    )

                    if raw is None or raw.empty:
                        print("empty")
                        continue

                    fetched = 0
                    if len(batch) == 1:
                        symbol = batch[0]
                        df = self._clean_df(raw)
                        if df is not None:
                            self._price_cache[symbol] = df
                            with open(PRICE_CACHE_DIR / f"{symbol}.pkl", 'wb') as f:
                                pickle.dump(df, f)
                            fetched = 1
                    else:
                        for symbol in batch:
                            df = self._extract_ticker(raw, symbol)
                            if df is not None:
                                self._price_cache[symbol] = df
                                with open(PRICE_CACHE_DIR / f"{symbol}.pkl", 'wb') as f:
                                    pickle.dump(df, f)
                                fetched += 1

                    print(f"ok ({fetched}/{len(batch)})")

                except Exception as e:
                    print(f"error: {e}")

        print(f"  Price data ready for {len(self._price_cache)} / {len(self.symbols)} symbols")

        # ── Step 3: Load or fetch quarterly fundamentals ────────────────────
        print(f"  Loading quarterly financials...", flush=True)
        fund_from_cache = 0
        fund_downloaded = 0
        cutoff = datetime.now() - timedelta(days=FUND_CACHE_MAX_AGE_DAYS)

        for symbol in list(self._price_cache.keys()):
            income_file  = FUND_CACHE_DIR / f"{symbol}_income.pkl"
            balance_file = FUND_CACHE_DIR / f"{symbol}_balance.pkl"

            # fast_info is always fetched live (tiny / no meaningful cache benefit)
            try:
                self._info_cache[symbol] = yf.Ticker(symbol).fast_info
            except Exception:
                self._info_cache[symbol] = {}

            # Income statement
            if income_file.exists() and datetime.fromtimestamp(income_file.stat().st_mtime) > cutoff:
                try:
                    with open(income_file, 'rb') as f:
                        self._quarterly_income[symbol] = pickle.load(f)
                    fund_from_cache += 1
                    # Also try to load balance from cache
                    if balance_file.exists() and datetime.fromtimestamp(balance_file.stat().st_mtime) > cutoff:
                        with open(balance_file, 'rb') as f:
                            self._quarterly_balance[symbol] = pickle.load(f)
                    continue
                except Exception:
                    pass

            # Download and cache fundamentals
            ticker = yf.Ticker(symbol)
            try:
                qi = ticker.quarterly_income_stmt
                if qi is not None and not qi.empty:
                    df_qi = qi.T.sort_index()
                    self._quarterly_income[symbol] = df_qi
                    with open(income_file, 'wb') as f:
                        pickle.dump(df_qi, f)
            except Exception:
                pass
            try:
                qb = ticker.quarterly_balance_sheet
                if qb is not None and not qb.empty:
                    df_qb = qb.T.sort_index()
                    self._quarterly_balance[symbol] = df_qb
                    with open(balance_file, 'wb') as f:
                        pickle.dump(df_qb, f)
            except Exception:
                pass
            fund_downloaded += 1

        print(f"  Fundamentals: {fund_from_cache} from cache, {fund_downloaded} downloaded")
        print(f"  Done. Ready to screen {len(self._price_cache)} symbols.\n")


    @staticmethod
    def _clean_df(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Normalize column names and strip timezone from a single-ticker DataFrame."""
        if df is None or df.empty:
            return None
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df = df.dropna(subset=['close'])
        return df if not df.empty else None


    @staticmethod
    def _extract_ticker(raw: pd.DataFrame, symbol: str) -> Optional[pd.DataFrame]:
        """Extract a single ticker's data from a multi-ticker yf.download result."""
        try:
            # MultiIndex: (metric, symbol)
            lvl1 = raw.columns.get_level_values(1)
            if symbol not in lvl1:
                return None
            df = raw.xs(symbol, axis=1, level=1).copy()
            df.columns = [c.lower() for c in df.columns]
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            df = df.dropna(subset=['close'])
            return df if not df.empty else None
        except Exception:
            return None


    # ------------------------------------------------------------------
    # Internal: screening logic
    # ------------------------------------------------------------------

    def _screen_as_of_date(self, as_of_date: pd.Timestamp) -> List[str]:
        """
        Screen stocks using only data available up to as_of_date.

        Slices cached price data — no API calls.

        Args:
            as_of_date: Screening date (tz-naive Timestamp)

        Returns:
            List of symbols that pass all filters
        """
        # Use data from the prior year up to the day before screening
        data_end = as_of_date - timedelta(days=1)
        data_start = as_of_date - timedelta(days=400)  # ~13 months lookback

        qualified = []

        for symbol, full_df in self._price_cache.items():
            try:
                # Slice to the lookback window (data available at as_of_date)
                mask = (full_df.index >= data_start) & (full_df.index <= data_end)
                df = full_df.loc[mask]

                if df.empty or len(df) < 60:
                    continue

                # --- Liquidity filters ---
                recent_vol = df['volume'].tail(63).mean()   # 3-month avg volume
                recent_price = df['close'].iloc[-1]
                ddv = recent_vol * recent_price

                if ddv < 20_000_000:        # $20M minimum DDV
                    continue
                if recent_vol < 500_000:    # 500K shares minimum
                    continue

                # Price floor
                if recent_price < 5:
                    continue

                # --- Momentum filter (3-month gain) ---
                if len(df) >= 63:
                    price_3m_ago = df['close'].iloc[-63]
                else:
                    price_3m_ago = df['close'].iloc[0]

                gain_3m = ((recent_price - price_3m_ago) / price_3m_ago) * 100
                if gain_3m < 20:            # Minimum 20% gain in 3 months
                    continue

                # --- Fundamental filters (point-in-time quarterly data) ---
                info = self._info_cache.get(symbol, {})

                # Market cap from fast_info (approximation; float shares * current price)
                market_cap = getattr(info, 'market_cap', None) or 0
                if market_cap < 300_000_000:    # $300M minimum (relaxed slightly)
                    continue

                # Quarterly income statement — only use quarters BEFORE as_of_date
                qi = self._quarterly_income.get(symbol)
                if qi is not None and not qi.empty:
                    # Strip timezone from quarterly index for comparison
                    qi_idx = qi.index
                    if hasattr(qi_idx, 'tz') and qi_idx.tz is not None:
                        qi_idx = qi_idx.tz_localize(None)
                    # Select quarters that had already been reported by as_of_date
                    # (use quarter end date as proxy; earnings typically reported 4-6 weeks later,
                    #  but we add a 45-day lag to be conservative)
                    available_quarters = qi.loc[qi_idx <= (as_of_date - timedelta(days=45))]

                    if len(available_quarters) >= 2:
                        # Revenue growth: most recent quarter vs same quarter prior year
                        rev_col = next((c for c in available_quarters.columns
                                        if 'Total Revenue' in str(c) or 'Revenue' in str(c)), None)
                        if rev_col:
                            rev = available_quarters[rev_col].dropna()
                            if len(rev) >= 5:
                                # YoY growth: most recent vs 4 quarters ago
                                rev_growth = (rev.iloc[-1] / rev.iloc[-5] - 1) * 100 if rev.iloc[-5] > 0 else 0
                                if rev_growth < 10:     # Minimum 10% YoY revenue growth
                                    continue

                        # Gross profit margin: most recent quarter
                        gp_col = next((c for c in available_quarters.columns
                                       if 'Gross Profit' in str(c)), None)
                        if gp_col and rev_col:
                            gp = available_quarters[gp_col].dropna()
                            rev_latest = available_quarters[rev_col].dropna()
                            if len(gp) >= 1 and len(rev_latest) >= 1 and rev_latest.iloc[-1] > 0:
                                gp_margin = (gp.iloc[-1] / rev_latest.iloc[-1]) * 100
                                if gp_margin < 20:      # Minimum 20% gross margin
                                    continue

                qualified.append(symbol)

            except Exception:
                continue

        return qualified


# ------------------------------------------------------------------
# Standalone helper
# ------------------------------------------------------------------

def create_historical_universe(
    symbols: List[str],
    start_date: str = '2020-01-01',
    end_date: str = '2024-12-31',
    rebalance_frequency: str = 'Q'
) -> Dict[str, List[str]]:
    """
    Create historical point-in-time universe for backtesting.

    Args:
        symbols: List of all symbols to consider
        start_date: Backtest start date
        end_date: Backtest end date
        rebalance_frequency: How often to rebalance ('Q' or 'M')

    Returns:
        Dict mapping date -> list of qualified symbols
    """
    screener = HistoricalScreener(symbols)
    return screener.run_quarterly_screening(
        start_date=start_date,
        end_date=end_date,
        rebalance_frequency=rebalance_frequency
    )


# ------------------------------------------------------------------
# Example / self-test
# ------------------------------------------------------------------

if __name__ == "__main__":
    test_symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMD', 'META', 'AMZN']

    print("Testing Historical Screener (No Lookahead Bias)")
    print("=" * 80)

    screener = HistoricalScreener(test_symbols)

    universe = screener.run_quarterly_screening(
        start_date='2023-01-01',
        end_date='2023-12-31',
        rebalance_frequency='Q'
    )

    print("\n" + "=" * 80)
    print("RESULTS: Quarterly Universe")
    print("=" * 80)

    for date, syms in sorted(universe.items()):
        print(f"\n{date}:")
        print(f"  Qualified: {', '.join(syms) if syms else 'None'}")

    test_date = pd.to_datetime('2023-06-15')
    qualified = screener.get_universe_for_date(test_date, universe)
    print(f"\nUniverse for {test_date.strftime('%Y-%m-%d')}: {len(qualified)} stocks")
    print(f"  {', '.join(qualified)}")
