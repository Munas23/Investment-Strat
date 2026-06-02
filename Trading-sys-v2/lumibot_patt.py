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

class FlagPatternStrategy(Strategy):
    """
    Flag Pattern Trading Strategy using Lumibot
    
    This strategy looks for stocks that have:
    1. A strong upward trend (flagpole)
    2. A consolidation period (flag)
    3. Breakout above the flag with volume confirmation
    4. Proper moving average alignment
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        # Set the minimum sleep time between iterations (in seconds)
        self.sleeptime = "1D"  # Check once per day
        
        # Strategy Configuration
        self.flagpole_period = 60        # How far back to look for trend (days)
        self.flagpole_min_gain = 0.15    # Minimum price increase required (15%)
        
        # Moving Averages
        self.ma_fast = 10               # Fast MA period
        self.ma_medium = 20            # Medium MA period
        self.ma_slow = 50             # Slow MA period
        
        # Consolidation/Volatility
        self.consolidation_window = 20                    # Days to check for consolidation
        self.consolidation_volatility_threshold = 0.6     # Maximum allowed volatility
        
        # Risk Management
        self.max_stop_loss = 0.08        # 8% stop loss
        self.min_stop_loss = 0.02        # 2% minimum stop
        self.max_position_size = 0.10    # 10% max position size per stock
        self.max_positions = 10          # Maximum number of positions
        
        # Get S&P 500 tickers (limit for faster backtesting)
        self.tickers = self.get_sp500_tickers()  # Limit to first 30 for faster backtesting
        
        # Performance tracking
        self.trades_log = []
        
        self.log_message("Strategy initialized successfully")
        
    def get_sp500_tickers(self):
        """Get S&P 500 tickers from Wikipedia"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            tickers = table['Symbol'].tolist()
            # Clean tickers - remove problematic ones
            clean_tickers = []
            for ticker in tickers:
                # Replace periods with dashes and filter out problematic symbols
                clean_ticker = ticker.replace('.', '-')
                if not ticker.startswith('$') and len(ticker) <= 5:
                    clean_tickers.append(clean_ticker)
            
            self.log_message(f"Fetched {len(clean_tickers)} S&P 500 tickers")
            return clean_tickers
        except Exception as e:
            self.log_message(f"Could not fetch S&P 500 tickers: {e}")
            # Fallback list of reliable tickers
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'V', 'PG',
                   'UNH', 'HD', 'MA', 'PFE', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX', 'CMCSA']
    
    def get_symbol_data(self, symbol, days_back=100):
        """Get historical data for a symbol using Lumibot's method"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            
            if bars is not None and hasattr(bars, 'df') and len(bars.df) > 0:
                return bars.df
            return None
        except Exception as e:
            self.log_message(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_moving_averages(self, df):
        """Calculate moving averages"""
        if len(df) < self.ma_slow:
            return None, None, None
            
        ma_fast = df['close'].rolling(window=self.ma_fast).mean()
        ma_medium = df['close'].rolling(window=self.ma_medium).mean()
        ma_slow = df['close'].rolling(window=self.ma_slow).mean()
        
        return ma_fast, ma_medium, ma_slow
    
    def check_flagpole_pattern(self, df):
        """Check if stock has a strong upward trend (flagpole)"""
        if len(df) < self.flagpole_period:
            return False, 0
            
        # Look for the highest high and lowest low in the flagpole period
        recent_data = df.tail(self.flagpole_period)
        high_max = recent_data['high'].max()
        low_min = recent_data['low'].min()
        
        # Calculate the gain over the flagpole period
        if low_min <= 0:
            return False, 0
            
        trend_gain = (high_max / low_min) - 1
        
        return trend_gain > self.flagpole_min_gain, trend_gain
    
    def check_consolidation(self, df):
        """Check if stock is in consolidation (low volatility)"""
        if len(df) < self.consolidation_window:
            return False
            
        recent_data = df.tail(self.consolidation_window)
        price_std = recent_data['close'].std()
        price_mean = recent_data['close'].mean()
        
        if price_mean <= 0:
            return False
            
        volatility_ratio = price_std / price_mean
        
        return volatility_ratio < self.consolidation_volatility_threshold
    
    def check_volume_confirmation(self, df):
        """Check if current volume is above average"""
        if len(df) < self.consolidation_window:
            return False
            
        recent_data = df.tail(self.consolidation_window)
        volume_avg = recent_data['volume'].mean()
        current_volume = df['volume'].iloc[-1]
        
        return current_volume > volume_avg * 1.2  # Require 20% above average
    
    def check_ma_alignment(self, ma_fast, ma_medium, ma_slow):
        """Check if moving averages are properly aligned"""
        if ma_fast is None or ma_medium is None or ma_slow is None:
            return False
            
        if len(ma_fast) == 0 or len(ma_medium) == 0 or len(ma_slow) == 0:
            return False
            
        latest_fast = ma_fast.iloc[-1]
        latest_medium = ma_medium.iloc[-1]
        latest_slow = ma_slow.iloc[-1]
        
        # Check for NaN values
        if pd.isna(latest_fast) or pd.isna(latest_medium) or pd.isna(latest_slow):
            return False
        
        # Check if MAs are aligned (fast > medium > slow) with some tolerance
        ma_aligned = (latest_fast > latest_medium * 0.99 and 
                     latest_medium > latest_slow * 0.99)
        
        return ma_aligned
    
    def check_entry_conditions(self, symbol, df):
        """Check all entry conditions for a symbol"""
        try:
            if len(df) < self.ma_slow:
                return False, "Insufficient data"
                
            current_price = df['close'].iloc[-1]
            
            if pd.isna(current_price) or current_price <= 0:
                return False, "Invalid price data"
            
            # 1. Check flagpole pattern
            has_flagpole, trend_gain = self.check_flagpole_pattern(df)
            if not has_flagpole:
                return False, "No flagpole pattern"
            
            # 2. Calculate moving averages
            ma_fast, ma_medium, ma_slow = self.calculate_moving_averages(df)
            if ma_fast is None:
                return False, "Insufficient data for MAs"
            
            # 3. Check MA alignment
            if not self.check_ma_alignment(ma_fast, ma_medium, ma_slow):
                return False, "MAs not aligned"
            
            # 4. Check if price is above fast MA (trend confirmation)
            latest_ma_fast = ma_fast.iloc[-1]
            if pd.isna(latest_ma_fast) or current_price < latest_ma_fast:
                return False, "Price below fast MA"
            
            # 5. Check consolidation
            if not self.check_consolidation(df):
                return False, "Not in consolidation"
            
            # 6. Check volume confirmation
            if not self.check_volume_confirmation(df):
                return False, "No volume confirmation"
            
            return True, f"All conditions met. Trend gain: {trend_gain:.2%}"
            
        except Exception as e:
            return False, f"Error checking conditions: {e}"
    
    def calculate_position_size(self, price):
        """Calculate position size based on available cash and risk management"""
        try:
            cash = self.get_cash()
            max_position_value = cash * self.max_position_size
            shares = int(max_position_value / price)
            return max(shares, 0)  # At least 0 shares
        except:
            return 0
    
    def on_trading_iteration(self):
        """Main trading logic executed on each iteration"""
        try:
            # Get current date
            current_date = self.get_datetime()
            
            # Get current positions
            positions = self.get_positions()
            current_positions = len(positions)
            
            self.log_message(f"Date: {current_date.date()}, Current positions: {current_positions}")
            
            # Check exit conditions for existing positions
            self.check_exit_conditions()
            
            # Look for new entries if we have room for more positions
            if current_positions < self.max_positions:
                self.look_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_exit_conditions(self):
        """Check exit conditions for all current positions"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None or current_price <= 0:
                    continue
                
                # Get recent data for MA calculation
                df = self.get_symbol_data(symbol, days_back=60)
                if df is None or len(df) < self.ma_medium:
                    continue
                
                # Calculate medium MA for exit signal
                ma_medium = df['close'].rolling(window=self.ma_medium).mean().iloc[-1]
                
                if pd.isna(ma_medium):
                    continue
                
                # Exit condition: price falls below medium MA
                if current_price < ma_medium * 0.98:  # 2% buffer
                    self.log_message(f"Selling {symbol}: Price {current_price:.2f} below MA {ma_medium:.2f}")
                    
                    # Create sell order
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    # Log the trade
                    self.log_trade(symbol, "sell", current_price, position.quantity, "MA exit")
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def look_for_entries(self):
        """Look for new entry opportunities"""
        entries_found = 0
        
        for symbol in self.tickers:
            try:
                # Skip if we already have a position
                existing_position = None
                for pos in self.get_positions():
                    if pos.asset.symbol == symbol:
                        existing_position = pos
                        break
                
                if existing_position is not None:
                    continue
                
                # Get historical data
                df = self.get_symbol_data(symbol, days_back=100)
                if df is None or len(df) < self.ma_slow:
                    continue
                
                # Check entry conditions
                should_enter, reason = self.check_entry_conditions(symbol, df)
                
                if should_enter:
                    current_price = df['close'].iloc[-1]
                    quantity = self.calculate_position_size(current_price)
                    
                    if quantity > 0:
                        try:
                            # Create and submit buy order
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, quantity, "buy")
                            self.submit_order(order)
                            
                            self.log_message(f"Buying {symbol}: {quantity} shares at ${current_price:.2f}. Reason: {reason}")
                            
                            # Log the trade
                            self.log_trade(symbol, "buy", current_price, quantity, reason)
                            
                            entries_found += 1
                            
                            # Limit entries per iteration to avoid overloading
                            if entries_found >= 2:
                                break
                                
                        except Exception as e:
                            self.log_message(f"Error submitting order for {symbol}: {e}")
                            
            except Exception as e:
                self.log_message(f"Error checking entry for {symbol}: {e}")
                continue
        
        if entries_found == 0:
            self.log_message("No new entry opportunities found")
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trade details"""
        trade_data = {
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason
        }
        self.trades_log.append(trade_data)
    
    def on_strategy_end(self):
        """Called when strategy ends"""
        self.log_message("Strategy ended")
        self.export_trades_to_csv()
        self.print_performance_summary()
    
    def export_trades_to_csv(self):
        """Export all trades to CSV"""
        if not self.trades_log:
            self.log_message("No trades to export")
            return
        
        try:
            df = pd.DataFrame(self.trades_log)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lumibot_trades_{timestamp}.csv"
            df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(df)} trades to {filename}")
        except Exception as e:
            self.log_message(f"Error exporting trades: {e}")
    
    def print_performance_summary(self):
        """Print a summary of strategy performance"""
        try:
            positions = self.get_positions()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            
            self.log_message("=== STRATEGY PERFORMANCE SUMMARY ===")
            self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
            self.log_message(f"Cash: ${cash:,.2f}")
            self.log_message(f"Active Positions: {len(positions)}")
            self.log_message(f"Total Trades: {len(self.trades_log)}")
            
            if self.trades_log:
                trades_df = pd.DataFrame(self.trades_log)
                buy_trades = trades_df[trades_df['action'] == 'buy']
                sell_trades = trades_df[trades_df['action'] == 'sell']
                
                self.log_message(f"Buy Orders: {len(buy_trades)}")
                self.log_message(f"Sell Orders: {len(sell_trades)}")
                
                if len(buy_trades) > 0:
                    total_invested = buy_trades['value'].sum()
                    self.log_message(f"Total Amount Invested: ${total_invested:,.2f}")
                
                if len(sell_trades) > 0:
                    total_sold = sell_trades['value'].sum()
                    self.log_message(f"Total Amount from Sales: ${total_sold:,.2f}")
            
        except Exception as e:
            self.log_message(f"Error printing performance summary: {e}")


def run_backtest():
    """Run the backtest using the correct Lumibot pattern"""
    try:
        # Strategy parameters
        backtesting_start = datetime(2020, 1, 1)  # Shorter period for faster testing
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
        results = FlagPatternStrategy.backtest(
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
        print("Running Flag Pattern Strategy Backtest...")
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