"""
Position Sizing Calculator for $2M Trading Account

Integrates:
- Liquidity screening results
- Fundamental screening results
- Technical conviction levels
- Risk management framework
- ATR-based stops
- Market health conditions

Author: Trading System
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, Optional, Tuple
import time


class PositionSizingCalculator:
    """
    Complete position sizing calculator following the risk management framework.
    """

    def __init__(self, account_size: float = 2_000_000):
        """
        Initialize calculator with account size.

        Args:
            account_size: Total account value (default $2M)
        """
        self.account_size = account_size

        # Risk Management Parameters
        self.base_risk_percent = 1.5  # Base risk per trade
        self.max_risk_per_trade = 3.0  # Hard cap
        self.max_total_portfolio_risk = 20.0  # 20% max total risk
        self.max_positions = 12
        self.max_single_position_percent = 25.0  # 25% max per stock

        # Conviction Multipliers
        self.conviction_multipliers = {
            5: 1.5,   # Level 5 = 150% of base (2.25%)
            4: 1.25,  # Level 4 = 125% of base (1.875%)
            3: 1.0,   # Level 3 = 100% of base (1.5%)
            2: 0.75,  # Level 2 = 75% of base (1.125%)
            1: 0.5,   # Level 1 = 50% of base (0.75%)
        }

        # Market Health Multipliers
        self.market_multipliers = {
            'strong_bull': 2.0,
            'bull': 1.5,
            'uptrend': 1.25,
            'neutral': 1.0,
            'choppy': 0.75,
            'downtrend': 0.5,
            'bear': 0.25,
        }

        # ATR Multipliers for Stops (by conviction)
        self.atr_stop_multipliers = {
            5: 1.5,  # Tight stops for perfect setups
            4: 2.0,  # Standard 2 ATR (Turtle style)
            3: 2.5,  # Slightly wider
            2: 3.0,  # Wide
            1: 3.0,  # Skip these
        }

        # Maximum Stop Loss Percentages (caps)
        self.max_stop_percent = {
            5: 5.0,   # Max 5% for Level 5
            4: 7.0,   # Max 7% for Level 4
            3: 8.0,   # Max 8% for Level 3
            2: 10.0,  # Max 10% for Level 2
            1: 10.0,  # Skip these
        }

        # Position Size Limits by Tier
        self.position_limits_by_tier = {
            'TIER 1 - EXCELLENT': 25,  # Can go up to 25%
            'TIER 2 - GOOD': 20,       # Max 20%
            'TIER 3 - ADEQUATE': 15,   # Max 15%
        }

        # Liquidity Limits (position as % of DDV)
        self.max_position_pct_of_ddv = 2.0  # 2% max

        # Current portfolio tracking
        self.current_positions = []
        self.current_total_risk = 0.0


    def calculate_atr(self, symbol: str, period: int = 14) -> Optional[float]:
        """
        Calculate Average True Range (ATR) for a symbol.

        Args:
            symbol: Stock ticker
            period: ATR period (default 14 days)

        Returns:
            ATR value or None if error
        """
        try:
            # Fetch historical data (need extra days for calculation)
            stock = yf.Ticker(symbol)
            hist = stock.history(period=f"{period + 10}d")

            if len(hist) < period:
                print(f"⚠️  Warning: Insufficient data for {symbol} ATR calculation")
                return None

            # Calculate True Range
            high = hist['High']
            low = hist['Low']
            close = hist['Close'].shift(1)

            tr1 = high - low
            tr2 = abs(high - close)
            tr3 = abs(low - close)

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Calculate ATR (simple moving average of TR)
            atr = tr.rolling(window=period).mean().iloc[-1]

            return round(atr, 2)

        except Exception as e:
            print(f"❌ Error calculating ATR for {symbol}: {e}")
            return None


    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Current price or None if error
        """
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")

            if len(hist) == 0:
                print(f"⚠️  Warning: No price data for {symbol}")
                return None

            return round(hist['Close'].iloc[-1], 2)

        except Exception as e:
            print(f"❌ Error fetching price for {symbol}: {e}")
            return None


    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        conviction_level: int,
        pattern_type: str = 'standard'
    ) -> Tuple[float, float]:
        """
        Calculate stop loss price and percentage.

        Args:
            entry_price: Entry price
            atr: Average True Range
            conviction_level: Technical conviction level (1-5)
            pattern_type: Pattern type (standard, vcp, episodic_pivot)

        Returns:
            Tuple of (stop_price, stop_percent)
        """
        # Get ATR multiplier for conviction level
        atr_multiplier = self.atr_stop_multipliers.get(conviction_level, 2.5)

        # Adjust for pattern type
        if pattern_type == 'vcp':
            atr_multiplier = min(atr_multiplier, 1.0)  # Even tighter for VCP

        # Calculate ATR-based stop
        atr_stop_distance = atr * atr_multiplier
        atr_stop_price = entry_price - atr_stop_distance
        atr_stop_percent = (atr_stop_distance / entry_price) * 100

        # Get maximum stop percentage cap
        max_stop_pct = self.max_stop_percent.get(conviction_level, 8.0)
        max_stop_price = entry_price * (1 - max_stop_pct / 100)

        # Use tighter of ATR-based or percentage cap
        final_stop_price = max(atr_stop_price, max_stop_price)
        final_stop_percent = ((entry_price - final_stop_price) / entry_price) * 100

        return round(final_stop_price, 2), round(final_stop_percent, 2)


    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        atr: float,
        conviction_level: int,
        market_health: str,
        liquidity_tier: str,
        ddv: float,
        fundamental_score: Optional[float] = None,
        pattern_type: str = 'standard'
    ) -> Dict:
        """
        Complete position sizing calculation.

        Args:
            symbol: Stock ticker
            entry_price: Entry price
            atr: Average True Range
            conviction_level: Technical conviction level (1-5)
            market_health: Market condition (bull, uptrend, neutral, etc.)
            liquidity_tier: Liquidity tier classification
            ddv: Daily Dollar Volume
            fundamental_score: Optional fundamental score percentage
            pattern_type: Pattern type (standard, vcp, episodic_pivot)

        Returns:
            Dictionary with complete position sizing details
        """
        # Step 1: Calculate Stop Loss
        stop_price, stop_percent = self.calculate_stop_loss(
            entry_price, atr, conviction_level, pattern_type
        )
        stop_distance = entry_price - stop_price

        # Step 2: Calculate Risk Percentage
        tech_mult = self.conviction_multipliers.get(conviction_level, 1.0)
        market_mult = self.market_multipliers.get(market_health.lower(), 1.0)

        conviction_risk_pct = self.base_risk_percent * tech_mult * market_mult

        # Apply maximum cap
        final_risk_pct = min(conviction_risk_pct, self.max_risk_per_trade)
        dollar_risk = self.account_size * (final_risk_pct / 100)

        # Step 3: Calculate Shares (based on dollar risk and stop distance)
        shares = int(dollar_risk / stop_distance)

        # Step 4: Calculate Position Value
        position_value = shares * entry_price
        position_pct = (position_value / self.account_size) * 100

        # Step 5: Apply Position Size Limits

        # Limit by conviction level
        conviction_position_limits = {
            5: 25,  # Max 25% for Level 5
            4: 20,  # Max 20% for Level 4
            3: 15,  # Max 15% for Level 3
            2: 10,  # Max 10% for Level 2
            1: 5,   # Max 5% for Level 1
        }
        max_position_by_conviction = conviction_position_limits.get(conviction_level, 15)

        # Limit by liquidity tier
        max_position_by_tier = self.position_limits_by_tier.get(liquidity_tier, 10)

        # Use most restrictive limit
        max_position_pct = min(
            max_position_by_conviction,
            max_position_by_tier,
            self.max_single_position_percent
        )
        max_position_value = self.account_size * (max_position_pct / 100)

        # Step 6: Check Liquidity Limits
        liquidity_limit_value = ddv * (self.max_position_pct_of_ddv / 100)

        # Apply most restrictive limit
        final_max_value = min(max_position_value, liquidity_limit_value)

        limited = False
        limiting_factor = None

        if position_value > final_max_value:
            limited = True
            # Determine which limit was hit
            if liquidity_limit_value < max_position_value:
                limiting_factor = 'liquidity'
            else:
                limiting_factor = 'position_size'

            # Recalculate with limit
            position_value = final_max_value
            shares = int(position_value / entry_price)
            position_pct = (position_value / self.account_size) * 100

            # Recalculate actual risk
            actual_risk = shares * stop_distance
            final_risk_pct = (actual_risk / self.account_size) * 100
            dollar_risk = actual_risk

        # Step 7: Calculate Position as % of DDV
        position_pct_of_ddv = (position_value / ddv) * 100

        # Step 8: Calculate Profit Targets (ATR-based)
        target_1_price = entry_price + (atr * 2)  # 2 ATR
        target_1_percent = ((target_1_price - entry_price) / entry_price) * 100

        target_2_price = entry_price + (atr * 4)  # 4 ATR
        target_2_percent = ((target_2_price - entry_price) / entry_price) * 100

        target_3_price = entry_price + (atr * 6)  # 6 ATR
        target_3_percent = ((target_3_price - entry_price) / entry_price) * 100

        # Step 9: Calculate Risk/Reward Ratio
        risk_amount = stop_percent
        reward_amount = target_1_percent
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

        # Step 10: Calculate R-Multiples for targets
        r_multiple_1 = target_1_percent / stop_percent if stop_percent > 0 else 0
        r_multiple_2 = target_2_percent / stop_percent if stop_percent > 0 else 0
        r_multiple_3 = target_3_percent / stop_percent if stop_percent > 0 else 0

        # Compile results
        result = {
            # Input Parameters
            'symbol': symbol,
            'entry_price': entry_price,
            'atr': atr,
            'conviction_level': conviction_level,
            'market_health': market_health,
            'liquidity_tier': liquidity_tier,
            'ddv': ddv,
            'fundamental_score': fundamental_score,
            'pattern_type': pattern_type,

            # Risk Calculation
            'base_risk_pct': self.base_risk_percent,
            'conviction_multiplier': tech_mult,
            'market_multiplier': market_mult,
            'calculated_risk_pct': round(conviction_risk_pct, 3),
            'final_risk_pct': round(final_risk_pct, 3),
            'dollar_risk': round(dollar_risk, 2),

            # Stop Loss
            'stop_price': stop_price,
            'stop_percent': stop_percent,
            'stop_distance': round(stop_distance, 2),
            'atr_multiplier': self.atr_stop_multipliers.get(conviction_level, 2.5),

            # Position Size
            'shares': shares,
            'position_value': round(position_value, 2),
            'position_pct_of_account': round(position_pct, 2),
            'position_pct_of_ddv': round(position_pct_of_ddv, 3),

            # Limits Applied
            'limited': limited,
            'limiting_factor': limiting_factor,
            'max_position_by_conviction': max_position_by_conviction,
            'max_position_by_tier': max_position_by_tier,
            'liquidity_limit_value': round(liquidity_limit_value, 2),

            # Profit Targets
            'target_1_price': round(target_1_price, 2),
            'target_1_percent': round(target_1_percent, 2),
            'target_1_r_multiple': round(r_multiple_1, 2),
            'target_2_price': round(target_2_price, 2),
            'target_2_percent': round(target_2_percent, 2),
            'target_2_r_multiple': round(r_multiple_2, 2),
            'target_3_price': round(target_3_price, 2),
            'target_3_percent': round(target_3_percent, 2),
            'target_3_r_multiple': round(r_multiple_3, 2),

            # Risk/Reward
            'risk_reward_ratio': round(risk_reward_ratio, 2),

            # Scaled Exit Values (33/33/34 method)
            'exit_1_shares': int(shares * 0.33),
            'exit_2_shares': int(shares * 0.33),
            'exit_3_shares': shares - (int(shares * 0.33) * 2),
        }

        return result


    def check_portfolio_limits(self, new_position_risk: float) -> Tuple[bool, str]:
        """
        Check if adding a new position would exceed portfolio limits.

        Args:
            new_position_risk: Risk % of new position

        Returns:
            Tuple of (can_add, message)
        """
        # Check position count
        if len(self.current_positions) >= self.max_positions:
            return False, f"Maximum positions reached ({self.max_positions})"

        # Check total portfolio risk
        new_total_risk = self.current_total_risk + new_position_risk
        if new_total_risk > self.max_total_portfolio_risk:
            remaining_risk = self.max_total_portfolio_risk - self.current_total_risk
            return False, f"Would exceed max portfolio risk. Available: {remaining_risk:.2f}%"

        return True, "OK"


    def add_position_to_portfolio(self, position: Dict):
        """
        Add a position to the portfolio tracker.

        Args:
            position: Position dictionary from calculate_position_size()
        """
        self.current_positions.append(position)
        self.current_total_risk += position['final_risk_pct']


    def get_portfolio_summary(self) -> Dict:
        """
        Get summary of current portfolio.

        Returns:
            Dictionary with portfolio statistics
        """
        if not self.current_positions:
            return {
                'total_positions': 0,
                'total_risk_pct': 0,
                'total_capital_deployed': 0,
                'average_position_size': 0,
                'available_risk': self.max_total_portfolio_risk,
                'available_positions': self.max_positions,
            }

        total_value = sum(p['position_value'] for p in self.current_positions)

        return {
            'total_positions': len(self.current_positions),
            'total_risk_pct': round(self.current_total_risk, 2),
            'total_capital_deployed': round(total_value, 2),
            'capital_deployed_pct': round((total_value / self.account_size) * 100, 2),
            'average_position_size': round(total_value / len(self.current_positions), 2),
            'available_risk': round(self.max_total_portfolio_risk - self.current_total_risk, 2),
            'available_positions': self.max_positions - len(self.current_positions),
        }


    def print_position_report(self, position: Dict, detailed: bool = True):
        """
        Print formatted position sizing report.

        Args:
            position: Position dictionary
            detailed: Include detailed breakdown
        """
        print("\n" + "="*80)
        print(f"POSITION SIZING REPORT: {position['symbol']}")
        print("="*80)

        # Summary Section
        print("\n📊 POSITION SUMMARY")
        print(f"   Entry Price:        ${position['entry_price']:,.2f}")
        print(f"   Shares:             {position['shares']:,}")
        print(f"   Position Value:     ${position['position_value']:,.2f} ({position['position_pct_of_account']:.2f}% of account)")
        print(f"   Dollar Risk:        ${position['dollar_risk']:,.2f} ({position['final_risk_pct']:.2f}% risk)")

        # Stop Loss Section
        print("\n🛑 STOP LOSS")
        print(f"   Stop Price:         ${position['stop_price']:,.2f}")
        print(f"   Stop Distance:      ${position['stop_distance']:.2f} ({position['stop_percent']:.2f}%)")
        print(f"   ATR:                ${position['atr']:.2f} (using {position['atr_multiplier']}x multiplier)")

        # Profit Targets Section
        print("\n🎯 PROFIT TARGETS (33/33/34 Exit Strategy)")
        print(f"   Target 1 (2 ATR):   ${position['target_1_price']:,.2f} (+{position['target_1_percent']:.1f}%) = {position['target_1_r_multiple']:.1f}R")
        print(f"      → Sell {position['exit_1_shares']:,} shares, move stop to breakeven")
        print(f"   Target 2 (4 ATR):   ${position['target_2_price']:,.2f} (+{position['target_2_percent']:.1f}%) = {position['target_2_r_multiple']:.1f}R")
        print(f"      → Sell {position['exit_2_shares']:,} shares, move stop to Target 1")
        print(f"   Target 3 (6 ATR):   ${position['target_3_price']:,.2f} (+{position['target_3_percent']:.1f}%) = {position['target_3_r_multiple']:.1f}R")
        print(f"      → Trail final {position['exit_3_shares']:,} shares with 10/20 MA")

        # Risk/Reward
        print("\n⚖️  RISK/REWARD")
        print(f"   Risk Amount:        {position['stop_percent']:.2f}%")
        print(f"   Reward (Target 1):  {position['target_1_percent']:.2f}%")
        print(f"   Risk/Reward Ratio:  1:{position['risk_reward_ratio']:.2f}")

        if detailed:
            # Detailed Parameters
            print("\n📋 DETAILED PARAMETERS")
            print(f"   Conviction Level:   Level {position['conviction_level']} ({position['conviction_multiplier']}x multiplier)")
            print(f"   Market Health:      {position['market_health']} ({position['market_multiplier']}x multiplier)")
            print(f"   Liquidity Tier:     {position['liquidity_tier']}")
            print(f"   Pattern Type:       {position['pattern_type']}")
            if position['fundamental_score']:
                print(f"   Fundamental Score:  {position['fundamental_score']:.1f}%")

            # Risk Calculation Breakdown
            print("\n🔢 RISK CALCULATION")
            print(f"   Base Risk:          {position['base_risk_pct']:.2f}%")
            print(f"   × Conviction ({position['conviction_multiplier']}x):  {position['base_risk_pct'] * position['conviction_multiplier']:.2f}%")
            print(f"   × Market ({position['market_multiplier']}x):      {position['calculated_risk_pct']:.2f}%")
            print(f"   Capped at:          {position['final_risk_pct']:.2f}% (max {self.max_risk_per_trade}%)")

            # Limits Applied
            print("\n🚦 LIMITS & CHECKS")
            print(f"   Max by Conviction:  {position['max_position_by_conviction']}% of account")
            print(f"   Max by Liquidity:   {position['max_position_by_tier']}% of account")
            print(f"   Position vs DDV:    {position['position_pct_of_ddv']:.3f}% (max {self.max_position_pct_of_ddv}%)")

            if position['limited']:
                print(f"   ⚠️  LIMITED BY:       {position['limiting_factor'].upper()}")

        print("\n" + "="*80)


    def save_position_to_csv(self, position: Dict, filename: str):
        """
        Save position details to CSV file.

        Args:
            position: Position dictionary
            filename: Output filename
        """
        df = pd.DataFrame([position])
        df.to_csv(filename, index=False)
        print(f"✅ Position saved to {filename}")


def main():
    """
    Main function for interactive position sizing.
    """
    print("="*80)
    print("POSITION SIZING CALCULATOR - $2M Account")
    print("="*80)

    # Initialize calculator
    calc = PositionSizingCalculator(account_size=2_000_000)

    # Example usage
    print("\n📝 Enter trade details:")

    symbol = input("Symbol: ").strip().upper()
    entry_price = float(input("Entry Price: $"))
    conviction_level = int(input("Conviction Level (1-5): "))
    market_health = input("Market Health (bull/uptrend/neutral/choppy/downtrend/bear): ").strip().lower()
    liquidity_tier = input("Liquidity Tier (TIER 1 - EXCELLENT / TIER 2 - GOOD / TIER 3 - ADEQUATE): ").strip()
    ddv = float(input("Daily Dollar Volume: $"))

    # Optional fundamental score
    fund_score_input = input("Fundamental Score % (optional, press Enter to skip): ").strip()
    fundamental_score = float(fund_score_input) if fund_score_input else None

    pattern_type = input("Pattern Type (standard/vcp/episodic_pivot): ").strip().lower()

    # Fetch ATR
    print(f"\n⏳ Fetching ATR for {symbol}...")
    atr = calc.calculate_atr(symbol)

    if atr is None:
        atr = float(input(f"⚠️  Could not fetch ATR. Enter manually: $"))
    else:
        print(f"✅ ATR: ${atr:.2f}")

    # Check portfolio limits
    temp_position = calc.calculate_position_size(
        symbol=symbol,
        entry_price=entry_price,
        atr=atr,
        conviction_level=conviction_level,
        market_health=market_health,
        liquidity_tier=liquidity_tier,
        ddv=ddv,
        fundamental_score=fundamental_score,
        pattern_type=pattern_type
    )

    can_add, message = calc.check_portfolio_limits(temp_position['final_risk_pct'])

    if not can_add:
        print(f"\n❌ PORTFOLIO LIMIT EXCEEDED: {message}")
        return

    # Calculate and display
    position = temp_position
    calc.print_position_report(position, detailed=True)

    # Portfolio Summary
    print("\n📊 PORTFOLIO SUMMARY (if added)")
    calc.add_position_to_portfolio(position)
    summary = calc.get_portfolio_summary()
    print(f"   Total Positions:    {summary['total_positions']}/{calc.max_positions}")
    print(f"   Total Risk:         {summary['total_risk_pct']:.2f}% / {calc.max_total_portfolio_risk}%")
    print(f"   Capital Deployed:   ${summary['total_capital_deployed']:,.2f} ({summary['capital_deployed_pct']:.1f}%)")
    print(f"   Available Risk:     {summary['available_risk']:.2f}%")

    # Save option
    save = input("\n💾 Save to CSV? (y/n): ").strip().lower()
    if save == 'y':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"position_{symbol}_{timestamp}.csv"
        calc.save_position_to_csv(position, filename)


if __name__ == "__main__":
    main()
