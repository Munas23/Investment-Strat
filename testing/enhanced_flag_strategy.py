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
from risk_manager import RiskManager

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

class EnhancedFlagPatternStrategy(Strategy):
    """
    Enhanced Flag Pattern Trading Strategy with integrated risk management
    from place_trade.py and proper stop loss implementation
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        self.sleeptime = "1D"
        
        # Strategy Configuration
        self.flagpole_period = 60
        self.flagpole_min_gain = 0.30
        
        # Moving Averages
        self.ma_fast = 10
        self.ma_medium = 20
        self.ma_slow = 50
        
        # Consolidation/Volatility
        self.consolidation_window = 20
        self.consolidation_volatility_threshold = 0.6
        
        # Initialize Risk Manager with strategy parameters
        initial_cash = 100000  # Starting capital
        self.risk_manager = RiskManager(
            account_balance=initial_cash,
            default_risk_percent=2,  # Risk 2% per trade
            max_position_size=0.10,  # Max 10% per position
            max_positions=10         # Max 10 positions
        )
        
        # Get tickers
        self.tickers = self.get_sp500_tickers()
        
        # Tracking
        self.trades_log = []
        self.stop_losses = {}  # Track stop loss levels for active positions
        
        self.log_message("Enhanced strategy initialized successfully")
        
    def get_sp500_tickers(self):
        """Get S&P 500 tickers with fallback"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            tickers = table['Symbol'].tolist()
            clean_tickers = []
            for ticker in tickers:
                clean_ticker = ticker.replace('.', '-')
                if not ticker.startswith('$') and len(ticker) <= 5:
                    clean_tickers.append(clean_ticker)
            
            self.log_message(f"Fetched {len(clean_tickers)} S&P 500 tickers")
            return clean_tickers[:50]  # Limit for testing
        except Exception as e:
            self.log_message(f"Could not fetch S&P 500 tickers: {e}")
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'V', 'PG',
                   'UNH', 'HD', 'MA', 'PFE', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX', 'CMCSA']
    
    def get_symbol_data(self, symbol, days_back=100):
        """Get historical data for a symbol"""
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
            
        recent_data = df.tail(self.flagpole_period)
        high_max = recent_data['high'].max()
        low_min = recent_data['low'].min()
        
        if low_min <= 0:
            return False, 0
            
        trend_gain = (high_max / low_min) - 1
        return trend_gain > self.flagpole_min_gain, trend_gain
    
    def check_consolidation(self, df):
        """Check if stock is in consolidation"""
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
        
        return current_volume > volume_avg * 1.2
    
    def check_ma_alignment(self, ma_fast, ma_medium, ma_slow):
        """Check if moving averages are properly aligned"""
        if ma_fast is None or ma_medium is None or ma_slow is None:
            return False
            
        if len(ma_fast) == 0 or len(ma_medium) == 0 or len(ma_slow) == 0:
            return False
            
        latest_fast = ma_fast.iloc[-1]
        latest_medium = ma_medium.iloc[-1]
        latest_slow = ma_slow.iloc[-1]
        
        if pd.isna(latest_fast) or pd.isna(latest_medium) or pd.isna(latest_slow):
            return False
        
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
            
            # 4. Check if price is above fast MA
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
    
    def on_trading_iteration(self):
        """Main trading logic with enhanced risk management"""
        try:
            current_date = self.get_datetime()
            
            # Update risk manager with current portfolio value
            portfolio_value = self.get_portfolio_value()
            self.risk_manager.update_account_balance(portfolio_value)
            
            positions = self.get_positions()
            self.log_message(f"Date: {current_date.date()}, Positions: {len(positions)}, Portfolio: ${portfolio_value:,.2f}")
            
            # Check stop losses first
            self.check_stop_losses()
            
            # Check other exit conditions
            self.check_exit_conditions()
            
            # Look for new entries
            if len(positions) < self.risk_manager.max_positions:
                self.look_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_stop_losses(self):
        """Check and execute stop losses using risk manager"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None or current_price <= 0:
                    continue
                
                # Check if we should stop out using risk manager
                if self.risk_manager.check_stop_loss(symbol, current_price):
                    self.log_message(f"STOP LOSS triggered for {symbol}: Price ${current_price:.2f}")
                    
                    # Create sell order
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    # Remove from risk manager tracking
                    self.risk_manager.remove_position(symbol)
                    
                    # Log the trade
                    self.log_trade(symbol, "sell", current_price, position.quantity, "Stop loss")
                    
            except Exception as e:
                self.log_message(f"Error checking stop loss for {position.asset.symbol}: {e}")
    
    def check_exit_conditions(self):
        """Check additional exit conditions (MA breach)"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None or current_price <= 0:
                    continue
                
                # Skip if already stopped out
                if symbol not in self.risk_manager.active_positions:
                    continue
                
                df = self.get_symbol_data(symbol, days_back=60)
                if df is None or len(df) < self.ma_medium:
                    continue
                
                # Calculate medium MA for exit signal
                ma_medium = df['close'].rolling(window=self.ma_medium).mean().iloc[-1]
                
                if pd.isna(ma_medium):
                    continue
                
                # Exit condition: price falls below medium MA
                if current_price < ma_medium * 0.98:  # 2% buffer
                    self.log_message(f"MA EXIT for {symbol}: Price ${current_price:.2f} below MA ${ma_medium:.2f}")
                    
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.risk_manager.remove_position(symbol)
                    self.log_trade(symbol, "sell", current_price, position.quantity, "MA exit")
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def look_for_entries(self):
        """Look for new entry opportunities using risk manager"""
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
                
                df = self.get_symbol_data(symbol, days_back=100)
                if df is None or len(df) < self.ma_slow:
                    continue
                
                should_enter, reason = self.check_entry_conditions(symbol, df)
                
                if should_enter:
                    current_price = df['close'].iloc[-1]
                    
                    try:
                        # Use risk manager to calculate trade
                        trade_data = self.risk_manager.calculate_trade(
                            ticker=symbol,
                            current_price=current_price,
                            stop_loss_percent=8  # 8% stop loss
                        )
                        
                        quantity = trade_data['shares']
                        
                        if quantity > 0:
                            # Create and submit buy order
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, quantity, "buy")
                            self.submit_order(order)
                            
                            # Add to risk manager tracking
                            self.risk_manager.add_position(trade_data)
                            
                            self.log_message(f"BUY {symbol}: {quantity} shares at ${current_price:.2f}, Stop: ${trade_data['stop_loss']:.2f}")
                            self.log_trade(symbol, "buy", current_price, quantity, reason)
                            
                            entries_found += 1
                            
                            if entries_found >= 2:
                                break
                                
                    except Exception as e:
                        self.log_message(f"Risk manager rejected {symbol}: {e}")
                        
            except Exception as e:
                self.log_message(f"Error checking entry for {symbol}: {e}")
                continue
        
        if entries_found == 0:
            exposure = self.risk_manager.get_portfolio_exposure()
            self.log_message(f"No entries found. Exposure: {exposure['exposure_percent']:.1f}%")
    
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
        self.log_message("Enhanced strategy ended")
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
            filename = f"enhanced_trades_{timestamp}.csv"
            df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(df)} trades to {filename}")
        except Exception as e:
            self.log_message(f"Error exporting trades: {e}")
    
    def print_performance_summary(self):
        """Print enhanced performance summary"""
        try:
            positions = self.get_positions()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            exposure = self.risk_manager.get_portfolio_exposure()
            
            self.log_message("=== ENHANCED STRATEGY PERFORMANCE ===")
            self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
            self.log_message(f"Cash: ${cash:,.2f}")
            self.log_message(f"Active Positions: {len(positions)}")
            self.log_message(f"Portfolio Exposure: {exposure['exposure_percent']:.1f}%")
            self.log_message(f"Total Trades: {len(self.trades_log)}")
            
            if self.trades_log:
                trades_df = pd.DataFrame(self.trades_log)
                buy_trades = trades_df[trades_df['action'] == 'buy']
                sell_trades = trades_df[trades_df['action'] == 'sell']
                stop_losses = sell_trades[sell_trades['reason'] == 'Stop loss']
                
                self.log_message(f"Buy Orders: {len(buy_trades)}")
                self.log_message(f"Sell Orders: {len(sell_trades)}")
                self.log_message(f"Stop Losses Triggered: {len(stop_losses)}")
                
        except Exception as e:
            self.log_message(f"Error printing performance summary: {e}")


def run_enhanced_backtest():
    """Run the enhanced backtest"""
    try:
        backtesting_start = datetime(2022, 1, 1)
        backtesting_end = datetime(2023, 12, 31)
        
        print("Setting up enhanced backtest with integrated risk management...")
        print(f"Period: {backtesting_start} to {backtesting_end}")
        
        class CustomYahooDataBacktesting(YahooDataBacktesting):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.min_fee = 1.0
                self.max_fee = 10.0
        
        results = EnhancedFlagPatternStrategy.backtest(
            CustomYahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={},
            benchmark_asset="SPY"
        )
        
        return results
        
    except Exception as e:
        print(f"Error in enhanced backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    try:
        print("Running Enhanced Flag Pattern Strategy with Risk Management...")
        results = run_enhanced_backtest()
        
        if results is not None:
            print("\n=== ENHANCED BACKTEST COMPLETED ===")
            print("Features integrated:")
            print("- Risk management from place_trade.py")
            print("- Proper stop loss implementation")
            print("- Portfolio-level risk controls")
            print("- Enhanced position sizing")
            print("- Input validation and error handling")
        else:
            print("Enhanced backtest failed to complete")
        
    except Exception as e:
        print(f"Error running enhanced backtest: {e}")
        import traceback
        traceback.print_exc()