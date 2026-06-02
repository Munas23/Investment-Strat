
"""
Simple Lumibot Backtest Example
===============================
"""

from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting
from lumibot.traders import Trader
from datetime import datetime
from lumibot_hybrid_strategy import ProfessionalGrowthStrategy

def run_simple_backtest():
    """Run a simple backtest example"""
    
    print("SIMPLE BACKTEST EXAMPLE")
    print("=" * 30)
    
    # Create strategy
    strategy = ProfessionalGrowthStrategy()
    
    # Set test market
    strategy.set_test_market("TECHNOLOGY")
    
    # Configure backtest
    backtest = YahooDataBacktesting(
        datetime_start=datetime(2023, 1, 1),
        datetime_end=datetime(2024, 1, 1),
        budget=100000
    )
    
    # Run backtest
    trader = Trader()
    trader.add_strategy(strategy)
    
    print("Running backtest...")
    results = trader.backtest(backtest)
    
    print("Backtest complete!")
    print(f"Results: {results}")
    
    return results

if __name__ == "__main__":
    results = run_simple_backtest()
