"""
Optimized Flag Pattern Strategy using Lumibot
Uses the best parameters from your optimization results with stable Lumibot framework
"""

import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from lumibot.entities import Asset
import logging

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OptimizedFlagPatternStrategy(Strategy):
    """
    Optimized Flag Pattern Trading Strategy using best parameters from backtesting results
    
    Key optimizations:
    - MA(5/20/60) configuration (best performer)
    - 15% flagpole threshold 
    - 15% position size (46% return achieved)
    - 8% stop loss (optimal risk/reward)
    """
    
    def initialize(self):
        """Initialize strategy with optimized parameters"""
        self.sleeptime = "1D"  # Daily checks
        
        # OPTIMIZED PARAMETERS from your backtesting results
        # Best configuration: MA(5/20/60), 15% flagpole, 15% position, 8% stop
        self.flagpole_period = 60           # Lookback for trend analysis
        self.flagpole_min_gain = 0.15       # 15% minimum gain (optimized)
        
        # Moving Averages - OPTIMIZED CONFIGURATION (5/20/60)
        self.ma_fast = 5                    # Fast MA (optimized from 10)
        self.ma_medium = 20                 # Medium MA 
        self.ma_slow = 60                   # Slow MA (optimized from 50)
        
        # Consolidation parameters
        self.consolidation_window = 20
        self.consolidation_volatility_threshold = 0.3  # Tight consolidation
        
        # Risk Management - OPTIMIZED VALUES
        self.max_stop_loss = 0.08           # 8% stop loss (optimal)
        self.min_stop_loss = 0.02           # 2% minimum
        self.max_position_size = 0.15       # 15% position size (best return: 46%)
        self.max_positions = 10             # Maximum concurrent positions
        
        # Get tickers - using proven working approach
        self.tickers = self.get_sp500_tickers()
        
        # Performance tracking
        self.trades_log = []
        self.daily_stats = []
        
        self.log_message(f"Optimized Flag Pattern Strategy initialized")
        self.log_message(f"Parameters: MA({self.ma_fast}/{self.ma_medium}/{self.ma_slow}), "
                        f"Flagpole({self.flagpole_min_gain:.0%}), "
                        f"Position({self.max_position_size:.0%}), "
                        f"Stop({self.max_stop_loss:.0%})")
        
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
            return clean_tickers[:100]  # Limit for faster backtesting
        except Exception as e:
            self.log_message(f"Could not fetch S&P 500 tickers: {e}")
            # High-quality fallback list
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'PG',
                   'UNH', 'HD', 'MA', 'PFE', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX', 'CMCSA',
                   'XOM', 'BAC', 'WMT', 'KO', 'MRK', 'ABT', 'COST', 'AVGO', 'TMO', 'DHR']
    
    def get_symbol_data(self, symbol, days_back=120):
        """Get historical data using Lumibot's method"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            
            if bars is not None and hasattr(bars, 'df') and len(bars.df) > 0:
                return bars.df
            return None
        except Exception as e:
            self.log_message(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Calculate optimized technical indicators"""
        if len(df) < self.ma_slow:
            return None, None, None, None, None
            
        try:
            # Moving averages with OPTIMIZED periods
            ma_fast = df['close'].rolling(window=self.ma_fast).mean()
            ma_medium = df['close'].rolling(window=self.ma_medium).mean()
            ma_slow = df['close'].rolling(window=self.ma_slow).mean()
            
            # Flagpole analysis
            high_max = df['high'].rolling(window=self.flagpole_period).max()
            low_min = df['low'].rolling(window=self.flagpole_period).min()
            flagpole_gain = (high_max / low_min) - 1
            
            # Consolidation volatility
            price_std = df['close'].rolling(window=self.consolidation_window).std()
            price_mean = df['close'].rolling(window=self.consolidation_window).mean()
            volatility_ratio = price_std / price_mean
            
            # Volume analysis
            volume_avg = df['volume'].rolling(window=self.consolidation_window).mean()
            
            return ma_fast, ma_medium, ma_slow, flagpole_gain, volatility_ratio
            
        except Exception as e:
            self.log_message(f"Error calculating indicators: {e}")
            return None, None, None, None, None
    
    def check_optimized_entry_conditions(self, symbol, df):
        """Enhanced entry conditions using optimized parameters"""
        try:
            if len(df) < self.ma_slow:
                return False, "Insufficient data"
                
            current_price = df['close'].iloc[-1]
            
            if pd.isna(current_price) or current_price <= 0:
                return False, "Invalid price"
            
            # Calculate all indicators
            ma_fast, ma_medium, ma_slow, flagpole_gain, volatility_ratio = self.calculate_technical_indicators(df)
            
            if ma_fast is None:
                return False, "Indicator calculation failed"
            
            # Get latest values
            latest_ma_fast = ma_fast.iloc[-1]
            latest_ma_medium = ma_medium.iloc[-1]
            latest_ma_slow = ma_slow.iloc[-1]
            latest_flagpole_gain = flagpole_gain.iloc[-1]
            latest_volatility = volatility_ratio.iloc[-1]
            
            # Check for NaN values
            values_to_check = [latest_ma_fast, latest_ma_medium, latest_ma_slow, 
                             latest_flagpole_gain, latest_volatility]
            if any(pd.isna(val) for val in values_to_check):
                return False, "NaN in indicators"
            
            # 1. OPTIMIZED Flagpole condition (15% threshold)
            if latest_flagpole_gain < self.flagpole_min_gain:
                return False, f"Flagpole gain {latest_flagpole_gain:.1%} < {self.flagpole_min_gain:.1%}"
            
            # 2. OPTIMIZED MA alignment (5/20/60 configuration)
            if not (latest_ma_fast > latest_ma_medium * 0.99 and 
                   latest_ma_medium > latest_ma_slow * 0.99):
                return False, "MAs not aligned"
            
            # 3. Price above MAs (trend confirmation)
            if current_price < latest_ma_fast * 0.99:
                return False, "Price below fast MA"
            
            # 4. Low volatility consolidation
            if latest_volatility > self.consolidation_volatility_threshold:
                return False, f"High volatility {latest_volatility:.2f}"
            
            # 5. Near recent highs (breakout potential)
            recent_high = df['high'].rolling(window=20).max().iloc[-1]
            if current_price < recent_high * 0.85:
                return False, "Not near recent highs"
            
            # 6. Volume confirmation
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            if current_volume < avg_volume * 1.1:
                return False, "Insufficient volume"
            
            # 7. Strong close position
            daily_high = df['high'].iloc[-1]
            daily_low = df['low'].iloc[-1]
            close_position = (current_price - daily_low) / (daily_high - daily_low) if daily_high > daily_low else 0.5
            if close_position < 0.6:
                return False, "Weak close position"
            
            return True, f"All conditions met. Flagpole: {latest_flagpole_gain:.1%}, Vol: {latest_volatility:.2f}"
            
        except Exception as e:
            return False, f"Error in entry check: {e}"
    
    def calculate_risk_based_position_size(self, symbol, current_price, risk_percent=2, stop_loss_percent=8):
        """
        Calculate position size based on risk management principles
        Uses account balance, risk percentage, and stop loss to determine optimal position size
        """
        try:
            account_balance = self.get_portfolio_value()
            
            # Calculate capital to risk (default 2% of account)
            capital_to_risk = account_balance * (risk_percent / 100)
            
            # Calculate stop loss price
            stop_loss = current_price * (1 - stop_loss_percent / 100)
            
            # Risk per share
            risk_per_share = current_price - stop_loss
            
            if risk_per_share <= 0:
                return 0, stop_loss
            
            # Number of shares to buy (rounded down to nearest whole share)
            shares = int(capital_to_risk / risk_per_share)
            
            # Additional validation: don't exceed maximum position size
            max_position_value = self.get_cash() * self.max_position_size  # 15% of cash
            max_shares_by_cash = int(max_position_value / current_price)
            
            # Use the smaller of the two calculations
            final_shares = min(shares, max_shares_by_cash)
            
            # Ensure we have enough cash
            trade_value = final_shares * current_price
            available_cash = self.get_cash()
            if trade_value > available_cash * 0.95:  # Leave 5% cash buffer
                final_shares = int((available_cash * 0.95) / current_price)
            
            self.log_message(f"Risk calc for {symbol}: Risk ${capital_to_risk:.2f}, "
                           f"Risk/share ${risk_per_share:.2f}, Shares: {final_shares}, "
                           f"Stop: ${stop_loss:.2f}")
            
            return max(final_shares, 0), stop_loss
            
        except Exception as e:
            self.log_message(f"Error calculating position size for {symbol}: {e}")
            return 0, current_price * 0.92  # fallback stop loss
    
    def on_trading_iteration(self):
        """Main trading logic with optimized parameters"""
        try:
            current_date = self.get_datetime()
            positions = self.get_positions()
            current_positions = len(positions)
            
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            
            self.log_message(f"Date: {current_date.date()}, Positions: {current_positions}, "
                           f"Portfolio: ${portfolio_value:,.2f}, Cash: ${cash:,.2f}")
            
            # Check exit conditions first
            self.check_optimized_exit_conditions()
            
            # Look for new entries if we have room
            if current_positions < self.max_positions:
                self.look_for_optimized_entries()
            
            # Track daily performance
            self.track_daily_performance(current_date, portfolio_value, cash)
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_optimized_exit_conditions(self):
        """Optimized exit logic"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None or current_price <= 0:
                    continue
                
                # Get recent data
                df = self.get_symbol_data(symbol, days_back=80)
                if df is None or len(df) < self.ma_medium:
                    continue
                
                # Calculate medium MA for exit
                ma_medium = df['close'].rolling(window=self.ma_medium).mean().iloc[-1]
                
                if pd.isna(ma_medium):
                    continue
                
                # OPTIMIZED Exit condition: price below medium MA with buffer
                exit_threshold = ma_medium * 0.97  # 3% buffer below MA
                
                if current_price < exit_threshold:
                    self.log_message(f"Selling {symbol}: Price ${current_price:.2f} < MA exit ${exit_threshold:.2f}")
                    
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    # Calculate return
                    entry_price = position.quantity * position.asset.symbol  # Simplified
                    trade_return = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                    
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"MA exit, Return: {trade_return:.1%}")
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def look_for_optimized_entries(self):
        """Look for entries using optimized criteria"""
        entries_found = 0
        stocks_checked = 0
        
        for symbol in self.tickers:
            try:
                stocks_checked += 1
                
                # Skip if we already have this position
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                # Get historical data
                df = self.get_symbol_data(symbol, days_back=120)
                if df is None or len(df) < self.ma_slow:
                    continue
                
                # Check optimized entry conditions
                should_enter, reason = self.check_optimized_entry_conditions(symbol, df)
                
                if should_enter:
                    current_price = df['close'].iloc[-1]
                    quantity, calculated_stop_loss = self.calculate_risk_based_position_size(symbol, current_price)
                    
                    if quantity > 0:
                        try:
                            asset = Asset(symbol=symbol, asset_type="stock")
                            
                            # Create buy order
                            buy_order = self.create_order(asset, quantity, "buy")
                            self.submit_order(buy_order)
                            
                            # Store stop loss for this position (could be enhanced to track per position)
                            trade_value = quantity * current_price
                            
                            self.log_message(f"Buying {symbol}: {quantity} shares @ ${current_price:.2f}")
                            self.log_message(f"Trade value: ${trade_value:.2f}, Stop loss: ${calculated_stop_loss:.2f}")
                            self.log_message(f"Entry reason: {reason}")
                            
                            self.log_trade(symbol, "buy", current_price, quantity, 
                                         f"{reason} | Stop: ${calculated_stop_loss:.2f} | Risk: {((current_price - calculated_stop_loss) / current_price * 100):.1f}%")
                            
                            entries_found += 1
                            
                            # Limit entries per day
                            if entries_found >= 3:
                                break
                                
                        except Exception as e:
                            self.log_message(f"Error submitting order for {symbol}: {e}")
                            
            except Exception as e:
                self.log_message(f"Error checking {symbol}: {e}")
                continue
        
        self.log_message(f"Entry scan: {stocks_checked} stocks checked, {entries_found} entries found")
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Enhanced trade logging"""
        trade_data = {
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value(),
            'cash': self.get_cash()
        }
        self.trades_log.append(trade_data)
    
    def track_daily_performance(self, date, portfolio_value, cash):
        """Track daily performance metrics"""
        daily_data = {
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': cash,
            'positions': len(self.get_positions()),
            'total_value': portfolio_value
        }
        self.daily_stats.append(daily_data)
    
    def on_strategy_end(self):
        """Enhanced strategy end reporting"""
        self.log_message("=== OPTIMIZED STRATEGY COMPLETED ===")
        
        # Export trades
        self.export_enhanced_results()
        
        # Print performance summary
        self.print_optimized_performance_summary()
    
    def export_enhanced_results(self):
        """Export comprehensive results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Export trades
            if self.trades_log:
                trades_df = pd.DataFrame(self.trades_log)
                trades_file = f"optimized_lumibot_trades_{timestamp}.csv"
                trades_df.to_csv(trades_file, index=False)
                self.log_message(f"Exported {len(trades_df)} trades to {trades_file}")
            
            # Export daily stats
            if self.daily_stats:
                daily_df = pd.DataFrame(self.daily_stats)
                daily_file = f"optimized_lumibot_daily_{timestamp}.csv"
                daily_df.to_csv(daily_file, index=False)
                self.log_message(f"Exported daily stats to {daily_file}")
                
        except Exception as e:
            self.log_message(f"Error exporting results: {e}")
    
    def print_optimized_performance_summary(self):
        """Print comprehensive performance summary"""
        try:
            positions = self.get_positions()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            
            self.log_message("="*80)
            self.log_message("OPTIMIZED FLAG PATTERN STRATEGY - FINAL RESULTS")
            self.log_message("="*80)
            self.log_message(f"Configuration Used:")
            self.log_message(f"  MA Periods: {self.ma_fast}/{self.ma_medium}/{self.ma_slow}")
            self.log_message(f"  Flagpole Threshold: {self.flagpole_min_gain:.0%}")
            self.log_message(f"  Position Size: {self.max_position_size:.0%}")
            self.log_message(f"  Stop Loss: {self.max_stop_loss:.0%}")
            self.log_message("")
            self.log_message(f"Final Results:")
            self.log_message(f"  Portfolio Value: ${portfolio_value:,.2f}")
            self.log_message(f"  Cash: ${cash:,.2f}")
            self.log_message(f"  Active Positions: {len(positions)}")
            self.log_message(f"  Total Trades: {len(self.trades_log)}")
            
            if self.trades_log:
                trades_df = pd.DataFrame(self.trades_log)
                buy_trades = trades_df[trades_df['action'] == 'buy']
                sell_trades = trades_df[trades_df['action'] == 'sell']
                
                self.log_message(f"  Buy Orders: {len(buy_trades)}")
                self.log_message(f"  Sell Orders: {len(sell_trades)}")
                
                if len(buy_trades) > 0:
                    total_invested = buy_trades['value'].sum()
                    self.log_message(f"  Total Invested: ${total_invested:,.2f}")
                
                if len(sell_trades) > 0:
                    total_proceeds = sell_trades['value'].sum()
                    self.log_message(f"  Total Proceeds: ${total_proceeds:,.2f}")
            
            # Performance metrics
            if self.daily_stats and len(self.daily_stats) > 1:
                initial_value = self.daily_stats[0]['total_value']
                final_value = self.daily_stats[-1]['total_value']
                total_return = (final_value - initial_value) / initial_value
                
                days = len(self.daily_stats)
                annualized_return = (1 + total_return) ** (365 / days) - 1
                
                self.log_message(f"  Total Return: {total_return:.1%}")
                self.log_message(f"  Annualized Return: {annualized_return:.1%}")
            
            self.log_message("="*80)
            
        except Exception as e:
            self.log_message(f"Error in performance summary: {e}")


def run_optimized_backtest():
    """Run the optimized backtest"""
    try:
        # Backtest parameters
        backtesting_start = datetime(2020, 1, 1)  # Focused period
        backtesting_end = datetime(2023, 12, 31)
        initial_cash = 100000.0
        
        print("="*80)
        print("OPTIMIZED FLAG PATTERN STRATEGY BACKTEST")
        print("="*80)
        print("Using optimized parameters from backtesting results:")
        print("- MA Configuration: 5/20/60 (best performer)")
        print("- Flagpole Threshold: 15% (optimal entry)")
        print("- Position Size: 15% (achieved 46% return)")
        print("- Stop Loss: 8% (optimal risk/reward)")
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Cash: ${initial_cash:,.2f}")
        print("="*80)
        
        # Create custom backtesting class
        class CustomYahooDataBacktesting(YahooDataBacktesting):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.min_fee = 1.0  # $1 minimum fee
                self.max_fee = 10.0  # $10 maximum fee
        
        # Run backtest
        print("Starting backtest...")
        results = OptimizedFlagPatternStrategy.backtest(
            CustomYahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={
                'initial_cash': initial_cash
            },
            benchmark_asset="SPY"
        )
        
        print("\n=== BACKTEST COMPLETED SUCCESSFULLY ===")
        print("Results have been exported to CSV files")
        print("Check the generated files for detailed analysis")
        
        return results
        
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting Optimized Lumibot Flag Pattern Strategy...")
    results = run_optimized_backtest()
    
    if results is not None:
        print("\nBacktest completed successfully!")
        print("Check the CSV exports for detailed trade and performance data.")
    else:
        print("Backtest failed. Check the error messages above.")