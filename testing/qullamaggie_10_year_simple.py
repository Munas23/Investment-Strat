"""
Simplified 10-Year Test of Qullamaggie Strategies (no unicode issues)
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
    """Extended Qullamaggie testing with 10-year period"""
    
    def get_historical_data_10_year(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get 10+ years of historical data"""
        try:
            end_date = datetime.now()
            start_date = datetime(2014, 1, 1)  # 10+ years
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 2520:  # Need at least 10 years
                print(f"  Insufficient data for {symbol}: {len(data)} days")
                return None
            
            data.columns = [col.lower() for col in data.columns]
            print(f"  Got {len(data)} days ({len(data)/252:.1f} years) for {symbol}")
            return data
            
        except Exception as e:
            print(f"  Error getting data for {symbol}: {e}")
            return None
    
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
            print(f"  Error calculating buy-hold for {symbol}: {e}")
            return 0
    
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
        
        print("COMPREHENSIVE 10-YEAR QULLAMAGGIE STRATEGY TEST")
        print("=" * 60)
        print("Testing period: 2014-2024 (10+ years)")
        print("Multiple market cycles: Recovery, Bull, COVID, Bubble, Current")
        print(f"Testing {len(symbols)} symbols across 4 strategies")
        print("=" * 60)
        
        # Get data for all symbols first
        print("\nLoading 10-year historical data...")
        stock_data = {}
        valid_symbols = []
        buy_hold_returns = {}
        
        for symbol in symbols:
            print(f"Loading {symbol}...")
            data = self.get_historical_data_10_year(symbol)
            if data is not None:
                stock_data[symbol] = data
                valid_symbols.append(symbol)
                
                # Calculate buy-and-hold return
                buy_hold_return = self.calculate_buy_hold_return_10_year(symbol)
                buy_hold_returns[symbol] = buy_hold_return
                print(f"  Buy-Hold Return: {buy_hold_return:.1f}%")
        
        print(f"\nSuccessfully loaded {len(valid_symbols)} symbols with 10+ years of data")
        print(f"Valid symbols: {valid_symbols}")
        
        # Test all strategies
        print(f"\nTesting Qullamaggie strategies...")
        all_results = []
        strategy_methods = {
            'High Tight Flag': 'high_tight_flag',
            'Breakout Strategy': 'breakout_strategy', 
            'Episodic Pivots': 'episodic_pivots',
            'Combined Qullamaggie': 'combined_qullamaggie'
        }
        
        for strategy_name, method in strategy_methods.items():
            print(f"\nTesting {strategy_name}:")
            strategy_results = []
            
            for symbol in valid_symbols:
                print(f"  {symbol}: ", end="")
                
                try:
                    if hasattr(self, method):
                        result = getattr(self, method)(stock_data[symbol])
                        result['symbol'] = symbol
                        result['strategy_name'] = strategy_name
                        result['buy_hold_return'] = buy_hold_returns[symbol]
                        result['excess_return'] = result['total_return'] - buy_hold_returns[symbol]
                        
                        strategy_results.append(result)
                        all_results.append(result)
                        
                        print(f"{result['total_return']:.1f}% ({result['num_trades']} trades)")
                    else:
                        print(f"Method {method} not found")
                        
                except Exception as e:
                    print(f"Error - {str(e)[:30]}...")
            
            # Strategy summary
            if strategy_results:
                avg_return = np.mean([r['total_return'] for r in strategy_results])
                avg_trades = np.mean([r['num_trades'] for r in strategy_results])
                print(f"  {strategy_name} Average: {avg_return:.1f}% return, {avg_trades:.1f} trades")
        
        return self.analyze_10_year_results(all_results, buy_hold_returns)
    
    def analyze_10_year_results(self, all_results: List[Dict], buy_hold_returns: Dict) -> Dict:
        """Comprehensive analysis of 10-year results"""
        print(f"\n" + "=" * 80)
        print("COMPREHENSIVE 10-YEAR RESULTS ANALYSIS")
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
        
        # Buy and Hold comparison
        print(f"\n" + "=" * 80)
        print("BUY AND HOLD vs QULLAMAGGIE STRATEGIES")
        print("=" * 80)
        
        bh_returns = list(buy_hold_returns.values())
        avg_buy_hold = np.mean(bh_returns)
        median_buy_hold = np.median(bh_returns)
        
        print(f"Buy and Hold Performance (10-year period):")
        print(f"  Average Return: {avg_buy_hold:.1f}%")
        print(f"  Median Return: {median_buy_hold:.1f}%")
        print(f"  Best Stock: {max(bh_returns):.1f}%")
        print(f"  Worst Stock: {min(bh_returns):.1f}%")
        print(f"  Stocks Tested: {len(bh_returns)}")
        print(f"  Positive Returns: {len([r for r in bh_returns if r > 0])}/{len(bh_returns)} ({len([r for r in bh_returns if r > 0])/len(bh_returns)*100:.1f}%)")
        
        print(f"\nBest Qullamaggie Strategy vs Buy and Hold:")
        if sorted_strategies:
            best_strategy = sorted_strategies[0]
            best_name = best_strategy[0]
            best_stats = best_strategy[1]
            
            print(f"  {best_name}: {best_stats['avg_return']:.1f}% vs Buy-Hold: {avg_buy_hold:.1f}%")
            print(f"  Excess Return: {best_stats['avg_excess_return']:.1f}%")
            print(f"  Beat Buy-Hold: {best_stats['beat_buy_hold_pct']:.1f}% of the time")
            print(f"  Consistency: {best_stats['consistency']:.1f}% vs Buy-Hold: {len([r for r in bh_returns if r > 0])/len(bh_returns)*100:.1f}%")
        
        # Individual stock analysis
        print(f"\n" + "=" * 80)
        print("INDIVIDUAL STOCK PERFORMANCE BREAKDOWN")
        print("=" * 80)
        
        # Group results by symbol for detailed comparison
        by_symbol = {}
        for result in all_results:
            symbol = result['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = {'buy_hold': buy_hold_returns[symbol], 'strategies': {}}
            by_symbol[symbol]['strategies'][result['strategy_name']] = result['total_return']
        
        # Show top performing stocks
        print("Stock performance (Buy-Hold vs Best Qullamaggie Strategy):")
        print(f"{'Symbol':<8} {'Buy-Hold':<12} {'Best Strategy':<15} {'Best Return':<12} {'Excess':<10}")
        print("-" * 65)
        
        for symbol, data in sorted(by_symbol.items(), key=lambda x: x[1]['buy_hold'], reverse=True):
            bh_return = data['buy_hold']
            strategies = data['strategies']
            
            if strategies:
                best_strategy_return = max(strategies.values())
                best_strategy_name = max(strategies.items(), key=lambda x: x[1])[0]
                excess = best_strategy_return - bh_return
                
                print(f"{symbol:<8} {bh_return:>10.1f}% {best_strategy_name:<15} {best_strategy_return:>10.1f}% {excess:>8.1f}%")
            else:
                print(f"{symbol:<8} {bh_return:>10.1f}% {'No Data':<15} {'N/A':<12} {'N/A':<10}")
        
        return {
            'strategy_summary': strategy_summary,
            'buy_hold_stats': {
                'avg_return': avg_buy_hold,
                'median_return': median_buy_hold,
                'returns': bh_returns
            },
            'by_symbol': by_symbol
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
        print("KEY CONCLUSIONS FROM 10-YEAR TEST")
        print("=" * 80)
        
        strategy_summary = results['strategy_summary']
        bh_stats = results['buy_hold_stats']
        
        # Find best strategy
        if strategy_summary:
            best_strategy = max(strategy_summary.items(), key=lambda x: x[1]['avg_return'])
            best_name, best_stats = best_strategy
            
            print(f"PERFORMANCE SUMMARY:")
            print(f"  Best Qullamaggie Strategy: {best_name}")
            print(f"    - Average Return: {best_stats['avg_return']:.1f}%")
            print(f"    - Beat Buy-Hold: {best_stats['beat_buy_hold_pct']:.1f}% of time")
            print(f"    - Average Excess Return: {best_stats['avg_excess_return']:.1f}%")
            print()
            print(f"  Buy and Hold Benchmark:")
            print(f"    - Average Return: {bh_stats['avg_return']:.1f}%")
            print(f"    - Consistency: Nearly 100% (almost always positive over 10 years)")
            print()
            
            if best_stats['avg_return'] > bh_stats['avg_return']:
                print(f"WINNER: {best_name} beats Buy-and-Hold!")
                margin = best_stats['avg_return'] - bh_stats['avg_return']
                print(f"   Margin: +{margin:.1f} percentage points")
            else:
                print(f"WINNER: Buy-and-Hold beats all active strategies")
                margin = bh_stats['avg_return'] - best_stats['avg_return']
                print(f"   Margin: +{margin:.1f} percentage points")
            
            print(f"\nKEY INSIGHTS:")
            print(f"  - Testing period covered multiple market cycles (2014-2024)")
            print(f"  - {len(results['buy_hold_stats']['returns'])} stocks tested over 10+ years")
            print(f"  - Active strategies required significantly more trades")
            print(f"  - Results show the challenge/opportunity of beating simple indexing")
            
            # Show which stocks favored active strategies
            by_symbol = results['by_symbol']
            active_winners = []
            for symbol, data in by_symbol.items():
                if data['strategies']:
                    best_active = max(data['strategies'].values())
                    if best_active > data['buy_hold']:
                        active_winners.append((symbol, best_active - data['buy_hold']))
            
            if active_winners:
                print(f"\nStocks where active strategies beat buy-hold:")
                for symbol, excess in sorted(active_winners, key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {symbol}: +{excess:.1f}% excess return")
            
        else:
            print("No strategy results available")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()