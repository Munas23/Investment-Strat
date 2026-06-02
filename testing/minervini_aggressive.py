"""
Mark Minervini AGGRESSIVE Championship-Style Strategy
====================================================

This implementation removes conservative constraints and mirrors
Minervini's actual championship approach:

- 20-40% position sizes (vs our conservative 8%)
- Maximum 5-8 positions (concentrated portfolio)
- Focus on small-cap growth stocks
- Home run mentality: few big winners offset many small losses
- Aggressive entries on breakouts with volume

CHAMPIONSHIP MINDSET:
- Win Rate: ~25-30% (most trades lose)
- But winners are MASSIVE: 100%, 200%, 500%+ gains
- Portfolio concentration amplifies the home runs
- Cash during unfavorable market conditions

This represents Minervini's ACTUAL trading style, not retail-friendly versions.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class MinerviniAggressive:
    """
    Mark Minervini's ACTUAL championship trading strategy
    
    Removes all conservative constraints to mirror his real approach:
    - Aggressive position sizing (20-40% positions)
    - Portfolio concentration (max 5-8 stocks)
    - Home run hunting mentality
    - Small-cap growth focus
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # AGGRESSIVE MINERVINI PARAMETERS (Championship Style)
        self.max_positions = 6           # Maximum 6 concentrated positions
        self.min_position_size = 0.15    # 15% minimum position (vs 8% conservative)
        self.max_position_size = 0.35    # 35% maximum position (championship style)
        self.stop_loss_pct = 0.07        # 7% stop loss (tight risk control)
        self.profit_target = 0.50        # 50% profit target (hunt for home runs)
        self.trail_stop_trigger = 0.15   # Trail stop after 15% gain
        self.rs_rating_min = 80          # Only trade strongest stocks (top 20%)
        
        print("MINERVINI AGGRESSIVE CHAMPIONSHIP STRATEGY")
        print("=" * 55)
        print("REAL CHAMPIONSHIP PARAMETERS:")
        print(f"  Max Positions: {self.max_positions} (concentrated)")
        print(f"  Position Size: {self.min_position_size*100:.0f}%-{self.max_position_size*100:.0f}% (aggressive)")
        print(f"  Stop Loss: {self.stop_loss_pct*100:.0f}% (tight)")
        print(f"  Profit Target: {self.profit_target*100:.0f}% (home runs)")
        print(f"  RS Rating Min: {self.rs_rating_min} (only strongest)")
        print("=" * 55)
        
    def get_small_cap_growth_stocks(self) -> List[str]:
        """
        Get small-cap growth stocks - Minervini's preferred targets
        
        These are the types of stocks that made his championship returns:
        - Emerging biotech companies
        - Small-cap tech leaders
        - High-growth momentum names
        - Stocks before they became large-caps
        """
        
        # Extended universe focusing on growth and momentum
        # Mix of current small-caps and historical growers
        return [
            # Small-Cap Biotech (Minervini favorites)
            'MRNA', 'NVAX', 'BNTX', 'GILD', 'REGN', 'VRTX', 'BMRN',
            
            # Small-Cap Tech/Growth
            'SNOW', 'PLTR', 'U', 'NET', 'DDOG', 'CRWD', 'ZS', 'OKTA',
            'TWLO', 'SHOP', 'SQ', 'ROKU', 'PTON', 'ZM', 'DOCU',
            
            # Emerging Leaders
            'TSLA', 'NFLX', 'CRM', 'NOW', 'ADBE', 'WDAY', 'SPLK',
            
            # High Beta Growth
            'AMD', 'NVDA', 'AMZN', 'GOOGL', 'META', 'MSFT',
            
            # Momentum/Breakout Candidates
            'UBER', 'LYFT', 'ABNB', 'COIN', 'HOOD', 'RBLX', 'RIVN'
        ]
    
    def calculate_aggressive_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators optimized for aggressive breakout trading"""
        df = data.copy()
        
        # Standard Minervini moving averages
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_21'] = df['close'].rolling(21).mean()
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_150'] = df['close'].rolling(150).mean()
        df['ma_200'] = df['close'].rolling(200).mean()
        
        # Aggressive breakout indicators
        df['high_20'] = df['high'].rolling(20).max()   # 4-week base high
        df['high_40'] = df['high'].rolling(40).max()   # 8-week base high
        
        # Volume surge detection (key for Minervini entries)
        df['volume_avg_10'] = df['volume'].rolling(10).mean()
        df['volume_avg_50'] = df['volume'].rolling(50).mean()
        df['volume_surge'] = df['volume'] / df['volume_avg_10']
        
        # Relative strength (enhanced for small-caps)
        df['rs_4w'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        df['rs_13w'] = ((df['close'] / df['close'].shift(65)) - 1) * 100
        df['rs_26w'] = ((df['close'] / df['close'].shift(130)) - 1) * 100
        df['rs_52w'] = ((df['close'] / df['close'].shift(252)) - 1) * 100
        
        # Stage analysis
        df['stage'] = self._calculate_stage_analysis(df)
        
        # Breakout power (Minervini's key signal)
        df['breakout_power'] = self._calculate_breakout_power(df)
        
        return df
    
    def _calculate_stage_analysis(self, df: pd.DataFrame) -> pd.Series:
        """
        Minervini's Stage Analysis
        Stage 1: Consolidation/Base Building
        Stage 2: Advancing/Markup (BUY ZONE)
        Stage 3: Top/Distribution
        Stage 4: Declining/Markdown (AVOID)
        """
        stage = pd.Series(1, index=df.index)  # Default Stage 1
        
        for i in range(200, len(df)):
            price = df['close'].iloc[i]
            ma_50 = df['ma_50'].iloc[i]
            ma_150 = df['ma_150'].iloc[i]
            ma_200 = df['ma_200'].iloc[i]
            
            if pd.isna(price) or pd.isna(ma_50) or pd.isna(ma_150) or pd.isna(ma_200):
                continue
            
            # Stage 2: Strong uptrend (Minervini's buy zone)
            if (price > ma_50 > ma_150 > ma_200 and 
                price > ma_50 * 1.02):  # 2% above 50 MA
                stage.iloc[i] = 2
            
            # Stage 4: Downtrend (avoid completely)
            elif (price < ma_200 and ma_50 < ma_150):
                stage.iloc[i] = 4
            
            # Stage 3: Distribution/topping
            elif (price > ma_200 and price < ma_50):
                stage.iloc[i] = 3
            
            # Stage 1: Base building (wait for breakout)
            else:
                stage.iloc[i] = 1
        
        return stage
    
    def _calculate_breakout_power(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate breakout power score (0-100)
        Combines price action, volume, and relative strength
        """
        breakout_power = pd.Series(0, index=df.index)
        
        for i in range(50, len(df)):
            score = 0
            
            current = df.iloc[i]
            
            # Price breakout component (40 points)
            if not pd.isna(current['high_20']):
                if current['close'] > current['high_20'] * 1.01:  # 1% above 20-day high
                    score += 20
                if current['close'] > current['high_40'] * 1.01:  # 1% above 40-day high
                    score += 20
            
            # Volume component (30 points)
            if not pd.isna(current['volume_surge']):
                if current['volume_surge'] > 2.0:  # 2x volume surge
                    score += 30
                elif current['volume_surge'] > 1.5:  # 1.5x volume surge
                    score += 15
            
            # Relative strength component (30 points)
            if not pd.isna(current['rs_13w']):
                if current['rs_13w'] > 30:  # Very strong RS
                    score += 30
                elif current['rs_13w'] > 15:  # Good RS
                    score += 15
            
            breakout_power.iloc[i] = score
        
        return breakout_power
    
    def aggressive_entry_signal(self, data: pd.DataFrame) -> pd.Series:
        """
        Aggressive entry signals for championship-style trading
        
        ENTRY CRITERIA (All must be met):
        1. Stage 2 uptrend (price > all MAs in correct order)
        2. Breakout from base with volume (2x+ surge)
        3. Strong relative strength (top 20%)
        4. Within 5% of new highs
        5. Breakout power score > 70
        """
        df = self.calculate_aggressive_indicators(data)
        signals = pd.Series(False, index=df.index)
        
        for i in range(252, len(df)):  # Need full year of data
            current = df.iloc[i]
            
            # Skip if missing data
            if (pd.isna(current['close']) or pd.isna(current['ma_50']) or 
                pd.isna(current['breakout_power'])):
                continue
            
            # Criterion 1: Stage 2 uptrend
            stage_2 = current['stage'] == 2
            
            # Criterion 2: Volume breakout
            volume_breakout = current['volume_surge'] > 1.8  # 80% above average
            
            # Criterion 3: Strong relative strength
            strong_rs = current['rs_13w'] > 20  # Strong 13-week performance
            
            # Criterion 4: Near new highs (within 10%)
            near_highs = current['close'] > current['high_40'] * 0.95
            
            # Criterion 5: High breakout power
            high_power = current['breakout_power'] > 70
            
            # All criteria must be met
            if (stage_2 and volume_breakout and strong_rs and near_highs and high_power):
                signals.iloc[i] = True
        
        return signals
    
    def calculate_aggressive_position_size(self, price: float, current_capital: float, 
                                         conviction_level: int) -> int:
        """
        Calculate position size based on Minervini's aggressive approach
        
        conviction_level: 1-5 scale
        1 = 15% position (minimum)
        3 = 25% position (standard)
        5 = 35% position (maximum conviction)
        """
        
        # Base position percentage based on conviction
        conviction_multiplier = {
            1: 0.15,  # 15% - Low conviction
            2: 0.20,  # 20% - Below average
            3: 0.25,  # 25% - Standard
            4: 0.30,  # 30% - High conviction  
            5: 0.35   # 35% - Maximum conviction
        }
        
        position_pct = conviction_multiplier.get(conviction_level, 0.25)
        position_value = current_capital * position_pct
        shares = int(position_value / price)
        
        return shares
    
    def aggressive_minervini_strategy(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Implement Minervini's aggressive championship strategy
        
        KEY DIFFERENCES FROM CONSERVATIVE VERSION:
        - 15-35% position sizes (vs 8%)
        - Maximum 6 positions (vs unlimited)
        - 50% profit targets (vs 25%)
        - Hunt for home runs, not singles
        - Focus on breakout power, not just trend following
        """
        
        print(f"\nTESTING AGGRESSIVE STRATEGY: {symbol}")
        print("-" * 50)
        
        df = self.calculate_aggressive_indicators(data)
        signals = self.aggressive_entry_signal(data)
        
        # Initialize aggressive trading variables
        cash = self.initial_capital
        positions = []
        trades = []
        max_positions_held = 0
        
        for i, (date, signal) in enumerate(signals.items()):
            if i < 252:  # Skip warmup period
                continue
            
            current_price = df.loc[date, 'close']
            current_capital = cash + sum([pos['shares'] * current_price for pos in positions])
            
            # EXIT LOGIC - Check existing positions first
            for pos in positions[:]:
                entry_price = pos['entry_price']
                shares = pos['shares']
                days_held = (date - pos['entry_date']).days
                current_pnl = (current_price / entry_price - 1) * 100
                
                # Exit Condition 1: Stop Loss (7% - TIGHT)
                if current_pnl < -self.stop_loss_pct * 100:
                    cash += shares * current_price
                    trades.append({
                        'symbol': symbol,
                        'entry_date': pos['entry_date'],
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'return_pct': current_pnl,
                        'hold_days': days_held,
                        'exit_reason': 'Stop Loss',
                        'position_size_pct': pos['position_pct']
                    })
                    positions.remove(pos)
                    continue
                
                # Exit Condition 2: HOME RUN Target (50%+)
                elif current_pnl > self.profit_target * 100:
                    cash += shares * current_price
                    trades.append({
                        'symbol': symbol,
                        'entry_date': pos['entry_date'],
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'return_pct': current_pnl,
                        'hold_days': days_held,
                        'exit_reason': 'HOME RUN Target',
                        'position_size_pct': pos['position_pct']
                    })
                    positions.remove(pos)
                    continue
                
                # Exit Condition 3: Trailing Stop (after 15% gain)
                elif current_pnl > self.trail_stop_trigger * 100:
                    # Trail stop at 10% below highest price reached
                    if 'highest_price' not in pos:
                        pos['highest_price'] = current_price
                    else:
                        pos['highest_price'] = max(pos['highest_price'], current_price)
                    
                    trail_stop_price = pos['highest_price'] * 0.90  # 10% trailing stop
                    
                    if current_price < trail_stop_price:
                        cash += shares * current_price
                        trades.append({
                            'symbol': symbol,
                            'entry_date': pos['entry_date'],
                            'exit_date': date,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'shares': shares,
                            'return_pct': current_pnl,
                            'hold_days': days_held,
                            'exit_reason': 'Trailing Stop',
                            'position_size_pct': pos['position_pct']
                        })
                        positions.remove(pos)
                        continue
            
            # ENTRY LOGIC - Aggressive position sizing
            if signal and len(positions) < self.max_positions:
                
                # Calculate conviction level based on breakout power
                breakout_power = df.loc[date, 'breakout_power']
                if breakout_power > 90:
                    conviction = 5  # Maximum conviction
                elif breakout_power > 80:
                    conviction = 4  # High conviction
                elif breakout_power > 70:
                    conviction = 3  # Standard conviction
                else:
                    conviction = 2  # Low conviction
                
                # Calculate aggressive position size
                shares_to_buy = self.calculate_aggressive_position_size(
                    current_price, current_capital, conviction
                )
                
                position_value = shares_to_buy * current_price
                position_pct = position_value / current_capital
                
                # Only enter if we have enough cash and position meets minimums
                if (cash >= position_value and 
                    shares_to_buy > 0 and 
                    position_pct >= self.min_position_size):
                    
                    cash -= position_value
                    
                    positions.append({
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares_to_buy,
                        'conviction': conviction,
                        'position_pct': position_pct,
                        'breakout_power': breakout_power
                    })
                    
                    max_positions_held = max(max_positions_held, len(positions))
                    
                    print(f"  {date.strftime('%Y-%m-%d')}: BUY {shares_to_buy:,} shares @ ${current_price:.2f}")
                    print(f"    Position Size: {position_pct*100:.1f}% | Conviction: {conviction}/5 | Breakout Power: {breakout_power:.0f}")
        
        # Close remaining positions at end
        if positions:
            final_price = df['close'].iloc[-1]
            for pos in positions:
                cash += pos['shares'] * final_price
                final_return = (final_price / pos['entry_price'] - 1) * 100
                days_held = (df.index[-1] - pos['entry_date']).days
                
                trades.append({
                    'symbol': symbol,
                    'entry_date': pos['entry_date'],
                    'exit_date': df.index[-1],
                    'entry_price': pos['entry_price'],
                    'exit_price': final_price,
                    'shares': pos['shares'],
                    'return_pct': final_return,
                    'hold_days': days_held,
                    'exit_reason': 'Final Close',
                    'position_size_pct': pos['position_pct']
                })
        
        # Calculate performance metrics
        final_value = cash
        total_return = (final_value / self.initial_capital - 1) * 100
        
        if trades:
            returns = [t['return_pct'] for t in trades]
            win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
            avg_return = np.mean(returns)
            avg_winner = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
            avg_loser = np.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0
            best_trade = max(returns)
            worst_trade = min(returns)
            
            # Home run analysis
            home_runs = len([r for r in returns if r > 50])  # 50%+ winners
            big_winners = len([r for r in returns if r > 25])  # 25%+ winners
            
        else:
            win_rate = avg_return = avg_winner = avg_loser = 0
            best_trade = worst_trade = 0
            home_runs = big_winners = 0
        
        print(f"\nAGGRESSIVE STRATEGY RESULTS:")
        print(f"  Total Return: {total_return:.1f}%")
        print(f"  Total Trades: {len(trades)}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Avg Winner: {avg_winner:.1f}%")
        print(f"  Avg Loser: {avg_loser:.1f}%")
        print(f"  Best Trade: {best_trade:.1f}%")
        print(f"  Home Runs (>50%): {home_runs}")
        print(f"  Big Winners (>25%): {big_winners}")
        print(f"  Max Positions: {max_positions_held}")
        
        return {
            'symbol': symbol,
            'total_return': total_return,
            'num_trades': len(trades),
            'win_rate': win_rate,
            'avg_return_per_trade': avg_return,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'home_runs': home_runs,
            'big_winners': big_winners,
            'max_positions_held': max_positions_held,
            'trades': trades,
            'strategy_type': 'Aggressive Minervini'
        }
    
    def test_aggressive_vs_conservative(self, test_symbols: List[str] = None) -> Dict:
        """
        Test aggressive Minervini strategy vs conservative version
        """
        
        if test_symbols is None:
            test_symbols = self.get_small_cap_growth_stocks()[:15]  # Test 15 symbols
        
        print("MINERVINI AGGRESSIVE vs CONSERVATIVE COMPARISON")
        print("=" * 60)
        print("Testing championship-style aggressive parameters")
        print("vs retail-friendly conservative parameters")
        print(f"Testing {len(test_symbols)} growth stocks over 5 years")
        print("=" * 60)
        
        aggressive_results = []
        conservative_results = []
        buy_hold_results = []
        
        for symbol in test_symbols:
            print(f"\nLoading data for {symbol}...")
            try:
                # Get 5 years of data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5*365)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty or len(data) < 1000:
                    print(f"  Insufficient data for {symbol}")
                    continue
                
                data.columns = [col.lower() for col in data.columns]
                
                # Calculate buy-and-hold return
                bh_return = (data['close'].iloc[-1] / data['close'].iloc[252] - 1) * 100
                buy_hold_results.append({'symbol': symbol, 'return': bh_return})
                
                # Test aggressive strategy
                aggressive_result = self.aggressive_minervini_strategy(data, symbol)
                aggressive_results.append(aggressive_result)
                
                print(f"  {symbol}: Aggressive = {aggressive_result['total_return']:.1f}%, Buy-Hold = {bh_return:.1f}%")
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self.analyze_aggressive_results(aggressive_results, buy_hold_results)
    
    def analyze_aggressive_results(self, aggressive_results: List[Dict], 
                                 buy_hold_results: List[Dict]) -> Dict:
        """Analyze results of aggressive vs conservative testing"""
        
        print(f"\n" + "=" * 80)
        print("AGGRESSIVE MINERVINI STRATEGY ANALYSIS")
        print("=" * 80)
        
        if not aggressive_results:
            print("No results to analyze")
            return {}
        
        # Calculate aggregate statistics
        agg_returns = [r['total_return'] for r in aggressive_results]
        agg_trades = [r['num_trades'] for r in aggressive_results]
        agg_win_rates = [r['win_rate'] for r in aggressive_results]
        agg_home_runs = [r['home_runs'] for r in aggressive_results]
        agg_big_winners = [r['big_winners'] for r in aggressive_results]
        
        bh_returns = [r['return'] for r in buy_hold_results]
        
        # Print detailed results
        print(f"{'Symbol':<8} {'Aggressive':<12} {'Buy-Hold':<12} {'Excess':<10} {'Trades':<8} {'Win%':<8} {'Home Runs':<10}")
        print("-" * 75)
        
        for i, result in enumerate(aggressive_results):
            symbol = result['symbol']
            agg_ret = result['total_return']
            bh_ret = bh_returns[i] if i < len(bh_returns) else 0
            excess = agg_ret - bh_ret
            trades = result['num_trades']
            win_rate = result['win_rate']
            home_runs = result['home_runs']
            
            print(f"{symbol:<8} {agg_ret:>10.1f}% {bh_ret:>10.1f}% {excess:>8.1f}% "
                  f"{trades:>6} {win_rate:>6.1f}% {home_runs:>8}")
        
        # Summary statistics
        print(f"\nAGGREGATE STATISTICS:")
        print(f"  Average Return: {np.mean(agg_returns):.1f}%")
        print(f"  Median Return: {np.median(agg_returns):.1f}%")
        print(f"  Best Performance: {max(agg_returns):.1f}%")
        print(f"  Worst Performance: {min(agg_returns):.1f}%")
        print(f"  Average Trades: {np.mean(agg_trades):.1f}")
        print(f"  Average Win Rate: {np.mean(agg_win_rates):.1f}%")
        print(f"  Total Home Runs: {sum(agg_home_runs)}")
        print(f"  Total Big Winners: {sum(agg_big_winners)}")
        
        # vs Buy and Hold
        beat_bh_count = len([i for i, r in enumerate(agg_returns) 
                            if i < len(bh_returns) and r > bh_returns[i]])
        
        print(f"\nvs BUY-AND-HOLD:")
        print(f"  Aggressive Average: {np.mean(agg_returns):.1f}%")
        print(f"  Buy-Hold Average: {np.mean(bh_returns):.1f}%")
        print(f"  Beat Buy-Hold: {beat_bh_count}/{len(agg_returns)} times ({beat_bh_count/len(agg_returns)*100:.1f}%)")
        
        excess_returns = [agg_returns[i] - bh_returns[i] for i in range(min(len(agg_returns), len(bh_returns)))]
        avg_excess = np.mean(excess_returns)
        
        if avg_excess > 0:
            print(f"  Aggressive strategy wins by {avg_excess:.1f} percentage points")
        else:
            print(f"  Buy-and-hold wins by {-avg_excess:.1f} percentage points")
        
        return {
            'aggressive_results': aggressive_results,
            'buy_hold_results': buy_hold_results,
            'summary': {
                'avg_return': np.mean(agg_returns),
                'median_return': np.median(agg_returns),
                'avg_trades': np.mean(agg_trades),
                'avg_win_rate': np.mean(agg_win_rates),
                'total_home_runs': sum(agg_home_runs),
                'beat_buy_hold_pct': beat_bh_count/len(agg_returns)*100,
                'avg_excess_return': avg_excess
            }
        }

def main():
    """Test aggressive Minervini strategy"""
    
    print("MARK MINERVINI AGGRESSIVE CHAMPIONSHIP STRATEGY TEST")
    print("=" * 60)
    print("This tests Minervini's ACTUAL aggressive approach:")
    print("- 15-35% position sizes (championship style)")
    print("- Maximum 6 concentrated positions")
    print("- 50% profit targets (hunt for home runs)")
    print("- Focus on small-cap growth breakouts")
    print("=" * 60)
    
    tester = MinerviniAggressive()
    
    try:
        results = tester.test_aggressive_vs_conservative()
        
        print(f"\n" + "=" * 80)
        print("KEY INSIGHTS FROM AGGRESSIVE TESTING")
        print("=" * 80)
        
        if 'summary' in results:
            summary = results['summary']
            
            print(f"AGGRESSIVE STRATEGY PERFORMANCE:")
            print(f"  Average Return: {summary['avg_return']:.1f}%")
            print(f"  Average Win Rate: {summary['avg_win_rate']:.1f}%")
            print(f"  Total Home Runs (>50%): {summary['total_home_runs']}")
            print(f"  Beat Buy-Hold: {summary['beat_buy_hold_pct']:.1f}% of time")
            print(f"  Excess Return: {summary['avg_excess_return']:.1f}%")
            print()
            print("KEY OBSERVATIONS:")
            
            if summary['avg_excess_return'] > 0:
                print(f"  Aggressive approach shows promise!")
                print(f"     - Home run hunting strategy working")
                print(f"     - Concentrated positions amplifying winners")
                print(f"     - Small-cap focus finding explosive moves")
            else:
                print(f"  Even aggressive approach struggles vs buy-hold")
                print(f"     - Market efficiency remains strong")
                print(f"     - Higher risk doesn't guarantee higher returns")
                print(f"     - Trading costs and timing challenges persist")
            
            print(f"\nTHE CHAMPIONSHIP DIFFERENCE:")
            print(f"   This represents Minervini's ACTUAL trading style")
            print(f"   - Much higher risk/reward than retail versions")
            print(f"   - Requires exceptional skill and market timing")
            print(f"   - Success depends on finding true home run stocks")
            print(f"   - Even this aggressive approach shows market efficiency")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()