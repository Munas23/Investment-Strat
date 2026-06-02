"""
Batch Position Calculator

Automatically calculates position sizes for all stocks from screening results.
Integrates liquidity + fundamental + technical screening data.

Author: Trading System
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
from position_calculator import PositionSizingCalculator
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict


class BatchPositionCalculator:
    """
    Calculate positions for multiple stocks from screening results.
    """

    def __init__(self, account_size: float = 2_000_000):
        """
        Initialize batch calculator.

        Args:
            account_size: Total account value
        """
        self.calc = PositionSizingCalculator(account_size=account_size)
        self.downloads_folder = self._find_latest_downloads_folder()


    def _find_latest_downloads_folder(self) -> Path:
        """
        Find the most recent downloads folder.

        Returns:
            Path to latest downloads folder
        """
        scans_path = Path(__file__).parent
        download_folders = list(scans_path.glob("downloads_*"))

        if not download_folders:
            raise FileNotFoundError("No downloads folder found. Run download_the_csv.py first.")

        latest_folder = max(download_folders, key=lambda p: p.name)
        print(f"📁 Using downloads folder: {latest_folder.name}")
        return latest_folder


    def load_screening_data(self) -> pd.DataFrame:
        """
        Load and merge all screening data (liquidity + fundamental).

        Returns:
            DataFrame with merged screening data
        """
        # Find latest screening files
        liquidity_files = list(self.downloads_folder.glob("liquidity_screen_*_TRADEABLE.csv"))
        fundamental_files = list(self.downloads_folder.glob("fundamental_screen_*_QUALITY.csv"))

        if not liquidity_files:
            raise FileNotFoundError("No liquidity screening results found.")

        if not fundamental_files:
            print("⚠️  Warning: No fundamental screening results found. Using liquidity data only.")
            liquidity_file = max(liquidity_files, key=lambda p: p.stat().st_mtime)
            return pd.read_csv(liquidity_file)

        # Load latest files
        liquidity_file = max(liquidity_files, key=lambda p: p.stat().st_mtime)
        fundamental_file = max(fundamental_files, key=lambda p: p.stat().st_mtime)

        print(f"📊 Loading: {liquidity_file.name}")
        print(f"📊 Loading: {fundamental_file.name}")

        liquidity_df = pd.read_csv(liquidity_file)
        fundamental_df = pd.read_csv(fundamental_file)

        # Merge on symbol
        merged_df = pd.merge(
            fundamental_df,
            liquidity_df[['symbol', 'liquidity_tier', 'liquidity_score', 'ddv']],
            on='symbol',
            how='left',
            suffixes=('_fund', '_liq')
        )

        # Use fundamental liquidity data if merge didn't work
        if 'liquidity_tier_liq' in merged_df.columns:
            merged_df['liquidity_tier'] = merged_df['liquidity_tier_liq'].fillna(merged_df['liquidity_tier_fund'])
            merged_df['ddv'] = merged_df['ddv_liq'].fillna(merged_df['ddv_fund'])

        print(f"✅ Loaded {len(merged_df)} quality stocks with fundamentals")
        return merged_df


    def calculate_positions_for_watchlist(
        self,
        symbols: List[str],
        conviction_levels: Dict[str, int],
        market_health: str = 'neutral',
        pattern_types: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        Calculate positions for a watchlist of symbols.

        Args:
            symbols: List of stock symbols
            conviction_levels: Dict mapping symbol to conviction level (1-5)
            market_health: Current market condition
            pattern_types: Optional dict mapping symbol to pattern type

        Returns:
            DataFrame with position sizing for all symbols
        """
        # Load screening data
        screening_data = self.load_screening_data()

        positions = []

        for symbol in symbols:
            # Get stock data from screening
            stock_data = screening_data[screening_data['symbol'] == symbol]

            if stock_data.empty:
                print(f"⚠️  {symbol}: Not found in screening data, skipping")
                continue

            stock = stock_data.iloc[0]

            # Get parameters
            conviction = conviction_levels.get(symbol, 3)
            pattern = pattern_types.get(symbol, 'standard') if pattern_types else 'standard'

            # Get current price and ATR
            print(f"\n⏳ Processing {symbol}...")
            current_price = self.calc.get_current_price(symbol)
            atr = self.calc.calculate_atr(symbol)

            if current_price is None or atr is None:
                print(f"❌ {symbol}: Could not fetch price/ATR, skipping")
                continue

            # Calculate position
            try:
                position = self.calc.calculate_position_size(
                    symbol=symbol,
                    entry_price=current_price,
                    atr=atr,
                    conviction_level=conviction,
                    market_health=market_health,
                    liquidity_tier=stock.get('liquidity_tier', 'TIER 3 - ADEQUATE'),
                    ddv=stock.get('ddv', 0),
                    fundamental_score=stock.get('fundamental_percentage', None),
                    pattern_type=pattern
                )

                # Check portfolio limits
                can_add, message = self.calc.check_portfolio_limits(position['final_risk_pct'])

                position['can_add_to_portfolio'] = can_add
                position['portfolio_message'] = message

                positions.append(position)
                print(f"✅ {symbol}: Position calculated")

            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
                continue

        # Convert to DataFrame
        if not positions:
            print("❌ No positions calculated")
            return pd.DataFrame()

        df = pd.DataFrame(positions)

        # Sort by conviction level (descending) then fundamental score
        df = df.sort_values(
            by=['conviction_level', 'fundamental_score'],
            ascending=[False, False]
        )

        return df


    def calculate_positions_from_technical_screen(
        self,
        technical_results_file: str,
        market_health: str = 'neutral',
        min_conviction: int = 3
    ) -> pd.DataFrame:
        """
        Calculate positions directly from technical screening results.

        Args:
            technical_results_file: Path to technical screening CSV
            market_health: Current market condition
            min_conviction: Minimum conviction level to include

        Returns:
            DataFrame with position sizing
        """
        # Load technical screening results
        tech_df = pd.read_csv(technical_results_file)

        # Filter by minimum conviction
        tech_df = tech_df[tech_df['conviction_level'] >= min_conviction]

        if tech_df.empty:
            print(f"❌ No stocks with conviction >= {min_conviction}")
            return pd.DataFrame()

        print(f"📊 Found {len(tech_df)} stocks with conviction >= {min_conviction}")

        # Extract symbols and conviction levels
        symbols = tech_df['symbol'].tolist()
        conviction_levels = dict(zip(tech_df['symbol'], tech_df['conviction_level']))

        # Determine pattern types if available
        pattern_types = None
        if 'is_breakout' in tech_df.columns:
            pattern_types = {}
            for _, row in tech_df.iterrows():
                if row.get('is_breakout', False):
                    pattern_types[row['symbol']] = 'breakout'
                else:
                    pattern_types[row['symbol']] = 'standard'

        # Calculate positions
        return self.calculate_positions_for_watchlist(
            symbols=symbols,
            conviction_levels=conviction_levels,
            market_health=market_health,
            pattern_types=pattern_types
        )


    def generate_trading_plan(
        self,
        positions_df: pd.DataFrame,
        max_positions: int = 12
    ) -> pd.DataFrame:
        """
        Generate a trading plan respecting portfolio limits.

        Args:
            positions_df: DataFrame of calculated positions
            max_positions: Maximum number of positions

        Returns:
            DataFrame with positions to trade (respecting limits)
        """
        if positions_df.empty:
            return pd.DataFrame()

        # Sort by conviction level and fundamental score
        sorted_df = positions_df.sort_values(
            by=['conviction_level', 'fundamental_score'],
            ascending=[False, False]
        ).copy()

        # Build portfolio respecting limits
        selected = []
        total_risk = 0
        max_total_risk = self.calc.max_total_portfolio_risk

        for idx, row in sorted_df.iterrows():
            # Check if can add
            if len(selected) >= max_positions:
                break

            if total_risk + row['final_risk_pct'] > max_total_risk:
                # Try to see if we can still fit smaller positions
                continue

            selected.append(idx)
            total_risk += row['final_risk_pct']

        # Create trading plan
        trading_plan = sorted_df.loc[selected].copy()
        trading_plan['portfolio_risk_pct'] = total_risk
        trading_plan['portfolio_position_number'] = range(1, len(trading_plan) + 1)

        return trading_plan


    def save_results(
        self,
        positions_df: pd.DataFrame,
        filename_prefix: str = "batch_positions"
    ):
        """
        Save results to CSV files.

        Args:
            positions_df: DataFrame of positions
            filename_prefix: Prefix for output files
        """
        if positions_df.empty:
            print("❌ No positions to save")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Full results
        full_file = f"{filename_prefix}_{timestamp}_FULL.csv"
        positions_df.to_csv(full_file, index=False)
        print(f"✅ Full results saved to {full_file}")

        # Trading plan (respecting limits)
        trading_plan = self.generate_trading_plan(positions_df)

        if not trading_plan.empty:
            plan_file = f"{filename_prefix}_{timestamp}_TRADING_PLAN.csv"
            trading_plan.to_csv(plan_file, index=False)
            print(f"✅ Trading plan saved to {plan_file}")

            # Summary
            print(f"\n📊 TRADING PLAN SUMMARY")
            print(f"   Selected Positions: {len(trading_plan)}")
            print(f"   Total Risk:         {trading_plan['portfolio_risk_pct'].iloc[0]:.2f}%")
            print(f"   Total Capital:      ${trading_plan['position_value'].sum():,.2f}")


    def print_summary_table(self, positions_df: pd.DataFrame):
        """
        Print a summary table of positions.

        Args:
            positions_df: DataFrame of positions
        """
        if positions_df.empty:
            print("❌ No positions to display")
            return

        print("\n" + "="*120)
        print("POSITION SIZING SUMMARY")
        print("="*120)

        # Select key columns
        summary_cols = [
            'symbol', 'conviction_level', 'entry_price', 'shares',
            'position_value', 'position_pct_of_account', 'final_risk_pct',
            'stop_price', 'stop_percent', 'target_1_price', 'risk_reward_ratio'
        ]

        display_df = positions_df[summary_cols].copy()

        # Format for display
        display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
        display_df['shares'] = display_df['shares'].apply(lambda x: f"{x:,}")
        display_df['position_value'] = display_df['position_value'].apply(lambda x: f"${x:,.0f}")
        display_df['position_pct_of_account'] = display_df['position_pct_of_account'].apply(lambda x: f"{x:.1f}%")
        display_df['final_risk_pct'] = display_df['final_risk_pct'].apply(lambda x: f"{x:.2f}%")
        display_df['stop_price'] = display_df['stop_price'].apply(lambda x: f"${x:,.2f}")
        display_df['stop_percent'] = display_df['stop_percent'].apply(lambda x: f"{x:.1f}%")
        display_df['target_1_price'] = display_df['target_1_price'].apply(lambda x: f"${x:,.2f}")
        display_df['risk_reward_ratio'] = display_df['risk_reward_ratio'].apply(lambda x: f"1:{x:.1f}")

        # Rename columns for display
        display_df.columns = [
            'Symbol', 'Conv', 'Entry', 'Shares', 'Position $', 'Pos %',
            'Risk %', 'Stop $', 'Stop %', 'Target 1', 'R:R'
        ]

        print(display_df.to_string(index=False))
        print("="*120)


def main():
    """
    Main function for batch position sizing.
    """
    print("="*80)
    print("BATCH POSITION CALCULATOR - $2M Account")
    print("="*80)

    calc = BatchPositionCalculator(account_size=2_000_000)

    # Menu
    print("\nSelect calculation mode:")
    print("1. Calculate from watchlist (manual symbol entry)")
    print("2. Calculate from technical screening results (CSV file)")
    print("3. Calculate for top N fundamental stocks")

    choice = input("\nChoice (1-3): ").strip()

    market_health = input("Current Market Health (bull/uptrend/neutral/choppy/downtrend): ").strip().lower()

    if choice == '1':
        # Manual watchlist
        print("\nEnter symbols separated by commas (e.g., AAPL,NVDA,MSFT):")
        symbols_input = input("Symbols: ").strip().upper()
        symbols = [s.strip() for s in symbols_input.split(',')]

        # Get conviction levels
        conviction_levels = {}
        print("\nEnter conviction level for each symbol (1-5):")
        for symbol in symbols:
            conv = int(input(f"  {symbol}: "))
            conviction_levels[symbol] = conv

        positions_df = calc.calculate_positions_for_watchlist(
            symbols=symbols,
            conviction_levels=conviction_levels,
            market_health=market_health
        )

    elif choice == '2':
        # From technical screening file
        tech_file = input("\nPath to technical screening CSV: ").strip()
        min_conviction = int(input("Minimum conviction level (3-5): "))

        positions_df = calc.calculate_positions_from_technical_screen(
            technical_results_file=tech_file,
            market_health=market_health,
            min_conviction=min_conviction
        )

    elif choice == '3':
        # Top N fundamental stocks
        n = int(input("\nHow many top stocks to analyze? "))
        default_conviction = int(input("Default conviction level (1-5): "))

        # Load screening data
        screening_data = calc.load_screening_data()

        # Take top N by fundamental score
        top_stocks = screening_data.nlargest(n, 'fundamental_percentage')
        symbols = top_stocks['symbol'].tolist()
        conviction_levels = {s: default_conviction for s in symbols}

        positions_df = calc.calculate_positions_for_watchlist(
            symbols=symbols,
            conviction_levels=conviction_levels,
            market_health=market_health
        )

    else:
        print("Invalid choice")
        return

    # Display results
    if not positions_df.empty:
        calc.print_summary_table(positions_df)

        # Save option
        save = input("\n💾 Save results? (y/n): ").strip().lower()
        if save == 'y':
            calc.save_results(positions_df)
    else:
        print("\n❌ No positions calculated")


if __name__ == "__main__":
    main()
