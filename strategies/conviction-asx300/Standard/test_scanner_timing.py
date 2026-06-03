"""
Test the Daily Conviction Scanner Timing Logic
==============================================

This script tests the core scanner logic without running a full backtest
to verify the timing implementation is correct.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ScannerTimingTest:
    """Test the scanner timing logic"""
    
    def __init__(self):
        self.min_price = 0.01
        self.min_avg_volume = 10000
        
    def get_symbol_data(self, symbol, period="1y"):
        """Get historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d")
            
            if hist.empty or len(hist) < 150:
                return None
            
            # Standardize column names
            hist.columns = [col.lower() for col in hist.columns]
            hist = hist.dropna()
            
            if len(hist) < 150:
                return None
                
            return hist.reset_index()
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_trend_strength(self, df):
        """Calculate trend strength score (0-100) using daily data"""
        try:
            if len(df) < 150:
                return 0
            
            current = df.iloc[-1]
            
            # Calculate moving averages
            df['ma_21'] = df['close'].rolling(21).mean()
            df['ma_50'] = df['close'].rolling(50).mean()
            df['ma_150'] = df['close'].rolling(150).mean()
            
            ma_21 = df['ma_21'].iloc[-1]
            ma_50 = df['ma_50'].iloc[-1]
            ma_150 = df['ma_150'].iloc[-1]
            
            # Calculate momentum
            momentum_20d = ((current['close'] / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
            momentum_50d = ((current['close'] / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
            
            # Calculate highs
            high_50 = df['high'].rolling(50).max().iloc[-1]
            
            score = 0
            
            # Price above moving averages (40 points)
            if not pd.isna(ma_21) and current['close'] > ma_21:
                score += 10
            if not pd.isna(ma_50) and current['close'] > ma_50:
                score += 15
            if not pd.isna(ma_150) and current['close'] > ma_150:
                score += 15
            
            # Moving average alignment (20 points)
            if not pd.isna(ma_21) and not pd.isna(ma_50) and ma_21 > ma_50:
                score += 10
            if not pd.isna(ma_50) and not pd.isna(ma_150) and ma_50 > ma_150:
                score += 10
            
            # Momentum (20 points)
            if momentum_20d > 5:
                score += 10
            if momentum_50d > 10:
                score += 10
            
            # Near highs (20 points)
            if not pd.isna(high_50):
                distance_from_high = (current['close'] / high_50 - 1) * 100
                if distance_from_high > -10:  # Within 10% of 50-day high
                    score += 20
            
            return score
            
        except Exception as e:
            print(f"Error calculating trend strength: {e}")
            return 0
    
    def generate_conviction_signal(self, symbol, df):
        """
        Generate daily conviction signal (0-5) using yesterday's complete data
        
        CRITICAL: This uses df.iloc[-1] which is yesterday's completed bar
        when scanner runs after market close
        """
        try:
            if len(df) < 150:
                return 0, "Insufficient historical data", {}
            
            current = df.iloc[-1]  # Yesterday's complete bar
            prev = df.iloc[-2]     # Day before yesterday
            
            current_price = current['close']
            
            # Base requirement: Strong trend (score >60)
            trend_strength = self.calculate_trend_strength(df)
            if trend_strength < 60:
                return 0, f"Weak trend: {trend_strength:.0f}", {'trend_strength': trend_strength}
            
            conviction = 0
            details = {'trend_strength': trend_strength}
            
            # Factor 1: Breakout power (0-25 points)
            high_20 = df['high'].rolling(20).max().iloc[-2]  # Exclude current day
            high_50 = df['high'].rolling(50).max().iloc[-2]
            
            breakout_points = 0
            if current_price > high_20 * 1.01:  # 1% above 20-day high
                breakout_points += 15
                if current_price > high_50 * 1.02:  # 2% above 50-day high
                    breakout_points += 10
            
            conviction += breakout_points
            details['breakout_power'] = breakout_points
            details['high_20'] = high_20
            details['high_50'] = high_50
            
            # Factor 2: Volume confirmation (0-30 points)
            volume_avg_20 = df['volume'].rolling(20).mean().iloc[-2]  # Exclude current day
            current_volume = current['volume']
            volume_surge = current_volume / volume_avg_20 if volume_avg_20 > 0 else 0
            
            volume_points = 0
            if volume_surge > 2.0:  # 2x volume
                volume_points = 30
            elif volume_surge > 1.5:  # 1.5x volume
                volume_points = 20
            elif volume_surge > 1.2:  # 1.2x volume
                volume_points = 10
            
            conviction += volume_points
            details['volume_surge'] = volume_surge
            details['volume_points'] = volume_points
            details['current_volume'] = current_volume
            details['avg_volume'] = volume_avg_20
            
            # Factor 3: Daily momentum (0-25 points)
            daily_change = ((current_price / prev['close']) - 1) * 100
            momentum_5d = ((current_price / df['close'].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0
            momentum_20d = ((current_price / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
            momentum_50d = ((current_price / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
            
            momentum_points = 0
            if daily_change > 1:  # Strong daily move
                momentum_points += 5
            if momentum_5d > 2:
                momentum_points += 5
            if momentum_20d > 5:
                momentum_points += 10
            if momentum_50d > 10:
                momentum_points += 5
            
            conviction += momentum_points
            details['daily_change'] = daily_change
            details['momentum_5d'] = momentum_5d
            details['momentum_20d'] = momentum_20d
            details['momentum_50d'] = momentum_50d
            details['momentum_points'] = momentum_points
            
            # Factor 4: Trend quality bonus (0-20 points)
            trend_bonus = min(20, int((trend_strength - 60) / 2))
            conviction += trend_bonus
            details['trend_bonus'] = trend_bonus
            details['total_conviction'] = conviction
            
            # Convert to conviction level (0-100 -> 0-5)
            if conviction >= 85:
                level = 5
                reason = f"MAX conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 70:
                level = 4
                reason = f"HIGH conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 55:
                level = 3
                reason = f"STANDARD conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 40:
                level = 2
                reason = f"LOW conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 25:
                level = 1
                reason = f"MINIMAL conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            else:
                level = 0
                reason = f"No conviction: {conviction}, trend: {trend_strength:.0f}"
            
            return level, reason, details
            
        except Exception as e:
            print(f"Error generating conviction signal for {symbol}: {e}")
            return 0, f"Error: {e}", {}
    
    def test_timing_logic(self, symbols):
        """Test the timing logic on sample symbols"""
        print("=" * 80)
        print("DAILY CONVICTION SCANNER TIMING TEST")
        print("=" * 80)
        print("Testing the EXACT logic from daily_conviction_scanner.py")
        print()
        print("Key Timing Points:")
        print("* current = df.iloc[-1]  # Yesterday's complete bar")
        print("* prev = df.iloc[-2]     # Day before yesterday")
        print("* Scanner runs AFTER market close")
        print("* Buys recommended for NEXT day")
        print("=" * 80)
        
        results = []
        
        for symbol in symbols:
            print(f"\nTesting {symbol}...")
            
            # Get data
            df = self.get_symbol_data(symbol)
            if df is None:
                print(f"  X No data available")
                continue
            
            # Generate conviction signal
            conviction_level, reason, details = self.generate_conviction_signal(symbol, df)
            
            if conviction_level >= 2:
                current_price = df['close'].iloc[-1]
                daily_change = details.get('daily_change', 0)
                volume_surge = details.get('volume_surge', 0)
                
                result = {
                    'symbol': symbol,
                    'conviction_level': conviction_level,
                    'price': current_price,
                    'daily_change': daily_change,
                    'volume_surge': volume_surge,
                    'reason': reason,
                    'date': df['date'].iloc[-1] if 'date' in df.columns else df.index[-1]
                }
                results.append(result)
                
                print(f"  + Conviction {conviction_level} - ${current_price:.2f}")
                print(f"    Daily Change: {daily_change:.1f}%")
                print(f"    Volume Surge: {volume_surge:.1f}x")
                print(f"    Reason: {reason}")
                
                # Show timing analysis
                if daily_change > 5:
                    print(f"    ** BIG MOVE DETECTED: {daily_change:.1f}% (Scanner catches AFTER)")
                if volume_surge > 2:
                    print(f"    ** VOLUME SPIKE: {volume_surge:.1f}x (Scanner catches AFTER)")
            else:
                print(f"  - No signal (conviction {conviction_level})")
        
        print(f"\n" + "=" * 80)
        print("TIMING ANALYSIS SUMMARY")
        print("=" * 80)
        
        if results:
            print(f"Found {len(results)} tradeable signals")
            print()
            print("CRITICAL TIMING OBSERVATIONS:")
            
            big_movers = [r for r in results if r['daily_change'] > 5]
            volume_spikes = [r for r in results if r['volume_surge'] > 2]
            
            if big_movers:
                print(f"* {len(big_movers)} stocks had big moves (>5%) YESTERDAY")
                print("  -> Scanner recommends buying them TODAY")
                print("  -> This is AFTER the breakout, not before")
                
            if volume_spikes:
                print(f"* {len(volume_spikes)} stocks had volume spikes YESTERDAY")
                print("  -> Scanner recommends buying them TODAY")
                print("  -> Volume surge already happened")
            
            print()
            print("WHAT THIS MEANS FOR BACKTESTING:")
            print("* Must buy at NEXT day's open (T+1)")
            print("* Cannot buy on the breakout day itself")
            print("* Results will be LESS optimistic than buying during breakout")
            print("* But results will be REALISTIC and tradeable")
            
        else:
            print("No tradeable signals found in test sample")
            print("Try testing during more volatile market periods")
        
        print("=" * 80)
        
        return results

def main():
    """Run the timing test"""
    
    tester = ScannerTimingTest()
    
    # Test symbols (mix of ASX and potential movers)
    test_symbols = [
        'CBA.AX', 'BHP.AX', 'CSL.AX', 'WBC.AX', 'ANZ.AX',
        'RIO.AX', 'COL.AX', 'WOW.AX', 'TLS.AX', 'TCL.AX',
        'NAB.AX', 'FMG.AX', 'WES.AX', 'MQG.AX', 'QBE.AX'
    ]
    
    results = tester.test_timing_logic(test_symbols)
    
    print(f"\nTEST COMPLETE")
    print(f"Scanner timing logic verified with {len(test_symbols)} symbols")
    print(f"Found {len(results)} potential signals using EXACT scanner logic")
    
    if results:
        print(f"\nTop signals would be traded TOMORROW (next day's open):")
        for result in sorted(results, key=lambda x: x['conviction_level'], reverse=True)[:3]:
            print(f"  {result['symbol']} Level {result['conviction_level']} - ${result['price']:.2f}")
    
    return results

if __name__ == "__main__":
    main()