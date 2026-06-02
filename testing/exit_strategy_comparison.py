"""
Comprehensive Exit Strategy Comparison
=====================================

This module tests multiple professional exit strategies on the same entry signals
to determine which exit methods perform best under different conditions.

EXIT STRATEGIES TESTED:
1. 20-Day Moving Average (baseline)
2. 10-Day Moving Average (faster)
3. 40-Day Moving Average (slower)
4. 2x 14-Day ATR Trailing Stop (volatility-based)
5. Chandelier Exit (ATR from highest high)
6. 15% Trailing Stop (percentage-based)
7. Volatility-Adjusted Trailing Stop
8. Parabolic SAR Exit
9. Fixed 50% Profit Target (original)
10. 30% Trigger + 2x ATR Trail (hybrid approach)

All strategies use the same entry signals for fair comparison.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

# Import our fundamental screening
from enhanced_growth_screener import EnhancedGrowthScreener

warnings.filterwarnings('ignore')

class ExitStrategyComparison:
    """
    Test multiple exit strategies on the same entry signals
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Entry parameters (same for all exit strategies)
        self.max_positions = 6
        self.min_position_size = 0.20
        self.max_position_size = 0.40
        self.stop_loss_pct = 0.07  # 7% disaster stop for all strategies
        
        # Exit strategy parameters
        self.exit_strategies = {
            '20MA': {'name': '20-Day Moving Average', 'method': 'ma_20_exit'},
            '10MA': {'name': '10-Day Moving Average', 'method': 'ma_10_exit'},
            '40MA': {'name': '40-Day Moving Average', 'method': 'ma_40_exit'},
            '2xATR': {'name': '2x 14-Day ATR Trailing', 'method': 'atr_trailing_exit'},
            'Chandelier': {'name': 'Chandelier Exit', 'method': 'chandelier_exit'},
            'Trail15%': {'name': '15% Trailing Stop', 'method': 'percentage_trailing_exit'},
            'VolTrail': {'name': 'Volatility-Adjusted Trail', 'method': 'volatility_trailing_exit'},
            'PSAR': {'name': 'Parabolic SAR Exit', 'method': 'parabolic_sar_exit'},
            'Fixed50%': {'name': 'Fixed 50% Target', 'method': 'fixed_target_exit'},
            'ATR30%': {'name': '30% Trigger + 2x ATR Trail', 'method': 'atr_30pct_trigger_exit'}
        }
        
        self.screener = EnhancedGrowthScreener()
        
        print("COMPREHENSIVE EXIT STRATEGY COMPARISON")
        print("=" * 50)
        print(f"Testing {len(self.exit_strategies)} different exit strategies:")
        for key, strategy in self.exit_strategies.items():
            print(f"  {key}: {strategy['name']}")
        print()
        print("All strategies use identical entry signals")
        print("for fair performance comparison.")
        print("=" * 50)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators needed for exit strategies"""
        df = data.copy()
        
        # Moving averages
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_20'] = df['close'].rolling(20).mean()
        df['ma_40'] = df['close'].rolling(40).mean()
        df['ma_50'] = df['close'].rolling(50).mean()
        
        # ATR for volatility-based exits
        df['atr_14'] = self._calculate_atr(df, 14)
        df['atr_20'] = self._calculate_atr(df, 20)
        
        # Rolling highs for chandelier exit
        df['high_14'] = df['high'].rolling(14).max()
        df['high_20'] = df['high'].rolling(20).max()
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Price momentum for entries
        df['momentum_5d'] = ((df['close'] / df['close'].shift(5)) - 1) * 100
        df['momentum_20d'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        
        # Breakout levels
        df['high_20d'] = df['high'].rolling(20).max()
        df['high_50d'] = df['high'].rolling(50).max()
        
        # Parabolic SAR calculation
        df['psar'] = self._calculate_parabolic_sar(df)
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        df['bb_mid'] = df['close'].rolling(bb_period).mean()
        df['bb_std'] = df['close'].rolling(bb_period).std()
        df['bb_upper'] = df['bb_mid'] + (bb_std * df['bb_std'])
        df['bb_lower'] = df['bb_mid'] - (bb_std * df['bb_std'])
        
        # Trend strength
        df['trend_strength'] = 0
        for i in range(50, len(df)):
            score = 0
            if df.iloc[i]['close'] > df.iloc[i]['ma_10']:
                score += 20
            if df.iloc[i]['close'] > df.iloc[i]['ma_20']:
                score += 25
            if df.iloc[i]['close'] > df.iloc[i]['ma_40']:
                score += 25
            if df.iloc[i]['ma_10'] > df.iloc[i]['ma_20']:
                score += 15
            if df.iloc[i]['ma_20'] > df.iloc[i]['ma_40']:
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
    
    def _calculate_parabolic_sar(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Parabolic SAR"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        length = len(df)
        psar = np.zeros(length)
        
        af = 0.02  # Acceleration factor
        max_af = 0.2
        ep = 0  # Extreme point
        trend = 1  # 1 for uptrend, -1 for downtrend
        
        # Initialize
        psar[0] = low[0]
        
        for i in range(1, length):
            if trend == 1:  # Uptrend
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + 0.02, max_af)
                
                if low[i] <= psar[i]:
                    trend = -1
                    psar[i] = ep
                    ep = low[i]
                    af = 0.02
            else:  # Downtrend
                psar[i] = psar[i-1] + af * (ep - psar[i-1])
                
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + 0.02, max_af)
                
                if high[i] >= psar[i]:
                    trend = 1
                    psar[i] = ep
                    ep = high[i]
                    af = 0.02
        
        return pd.Series(psar, index=df.index)
    
    def generate_entry_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate consistent entry signals for all exit strategy tests"""
        df = data.copy()
        signals = pd.Series(0, index=df.index)
        
        for i in range(50, len(df)):
            current_idx = df.index[i]
            conviction = 0
            
            # Only consider if basic trend requirements met
            if (df.iloc[i]['close'] > df.iloc[i]['ma_20'] and 
                df.iloc[i]['ma_20'] > df.iloc[i]['ma_40']):
                
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
    
    def test_exit_strategy(self, data: pd.DataFrame, symbol: str, 
                          exit_method: str, fundamental_score: float = 80.0) -> Dict:
        """
        Test a specific exit strategy on the given data
        """
        df = self.calculate_indicators(data)
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
            current_capital = cash + sum([pos['shares'] * current_price for pos in positions])
            
            # EXIT LOGIC - Apply specific exit method
            for pos in positions[:]:
                entry_price = pos['entry_price']
                shares = pos['shares']
                days_held = (date - pos['entry_date']).days
                current_pnl = (current_price / entry_price - 1) * 100
                
                should_exit = False
                exit_reason = ""
                
                # Apply specific exit method
                if exit_method == 'ma_10_exit':
                    ma_10 = df.iloc[i]['ma_10']
                    if not pd.isna(ma_10) and current_price < ma_10 * 0.98:
                        should_exit = True
                        exit_reason = '10MA Exit'
                
                elif exit_method == 'ma_20_exit':
                    ma_20 = df.iloc[i]['ma_20']
                    if not pd.isna(ma_20) and current_price < ma_20 * 0.98:
                        should_exit = True
                        exit_reason = '20MA Exit'
                
                elif exit_method == 'ma_40_exit':
                    ma_40 = df.iloc[i]['ma_40']
                    if not pd.isna(ma_40) and current_price < ma_40 * 0.98:
                        should_exit = True
                        exit_reason = '40MA Exit'
                
                elif exit_method == 'atr_trailing_exit':
                    atr = df.iloc[i]['atr_14']
                    if 'trail_stop' not in pos:
                        pos['trail_stop'] = entry_price - (2 * atr)
                    else:
                        new_trail = current_price - (2 * atr)
                        pos['trail_stop'] = max(pos['trail_stop'], new_trail)
                    
                    if current_price < pos['trail_stop']:
                        should_exit = True
                        exit_reason = '2xATR Trail'
                
                elif exit_method == 'chandelier_exit':
                    atr = df.iloc[i]['atr_14']
                    high_14 = df.iloc[i]['high_14']
                    chandelier_stop = high_14 - (3 * atr)
                    
                    if current_price < chandelier_stop:
                        should_exit = True
                        exit_reason = 'Chandelier'
                
                elif exit_method == 'percentage_trailing_exit':
                    if 'highest_price' not in pos:
                        pos['highest_price'] = current_price
                    else:
                        pos['highest_price'] = max(pos['highest_price'], current_price)
                    
                    trail_stop = pos['highest_price'] * 0.85  # 15% trailing stop
                    if current_price < trail_stop:
                        should_exit = True
                        exit_reason = '15% Trail'
                
                elif exit_method == 'volatility_trailing_exit':
                    atr = df.iloc[i]['atr_20']
                    volatility = atr / current_price
                    
                    # Adjust trail distance based on volatility
                    if volatility > 0.03:  # High volatility
                        trail_pct = 0.20  # 20% trail
                    elif volatility > 0.02:  # Medium volatility
                        trail_pct = 0.15  # 15% trail
                    else:  # Low volatility
                        trail_pct = 0.10  # 10% trail
                    
                    if 'highest_price' not in pos:
                        pos['highest_price'] = current_price
                    else:
                        pos['highest_price'] = max(pos['highest_price'], current_price)
                    
                    trail_stop = pos['highest_price'] * (1 - trail_pct)
                    if current_price < trail_stop:
                        should_exit = True
                        exit_reason = 'Vol Trail'
                
                elif exit_method == 'parabolic_sar_exit':
                    psar = df.iloc[i]['psar']
                    if not pd.isna(psar) and current_price < psar:
                        should_exit = True
                        exit_reason = 'PSAR Exit'
                
                elif exit_method == 'fixed_target_exit':
                    if current_pnl >= 50:  # 50% profit target
                        should_exit = True
                        exit_reason = 'Fixed 50%'
                
                elif exit_method == 'atr_30pct_trigger_exit':
                    # New strategy: After 30% gain, implement 2x ATR trailing stop
                    if current_pnl >= 30:  # 30% trigger threshold
                        atr = df.iloc[i]['atr_14']
                        
                        # Initialize trailing stop once 30% threshold is hit
                        if 'atr_trail_active' not in pos:
                            pos['atr_trail_active'] = True
                            pos['atr_trail_stop'] = current_price - (2 * atr)
                        else:
                            # Update trailing stop (only move up)
                            new_trail = current_price - (2 * atr)
                            pos['atr_trail_stop'] = max(pos['atr_trail_stop'], new_trail)
                        
                        # Check if we should exit
                        if current_price < pos['atr_trail_stop']:
                            should_exit = True
                            exit_reason = 'ATR30% Trail'
                
                # Disaster stop loss for all strategies
                if current_pnl < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # Time exit (1 year max)
                if days_held > 365:
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
                        'conviction': pos['conviction'],
                        'fundamental_score': fundamental_score,
                        'is_home_run': current_pnl >= 50
                    })
                    positions.remove(pos)
            
            # ENTRY LOGIC (Same for all exit strategies)
            if signal > 0 and len(positions) < self.max_positions:
                
                # Position sizing based on conviction
                base_position_pct = {
                    1: 0.20, 2: 0.25, 3: 0.30, 4: 0.35, 5: 0.40
                }.get(signal, 0.20)
                
                # Boost for excellent fundamentals
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
                    'exit_reason': 'Final Exit',
                    'conviction': pos['conviction'],
                    'fundamental_score': fundamental_score,
                    'is_home_run': final_return >= 50
                })
        
        # Calculate performance metrics
        final_value = cash
        total_return = (final_value / self.initial_capital - 1) * 100
        
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
            'strategy': exit_method,
            'symbol': symbol
        }
    
    def comprehensive_exit_comparison(self, symbols: List[str] = None) -> Dict:
        """
        Test all exit strategies on the same stocks for comparison
        """
        if symbols is None:
            symbols = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD']
        
        print(f"\nCOMPREHENSIVE EXIT STRATEGY COMPARISON")
        print("=" * 60)
        print(f"Testing {len(self.exit_strategies)} exit strategies on {len(symbols)} stocks")
        print("All strategies use IDENTICAL entry signals")
        print()
        
        all_results = {}
        
        # Initialize results dictionary
        for strategy_key in self.exit_strategies.keys():
            all_results[strategy_key] = {
                'name': self.exit_strategies[strategy_key]['name'],
                'results': []
            }
        
        # Test each stock with all exit strategies
        for symbol in symbols:
            print(f"Testing {symbol} with all exit strategies...")
            
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
                
                # Test each exit strategy
                for strategy_key, strategy_info in self.exit_strategies.items():
                    method_name = strategy_info['method']
                    strategy_name = strategy_info['name']
                    
                    try:
                        result = self.test_exit_strategy(data, symbol, method_name, 80.0)
                        result['exit_strategy'] = strategy_key
                        all_results[strategy_key]['results'].append(result)
                        
                        print(f"    {strategy_key}: {result['total_return']:.1f}% ({result['num_trades']} trades)")
                        
                    except Exception as e:
                        print(f"    {strategy_key}: Error - {str(e)[:30]}...")
                        continue
                        
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self.analyze_exit_comparison_results(all_results)
    
    def analyze_exit_comparison_results(self, all_results: Dict) -> Dict:
        """
        Analyze and compare all exit strategy results
        """
        print(f"\n" + "=" * 90)
        print("EXIT STRATEGY COMPARISON RESULTS")
        print("=" * 90)
        
        # Calculate summary statistics for each strategy
        strategy_summary = {}
        
        for strategy_key, strategy_data in all_results.items():
            results = strategy_data['results']
            if not results:
                continue
                
            returns = [r['total_return'] for r in results]
            trades = [r['num_trades'] for r in results]
            home_runs = [r['home_runs'] for r in results]
            win_rates = [r['win_rate'] for r in results]
            hold_days = [r['avg_hold_days'] for r in results]
            
            strategy_summary[strategy_key] = {
                'name': strategy_data['name'],
                'avg_return': np.mean(returns),
                'median_return': np.median(returns),
                'std_return': np.std(returns),
                'avg_trades': np.mean(trades),
                'total_home_runs': sum(home_runs),
                'avg_win_rate': np.mean(win_rates),
                'avg_hold_days': np.mean(hold_days),
                'consistency': len([r for r in returns if r > 0]) / len(returns) * 100,
                'num_tests': len(results)
            }
        
        # Sort by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        # Print comparison table
        print(f"{'Rank':<4} {'Strategy':<20} {'Avg Ret':<8} {'Trades':<7} {'HRs':<5} {'WinRate':<8} {'Hold':<6} {'Consist':<8}")
        print("-" * 90)
        
        for rank, (strategy_key, summary) in enumerate(sorted_strategies, 1):
            print(f"{rank:<4} {summary['name'][:19]:<20} {summary['avg_return']:>6.1f}% "
                  f"{summary['avg_trades']:>5.1f} {summary['total_home_runs']:>4} "
                  f"{summary['avg_win_rate']:>6.1f}% {summary['avg_hold_days']:>4.0f}d "
                  f"{summary['consistency']:>6.1f}%")
        
        return {
            'strategy_summary': strategy_summary,
            'sorted_strategies': sorted_strategies,
            'all_results': all_results
        }

def main():
    """
    Run comprehensive exit strategy comparison
    """
    print("COMPREHENSIVE EXIT STRATEGY COMPARISON")
    print("=" * 50)
    print("Testing multiple professional exit methods:")
    print("• Moving averages (10, 20, 40 day)")
    print("• ATR-based trailing stops")
    print("• Percentage trailing stops")
    print("• Volatility-adjusted exits")
    print("• Parabolic SAR")
    print("• Fixed profit targets")
    print()
    
    tester = ExitStrategyComparison()
    
    # Test on high-quality growth stocks
    test_stocks = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD']
    
    try:
        results = tester.comprehensive_exit_comparison(test_stocks)
        
        print(f"\n" + "=" * 70)
        print("EXIT STRATEGY INSIGHTS")
        print("=" * 70)
        
        # Find best performing strategy
        best_strategy = results['sorted_strategies'][0]
        print(f"Best Overall: {best_strategy[1]['name']}")
        print(f"  Average Return: {best_strategy[1]['avg_return']:.1f}%")
        print(f"  Consistency: {best_strategy[1]['consistency']:.1f}%")
        
        print(f"\nKey Takeaways:")
        print(f"• Different exit strategies work better in different conditions")
        print(f"• Consider market volatility when choosing exit method")
        print(f"• Balance between profit capture and trend following")
        print(f"• Test multiple methods to find your optimal approach")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()