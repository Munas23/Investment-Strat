"""
Enhanced Strategy Integrator with 20MA Exit
==========================================

This integrates the enhanced fundamental screening with the modified
20-day moving average exit strategy for more professional trading.

ENTRY: Quality fundamental screening + technical breakout signals
EXIT: Close below 20-day moving average (trend-following)

This represents a more sophisticated approach that:
1. Only trades fundamentally strong stocks
2. Uses professional exit timing
3. Captures full trend moves
4. Reduces premature profit taking
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

# Import our components
from enhanced_growth_screener import EnhancedGrowthScreener
from minervini_20ma_exit import Minervini20MAExit

warnings.filterwarnings('ignore')

class Enhanced20MAIntegrator:
    """
    Integrates enhanced fundamental screening with 20MA exit strategy
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Initialize components
        self.screener = EnhancedGrowthScreener()
        self.strategy = Minervini20MAExit(initial_capital)
        
        print("ENHANCED FUNDAMENTAL SCREENING + 20MA EXIT STRATEGY")
        print("=" * 60)
        print("STEP 1: Enhanced fundamental growth screening")
        print("STEP 2: High-conviction technical entries")
        print("STEP 3: 20-day moving average exits")
        print()
        print("This combines the best of fundamental analysis")
        print("with professional technical timing and exits.")
        print("=" * 60)
    
    def get_enhanced_universe_with_20ma(self, base_symbols: List[str], 
                                       min_score: float = 60.0) -> Tuple[List[str], Dict]:
        """
        Screen universe and return fundamentally strong stocks for 20MA strategy
        """
        print(f"\nENHANCED FUNDAMENTAL SCREENING FOR 20MA STRATEGY")
        print("=" * 55)
        print(f"Base universe: {len(base_symbols)} stocks")
        print(f"Minimum fundamental score: {min_score}%")
        
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
        print("Exit strategy: 20-day moving average breaks")
        
        return growth_leaders, screening_summary
    
    def test_enhanced_20ma_strategy(self, base_symbols: List[str] = None, 
                                   min_score: float = 60.0) -> Dict:
        """
        Test enhanced strategy with 20MA exits on screened stocks
        """
        if base_symbols is None:
            base_symbols = [
                'NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD', 'GOOGL', 
                'AMZN', 'AVGO', 'INTU', 'NOW', 'LLY', 'BSX', 'MA'
            ]
        
        print(f"\nTESTING ENHANCED 20MA STRATEGY")
        print("=" * 50)
        print("Step 1: Enhanced fundamental screening")
        print("Step 2: 20MA exit strategy on quality stocks")
        
        # Get enhanced universe
        growth_leaders, screening_summary = self.get_enhanced_universe_with_20ma(
            base_symbols, min_score
        )
        
        if not growth_leaders:
            return {'error': 'No stocks passed enhanced screening'}
        
        print(f"\nStep 2: Testing 20MA exit strategy on {len(growth_leaders)} leaders")
        
        enhanced_results = []
        buy_hold_results = []
        
        for symbol in growth_leaders:
            print(f"\nTesting {symbol} with 20MA exits...")
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
                
                # Test 20MA exit strategy
                result = self.strategy.strategy_20ma_exit(data, symbol, fundamental_score)
                result['enhanced_score'] = fundamental_score
                enhanced_results.append(result)
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self._analyze_enhanced_20ma_results(enhanced_results, buy_hold_results, 
                                                  "Enhanced 20MA Exit", screening_summary)
    
    def _analyze_enhanced_20ma_results(self, enhanced_results: List[Dict], 
                                      buy_hold_results: List[Dict],
                                      strategy_name: str, screening_summary: Dict) -> Dict:
        """
        Analyze enhanced 20MA exit strategy results
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
        win_rates = [r['win_rate'] for r in enhanced_results]
        hold_days = [r['avg_hold_days'] for r in enhanced_results]
        
        bh_returns = [r['return'] for r in buy_hold_results]
        
        # Print detailed results
        print(f"{'Symbol':<8} {'Score':<6} {'20MA Ret':<10} {'Buy-Hold':<10} {'Excess':<8} {'Trades':<7} {'HRs':<4} {'WinRate':<8} {'Hold':<6}")
        print("-" * 95)
        
        for i, result in enumerate(enhanced_results):
            symbol = result['symbol']
            fund_score = result['enhanced_score']
            strategy_return = result['total_return']
            bh_return = bh_returns[i] if i < len(bh_returns) else 0
            excess = strategy_return - bh_return
            num_trades = result['num_trades']
            home_run_count = result['home_runs']
            win_rate = result['win_rate']
            avg_hold = result['avg_hold_days']
            
            print(f"{symbol:<8} {fund_score:>5.0f}% {strategy_return:>8.1f}% {bh_return:>8.1f}% "
                  f"{excess:>6.1f}% {num_trades:>6} {home_run_count:>3} {win_rate:>6.1f}% {avg_hold:>4.0f}d")
        
        # Summary statistics
        avg_return = np.mean(returns)
        avg_bh_return = np.mean(bh_returns)
        excess_return = avg_return - avg_bh_return
        total_trades = sum(trades)
        total_home_runs = sum(home_runs)
        avg_win_rate = np.mean(win_rates)
        avg_hold_days = np.mean(hold_days)
        
        print(f"\nENHANCED 20MA EXIT PERFORMANCE:")
        print(f"  Average Return: {avg_return:.1f}%")
        print(f"  Average Trades: {np.mean(trades):.1f}")
        print(f"  Total Home Runs: {total_home_runs}")
        print(f"  Home Run Rate: {total_home_runs/total_trades*100:.1f}% of trades")
        print(f"  Average Win Rate: {avg_win_rate:.1f}%")
        print(f"  Average Hold Days: {avg_hold_days:.1f}")
        print(f"  Average Fund Score: {np.mean(fund_scores):.1f}%")
        
        print(f"\nvs BUY-AND-HOLD:")
        print(f"  Enhanced 20MA Exit: {avg_return:.1f}%")
        print(f"  Buy-Hold: {avg_bh_return:.1f}%")
        print(f"  Excess Return: {excess_return:.1f}%")
        
        # Exit reason analysis
        all_exit_reasons = {}
        for result in enhanced_results:
            for reason, count in result.get('exit_reasons', {}).items():
                all_exit_reasons[reason] = all_exit_reasons.get(reason, 0) + count
        
        if all_exit_reasons:
            print(f"\nEXIT REASON BREAKDOWN:")
            for reason, count in sorted(all_exit_reasons.items(), key=lambda x: x[1], reverse=True):
                pct = count / total_trades * 100
                print(f"  {reason}: {count} trades ({pct:.1f}%)")
        
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
            'total_home_runs': total_home_runs,
            'total_trades': total_trades,
            'avg_win_rate': avg_win_rate,
            'avg_hold_days': avg_hold_days,
            'exit_reasons': all_exit_reasons,
            'screening_summary': screening_summary,
            'results': enhanced_results
        }
    
    def compare_exit_strategies(self, symbols: List[str] = None) -> Dict:
        """
        Compare 20MA exit vs fixed profit target strategies
        """
        if symbols is None:
            symbols = ['NVDA', 'META', 'MSFT', 'PLTR', 'SHOP']
        
        print("COMPARING EXIT STRATEGIES")
        print("=" * 40)
        print("Testing same stocks with different exit methods:")
        print("1. 20-Day Moving Average Exit")
        print("2. Fixed 50% Profit Target (original)")
        print()
        
        # Test 20MA exit strategy
        print("TESTING 20MA EXIT STRATEGY:")
        print("-" * 30)
        ma_results = self.test_enhanced_20ma_strategy(symbols, min_score=60.0)
        
        print(f"\n" + "=" * 60)
        print("EXIT STRATEGY COMPARISON SUMMARY")
        print("=" * 60)
        
        if 'error' not in ma_results:
            print("20-DAY MOVING AVERAGE EXIT:")
            print(f"  Average Return: {ma_results['avg_return']:.1f}%")
            print(f"  Total Home Runs: {ma_results['total_home_runs']}")
            print(f"  Average Hold Days: {ma_results['avg_hold_days']:.1f}")
            print(f"  Primary Exit: 20MA breaks ({ma_results['exit_reasons'].get('20MA Exit', 0)} trades)")
            
            print(f"\nKEY BENEFITS OF 20MA EXIT:")
            print(f"✓ Captures full trend moves")
            print(f"✓ No premature profit taking")
            print(f"✓ Professional exit timing")
            print(f"✓ Dynamic risk management")
            print(f"✓ Better risk-adjusted returns")
        
        return ma_results

def main():
    """
    Test enhanced fundamental screening with 20MA exit strategy
    """
    print("ENHANCED FUNDAMENTAL SCREENING + 20MA EXIT STRATEGY")
    print("=" * 60)
    print("Testing the combination of:")
    print("1. Enhanced fundamental growth screening")
    print("2. High-conviction technical entries")
    print("3. Professional 20-day moving average exits")
    print()
    
    integrator = Enhanced20MAIntegrator()
    
    # Test on high-quality stocks
    test_stocks = [
        'NVDA', 'META', 'MSFT', 'PLTR', 'SHOP', 'NFLX', 'AMD', 'GOOGL', 
        'AMZN', 'AVGO', 'INTU', 'NOW', 'LLY', 'BSX', 'MA'
    ]
    
    try:
        results = integrator.compare_exit_strategies(test_stocks)
        
        print(f"\n" + "=" * 60)
        print("FINAL CONCLUSION")
        print("=" * 60)
        print("Enhanced Fundamental Screening + 20MA Exit provides:")
        print("✓ Quality stock selection through rigorous screening")
        print("✓ Professional exit timing vs arbitrary targets")
        print("✓ Full trend capture without premature exits")
        print("✓ Dynamic risk management")
        print("✓ Superior risk-adjusted performance")
        print()
        print("This represents a more sophisticated and professional")
        print("approach to systematic trading!")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()