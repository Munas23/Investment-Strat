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
from multi_market_risk_manager import MultiMarketRiskManager
from market_config import MultiMarketDataFetcher, MAJOR_MARKETS

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

class GlobalFlagPatternStrategy(Strategy):
    """
    Global Flag Pattern Trading Strategy across 10 major markets
    including ASX 300, with multi-currency risk management
    """
    
    def initialize(self):
        """Initialize strategy for global markets"""
        self.sleeptime = "1D"
        
        # Strategy Configuration
        self.flagpole_period = 60
        self.flagpole_min_gain = 0.25  # Slightly lower for international markets
        
        # Moving Averages
        self.ma_fast = 10
        self.ma_medium = 20
        self.ma_slow = 50
        
        # Consolidation/Volatility
        self.consolidation_window = 20
        self.consolidation_volatility_threshold = 0.7  # Slightly higher for international
        
        # Initialize Multi-Market Risk Manager
        initial_capital_usd = 500000  # Larger capital for global trading
        self.risk_manager = MultiMarketRiskManager(
            account_balance_usd=initial_capital_usd,
            default_risk_percent=1.5,  # More conservative for international
            max_position_size=0.08,    # 8% max per position (lower for diversification)
            max_positions_per_market=5, # Max 5 positions per market
            max_total_positions=25     # Max 25 total positions across all markets
        )
        
        # Initialize market data fetcher
        self.market_fetcher = MultiMarketDataFetcher()
        
        # Get tickers from all markets
        self.all_market_tickers = self.get_global_tickers()
        
        # Flatten all tickers for iteration
        self.all_tickers = []
        for market_tickers in self.all_market_tickers.values():
            self.all_tickers.extend(market_tickers)
        
        # Tracking
        self.trades_log = []
        self.market_performance = {market: {'trades': 0, 'pnl': 0.0} 
                                 for market in MAJOR_MARKETS.keys()}
        
        self.log_message(f"Global strategy initialized with {len(self.all_tickers)} tickers across {len(self.all_market_tickers)} markets")
        
    def get_global_tickers(self):
        """Get tickers from all major markets"""
        self.log_message("Fetching tickers from global markets...")
        
        # Limit tickers per market for manageable backtesting
        market_limits = {
            'US_SP500': 30,      # S&P 500
            'US_NASDAQ': 20,     # NASDAQ 100
            'AU_ASX300': 25,     # ASX 300 (key request)
            'UK_FTSE100': 15,    # FTSE 100
            'DE_DAX': 15,        # DAX 40
            'JP_NIKKEI': 15,     # Nikkei 225
            'CA_TSX': 15,        # TSX 60
            'FR_CAC40': 10,      # CAC 40
            'HK_HSI': 10,        # Hang Seng
            'CH_SMI': 10         # Swiss Market Index
        }
        
        all_tickers = {}
        for market_code, limit in market_limits.items():
            try:
                tickers = self.market_fetcher.get_market_tickers(market_code, limit)
                # Validate a sample to ensure data availability
                validated_tickers = self.market_fetcher.validate_tickers(tickers, sample_size=3)
                all_tickers[market_code] = validated_tickers
                self.log_message(f"✓ {market_code}: {len(validated_tickers)} validated tickers")
            except Exception as e:
                self.log_message(f"✗ {market_code}: Error - {e}")
                all_tickers[market_code] = []
        
        return all_tickers
    
    def get_symbol_data(self, symbol, days_back=100):
        """Get historical data for a symbol with error handling"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            
            if bars is not None and hasattr(bars, 'df') and len(bars.df) > 0:
                # Ensure we have minimum required data
                if len(bars.df) >= self.ma_slow:
                    return bars.df
            return None
        except Exception as e:
            self.log_message(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_moving_averages(self, df):
        """Calculate moving averages with validation"""
        if len(df) < self.ma_slow:
            return None, None, None
            
        try:
            ma_fast = df['close'].rolling(window=self.ma_fast).mean()
            ma_medium = df['close'].rolling(window=self.ma_medium).mean()
            ma_slow = df['close'].rolling(window=self.ma_slow).mean()
            
            # Validate no NaN in latest values
            if (pd.isna(ma_fast.iloc[-1]) or pd.isna(ma_medium.iloc[-1]) or 
                pd.isna(ma_slow.iloc[-1])):
                return None, None, None
                
            return ma_fast, ma_medium, ma_slow
        except:
            return None, None, None
    
    def check_flagpole_pattern(self, df):
        """Check if stock has a strong upward trend (flagpole)"""
        if len(df) < self.flagpole_period:
            return False, 0
            
        try:
            recent_data = df.tail(self.flagpole_period)
            high_max = recent_data['high'].max()
            low_min = recent_data['low'].min()
            
            if low_min <= 0 or pd.isna(high_max) or pd.isna(low_min):
                return False, 0
                
            trend_gain = (high_max / low_min) - 1
            return trend_gain > self.flagpole_min_gain, trend_gain
        except:
            return False, 0
    
    def check_consolidation(self, df):
        """Check if stock is in consolidation with improved logic"""
        if len(df) < self.consolidation_window:
            return False
            
        try:
            recent_data = df.tail(self.consolidation_window)
            price_std = recent_data['close'].std()
            price_mean = recent_data['close'].mean()
            
            if price_mean <= 0 or pd.isna(price_std) or pd.isna(price_mean):
                return False
                
            volatility_ratio = price_std / price_mean
            return volatility_ratio < self.consolidation_volatility_threshold
        except:
            return False
    
    def check_volume_confirmation(self, df):
        """Check if current volume is above average"""
        if len(df) < self.consolidation_window:
            return False
            
        try:
            recent_data = df.tail(self.consolidation_window)
            volume_avg = recent_data['volume'].mean()
            current_volume = df['volume'].iloc[-1]
            
            if pd.isna(volume_avg) or pd.isna(current_volume) or volume_avg <= 0:
                return False
                
            return current_volume > volume_avg * 1.1  # Slightly lower threshold for international
        except:
            return False
    
    def check_ma_alignment(self, ma_fast, ma_medium, ma_slow):
        """Check if moving averages are properly aligned"""
        if ma_fast is None or ma_medium is None or ma_slow is None:
            return False
            
        try:
            latest_fast = ma_fast.iloc[-1]
            latest_medium = ma_medium.iloc[-1]
            latest_slow = ma_slow.iloc[-1]
            
            if pd.isna(latest_fast) or pd.isna(latest_medium) or pd.isna(latest_slow):
                return False
            
            # Check alignment with tolerance for international markets
            ma_aligned = (latest_fast > latest_medium * 0.98 and 
                         latest_medium > latest_slow * 0.98)
            
            return ma_aligned
        except:
            return False
    
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
                return False, "Invalid moving averages"
            
            # 3. Check MA alignment
            if not self.check_ma_alignment(ma_fast, ma_medium, ma_slow):
                return False, "MAs not aligned"
            
            # 4. Check if price is above fast MA
            latest_ma_fast = ma_fast.iloc[-1]
            if current_price < latest_ma_fast * 0.99:  # Small tolerance
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
        """Main trading logic for global markets"""
        try:
            current_date = self.get_datetime()
            
            # Update risk manager with current portfolio value
            portfolio_value = self.get_portfolio_value()
            self.risk_manager.update_account_balance(portfolio_value)
            
            positions = self.get_positions()
            exposure = self.risk_manager.get_portfolio_exposure()
            
            self.log_message(f"Date: {current_date.date()}")
            self.log_message(f"Portfolio: ${portfolio_value:,.0f}, Exposure: {exposure['exposure_percent']:.1f}%")
            self.log_message(f"Positions: {len(positions)}/{self.risk_manager.max_total_positions}")
            
            # Check stop losses first
            self.check_stop_losses()
            
            # Check other exit conditions
            self.check_exit_conditions()
            
            # Look for new entries across all markets
            if len(positions) < self.risk_manager.max_total_positions:
                self.look_for_global_entries()
            
            # Log market breakdown
            self.log_market_exposure()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_stop_losses(self):
        """Check and execute stop losses across all markets"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None or current_price <= 0:
                    continue
                
                if self.risk_manager.check_stop_loss(symbol, current_price):
                    market_code = self.risk_manager.active_positions[symbol]['market_code']
                    currency = self.risk_manager.active_positions[symbol]['currency']
                    
                    self.log_message(f"STOP LOSS: {symbol} ({market_code}) at {current_price:.2f} {currency}")
                    
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.risk_manager.remove_position(symbol)
                    self.log_trade(symbol, "sell", current_price, position.quantity, "Stop loss", market_code)
                    
            except Exception as e:
                self.log_message(f"Error checking stop loss for {position.asset.symbol}: {e}")
    
    def check_exit_conditions(self):
        """Check additional exit conditions (MA breach)"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if (current_price is None or current_price <= 0 or 
                    symbol not in self.risk_manager.active_positions):
                    continue
                
                df = self.get_symbol_data(symbol, days_back=60)
                if df is None or len(df) < self.ma_medium:
                    continue
                
                ma_medium = df['close'].rolling(window=self.ma_medium).mean().iloc[-1]
                
                if pd.isna(ma_medium):
                    continue
                
                # Exit condition: price falls below medium MA
                if current_price < ma_medium * 0.97:  # 3% buffer for international
                    market_code = self.risk_manager.active_positions[symbol]['market_code']
                    currency = self.risk_manager.active_positions[symbol]['currency']
                    
                    self.log_message(f"MA EXIT: {symbol} ({market_code}) at {current_price:.2f} {currency}")
                    
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.risk_manager.remove_position(symbol)
                    self.log_trade(symbol, "sell", current_price, position.quantity, "MA exit", market_code)
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def look_for_global_entries(self):
        """Look for entry opportunities across all global markets"""
        entries_found = 0
        markets_checked = set()
        
        # Randomize ticker order for better market distribution
        import random
        shuffled_tickers = self.all_tickers.copy()
        random.shuffle(shuffled_tickers)
        
        for symbol in shuffled_tickers:
            try:
                # Skip if we already have this position
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                # Determine market for this ticker
                market_code = self.risk_manager.get_market_from_ticker(symbol)
                if market_code is None:
                    continue
                
                # Get market positions to check per-market limits
                market_positions = len(self.risk_manager.get_positions_by_market(market_code))
                if market_positions >= self.risk_manager.max_positions_per_market:
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
                            market_code=market_code,
                            stop_loss_percent=10  # 10% stop loss for international
                        )
                        
                        quantity = trade_data['shares']
                        
                        if quantity > 0:
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, quantity, "buy")
                            self.submit_order(order)
                            
                            self.risk_manager.add_position(trade_data)
                            
                            currency = trade_data['currency']
                            self.log_message(f"BUY: {symbol} ({market_code}) {quantity} shares at {current_price:.2f} {currency}")
                            self.log_trade(symbol, "buy", current_price, quantity, reason, market_code)
                            
                            entries_found += 1
                            markets_checked.add(market_code)
                            
                            # Limit entries per iteration
                            if entries_found >= 3:
                                break
                                
                    except Exception as e:
                        self.log_message(f"Risk manager rejected {symbol}: {e}")
                        
            except Exception as e:
                continue
        
        if entries_found == 0:
            self.log_message("No new global entry opportunities found")
        else:
            self.log_message(f"Found {entries_found} entries across {len(markets_checked)} markets: {list(markets_checked)}")
    
    def log_market_exposure(self):
        """Log current market and currency exposure"""
        try:
            exposure = self.risk_manager.get_portfolio_exposure()
            
            if exposure['market_breakdown']:
                self.log_message("Market Exposure:")
                for market, data in exposure['market_breakdown'].items():
                    market_name = MAJOR_MARKETS[market].name
                    self.log_message(f"  {market_name}: {data['percentage']:.1f}% ({data['positions']} pos)")
            
            if exposure['currency_breakdown']:
                currency_summary = self.risk_manager.get_currency_risk_summary()
                self.log_message(f"Currency Risk: {currency_summary['foreign_exposure_percentage']:.1f}% in {currency_summary['number_of_currencies']} currencies")
                
        except Exception as e:
            self.log_message(f"Error logging market exposure: {e}")
    
    def log_trade(self, symbol, action, price, quantity, reason, market_code):
        """Log trade details with market information"""
        market_config = MAJOR_MARKETS[market_code]
        
        trade_data = {
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'market_code': market_code,
            'market_name': market_config.name,
            'currency': market_config.currency,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason
        }
        self.trades_log.append(trade_data)
        
        # Update market performance tracking
        if action == 'buy':
            self.market_performance[market_code]['trades'] += 1
    
    def on_strategy_end(self):
        """Called when strategy ends"""
        self.log_message("Global strategy ended")
        self.export_trades_to_csv()
        self.print_global_performance_summary()
    
    def export_trades_to_csv(self):
        """Export all trades to CSV with market details"""
        if not self.trades_log:
            self.log_message("No trades to export")
            return
        
        try:
            df = pd.DataFrame(self.trades_log)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"global_trades_{timestamp}.csv"
            df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(df)} global trades to {filename}")
        except Exception as e:
            self.log_message(f"Error exporting trades: {e}")
    
    def print_global_performance_summary(self):
        """Print comprehensive global performance summary"""
        try:
            positions = self.get_positions()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            exposure = self.risk_manager.get_portfolio_exposure()
            currency_risk = self.risk_manager.get_currency_risk_summary()
            
            self.log_message("=== GLOBAL STRATEGY PERFORMANCE ===")
            self.log_message(f"Final Portfolio Value: ${portfolio_value:,.0f}")
            self.log_message(f"Cash: ${cash:,.0f}")
            self.log_message(f"Total Exposure: {exposure['exposure_percent']:.1f}%")
            self.log_message(f"Active Positions: {len(positions)}")
            self.log_message(f"Total Trades: {len(self.trades_log)}")
            
            # Market breakdown
            self.log_message("\n=== MARKET BREAKDOWN ===")
            for market, data in exposure['market_breakdown'].items():
                market_name = MAJOR_MARKETS[market].name
                trades_count = self.market_performance[market]['trades']
                self.log_message(f"{market_name}: {data['percentage']:.1f}% exposure, {data['positions']} positions, {trades_count} trades")
            
            # Currency breakdown
            self.log_message("\n=== CURRENCY EXPOSURE ===")
            self.log_message(f"Foreign Currency Exposure: {currency_risk['foreign_exposure_percentage']:.1f}%")
            for currency, data in currency_risk['currency_breakdown'].items():
                self.log_message(f"{currency}: {data['percentage_of_portfolio']:.1f}% of portfolio")
            
            # Trade statistics
            if self.trades_log:
                trades_df = pd.DataFrame(self.trades_log)
                buy_trades = trades_df[trades_df['action'] == 'buy']
                sell_trades = trades_df[trades_df['action'] == 'sell']
                
                self.log_message(f"\n=== TRADE STATISTICS ===")
                self.log_message(f"Buy Orders: {len(buy_trades)}")
                self.log_message(f"Sell Orders: {len(sell_trades)}")
                
                # Market distribution
                market_dist = buy_trades['market_name'].value_counts()
                self.log_message("Trades by Market:")
                for market, count in market_dist.items():
                    self.log_message(f"  {market}: {count} trades")
            
        except Exception as e:
            self.log_message(f"Error printing global performance summary: {e}")


def run_global_backtest():
    """Run the global multi-market backtest"""
    try:
        backtesting_start = datetime(2022, 1, 1)
        backtesting_end = datetime(2023, 12, 31)
        
        print("Setting up global multi-market backtest...")
        print(f"Period: {backtesting_start} to {backtesting_end}")
        print("Markets: S&P 500, NASDAQ, ASX 300, FTSE 100, DAX, Nikkei 225, TSX, CAC 40, Hang Seng, SMI")
        print("This may take 10-15 minutes due to international data fetching...")
        
        class CustomYahooDataBacktesting(YahooDataBacktesting):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.min_fee = 2.0  # Higher fees for international trading
                self.max_fee = 20.0
        
        results = GlobalFlagPatternStrategy.backtest(
            CustomYahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={},
            benchmark_asset="SPY"
        )
        
        return results
        
    except Exception as e:
        print(f"Error in global backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    try:
        print("Running Global Flag Pattern Strategy across 10 Major Markets...")
        print("Including ASX 300 as requested!")
        results = run_global_backtest()
        
        if results is not None:
            print("\n=== GLOBAL BACKTEST COMPLETED ===")
            print("✓ Multi-market trading implemented")
            print("✓ ASX 300 included with .AX suffix tickers")
            print("✓ Currency risk management active")
            print("✓ Market-specific position limits enforced")
            print("✓ Global exposure tracking enabled")
        else:
            print("Global backtest failed to complete")
        
    except Exception as e:
        print(f"Error running global backtest: {e}")
        import traceback
        traceback.print_exc()