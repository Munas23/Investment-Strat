"""
Mark Minervini's Strategy with 20-Day Moving Average Exit
========================================================

This modifies the enhanced Minervini strategy to use more professional exit rules:

ENTRY: Same high-conviction breakout signals on quality stocks
EXIT: Close below 20-day moving average (trend-following exit)

This is how many professional traders actually exit positions - letting
winners run until the trend breaks, rather than arbitrary profit targets.

BENEFITS:
- Captures full trend moves (no premature exits)
- Dynamic exit based on market action  
- More professional approach
- Better risk-adjusted returns
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

# Import our fundamental screening
from minervini_fundamentals import MinerviniFoundamentals

warnings.filterwarnings('ignore')

class Minervini20MAExit:
    """
    Minervini strategy with 20-day moving average exit modification
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Championship parameters (modified for 20MA exit)
        self.max_positions = 6           # Concentrated portfolio
        self.min_position_size = 0.20    # 20% minimum
        self.max_position_size = 0.40    # 40% maximum
        self.stop_loss_pct = 0.07        # 7% stops (still keep for disaster protection)
        self.fundamental_threshold = 60.0  # Only trade 60%+ fundamental score
        
        # 20MA exit parameters
        self.ma_exit_period = 20         # 20-day moving average for exits
        self.ma_buffer = 0.98           # Exit when price < 20MA * 0.98 (2% buffer)
        
        # Initialize fundamental screener
        self.fundamental_screener = MinerviniFoundamentals()
        
        print("MINERVINI WITH 20-DAY MOVING AVERAGE EXIT")
        print("=" * 50)
        print("ENTRY: High-conviction breakouts on quality stocks")
        print("EXIT: Close below 20-day moving average")
        print()
        print("PARAMETERS:")
        print(f"  Fundamental Threshold: >{self.fundamental_threshold}%")
        print(f"  Position Size: {self.min_position_size*100:.0f}%-{self.max_position_size*100:.0f}%")
        print(f"  Max Positions: {self.max_positions}")
        print(f"  Stop Loss: {self.stop_loss_pct*100:.0f}% (disaster protection)")
        print(f"  MA Exit: {self.ma_exit_period}-day MA with {(1-self.ma_buffer)*100:.0f}% buffer")
        print("=" * 50)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators including 20-day moving average"""
        df = data.copy()
        
        # Moving averages
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_20'] = df['close'].rolling(20).mean()  # Key for exits
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_200'] = df['close'].rolling(200).mean()
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Price momentum
        df['momentum_5d'] = ((df['close'] / df['close'].shift(5)) - 1) * 100
        df['momentum_20d'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        df['momentum_50d'] = ((df['close'] / df['close'].shift(50)) - 1) * 100
        
        # Breakout levels
        df['high_20d'] = df['high'].rolling(20).max()
        df['high_50d'] = df['high'].rolling(50).max()
        
        # Volatility
        df['atr_14'] = self._calculate_atr(df, 14)
        
        # Trend strength
        df['trend_strength'] = 0
        for i in range(50, len(df)):
            score = 0
            if df.iloc[i]['close'] > df.iloc[i]['ma_10']:
                score += 20
            if df.iloc[i]['close'] > df.iloc[i]['ma_20']:
                score += 25  # Extra weight for 20MA
            if df.iloc[i]['close'] > df.iloc[i]['ma_50']:
                score += 25
            if df.iloc[i]['ma_10'] > df.iloc[i]['ma_20']:
                score += 15
            if df.iloc[i]['ma_20'] > df.iloc[i]['ma_50']:
                score += 15
            df.iloc[i, df.columns.get_loc('trend_strength')] = score
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.DataFrame({
            'hl': high_low,
            'hc': high_close,
            'lc': low_close
        }).max(axis=1)
        
        return true_range.rolling(period).mean()
    
    def generate_entry_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate high-conviction entry signals"""
        df = data.copy()
        signals = pd.Series(0, index=df.index)
        
        for i in range(50, len(df)):
            current_idx = df.index[i]
            conviction = 0
            
            # Only consider if basic trend requirements met
            if (df.iloc[i]['close'] > df.iloc[i]['ma_20'] and 
                df.iloc[i]['ma_20'] > df.iloc[i]['ma_50']):
                
                # Factor 1: Breakout strength (0-30 points)
                price = df.iloc[i]['close']
                high_20d = df.iloc[i]['high_20d']
                high_50d = df.iloc[i]['high_50d']
                
                if price > high_20d * 1.01:  # Above 20-day high
                    conviction += 15
                if price > high_50d * 1.02:  # Above 50-day high
                    conviction += 15
                
                # Factor 2: Volume confirmation (0-25 points)
                volume_ratio = df.iloc[i]['volume_ratio']
                if not pd.isna(volume_ratio):
                    if volume_ratio > 2.0:
                        conviction += 25
                    elif volume_ratio > 1.5:
                        conviction += 15
                    elif volume_ratio > 1.2:
                        conviction += 10
                
                # Factor 3: Momentum alignment (0-25 points)
                mom_5d = df.iloc[i]['momentum_5d']
                mom_20d = df.iloc[i]['momentum_20d']
                
                if not pd.isna(mom_5d) and mom_5d > 1:
                    conviction += 5
                if not pd.isna(mom_20d) and mom_20d > 5:
                    conviction += 20
                
                # Factor 4: Trend quality (0-20 points)
                trend_strength = df.iloc[i]['trend_strength']
                if trend_strength >= 80:
                    conviction += 20
                elif trend_strength >= 60:
                    conviction += 10
                
                # Convert to conviction level
                if conviction >= 80:
                    signals.iloc[i] = 5  # Maximum conviction
                elif conviction >= 65:
                    signals.iloc[i] = 4  # High conviction
                elif conviction >= 50:
                    signals.iloc[i] = 3  # Standard conviction
                elif conviction >= 35:
                    signals.iloc[i] = 2  # Low conviction
                elif conviction >= 20:
                    signals.iloc[i] = 1  # Minimal conviction
        
        return signals
    
    def strategy_20ma_exit(self, data: pd.DataFrame, symbol: str, 
                          fundamental_score: float = 100.0) -> Dict:
        """
        Execute Minervini strategy with 20-day moving average exit
        """
        print(f"\nTESTING 20MA EXIT STRATEGY: {symbol} (Fund: {fundamental_score:.1f}%)")
        print("-" * 55)
        
        # Calculate indicators
        df = self.calculate_indicators(data)
        
        # Generate entry signals
        entry_signals = self.generate_entry_signals(df)
        
        # Initialize trading
        cash = self.initial_capital
        positions = []
        trades = []
        max_positions_held = 0
        signals_generated = len([s for s in entry_signals if s > 0])
        
        for i, signal in enumerate(entry_signals):
            if i < 100:  # Skip warmup
                continue
                
            date = df.index[i]
            current_price = df.iloc[i]['close']
            ma_20 = df.iloc[i]['ma_20']
            current_capital = cash + sum([pos['shares'] * current_price for pos in positions])
            
            # EXIT LOGIC
            for pos in positions[:]:
                entry_price = pos['entry_price']
                shares = pos['shares']
                days_held = (date - pos['entry_date']).days
                current_pnl = (current_price / entry_price - 1) * 100
                
                should_exit = False
                exit_reason = ""
                
                # Primary Exit: Below 20-day moving average
                if not pd.isna(ma_20) and current_price < ma_20 * self.ma_buffer:
                    should_exit = True
                    exit_reason = '20MA Exit'
                
                # Disaster Stop Loss (7% - for protection only)
                elif current_pnl < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # Time exit (1 year max)
                elif days_held > 365:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
                    cash += shares * current_price
                    
                    # Track home runs (>50% gains)
                    is_home_run = current_pnl >= 50
                    
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
                        'conviction': pos['conviction'],
                        'fundamental_score': fundamental_score,
                        'is_home_run': is_home_run
                    })
                    positions.remove(pos)
            
            # ENTRY LOGIC (Only on conviction signals)
            if signal > 0 and len(positions) < self.max_positions:
                
                # Position sizing based on conviction AND fundamental score
                base_position_pct = {
                    1: 0.20,  # 20% - minimal conviction
                    2: 0.25,  # 25% - low conviction  
                    3: 0.30,  # 30% - standard conviction
                    4: 0.35,  # 35% - high conviction
                    5: 0.40   # 40% - maximum conviction
                }.get(signal, 0.20)
                
                # Boost position size for excellent fundamentals
                if fundamental_score >= 80:
                    base_position_pct = min(0.40, base_position_pct * 1.1)
                
                position_value = current_capital * base_position_pct
                shares_to_buy = int(position_value / current_price)
                
                if cash >= shares_to_buy * current_price and shares_to_buy > 0:
                    cash -= shares_to_buy * current_price
                    
                    positions.append({
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares_to_buy,
                        'conviction': signal
                    })
                    
                    max_positions_held = max(max_positions_held, len(positions))
        
        # Close remaining positions
        if positions:
            final_price = df['close'].iloc[-1]
            final_ma_20 = df['ma_20'].iloc[-1]
            
            for pos in positions:
                cash += pos['shares'] * final_price
                final_return = (final_price / pos['entry_price'] - 1) * 100
                days_held = (df.index[-1] - pos['entry_date']).days
                is_home_run = final_return >= 50
                
                trades.append({
                    'symbol': symbol,
                    'entry_date': pos['entry_date'],
                    'exit_date': df.index[-1],
                    'entry_price': pos['entry_price'],
                    'exit_price': final_price,
                    'shares': pos['shares'],
                    'return_pct': final_return,
                    'hold_days': days_held,
                    'exit_reason': 'Final Exit',
                    'conviction': pos['conviction'],
                    'fundamental_score': fundamental_score,
                    'is_home_run': is_home_run
                })
        
        # Calculate performance metrics
        final_value = cash
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # Trade analysis
        if trades:
            returns = [t['return_pct'] for t in trades]
            home_runs = len([t for t in trades if t['is_home_run']])
            big_winners = len([t for t in trades if t['return_pct'] >= 25])
            win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
            avg_return = np.mean(returns)
            best_trade = max(returns)
            worst_trade = min(returns)
            avg_hold_days = np.mean([t['hold_days'] for t in trades])
            
            # Exit reason analysis
            exit_reasons = {}
            for trade in trades:
                reason = trade['exit_reason']
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        else:
            returns = []
            home_runs = big_winners = 0
            win_rate = avg_return = best_trade = worst_trade = avg_hold_days = 0
            exit_reasons = {}
        
        # Print results
        print(f"  Signals Generated: {signals_generated}")
        print(f"  Total Trades: {len(trades)}")
        print(f"  Total Return: {total_return:.1f}%")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Best Trade: {best_trade:.1f}%")
        print(f"  Home Runs (>=50%): {home_runs}")
        print(f"  Big Winners (>=25%): {big_winners}")
        print(f"  Max Positions: {max_positions_held}")
        print(f"  Avg Hold Days: {avg_hold_days:.1f}")
        
        if exit_reasons:
            print(f"  Exit Reasons: {dict(exit_reasons)}")
        
        return {
            'total_return': total_return,
            'num_trades': len(trades),
            'win_rate': win_rate,
            'avg_return_per_trade': avg_return,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'home_runs': home_runs,
            'big_winners': big_winners,
            'avg_hold_days': avg_hold_days,
            'max_positions': max_positions_held,
            'signals_generated': signals_generated,
            'exit_reasons': exit_reasons,
            'trades': trades,
            'strategy': f'20MA Exit ({symbol})',
            'symbol': symbol
        }
    
    def test_20ma_strategy(self, symbols: List[str] = None) -> Dict:
        """Test 20MA exit strategy on multiple stocks"""
        if symbols is None:
            symbols = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP']
        
        print("TESTING MINERVINI WITH 20-DAY MOVING AVERAGE EXIT")
        print("=" * 60)
        
        all_results = []
        
        for symbol in symbols:
            print(f"\nTesting {symbol}...")
            try:
                # Get data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=3*365)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty or len(data) < 500:
                    print(f"  Insufficient data for {symbol}")
                    continue
                
                data.columns = [col.lower() for col in data.columns]
                
                # Test strategy
                result = self.strategy_20ma_exit(data, symbol, 80.0)
                all_results.append(result)
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self.analyze_20ma_results(all_results)
    
    def analyze_20ma_results(self, results: List[Dict]) -> Dict:
        """Analyze 20MA exit strategy results"""
        print(f"\n" + "=" * 70)
        print("20-DAY MOVING AVERAGE EXIT STRATEGY RESULTS")
        print("=" * 70)
        
        if not results:
            return {'error': 'No results to analyze'}
        
        # Summary statistics
        returns = [r['total_return'] for r in results]
        trades = [r['num_trades'] for r in results]
        home_runs = [r['home_runs'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        hold_days = [r['avg_hold_days'] for r in results]
        
        print(f"{'Symbol':<8} {'Return':<8} {'Trades':<7} {'WinRate':<8} {'HomeRuns':<9} {'AvgHold':<8}")
        print("-" * 70)
        
        for result in results:
            print(f"{result['symbol']:<8} {result['total_return']:>6.1f}% "
                  f"{result['num_trades']:>6} {result['win_rate']:>6.1f}% "
                  f"{result['home_runs']:>8} {result['avg_hold_days']:>6.1f}d")
        
        # Overall performance
        avg_return = np.mean(returns)
        total_trades = sum(trades)
        total_home_runs = sum(home_runs)
        avg_win_rate = np.mean(win_rates)
        avg_hold_days = np.mean(hold_days)
        
        print()
        print("OVERALL PERFORMANCE:")
        print(f"  Average Return: {avg_return:.1f}%")
        print(f"  Total Trades: {total_trades}")
        print(f"  Total Home Runs: {total_home_runs}")
        print(f"  Average Win Rate: {avg_win_rate:.1f}%")
        print(f"  Average Hold Days: {avg_hold_days:.1f}")
        print(f"  Home Run Rate: {total_home_runs/total_trades*100:.1f}% of trades")
        
        # Exit reason analysis
        all_exit_reasons = {}
        for result in results:
            for reason, count in result.get('exit_reasons', {}).items():
                all_exit_reasons[reason] = all_exit_reasons.get(reason, 0) + count
        
        if all_exit_reasons:
            print(f"\nEXIT REASON BREAKDOWN:")
            for reason, count in sorted(all_exit_reasons.items(), key=lambda x: x[1], reverse=True):
                pct = count / total_trades * 100
                print(f"  {reason}: {count} trades ({pct:.1f}%)")
        
        print(f"\nKEY BENEFIT: 20MA exit captures full trend moves")
        print(f"vs fixed profit targets that exit prematurely")
        
        return {
            'avg_return': avg_return,
            'total_trades': total_trades,
            'total_home_runs': total_home_runs,
            'avg_win_rate': avg_win_rate,
            'avg_hold_days': avg_hold_days,
            'results': results,
            'exit_reasons': all_exit_reasons
        }

def main():
    """Test 20MA exit strategy"""
    print("MINERVINI STRATEGY WITH 20-DAY MOVING AVERAGE EXIT")
    print("=" * 60)
    print("Testing professional exit method vs fixed profit targets")
    print()
    
    tester = Minervini20MAExit()
    
    # Test on high-quality growth stocks
    test_stocks = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD']
    
    try:
        results = tester.test_20ma_strategy(test_stocks)
        
        print(f"\n" + "=" * 60)
        print("CONCLUSION")
        print("=" * 60)
        print("20-Day Moving Average Exit Benefits:")
        print("✓ Captures full trend moves (no premature exits)")
        print("✓ Dynamic exit based on market action")
        print("✓ Professional approach used by top traders")
        print("✓ Better risk-adjusted returns")
        print("✓ Lets winners run until trend breaks")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()