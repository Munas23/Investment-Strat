"""
ASX SMALL CAP SCREENER — POSITIVE CASHFLOW STRATEGY
====================================================

Screens ASX stocks (excluding ASX50) for positive cash-generating businesses.

Universe:        ASX stocks NOT in the S&P/ASX 50 index
Primary filter:  Positive operating cash flow
Secondary:       Market cap $50M-$3B AUD, min liquidity

Scoring (100 points total):
  Cashflow strength  — 35 pts  (OCF yield, FCF yield)
  Profitability      — 25 pts  (profit margin, ROE)
  Growth             — 20 pts  (revenue growth, earnings growth)
  Balance sheet      — 10 pts  (current ratio, debt/equity)
  Size & liquidity   — 10 pts  (market cap sweet spot, DDV)

Author: Trading System
Date:   2026-03-24
"""

import logging
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

import config

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Screener
# ---------------------------------------------------------------------------

class ASXSmallCapScreener:
    """
    Screens ASX small-cap stocks (ex-ASX50) for positive cashflow quality.

    Run standalone (python asx_smallcap_screener.py) or import and call
    run_screen() from a scheduler.
    """

    def __init__(self, account_size: float = config.ACCOUNT_SIZE):
        self.account_size    = account_size
        self.asx50_exclude   = config.ASX50_CODES
        self.min_market_cap  = config.MIN_MARKET_CAP_AUD
        self.max_market_cap  = config.MAX_MARKET_CAP_AUD
        self.min_avg_volume  = config.MIN_AVG_VOLUME
        self.min_ddv         = config.MIN_DDV_AUD

        log.info("=" * 70)
        log.info("ASX SMALL CAP SCREENER — POSITIVE CASHFLOW STRATEGY")
        log.info("=" * 70)
        log.info(f"Account:    ${account_size:,.0f}")
        log.info(f"Universe:   ASX stocks EXCLUDING ASX50 ({len(self.asx50_exclude)} tickers excluded)")
        log.info(f"Mkt cap:    ${self.min_market_cap/1e6:.0f}M – ${self.max_market_cap/1e9:.0f}B AUD")
        log.info(f"Min DDV:    ${self.min_ddv:,.0f} AUD/day")
        log.info(f"Primary:    POSITIVE OPERATING CASHFLOW")
        log.info("=" * 70)

    # ------------------------------------------------------------------
    # Universe loading
    # ------------------------------------------------------------------

    def load_universe(self, csv_path: Optional[Path] = None) -> List[str]:
        """
        Load ASX stock universe and exclude ASX50 companies.

        Priority:
        1. csv_path argument if provided
        2. Paths in config.SYMBOL_CSV_SEARCH_PATHS in order
        3. Built-in fallback list of ASX small/mid cap tickers

        Returns list of Yahoo Finance symbols (e.g. 'WTC.AX').
        """
        raw_symbols: List[str] = []

        # Try explicit path first
        search = [csv_path] if csv_path else []
        search += config.SYMBOL_CSV_SEARCH_PATHS

        for path in search:
            if path and Path(path).exists():
                try:
                    df = pd.read_csv(path)
                    col = next((c for c in df.columns if c.lower() in ('symbol', 'ticker', 'code')), None)
                    if col:
                        raw_symbols = df[col].dropna().str.upper().str.strip().tolist()
                        log.info(f"Loaded {len(raw_symbols)} symbols from {path}")
                        break
                except Exception as e:
                    log.warning(f"Could not read {path}: {e}")

        if not raw_symbols:
            log.warning("No symbol CSV found — using built-in ASX small/mid cap list")
            raw_symbols = _BUILTIN_ASX_SMALLCAP_TICKERS

        # Exclude ASX50, ensure .AX suffix
        universe = []
        excluded = 0
        for sym in raw_symbols:
            base = sym.replace('.AX', '').upper()
            if base in self.asx50_exclude:
                excluded += 1
                continue
            yf_sym = base + '.AX'
            universe.append(yf_sym)

        log.info(f"Universe: {len(universe)} stocks  ({excluded} ASX50 excluded)")
        return universe

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def _get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch fundamentals + cashflow for a single symbol from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Quick existence check
            if not info or info.get('regularMarketPrice') is None:
                return None

            # ---- Cashflow statement ----
            operating_cf: Optional[float] = None
            free_cf: Optional[float] = None
            capex: Optional[float] = None

            try:
                cf_stmt = ticker.cashflow  # columns = dates, index = line items
                if cf_stmt is not None and not cf_stmt.empty:
                    # Operating cash flow
                    for label in ('Operating Cash Flow',
                                  'Total Cash From Operating Activities',
                                  'Cash From Operating Activities'):
                        if label in cf_stmt.index:
                            vals = cf_stmt.loc[label].dropna()
                            if not vals.empty:
                                operating_cf = float(vals.iloc[0])
                            break

                    # Capital expenditure
                    for label in ('Capital Expenditure',
                                  'Capital Expenditures',
                                  'Purchase Of Property Plant And Equipment'):
                        if label in cf_stmt.index:
                            vals = cf_stmt.loc[label].dropna()
                            if not vals.empty:
                                capex = float(vals.iloc[0])
                            break

                    # Free cash flow (direct or derived)
                    if 'Free Cash Flow' in cf_stmt.index:
                        vals = cf_stmt.loc['Free Cash Flow'].dropna()
                        if not vals.empty:
                            free_cf = float(vals.iloc[0])
                    elif operating_cf is not None and capex is not None:
                        free_cf = operating_cf - abs(capex)

            except Exception:
                pass  # Fall through to info-based fallback

            # Fallback: yfinance info fields
            if operating_cf is None:
                val = info.get('operatingCashflow')
                operating_cf = float(val) if val is not None else None
            if free_cf is None:
                val = info.get('freeCashflow')
                free_cf = float(val) if val is not None else None

            return {
                'symbol':         symbol,
                'short_name':     info.get('shortName', symbol),
                'sector':         info.get('sector', ''),
                'industry':       info.get('industry', ''),
                'currency':       info.get('currency', ''),
                # Price & size
                'price':          info.get('currentPrice') or info.get('regularMarketPrice') or 0,
                'market_cap':     info.get('marketCap') or 0,
                'avg_volume':     info.get('averageVolume') or 0,
                'shares_out':     info.get('sharesOutstanding') or 0,
                'float_shares':   info.get('floatShares') or 0,
                # Cashflow
                'operating_cf':   operating_cf,
                'free_cf':        free_cf,
                'capex':          capex,
                # Profitability
                'profit_margin':  info.get('profitMargins') or 0,
                'gross_margin':   info.get('grossMargins') or 0,
                'roe':            info.get('returnOnEquity') or 0,
                'roa':            info.get('returnOnAssets') or 0,
                # Growth
                'revenue_growth': info.get('revenueGrowth') or 0,
                'earn_growth':    info.get('earningsGrowth') or 0,
                'earn_q_growth':  info.get('earningsQuarterlyGrowth') or 0,
                # Balance sheet
                'current_ratio':  info.get('currentRatio') or 0,
                'quick_ratio':    info.get('quickRatio') or 0,
                'debt_equity':    info.get('debtToEquity') or 0,   # yfinance: percentage (e.g. 45 = 45%)
                'total_cash':     info.get('totalCash') or 0,
                'total_debt':     info.get('totalDebt') or 0,
                # Valuation
                'pe_ratio':       info.get('trailingPE') or 0,
                'pb_ratio':       info.get('priceToBook') or 0,
                'revenue':        info.get('totalRevenue') or 0,
            }

        except Exception as e:
            log.debug(f"{symbol}: fetch error — {e}")
            return None

    # ------------------------------------------------------------------
    # Hard filters
    # ------------------------------------------------------------------

    def _passes_hard_filters(self, d: Dict) -> Tuple[bool, str]:
        """
        Return (passes, reason).
        All hard filters must pass before scoring occurs.
        The PRIMARY criterion is positive operating cashflow.
        """
        price      = d['price']      or 0
        mkt_cap    = d['market_cap'] or 0
        avg_vol    = d['avg_volume'] or 0
        op_cf      = d['operating_cf']

        # Must be an AUD-denominated ASX stock
        if d['currency'] not in ('AUD', 'aud'):
            return False, f"Currency {d['currency']} (not AUD)"

        # Market cap range
        if mkt_cap < self.min_market_cap:
            return False, f"Mkt cap ${mkt_cap/1e6:.1f}M < ${self.min_market_cap/1e6:.0f}M min"
        if mkt_cap > self.max_market_cap:
            return False, f"Mkt cap ${mkt_cap/1e9:.1f}B > ${self.max_market_cap/1e9:.0f}B max"

        # Minimum liquidity
        if avg_vol < self.min_avg_volume:
            return False, f"Avg volume {avg_vol:,.0f} < {self.min_avg_volume:,} min"
        ddv = price * avg_vol
        if ddv < self.min_ddv:
            return False, f"DDV ${ddv:,.0f} < ${self.min_ddv:,} min"

        # *** PRIMARY CRITERION: Positive operating cashflow ***
        if op_cf is None:
            return False, "Operating cashflow data unavailable"
        if op_cf <= 0:
            return False, f"Negative operating CF: ${op_cf/1e6:.1f}M"

        return True, "PASSED"

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score(self, d: Dict) -> Tuple[float, Dict]:
        """
        Score cashflow quality and supporting fundamentals.
        Returns (total_score_0_to_100, component_scores).
        """
        op_cf   = d['operating_cf'] or 0
        free_cf = d['free_cf']
        mkt_cap = d['market_cap']   or 1
        price   = d['price']        or 1
        avg_vol = d['avg_volume']   or 0

        # ---- 1. Cashflow strength (35 pts) ---------------------------------
        cf_pts = 0.0

        # Operating CF yield = OCF / market cap
        ocf_yield = (op_cf / mkt_cap) * 100
        if ocf_yield >= 10:
            cf_pts += 20
        elif ocf_yield >= 6:
            cf_pts += 15
        elif ocf_yield >= 3:
            cf_pts += 10
        elif ocf_yield > 0:
            cf_pts += 5

        # Free CF bonus
        if free_cf is not None and free_cf > 0:
            fcf_yield = (free_cf / mkt_cap) * 100
            if fcf_yield >= 8:
                cf_pts += 15
            elif fcf_yield >= 4:
                cf_pts += 10
            elif fcf_yield >= 2:
                cf_pts += 7
            else:
                cf_pts += 3

        cf_score = min(35.0, cf_pts)

        # ---- 2. Profitability (25 pts) -------------------------------------
        pm  = (d['profit_margin'] or 0) * 100
        roe = (d['roe'] or 0) * 100

        pm_pts = 0.0
        if pm >= 20:   pm_pts = 15
        elif pm >= 12: pm_pts = 11
        elif pm >= 6:  pm_pts = 7
        elif pm > 0:   pm_pts = 3

        roe_pts = 0.0
        if roe >= 20:   roe_pts = 10
        elif roe >= 12: roe_pts = 7
        elif roe >= 6:  roe_pts = 4
        elif roe > 0:   roe_pts = 2

        profit_score = min(25.0, pm_pts + roe_pts)

        # ---- 3. Growth (20 pts) --------------------------------------------
        rev_g  = (d['revenue_growth'] or 0) * 100
        earn_g = (d['earn_growth']    or 0) * 100

        rev_pts = 0.0
        if rev_g >= 20:   rev_pts = 10
        elif rev_g >= 10: rev_pts = 7
        elif rev_g >= 5:  rev_pts = 4
        elif rev_g > 0:   rev_pts = 2

        earn_pts = 0.0
        if earn_g >= 20:   earn_pts = 10
        elif earn_g >= 10: earn_pts = 7
        elif earn_g >= 5:  earn_pts = 4
        elif earn_g > 0:   earn_pts = 2

        growth_score = min(20.0, rev_pts + earn_pts)

        # ---- 4. Balance sheet (10 pts) -------------------------------------
        cr  = d['current_ratio'] or 0
        de  = (d['debt_equity'] or 0) / 100   # convert from % to ratio

        cr_pts = 0.0
        if cr >= 2.0:   cr_pts = 5
        elif cr >= 1.5: cr_pts = 3
        elif cr >= 1.0: cr_pts = 2

        de_pts = 0.0
        if de <= 0.2:   de_pts = 5
        elif de <= 0.5: de_pts = 3
        elif de <= 1.0: de_pts = 1

        balance_score = min(10.0, cr_pts + de_pts)

        # ---- 5. Size & liquidity (10 pts) ----------------------------------
        ddv = price * avg_vol

        # Market cap sweet spot: $100M-$1B (classic small cap)
        cap_pts = 0.0
        if 100_000_000 <= mkt_cap <= 1_000_000_000:  cap_pts = 5
        elif 1_000_000_000 < mkt_cap <= 3_000_000_000: cap_pts = 4
        elif mkt_cap < 100_000_000:                   cap_pts = 3

        ddv_pts = 0.0
        if ddv >= 5_000_000:   ddv_pts = 5
        elif ddv >= 2_000_000: ddv_pts = 4
        elif ddv >= 1_000_000: ddv_pts = 3
        else:                  ddv_pts = 1

        size_score = min(10.0, cap_pts + ddv_pts)

        # ---- Total -----------------------------------------------------------
        components = {
            'cashflow':     cf_score,
            'profitability': profit_score,
            'growth':       growth_score,
            'balance_sheet': balance_score,
            'size_liquidity': size_score,
        }
        total = sum(components.values())
        return total, components

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 80: return 'A+'
        if score >= 70: return 'A'
        if score >= 60: return 'B+'
        if score >= 50: return 'B'
        if score >= 40: return 'C'
        if score >= 30: return 'D'
        return 'F'

    # ------------------------------------------------------------------
    # Single symbol
    # ------------------------------------------------------------------

    def screen_symbol(self, symbol: str) -> Optional[Dict]:
        """Fetch, filter, and score one symbol. Returns result dict or None."""
        d = self._get_stock_data(symbol)
        if d is None:
            return None

        passes, reason = self._passes_hard_filters(d)
        if not passes:
            log.debug(f"{symbol}: FAIL — {reason}")
            return None

        total, comps = self._score(d)
        grade = self._grade(total)

        price   = d['price']      or 1
        mkt_cap = d['market_cap'] or 1
        avg_vol = d['avg_volume'] or 0
        op_cf   = d['operating_cf'] or 0
        free_cf = d['free_cf']

        return {
            'symbol':             symbol,
            'short_name':         d['short_name'],
            'sector':             d['sector'],
            'industry':           d['industry'],
            # Score
            'total_score':        round(total, 1),
            'grade':              grade,
            'cf_score':           comps['cashflow'],
            'profit_score':       comps['profitability'],
            'growth_score':       comps['growth'],
            'balance_score':      comps['balance_sheet'],
            'size_score':         comps['size_liquidity'],
            # Cashflow
            'operating_cf_m':     round(op_cf / 1e6, 2),
            'free_cf_m':          round(free_cf / 1e6, 2) if free_cf is not None else None,
            'ocf_yield_pct':      round((op_cf / mkt_cap) * 100, 2),
            'fcf_yield_pct':      round((free_cf / mkt_cap) * 100, 2) if free_cf and free_cf > 0 else 0.0,
            # Fundamentals
            'price':              round(price, 3),
            'market_cap_m':       round(mkt_cap / 1e6, 1),
            'avg_volume':         int(avg_vol),
            'ddv_k':              round(price * avg_vol / 1_000, 1),
            'profit_margin_pct':  round((d['profit_margin'] or 0) * 100, 1),
            'roe_pct':            round((d['roe'] or 0) * 100, 1),
            'revenue_growth_pct': round((d['revenue_growth'] or 0) * 100, 1),
            'earn_growth_pct':    round((d['earn_growth'] or 0) * 100, 1),
            'current_ratio':      round(d['current_ratio'] or 0, 2),
            'debt_equity_ratio':  round((d['debt_equity'] or 0) / 100, 2),
            'pe_ratio':           round(d['pe_ratio'] or 0, 1),
            # Balance sheet
            'total_cash_m':       round((d['total_cash'] or 0) / 1e6, 1),
            'total_debt_m':       round((d['total_debt'] or 0) / 1e6, 1),
        }

    # ------------------------------------------------------------------
    # Batch screen
    # ------------------------------------------------------------------

    def run_screen(self, symbols: List[str]) -> pd.DataFrame:
        """Screen all symbols and return ranked DataFrame."""
        results = []
        total = len(symbols)

        log.info(f"Screening {total} symbols...")

        for i, symbol in enumerate(symbols, 1):
            if i % 25 == 0:
                log.info(f"  Progress: {i}/{total} ({i/total*100:.0f}%) — {len(results)} passed")

            result = self.screen_symbol(symbol)
            if result:
                results.append(result)

            time.sleep(0.15)   # Rate-limit Yahoo Finance requests

        log.info(f"Done: {len(results)}/{total} passed the cashflow screen ({len(results)/total*100:.1f}%)")

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        df = df.sort_values(['total_score', 'ocf_yield_pct'], ascending=[False, False]).reset_index(drop=True)
        return df

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def save_results(self, df: pd.DataFrame, output_dir: Path) -> None:
        """Save results to timestamped CSV files in output_dir."""
        if df.empty:
            log.warning("No results to save.")
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')

        # All stocks that passed hard filters
        all_file = output_dir / f'smallcap_{ts}_ALL.csv'
        df.to_csv(all_file, index=False)
        log.info(f"Saved: {all_file.name}  ({len(df)} stocks)")

        # Quality (score >= 60)
        q_df = df[df['total_score'] >= config.MIN_SCORE_QUALITY]
        if not q_df.empty:
            q_file = output_dir / f'smallcap_{ts}_QUALITY.csv'
            q_df.to_csv(q_file, index=False)
            log.info(f"Saved: {q_file.name}  ({len(q_df)} stocks, score >= {config.MIN_SCORE_QUALITY})")

        # Top tier (score >= 70)
        t_df = df[df['total_score'] >= config.MIN_SCORE_TOP]
        if not t_df.empty:
            t_file = output_dir / f'smallcap_{ts}_TOP.csv'
            t_df.to_csv(t_file, index=False)
            log.info(f"Saved: {t_file.name}  ({len(t_df)} stocks, score >= {config.MIN_SCORE_TOP})")

        self._print_summary(df)

    def _print_summary(self, df: pd.DataFrame) -> None:
        log.info("")
        log.info("=" * 70)
        log.info("ASX SMALL CAP CASHFLOW SCREEN — SUMMARY")
        log.info("=" * 70)
        log.info(f"Total passed:   {len(df)}")
        log.info(f"  TOP   (>= {config.MIN_SCORE_TOP}):  {len(df[df['total_score'] >= config.MIN_SCORE_TOP])}")
        log.info(f"  GOOD  (>= {config.MIN_SCORE_QUALITY}):  {len(df[df['total_score'] >= config.MIN_SCORE_QUALITY])}")
        log.info(f"  PASS  (>= 50):  {len(df[df['total_score'] >= 50])}")

        pos_fcf = df[df['fcf_yield_pct'] > 0]
        log.info(f"\nCASHFLOW:")
        log.info(f"  Avg OCF yield:    {df['ocf_yield_pct'].mean():.1f}%")
        if not pos_fcf.empty:
            log.info(f"  Avg FCF yield:    {pos_fcf['fcf_yield_pct'].mean():.1f}%")
        log.info(f"  Positive FCF:     {len(pos_fcf)}/{len(df)} stocks")

        log.info(f"\nTOP 15 BY SCORE:")
        log.info(f"  {'Symbol':<10} {'Score':>5} {'Grd':>3}  {'OCF $M':>8}  {'OCF%':>5}  {'FCF%':>5}  {'Cap $M':>7}  Sector")
        log.info(f"  {'-'*10} {'-'*5} {'-'*3}  {'-'*8}  {'-'*5}  {'-'*5}  {'-'*7}  ------")
        for _, r in df.head(15).iterrows():
            log.info(
                f"  {r['symbol']:<10} {r['total_score']:>5.1f} {r['grade']:>3}  "
                f"{r['operating_cf_m']:>8.1f}  {r['ocf_yield_pct']:>5.1f}  "
                f"{r['fcf_yield_pct']:>5.1f}  {r['market_cap_m']:>7.0f}  {r['sector']}"
            )
        log.info("=" * 70)


# ---------------------------------------------------------------------------
# Built-in fallback ASX small/mid cap ticker list
# ---------------------------------------------------------------------------
# A representative selection of ASX tickers outside the ASX50.
# For production use, replace with a full ASX universe CSV
# (place it at smallcaps/asx_symbols.csv).

_BUILTIN_ASX_SMALLCAP_TICKERS: List[str] = [
    # Financials & diversified
    'AMP', 'MFG', 'PTM', 'PPT', 'CGF', 'IFL', 'HUB', 'NHF', 'MPL',
    # Resources (ex-big miners)
    'S32', 'IGO', 'LYC', 'ILU', 'EVN', 'OGC', 'SAR', 'RRL', 'NST',
    'SFR', 'NIC', 'PDN', 'BOE', 'PLS', 'AKE', 'SYA', 'LRS', 'CXO',
    'MIN', 'WHC', 'NHC', 'YAL', 'WAF', 'CMM', 'DCN', 'RMS',
    # Technology
    'WTC', 'TNE', 'NXT', 'XRO', 'NEA', 'ALU', 'VHT', 'PME', 'ELO',
    'HLS', 'MP1', 'APX', 'DGL', 'AD8', 'CPU',
    # Healthcare
    'RMD', 'SHL', 'RHC', 'COH', 'MSB', 'IMD', 'CU6', 'AVH', 'NEU',
    'PNV', 'TLX', 'IMM', 'MX1',
    # Consumer
    'WOW', 'COL', 'HVN', 'JBH', 'SUL', 'LOV', 'MYR', 'ARB', 'GUD',
    'DMP', 'RFG', 'TRS', 'BWX',
    # Industrials
    'BLD', 'CSR', 'RWC', 'JHX', 'NUF', 'IPL', 'ORI', 'WOR', 'MND',
    'NWH', 'CIM', 'SXL', 'AZJ', 'TCL', 'ALX',
    # REITs
    'GPT', 'SCG', 'DXS', 'MGR', 'CHC', 'CLW', 'GDI', 'CQR',
    # Energy
    'STO', 'WDS', 'BPT', 'SXY', 'CVN', 'KAR',
    # Communications
    'TLS', 'TPG', 'VOC', 'HT1',
    # Diversified / other
    'APA', 'ASX', 'QAN', 'AIA', 'FLT', 'CTD', 'WEB', 'CCP', 'SVW',
    'MMS', 'OFX', 'GQG', 'PAR', 'PBH', 'IEL', 'EBO', 'RHC',
]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n" + "=" * 70)
    print("ASX SMALL CAP SCREENER — POSITIVE CASHFLOW")
    print("Excludes ASX50  |  Focus: Cash-generating small/mid cap businesses")
    print("=" * 70 + "\n")

    screener = ASXSmallCapScreener()

    # Load universe (CSV in this folder > scans downloads > built-in list)
    symbols = screener.load_universe()
    if not symbols:
        log.error("No symbols loaded. Add asx_symbols.csv to the smallcaps folder.")
        return

    # Run screen
    results_df = screener.run_screen(symbols)

    if results_df.empty:
        log.warning("No stocks passed the cashflow screen.")
        return

    # Save to results_YYYY-MM subfolder
    results_dir = config.SMALLCAPS_DIR / f'results_{datetime.now().strftime("%Y-%m")}'
    screener.save_results(results_df, results_dir)

    print(f"\nResults saved to: {results_dir}")
    print("Next step: run schedule_screener.py to set up automated scanning.")


if __name__ == '__main__':
    main()
