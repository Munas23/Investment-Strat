"""
Fast Optimized Flag Strategy - Shorter backtest for quick results
Using the same optimized parameters but with reduced scope for faster execution
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

class FastOptimizedStrategy(Strategy):
    """Fast version of optimized flag pattern strategy for quick testing"""
    
    def initialize(self):
        """Initialize with optimized parameters"""
        self.sleeptime = "1D"
        
        # OPTIMIZED PARAMETERS (from your backtesting results)
        self.flagpole_period = 60
        self.flagpole_min_gain = 0.15       # 15% (optimized)
        self.ma_fast = 5                    # Fast MA (optimized)
        self.ma_medium = 20                 # Medium MA 
        self.ma_slow = 60                   # Slow MA (optimized)
        self.consolidation_window = 20
        self.consolidation_volatility_threshold = 0.3
        self.max_stop_loss = 0.08           # 8% stop loss (optimized)
        self.max_position_size = 0.15       # 15% position (optimized)
        self.max_positions = 5              # Reduced for faster execution
        
        # Smaller, high-quality stock list for faster backtesting
        self.tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JPM', 
            'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'ADBE', 'CRM',
            'NFLX', 'COST', 'WMT', 'KO', 'PFE', 'XOM', 'BAC'
        ]
        
        self.trades_log = []
        self.log_message("Fast Optimized Strategy initialized")
        self.log_message(f"Testing {len(self.tickers)} stocks with optimized parameters")
    
    def calculate_risk_position(self, current_price, risk_percent=2):
        """Risk-based position sizing"""
        try:
            account_balance = self.get_portfolio_value()
            capital_to_risk = account_balance * (risk_percent / 100)
            stop_loss = current_price * (1 - self.max_stop_loss)
            risk_per_share = current_price - stop_loss
            
            if risk_per_share <= 0:
                return 0, stop_loss
            
            shares = int(capital_to_risk / risk_per_share)
            
            # Limit by available cash and max position size
            max_cash_shares = int((self.get_cash() * self.max_position_size) / current_price)
            final_shares = min(shares, max_cash_shares)
            
            return max(final_shares, 0), stop_loss
            
        except Exception as e:
            self.log_message(f"Error in position calculation: {e}")
            return 0, current_price * 0.92
    
    def get_symbol_data(self, symbol, days_back=80):
        """Get historical data"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            
            if bars and hasattr(bars, 'df') and len(bars.df) > 0:
                return bars.df
            return None
        except:
            return None
    
    def check_entry_signal(self, symbol, df):
        """Simplified but optimized entry logic"""
        try:
            if len(df) < self.ma_slow:
                return False, "Insufficient data"
            
            current_price = df['close'].iloc[-1]
            
            # Calculate indicators
            ma_fast = df['close'].rolling(self.ma_fast).mean()
            ma_medium = df['close'].rolling(self.ma_medium).mean() 
            ma_slow = df['close'].rolling(self.ma_slow).mean()
            
            # Flagpole analysis
            high_60 = df['high'].rolling(self.flagpole_period).max()
            low_60 = df['low'].rolling(self.flagpole_period).min()
            flagpole_gain = (high_60 / low_60 - 1).iloc[-1]
            
            # Volatility
            price_std = df['close'].rolling(self.consolidation_window).std()
            price_mean = df['close'].rolling(self.consolidation_window).mean()
            volatility = (price_std / price_mean).iloc[-1]
            
            # Get latest MA values
            latest_ma_fast = ma_fast.iloc[-1]
            latest_ma_medium = ma_medium.iloc[-1]
            latest_ma_slow = ma_slow.iloc[-1]
            
            # Check all conditions
            if pd.isna(flagpole_gain) or pd.isna(volatility):
                return False, "NaN in indicators"
            
            # 1. Flagpole condition (15% optimized threshold)
            if flagpole_gain < self.flagpole_min_gain:
                return False, f"Flagpole {flagpole_gain:.1%} < 15%"
            
            # 2. MA alignment (5/20/60 optimized)
            if not (latest_ma_fast > latest_ma_medium * 0.99 and 
                   latest_ma_medium > latest_ma_slow * 0.99):
                return False, "MAs not aligned"
            
            # 3. Price above fast MA
            if current_price < latest_ma_fast * 0.99:
                return False, "Price below fast MA"
            
            # 4. Low volatility (optimized 0.3 threshold)
            if volatility > self.consolidation_volatility_threshold:
                return False, f"High volatility {volatility:.2f}"
            
            # 5. Near highs
            recent_high = df['high'].rolling(20).max().iloc[-1]
            if current_price < recent_high * 0.85:
                return False, "Not near highs"
            
            # 6. Volume check
            vol_avg = df['volume'].rolling(20).mean().iloc[-1]
            if df['volume'].iloc[-1] < vol_avg * 1.1:
                return False, "Low volume"
            
            return True, f"Entry signal: Flagpole {flagpole_gain:.1%}, Vol {volatility:.2f}"
            
        except Exception as e:
            return False, f"Error: {e}"
    
    def on_trading_iteration(self):
        """Main trading logic"""
        try:
            current_positions = len(self.get_positions())
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            
            self.log_message(f"Positions: {current_positions}, Portfolio: ${portfolio_value:,.0f}, Cash: ${cash:,.0f}")
            
            # Check exits first
            self.check_exits()
            
            # Look for entries if we have room
            if current_positions < self.max_positions:
                self.look_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_exits(self):
        """Check exit conditions for existing positions"""
        for position in self.get_positions():
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
                df = self.get_symbol_data(symbol, 40)
                if df is None or len(df) < self.ma_medium:
                    continue
                
                # Exit below medium MA (optimized exit)
                ma_medium = df['close'].rolling(self.ma_medium).mean().iloc[-1]
                exit_price = ma_medium * 0.97  # 3% buffer
                
                if current_price < exit_price:
                    self.log_message(f"Selling {symbol}: ${current_price:.2f} < ${exit_price:.2f}")
                    
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.log_trade(symbol, "sell", current_price, position.quantity, "MA exit")
                    
            except Exception as e:
                self.log_message(f"Exit error for {position.asset.symbol}: {e}")
    
    def look_for_entries(self):
        """Look for new entry opportunities"""
        entries_found = 0
        
        for symbol in self.tickers[:15]:  # Check first 15 stocks for speed
            try:
                # Skip if already holding
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                df = self.get_symbol_data(symbol, 80)
                if df is None:
                    continue
                
                should_enter, reason = self.check_entry_signal(symbol, df)
                
                if should_enter:
                    current_price = df['close'].iloc[-1]
                    quantity, stop_loss = self.calculate_risk_position(current_price)
                    
                    if quantity > 0:
                        try:
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, quantity, "buy")
                            self.submit_order(order)
                            
                            trade_value = quantity * current_price
                            risk_pct = ((current_price - stop_loss) / current_price) * 100
                            
                            self.log_message(f"Buying {symbol}: {quantity} shares @ ${current_price:.2f}")
                            self.log_message(f"Trade: ${trade_value:.0f}, Stop: ${stop_loss:.2f}, Risk: {risk_pct:.1f}%")
                            
                            self.log_trade(symbol, "buy", current_price, quantity, 
                                         f"{reason} | Stop: ${stop_loss:.2f}")
                            
                            entries_found += 1
                            if entries_found >= 2:  # Limit entries per day
                                break
                                
                        except Exception as e:
                            self.log_message(f"Order error for {symbol}: {e}")
                            
            except Exception as e:
                continue
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trade details"""
        trade_data = {
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value()
        }
        self.trades_log.append(trade_data)
    
    def on_strategy_end(self):
        """Strategy completion"""
        self.log_message("=== FAST OPTIMIZED STRATEGY COMPLETED ===")
        
        # Export results
        if self.trades_log:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            trades_df = pd.DataFrame(self.trades_log)
            filename = f"fast_optimized_trades_{timestamp}.csv"
            trades_df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(trades_df)} trades to {filename}")
        
        # Print summary
        portfolio_value = self.get_portfolio_value()
        positions = len(self.get_positions())
        total_trades = len(self.trades_log)
        
        self.log_message("="*50)
        self.log_message("FAST OPTIMIZED STRATEGY RESULTS")
        self.log_message("="*50)
        self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log_message(f"Active Positions: {positions}")
        self.log_message(f"Total Trades: {total_trades}")
        
        if total_trades > 0:
            trades_df = pd.DataFrame(self.trades_log)
            buy_trades = trades_df[trades_df['action'] == 'buy']
            sell_trades = trades_df[trades_df['action'] == 'sell']
            self.log_message(f"Buy Trades: {len(buy_trades)}")
            self.log_message(f"Sell Trades: {len(sell_trades)}")
            
            if len(buy_trades) > 0:
                total_invested = buy_trades['value'].sum()
                self.log_message(f"Total Invested: ${total_invested:,.2f}")
        
        # Calculate return
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value
        self.log_message(f"Total Return: {total_return:.1%}")
        self.log_message("="*50)

def run_fast_backtest():
    """Run fast backtest with optimized parameters"""
    try:
        # Shorter time period for faster execution
        backtesting_start = datetime(2022, 1, 1)  # Just 2 years
        backtesting_end = datetime(2023, 12, 31)
        initial_cash = 100000.0
        
        print("="*60)
        print("FAST OPTIMIZED FLAG PATTERN STRATEGY")
        print("="*60)
        print("Optimized Parameters:")
        print("- MA Configuration: 5/20/60 (best performer)")
        print("- Flagpole Threshold: 15% (optimal)")
        print("- Position Size: 15% max, Risk-based sizing")
        print("- Stop Loss: 8% (optimal)")
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Cash: ${initial_cash:,.2f}")
        print(f"Stocks: Top 25 liquid stocks")
        print("="*60)
        
        print("Starting fast backtest...")
        results = FastOptimizedStrategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash}
        )
        
        print("\n=== FAST BACKTEST COMPLETED ===")
        print("Check the generated CSV file for detailed trade data")
        
        return results
        
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting Fast Optimized Strategy...")
    results = run_fast_backtest()
    
    if results:
        print("Backtest completed successfully!")
        print("Results exported to CSV file.")
    else:
        print("Backtest failed - check error messages above.")