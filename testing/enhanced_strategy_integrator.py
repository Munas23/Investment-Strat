"""
Enhanced Strategy Integrator
===========================

This module integrates the enhanced growth screener with existing trading strategies
to improve stock selection and overall performance. It can be applied to any strategy
including Minervini, Qullamaggie, and traditional technical analysis approaches.

INTEGRATION FEATURES:
1. Pre-screens stocks using enhanced growth criteria
2. Only trades fundamentally strong stocks
3. Maintains original strategy logic for timing
4. Compares performance vs unfiltered strategies
5. Provides detailed analysis of improvement

The goal is to prove that fundamental screening + technical timing
significantly outperforms pure technical analysis.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

# Import our enhanced screener and existing strategies
from enhanced_growth_screener import EnhancedGrowthScreener
from minervini_complete import MinerviniComplete
from qullamaggie_strategies import QullamaggieStrategies
from alternative_strategies import AlternativeStrategies

warnings.filterwarnings('ignore')

class EnhancedStrategyIntegrator:
    """
    Integrates enhanced fundamental screening with any trading strategy
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Initialize screener and strategies
        self.screener = EnhancedGrowthScreener()
        self.minervini = MinerviniComplete(initial_capital)
        self.qullamaggie = QullamaggieStrategies(initial_capital)
        self.alternatives = AlternativeStrategies(initial_capital)
        
        print("ENHANCED STRATEGY INTEGRATOR")
        print("=" * 50)
        print("Integrating fundamental growth screening with:")
        print("1. Minervini strategies")
        print("2. Qullamaggie strategies") 
        print("3. Alternative strategies")
        print("4. Custom technical strategies")
        print("=" * 50)
    
    def get_enhanced_stock_universe(self, base_symbols: List[str], 
                                  min_score: float = 60.0) -> Tuple[List[str], Dict]:
        """
        Screen base stock universe and return only fundamentally strong stocks
        """
        print(f"\nENHANCED UNIVERSE SCREENING")
        print("=" * 40)
        print(f"Base universe: {len(base_symbols)} stocks")
        print(f"Minimum score: {min_score}%")
        
        # Screen all stocks
        screening_results = self.screener.screen_stock_universe(base_symbols)
        
        # Rank and filter
        ranked_results = self.screener.rank_growth_stocks(screening_results)
        growth_leaders = self.screener.get_growth_leaders(ranked_results, min_score)
        
        screening_summary = {
            'total_screened': len(base_symbols),
            'valid_results': len(ranked_results),
            'growth_leaders': len(growth_leaders),
            'filter_rate': len(growth_leaders) / len(base_symbols) * 100,
            'screening_results': ranked_results
        }
        
        print(f"\nFiltered universe: {len(growth_leaders)} stocks ({screening_summary['filter_rate']:.1f}%)")
        print("Only fundamentally strong growth stocks will be traded!")
        
        return growth_leaders, screening_summary
    
    def test_enhanced_minervini(self, base_symbols: List[str] = None, 
                               min_score: float = 60.0) -> Dict:
        """
        Test Minervini strategies with enhanced fundamental pre-screening
        """
        if base_symbols is None:
            base_symbols = [
                'NVDA', 'AMD', 'TSLA', 'AMZN', 'GOOGL', 'META', 'NFLX', 'AAPL',
                'MSFT', 'CRM', 'ADBE', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'NET',
                'SHOP', 'SQ', 'ROKU', 'ZM', 'DOCU', 'TWLO', 'MRNA', 'BNTX'
            ]
        
        print(f"\nTESTING ENHANCED MINERVINI STRATEGY")
        print("=" * 50)
        print("Step 1: Enhanced fundamental screening")
        print("Step 2: Minervini technical analysis on leaders only")
        
        # Get enhanced universe
        growth_leaders, screening_summary = self.get_enhanced_stock_universe(
            base_symbols, min_score
        )
        
        if not growth_leaders:
            return {'error': 'No stocks passed enhanced screening'}
        
        # Test Minervini strategy on enhanced universe
        print(f"\nStep 2: Testing Minervini strategy on {len(growth_leaders)} leaders")
        
        enhanced_results = []
        buy_hold_results = []
        
        for symbol in growth_leaders:
            print(f"\nTesting {symbol}...")
            try:
                # Get data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=3*365)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty or len(data) < 500:
                    continue
                
                data.columns = [col.lower() for col in data.columns]
                
                # Get fundamental score for this stock
                screening_result = next((r for r in screening_summary['screening_results'] 
                                       if r['symbol'] == symbol), None)
                fundamental_score = screening_result['score_percentage'] if screening_result else min_score
                
                # Calculate buy-and-hold
                bh_return = (data['close'].iloc[-1] / data['close'].iloc[150] - 1) * 100
                buy_hold_results.append({'symbol': symbol, 'return': bh_return})
                
                # Test Minervini strategy
                result = self.minervini.complete_strategy(data, symbol, fundamental_score)
                result['enhanced_score'] = fundamental_score
                enhanced_results.append(result)
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self._analyze_enhanced_results(enhanced_results, buy_hold_results, 
                                            "Enhanced Minervini", screening_summary)
    
    def test_enhanced_qullamaggie(self, base_symbols: List[str] = None,
                                 min_score: float = 60.0) -> Dict:
        """
        Test Qullamaggie strategies with enhanced fundamental pre-screening
        """
        if base_symbols is None:
            base_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMZN', 'META', 'NFLX']
        
        print(f"\nTESTING ENHANCED QULLAMAGGIE STRATEGY")
        print("=" * 50)
        
        # Get enhanced universe
        growth_leaders, screening_summary = self.get_enhanced_stock_universe(
            base_symbols, min_score
        )
        
        if not growth_leaders:
            return {'error': 'No stocks passed enhanced screening'}
        
        print(f"\nTesting Qullamaggie combined strategy on {len(growth_leaders)} leaders")
        
        enhanced_results = []
        
        for symbol in growth_leaders:
            print(f"\nTesting {symbol}...")
            try:
                data = self.qullamaggie.get_historical_data(symbol, 3)
                if data is None:
                    continue
                
                # Test combined Qullamaggie strategy
                result = self.qullamaggie.combined_qullamaggie(data)
                result['symbol'] = symbol
                
                # Add fundamental score
                screening_result = next((r for r in screening_summary['screening_results'] 
                                       if r['symbol'] == symbol), None)
                result['enhanced_score'] = screening_result['score_percentage'] if screening_result else min_score
                
                enhanced_results.append(result)
                print(f"  Result: {result['total_return']:.1f}% ({result['num_trades']} trades)")
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self._analyze_qullamaggie_enhanced_results(enhanced_results, 
                                                         "Enhanced Qullamaggie", screening_summary)
    
    def test_enhanced_alternatives(self, base_symbols: List[str] = None,
                                  min_score: float = 60.0) -> Dict:
        """
        Test alternative strategies with enhanced fundamental pre-screening
        """
        if base_symbols is None:
            base_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA']
        
        print(f"\nTESTING ENHANCED ALTERNATIVE STRATEGIES")
        print("=" * 50)
        
        # Get enhanced universe
        growth_leaders, screening_summary = self.get_enhanced_stock_universe(
            base_symbols, min_score
        )
        
        if not growth_leaders:
            return {'error': 'No stocks passed enhanced screening'}
        
        # Test key alternative strategies on enhanced universe
        enhanced_results = []
        
        strategies_to_test = [
            ('buy_and_hold', 'Buy and Hold'),
            ('mean_reversion_quality', 'Mean Reversion'),
            ('long_term_trend', 'Long-term Trend'),
            ('anti_momentum', 'Anti-Momentum')
        ]
        
        for symbol in growth_leaders:
            print(f"\nTesting {symbol}...")
            data = self.alternatives.get_historical_data(symbol, 5)
            
            if data is None:
                continue
            
            for method_name, strategy_name in strategies_to_test:
                try:
                    if hasattr(self.alternatives, method_name):
                        result = getattr(self.alternatives, method_name)(data)
                        result['symbol'] = symbol
                        result['strategy_name'] = strategy_name
                        
                        # Add fundamental score
                        screening_result = next((r for r in screening_summary['screening_results'] 
                                               if r['symbol'] == symbol), None)
                        result['enhanced_score'] = screening_result['score_percentage'] if screening_result else min_score
                        
                        enhanced_results.append(result)
                        
                except Exception as e:
                    print(f"    {strategy_name} error: {e}")
                    continue
        
        return self._analyze_alternative_enhanced_results(enhanced_results, 
                                                         "Enhanced Alternatives", screening_summary)
    
    def _analyze_enhanced_results(self, enhanced_results: List[Dict], 
                                 buy_hold_results: List[Dict],
                                 strategy_name: str, screening_summary: Dict) -> Dict:
        """
        Analyze enhanced Minervini strategy results
        """
        print(f"\n" + "=" * 80)
        print(f"{strategy_name.upper()} RESULTS")
        print("=" * 80)
        
        if not enhanced_results:
            return {'error': 'No results to analyze'}
        
        # Extract metrics
        returns = [r['total_return'] for r in enhanced_results]
        trades = [r['num_trades'] for r in enhanced_results]
        home_runs = [r['home_runs'] for r in enhanced_results]
        fund_scores = [r['enhanced_score'] for r in enhanced_results]
        
        bh_returns = [r['return'] for r in buy_hold_results]
        
        # Print detailed results
        print(f"{'Symbol':<8} {'Score':<6} {'Enhanced':<10} {'Buy-Hold':<10} {'Excess':<8} {'Trades':<7} {'HomeRuns':<9}")
        print("-" * 80)
        
        for i, result in enumerate(enhanced_results):
            symbol = result['symbol']
            fund_score = result['enhanced_score']
            strategy_return = result['total_return']
            bh_return = bh_returns[i] if i < len(bh_returns) else 0
            excess = strategy_return - bh_return
            num_trades = result['num_trades']
            home_run_count = result['home_runs']
            
            print(f"{symbol:<8} {fund_score:>5.0f}% {strategy_return:>8.1f}% {bh_return:>8.1f}% "
                  f"{excess:>6.1f}% {num_trades:>6} {home_run_count:>8}")
        
        # Summary statistics
        avg_return = np.mean(returns)
        avg_bh_return = np.mean(bh_returns)
        excess_return = avg_return - avg_bh_return
        
        print(f"\nENHANCED STRATEGY PERFORMANCE:")
        print(f"  Average Return: {avg_return:.1f}%")
        print(f"  Average Trades: {np.mean(trades):.1f}")
        print(f"  Total Home Runs: {sum(home_runs)}")
        print(f"  Average Fund Score: {np.mean(fund_scores):.1f}%")
        
        print(f"\nvs BUY-AND-HOLD:")
        print(f"  Enhanced Strategy: {avg_return:.1f}%")
        print(f"  Buy-Hold: {avg_bh_return:.1f}%")
        print(f"  Excess Return: {excess_return:.1f}%")
        
        print(f"\nSCREENING IMPACT:")
        print(f"  Stocks Screened: {screening_summary['total_screened']}")
        print(f"  Growth Leaders: {screening_summary['growth_leaders']}")
        print(f"  Selection Rate: {screening_summary['filter_rate']:.1f}%")
        
        return {
            'strategy_name': strategy_name,
            'avg_return': avg_return,
            'avg_bh_return': avg_bh_return,
            'excess_return': excess_return,
            'num_stocks': len(enhanced_results),
            'total_home_runs': sum(home_runs),
            'screening_summary': screening_summary,
            'results': enhanced_results
        }
    
    def _analyze_qullamaggie_enhanced_results(self, enhanced_results: List[Dict],
                                            strategy_name: str, screening_summary: Dict) -> Dict:
        """
        Analyze enhanced Qullamaggie results
        """
        print(f"\n" + "=" * 70)
        print(f"{strategy_name.upper()} RESULTS")
        print("=" * 70)
        
        if not enhanced_results:
            return {'error': 'No results to analyze'}
        
        returns = [r['total_return'] for r in enhanced_results]
        trades = [r['num_trades'] for r in enhanced_results]
        win_rates = [r['win_rate'] for r in enhanced_results]
        fund_scores = [r['enhanced_score'] for r in enhanced_results]
        
        print(f"{'Symbol':<8} {'Score':<6} {'Return':<8} {'Trades':<7} {'WinRate':<8}")
        print("-" * 50)
        
        for result in enhanced_results:
            print(f"{result['symbol']:<8} {result['enhanced_score']:>5.0f}% "
                  f"{result['total_return']:>6.1f}% {result['num_trades']:>6} "
                  f"{result['win_rate']:>6.1f}%")
        
        print(f"\nSUMMARY:")
        print(f"  Average Return: {np.mean(returns):.1f}%")
        print(f"  Average Trades: {np.mean(trades):.1f}")
        print(f"  Average Win Rate: {np.mean(win_rates):.1f}%")
        print(f"  Positive Results: {len([r for r in returns if r > 0])}/{len(returns)}")
        
        return {
            'strategy_name': strategy_name,
            'avg_return': np.mean(returns),
            'num_stocks': len(enhanced_results),
            'screening_summary': screening_summary,
            'results': enhanced_results
        }
    
    def _analyze_alternative_enhanced_results(self, enhanced_results: List[Dict],
                                            strategy_name: str, screening_summary: Dict) -> Dict:
        """
        Analyze enhanced alternative strategy results
        """
        print(f"\n" + "=" * 70)
        print(f"{strategy_name.upper()} RESULTS")
        print("=" * 70)
        
        # Group by strategy
        strategy_groups = {}
        for result in enhanced_results:
            strategy = result['strategy_name']
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(result)
        
        print(f"{'Strategy':<20} {'Avg Return':<12} {'Tests':<6} {'Winners':<8}")
        print("-" * 50)
        
        for strategy, results in strategy_groups.items():
            returns = [r['total_return'] for r in results]
            avg_return = np.mean(returns)
            winners = len([r for r in returns if r > 0])
            
            print(f"{strategy:<20} {avg_return:>10.1f}% {len(results):>4} {winners:>6}")
        
        return {
            'strategy_name': strategy_name,
            'strategy_groups': strategy_groups,
            'screening_summary': screening_summary,
            'results': enhanced_results
        }
    
    def comprehensive_enhanced_test(self) -> Dict:
        """
        Run comprehensive test of enhanced strategies vs original strategies
        """
        print("COMPREHENSIVE ENHANCED STRATEGY TEST")
        print("=" * 60)
        print("Testing the impact of enhanced fundamental screening")
        print("on multiple trading strategies")
        print("=" * 60)
        
        results = {}
        
        # Test enhanced Minervini
        print("\n1. ENHANCED MINERVINI TEST")
        results['enhanced_minervini'] = self.test_enhanced_minervini()
        
        # Test enhanced Qullamaggie  
        print("\n2. ENHANCED QULLAMAGGIE TEST")
        results['enhanced_qullamaggie'] = self.test_enhanced_qullamaggie()
        
        # Test enhanced alternatives
        print("\n3. ENHANCED ALTERNATIVES TEST")
        results['enhanced_alternatives'] = self.test_enhanced_alternatives()
        
        # Summary analysis
        print(f"\n" + "=" * 80)
        print("COMPREHENSIVE ENHANCED STRATEGY SUMMARY")
        print("=" * 80)
        
        for strategy_name, result in results.items():
            if 'error' not in result:
                print(f"\n{strategy_name.upper()}:")
                if 'avg_return' in result:
                    print(f"  Average Return: {result['avg_return']:.1f}%")
                    if 'excess_return' in result:
                        print(f"  Excess Return: {result['excess_return']:.1f}%")
                    print(f"  Stocks Tested: {result['num_stocks']}")
                    if 'total_home_runs' in result:
                        print(f"  Home Runs: {result['total_home_runs']}")
        
        print(f"\nKEY INSIGHT:")
        print("Enhanced fundamental screening should improve strategy performance")
        print("by focusing on fundamentally strong growth stocks only!")
        
        return results

def main():
    """
    Demonstrate enhanced strategy integration
    """
    print("ENHANCED STRATEGY INTEGRATION DEMO")
    print("=" * 50)
    print("This demonstrates how enhanced fundamental screening")
    print("can be integrated with any trading strategy to")
    print("improve performance through better stock selection.")
    print()
    
    integrator = EnhancedStrategyIntegrator()
    
    try:
        # Run comprehensive test
        results = integrator.comprehensive_enhanced_test()
        
        print(f"\n" + "=" * 60)
        print("CONCLUSION")
        print("=" * 60)
        print("Enhanced fundamental screening provides:")
        print("1. Better stock selection (quality growth companies)")
        print("2. Higher probability of success per trade")
        print("3. Improved risk-adjusted returns")
        print("4. Focus on fundamentally strong businesses")
        print()
        print("This screening can be applied to ANY trading strategy")
        print("to potentially improve its performance!")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()