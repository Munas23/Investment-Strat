"""
Mark Minervini REALISTIC Aggressive Strategy
===========================================

The previous aggressive strategy was too restrictive (0 trades).
This version adjusts the criteria to be more realistic while maintaining
the aggressive position sizing and home run hunting mentality.

ADJUSTED CRITERIA:
- Looser breakout power requirements (50+ vs 70+)
- More flexible relative strength (10%+ vs 20%+) 
- Simplified stage analysis
- Still maintains aggressive position sizing (15-35%)
- Still hunts for 50%+ home runs
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class MinerviniRealistic:
    """
    Realistic aggressive Minervini strategy with adjusted criteria
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # AGGRESSIVE PARAMETERS (Championship Style)
        self.max_positions = 6           # Maximum 6 concentrated positions
        self.min_position_size = 0.15    # 15% minimum position
        self.max_position_size = 0.35    # 35% maximum position
        self.stop_loss_pct = 0.07        # 7% stop loss
        self.profit_target = 0.50        # 50% profit target (hunt for home runs)
        self.trail_stop_trigger = 0.15   # Trail stop after 15% gain
        
        print("MINERVINI REALISTIC AGGRESSIVE STRATEGY")
        print("=" * 45)
        print("ADJUSTED PARAMETERS FOR BACKTESTING:")
        print(f"  Max Positions: {self.max_positions} (concentrated)")
        print(f"  Position Size: {self.min_position_size*100:.0f}%-{self.max_position_size*100:.0f}% (aggressive)")
        print(f"  Stop Loss: {self.stop_loss_pct*100:.0f}% (tight)")
        print(f"  Profit Target: {self.profit_target*100:.0f}% (home runs)")
        print("=" * 45)
        
    def get_growth_stocks(self) -> List[str]:
        """Get growth stocks for testing - mix of winners and losers"""
        return [
            # High growth tech (Minervini style)
            'NVDA', 'AMD', 'TSLA', 'AMZN', 'GOOGL', 'META', 'NFLX', 'AAPL',
            # Software/SaaS 
            'CRM', 'ADBE', 'NOW', 'WDAY', 'SNOW', 'PLTR',
            # Growth names from different periods
            'SHOP', 'SQ', 'ROKU', 'ZM', 'DOCU', 'TWLO'
        ]
    
    def calculate_realistic_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators with realistic thresholds"""
        df = data.copy()
        
        # Standard moving averages
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_21'] = df['close'].rolling(21).mean()
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_150'] = df['close'].rolling(150).mean()
        
        # Breakout detection
        df['high_20'] = df['high'].rolling(20).max()
        df['high_40'] = df['high'].rolling(40).max()
        
        # Volume analysis
        df['volume_avg_20'] = df['volume'].rolling(20).mean()
        df['volume_surge'] = df['volume'] / df['volume_avg_20']
        
        # Relative strength (simplified)
        df['rs_13w'] = ((df['close'] / df['close'].shift(65)) - 1) * 100
        df['rs_26w'] = ((df['close'] / df['close'].shift(130)) - 1) * 100
        
        # Price momentum
        df['momentum_5d'] = ((df['close'] / df['close'].shift(5)) - 1) * 100
        df['momentum_20d'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        
        return df
    
    def realistic_trend_check(self, data: pd.DataFrame, index: int) -> bool:
        """
        Simplified trend check - more realistic for backtesting
        
        CRITERIA:
        1. Price above 21-day MA (short-term trend)
        2. 21-day MA above 50-day MA (medium-term trend)
        3. Price within 15% of 20-day high (not too extended)
        """
        if index < 65:  # Need enough data
            return False
            
        current = data.iloc[index]
        
        # Check for missing data
        if (pd.isna(current['close']) or pd.isna(current['ma_21']) or 
            pd.isna(current['ma_50']) or pd.isna(current['high_20'])):
            return False
        
        # Trend criteria
        price_above_ma21 = current['close'] > current['ma_21']
        ma21_above_ma50 = current['ma_21'] > current['ma_50']
        not_extended = current['close'] > current['high_20'] * 0.85  # Within 15% of highs
        
        return price_above_ma21 and ma21_above_ma50 and not_extended
    
    def realistic_breakout_signal(self, data: pd.DataFrame, index: int) -> int:
        """
        Realistic breakout signal with conviction scoring
        
        Returns conviction level 1-5:
        1 = Weak signal
        3 = Standard signal  
        5 = Maximum conviction
        """
        if index < 65:
            return 0
            
        current = data.iloc[index]
        
        # Check basic trend first
        if not self.realistic_trend_check(data, index):
            return 0
        
        conviction = 0
        
        # Factor 1: Breakout from base (20 points)
        if not pd.isna(current['high_20']):
            if current['close'] > current['high_20'] * 1.005:  # 0.5% above 20-day high
                conviction += 20
        
        # Factor 2: Volume confirmation (30 points)
        if not pd.isna(current['volume_surge']):
            if current['volume_surge'] > 1.5:  # 50% above average
                conviction += 30
            elif current['volume_surge'] > 1.2:  # 20% above average
                conviction += 15
        
        # Factor 3: Relative strength (30 points)
        if not pd.isna(current['rs_13w']):
            if current['rs_13w'] > 15:  # Strong 13-week performance
                conviction += 30
            elif current['rs_13w'] > 5:  # Decent performance
                conviction += 15
        
        # Factor 4: Momentum (20 points)
        if not pd.isna(current['momentum_5d']):
            if current['momentum_5d'] > 2:  # Strong 5-day momentum
                conviction += 20
            elif current['momentum_5d'] > 0:  # Positive momentum
                conviction += 10
        
        # Convert to conviction level (0-100 -> 0-5)
        if conviction >= 80:
            return 5  # Maximum conviction
        elif conviction >= 60:
            return 4  # High conviction
        elif conviction >= 40:
            return 3  # Standard conviction
        elif conviction >= 20:
            return 2  # Low conviction
        elif conviction > 0:
            return 1  # Minimal conviction
        else:
            return 0  # No signal
    
    def realistic_aggressive_strategy(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Realistic aggressive Minervini strategy implementation
        """
        print(f"\nTESTING REALISTIC AGGRESSIVE: {symbol}")
        print("-" * 45)
        
        df = self.calculate_realistic_indicators(data)
        
        # Initialize trading variables
        cash = self.initial_capital
        positions = []
        trades = []
        max_positions_held = 0
        signals_generated = 0
        
        for i in range(65, len(df)):  # Start after warmup
            date = df.index[i]
            current_price = df.iloc[i]['close']
            current_capital = cash + sum([pos['shares'] * current_price for pos in positions])
            
            # EXIT LOGIC
            for pos in positions[:]:
                entry_price = pos['entry_price']
                shares = pos['shares']
                days_held = (date - pos['entry_date']).days
                current_pnl = (current_price / entry_price - 1) * 100
                
                # Exit conditions
                should_exit = False
                exit_reason = ""
                
                # Stop Loss (7%)
                if current_pnl < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # Home Run Target (50%)
                elif current_pnl > self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'HOME RUN Target'
                
                # Trailing Stop (after 15% gain)
                elif current_pnl > self.trail_stop_trigger * 100:
                    if 'highest_price' not in pos:
                        pos['highest_price'] = current_price
                    else:
                        pos['highest_price'] = max(pos['highest_price'], current_price)
                    
                    trail_stop_price = pos['highest_price'] * 0.90  # 10% trailing
                    if current_price < trail_stop_price:
                        should_exit = True
                        exit_reason = 'Trailing Stop'
                
                # Time-based exit (hold max 6 months for momentum stocks)
                elif days_held > 180:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
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
                        'exit_reason': exit_reason,
                        'conviction': pos['conviction']
                    })
                    positions.remove(pos)
            
            # ENTRY LOGIC
            conviction = self.realistic_breakout_signal(df, i)
            
            if conviction > 0 and len(positions) < self.max_positions:
                signals_generated += 1
                
                # Position sizing based on conviction
                if conviction == 5:
                    position_pct = 0.35  # 35% - maximum conviction
                elif conviction == 4:
                    position_pct = 0.30  # 30% - high conviction
                elif conviction == 3:
                    position_pct = 0.25  # 25% - standard
                elif conviction == 2:
                    position_pct = 0.20  # 20% - low conviction
                else:
                    position_pct = 0.15  # 15% - minimal
                
                position_value = current_capital * position_pct
                shares_to_buy = int(position_value / current_price)
                
                if cash >= shares_to_buy * current_price and shares_to_buy > 0:
                    cash -= shares_to_buy * current_price
                    
                    positions.append({
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares_to_buy,
                        'conviction': conviction
                    })
                    
                    max_positions_held = max(max_positions_held, len(positions))
        
        # Close remaining positions
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
                    'conviction': pos['conviction']
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
            home_runs = len([r for r in returns if r > 50])
            big_winners = len([r for r in returns if r > 25])
            
        else:
            win_rate = avg_return = avg_winner = avg_loser = 0
            best_trade = worst_trade = 0
            home_runs = big_winners = 0
        
        print(f"  Signals Generated: {signals_generated}")
        print(f"  Total Trades: {len(trades)}")
        print(f"  Total Return: {total_return:.1f}%")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Best Trade: {best_trade:.1f}%")
        print(f"  Home Runs (>50%): {home_runs}")
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
            'signals_generated': signals_generated,
            'trades': trades
        }
    
    def test_realistic_aggressive(self, test_symbols: List[str] = None) -> Dict:
        """Test realistic aggressive strategy"""
        
        if test_symbols is None:
            test_symbols = self.get_growth_stocks()
        
        print("MINERVINI REALISTIC AGGRESSIVE STRATEGY TEST")
        print("=" * 50)
        print("Adjusted criteria for realistic backtesting")
        print("while maintaining aggressive position sizing")
        print(f"Testing {len(test_symbols)} growth stocks")
        print("=" * 50)
        
        results = []
        buy_hold_results = []
        
        for symbol in test_symbols:
            print(f"\nLoading {symbol}...")
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
                
                # Calculate buy-and-hold
                bh_return = (data['close'].iloc[-1] / data['close'].iloc[252] - 1) * 100
                buy_hold_results.append({'symbol': symbol, 'return': bh_return})
                
                # Test strategy
                result = self.realistic_aggressive_strategy(data, symbol)
                results.append(result)
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self.analyze_realistic_results(results, buy_hold_results)
    
    def analyze_realistic_results(self, results: List[Dict], buy_hold_results: List[Dict]) -> Dict:
        """Analyze realistic aggressive results"""
        
        print(f"\n" + "=" * 80)
        print("REALISTIC AGGRESSIVE STRATEGY ANALYSIS")
        print("=" * 80)
        
        if not results:
            print("No results to analyze")
            return {}
        
        # Extract metrics
        agg_returns = [r['total_return'] for r in results]
        agg_trades = [r['num_trades'] for r in results]
        agg_win_rates = [r['win_rate'] for r in results]
        agg_home_runs = [r['home_runs'] for r in results]
        total_signals = sum([r['signals_generated'] for r in results])
        
        bh_returns = [r['return'] for r in buy_hold_results]
        
        # Print results
        print(f"{'Symbol':<8} {'Aggressive':<12} {'Buy-Hold':<12} {'Excess':<10} {'Trades':<8} {'Signals':<8} {'Home Runs':<10}")
        print("-" * 80)
        
        for i, result in enumerate(results):
            symbol = result['symbol']
            agg_ret = result['total_return']
            bh_ret = bh_returns[i] if i < len(bh_returns) else 0
            excess = agg_ret - bh_ret
            trades = result['num_trades']
            signals = result['signals_generated']
            home_runs = result['home_runs']
            
            print(f"{symbol:<8} {agg_ret:>10.1f}% {bh_ret:>10.1f}% {excess:>8.1f}% "
                  f"{trades:>6} {signals:>7} {home_runs:>8}")
        
        # Summary statistics
        print(f"\nSUMMARY STATISTICS:")
        print(f"  Average Return: {np.mean(agg_returns):.1f}%")
        print(f"  Average Trades: {np.mean(agg_trades):.1f}")
        print(f"  Average Win Rate: {np.mean(agg_win_rates):.1f}%")
        print(f"  Total Home Runs: {sum(agg_home_runs)}")
        print(f"  Total Signals: {total_signals}")
        
        # vs Buy and Hold
        beat_bh_count = len([i for i, r in enumerate(agg_returns) 
                            if i < len(bh_returns) and r > bh_returns[i]])
        
        print(f"\nvs BUY-AND-HOLD:")
        print(f"  Aggressive Average: {np.mean(agg_returns):.1f}%")
        print(f"  Buy-Hold Average: {np.mean(bh_returns):.1f}%")
        print(f"  Beat Buy-Hold: {beat_bh_count}/{len(agg_returns)} times ({beat_bh_count/len(agg_returns)*100:.1f}%)")
        
        excess_returns = [agg_returns[i] - bh_returns[i] for i in range(min(len(agg_returns), len(bh_returns)))]
        avg_excess = np.mean(excess_returns)
        
        print(f"\nFINAL VERDICT:")
        if avg_excess > 0:
            print(f"  AGGRESSIVE STRATEGY WINS by {avg_excess:.1f} percentage points!")
            print(f"  This shows Minervini's aggressive approach CAN work")
        else:
            print(f"  Buy-and-hold wins by {-avg_excess:.1f} percentage points")
            print(f"  Even realistic aggressive approach struggles")
        
        return {
            'results': results,
            'buy_hold_results': buy_hold_results,
            'summary': {
                'avg_return': np.mean(agg_returns),
                'avg_trades': np.mean(agg_trades),
                'avg_win_rate': np.mean(agg_win_rates),
                'total_home_runs': sum(agg_home_runs),
                'total_signals': total_signals,
                'beat_buy_hold_pct': beat_bh_count/len(agg_returns)*100,
                'avg_excess_return': avg_excess
            }
        }

def main():
    """Test realistic aggressive strategy"""
    
    tester = MinerviniRealistic()
    
    try:
        results = tester.test_realistic_aggressive()
        
        print(f"\n" + "=" * 60)
        print("KEY INSIGHTS FROM REALISTIC AGGRESSIVE TEST")
        print("=" * 60)
        
        if 'summary' in results:
            summary = results['summary']
            
            print(f"REALISTIC AGGRESSIVE PERFORMANCE:")
            print(f"  Average Return: {summary['avg_return']:.1f}%")
            print(f"  Average Trades: {summary['avg_trades']:.1f}")
            print(f"  Total Home Runs: {summary['total_home_runs']}")
            print(f"  Total Signals: {summary['total_signals']}")
            print(f"  Beat Buy-Hold: {summary['beat_buy_hold_pct']:.1f}% of time")
            print(f"  Excess Return: {summary['avg_excess_return']:.1f}%")
            
            print(f"\nCONCLUSIONS:")
            if summary['avg_excess_return'] > 0:
                print(f"  SUCCESS! Aggressive Minervini approach beats buy-hold!")
                print(f"  Key factors:")
                print(f"    - Concentrated positions (15-35%)")
                print(f"    - Home run hunting (50% targets)")
                print(f"    - Tight stops (7% losses)")
                print(f"    - Realistic entry criteria")
            else:
                print(f"  Even with realistic criteria, buy-hold still wins")
                print(f"  This reinforces market efficiency")
                print(f"  Active trading faces significant headwinds")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()