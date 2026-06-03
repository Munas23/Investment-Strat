"""
S&P 500 Flag Strategy Optimization - Find Best Parameters
Systematic testing of different criteria on the full S&P 500 universe
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
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

warnings.filterwarnings('ignore')

class SP500OptimizationStrategy(Strategy):
    """Optimizable flag pattern strategy for S&P 500 testing"""
    
    def initialize(self, params=None):
        """Initialize with configurable parameters"""
        self.sleeptime = "1D"
        
        # Default parameters (can be overridden)
        default_params = {
            'flagpole_period': 60,
            'flagpole_min_gain': 0.15,
            'ma_fast': 5,
            'ma_medium': 20,
            'ma_slow': 60,
            'consolidation_window': 20,
            'consolidation_volatility_threshold': 0.3,
            'max_stop_loss': 0.08,
            'max_position_size': 0.15,
            'max_positions': 10,
            'volume_threshold': 1.1,
            'near_highs_threshold': 0.85,
            'ma_buffer': 0.99,
            'exit_ma_buffer': 0.97,
            'risk_percent': 2.0
        }
        
        # Update with provided parameters
        if params:
            default_params.update(params)
        
        # Set all parameters as instance variables
        for key, value in default_params.items():
            setattr(self, key, value)
        
        # Get S&P 500 tickers
        self.tickers = self.get_sp500_tickers()
        
        self.trades_log = []
        self.param_set = params if params else {}
        
        self.log_message(f"Strategy initialized with {len(self.tickers)} S&P 500 stocks")
        self.log_message(f"Parameters: {self.param_set}")
    
    def get_sp500_tickers(self):
        """Get current S&P 500 tickers from Wikipedia"""
        try:
            # Read S&P 500 list from Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            tickers = sp500_table['Symbol'].tolist()
            
            # Clean tickers (some have dots)
            cleaned_tickers = []
            for ticker in tickers:
                # Replace dots with dashes for Yahoo Finance compatibility
                cleaned_ticker = ticker.replace('.', '-')
                cleaned_tickers.append(cleaned_ticker)
            
            self.log_message(f"Loaded {len(cleaned_tickers)} S&P 500 tickers")
            return cleaned_tickers[:100]  # Use first 100 for faster testing
            
        except Exception as e:
            self.log_message(f"Error loading S&P 500 tickers: {e}")
            # Fallback to major stocks
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'GOOG',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'CVX', 'MA', 'BAC', 'ABBV',
                'PFE', 'AVGO', 'KO', 'COST', 'DIS', 'TMO', 'WMT', 'MRK', 'DHR',
                'VZ', 'ABT', 'ADBE', 'CRM', 'ACN', 'NFLX', 'NKE', 'TXN', 'RTX',
                'LIN', 'QCOM', 'NEE', 'ORCL', 'PM', 'AMD', 'BMY', 'UNP', 'T',
                'HON', 'IBM', 'SPGI', 'LLY', 'LOW', 'UPS', 'CAT', 'GS', 'INTC'
            ]
    
    def calculate_risk_position(self, current_price):
        """Risk-based position sizing"""
        try:
            account_balance = self.get_portfolio_value()
            capital_to_risk = account_balance * (self.risk_percent / 100)
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
            return 0, current_price * (1 - self.max_stop_loss)
    
    def get_symbol_data(self, symbol, days_back=100):
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
        """Configurable entry logic"""
        try:
            if len(df) < max(self.ma_slow, self.flagpole_period):
                return False, "Insufficient data"
            
            current_price = df['close'].iloc[-1]
            
            # Calculate indicators
            ma_fast = df['close'].rolling(self.ma_fast).mean()
            ma_medium = df['close'].rolling(self.ma_medium).mean()
            ma_slow = df['close'].rolling(self.ma_slow).mean()
            
            # Flagpole analysis
            high_period = df['high'].rolling(self.flagpole_period).max()
            low_period = df['low'].rolling(self.flagpole_period).min()
            flagpole_gain = (high_period / low_period - 1).iloc[-1]
            
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
            
            # 1. Flagpole condition
            if flagpole_gain < self.flagpole_min_gain:
                return False, f"Flagpole {flagpole_gain:.1%} < {self.flagpole_min_gain:.1%}"
            
            # 2. MA alignment
            if not (latest_ma_fast > latest_ma_medium * self.ma_buffer and 
                   latest_ma_medium > latest_ma_slow * self.ma_buffer):
                return False, "MAs not aligned"
            
            # 3. Price above fast MA
            if current_price < latest_ma_fast * self.ma_buffer:
                return False, "Price below fast MA"
            
            # 4. Low volatility
            if volatility > self.consolidation_volatility_threshold:
                return False, f"High volatility {volatility:.2f}"
            
            # 5. Near highs
            recent_high = df['high'].rolling(self.consolidation_window).max().iloc[-1]
            if current_price < recent_high * self.near_highs_threshold:
                return False, "Not near highs"
            
            # 6. Volume check
            vol_avg = df['volume'].rolling(self.consolidation_window).mean().iloc[-1]
            if df['volume'].iloc[-1] < vol_avg * self.volume_threshold:
                return False, "Low volume"
            
            return True, f"Entry: FP {flagpole_gain:.1%}, Vol {volatility:.2f}"
            
        except Exception as e:
            return False, f"Error: {e}"
    
    def on_trading_iteration(self):
        """Main trading logic"""
        try:
            current_positions = len(self.get_positions())
            
            # Check exits first
            self.check_exits()
            
            # Look for entries if we have room
            if current_positions < self.max_positions:
                self.look_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_exits(self):
        """Check exit conditions"""
        for position in self.get_positions():
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
                df = self.get_symbol_data(symbol, 50)
                if df is None or len(df) < self.ma_medium:
                    continue
                
                # Exit below medium MA
                ma_medium = df['close'].rolling(self.ma_medium).mean().iloc[-1]
                exit_price = ma_medium * self.exit_ma_buffer
                
                if current_price < exit_price:
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    self.log_trade(symbol, "sell", current_price, position.quantity, "MA exit")
                    
            except Exception as e:
                continue
    
    def look_for_entries(self):
        """Look for new entries"""
        entries_found = 0
        
        # Randomize order to avoid bias
        import random
        tickers_shuffled = self.tickers.copy()
        random.shuffle(tickers_shuffled)
        
        for symbol in tickers_shuffled[:50]:  # Check 50 random stocks
            try:
                # Skip if already holding
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                df = self.get_symbol_data(symbol, 100)
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
                            
                            self.log_trade(symbol, "buy", current_price, quantity, reason)
                            
                            entries_found += 1
                            if entries_found >= 3:  # Limit entries per day
                                break
                                
                        except Exception as e:
                            continue
                            
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
        portfolio_value = self.get_portfolio_value()
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value
        
        self.final_portfolio_value = portfolio_value
        self.total_return = total_return
        self.total_trades = len(self.trades_log)
        
        # Calculate additional metrics
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            buy_trades = trades_df[trades_df['action'] == 'buy']
            self.total_invested = buy_trades['value'].sum() if len(buy_trades) > 0 else 0
        else:
            self.total_invested = 0

def run_parameter_optimization():
    """Run optimization across different parameter combinations"""
    
    # Parameter grid for optimization
    param_grid = {
        'flagpole_min_gain': [0.10, 0.15, 0.20, 0.25],
        'ma_fast': [3, 5, 8, 10],
        'ma_medium': [15, 20, 25, 30],
        'ma_slow': [50, 60, 80, 100],
        'consolidation_volatility_threshold': [0.2, 0.3, 0.4, 0.5],
        'max_stop_loss': [0.06, 0.08, 0.10, 0.12],
        'max_position_size': [0.10, 0.15, 0.20, 0.25],
        'volume_threshold': [1.0, 1.1, 1.2, 1.3],
        'near_highs_threshold': [0.80, 0.85, 0.90, 0.95]
    }
    
    print("="*80)
    print("S&P 500 FLAG STRATEGY OPTIMIZATION")
    print("="*80)
    
    # Generate parameter combinations (limit to manageable number)
    keys = list(param_grid.keys())
    
    # Test top combinations based on logical importance
    test_combinations = [
        # Conservative approach
        {
            'flagpole_min_gain': 0.15,
            'ma_fast': 5, 'ma_medium': 20, 'ma_slow': 60,
            'consolidation_volatility_threshold': 0.3,
            'max_stop_loss': 0.08,
            'max_position_size': 0.15,
            'volume_threshold': 1.1,
            'near_highs_threshold': 0.85
        },
        # Aggressive approach
        {
            'flagpole_min_gain': 0.10,
            'ma_fast': 3, 'ma_medium': 15, 'ma_slow': 50,
            'consolidation_volatility_threshold': 0.4,
            'max_stop_loss': 0.06,
            'max_position_size': 0.20,
            'volume_threshold': 1.0,
            'near_highs_threshold': 0.90
        },
        # High threshold approach
        {
            'flagpole_min_gain': 0.25,
            'ma_fast': 8, 'ma_medium': 25, 'ma_slow': 80,
            'consolidation_volatility_threshold': 0.2,
            'max_stop_loss': 0.10,
            'max_position_size': 0.10,
            'volume_threshold': 1.2,
            'near_highs_threshold': 0.80
        },
        # Balanced approach
        {
            'flagpole_min_gain': 0.20,
            'ma_fast': 10, 'ma_medium': 30, 'ma_slow': 100,
            'consolidation_volatility_threshold': 0.5,
            'max_stop_loss': 0.12,
            'max_position_size': 0.25,
            'volume_threshold': 1.3,
            'near_highs_threshold': 0.95
        }
    ]
    
    # Backtest settings
    backtesting_start = datetime(2015, 1, 1)
    backtesting_end = datetime(2023, 12, 31)
    initial_cash = 100000.0
    
    results = []
    
    for i, params in enumerate(test_combinations):
        print(f"\nTesting combination {i+1}/{len(test_combinations)}")
        print(f"Parameters: {params}")
        print("-" * 60)
        
        try:
            # Create strategy with specific parameters
            strategy_results = SP500OptimizationStrategy.backtest(
                YahooDataBacktesting,
                backtesting_start,
                backtesting_end,
                parameters={'initial_cash': initial_cash, 'params': params}
            )
            
            # Extract metrics from strategy
            final_value = getattr(strategy_results.strategy, 'final_portfolio_value', initial_cash)
            total_return = getattr(strategy_results.strategy, 'total_return', 0)
            total_trades = getattr(strategy_results.strategy, 'total_trades', 0)
            
            result = {
                'combination': i + 1,
                'parameters': params,
                'final_value': final_value,
                'total_return': total_return,
                'total_trades': total_trades,
                'return_pct': total_return * 100
            }
            
            results.append(result)
            
            print(f"Final Value: ${final_value:,.2f}")
            print(f"Total Return: {total_return:.1%}")
            print(f"Total Trades: {total_trades}")
            
        except Exception as e:
            print(f"Error in combination {i+1}: {e}")
            continue
    
    # Analyze results
    if results:
        print("\n" + "="*80)
        print("OPTIMIZATION RESULTS SUMMARY")
        print("="*80)
        
        # Sort by return
        results_sorted = sorted(results, key=lambda x: x['total_return'], reverse=True)
        
        for i, result in enumerate(results_sorted):
            print(f"\nRank {i+1}: Combination {result['combination']}")
            print(f"Return: {result['return_pct']:.1f}%")
            print(f"Final Value: ${result['final_value']:,.2f}")
            print(f"Trades: {result['total_trades']}")
            print(f"Best Parameters:")
            for key, value in result['parameters'].items():
                print(f"  {key}: {value}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df = pd.DataFrame(results_sorted)
        filename = f"sp500_optimization_results_{timestamp}.csv"
        results_df.to_csv(filename, index=False)
        
        print(f"\nResults saved to {filename}")
        print("="*80)
        
        return results_sorted
    
    else:
        print("No successful results to analyze")
        return None

if __name__ == "__main__":
    print("Starting S&P 500 Strategy Optimization...")
    results = run_parameter_optimization()
    
    if results:
        print("Optimization completed successfully!")
        print(f"Best performing combination achieved {results[0]['return_pct']:.1f}% return")
    else:
        print("Optimization failed - check error messages above.")