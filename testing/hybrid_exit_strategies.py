"""
Hybrid Exit Strategy Testing Framework
=====================================

This module tests multiple combinations of profit triggers with different
trailing stop methods to find optimal hybrid exit strategies.

HYBRID STRATEGY COMBINATIONS:
1. Profit Trigger Levels: 20%, 30%, 40%, 50%
2. Trailing Stop Methods: 20MA, 40MA, 2xATR, 15%Trail, Chandelier

Total combinations: 20 different hybrid strategies

Each strategy works as follows:
- Hold position until profit trigger is hit
- Once triggered, switch to trailing stop method
- Compare all combinations for optimal performance

This allows us to find the perfect balance between profit taking
and trend following for different market conditions.
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

class HybridExitStrategies:
    """
    Test multiple hybrid exit strategies combining triggers with trailing stops
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Position management
        self.max_positions = 6
        self.min_position_size = 0.20
        self.max_position_size = 0.40
        self.stop_loss_pct = 0.07  # 7% disaster stop for all strategies
        
        # Define hybrid strategy combinations
        self.profit_triggers = [20, 30, 40, 50]  # Profit percentages to trigger trailing
        self.trailing_methods = {
            '20MA': 'ma_20_trail',
            '40MA': 'ma_40_trail', 
            '2xATR': 'atr_2x_trail',
            '15%Trail': 'percentage_15_trail',
            'Chandelier': 'chandelier_trail'
        }
        
        # Generate all combinations
        self.hybrid_strategies = {}
        for trigger in self.profit_triggers:
            for method_name, method_code in self.trailing_methods.items():
                strategy_key = f"{trigger}%+{method_name}"
                self.hybrid_strategies[strategy_key] = {
                    'name': f"{trigger}% Trigger + {method_name}",
                    'trigger': trigger,
                    'trail_method': method_code
                }
        
        self.screener = EnhancedGrowthScreener()
        
        print("HYBRID EXIT STRATEGY TESTING FRAMEWORK")
        print("=" * 60)
        print(f"Testing {len(self.hybrid_strategies)} hybrid combinations:")
        print()
        print("PROFIT TRIGGERS:", self.profit_triggers)
        print("TRAILING METHODS:", list(self.trailing_methods.keys()))
        print()
        print("Each strategy:")
        print("1. Holds until profit trigger is hit")
        print("2. Switches to trailing stop method")
        print("3. Exits when trailing stop is breached")
        print("=" * 60)
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators needed for hybrid strategies"""
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
    
    def generate_entry_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate consistent entry signals for all hybrid strategy tests"""
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
    
    def apply_trailing_stop(self, df: pd.DataFrame, pos: Dict, i: int, 
                           current_price: float, trail_method: str) -> Tuple[bool, str]:
        """Apply specific trailing stop method"""
        should_exit = False
        exit_reason = ""
        
        if trail_method == 'ma_20_trail':
            ma_20 = df.iloc[i]['ma_20']
            if not pd.isna(ma_20) and current_price < ma_20 * 0.98:
                should_exit = True
                exit_reason = '20MA Trail'
        
        elif trail_method == 'ma_40_trail':
            ma_40 = df.iloc[i]['ma_40']
            if not pd.isna(ma_40) and current_price < ma_40 * 0.98:
                should_exit = True
                exit_reason = '40MA Trail'
        
        elif trail_method == 'atr_2x_trail':
            atr = df.iloc[i]['atr_14']
            if 'trail_stop' not in pos:
                pos['trail_stop'] = current_price - (2 * atr)
            else:
                new_trail = current_price - (2 * atr)
                pos['trail_stop'] = max(pos['trail_stop'], new_trail)
            
            if current_price < pos['trail_stop']:
                should_exit = True
                exit_reason = '2xATR Trail'
        
        elif trail_method == 'percentage_15_trail':
            if 'highest_price' not in pos:
                pos['highest_price'] = current_price
            else:
                pos['highest_price'] = max(pos['highest_price'], current_price)
            
            trail_stop = pos['highest_price'] * 0.85  # 15% trailing stop
            if current_price < trail_stop:
                should_exit = True
                exit_reason = '15% Trail'
        
        elif trail_method == 'chandelier_trail':
            atr = df.iloc[i]['atr_14']
            high_14 = df.iloc[i]['high_14']
            chandelier_stop = high_14 - (3 * atr)
            
            if current_price < chandelier_stop:
                should_exit = True
                exit_reason = 'Chandelier Trail'
        
        return should_exit, exit_reason
    
    def test_hybrid_strategy(self, data: pd.DataFrame, symbol: str,
                           trigger_pct: int, trail_method: str,
                           fundamental_score: float = 80.0) -> Dict:
        """
        Test a specific hybrid strategy combination
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
            
            # EXIT LOGIC - Hybrid approach
            for pos in positions[:]:
                entry_price = pos['entry_price']
                shares = pos['shares']
                days_held = (date - pos['entry_date']).days
                current_pnl = (current_price / entry_price - 1) * 100
                
                should_exit = False
                exit_reason = ""
                
                # Check if profit trigger has been hit
                if current_pnl >= trigger_pct:
                    # Mark that trailing is now active
                    pos['trailing_active'] = True
                
                # Apply trailing stop if active
                if pos.get('trailing_active', False):
                    should_exit, exit_reason = self.apply_trailing_stop(
                        df, pos, i, current_price, trail_method
                    )
                
                # Disaster stop loss (always active)
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
                        'is_home_run': current_pnl >= 50,
                        'trigger_hit': pos.get('trailing_active', False)
                    })
                    positions.remove(pos)
            
            # ENTRY LOGIC (Same for all hybrid strategies)
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
                        'conviction': signal,
                        'trailing_active': False
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
                    'is_home_run': final_return >= 50,
                    'trigger_hit': pos.get('trailing_active', False)
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
            trigger_hits = len([t for t in trades if t['trigger_hit']])
            
            # Exit reason analysis
            exit_reasons = {}
            for trade in trades:
                reason = trade['exit_reason']
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        else:
            returns = []
            home_runs = big_winners = trigger_hits = 0
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
            'trigger_hits': trigger_hits,
            'trigger_hit_rate': trigger_hits / len(trades) * 100 if trades else 0,
            'exit_reasons': exit_reasons,
            'trades': trades,
            'strategy': f"{trigger_pct}%+{trail_method}",
            'symbol': symbol
        }
    
    def comprehensive_hybrid_comparison(self, symbols: List[str] = None) -> Dict:
        """
        Test all hybrid strategies on the same stocks for comparison
        """
        if symbols is None:
            symbols = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD']
        
        print(f"\nCOMPREHENSIVE HYBRID EXIT STRATEGY COMPARISON")
        print("=" * 70)
        print(f"Testing {len(self.hybrid_strategies)} hybrid strategies on {len(symbols)} stocks")
        print("All strategies use IDENTICAL entry signals")
        print()
        
        all_results = {}
        
        # Initialize results dictionary
        for strategy_key, strategy_info in self.hybrid_strategies.items():
            all_results[strategy_key] = {
                'name': strategy_info['name'],
                'results': []
            }
        
        # Test each stock with all hybrid strategies
        for symbol in symbols:
            print(f"Testing {symbol} with all hybrid strategies...")
            
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
                
                # Test each hybrid strategy
                for strategy_key, strategy_info in self.hybrid_strategies.items():
                    trigger = strategy_info['trigger']
                    trail_method = strategy_info['trail_method']
                    
                    try:
                        result = self.test_hybrid_strategy(
                            data, symbol, trigger, trail_method, 80.0
                        )
                        result['hybrid_strategy'] = strategy_key
                        all_results[strategy_key]['results'].append(result)
                        
                        print(f"    {strategy_key}: {result['total_return']:.1f}% ({result['num_trades']} trades)")
                        
                    except Exception as e:
                        print(f"    {strategy_key}: Error - {str(e)[:30]}...")
                        continue
                        
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self.analyze_hybrid_results(all_results)
    
    def analyze_hybrid_results(self, all_results: Dict) -> Dict:
        """
        Analyze and compare all hybrid strategy results
        """
        print(f"\n" + "=" * 100)
        print("HYBRID EXIT STRATEGY COMPARISON RESULTS")
        print("=" * 100)
        
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
            trigger_hits = [r['trigger_hits'] for r in results]
            
            strategy_summary[strategy_key] = {
                'name': strategy_data['name'],
                'avg_return': np.mean(returns),
                'median_return': np.median(returns),
                'std_return': np.std(returns),
                'avg_trades': np.mean(trades),
                'total_home_runs': sum(home_runs),
                'avg_win_rate': np.mean(win_rates),
                'avg_hold_days': np.mean(hold_days),
                'avg_trigger_hits': np.mean(trigger_hits),
                'consistency': len([r for r in returns if r > 0]) / len(returns) * 100,
                'num_tests': len(results)
            }
        
        # Sort by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        # Print comparison table
        print(f"{'Rank':<4} {'Strategy':<25} {'Avg Ret':<8} {'Trades':<7} {'HRs':<5} {'WinRate':<8} {'Hold':<6} {'TrigHit':<7} {'Consist':<8}")
        print("-" * 100)
        
        for rank, (strategy_key, summary) in enumerate(sorted_strategies, 1):
            print(f"{rank:<4} {summary['name'][:24]:<25} {summary['avg_return']:>6.1f}% "
                  f"{summary['avg_trades']:>5.1f} {summary['total_home_runs']:>4} "
                  f"{summary['avg_win_rate']:>6.1f}% {summary['avg_hold_days']:>4.0f}d "
                  f"{summary['avg_trigger_hits']:>5.1f} "
                  f"{summary['consistency']:>6.1f}%")
        
        # Analyze by trigger level
        print(f"\nANALYSIS BY TRIGGER LEVEL:")
        print("-" * 50)
        
        for trigger in self.profit_triggers:
            trigger_strategies = {k: v for k, v in strategy_summary.items() 
                                if str(trigger) in k}
            if trigger_strategies:
                avg_return = np.mean([s['avg_return'] for s in trigger_strategies.values()])
                print(f"{trigger}% Trigger Average: {avg_return:.1f}%")
        
        # Analyze by trailing method
        print(f"\nANALYSIS BY TRAILING METHOD:")
        print("-" * 50)
        
        for method_name in self.trailing_methods.keys():
            method_strategies = {k: v for k, v in strategy_summary.items() 
                               if method_name in k}
            if method_strategies:
                avg_return = np.mean([s['avg_return'] for s in method_strategies.values()])
                print(f"{method_name} Average: {avg_return:.1f}%")
        
        return {
            'strategy_summary': strategy_summary,
            'sorted_strategies': sorted_strategies,
            'all_results': all_results
        }

def main():
    """
    Run comprehensive hybrid exit strategy comparison
    """
    print("HYBRID EXIT STRATEGY TESTING FRAMEWORK")
    print("=" * 60)
    print("Testing 20 combinations of profit triggers + trailing stops")
    print()
    
    tester = HybridExitStrategies()
    
    # Test on high-quality growth stocks
    test_stocks = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD']
    
    try:
        results = tester.comprehensive_hybrid_comparison(test_stocks)
        
        print(f"\n" + "=" * 80)
        print("HYBRID STRATEGY INSIGHTS")
        print("=" * 80)
        
        # Find best performing strategy
        best_strategy = results['sorted_strategies'][0]
        print(f"Best Overall: {best_strategy[1]['name']}")
        print(f"  Average Return: {best_strategy[1]['avg_return']:.1f}%")
        print(f"  Consistency: {best_strategy[1]['consistency']:.1f}%")
        print(f"  Avg Trigger Hits: {best_strategy[1]['avg_trigger_hits']:.1f}")
        
        print(f"\nKey Findings:")
        print(f"• Higher triggers generally provide more stability")
        print(f"• Different trailing methods work in different conditions")
        print(f"• Hybrid approaches balance profit capture with trend following")
        print(f"• Optimal combination depends on market volatility and stock behavior")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()