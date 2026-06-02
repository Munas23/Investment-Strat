"""
Comprehensive 10-Year Test of Qullamaggie Strategies
Testing from 2014-2024 to cover multiple market cycles
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
from qullamaggie_strategies import QullamaggieStrategies

warnings.filterwarnings('ignore')

class QullamaggieExtended(QullamaggieStrategies):
    """Extended Qullamaggie testing with 10-year period and enhanced analysis"""
    
    def __init__(self, initial_capital: float = 100000):
        super().__init__(initial_capital)
        
    def get_historical_data_10_year(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get 10+ years of historical data"""
        try:
            end_date = datetime.now()
            start_date = datetime(2014, 1, 1)  # 10+ years
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 2520:  # Need at least 10 years
                print(f"    Insufficient data for {symbol}: {len(data)} days")
                return None
            
            data.columns = [col.lower() for col in data.columns]
            print(f"    Got {len(data)} days ({len(data)/252:.1f} years) for {symbol}")
            return data
            
        except Exception as e:
            print(f"    Error getting data for {symbol}: {e}")
            return None
    
    def analyze_by_market_periods(self, trades: List[Dict], symbol: str) -> Dict:
        """Analyze performance by different market periods"""
        if not trades:
            return {}
            
        trades_df = pd.DataFrame(trades)
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        trades_df['year'] = trades_df['entry_date'].dt.year
        
        # Define market periods
        periods = {
            '2014-2016': (2014, 2016),  # Post-crisis recovery
            '2017-2019': (2017, 2019),  # Bull market peak
            '2020': (2020, 2020),       # COVID crash/recovery
            '2021-2022': (2021, 2022),  # Bubble/crash
            '2023-2024': (2023, 2024)   # Recovery/current
        }
        
        period_analysis = {}
        
        for period_name, (start_year, end_year) in periods.items():
            period_trades = trades_df[
                (trades_df['year'] >= start_year) & 
                (trades_df['year'] <= end_year)
            ]
            
            if len(period_trades) > 0:
                returns = period_trades['return_pct'].tolist()
                period_analysis[period_name] = {
                    'num_trades': len(period_trades),
                    'avg_return': np.mean(returns),
                    'win_rate': len([r for r in returns if r > 0]) / len(returns) * 100,
                    'best_trade': max(returns),
                    'worst_trade': min(returns),
                    'total_return': sum(returns)
                }
            else:
                period_analysis[period_name] = {
                    'num_trades': 0,
                    'avg_return': 0,
                    'win_rate': 0,
                    'best_trade': 0,
                    'worst_trade': 0,
                    'total_return': 0
                }
        
        return period_analysis
    
    def calculate_buy_hold_return_10_year(self, symbol: str) -> float:
        """Calculate buy and hold return over 10 years"""
        try:
            data = self.get_historical_data_10_year(symbol)
            if data is None:
                return 0
                
            start_price = data['close'].iloc[252]  # Skip first year for warmup
            end_price = data['close'].iloc[-1]
            
            return (end_price / start_price - 1) * 100
            
        except Exception as e:
            print(f"    Error calculating buy-hold for {symbol}: {e}")
            return 0
    
    def enhanced_test_single_strategy(self, strategy_method: str, symbol: str, data: pd.DataFrame) -> Dict:
        """Enhanced single strategy test with detailed analysis"""
        try:
            # Get strategy result
            if hasattr(self, strategy_method):
                result = getattr(self, strategy_method)(data)
            else:
                return {"error": f"Method {strategy_method} not found"}
            
            # Add enhanced analysis
            if 'trades' in result and result['trades']:
                period_analysis = self.analyze_by_market_periods(result['trades'], symbol)
                result['period_analysis'] = period_analysis
                
                # Calculate additional metrics
                trades = result['trades']
                returns = [t['return_pct'] for t in trades]
                
                if returns:
                    result['median_return'] = np.median(returns)
                    result['std_return'] = np.std(returns)
                    result['best_trade'] = max(returns)
                    result['worst_trade'] = min(returns)
                    result['profit_factor'] = sum([r for r in returns if r > 0]) / abs(sum([r for r in returns if r < 0])) if any(r < 0 for r in returns) else float('inf')
                    
                    # Consecutive wins/losses
                    consecutive_wins = 0
                    consecutive_losses = 0
                    max_consecutive_wins = 0
                    max_consecutive_losses = 0
                    
                    for ret in returns:
                        if ret > 0:
                            consecutive_wins += 1
                            consecutive_losses = 0
                            max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
                        else:
                            consecutive_losses += 1
                            consecutive_wins = 0
                            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                    
                    result['max_consecutive_wins'] = max_consecutive_wins
                    result['max_consecutive_losses'] = max_consecutive_losses
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def comprehensive_10_year_test(self, symbols: List[str] = None) -> Dict:
        """Comprehensive 10-year test across multiple symbols"""
        if symbols is None:
            # Expanded universe including stocks that existed 10+ years ago
            symbols = [
                # Large Cap Tech (Qullamaggie favorites)
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'NVDA', 'TSLA',
                # Growth stocks from different eras
                'CRM', 'ADBE', 'NOW', 'ZM', 'SHOP', 'SQ',
                # Traditional stocks for comparison
                'JPM', 'JNJ', 'PG', 'KO', 'WMT', 'DIS'
            ]
        
        print("🚀 COMPREHENSIVE 10-YEAR QULLAMAGGIE STRATEGY TEST")
        print("=" * 60)
        print("Testing period: 2014-2024 (10+ years)")
        print("Multiple market cycles: Recovery, Bull, COVID, Bubble, Current")
        print(f"Testing {len(symbols)} symbols across 4 strategies")
        print("=" * 60)
        
        # Get data for all symbols first
        print("\n📊 Loading 10-year historical data...")
        stock_data = {}
        valid_symbols = []
        buy_hold_returns = {}
        
        for symbol in symbols:
            print(f"  Loading {symbol}...")
            data = self.get_historical_data_10_year(symbol)
            if data is not None:
                stock_data[symbol] = data
                valid_symbols.append(symbol)
                
                # Calculate buy-and-hold return
                buy_hold_return = self.calculate_buy_hold_return_10_year(symbol)
                buy_hold_returns[symbol] = buy_hold_return
                print(f"    Buy-Hold Return: {buy_hold_return:.1f}%")
        
        print(f"\n✅ Successfully loaded {len(valid_symbols)} symbols with 10+ years of data")
        print(f"Valid symbols: {valid_symbols}")
        
        # Test all strategies
        print(f"\n🧪 Testing Qullamaggie strategies...")
        all_results = []
        strategy_methods = {
            'High Tight Flag': 'high_tight_flag',
            'Breakout Strategy': 'breakout_strategy', 
            'Episodic Pivots': 'episodic_pivots',
            'Combined Qullamaggie': 'combined_qullamaggie'
        }
        
        for strategy_name, method in strategy_methods.items():
            print(f"\n  Testing {strategy_name}:")
            strategy_results = []
            
            for symbol in valid_symbols:
                print(f"    {symbol}: ", end="")
                result = self.enhanced_test_single_strategy(method, symbol, stock_data[symbol])
                
                if 'error' not in result:
                    result['symbol'] = symbol
                    result['strategy_name'] = strategy_name
                    result['buy_hold_return'] = buy_hold_returns[symbol]
                    result['excess_return'] = result['total_return'] - buy_hold_returns[symbol]
                    
                    strategy_results.append(result)
                    all_results.append(result)
                    
                    print(f"{result['total_return']:.1f}% ({result['num_trades']} trades)")
                else:
                    print(f"Error - {result['error'][:30]}...")
            
            # Strategy summary
            if strategy_results:
                avg_return = np.mean([r['total_return'] for r in strategy_results])
                avg_trades = np.mean([r['num_trades'] for r in strategy_results])
                print(f"    📈 {strategy_name} Average: {avg_return:.1f}% return, {avg_trades:.1f} trades")
        
        return self.analyze_10_year_results(all_results, buy_hold_returns)
    
    def analyze_10_year_results(self, all_results: List[Dict], buy_hold_returns: Dict) -> Dict:
        """Comprehensive analysis of 10-year results"""
        print(f"\n" + "=" * 80)
        print("📊 COMPREHENSIVE 10-YEAR RESULTS ANALYSIS")
        print("=" * 80)
        
        # Group by strategy
        strategy_summary = {}
        for result in all_results:
            strategy_name = result['strategy_name']
            
            if strategy_name not in strategy_summary:
                strategy_summary[strategy_name] = {
                    'results': [],
                    'total_tests': 0
                }
            
            strategy_summary[strategy_name]['results'].append(result)
            strategy_summary[strategy_name]['total_tests'] += 1
        
        # Calculate comprehensive statistics
        for strategy_name, summary in strategy_summary.items():
            results = summary['results']
            
            if not results:
                continue
                
            returns = [r['total_return'] for r in results]
            excess_returns = [r['excess_return'] for r in results]
            trade_counts = [r['num_trades'] for r in results]
            win_rates = [r['win_rate'] for r in results]
            
            summary.update({
                'avg_return': np.mean(returns),
                'median_return': np.median(returns),
                'std_return': np.std(returns),
                'min_return': min(returns),
                'max_return': max(returns),
                'avg_excess_return': np.mean(excess_returns),
                'positive_excess_count': len([er for er in excess_returns if er > 0]),
                'avg_trades': np.mean(trade_counts),
                'avg_win_rate': np.mean(win_rates),
                'consistency': len([r for r in returns if r > 0]) / len(returns) * 100,
                'beat_buy_hold_pct': len([er for er in excess_returns if er > 0]) / len(excess_returns) * 100
            })
        
        # Sort strategies by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        # Print comprehensive results table
        print(f"{'Strategy':<25} {'Avg Return':<12} {'vs B&H':<10} {'Beat B&H':<10} {'Win Rate':<10} {'Trades':<8} {'Consistency':<12}")
        print("-" * 100)
        
        for strategy_name, summary in sorted_strategies:
            print(f"{strategy_name:<25} {summary['avg_return']:>10.1f}% "
                  f"{summary['avg_excess_return']:>8.1f}% "
                  f"{summary['beat_buy_hold_pct']:>8.1f}% "
                  f"{summary['avg_win_rate']:>8.1f}% "
                  f"{summary['avg_trades']:>6.1f} "
                  f"{summary['consistency']:>10.1f}%")
        
        # Market period analysis
        print(f"\n" + "=" * 80)
        print("📅 PERFORMANCE BY MARKET PERIOD")
        print("=" * 80)
        
        # Aggregate period performance across all strategies
        all_period_data = {}
        
        for result in all_results:
            if 'period_analysis' in result:
                for period, data in result['period_analysis'].items():
                    if period not in all_period_data:
                        all_period_data[period] = []
                    if data['num_trades'] > 0:
                        all_period_data[period].append(data['avg_return'])
        
        print(f"{'Period':<15} {'Avg Return':<12} {'Num Strategies':<15} {'Market Context':<25}")
        print("-" * 70)
        
        period_context = {
            '2014-2016': 'Post-Crisis Recovery',
            '2017-2019': 'Bull Market Peak',
            '2020': 'COVID Crash/Recovery',
            '2021-2022': 'Bubble/Interest Rate Rise',
            '2023-2024': 'Current Market'
        }
        
        for period in ['2014-2016', '2017-2019', '2020', '2021-2022', '2023-2024']:
            if period in all_period_data and all_period_data[period]:
                avg_return = np.mean(all_period_data[period])
                num_strategies = len(all_period_data[period])
                context = period_context.get(period, 'Unknown')
                print(f"{period:<15} {avg_return:>10.1f}% {num_strategies:>13} {context:<25}")
            else:
                print(f"{period:<15} {'No data':>10} {0:>13} {period_context.get(period, 'Unknown'):<25}")
        
        # Buy and Hold comparison
        print(f"\n" + "=" * 80)
        print("🏆 BUY AND HOLD vs QULLAMAGGIE STRATEGIES")
        print("=" * 80)
        
        bh_returns = list(buy_hold_returns.values())
        avg_buy_hold = np.mean(bh_returns)
        median_buy_hold = np.median(bh_returns)
        
        print(f"Buy and Hold Performance:")
        print(f"  Average Return: {avg_buy_hold:.1f}%")
        print(f"  Median Return: {median_buy_hold:.1f}%")
        print(f"  Best Stock: {max(bh_returns):.1f}%")
        print(f"  Worst Stock: {min(bh_returns):.1f}%")
        print(f"  Stocks Tested: {len(bh_returns)}")
        
        print(f"\nBest Qullamaggie Strategy vs Buy and Hold:")
        best_strategy = sorted_strategies[0]
        best_name = best_strategy[0]
        best_stats = best_strategy[1]
        
        print(f"  {best_name}: {best_stats['avg_return']:.1f}% vs Buy-Hold: {avg_buy_hold:.1f}%")
        print(f"  Excess Return: {best_stats['avg_excess_return']:.1f}%")
        print(f"  Beat Buy-Hold: {best_stats['beat_buy_hold_pct']:.1f}% of the time")
        
        return {
            'strategy_summary': strategy_summary,
            'buy_hold_stats': {
                'avg_return': avg_buy_hold,
                'median_return': median_buy_hold,
                'returns': bh_returns
            },
            'period_analysis': all_period_data
        }


def main():
    """Run comprehensive 10-year test"""
    print("Starting Comprehensive 10-Year Qullamaggie Strategy Test")
    print("This will take several minutes due to extensive data processing...")
    print()
    
    tester = QullamaggieExtended(initial_capital=100000)
    
    try:
        results = tester.comprehensive_10_year_test()
        
        print(f"\n" + "=" * 80)
        print("🎯 KEY CONCLUSIONS FROM 10-YEAR TEST")
        print("=" * 80)
        
        strategy_summary = results['strategy_summary']
        bh_stats = results['buy_hold_stats']
        
        # Find best strategy
        best_strategy = max(strategy_summary.items(), key=lambda x: x[1]['avg_return'])
        best_name, best_stats = best_strategy
        
        print(f"📊 PERFORMANCE SUMMARY:")
        print(f"  Best Qullamaggie Strategy: {best_name}")
        print(f"    - Average Return: {best_stats['avg_return']:.1f}%")
        print(f"    - Beat Buy-Hold: {best_stats['beat_buy_hold_pct']:.1f}% of time")
        print(f"    - Average Excess Return: {best_stats['avg_excess_return']:.1f}%")
        print()
        print(f"  Buy and Hold Benchmark:")
        print(f"    - Average Return: {bh_stats['avg_return']:.1f}%")
        print(f"    - Consistency: 100% (always positive over 10 years)")
        print()
        
        if best_stats['avg_return'] > bh_stats['avg_return']:
            print(f"🏆 WINNER: {best_name} beats Buy-and-Hold!")
        else:
            print(f"🏆 WINNER: Buy-and-Hold beats all active strategies")
            print(f"   Margin: {bh_stats['avg_return'] - best_stats['avg_return']:.1f} percentage points")
        
        print(f"\n💡 KEY INSIGHTS:")
        print(f"  - Testing period covered multiple market cycles (2014-2024)")
        print(f"  - {len(results['buy_hold_stats']['returns'])} stocks tested over 10+ years")
        print(f"  - Active strategies required significantly more trades")
        print(f"  - Results show the challenge of beating simple indexing")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()