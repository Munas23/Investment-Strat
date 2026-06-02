"""
LIQUIDITY SCREENER FOR $2M ACCOUNT
===================================

Screens stocks for adequate liquidity based on:
- Daily Dollar Volume (DDV)
- Bid-Ask Spread
- Turnover Ratio
- Float Size
- Market Cap

Position sizing: 10-40% of $2M = $200K-$800K per position
Target: Position should be 0.5-2% of DDV for efficient entry/exit

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


class LiquidityScreener:
    """Screen stocks for liquidity adequacy based on account size and position sizing"""

    def __init__(self, account_size: float = 2_000_000):
        """
        Initialize the liquidity screener

        Args:
            account_size: Total account size in dollars (default: $2M)
        """
        self.account_size = account_size
        self.setup_logging()

        # Position sizing parameters (from 5LC strategy)
        self.min_position_pct = 0.10  # 10% minimum
        self.max_position_pct = 0.40  # 40% maximum
        self.market_health_multiplier_range = (0.5, 2.0)  # Weak to strong market

        # Calculate position size range
        self.min_position_size = account_size * self.min_position_pct
        self.max_position_size = account_size * self.max_position_pct * self.market_health_multiplier_range[1]

        self.logger.info(f"Account Size: ${account_size:,.0f}")
        self.logger.info(f"Position Range: ${self.min_position_size:,.0f} - ${self.max_position_size:,.0f}")

        # Liquidity thresholds (based on research)
        self.thresholds = {
            'min_ddv': 20_000_000,           # $20M minimum daily dollar volume
            'ideal_ddv': 40_000_000,         # $40M ideal daily dollar volume
            'excellent_ddv': 100_000_000,    # $100M excellent daily dollar volume
            'max_spread_pct': 0.50,          # 0.50% maximum bid-ask spread
            'ideal_spread_pct': 0.25,        # 0.25% ideal spread
            'excellent_spread_pct': 0.10,    # 0.10% excellent spread
            'min_volume': 500_000,           # 500K shares minimum volume
            'min_float': 25_000_000,         # 25M shares minimum float
            'ideal_float': 50_000_000,       # 50M shares ideal float
            'min_market_cap': 500_000_000,   # $500M minimum market cap
            'ideal_market_cap': 1_000_000_000, # $1B ideal market cap
            'min_turnover_pct': 0.5,         # 0.5% minimum daily turnover
            'ideal_turnover_pct': 1.0,       # 1% ideal daily turnover
            'min_price': 10.0,               # $10 minimum stock price
        }

        # Scoring weights (research-based)
        self.weights = {
            'ddv': 0.35,        # 35% - Most important
            'spread': 0.25,     # 25% - Transaction cost
            'turnover': 0.20,   # 20% - Trading activity
            'float': 0.15,      # 15% - Available shares
            'market_cap': 0.10, # 10% - Company size
        }

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)

    def find_latest_download_folder(self) -> Optional[Path]:
        """Find the most recent downloads folder in the scans directory"""
        # Get the script's directory (liquidity screener folder)
        script_dir = Path(__file__).parent

        # Go up one level to scans directory
        scans_path = script_dir.parent

        # Look for download folders in the scans directory
        download_folders = list(scans_path.glob('downloads_*'))

        if not download_folders:
            self.logger.error(f"No download folders found in {scans_path}")
            return None

        # Sort by folder name (date format YYYY-MM-DD makes this work)
        latest_folder = sorted(download_folders)[-1]
        self.logger.info(f"Using data from: {latest_folder}")
        return latest_folder

    def load_symbols_from_folder(self, folder_path: Path) -> Dict[str, List[str]]:
        """
        Load all symbol files from the download folder

        Returns:
            Dict mapping source to list of symbols
        """
        symbols_dict = {}

        # Find all *_symbols.csv files
        symbol_files = list(folder_path.glob('*_symbols.csv'))

        for file_path in symbol_files:
            source_name = file_path.stem.replace('_symbols', '')
            try:
                df = pd.read_csv(file_path)
                symbols = df['Symbol'].dropna().unique().tolist()

                # Add .AX suffix for ASX stocks
                if source_name == 'ASX300':
                    symbols = [f"{s}.AX" for s in symbols]

                symbols_dict[source_name] = symbols
                self.logger.info(f"Loaded {len(symbols)} symbols from {source_name}")
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")

        return symbols_dict

    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock data from Yahoo Finance

        Returns:
            Dict with stock metrics or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get historical data for volume calculation
            hist = ticker.history(period='3mo')

            if hist.empty or info is None:
                return None

            # Calculate average volume over 3 months
            avg_volume = hist['Volume'].tail(60).mean()

            # Extract required metrics
            data = {
                'symbol': symbol,
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'avg_volume': avg_volume,
                'market_cap': info.get('marketCap', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0),
                'bid': info.get('bid', 0),
                'ask': info.get('ask', 0),
                'exchange': info.get('exchange', ''),
                'currency': info.get('currency', 'USD'),
            }

            return data

        except Exception as e:
            self.logger.debug(f"Error fetching data for {symbol}: {e}")
            return None

    def calculate_liquidity_metrics(self, data: Dict) -> Dict:
        """
        Calculate all liquidity metrics for a stock

        Args:
            data: Stock data dict from get_stock_data

        Returns:
            Dict with calculated metrics
        """
        metrics = {}

        # Daily Dollar Volume
        metrics['ddv'] = data['avg_volume'] * data['price']

        # Bid-Ask Spread (percentage)
        if data['ask'] > 0 and data['bid'] > 0:
            metrics['spread_pct'] = ((data['ask'] - data['bid']) / data['ask']) * 100
        else:
            metrics['spread_pct'] = None

        # Turnover Ratio (daily volume as % of shares outstanding)
        if data['shares_outstanding'] > 0:
            metrics['turnover_pct'] = (data['avg_volume'] / data['shares_outstanding']) * 100
        else:
            metrics['turnover_pct'] = None

        # Position sizing metrics
        metrics['position_as_pct_of_ddv'] = {}
        for position_size in [200_000, 400_000, 600_000, 800_000]:
            if metrics['ddv'] > 0:
                pct = (position_size / metrics['ddv']) * 100
                metrics['position_as_pct_of_ddv'][position_size] = pct
            else:
                metrics['position_as_pct_of_ddv'][position_size] = None

        # Days to liquidate (for various position sizes)
        metrics['days_to_liquidate'] = {}
        for position_size in [200_000, 400_000, 600_000, 800_000]:
            if metrics['ddv'] > 0:
                days = position_size / metrics['ddv']
                metrics['days_to_liquidate'][position_size] = days
            else:
                metrics['days_to_liquidate'][position_size] = None

        return metrics

    def score_ddv(self, ddv: float) -> float:
        """Score Daily Dollar Volume (0-100)"""
        if ddv >= self.thresholds['excellent_ddv']:
            return 100
        elif ddv >= self.thresholds['ideal_ddv']:
            # Linear interpolation between ideal and excellent
            return 75 + 25 * ((ddv - self.thresholds['ideal_ddv']) /
                             (self.thresholds['excellent_ddv'] - self.thresholds['ideal_ddv']))
        elif ddv >= self.thresholds['min_ddv']:
            # Linear interpolation between min and ideal
            return 50 + 25 * ((ddv - self.thresholds['min_ddv']) /
                             (self.thresholds['ideal_ddv'] - self.thresholds['min_ddv']))
        elif ddv >= self.thresholds['min_ddv'] / 2:
            # Below minimum but not terrible
            return 25 * (ddv / (self.thresholds['min_ddv'] / 2))
        else:
            return 0

    def score_spread(self, spread_pct: Optional[float]) -> float:
        """Score Bid-Ask Spread (0-100), lower spread = higher score"""
        if spread_pct is None:
            return 0

        if spread_pct <= self.thresholds['excellent_spread_pct']:
            return 100
        elif spread_pct <= self.thresholds['ideal_spread_pct']:
            # Linear interpolation
            return 90 - 20 * ((spread_pct - self.thresholds['excellent_spread_pct']) /
                             (self.thresholds['ideal_spread_pct'] - self.thresholds['excellent_spread_pct']))
        elif spread_pct <= self.thresholds['max_spread_pct']:
            # Linear interpolation
            return 40 + 30 * ((self.thresholds['max_spread_pct'] - spread_pct) /
                             (self.thresholds['max_spread_pct'] - self.thresholds['ideal_spread_pct']))
        elif spread_pct <= 1.0:
            # Poor but tradeable
            return 20 * ((1.0 - spread_pct) / (1.0 - self.thresholds['max_spread_pct']))
        else:
            return 0

    def score_turnover(self, turnover_pct: Optional[float]) -> float:
        """Score Daily Turnover (0-100)"""
        if turnover_pct is None:
            return 0

        if turnover_pct >= 3.0:
            return 100
        elif turnover_pct >= 2.0:
            return 80 + 20 * ((turnover_pct - 2.0) / 1.0)
        elif turnover_pct >= 1.0:
            return 60 + 20 * ((turnover_pct - 1.0) / 1.0)
        elif turnover_pct >= 0.5:
            return 40 + 20 * ((turnover_pct - 0.5) / 0.5)
        elif turnover_pct >= 0.25:
            return 20 + 20 * ((turnover_pct - 0.25) / 0.25)
        else:
            return 20 * (turnover_pct / 0.25)

    def score_float(self, float_shares: float) -> float:
        """Score Float Size (0-100)"""
        if float_shares >= 100_000_000:
            return 100
        elif float_shares >= 50_000_000:
            return 80 + 20 * ((float_shares - 50_000_000) / 50_000_000)
        elif float_shares >= 25_000_000:
            return 60 + 20 * ((float_shares - 25_000_000) / 25_000_000)
        elif float_shares >= 10_000_000:
            return 40 + 20 * ((float_shares - 10_000_000) / 15_000_000)
        elif float_shares >= 5_000_000:
            return 20 + 20 * ((float_shares - 5_000_000) / 5_000_000)
        else:
            return 20 * (float_shares / 5_000_000)

    def score_market_cap(self, market_cap: float) -> float:
        """Score Market Cap (0-100)"""
        if market_cap >= 10_000_000_000:  # $10B+
            return 100
        elif market_cap >= 5_000_000_000:  # $5-10B
            return 90 + 10 * ((market_cap - 5_000_000_000) / 5_000_000_000)
        elif market_cap >= 1_000_000_000:  # $1-5B
            return 80 + 10 * ((market_cap - 1_000_000_000) / 4_000_000_000)
        elif market_cap >= 500_000_000:  # $500M-$1B
            return 60 + 20 * ((market_cap - 500_000_000) / 500_000_000)
        elif market_cap >= 100_000_000:  # $100M-$500M
            return 30 + 30 * ((market_cap - 100_000_000) / 400_000_000)
        else:
            return 30 * (market_cap / 100_000_000)

    def calculate_liquidity_score(self, data: Dict, metrics: Dict) -> Tuple[float, Dict]:
        """
        Calculate overall liquidity score (0-100)

        Returns:
            Tuple of (total_score, component_scores)
        """
        scores = {
            'ddv_score': self.score_ddv(metrics['ddv']),
            'spread_score': self.score_spread(metrics.get('spread_pct')),
            'turnover_score': self.score_turnover(metrics.get('turnover_pct')),
            'float_score': self.score_float(data['float_shares'] if data['float_shares'] else 0),
            'market_cap_score': self.score_market_cap(data['market_cap']),
        }

        # Calculate weighted total
        total_score = (
            scores['ddv_score'] * self.weights['ddv'] +
            scores['spread_score'] * self.weights['spread'] +
            scores['turnover_score'] * self.weights['turnover'] +
            scores['float_score'] * self.weights['float'] +
            scores['market_cap_score'] * self.weights['market_cap']
        )

        return total_score, scores

    def get_liquidity_tier(self, liquidity_score: float, ddv: float) -> str:
        """
        Determine liquidity tier based on score and DDV

        Tiers:
        - TIER 1 EXCELLENT: Score 90+, DDV $100M+
        - TIER 2 GOOD: Score 70-89, DDV $50M+
        - TIER 3 ADEQUATE: Score 50-69, DDV $20M+
        - TIER 4 MARGINAL: Score 30-49, DDV $10M+
        - TIER 5 POOR: Score <30 or DDV <$10M
        """
        if liquidity_score >= 90 and ddv >= 100_000_000:
            return "TIER 1 - EXCELLENT"
        elif liquidity_score >= 70 and ddv >= 50_000_000:
            return "TIER 2 - GOOD"
        elif liquidity_score >= 50 and ddv >= 20_000_000:
            return "TIER 3 - ADEQUATE"
        elif liquidity_score >= 30 and ddv >= 10_000_000:
            return "TIER 4 - MARGINAL"
        else:
            return "TIER 5 - POOR"

    def get_max_position_recommendation(self, tier: str) -> str:
        """Get recommended maximum position size for liquidity tier"""
        tier_recommendations = {
            "TIER 1 - EXCELLENT": "$800K (full size)",
            "TIER 2 - GOOD": "$600K-$800K",
            "TIER 3 - ADEQUATE": "$300K-$400K",
            "TIER 4 - MARGINAL": "$100K-$200K max",
            "TIER 5 - POOR": "AVOID or <$100K only"
        }
        return tier_recommendations.get(tier, "Unknown")

    def screen_symbol(self, symbol: str, source: str) -> Optional[Dict]:
        """
        Screen a single symbol for liquidity

        Returns:
            Dict with screening results or None if failed
        """
        # Get stock data
        data = self.get_stock_data(symbol)
        if data is None:
            return None

        # Apply hard filters
        if data['price'] < self.thresholds['min_price']:
            return None
        if data['market_cap'] < self.thresholds['min_market_cap']:
            return None
        if data['avg_volume'] < self.thresholds['min_volume']:
            return None

        # Calculate metrics
        metrics = self.calculate_liquidity_metrics(data)

        # Calculate liquidity score
        liquidity_score, component_scores = self.calculate_liquidity_score(data, metrics)

        # Determine tier
        tier = self.get_liquidity_tier(liquidity_score, metrics['ddv'])

        # Compile results
        result = {
            'symbol': symbol,
            'source': source,
            'price': data['price'],
            'avg_volume': data['avg_volume'],
            'ddv': metrics['ddv'],
            'spread_pct': metrics.get('spread_pct'),
            'turnover_pct': metrics.get('turnover_pct'),
            'float_shares': data['float_shares'],
            'market_cap': data['market_cap'],
            'liquidity_score': liquidity_score,
            'liquidity_tier': tier,
            'max_position_rec': self.get_max_position_recommendation(tier),
            'position_200k_pct_adv': metrics['position_as_pct_of_ddv'].get(200_000),
            'position_400k_pct_adv': metrics['position_as_pct_of_ddv'].get(400_000),
            'position_800k_pct_adv': metrics['position_as_pct_of_ddv'].get(800_000),
            'days_to_liquidate_400k': metrics['days_to_liquidate'].get(400_000),
            'ddv_score': component_scores['ddv_score'],
            'spread_score': component_scores['spread_score'],
            'turnover_score': component_scores['turnover_score'],
            'float_score': component_scores['float_score'],
            'market_cap_score': component_scores['market_cap_score'],
            'exchange': data['exchange'],
            'currency': data['currency'],
        }

        return result

    def screen_all_symbols(self, symbols_dict: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Screen all symbols from all sources

        Args:
            symbols_dict: Dict mapping source to list of symbols

        Returns:
            DataFrame with screening results
        """
        results = []
        total_symbols = sum(len(symbols) for symbols in symbols_dict.values())
        processed = 0

        self.logger.info(f"Screening {total_symbols} symbols...")

        for source, symbols in symbols_dict.items():
            self.logger.info(f"Processing {source} ({len(symbols)} symbols)...")

            for symbol in symbols:
                processed += 1
                if processed % 50 == 0:
                    self.logger.info(f"Progress: {processed}/{total_symbols} ({processed/total_symbols*100:.1f}%)")

                result = self.screen_symbol(symbol, source)
                if result:
                    results.append(result)

                # Rate limiting to avoid overwhelming Yahoo Finance
                time.sleep(0.1)

        self.logger.info(f"Screening complete. {len(results)} stocks passed filters.")

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
        full_file = output_folder / f'liquidity_screen_{timestamp}_FULL.csv'
        df_sorted = df.sort_values('liquidity_score', ascending=False)
        df_sorted.to_csv(full_file, index=False)
        self.logger.info(f"Saved full results to: {full_file}")

        # Save excellent tier only (Tier 1 & 2)
        excellent_df = df[df['liquidity_tier'].isin(['TIER 1 - EXCELLENT', 'TIER 2 - GOOD'])]
        if not excellent_df.empty:
            excellent_file = output_folder / f'liquidity_screen_{timestamp}_EXCELLENT.csv'
            excellent_df.sort_values('liquidity_score', ascending=False).to_csv(excellent_file, index=False)
            self.logger.info(f"Saved excellent tier results to: {excellent_file}")

        # Save tradeable (Tier 1-3)
        tradeable_df = df[df['liquidity_tier'].isin(['TIER 1 - EXCELLENT', 'TIER 2 - GOOD', 'TIER 3 - ADEQUATE'])]
        if not tradeable_df.empty:
            tradeable_file = output_folder / f'liquidity_screen_{timestamp}_TRADEABLE.csv'
            tradeable_df.sort_values('liquidity_score', ascending=False).to_csv(tradeable_file, index=False)
            self.logger.info(f"Saved tradeable results to: {tradeable_file}")

        # Print summary statistics
        self.print_summary(df)

    def print_summary(self, df: pd.DataFrame):
        """Print summary statistics"""
        self.logger.info("\n" + "="*80)
        self.logger.info("LIQUIDITY SCREENING SUMMARY")
        self.logger.info("="*80)

        # Tier distribution
        self.logger.info("\nLIQUIDITY TIER DISTRIBUTION:")
        tier_counts = df['liquidity_tier'].value_counts()
        for tier, count in tier_counts.items():
            pct = (count / len(df)) * 100
            self.logger.info(f"  {tier}: {count} stocks ({pct:.1f}%)")

        # Score statistics
        self.logger.info("\nLIQUIDITY SCORE STATISTICS:")
        self.logger.info(f"  Mean: {df['liquidity_score'].mean():.1f}")
        self.logger.info(f"  Median: {df['liquidity_score'].median():.1f}")
        self.logger.info(f"  Min: {df['liquidity_score'].min():.1f}")
        self.logger.info(f"  Max: {df['liquidity_score'].max():.1f}")

        # DDV statistics
        self.logger.info("\nDAILY DOLLAR VOLUME STATISTICS:")
        self.logger.info(f"  Mean: ${df['ddv'].mean():,.0f}")
        self.logger.info(f"  Median: ${df['ddv'].median():,.0f}")
        self.logger.info(f"  Min: ${df['ddv'].min():,.0f}")
        self.logger.info(f"  Max: ${df['ddv'].max():,.0f}")

        # Top 10 by liquidity score
        self.logger.info("\nTOP 10 STOCKS BY LIQUIDITY SCORE:")
        top_10 = df.nlargest(10, 'liquidity_score')[['symbol', 'liquidity_score', 'liquidity_tier', 'ddv', 'source']]
        for idx, row in top_10.iterrows():
            self.logger.info(f"  {row['symbol']:8} - Score: {row['liquidity_score']:5.1f} - {row['liquidity_tier']:20} - DDV: ${row['ddv']:>12,.0f} - {row['source']}")

        self.logger.info("="*80 + "\n")


def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("LIQUIDITY SCREENER - $2M ACCOUNT")
    print("="*80 + "\n")

    # Initialize screener
    screener = LiquidityScreener(account_size=2_000_000)

    # Find latest download folder
    download_folder = screener.find_latest_download_folder()
    if download_folder is None:
        print("ERROR: No download folder found. Please run download_the_csv.py first.")
        return

    # Load symbols
    symbols_dict = screener.load_symbols_from_folder(download_folder)
    if not symbols_dict:
        print("ERROR: No symbols loaded. Check download folder.")
        return

    # Screen all symbols
    results_df = screener.screen_all_symbols(symbols_dict)

    # Save results to the download folder
    screener.save_results(results_df, download_folder)

    print("\n" + "="*80)
    print("SCREENING COMPLETE!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
