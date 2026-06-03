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
import talib

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)

class QullamaggieBreakoutStrategy(Strategy):
    """
    Qullamaggie-style Breakout Strategy using Lumibot
    
    Based on Kristjan Kullamägi's three timeless setups:
    1. Episodic Pivot (EP) - Breakout from tight consolidation after big move
    2. Breakout variations - Flag patterns and tight ranges
    3. Momentum continuation - Leading stocks making new highs
    
    Key principles:
    - Focus on leading stocks (best RS vs market)
    - Buy breakouts from tight consolidations
    - Cut losses quickly (3-7%)
    - Let winners run with trailing stops
    - Position size based on volatility
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        # Set the minimum sleep time between iterations (in seconds)
        self.sleeptime = "1D"  # Check once per day
        
        # Qullamaggie-style Parameters
        self.momentum_lookback = 60        # Days to measure momentum (leading stocks)
        self.min_momentum = 0.20           # Minimum 20% gain to qualify as leader
        
        # Consolidation Parameters (for tight ranges)
        self.consolidation_period = 10     # Days to check for tight consolidation
        self.max_consolidation_depth = 0.15  # Max 15% depth from high to low
        self.min_consolidation_days = 5   # Minimum days in consolidation
        
        # Breakout Parameters
        self.volume_surge = 1.5            # 50% above average volume on breakout
        self.breakout_range_days = 20      # Look for breakout from 20-day range
        
        # Risk Management (Qullamaggie style)
        self.stop_loss_percent = 0.03      # 7% hard stop (he uses 3-7%)
        self.trail_profit_trigger = 0.20   # Start trailing after 20% gain
        self.trail_percent = 0.10          # Trail by 10% from highs
        
        # Position Sizing
        self.risk_per_trade = 0.02         # Risk 1% of portfolio per trade
        self.max_position_size = 0.20      # Max 20% in any position
        self.max_positions = 20             # Focus on best setups only
        
        # Market Health
        self.use_market_filter = True      # Only trade when market is healthy
        
        # Get universe of stocks
        self.tickers = self.get_trading_universe()
        
        # Performance tracking
        self.trades_log = []
        self.position_tracker = {}
        
        self.log_message("Qullamaggie Strategy initialized successfully")
        
    def get_trading_universe(self):
        """Get universe of stocks to trade - focus on growth stocks"""
        try:
            # Get S&P 500
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            sp500_tickers = table['Symbol'].tolist()
            
            # Clean tickers
            clean_tickers = []
            for ticker in sp500_tickers:
                clean_ticker = ticker.replace('.', '-')
                if not ticker.startswith('$') and len(ticker) <= 5:
                    clean_tickers.append(clean_ticker)
            
            # For backtesting, limit to subset of likely growth stocks
            # In real trading, you'd scan for actual leaders
            growth_sectors = ['Technology', 'Communication Services', 'Consumer Discretionary']
            growth_stocks = table[table['GICS Sector'].isin(growth_sectors)]['Symbol'].tolist()
            growth_stocks = [t.replace('.', '-') for t in growth_stocks]
            
            # Add some known momentum stocks
            momentum_stocks = ['NVDA', 'TSLA', 'AMD', 'NFLX', 'SHOP', 'SQ', 'ROKU', 
                             'CRWD', 'NET', 'DDOG', 'SNOW', 'ABNB', 'COIN']
            
            all_tickers = list(set(growth_stocks + momentum_stocks))
            
            self.log_message(f"Trading universe: {len(all_tickers)} potential momentum stocks")
            return all_tickers[:50]  # Limit for faster backtesting
            
        except Exception as e:
            self.log_message(f"Could not fetch tickers: {e}")
            # Fallback to known momentum stocks
            return ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMD', 'GOOGL', 'AMZN', 'META', 
                   'NFLX', 'AVGO', 'ADBE', 'CRM', 'NOW', 'SHOP', 'SQ']
    
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
    
    def calculate_relative_strength(self, df, market_df):
        """Calculate relative strength vs market"""
        try:
            if len(df) < self.momentum_lookback or len(market_df) < self.momentum_lookback:
                return 0
            
            stock_return = (df['close'].iloc[-1] / df['close'].iloc[-self.momentum_lookback] - 1)
            market_return = (market_df['close'].iloc[-1] / market_df['close'].iloc[-self.momentum_lookback] - 1)
            
            rs = stock_return - market_return
            return rs
        except:
            return 0
    
    def is_in_tight_consolidation(self, df):
        """Check if stock is in tight consolidation (EP setup)"""
        try:
            if len(df) < self.consolidation_period:
                return False, 0
            
            recent = df.tail(self.consolidation_period)
            high_price = recent['high'].max()
            low_price = recent['low'].min()
            
            if high_price <= 0:
                return False, 0
            
            # Calculate consolidation depth
            depth = (high_price - low_price) / high_price
            
            # Check if it's tight enough
            is_tight = depth <= self.max_consolidation_depth
            
            # Also check that we've been consolidating for minimum days
            days_near_high = 0
            for i in range(len(recent)):
                if recent['close'].iloc[i] >= high_price * 0.95:  # Within 5% of high
                    days_near_high += 1
            
            is_consolidated = days_near_high >= self.min_consolidation_days
            
            return (is_tight and is_consolidated), depth
            
        except Exception as e:
            return False, 0
    
    def check_breakout_conditions(self, symbol, df, market_df):
        """Check if stock meets Qullamaggie breakout criteria"""
        try:
            if len(df) < max(self.momentum_lookback, self.breakout_range_days):
                return False, "Insufficient data"
            
            current_price = df['close'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            
            # 1. Relative Strength - Must be a leader
            rs = self.calculate_relative_strength(df, market_df)
            if rs < self.min_momentum:
                return False, f"Weak RS: {rs:.2%}"
            
            # 2. Price action - Must be near highs
            range_high = df['high'].tail(self.breakout_range_days).max()
            if current_price < range_high * 0.95:  # Must be within 5% of range high
                return False, "Not near highs"
            
            # 3. Check for tight consolidation (EP setup)
            is_tight, depth = self.is_in_tight_consolidation(df)
            if not is_tight:
                return False, f"Not tight consolidation: {depth:.2%}"
            
            # 4. Volume confirmation - Need surge on breakout
            avg_volume = df['volume'].tail(20).mean()
            if current_volume < avg_volume * self.volume_surge:
                return False, "No volume surge"
            
            # 5. Price breakout - Must break above range
            yesterday_high = df['high'].iloc[-2]
            if current_price <= yesterday_high:
                return False, "No breakout yet"
            
            # 6. Stock should be up today (momentum)
            if current_price <= df['open'].iloc[-1]:
                return False, "Not up on day"
            
            return True, f"RS: {rs:.2%}, Consolidation: {depth:.2%}"
            
        except Exception as e:
            return False, f"Error: {e}"
    
    def calculate_position_size(self, price, atr=None):
        """Calculate position size based on volatility and risk"""
        try:
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            
            # Risk-based position sizing
            risk_amount = portfolio_value * self.risk_per_trade
            stop_price = price * (1 - self.stop_loss_percent)
            risk_per_share = price - stop_price
            
            if risk_per_share > 0:
                shares = int(risk_amount / risk_per_share)
                
                # Apply position limits
                max_shares_by_cash = int(cash / price)
                max_shares_by_position = int(portfolio_value * self.max_position_size / price)
                
                shares = min(shares, max_shares_by_cash, max_shares_by_position)
                
                return max(shares, 0)
            return 0
        except:
            return 0
    
    def on_trading_iteration(self):
        """Main trading logic executed on each iteration"""
        try:
            current_date = self.get_datetime()
            
            # Get market data for RS calculation
            spy_asset = Asset(symbol="SPY", asset_type="stock")
            market_df = self.get_symbol_data("SPY", days_back=100)
            
            if market_df is None:
                self.log_message(f"Date: {current_date.date()}, No market data available")
                return
            
            # Check market health if filter is on
            if self.use_market_filter:
                market_ma200 = market_df['close'].rolling(200).mean().iloc[-1]
                if market_df['close'].iloc[-1] < market_ma200:
                    self.log_message(f"Date: {current_date.date()}, Market below MA50, no new trades")
                    # Still check exits
                    self.check_exit_conditions()
                    return
            
            # Get current positions
            positions = self.get_positions()
            current_positions = len(positions)
            
            self.log_message(f"Date: {current_date.date()}, Positions: {current_positions}/{self.max_positions}")
            
            # Check exit conditions first
            self.check_exit_conditions()
            
            # Look for new entries if we have room
            if current_positions < self.max_positions:
                self.scan_for_breakouts(market_df)
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def scan_for_breakouts(self, market_df):
        """Scan for Qullamaggie-style breakout setups"""
        setups_found = []
        
        for symbol in self.tickers:
            try:
                # Skip if already have position
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                # Get data
                df = self.get_symbol_data(symbol, days_back=100)
                if df is None or len(df) < self.momentum_lookback:
                    continue
                
                # Check for breakout setup
                qualifies, reason = self.check_breakout_conditions(symbol, df, market_df)
                
                if qualifies:
                    rs = self.calculate_relative_strength(df, market_df)
                    setups_found.append({
                        'symbol': symbol,
                        'rs': rs,
                        'price': df['close'].iloc[-1],
                        'reason': reason
                    })
                    
            except Exception as e:
                continue
        
        # Sort by relative strength and take the best setups
        setups_found.sort(key=lambda x: x['rs'], reverse=True)
        
        # Enter the best setups
        entries_made = 0
        max_entries_per_day = 2
        
        for setup in setups_found[:max_entries_per_day]:
            if self.enter_position(setup):
                entries_made += 1
                if len(self.get_positions()) >= self.max_positions:
                    break
        
        if entries_made == 0 and len(setups_found) > 0:
            self.log_message(f"Found {len(setups_found)} setups but couldn't enter any")
    
    def enter_position(self, setup):
        """Enter a position with Qullamaggie-style risk management"""
        try:
            symbol = setup['symbol']
            price = setup['price']
            
            # Calculate position size
            shares = self.calculate_position_size(price)
            
            if shares > 0:
                # Create and submit order
                asset = Asset(symbol=symbol, asset_type="stock")
                order = self.create_order(asset, shares, "buy")
                self.submit_order(order)
                
                # Track the position
                stop_price = price * (1 - self.stop_loss_percent)
                self.position_tracker[symbol] = {
                    'entry_price': price,
                    'entry_date': self.get_datetime(),
                    'stop_loss': stop_price,
                    'highest_price': price,
                    'trailing': False
                }
                
                self.log_message(f"ENTRY: {symbol} - {shares} shares @ ${price:.2f}, Stop: ${stop_price:.2f}, {setup['reason']}")
                self.log_trade(symbol, "buy", price, shares, setup['reason'])
                
                return True
                
        except Exception as e:
            self.log_message(f"Error entering {symbol}: {e}")
        
        return False
    
    def check_exit_conditions(self):
        """Check exits using Qullamaggie-style stops"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                
                # Get current data
                df = self.get_symbol_data(symbol, days_back=20)
                if df is None:
                    continue
                
                current_price = df['close'].iloc[-1]
                
                # Get position tracking
                if symbol not in self.position_tracker:
                    continue
                
                pos_data = self.position_tracker[symbol]
                entry_price = pos_data['entry_price']
                stop_loss = pos_data['stop_loss']
                highest_price = pos_data['highest_price']
                
                # Update highest price
                if current_price > highest_price:
                    pos_data['highest_price'] = current_price
                    highest_price = current_price
                
                # Calculate gain
                gain = (current_price / entry_price) - 1
                
                # Check if we should start trailing
                if gain >= self.trail_profit_trigger and not pos_data['trailing']:
                    pos_data['trailing'] = True
                    new_stop = highest_price * (1 - self.trail_percent)
                    pos_data['stop_loss'] = max(new_stop, entry_price)  # Never below breakeven
                    self.log_message(f"TRAILING: {symbol} - Gain: {gain:.1%}, New stop: ${pos_data['stop_loss']:.2f}")
                
                # Update trailing stop if active
                if pos_data['trailing']:
                    new_stop = highest_price * (1 - self.trail_percent)
                    if new_stop > pos_data['stop_loss']:
                        pos_data['stop_loss'] = new_stop
                
                # Check if stop hit
                if current_price <= pos_data['stop_loss']:
                    # Exit position
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    exit_gain = (current_price / entry_price) - 1
                    reason = "Trailing stop" if pos_data['trailing'] else "Initial stop"
                    
                    self.log_message(f"EXIT: {symbol} - {reason} @ ${current_price:.2f}, Gain: {exit_gain:.1%}")
                    self.log_trade(symbol, "sell", current_price, position.quantity, reason)
                    
                    del self.position_tracker[symbol]
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
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
            filename = f"qullamaggie_trades_{timestamp}.csv"
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
            
            self.log_message("=== QULLAMAGGIE STRATEGY PERFORMANCE ===")
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
                
                # Calculate win rate if we have pairs
                if len(sell_trades) > 0:
                    # Simple win rate calculation
                    self.log_message("\n--- Trade Analysis ---")
                    self.log_message(f"Completed Trades: {len(sell_trades)}")
            
        except Exception as e:
            self.log_message(f"Error printing performance summary: {e}")


def run_backtest():
    """Run the backtest"""
    try:
        # Strategy parameters
        backtesting_start = datetime(2018, 1, 1)
        backtesting_end = datetime(2023, 12, 31)
        
        print("Setting up Qullamaggie Breakout Strategy backtest...")
        print(f"Period: {backtesting_start} to {backtesting_end}")
        print("Starting backtest...")
        print("This may take several minutes...")
        
        # Create custom backtesting class
        class CustomYahooDataBacktesting(YahooDataBacktesting):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.min_fee = 1.0  # $1 minimum fee per trade
                self.max_fee = 10.0  # $10 maximum fee per trade
        
        # Run the backtest
        results = QullamaggieBreakoutStrategy.backtest(
            CustomYahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={},
            benchmark_asset="SPY"
        )
        
        return results
        
    except Exception as e:
        print(f"Error in backtest setup: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    try:
        print("Running Qullamaggie Breakout Strategy Backtest...")
        print("=" * 60)
        print("Strategy based on Kristjan Kullamägi's approach:")
        print("- Focus on leading stocks (best relative strength)")
        print("- Buy breakouts from tight consolidations")
        print("- Cut losses at 7%, trail winners by 10%")
        print("- Risk 1% per trade, max 5 positions")
        print("=" * 60)
        
        results = run_backtest()
        
        if results is not None:
            print("\n=== BACKTEST COMPLETED ===")
            print("Check the generated CSV file for detailed trade records")
            
            try:
                print("\nBacktest Results:")
                print(f"Results type: {type(results)}")
                
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