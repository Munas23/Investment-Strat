import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from lumibot.entities import Asset
import logging

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)

class SPY200MAStrategy(Strategy):
    def initialize(self):
        self.sleeptime = "1D"
        self.spy = Asset(symbol="SPY", asset_type="stock")
        self.ma_period = 200
        self.in_position = False
        self.log_message("SPY 200MA strategy initialized.")

    def on_trading_iteration(self):
        # Get last 200 days of SPY data
        df = self.get_historical_prices(self.spy, self.ma_period, "day")
        if df is None or len(df.df) < self.ma_period:
            self.log_message("Not enough data for 200MA.")
            return

        close = df.df['close']
        ma200 = close.rolling(window=self.ma_period).mean()
        current_price = close.iloc[-1]
        current_ma200 = ma200.iloc[-1]

        # Check if we have a position
        position = self.get_position(self.spy)

        # Buy condition: price > 200MA and not in position
        if current_price > current_ma200 and position is None:
            cash = self.get_cash()
            shares = int(cash // current_price)
            if shares > 0:
                order = self.create_order(self.spy, shares, "buy")
                self.submit_order(order)
                self.log_message(f"BUY {shares} SPY at {current_price:.2f}")

        # Sell condition: price < 200MA and in position
        elif current_price < current_ma200 and position is not None:
            order = self.create_order(self.spy, position.quantity, "sell")
            self.submit_order(order)
            self.log_message(f"SELL {position.quantity} SPY at {current_price:.2f}")

def run_backtest():
    """Run the backtest using the correct Lumibot pattern"""
    try:
        # Strategy parameters
        backtesting_start = datetime(2018, 1, 1)  # Shorter period for faster testing
        backtesting_end = datetime(2023, 12, 31)
        
        print("Setting up backtest...")
        print(f"Period: {backtesting_start} to {backtesting_end}")
        print("Starting backtest...")
        print("This may take several minutes...")
        
        # Alternative approach: Create a custom YahooDataBacktesting class with proper fee structure
        class CustomYahooDataBacktesting(YahooDataBacktesting):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Set trading fees as a flat rate per trade instead of percentage
                self.min_fee = 1.0  # $1 minimum fee per trade
                self.max_fee = 10.0  # $10 maximum fee per trade
        
        # Run the backtest - CORRECT METHOD using class method
        results = SPY200MAStrategy.backtest(
            CustomYahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={},  # Strategy parameters if needed
            benchmark_asset="SPY"
        )
        
        return results
        
    except Exception as e:
        print(f"Error in backtest setup: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run the backtest using the correct Lumibot pattern
    try:
        print("Running 200day MA Pattern Strategy Backtest...")
        results = run_backtest()
        
        if results is not None:
            print("\n=== BACKTEST COMPLETED ===")
            print("Check the generated CSV file for detailed trade records")
            
            # Print results if available
            try:
                # Display basic results
                print("\nBacktest Results:")
                print(f"Results type: {type(results)}")
                
                # Try to access common result attributes
                if hasattr(results, 'portfolio_value'):
                    print(f"Final Portfolio Value: ${results.portfolio_value[-1]:,.2f}")
                
                if hasattr(results, 'get_stats'):
                    stats = results.get_stats()
                    print("Performance Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                        
            except Exception as e:
                print(f"Error displaying results: {e}")
                print("Backtest completed but couldn't display detailed results")
        else:
            print("Backtest failed to complete")
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        import traceback
        traceback.print_exc()