"""
Comprehensive Strategy Testing Framework
Tests 20 different trading strategies over 5 years to find what works best
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
import warnings
from technical_indicators import StrategyConditions
from multi_market_risk_manager import MultiMarketRiskManager
from market_config import MAJOR_MARKETS

warnings.filterwarnings('ignore')

class StrategyTester:
    """Comprehensive strategy testing framework"""
    
    def __init__(self, initial_capital: float = 100000, test_period_years: int = 5):
        self.initial_capital = initial_capital
        self.test_period_years = test_period_years
        
        # Define all 20 strategies
        self.strategies = {
            1: {"name": "Golden Cross", "method": "golden_cross"},
            2: {"name": "Fast MA Cross", "method": "fast_ma_cross"},
            3: {"name": "Triple MA Alignment", "method": "triple_ma_alignment"},
            4: {"name": "EMA Cross", "method": "ema_cross"},
            5: {"name": "Strong Momentum (40%/60d)", "method": "strong_momentum"},
            6: {"name": "Moderate Momentum (10%/20d)", "method": "moderate_momentum"},
            7: {"name": "Momentum + MA Confirmation", "method": "momentum_ma_confirmation"},
            8: {"name": "Acceleration Pattern", "method": "acceleration_pattern"},
            9: {"name": "Volume Breakout", "method": "volume_breakout"},
            10: {"name": "Volatility Breakout", "method": "volatility_breakout"},
            11: {"name": "Range Breakout", "method": "range_breakout"},
            12: {"name": "Gap Up Follow Through", "method": "gap_up_follow_through"},
            13: {"name": "RSI Recovery", "method": "rsi_recovery"},
            14: {"name": "MACD Bullish Cross", "method": "macd_bullish_cross"},
            15: {"name": "Bollinger Squeeze", "method": "bollinger_squeeze"},
            16: {"name": "Stochastic Recovery", "method": "stochastic_oversold_recovery"},
            17: {"name": "Pullback Entry", "method": "pullback_entry"},
            18: {"name": "Cup and Handle", "method": "cup_and_handle"},
            19: {"name": "Higher Highs/Lows", "method": "higher_highs_lows_trend"},
            20: {"name": "Support/Resistance Breakout", "method": "support_resistance_breakout"}
        }
        
        # Test universe - reliable tickers from multiple markets
        self.test_universe = [
            # US Stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
            # ASX Stocks
            'CBA.AX', 'BHP.AX', 'WBC.AX', 'ANZ.AX', 'CSL.AX',
            # UK Stocks  
            'SHEL.L', 'AZN.L', 'ULVR.L',
            # German Stocks
            'SAP.DE', 'SIE.DE'
        ]
        
        self.results = {}
        
    def get_historical_data(self, symbol: str, years: int = 5) -> Optional[pd.DataFrame]:
        """Get historical data for a symbol"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365 + 100)  # Extra buffer for indicators
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 252:  # Need at least 1 year of data
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            return data
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def test_single_strategy(self, strategy_id: int, symbol: str, data: pd.DataFrame) -> Dict:
        """Test a single strategy on a single stock"""
        try:
            # Get strategy info
            strategy_info = self.strategies[strategy_id]
            strategy_method = strategy_info["method"]
            
            # Create strategy conditions object
            conditions = StrategyConditions(data.copy())
            
            # Get buy signals
            if hasattr(conditions, strategy_method):
                buy_signals = getattr(conditions, strategy_method)()
            else:
                return {"error": f"Method {strategy_method} not found"}
            
            # Simulate trading
            positions = []
            cash = self.initial_capital
            shares = 0
            position_value = 0
            
            # Track trades
            trades = []
            
            for i, (date, signal) in enumerate(buy_signals.items()):
                if i < 200:  # Skip first 200 days for indicator warmup
                    continue
                    
                current_price = data.loc[date, 'close']
                
                # Exit logic: sell if price drops 8% from entry or signal turns off
                if shares > 0:
                    position_value = shares * current_price
                    
                    # Check stop loss (8% down from entry)
                    if len(trades) > 0:
                        entry_price = trades[-1]['entry_price']
                        if current_price < entry_price * 0.92:  # 8% stop loss
                            # Sell position
                            cash = shares * current_price
                            exit_return = (current_price / entry_price - 1) * 100
                            trades[-1]['exit_price'] = current_price
                            trades[-1]['exit_date'] = date
                            trades[-1]['return_pct'] = exit_return
                            trades[-1]['hold_days'] = (date - trades[-1]['entry_date']).days
                            shares = 0
                            continue
                
                # Entry logic: buy when signal is true and we don't have position
                if signal and shares == 0 and not pd.isna(current_price):
                    # Calculate position size (risk 2% of capital)
                    risk_amount = cash * 0.02
                    stop_loss_price = current_price * 0.92  # 8% stop
                    risk_per_share = current_price - stop_loss_price
                    
                    if risk_per_share > 0:
                        shares_to_buy = min(int(risk_amount / risk_per_share), int(cash / current_price))
                        
                        if shares_to_buy > 0:
                            shares = shares_to_buy
                            cost = shares * current_price
                            cash -= cost
                            
                            # Record trade
                            trades.append({
                                'entry_date': date,
                                'entry_price': current_price,
                                'shares': shares,
                                'cost': cost,
                                'exit_price': None,
                                'exit_date': None,
                                'return_pct': None,
                                'hold_days': None
                            })
            
            # Close any remaining position at the end
            if shares > 0 and len(trades) > 0 and trades[-1]['exit_price'] is None:
                final_price = data['close'].iloc[-1]
                cash = shares * final_price
                entry_price = trades[-1]['entry_price']
                exit_return = (final_price / entry_price - 1) * 100
                trades[-1]['exit_price'] = final_price
                trades[-1]['exit_date'] = data.index[-1]
                trades[-1]['return_pct'] = exit_return
                trades[-1]['hold_days'] = (data.index[-1] - trades[-1]['entry_date']).days
                shares = 0
            
            # Calculate performance metrics
            final_value = cash + (shares * data['close'].iloc[-1] if shares > 0 else 0)
            total_return = (final_value / self.initial_capital - 1) * 100
            
            # Calculate trade statistics
            completed_trades = [t for t in trades if t['return_pct'] is not None]
            
            if completed_trades:
                returns = [t['return_pct'] for t in completed_trades]
                win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
                avg_return = np.mean(returns)
                avg_win = np.mean([r for r in returns if r > 0]) if len([r for r in returns if r > 0]) > 0 else 0
                avg_loss = np.mean([r for r in returns if r < 0]) if len([r for r in returns if r < 0]) > 0 else 0
                max_win = max(returns) if returns else 0
                max_loss = min(returns) if returns else 0
                avg_hold_days = np.mean([t['hold_days'] for t in completed_trades])
            else:
                win_rate = avg_return = avg_win = avg_loss = max_win = max_loss = avg_hold_days = 0
            
            return {
                'symbol': symbol,
                'strategy_id': strategy_id,
                'strategy_name': strategy_info['name'],
                'total_return': total_return,
                'final_value': final_value,
                'num_trades': len(completed_trades),
                'win_rate': win_rate,
                'avg_return_per_trade': avg_return,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'max_win': max_win,
                'max_loss': max_loss,
                'avg_hold_days': avg_hold_days,
                'trades': completed_trades
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'strategy_id': strategy_id,
                'error': str(e)
            }
    
    def run_comprehensive_test(self, max_stocks: int = 10) -> Dict:
        """Run all 20 strategies across multiple stocks"""
        print("COMPREHENSIVE STRATEGY TESTING FRAMEWORK")
        print("=" * 50)
        print(f"Testing {len(self.strategies)} strategies across {max_stocks} stocks")
        print(f"Test period: {self.test_period_years} years")
        print(f"Initial capital: ${self.initial_capital:,}")
        print()
        
        # Get data for test universe
        print("Fetching historical data...")
        stock_data = {}
        valid_stocks = []
        
        for i, symbol in enumerate(self.test_universe[:max_stocks]):
            print(f"  Loading {symbol}... ({i+1}/{max_stocks})")
            data = self.get_historical_data(symbol, self.test_period_years)
            if data is not None:
                stock_data[symbol] = data
                valid_stocks.append(symbol)
            time.sleep(0.1)  # Rate limiting
        
        print(f"Loaded data for {len(valid_stocks)} stocks: {valid_stocks}")
        print()
        
        # Test all strategies
        all_results = []
        total_tests = len(self.strategies) * len(valid_stocks)
        test_count = 0
        
        print("Running strategy tests...")
        for strategy_id, strategy_info in self.strategies.items():
            print(f"\nTesting Strategy {strategy_id}: {strategy_info['name']}")
            strategy_results = []
            
            for symbol in valid_stocks:
                test_count += 1
                progress = (test_count / total_tests) * 100
                print(f"  {symbol} ({progress:.1f}% complete)")
                
                result = self.test_single_strategy(strategy_id, symbol, stock_data[symbol])
                if 'error' not in result:
                    strategy_results.append(result)
                    all_results.append(result)
            
            # Calculate strategy summary
            if strategy_results:
                avg_return = np.mean([r['total_return'] for r in strategy_results])
                avg_trades = np.mean([r['num_trades'] for r in strategy_results])
                avg_win_rate = np.mean([r['win_rate'] for r in strategy_results])
                
                print(f"    Strategy Summary: {avg_return:.1f}% avg return, {avg_trades:.1f} avg trades, {avg_win_rate:.1f}% win rate")
        
        return self.analyze_results(all_results)
    
    def analyze_results(self, all_results: List[Dict]) -> Dict:
        """Analyze and rank all strategy results"""
        print("\n" + "=" * 50)
        print("ANALYZING RESULTS")
        print("=" * 50)
        
        # Group by strategy
        strategy_summary = {}
        for result in all_results:
            strategy_id = result['strategy_id']
            strategy_name = result['strategy_name']
            
            if strategy_id not in strategy_summary:
                strategy_summary[strategy_id] = {
                    'name': strategy_name,
                    'results': [],
                    'avg_return': 0,
                    'avg_trades': 0,
                    'avg_win_rate': 0,
                    'consistency': 0,
                    'total_tests': 0
                }
            
            strategy_summary[strategy_id]['results'].append(result)
        
        # Calculate summary statistics
        for strategy_id, summary in strategy_summary.items():
            results = summary['results']
            returns = [r['total_return'] for r in results]
            
            summary['avg_return'] = np.mean(returns)
            summary['median_return'] = np.median(returns)
            summary['return_std'] = np.std(returns)
            summary['avg_trades'] = np.mean([r['num_trades'] for r in results])
            summary['avg_win_rate'] = np.mean([r['win_rate'] for r in results])
            summary['consistency'] = len([r for r in returns if r > 0]) / len(returns) * 100
            summary['total_tests'] = len(results)
            summary['sharpe_ratio'] = summary['avg_return'] / summary['return_std'] if summary['return_std'] > 0 else 0
        
        return strategy_summary
    
    def print_rankings(self, strategy_summary: Dict):
        """Print strategy rankings"""
        print("\n" + "=" * 70)
        print("STRATEGY RANKINGS")
        print("=" * 70)
        
        # Sort by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        print(f"{'Rank':<4} {'Strategy':<25} {'Avg Return':<12} {'Win Rate':<10} {'Trades':<8} {'Consistency':<12} {'Sharpe':<8}")
        print("-" * 70)
        
        for rank, (strategy_id, summary) in enumerate(sorted_strategies, 1):
            print(f"{rank:<4} {summary['name']:<25} {summary['avg_return']:>10.1f}% "
                  f"{summary['avg_win_rate']:>8.1f}% {summary['avg_trades']:>6.1f} "
                  f"{summary['consistency']:>10.1f}% {summary['sharpe_ratio']:>6.2f}")
        
        # Top 5 detailed analysis
        print("\n" + "=" * 70)
        print("TOP 5 STRATEGIES - DETAILED ANALYSIS")
        print("=" * 70)
        
        for rank, (strategy_id, summary) in enumerate(sorted_strategies[:5], 1):
            print(f"\n{rank}. {summary['name']}")
            print(f"   Average Return: {summary['avg_return']:.1f}% (Median: {summary['median_return']:.1f}%)")
            print(f"   Standard Deviation: {summary['return_std']:.1f}%")
            print(f"   Average Trades: {summary['avg_trades']:.1f}")
            print(f"   Win Rate: {summary['avg_win_rate']:.1f}%")
            print(f"   Consistency: {summary['consistency']:.1f}% (stocks with positive returns)")
            print(f"   Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
            print(f"   Tests Completed: {summary['total_tests']}")
        
        # Bottom 5
        print("\n" + "=" * 70)
        print("BOTTOM 5 STRATEGIES")
        print("=" * 70)
        
        for rank, (strategy_id, summary) in enumerate(sorted_strategies[-5:], len(sorted_strategies)-4):
            print(f"{rank}. {summary['name']}: {summary['avg_return']:.1f}% avg return")


def main():
    """Main testing function"""
    print("STRATEGY TESTING FRAMEWORK")
    print("Testing 20 different trading strategies over 5 years")
    print()
    
    # Create tester
    tester = StrategyTester(initial_capital=100000, test_period_years=5)
    
    # Run comprehensive test
    try:
        strategy_summary = tester.run_comprehensive_test(max_stocks=8)  # Test with 8 stocks for speed
        tester.print_rankings(strategy_summary)
        
        print("\n" + "=" * 70)
        print("TESTING COMPLETED!")
        print("=" * 70)
        print("Key Insights:")
        print("- Strategies are ranked by average return across all tested stocks")
        print("- Win Rate shows percentage of profitable trades")
        print("- Consistency shows percentage of stocks with positive returns")
        print("- Sharpe Ratio measures risk-adjusted returns")
        print("\nUse the top-performing strategies for your trading!")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()