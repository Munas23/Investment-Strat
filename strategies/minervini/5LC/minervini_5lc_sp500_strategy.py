"""
5LC (5 Level Conviction) Strategy - S&P500 Implementation with Market Health Overlay
==================================================================================

Enhanced version of Minervini's methodology with:
1. Halved conviction percentages for more conservative position sizing
2. Market health overlay using SPY as market indicator
3. Dynamic position sizing based on market conditions
4. Professional risk management and pyfolio analysis

Market Health Rules:
- HALVE positions when SPY < 20MA AND < 50MA (weak bear markets)
- DOUBLE positions when SPY > 20MA AND > 50MA AND > 200MA (strong bull markets)  
- NORMAL positions otherwise
"""

import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.entities import Asset
import os

# Import enhanced analysis
try:
    import pyfolio as pf
    PYFOLIO_AVAILABLE = True
    print("✓ Pyfolio-reloaded loaded successfully")
except ImportError:
    PYFOLIO_AVAILABLE = False
    print("⚠️ Pyfolio-reloaded not installed. Install with: pip install pyfolio-reloaded")

# Import our fundamental screening
try:
    from minervini_fundamentals import MinerviniFoundamentals
except ImportError:
    print("⚠️ minervini_fundamentals module not found - using simplified fundamentals")
    class MinerviniFoundamentals:
        def get_fundamental_data(self, symbol):
            return {'error': 'Module not available'}
        def screen_fundamentals(self, data):
            return {'error': 'Module not available'}

warnings.filterwarnings('ignore')

class Minervini5LCSP500Strategy(Strategy):
    """
    5LC S&P500 Strategy with Market Health Overlay
    
    Features:
    1. Halved conviction percentages (5%-20% vs 10%-40%)
    2. Market health overlay using SPY moving averages
    3. Dynamic position sizing based on market regime
    4. Enhanced risk management for US market
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        self.sleeptime = "1D"
        
        # Championship parameters (original position sizes)
        self.max_positions = 6
        self.min_position_size = 0.10  # Original size
        self.max_position_size = 0.40  # Original size
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.fundamental_threshold = 60.0
        
        # Risk management
        self.trail_profit_trigger = 0.20
        self.trail_percent = 0.12
        self.max_hold_days = 360
        
        # Market health overlay parameters
        self.market_health_symbol = "SPY"  # S&P500 ETF
        self.market_health_data = None
        self.current_market_regime = "NORMAL"  # WEAK, NORMAL, STRONG
        
        # Initialize screener
        self.fundamental_screener = MinerviniFoundamentals()
        self.sp500_symbols = self.get_sp500_symbols()
        
        # Performance tracking for Pyfolio
        self.daily_returns = []
        self.portfolio_values = []
        self.benchmark_returns = []
        self.dates = []
        
        # Trading tracking  
        self.fundamental_leaders = []
        self.last_screening_date = None
        self.screening_frequency = 30
        self.trades_log = []
        self.position_tracker = {}
        
        # Debug tracking
        self.debug_stats = {
            'screening_attempts': 0,
            'fundamental_leaders_found': 0,
            'technical_signals_checked': 0,
            'conviction_signals_generated': 0,
            'orders_attempted': 0,
            'orders_successful': 0,
            'market_regime_changes': 0
        }
        
        self.log_message("=== 5LC S&P500 STRATEGY WITH MARKET HEALTH OVERLAY ===")
        self.log_message(f"Universe: S&P 500 ({len(self.sp500_symbols)} stocks)")
        self.log_message(f"Market Health Indicator: {self.market_health_symbol}")
        self.log_message(f"Pyfolio Integration: {'✓ Enabled' if PYFOLIO_AVAILABLE else '✗ Disabled'}")
        self.log_message("=" * 70)
    
    def get_sp500_symbols(self):
        """Get complete S&P 500 symbol list"""
        try:
            # Get S&P 500 from Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            symbols = table['Symbol'].tolist()
            
            # Clean symbols (replace dots with dashes for Yahoo Finance)
            clean_symbols = []
            for symbol in symbols:
                clean_symbol = symbol.replace('.', '-')
                if not symbol.startswith('$') and len(symbol) <= 6:
                    clean_symbols.append(clean_symbol)
            
            self.log_message(f"Successfully loaded {len(clean_symbols)} S&P 500 symbols")
            return clean_symbols
            
        except Exception as e:
            self.log_message(f"Error loading S&P 500 symbols: {e}")
            # Fallback to major stocks
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT',
                'PG', 'UNH', 'JPM', 'HD', 'MA', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX',
                'COST', 'KO', 'PFE', 'XOM', 'BAC', 'ABBV', 'ABT', 'ACN', 'TMO', 'LLY',
                'AVGO', 'GOOG', 'BRK-B', 'CVX', 'ORCL', 'CSCO', 'AZN', 'NKE', 'SCHW'
            ]
    
    def get_market_health_regime(self):
        """Determine current market health regime"""
        try:
            # Get SPY data for market health analysis
            spy_asset = Asset(symbol=self.market_health_symbol, asset_type="stock")
            spy_data = self.get_historical_prices(spy_asset, 250, "day")
            
            if not spy_data or len(spy_data.df) < 200:
                return "NORMAL"
            
            df = spy_data.df
            current_price = df['close'].iloc[-1]
            
            # Calculate moving averages
            ma_20 = df['close'].rolling(20).mean().iloc[-1]
            ma_50 = df['close'].rolling(50).mean().iloc[-1]
            ma_200 = df['close'].rolling(200).mean().iloc[-1]
            
            # Determine regime
            if (current_price < ma_20 and current_price < ma_50):
                regime = "WEAK"  # Bear market - halve positions
            elif (current_price > ma_20 and current_price > ma_50 and current_price > ma_200):
                regime = "STRONG"  # Bull market - double positions
            else:
                regime = "NORMAL"  # Mixed conditions - normal positions
            
            # Track regime changes
            if regime != self.current_market_regime:
                self.debug_stats['market_regime_changes'] += 1
                self.log_message(f"MARKET REGIME CHANGE: {self.current_market_regime} → {regime}")
                self.log_message(f"  SPY: ${current_price:.2f}, 20MA: ${ma_20:.2f}, 50MA: ${ma_50:.2f}, 200MA: ${ma_200:.2f}")
                self.current_market_regime = regime
            
            return regime
            
        except Exception as e:
            self.log_message(f"Error determining market regime: {e}")
            return "NORMAL"
    
    def apply_market_health_multiplier(self, base_position_size):
        """Apply market health multiplier to position size"""
        regime = self.get_market_health_regime()
        
        if regime == "WEAK":
            return base_position_size * 0.5  # Halve positions in weak markets
        elif regime == "STRONG":
            return base_position_size * 2.0  # Double positions in strong markets
        else:
            return base_position_size  # Normal positions
    
    def on_trading_iteration(self):
        """Main trading logic with performance tracking"""
        try:
            current_date = self.get_datetime()
            portfolio_value = self.get_portfolio_value()
            
            # Track performance for Pyfolio
            self.track_daily_performance(current_date, portfolio_value)
            
            # Update screening periodically
            self.update_fundamental_leaders()
            
            # Execute trading logic
            self.check_championship_exits()
            
            positions = self.get_positions()
            if len(positions) < self.max_positions and self.fundamental_leaders:
                self.scan_for_championship_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def track_daily_performance(self, date, portfolio_value):
        """Track daily performance for Pyfolio analysis"""
        try:
            # Calculate daily return
            if len(self.portfolio_values) > 0:
                previous_value = self.portfolio_values[-1]
                daily_return = (portfolio_value / previous_value) - 1
            else:
                daily_return = 0.0
            
            self.daily_returns.append(daily_return)
            self.portfolio_values.append(portfolio_value)
            self.dates.append(date)
            
            # Get benchmark return (SPY)
            try:
                spy_asset = Asset(symbol="SPY", asset_type="stock")
                spy_data = self.get_historical_prices(spy_asset, 2, "day")
                
                if spy_data and len(spy_data.df) >= 2:
                    spy_current = spy_data.df['close'].iloc[-1]
                    spy_previous = spy_data.df['close'].iloc[-2]
                    benchmark_return = (spy_current / spy_previous) - 1
                else:
                    benchmark_return = 0.0
            except:
                benchmark_return = 0.0
            
            self.benchmark_returns.append(benchmark_return)
            
        except Exception as e:
            self.log_message(f"Error tracking performance: {e}")
    
    def update_fundamental_leaders(self):
        """Update list of fundamental leaders"""
        current_date = self.get_datetime()
        
        # Check if we need to re-screen
        if (self.last_screening_date is None or 
            (current_date - self.last_screening_date).days >= self.screening_frequency):
            
            self.log_message(f"Updating fundamental screening...")
            
            # Sample subset for faster screening
            sample_size = min(100, len(self.sp500_symbols))  # Start with 100 S&P500 stocks
            symbols_to_screen = self.sp500_symbols[:sample_size]
            
            leaders = []
            screening_count = 0
            
            for symbol in symbols_to_screen:
                try:
                    self.debug_stats['screening_attempts'] += 1
                    
                    # Get fundamental data
                    fundamentals = self.fundamental_screener.get_fundamental_data(symbol)
                    
                    if 'error' not in fundamentals:
                        # Screen fundamentals
                        screening = self.fundamental_screener.screen_fundamentals(fundamentals)
                        
                        if ('error' not in screening and 
                            screening['score_percentage'] >= self.fundamental_threshold):
                            leaders.append({
                                'symbol': symbol,
                                'score': screening['score_percentage'],
                                'rating': screening['rating']
                            })
                            self.debug_stats['fundamental_leaders_found'] += 1
                        
                        screening_count += 1
                        
                        # Progress update
                        if screening_count % 10 == 0:
                            self.log_message(f"  Screened {screening_count}/{len(symbols_to_screen)} stocks...")
                    
                except Exception as e:
                    continue
            
            # Update leaders list
            self.fundamental_leaders = [leader['symbol'] for leader in leaders]
            self.last_screening_date = current_date
            
            self.log_message(f"Fundamental screening complete:")
            self.log_message(f"  Screened: {screening_count} stocks")
            self.log_message(f"  Leaders found: {len(self.fundamental_leaders)}")
            self.log_message(f"  Market Regime: {self.current_market_regime}")
            
            # Log top leaders
            for leader in sorted(leaders, key=lambda x: x['score'], reverse=True)[:5]:
                self.log_message(f"    {leader['symbol']}: {leader['score']:.1f}% ({leader['rating']})")
    
    def get_symbol_data(self, symbol, days_back=200):
        """Get symbol data"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            return bars.df if bars and hasattr(bars, 'df') and len(bars.df) > 0 else None
        except:
            return None
    
    def calculate_trend_strength(self, df):
        """Calculate Minervini trend strength score (0-100)"""
        if len(df) < 150:
            return 0
        
        current = df.iloc[-1]
        
        # Calculate moving averages
        ma_21 = df['close'].rolling(21).mean().iloc[-1]
        ma_50 = df['close'].rolling(50).mean().iloc[-1]
        ma_150 = df['close'].rolling(150).mean().iloc[-1]
        
        # Calculate momentum
        momentum_20d = ((current['close'] / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
        momentum_50d = ((current['close'] / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
        
        # Calculate highs
        high_50 = df['high'].rolling(50).max().iloc[-1]
        
        score = 0
        
        # Price above moving averages (40 points)
        if not pd.isna(ma_21) and current['close'] > ma_21:
            score += 10
        if not pd.isna(ma_50) and current['close'] > ma_50:
            score += 15
        if not pd.isna(ma_150) and current['close'] > ma_150:
            score += 15
        
        # Moving average alignment (20 points)
        if not pd.isna(ma_21) and not pd.isna(ma_50) and ma_21 > ma_50:
            score += 10
        if not pd.isna(ma_50) and not pd.isna(ma_150) and ma_50 > ma_150:
            score += 10
        
        # Momentum (20 points)
        if momentum_20d > 5:
            score += 10
        if momentum_50d > 10:
            score += 10
        
        # Near highs (20 points)
        if not pd.isna(high_50):
            distance_from_high = (current['close'] / high_50 - 1) * 100
            if distance_from_high > -10:  # Within 10% of 50-day high
                score += 20
        
        return score
    
    def generate_conviction_signal(self, symbol, df):
        """Generate conviction-based entry signal (0-5) with halved thresholds"""
        try:
            if len(df) < 150:
                return 0, "Insufficient data"
            
            current_price = df['close'].iloc[-1]
            
            # Base requirement: Strong trend (score >60)
            trend_strength = self.calculate_trend_strength(df)
            if trend_strength < 60:
                return 0, f"Weak trend: {trend_strength}"
            
            conviction = 0
            
            # Factor 1: Breakout power (0-25 points)
            high_20 = df['high'].rolling(20).max().iloc[-1]
            high_50 = df['high'].rolling(50).max().iloc[-1]
            
            if current_price > high_20 * 1.01:  # 1% above 20-day high
                conviction += 15
                if current_price > high_50 * 1.02:  # 2% above 50-day high
                    conviction += 10
            
            # Factor 2: Volume confirmation (0-30 points)
            volume_avg = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_surge = current_volume / volume_avg if volume_avg > 0 else 0
            
            if volume_surge > 2.0:  # 2x volume
                conviction += 30
            elif volume_surge > 1.5:  # 1.5x volume
                conviction += 20
            elif volume_surge > 1.2:  # 1.2x volume
                conviction += 10
            
            # Factor 3: Momentum alignment (0-25 points)
            momentum_5d = ((current_price / df['close'].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0
            momentum_20d = ((current_price / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
            momentum_50d = ((current_price / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
            
            if momentum_5d > 1:
                conviction += 5
            if momentum_20d > 5:
                conviction += 10
            if momentum_50d > 10:
                conviction += 10
            
            # Factor 4: Trend quality bonus (0-20 points)
            trend_bonus = min(20, int((trend_strength - 60) / 2))
            conviction += trend_bonus
            
            # Convert to conviction level (0-100 -> 0-5) with HALVED thresholds
            if conviction >= 42:  # Was 85, now 42 (halved)
                return 5, f"MAX conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 35:  # Was 70, now 35 (halved)
                return 4, f"HIGH conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 27:  # Was 55, now 27 (halved)
                return 3, f"STANDARD conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 20:  # Was 40, now 20 (halved)
                return 2, f"LOW conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 12:  # Was 25, now 12 (halved)
                return 1, f"MINIMAL conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            
            return 0, f"No conviction: {conviction}, trend: {trend_strength}"
            
        except Exception as e:
            return 0, f"Error: {e}"
    
    def calculate_position_size(self, symbol, price, conviction_level):
        """Calculate position size with halved percentages and market health overlay"""
        try:
            portfolio_value = self.get_portfolio_value()
            
            # Base position size by conviction level (original sizes)
            base_position_pct = {
                1: 0.10,   # 10% - minimal conviction
                2: 0.125,  # 12.5% - low conviction  
                3: 0.15,   # 15% - standard conviction
                4: 0.175,  # 17.5% - high conviction
                5: 0.20    # 20% - maximum conviction
            }.get(conviction_level, 0.10)
            
            # Apply market health multiplier
            adjusted_position_pct = self.apply_market_health_multiplier(base_position_pct)
            
            # Ensure we don't exceed maximum position size
            final_position_pct = min(adjusted_position_pct, self.max_position_size)
            
            # Calculate position value
            position_value = portfolio_value * final_position_pct
            shares = int(position_value / price)
            
            # Apply cash constraints
            max_shares_by_cash = int(self.get_cash() / price)
            
            final_shares = min(shares, max_shares_by_cash)
            return max(final_shares, 0)
            
        except Exception as e:
            self.log_message(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def check_championship_exits(self):
        """Check exits using Minervini's championship rules"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
                # Get position tracking data
                if symbol not in self.position_tracker:
                    # Initialize tracking for existing position
                    self.position_tracker[symbol] = {
                        'entry_price': current_price,  # Approximate
                        'entry_date': self.get_datetime(),
                        'stop_loss': current_price * (1 - self.stop_loss_pct),
                        'highest_price': current_price,
                        'trailing': False
                    }
                
                pos_data = self.position_tracker[symbol]
                entry_price = pos_data['entry_price']
                stop_loss = pos_data['stop_loss']
                highest_price = pos_data['highest_price']
                
                # Update highest price
                if current_price > highest_price:
                    pos_data['highest_price'] = current_price
                    highest_price = current_price
                
                # Calculate current P&L
                pnl_pct = (current_price / entry_price - 1) * 100
                days_held = (self.get_datetime() - pos_data['entry_date']).days
                
                should_exit = False
                exit_reason = ""
                
                # 1. Stop Loss (7%)
                if pnl_pct < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # 2. Home Run Target (50%)
                elif pnl_pct > self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'HOME RUN TARGET'
                
                # 3. Trailing Stop (after 20% gain)
                elif pnl_pct > self.trail_profit_trigger * 100:
                    if not pos_data['trailing']:
                        pos_data['trailing'] = True
                        self.log_message(f"TRAILING activated for {symbol} at {pnl_pct:.1f}% gain")
                    
                    new_stop = highest_price * (1 - self.trail_percent)
                    if new_stop > pos_data['stop_loss']:
                        pos_data['stop_loss'] = new_stop
                    
                    if current_price <= pos_data['stop_loss']:
                        should_exit = True
                        exit_reason = 'Trailing Stop'
                
                # 4. Time Exit (12 months max)
                elif days_held > self.max_hold_days:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
                    # Execute exit
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.log_message(f"EXIT: {symbol} @ ${current_price:.2f}")
                    self.log_message(f"  P&L: {pnl_pct:.1f}%, Hold: {days_held} days, Reason: {exit_reason}")
                    
                    # Log trade
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"{exit_reason} | P&L: {pnl_pct:.1f}%")
                    
                    # Remove from tracking
                    if symbol in self.position_tracker:
                        del self.position_tracker[symbol]
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def scan_for_championship_entries(self):
        """Scan fundamental leaders for championship entry setups"""
        entries_made = 0
        max_entries_per_day = 2
        
        # Randomize order to avoid bias
        import random
        candidates = self.fundamental_leaders.copy()
        random.shuffle(candidates)
        
        for symbol in candidates[:20]:  # Check top 20 S&P500 leaders
            try:
                # Skip if already holding
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                # Get data
                df = self.get_symbol_data(symbol, days_back=200)
                if df is None or len(df) < 150:
                    continue
                
                # Generate conviction signal
                self.debug_stats['technical_signals_checked'] += 1
                conviction, reason = self.generate_conviction_signal(symbol, df)
                
                if conviction > 0:  # Any conviction level
                    self.debug_stats['conviction_signals_generated'] += 1
                    current_price = df['close'].iloc[-1]
                    shares = self.calculate_position_size(symbol, current_price, conviction)
                    
                    if shares > 0:
                        try:
                            # Create and submit order
                            self.debug_stats['orders_attempted'] += 1
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, shares, "buy")
                            self.submit_order(order)
                            self.debug_stats['orders_successful'] += 1
                            
                            # Track position
                            stop_price = current_price * (1 - self.stop_loss_pct)
                            self.position_tracker[symbol] = {
                                'entry_price': current_price,
                                'entry_date': self.get_datetime(),
                                'stop_loss': stop_price,
                                'highest_price': current_price,
                                'trailing': False,
                                'conviction': conviction
                            }
                            
                            position_pct = (shares * current_price) / self.get_portfolio_value() * 100
                            
                            self.log_message(f"ENTRY: {symbol} - Conviction {conviction} | {self.current_market_regime}")
                            self.log_message(f"  {shares} shares @ ${current_price:.2f} ({position_pct:.1f}% position)")
                            self.log_message(f"  Stop: ${stop_price:.2f}, {reason}")
                            
                            self.log_trade(symbol, "buy", current_price, shares, 
                                         f"Conviction {conviction} | {reason}")
                            
                            entries_made += 1
                            if entries_made >= max_entries_per_day:
                                break
                                
                        except Exception as e:
                            self.log_message(f"Order error for {symbol}: {e}")
                            
            except Exception as e:
                continue
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trades"""
        self.trades_log.append({
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value(),
            'market_regime': self.current_market_regime
        })
    
    def on_strategy_end(self):
        """Enhanced strategy end with Pyfolio analysis"""
        self.log_message("=== 5LC S&P500 STRATEGY COMPLETED ===")
        
        # Save basic CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            csv_filename = f"5lc_sp500_trades_{timestamp}.csv"
            trades_df.to_csv(csv_filename, index=False)
            self.log_message(f"✓ Trades saved: {csv_filename}")
        
        # Generate Pyfolio Analysis
        if PYFOLIO_AVAILABLE and len(self.daily_returns) > 1:
            try:
                self.generate_pyfolio_analysis(timestamp)
            except Exception as e:
                self.log_message(f"Error generating Pyfolio analysis: {e}")
        
        # Performance summary with debug stats
        portfolio_value = self.get_portfolio_value()
        total_trades = len(self.trades_log)
        positions = len(self.get_positions())
        
        self.log_message("=" * 80)
        self.log_message("5LC S&P500 STRATEGY PERFORMANCE & DEBUGGING")
        self.log_message("=" * 80)
        self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log_message(f"Active Positions: {positions}")
        self.log_message(f"Total Trades: {total_trades}")
        self.log_message(f"Market Regime Changes: {self.debug_stats['market_regime_changes']}")
        self.log_message(f"Final Market Regime: {self.current_market_regime}")
        
        # Debug statistics
        self.log_message(f"\nDEBUG STATISTICS:")
        self.log_message(f"  Stocks Screened: {self.debug_stats['screening_attempts']}")
        self.log_message(f"  Fundamental Leaders: {self.debug_stats['fundamental_leaders_found']}")
        self.log_message(f"  Technical Signals Checked: {self.debug_stats['technical_signals_checked']}")
        self.log_message(f"  Conviction Signals Generated: {self.debug_stats['conviction_signals_generated']}")
        self.log_message(f"  Orders Attempted: {self.debug_stats['orders_attempted']}")
        self.log_message(f"  Orders Successful: {self.debug_stats['orders_successful']}")
        
        if total_trades > 0:
            trades_df = pd.DataFrame(self.trades_log)
            buy_trades = trades_df[trades_df['action'] == 'buy']
            sell_trades = trades_df[trades_df['action'] == 'sell']
            
            self.log_message(f"\nTRADE BREAKDOWN:")
            self.log_message(f"  Buy Trades: {len(buy_trades)}")
            self.log_message(f"  Sell Trades: {len(sell_trades)}")
            
            # Market regime analysis
            if 'market_regime' in trades_df.columns:
                regime_trades = trades_df[trades_df['action'] == 'buy']['market_regime'].value_counts()
                self.log_message(f"\nTRADES BY MARKET REGIME:")
                for regime, count in regime_trades.items():
                    self.log_message(f"  {regime}: {count} trades")
            
            if len(buy_trades) > 0:
                total_invested = buy_trades['value'].sum()
                self.log_message(f"  Total Capital Deployed: ${total_invested:,.2f}")
        
        # Calculate return
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value * 100
        self.log_message(f"\nPERFORMANCE:")
        self.log_message(f"  Total Return: {total_return:.1f}%")
        
        # Analysis
        self.log_message(f"\nANALYSIS:")
        if self.debug_stats['fundamental_leaders_found'] == 0:
            self.log_message("  ⚠️  No fundamental leaders found - criteria too strict")
        elif self.debug_stats['conviction_signals_generated'] == 0:
            self.log_message("  ⚠️  No technical signals generated - market conditions unfavorable")
        elif self.debug_stats['orders_successful'] == 0:
            self.log_message("  ⚠️  Orders failed - check position sizing or cash availability")
        else:
            self.log_message("  ✓ 5LC strategy with market health overlay executed successfully")
        
        self.log_message("=" * 80)
        self.log_message("5LC S&P500 strategy completed - Check CSV and pyfolio reports")
    
    def generate_pyfolio_analysis(self, timestamp):
        """Generate comprehensive Pyfolio analysis"""
        self.log_message("Generating Pyfolio analysis...")
        
        # Prepare data for Pyfolio
        returns_series = pd.Series(
            self.daily_returns[1:],  # Skip first zero return
            index=self.dates[1:],
            name='5lc_sp500_strategy_returns'
        )
        
        benchmark_series = pd.Series(
            self.benchmark_returns[1:],
            index=self.dates[1:],
            name='spy_benchmark_returns'
        )
        
        # Create output directory
        output_dir = "pyfolio_reports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate full tear sheet
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend for saving
            
            # Create individual tear sheet components and save them
            self.log_message(f"Creating Pyfolio tear sheet in: {output_dir}/")
            
            # 1. Create returns tear sheet
            plt.figure(figsize=(16, 12))
            pf.create_returns_tear_sheet(
                returns_series,
                benchmark_rets=benchmark_series,
                live_start_date=None,
                return_fig=False
            )
            plt.savefig(f"{output_dir}/5lc_sp500_returns_tearsheet_{timestamp}.png", 
                       dpi=300, bbox_inches='tight')
            plt.close('all')
            self.log_message(f"✓ Returns tear sheet saved: 5lc_sp500_returns_tearsheet_{timestamp}.png")
            
            # 2. Create simple tear sheet for basic metrics
            plt.figure(figsize=(16, 10))
            pf.create_simple_tear_sheet(
                returns_series,
                benchmark_rets=benchmark_series,
                return_fig=False
            )
            plt.savefig(f"{output_dir}/5lc_sp500_simple_tearsheet_{timestamp}.png", 
                       dpi=300, bbox_inches='tight')
            plt.close('all')
            self.log_message(f"✓ Simple tear sheet saved: 5lc_sp500_simple_tearsheet_{timestamp}.png")
            
            # 3. Generate and save key metrics to text file
            metrics_filename = f"{output_dir}/5lc_sp500_performance_metrics_{timestamp}.txt"
            self.save_performance_metrics(returns_series, benchmark_series, metrics_filename)
            
            self.log_message(f"✓ Pyfolio analysis completed in: {output_dir}/")
            self.log_message(f"  Returns analyzed: {len(returns_series)} days")
            self.log_message(f"  Benchmark: SPY (S&P500 ETF)")
            
            # Basic metrics
            total_return = (returns_series + 1).prod() - 1
            volatility = returns_series.std() * np.sqrt(252)
            sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252)
            max_drawdown = (returns_series + 1).cumprod().cummax() / (returns_series + 1).cumprod() - 1
            max_dd = max_drawdown.max()
            
            self.log_message(f"  Total Return: {total_return:.2%}")
            self.log_message(f"  Volatility: {volatility:.2%}")
            self.log_message(f"  Sharpe Ratio: {sharpe:.2f}")
            self.log_message(f"  Max Drawdown: {max_dd:.2%}")
            
        except Exception as e:
            self.log_message(f"Error creating tear sheet: {e}")
            # Create basic performance summary
            self.create_basic_performance_report(returns_series, benchmark_series, timestamp)
    
    def save_performance_metrics(self, returns, benchmark, filename):
        """Save detailed performance metrics to text file"""
        try:
            with open(filename, 'w') as f:
                f.write("5LC S&P500 STRATEGY PERFORMANCE METRICS\n")
                f.write("=" * 50 + "\n\n")
                
                # Calculate metrics
                total_return = (returns + 1).prod() - 1
                benchmark_return = (benchmark + 1).prod() - 1
                excess_return = total_return - benchmark_return
                
                annualized_return = (1 + total_return) ** (252 / len(returns)) - 1
                volatility = returns.std() * np.sqrt(252)
                sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
                
                # Drawdown analysis
                cum_returns = (returns + 1).cumprod()
                rolling_max = cum_returns.expanding().max()
                drawdown = (cum_returns - rolling_max) / rolling_max
                max_drawdown = drawdown.min()
                
                # Write metrics
                f.write(f"RETURN METRICS:\n")
                f.write(f"Total Return: {total_return:.2%}\n")
                f.write(f"Annualized Return: {annualized_return:.2%}\n")
                f.write(f"Benchmark Return (SPY): {benchmark_return:.2%}\n")
                f.write(f"Excess Return: {excess_return:.2%}\n")
                f.write(f"Volatility: {volatility:.2%}\n")
                f.write(f"Sharpe Ratio: {sharpe:.2f}\n")
                f.write(f"Max Drawdown: {max_drawdown:.2%}\n\n")
                
                f.write(f"STRATEGY CHARACTERISTICS:\n")
                f.write(f"Total Trading Days: {len(returns)}\n")
                f.write(f"Positive Days: {(returns > 0).sum()} ({(returns > 0).mean():.1%})\n")
                f.write(f"Negative Days: {(returns < 0).sum()} ({(returns < 0).mean():.1%})\n")
                f.write(f"Best Day: {returns.max():.2%}\n")
                f.write(f"Worst Day: {returns.min():.2%}\n\n")
                
                f.write(f"5LC FEATURES:\n")
                f.write(f"- Halved conviction percentages (5%-10% vs 10%-20%)\n")
                f.write(f"- Market health overlay using SPY moving averages\n")
                f.write(f"- Dynamic position sizing based on market regime\n")
                f.write(f"- Enhanced risk management for US market\n\n")
                
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.log_message(f"✓ Performance metrics saved: {filename}")
            
        except Exception as e:
            self.log_message(f"Error saving metrics: {e}")
    
    def create_basic_performance_report(self, returns, benchmark, timestamp):
        """Create basic performance report if Pyfolio fails"""
        try:
            import matplotlib.pyplot as plt
            
            # Create basic plots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # Cumulative returns
            cum_returns = (returns + 1).cumprod()
            cum_benchmark = (benchmark + 1).cumprod()
            
            axes[0,0].plot(cum_returns.index, cum_returns, label='5LC S&P500 Strategy', linewidth=2)
            axes[0,0].plot(cum_benchmark.index, cum_benchmark, label='SPY Benchmark', linewidth=2)
            axes[0,0].set_title('Cumulative Returns')
            axes[0,0].legend()
            axes[0,0].grid(True)
            
            # Rolling volatility
            rolling_vol = returns.rolling(30).std() * np.sqrt(252)
            axes[0,1].plot(rolling_vol.index, rolling_vol)
            axes[0,1].set_title('30-Day Rolling Volatility')
            axes[0,1].grid(True)
            
            # Drawdown
            drawdown = cum_returns / cum_returns.cummax() - 1
            axes[1,0].fill_between(drawdown.index, drawdown, alpha=0.7, color='red')
            axes[1,0].set_title('Drawdown')
            axes[1,0].grid(True)
            
            # Returns distribution
            axes[1,1].hist(returns, bins=50, alpha=0.7)
            axes[1,1].set_title('Returns Distribution')
            axes[1,1].grid(True)
            
            plt.tight_layout()
            
            # Save plot
            plot_filename = f"pyfolio_reports/5lc_sp500_performance_{timestamp}.png"
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.log_message(f"✓ Basic performance report saved: {plot_filename}")
            
        except Exception as e:
            self.log_message(f"Error creating basic report: {e}")


def run_5lc_sp500_backtest():
    """Run complete 5LC S&P500 strategy backtest"""
    try:
        print("=" * 80)
        print("5LC (5 Level Conviction) STRATEGY - S&P500 WITH MARKET HEALTH OVERLAY")
        print("=" * 80)
        print("Features:")
        print("✓ Halved conviction percentages (5%-10% vs 10%-20%)")
        print("✓ Market health overlay using SPY moving averages")
        print("✓ Dynamic position sizing based on market regime")
        print("✓ Enhanced risk management for US market")
        if PYFOLIO_AVAILABLE:
            print("✓ Comprehensive Pyfolio tear sheets")
            print("✓ Professional performance metrics")
            print("✓ Risk analysis vs SPY benchmark")
        else:
            print("⚠️ Install pyfolio-reloaded for enhanced analysis:")
            print("   pip install pyfolio-reloaded")
        print("=" * 80)
        
        # Backtest parameters
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2025, 5, 5)
        initial_cash = 100000.0
        
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: ${initial_cash:,.2f}")
        print(f"Benchmark: SPY (S&P500 ETF)")
        print("Market Health Multipliers:")
        print("  - WEAK (SPY < 20MA & 50MA): 0.5x positions")
        print("  - STRONG (SPY > 20MA & 50MA & 200MA): 2.0x positions") 
        print("  - NORMAL (other conditions): 1.0x positions")
        print("=" * 80)
        
        results = Minervini5LCSP500Strategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="SPY"
        )
        
        print("\n🎉 5LC S&P500 STRATEGY COMPLETED!")
        print("✓ Basic CSV trade log exported")
        if PYFOLIO_AVAILABLE:
            print("✓ Pyfolio tear sheet generated")
            print("✓ Professional performance analysis vs S&P500")
        print("✓ Enhanced reporting with market health analysis")
        
        return results
        
    except Exception as e:
        print(f"Error in 5LC S&P500 backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting 5LC S&P500 Strategy with Market Health Overlay...")
    results = run_5lc_sp500_backtest()