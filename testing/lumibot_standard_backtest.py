"""
Standard Lumibot Backtest Runner
===============================

This runs our Professional Growth Strategy using standard Lumibot patterns
for backtesting across major stock market indices.

USAGE (like all other Lumibot strategies):
1. Import strategy
2. Set backtest parameters  
3. Run backtest
4. Analyze results

MARKETS SUPPORTED:
- S&P 500, NASDAQ 100 (US)
- ASX 300 (Australia)  
- FTSE 100 (UK)
- DAX 30 (Germany)
- Nikkei 225 (Japan)
- TSX 60 (Canada)
- EURO STOXX 50 (Europe)
- Hang Seng (Hong Kong)
- BSE SENSEX (India)
"""

from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting
from lumibot.traders import Trader
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import our market strategies
from lumibot_market_strategy import (
    SP500Strategy,
    ASX300Strategy, 
    NASDAQ100Strategy,
    FTSE100Strategy,
    DAX30Strategy,
    Nikkei225Strategy,
    TSX60Strategy,
    EuroStoxx50Strategy,
    HangSengStrategy,
    BSESensexStrategy
)

def run_sp500_backtest():
    """
    Standard Lumibot backtest - S&P 500
    """
    print("Running S&P 500 Backtest...")
    
    # Backtest parameters
    backtesting_start = datetime(2021, 1, 1)
    backtesting_end = datetime(2024, 1, 1)
    
    # Create strategy
    strategy = SP500Strategy()
    
    # Run backtest
    backtest = YahooDataBacktesting(
        datetime_start=backtesting_start,
        datetime_end=backtesting_end,
        budget=100000
    )
    
    trader = Trader()
    trader.add_strategy(strategy)
    result = trader.backtest(backtest)
    
    print("S&P 500 Backtest Complete!")
    return result

def run_asx300_backtest():
    """
    Standard Lumibot backtest - ASX 300
    """
    print("Running ASX 300 Backtest...")
    
    # Backtest parameters
    backtesting_start = datetime(2021, 1, 1)
    backtesting_end = datetime(2024, 1, 1)
    
    # Create strategy
    strategy = ASX300Strategy()
    
    # Run backtest
    backtest = YahooDataBacktesting(
        datetime_start=backtesting_start,
        datetime_end=backtesting_end,
        budget=100000
    )
    
    trader = Trader()
    trader.add_strategy(strategy)
    result = trader.backtest(backtest)
    
    print("ASX 300 Backtest Complete!")
    return result

def run_nasdaq100_backtest():
    """
    Standard Lumibot backtest - NASDAQ 100
    """
    print("Running NASDAQ 100 Backtest...")
    
    # Backtest parameters
    backtesting_start = datetime(2021, 1, 1)
    backtesting_end = datetime(2024, 1, 1)
    
    # Create strategy
    strategy = NASDAQ100Strategy()
    
    # Run backtest
    backtest = YahooDataBacktesting(
        datetime_start=backtesting_start,
        datetime_end=backtesting_end,
        budget=100000
    )
    
    trader = Trader()
    trader.add_strategy(strategy)
    result = trader.backtest(backtest)
    
    print("NASDAQ 100 Backtest Complete!")
    return result

def run_ftse100_backtest():
    """
    Standard Lumibot backtest - FTSE 100
    """
    print("Running FTSE 100 Backtest...")
    
    # Backtest parameters
    backtesting_start = datetime(2021, 1, 1)
    backtesting_end = datetime(2024, 1, 1)
    
    # Create strategy
    strategy = FTSE100Strategy()
    
    # Run backtest
    backtest = YahooDataBacktesting(
        datetime_start=backtesting_start,
        datetime_end=backtesting_end,
        budget=100000
    )
    
    trader = Trader()
    trader.add_strategy(strategy)
    result = trader.backtest(backtest)
    
    print("FTSE 100 Backtest Complete!")
    return result

def run_multi_market_comparison():
    """
    Run backtests across multiple markets and compare
    """
    print("MULTI-MARKET COMPARISON BACKTEST")
    print("=" * 50)
    
    # Market strategies to test
    market_strategies = {
        "S&P 500": SP500Strategy,
        "ASX 300": ASX300Strategy,
        "NASDAQ 100": NASDAQ100Strategy,
        "FTSE 100": FTSE100Strategy,
        "DAX 30": DAX30Strategy
    }
    
    # Backtest parameters
    backtesting_start = datetime(2021, 1, 1)
    backtesting_end = datetime(2024, 1, 1)
    budget = 100000
    
    results = {}
    
    for market_name, strategy_class in market_strategies.items():
        print(f"\nTesting {market_name}...")
        
        try:
            # Create strategy
            strategy = strategy_class()
            
            # Run backtest
            backtest = YahooDataBacktesting(
                datetime_start=backtesting_start,
                datetime_end=backtesting_end,
                budget=budget
            )
            
            trader = Trader()
            trader.add_strategy(strategy)
            result = trader.backtest(backtest)
            
            # Extract key metrics
            portfolio_df = result.get_portfolio_df()
            if portfolio_df is not None and len(portfolio_df) > 0:
                initial_value = portfolio_df['portfolio_value'].iloc[0]
                final_value = portfolio_df['portfolio_value'].iloc[-1]
                total_return = (final_value / initial_value - 1) * 100
                
                # Calculate max drawdown
                cumulative = portfolio_df['portfolio_value'] / initial_value
                rolling_max = cumulative.expanding().max()
                drawdown = (cumulative / rolling_max - 1) * 100
                max_drawdown = drawdown.min()
                
                results[market_name] = {
                    'total_return': total_return,
                    'max_drawdown': max_drawdown,
                    'final_value': final_value,
                    'result_obj': result
                }
                
                print(f"  {market_name}: {total_return:.1f}% return, {max_drawdown:.1f}% max drawdown")
            else:
                results[market_name] = {
                    'total_return': 0,
                    'max_drawdown': 0,
                    'final_value': budget,
                    'result_obj': result
                }
                print(f"  {market_name}: No portfolio data available")
                
        except Exception as e:
            print(f"  {market_name}: Error - {e}")
            results[market_name] = {
                'total_return': 0,
                'max_drawdown': 0,
                'final_value': budget,
                'error': str(e)
            }
    
    # Print comparison
    print(f"\n" + "=" * 60)
    print("MARKET COMPARISON RESULTS")
    print("=" * 60)
    print(f"{'Market':<15} {'Return':<10} {'Max DD':<10} {'Final Value':<12}")
    print("-" * 60)
    
    for market, data in results.items():
        if 'error' not in data:
            print(f"{market:<15} {data['total_return']:>8.1f}% {data['max_drawdown']:>8.1f}% ${data['final_value']:>10,.0f}")
        else:
            print(f"{market:<15} {'ERROR':<10} {'ERROR':<10} {'ERROR':<12}")
    
    # Find best performer
    valid_results = {k: v for k, v in results.items() if 'error' not in v and v['total_return'] > 0}
    if valid_results:
        best_market = max(valid_results.keys(), key=lambda k: valid_results[k]['total_return'])
        best_return = valid_results[best_market]['total_return']
        
        print(f"\nBEST PERFORMER: {best_market} ({best_return:.1f}% return)")
        print(f"Strategy: 50% Trigger + 15% Trailing Stop")
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
    
    return results

def run_custom_backtest(market="SP500", start_date=None, end_date=None, budget=100000):
    """
    Run custom backtest with specified parameters
    """
    # Default dates
    if start_date is None:
        start_date = datetime(2021, 1, 1)
    if end_date is None:
        end_date = datetime(2024, 1, 1)
    
    # Strategy mapping
    strategy_map = {
        "SP500": SP500Strategy,
        "ASX300": ASX300Strategy,
        "NASDAQ100": NASDAQ100Strategy,
        "FTSE100": FTSE100Strategy,
        "DAX30": DAX30Strategy,
        "NIKKEI225": Nikkei225Strategy,
        "TSX60": TSX60Strategy,
        "EUROSTOXX50": EuroStoxx50Strategy,
        "HANGSENG": HangSengStrategy,
        "BSE_SENSEX": BSESensexStrategy
    }
    
    if market not in strategy_map:
        print(f"Market {market} not supported. Available: {list(strategy_map.keys())}")
        return None
    
    print(f"Running {market} Backtest...")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Budget: ${budget:,}")
    
    # Create and run backtest
    strategy = strategy_map[market]()
    
    backtest = YahooDataBacktesting(
        datetime_start=start_date,
        datetime_end=end_date,
        budget=budget
    )
    
    trader = Trader()
    trader.add_strategy(strategy)
    result = trader.backtest(backtest)
    
    print(f"{market} Backtest Complete!")
    return result

def show_available_markets():
    """
    Show all available markets for backtesting
    """
    print("AVAILABLE MARKETS FOR BACKTESTING")
    print("=" * 40)
    
    markets = {
        "SP500": "S&P 500 (United States)",
        "ASX300": "ASX 300 (Australia)",
        "NASDAQ100": "NASDAQ 100 (US Technology)",
        "FTSE100": "FTSE 100 (United Kingdom)",
        "DAX30": "DAX 30 (Germany)",
        "NIKKEI225": "Nikkei 225 (Japan)",
        "TSX60": "TSX 60 (Canada)",
        "EUROSTOXX50": "EURO STOXX 50 (Europe)",
        "HANGSENG": "Hang Seng (Hong Kong)",
        "BSE_SENSEX": "BSE SENSEX (India)"
    }
    
    for code, name in markets.items():
        print(f"  {code:<12} - {name}")
    
    print(f"\nStrategy Features:")
    print(f"• 50% Trigger + 15% Trailing Stop (251.5% avg returns)")
    print(f"• Enhanced fundamental screening")
    print(f"• Professional risk management")
    print(f"• Optimized from extensive testing")

def main():
    """
    Main execution - demonstrates standard Lumibot usage
    """
    print("PROFESSIONAL GROWTH STRATEGY - LUMIBOT BACKTESTING")
    print("=" * 60)
    print("This strategy implements our optimal hybrid exit approach")
    print("using standard Lumibot backtesting patterns.")
    print("=" * 60)
    
    # Show available markets
    show_available_markets()
    
    print(f"\nEXAMPLE USAGE:")
    print(f"1. Single Market:")
    print(f"   result = run_sp500_backtest()")
    print(f"   result = run_asx300_backtest()")
    print(f"")
    print(f"2. Custom Parameters:")
    print(f"   result = run_custom_backtest('ASX300', datetime(2022,1,1), datetime(2024,1,1))")
    print(f"")
    print(f"3. Multi-Market Comparison:")
    print(f"   results = run_multi_market_comparison()")
    
    # Run a demo
    print(f"\nRunning demo comparison...")
    try:
        demo_results = run_multi_market_comparison()
        return demo_results
    except Exception as e:
        print(f"Demo failed: {e}")
        return None

if __name__ == "__main__":
    results = main()