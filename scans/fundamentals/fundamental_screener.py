"""
FUNDAMENTAL SCREENER - 5LC METHODOLOGY
======================================

Screens liquid stocks (Tier 1-3) for fundamental quality using
Mark Minervini's 5-Level Conviction (5LC) methodology.

Process:
1. Load liquid stocks from liquidity screener (Tier 1-3)
2. Fetch fundamental data from Yahoo Finance
3. Score each stock on 10 weighted criteria (150 points total)
4. Assign fundamental grade (A+, A, B+, B, C, D, F)
5. Filter for 60%+ score (90+ points minimum)

Author: Trading System
Date: 2026-01-01
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
import time
import warnings
warnings.filterwarnings('ignore')


class FundamentalScreener:
    """
    Screen stocks for fundamental quality using 5LC methodology

    Combines liquidity filtering with comprehensive fundamental analysis
    to identify high-quality growth companies.
    """

    def __init__(self):
        """Initialize the fundamental screener"""
        self.setup_logging()

        # 5LC Fundamental Criteria (150 points total)
        self.criteria = {
            # Market Metrics (20 points = 13.3%)
            'market_cap': {
                'weight': 10,
                'min_usd': 300_000_000,     # $300M minimum
                'max_usd': 50_000_000_000,  # $50B maximum
                'min_aud': 500_000_000,     # $500M minimum for ASX
                'max_aud': 50_000_000_000,  # $50B maximum for ASX
            },
            'price': {
                'weight': 5,
                'min_usd': 15,  # $15 minimum
                'min_aud': 5,   # $5 minimum for ASX
            },
            'volume': {
                'weight': 5,
                'min_usd': 500_000,  # 500K shares minimum
                'min_aud': 100_000,  # 100K shares minimum for ASX
            },

            # Profitability (35 points = 23.3%)
            'roe': {
                'weight': 20,
                'excellent': 25,  # 20 pts
                'good': 20,       # 15 pts
                'pass': 15,       # 10 pts
            },
            'profit_margin': {
                'weight': 15,
                'excellent': 20,  # 15 pts
                'good': 15,       # 12 pts
                'pass': 10,       # 8 pts
            },

            # Growth (50 points = 33.3%) - MOST IMPORTANT
            'revenue_growth': {
                'weight': 25,
                'excellent': 30,  # 25 pts
                'good': 25,       # 20 pts
                'pass': 20,       # 15 pts (RAISED from 15%)
            },
            'earnings_growth': {
                'weight': 25,
                'excellent': 40,  # 25 pts
                'good': 30,       # 20 pts (RAISED from 25%)
                'pass': 25,       # 15 pts (RAISED from 18%)
            },

            # Financial Strength (25 points = 16.7%)
            'current_ratio': {
                'weight': 15,
                'excellent': 2.0,   # 15 pts
                'good': 1.8,        # 12 pts
                'pass': 1.5,        # 8 pts
            },
            'debt_to_equity': {
                'weight': 10,
                'excellent': 0.20,  # 10 pts (RELAXED from 0.10)
                'good': 0.40,       # 8 pts (RELAXED from 0.20)
                'pass': 0.50,       # 5 pts (RELAXED from 0.30)
            },

            # Institutional (20 points = 13.3%)
            'institutional_ownership': {
                'weight': 20,
                'optimal_min': 50,  # 20 pts
                'optimal_max': 70,
                'good_min': 40,     # 15 pts
                'good_max': 80,
            }
        }

        self.logger.info("PURE GROWTH FUNDAMENTAL SCREENING (Option B)")
        self.logger.info("=" * 80)
        self.logger.info("Based on: Minervini/O'Neil methodology")
        self.logger.info("SCORING BREAKDOWN (150 points total):")
        self.logger.info("  Market Metrics:      20 pts (13.3%) - Size & liquidity")
        self.logger.info("  Profitability:       35 pts (23.3%) - ROE, margins")
        self.logger.info("  Growth:              50 pts (33.3%) - Revenue, earnings ← HIGHEST")
        self.logger.info("  Financial Strength:  25 pts (16.7%) - Ratios, debt")
        self.logger.info("  Institutional:       20 pts (13.3%) - Ownership")
        self.logger.info("=" * 80)
        self.logger.info("GROWTH THRESHOLDS (RAISED):")
        self.logger.info("  EPS Growth: 25%+ minimum (was 18%)")
        self.logger.info("  Revenue Growth: 20%+ minimum (was 15%)")
        self.logger.info("  Debt Limit: 50% max (was 30%)")
        self.logger.info("=" * 80)
        self.logger.info("MINIMUM PASS: 90/150 points (60%)")
        self.logger.info("=" * 80)

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def find_latest_download_folder(self) -> Optional[Path]:
        """Find the most recent downloads folder"""
        script_dir = Path(__file__).parent
        scans_path = script_dir.parent
        download_folders = list(scans_path.glob('downloads_*'))

        if not download_folders:
            self.logger.error(f"No download folders found in {scans_path}")
            return None

        latest_folder = sorted(download_folders)[-1]
        self.logger.info(f"Using data from: {latest_folder}")
        return latest_folder

    def load_liquid_stocks(self, folder_path: Path) -> Optional[pd.DataFrame]:
        """
        Load liquid stocks (Tier 1-3) from liquidity screening results

        Returns:
            DataFrame with liquid stocks or None if not found
        """
        # Find latest liquidity screening file (TRADEABLE = Tier 1-3)
        liquidity_files = list(folder_path.glob('liquidity_screen_*_TRADEABLE.csv'))

        if not liquidity_files:
            self.logger.error(f"No liquidity screening results found in {folder_path}")
            self.logger.error("Please run the liquidity screener first!")
            return None

        # Use most recent file
        latest_file = sorted(liquidity_files)[-1]
        self.logger.info(f"Loading liquid stocks from: {latest_file.name}")

        try:
            df = pd.read_csv(latest_file)
            self.logger.info(f"Loaded {len(df)} liquid stocks (Tier 1-3)")

            # Show tier distribution
            tier_counts = df['liquidity_tier'].value_counts()
            for tier, count in tier_counts.items():
                self.logger.info(f"  {tier}: {count} stocks")

            return df

        except Exception as e:
            self.logger.error(f"Error loading liquidity file: {e}")
            return None

    def get_fundamental_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch fundamental data from Yahoo Finance

        Returns:
            Dict with fundamental metrics or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return None

            # Extract fundamental metrics
            data = {
                'symbol': symbol,

                # Market metrics
                'market_cap': info.get('marketCap', 0),
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'volume': info.get('averageVolume', 0),
                'currency': info.get('currency', 'USD'),

                # Profitability
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                'operating_margin': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0,

                # Growth
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0,

                # Financial strength
                'current_ratio': info.get('currentRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                'quick_ratio': info.get('quickRatio', 0),
                'total_cash': info.get('totalCash', 0),
                'total_debt': info.get('totalDebt', 0),

                # Institutional
                'institutional_ownership': info.get('heldByInstitutions', 0) * 100 if info.get('heldByInstitutions') else 0,
                'insider_ownership': info.get('heldByInsiders', 0) * 100 if info.get('heldByInsiders') else 0,

                # Additional
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'pe_ratio': info.get('trailingPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
            }

            return data

        except Exception as e:
            self.logger.debug(f"Error fetching fundamentals for {symbol}: {e}")
            return None

    def score_market_cap(self, market_cap: float, currency: str) -> float:
        """Score market cap (0-10 points)"""
        if currency == 'AUD':
            min_cap = self.criteria['market_cap']['min_aud']
            max_cap = self.criteria['market_cap']['max_aud']
        else:
            min_cap = self.criteria['market_cap']['min_usd']
            max_cap = self.criteria['market_cap']['max_usd']

        if min_cap <= market_cap <= max_cap:
            return 10
        elif market_cap < min_cap:
            # Partial credit for being close
            return max(0, 10 * (market_cap / min_cap))
        else:
            # Over max (mega cap - slower growth)
            return 5

    def score_price(self, price: float, currency: str) -> float:
        """Score stock price (0-5 points)"""
        min_price = self.criteria['price']['min_aud'] if currency == 'AUD' else self.criteria['price']['min_usd']

        if price >= min_price:
            return 5
        else:
            return max(0, 5 * (price / min_price))

    def score_volume(self, volume: float, currency: str) -> float:
        """Score average volume (0-5 points)"""
        min_volume = self.criteria['volume']['min_aud'] if currency == 'AUD' else self.criteria['volume']['min_usd']

        if volume >= min_volume:
            return 5
        else:
            return max(0, 5 * (volume / min_volume))

    def score_roe(self, roe: float) -> float:
        """Score ROE (0-20 points)"""
        thresholds = self.criteria['roe']

        if roe >= thresholds['excellent']:
            return 20
        elif roe >= thresholds['good']:
            return 15
        elif roe >= thresholds['pass']:
            return 10
        elif roe > 0:
            return 5 * (roe / thresholds['pass'])
        else:
            return 0

    def score_profit_margin(self, margin: float) -> float:
        """Score profit margin (0-15 points)"""
        thresholds = self.criteria['profit_margin']

        if margin >= thresholds['excellent']:
            return 15
        elif margin >= thresholds['good']:
            return 12
        elif margin >= thresholds['pass']:
            return 8
        elif margin > 0:
            return 4 * (margin / thresholds['pass'])
        else:
            return 0

    def score_revenue_growth(self, growth: float) -> float:
        """Score revenue growth (0-25 points) - RAISED THRESHOLDS"""
        thresholds = self.criteria['revenue_growth']

        if growth >= thresholds['excellent']:  # 30%+
            return 25
        elif growth >= thresholds['good']:  # 25-29%
            return 20
        elif growth >= thresholds['pass']:  # 20-24%
            return 15
        elif growth > 0:
            return 10 * (growth / thresholds['pass'])
        else:
            return 0

    def score_earnings_growth(self, growth: float) -> float:
        """Score earnings growth (0-25 points) - RAISED THRESHOLDS"""
        thresholds = self.criteria['earnings_growth']

        if growth >= thresholds['excellent']:  # 40%+
            return 25
        elif growth >= thresholds['good']:  # 30-39%
            return 20
        elif growth >= thresholds['pass']:  # 25-29%
            return 15
        elif growth > 0:
            return 10 * (growth / thresholds['pass'])
        else:
            return 0

    def score_current_ratio(self, ratio: float) -> float:
        """Score current ratio (0-15 points)"""
        thresholds = self.criteria['current_ratio']

        if ratio >= thresholds['excellent']:
            return 15
        elif ratio >= thresholds['good']:
            return 12
        elif ratio >= thresholds['pass']:
            return 8
        elif ratio > 0:
            return 4 * (ratio / thresholds['pass'])
        else:
            return 0

    def score_debt_to_equity(self, de_ratio: float) -> float:
        """Score debt-to-equity (0-10 points), lower is better - RELAXED LIMITS"""
        thresholds = self.criteria['debt_to_equity']

        if de_ratio <= thresholds['excellent']:  # ≤0.20 (20% debt)
            return 10
        elif de_ratio <= thresholds['good']:  # ≤0.40 (40% debt)
            return 8
        elif de_ratio <= thresholds['pass']:  # ≤0.50 (50% debt)
            return 5
        elif de_ratio <= 1.0:
            # Partial credit up to 100% debt
            return 2
        else:
            return 0

    def score_institutional_ownership(self, ownership: float) -> float:
        """Score institutional ownership (0-20 points)"""
        thresholds = self.criteria['institutional_ownership']

        # Optimal range (50-70%)
        if thresholds['optimal_min'] <= ownership <= thresholds['optimal_max']:
            return 20
        # Good range (40-49% or 71-80%)
        elif thresholds['good_min'] <= ownership <= thresholds['good_max']:
            return 15
        # Too low or too high
        elif ownership < 20 or ownership > 95:
            return 0
        # Partial credit
        else:
            return 5

    def calculate_fundamental_score(self, data: Dict) -> Tuple[float, Dict, str]:
        """
        Calculate overall fundamental score (0-150 points)

        Returns:
            Tuple of (total_score, component_scores, grade)
        """
        scores = {
            'market_cap': self.score_market_cap(data['market_cap'], data['currency']),
            'price': self.score_price(data['price'], data['currency']),
            'volume': self.score_volume(data['volume'], data['currency']),
            'roe': self.score_roe(data['roe']),
            'profit_margin': self.score_profit_margin(data['profit_margin']),
            'revenue_growth': self.score_revenue_growth(data['revenue_growth']),
            'earnings_growth': self.score_earnings_growth(data['earnings_growth']),
            'current_ratio': self.score_current_ratio(data['current_ratio']),
            'debt_to_equity': self.score_debt_to_equity(data['debt_to_equity']),
            'institutional_ownership': self.score_institutional_ownership(data['institutional_ownership']),
        }

        # Calculate total
        total_score = sum(scores.values())

        # Calculate percentage and grade
        percentage = (total_score / 150) * 100

        if percentage >= 85:
            grade = 'A+'
        elif percentage >= 75:
            grade = 'A'
        elif percentage >= 65:
            grade = 'B+'
        elif percentage >= 60:
            grade = 'B'
        elif percentage >= 50:
            grade = 'C'
        elif percentage >= 40:
            grade = 'D'
        else:
            grade = 'F'

        return total_score, scores, grade

    def screen_symbol(self, symbol: str, liquidity_data: Dict) -> Optional[Dict]:
        """
        Screen a single symbol for fundamentals

        Args:
            symbol: Stock ticker
            liquidity_data: Liquidity metrics from previous screening

        Returns:
            Dict with screening results or None if failed
        """
        # Get fundamental data
        fund_data = self.get_fundamental_data(symbol)
        if fund_data is None:
            return None

        # Calculate fundamental score
        total_score, component_scores, grade = self.calculate_fundamental_score(fund_data)

        # Calculate percentage
        percentage = (total_score / 150) * 100

        # Compile results
        result = {
            # Identifiers
            'symbol': symbol,
            'source': liquidity_data.get('source', ''),
            'sector': fund_data['sector'],
            'industry': fund_data['industry'],

            # Liquidity metrics (from previous screening)
            'liquidity_tier': liquidity_data.get('liquidity_tier', ''),
            'liquidity_score': liquidity_data.get('liquidity_score', 0),
            'ddv': liquidity_data.get('ddv', 0),

            # Fundamental score
            'fundamental_score': total_score,
            'fundamental_percentage': percentage,
            'fundamental_grade': grade,

            # Component scores
            'market_cap_score': component_scores['market_cap'],
            'price_score': component_scores['price'],
            'volume_score': component_scores['volume'],
            'roe_score': component_scores['roe'],
            'profit_margin_score': component_scores['profit_margin'],
            'revenue_growth_score': component_scores['revenue_growth'],
            'earnings_growth_score': component_scores['earnings_growth'],
            'current_ratio_score': component_scores['current_ratio'],
            'debt_to_equity_score': component_scores['debt_to_equity'],
            'institutional_score': component_scores['institutional_ownership'],

            # Raw fundamentals
            'market_cap': fund_data['market_cap'],
            'price': fund_data['price'],
            'volume': fund_data['volume'],
            'roe': fund_data['roe'],
            'profit_margin': fund_data['profit_margin'],
            'gross_margin': fund_data['gross_margin'],
            'operating_margin': fund_data['operating_margin'],
            'revenue_growth': fund_data['revenue_growth'],
            'earnings_growth': fund_data['earnings_growth'],
            'earnings_quarterly_growth': fund_data['earnings_quarterly_growth'],
            'current_ratio': fund_data['current_ratio'],
            'debt_to_equity': fund_data['debt_to_equity'],
            'quick_ratio': fund_data['quick_ratio'],
            'institutional_ownership': fund_data['institutional_ownership'],
            'insider_ownership': fund_data['insider_ownership'],
            'pe_ratio': fund_data['pe_ratio'],
            'peg_ratio': fund_data['peg_ratio'],
            'currency': fund_data['currency'],
        }

        return result

    def screen_all_stocks(self, liquid_stocks_df: pd.DataFrame) -> pd.DataFrame:
        """
        Screen all liquid stocks for fundamentals

        Args:
            liquid_stocks_df: DataFrame with liquid stocks from liquidity screener

        Returns:
            DataFrame with fundamental screening results
        """
        results = []
        total = len(liquid_stocks_df)

        self.logger.info(f"Screening {total} liquid stocks for fundamentals...")

        for idx, row in liquid_stocks_df.iterrows():
            symbol = row['symbol']

            if (idx + 1) % 50 == 0:
                self.logger.info(f"Progress: {idx+1}/{total} ({(idx+1)/total*100:.1f}%)")

            # Convert row to dict for liquidity data
            liquidity_data = row.to_dict()

            # Screen fundamentals
            result = self.screen_symbol(symbol, liquidity_data)
            if result:
                results.append(result)

            # Rate limiting
            time.sleep(0.1)

        self.logger.info(f"Fundamental screening complete. {len(results)} stocks analyzed.")

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)

    def save_results(self, df: pd.DataFrame, output_folder: Path):
        """Save screening results to CSV files"""
        if df.empty:
            self.logger.warning("No results to save")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save full results
        full_file = output_folder / f'fundamental_screen_{timestamp}_FULL.csv'
        df_sorted = df.sort_values('fundamental_score', ascending=False)
        df_sorted.to_csv(full_file, index=False)
        self.logger.info(f"Saved full results to: {full_file}")

        # Save high quality only (60%+ = Grade B or better)
        quality_df = df[df['fundamental_percentage'] >= 60]
        if not quality_df.empty:
            quality_file = output_folder / f'fundamental_screen_{timestamp}_QUALITY.csv'
            quality_df.sort_values('fundamental_score', ascending=False).to_csv(quality_file, index=False)
            self.logger.info(f"Saved quality stocks (60%+) to: {quality_file}")

        # Save excellent only (75%+ = Grade A or A+)
        excellent_df = df[df['fundamental_percentage'] >= 75]
        if not excellent_df.empty:
            excellent_file = output_folder / f'fundamental_screen_{timestamp}_EXCELLENT.csv'
            excellent_df.sort_values('fundamental_score', ascending=False).to_csv(excellent_file, index=False)
            self.logger.info(f"Saved excellent stocks (75%+) to: {excellent_file}")

        # Print summary
        self.print_summary(df)

    def print_summary(self, df: pd.DataFrame):
        """Print summary statistics"""
        self.logger.info("\n" + "="*80)
        self.logger.info("FUNDAMENTAL SCREENING SUMMARY")
        self.logger.info("="*80)

        # Grade distribution
        self.logger.info("\nGRADE DISTRIBUTION:")
        grade_counts = df['fundamental_grade'].value_counts().sort_index()
        for grade, count in grade_counts.items():
            pct = (count / len(df)) * 100
            self.logger.info(f"  {grade}: {count} stocks ({pct:.1f}%)")

        # Score statistics
        self.logger.info("\nFUNDAMENTAL SCORE STATISTICS:")
        self.logger.info(f"  Mean: {df['fundamental_score'].mean():.1f}/150 ({df['fundamental_percentage'].mean():.1f}%)")
        self.logger.info(f"  Median: {df['fundamental_score'].median():.1f}/150 ({df['fundamental_percentage'].median():.1f}%)")
        self.logger.info(f"  Min: {df['fundamental_score'].min():.1f}/150 ({df['fundamental_percentage'].min():.1f}%)")
        self.logger.info(f"  Max: {df['fundamental_score'].max():.1f}/150 ({df['fundamental_percentage'].max():.1f}%)")

        # Pass rate
        passing = len(df[df['fundamental_percentage'] >= 60])
        self.logger.info(f"\nPASS RATE (60%+): {passing}/{len(df)} ({passing/len(df)*100:.1f}%)")

        # Top 10
        self.logger.info("\nTOP 10 STOCKS BY FUNDAMENTAL SCORE:")
        top_10 = df.nlargest(10, 'fundamental_score')[['symbol', 'fundamental_score', 'fundamental_grade', 'liquidity_tier', 'sector']]
        for idx, row in top_10.iterrows():
            self.logger.info(f"  {row['symbol']:8} - Score: {row['fundamental_score']:5.1f}/150 ({row['fundamental_score']/150*100:5.1f}%) - {row['fundamental_grade']:3} - {row['liquidity_tier']:20} - {row['sector']}")

        self.logger.info("="*80 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("FUNDAMENTAL SCREENER - 5LC METHODOLOGY")
    print("="*80 + "\n")

    # Initialize screener
    screener = FundamentalScreener()

    # Find latest download folder
    download_folder = screener.find_latest_download_folder()
    if download_folder is None:
        print("ERROR: No download folder found.")
        return

    # Load liquid stocks (Tier 1-3)
    liquid_stocks_df = screener.load_liquid_stocks(download_folder)
    if liquid_stocks_df is None:
        print("ERROR: No liquid stocks loaded. Run liquidity screener first.")
        return

    # Screen for fundamentals
    results_df = screener.screen_all_stocks(liquid_stocks_df)

    # Save results to download folder
    screener.save_results(results_df, download_folder)

    print("\n" + "="*80)
    print("FUNDAMENTAL SCREENING COMPLETE!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
