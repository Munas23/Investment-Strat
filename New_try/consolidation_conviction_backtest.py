"""
Consolidation Conviction Strategy - Based on 5LC Structure
=========================================================

Post-move consolidation pattern detection strategy using the proven 5LC backtesting framework.
Targets stocks AFTER big moves during consolidation periods with:
1. 30%+ 3-6 month performance requirement
2. Low/contracting ATR analysis 
3. Reduced recent momentum weighting
4. Professional risk management optimized for consolidation patterns
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
    print("Pyfolio-reloaded loaded successfully")
except ImportError:
    PYFOLIO_AVAILABLE = False
    print("WARNING: Pyfolio-reloaded not installed. Install with: pip install pyfolio-reloaded")

warnings.filterwarnings('ignore')

class ConsolidationConvictionStrategy(Strategy):
    """
    Consolidation Conviction Strategy based on 5LC framework
    
    Features:
    1. Post-move consolidation pattern detection
    2. 30%+ 3-6 month performance requirement
    3. ATR contraction analysis for consolidation identification  
    4. Dynamic position sizing (15%-35% based on conviction)
    5. Enhanced risk management optimized for consolidation patterns
    """
    
    def initialize(self):
        """Initialize strategy parameters - based on 5LC structure"""
        self.sleeptime = "1D"
        
        # Consolidation-specific parameters
        self.max_positions = 8
        self.min_position_size = 0.15  # 15% minimum 
        self.max_position_size = 0.35  # 35% maximum
        self.stop_loss_pct = 0.08  # 8% stop (tighter for consolidation)
        self.profit_target = 0.50  # 40% target (realistic for post-move)
        
        # Consolidation criteria
        self.min_3month_gain = 30.0  # Minimum 30% gain over 3-6 months
        self.min_price = 1.00  # Higher minimum price for quality
        self.min_avg_volume = 100000  # Higher volume requirement
        
        # Risk management for consolidation patterns
        self.trail_profit_trigger = 0.15  # Earlier trailing (15% vs 20%)
        self.trail_percent = 0.10  # Tighter trailing (10% vs 12%)
        self.max_hold_days = 180  # Shorter holds (6 months vs 12)
        
        # Universe - focus on liquid US stocks (same as 5LC approach)
        self.universe_symbols = self.get_universe_symbols()
        
        # Performance tracking for Pyfolio (same as 5LC)
        self.daily_returns = []
        self.portfolio_values = []
        self.benchmark_returns = []
        self.dates = []
        
        # Trading tracking (same structure as 5LC)
        self.consolidation_leaders = []
        self.last_screening_date = None
        self.screening_frequency = 14  # Screen every 2 weeks
        self.trades_log = []
        self.position_tracker = {}
        
        # Debug tracking (same as 5LC)
        self.debug_stats = {
            'screening_attempts': 0,
            'consolidation_patterns_found': 0,
            'technical_signals_checked': 0,
            'conviction_signals_generated': 0,
            'orders_attempted': 0,
            'orders_successful': 0
        }
        
        self.log_message("=== CONSOLIDATION CONVICTION STRATEGY ===")
        self.log_message(f"Universe: {len(self.universe_symbols)} liquid stocks")
        self.log_message(f"Focus: Post-move consolidation patterns")
        self.log_message(f"Min 3-6M gain: {self.min_3month_gain}%")
        self.log_message(f"Pyfolio Integration: {'Enabled' if PYFOLIO_AVAILABLE else 'Disabled'}")
        self.log_message("=" * 70)
    
    def get_universe_symbols(self):
        """Get universe of liquid stocks - same approach as 5LC"""
        try:
            # Get S&P 500 from Wikipedia (same as 5LC)
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            symbols = table['Symbol'].tolist()
            
            # Clean symbols (same as 5LC)
            clean_symbols = []
            for symbol in symbols:
                clean_symbol = symbol.replace('.', '-')
                if not symbol.startswith('$') and len(symbol) <= 6:
                    clean_symbols.append(clean_symbol)
            
            self.log_message(f"Successfully loaded {len(clean_symbols)} S&P 500 symbols")
            return clean_symbols
            
        except Exception as e:
            self.log_message(f"Error loading S&P 500 symbols: {e}")
            # Fallback to major stocks (same as 5LC)
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT',
                'PG', 'UNH', 'JPM', 'HD', 'MA', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX',
                'COST', 'KO', 'PFE', 'XOM', 'BAC', 'ABBV', 'ABT', 'ACN', 'TMO', 'LLY',
                'AVGO', 'GOOG', 'BRK-B', 'CVX', 'ORCL', 'CSCO', 'AZN', 'NKE', 'SCHW'
            ]
    
    def calculate_atr_series(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR series for consolidation analysis"""
        try:
            if len(df) < period + 1:
                return pd.Series(index=df.index, dtype=float)
            
            df = df.copy()
            df['prev_close'] = df['close'].shift(1)
            
            # True Range components
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['prev_close'] - df['low'])
            df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # ATR as rolling mean
            atr_series = df['true_range'].rolling(period).mean()
            
            return atr_series
            
        except Exception as e:
            self.log_message(f"Error calculating ATR series: {e}")
            return pd.Series(index=df.index, dtype=float)
    
    def analyze_consolidation_pattern(self, df: pd.DataFrame) -> dict:
        """Analyze consolidation characteristics - your scanner logic"""
        try:
            if len(df) < 100:
                return {'consolidation_score': 0, 'details': 'Insufficient data'}
            
            current_price = df['close'].iloc[-1]
            
            # Calculate ATR series
            atr_14 = self.calculate_atr_series(df, 14)
            
            # Get recent periods for analysis
            recent_2weeks = slice(-10, None)
            recent_4weeks = slice(-20, None)
            older_period = slice(-90, -30)
            
            # ATR Analysis - Key consolidation indicator
            recent_atr_2w = atr_14.iloc[recent_2weeks].mean() if len(atr_14.iloc[recent_2weeks]) > 0 else 0
            recent_atr_4w = atr_14.iloc[recent_4weeks].mean() if len(atr_14.iloc[recent_4weeks]) > 0 else 0
            older_atr = atr_14.iloc[older_period].mean() if len(atr_14.iloc[older_period]) > 0 else 0
            
            # ATR contraction ratios
            atr_contraction_2w = recent_atr_2w / older_atr if older_atr > 0 else 1
            atr_contraction_4w = recent_atr_4w / older_atr if older_atr > 0 else 1
            
            # Performance calculations - look back to capture the big move
            if len(df) >= 90:
                price_3m_ago = df['close'].iloc[-90]
                gain_3m = ((current_price / price_3m_ago) - 1) * 100 if price_3m_ago > 0 else 0
            else:
                gain_3m = 0
                
            # Look further back for 6M to capture pre-consolidation gains
            if len(df) >= 200:  # ~8 months back to capture pre-move price
                price_6m_ago = df['close'].iloc[-200]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
            elif len(df) >= 180:
                price_6m_ago = df['close'].iloc[-180]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
            elif len(df) >= 130:
                price_6m_ago = df['close'].iloc[-130]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
            else:
                gain_6m = gain_3m * 2.0 if gain_3m > 0 else 0
            
            # Recent performance (should be lower for consolidation)
            if len(df) >= 10:
                price_2w_ago = df['close'].iloc[-10]
                gain_2w = ((current_price / price_2w_ago) - 1) * 100 if price_2w_ago > 0 else 0
            else:
                gain_2w = 0
                
            if len(df) >= 20:
                price_4w_ago = df['close'].iloc[-20]
                gain_4w = ((current_price / price_4w_ago) - 1) * 100 if price_4w_ago > 0 else 0
            else:
                gain_4w = 0
            
            # ATR as percentage of price
            recent_atr_pct_2w = (recent_atr_2w / current_price * 100) if current_price > 0 else 0
            recent_atr_pct_4w = (recent_atr_4w / current_price * 100) if current_price > 0 else 0
            
            return {
                'gain_3m': gain_3m,
                'gain_6m': gain_6m,
                'gain_2w': gain_2w,
                'gain_4w': gain_4w,
                'recent_atr_pct_2w': recent_atr_pct_2w,
                'recent_atr_pct_4w': recent_atr_pct_4w,
                'atr_contraction_2w': atr_contraction_2w,
                'atr_contraction_4w': atr_contraction_4w,
                'current_atr_14': atr_14.iloc[-1] if len(atr_14) > 0 else 0
            }
            
        except Exception as e:
            self.log_message(f"Error analyzing consolidation pattern: {e}")
            return {'consolidation_score': 0, 'error': str(e)}
    
    def generate_consolidation_conviction_signal(self, symbol: str, df: pd.DataFrame):
        """Generate consolidation conviction signal - your scanner logic"""
        try:
            if len(df) < 150:
                return 0, "Insufficient historical data", {}
            
            current_price = df['close'].iloc[-1]
            
            # Get consolidation analysis
            consolidation_data = self.analyze_consolidation_pattern(df)
            
            # Check primary filter: 3-6 month performance
            medium_term_gain = max(consolidation_data.get('gain_3m', 0), consolidation_data.get('gain_6m', 0))
            if medium_term_gain < self.min_3month_gain:
                return 0, f"Insufficient 3-6M gain: {medium_term_gain:.1f}% < {self.min_3month_gain}%", consolidation_data
            
            conviction = 0
            details = consolidation_data.copy()
            
            # Factor 1: Medium-term Performance Strength (0-30 points)
            perf_points = 0
            if medium_term_gain >= 100:  # 100%+ gain
                perf_points = 30
            elif medium_term_gain >= 70:  # 70%+ gain
                perf_points = 25
            elif medium_term_gain >= 50:  # 50%+ gain
                perf_points = 20
            elif medium_term_gain >= 30:  # 30%+ gain (minimum)
                perf_points = 15
            
            conviction += perf_points
            details['performance_points'] = perf_points
            details['medium_term_gain'] = medium_term_gain
            
            # Factor 2: ATR Consolidation Analysis (0-35 points)
            atr_points = 0
            best_contraction = min(
                consolidation_data.get('atr_contraction_2w', 1),
                consolidation_data.get('atr_contraction_4w', 1)
            )
            
            if best_contraction <= 0.6:  # ATR contracted to 60% or less
                atr_points += 20
            elif best_contraction <= 0.8:  # ATR contracted to 80% or less
                atr_points += 15
            elif best_contraction <= 1.0:  # ATR staying same or lower
                atr_points += 10
            elif best_contraction <= 1.2:  # ATR only slightly higher
                atr_points += 5
            
            # Absolute ATR level
            recent_atr_pct = consolidation_data.get('recent_atr_pct_4w', 10)
            if recent_atr_pct <= 2.0:  # Very low volatility
                atr_points += 15
            elif recent_atr_pct <= 3.5:  # Low-moderate volatility
                atr_points += 10
            elif recent_atr_pct <= 5.0:  # Moderate volatility
                atr_points += 5
            
            conviction += atr_points
            details['atr_points'] = atr_points
            details['best_atr_contraction'] = best_contraction
            
            # Factor 3: Recent Momentum Dampening (0-20 points)
            momentum_points = 0
            recent_gain_2w = consolidation_data.get('gain_2w', 0)
            recent_gain_4w = consolidation_data.get('gain_4w', 0)
            avg_recent_gain = (abs(recent_gain_2w) + abs(recent_gain_4w)) / 2
            
            if avg_recent_gain <= 2:  # Very low recent movement
                momentum_points = 20
            elif avg_recent_gain <= 5:  # Low recent movement
                momentum_points = 15
            elif avg_recent_gain <= 8:  # Moderate recent movement
                momentum_points = 10
            elif avg_recent_gain <= 12:  # Some recent movement
                momentum_points = 5
            
            conviction += momentum_points
            details['momentum_points'] = momentum_points
            details['avg_recent_gain'] = avg_recent_gain
            details['total_conviction'] = conviction
            
            # Convert to conviction level (0-100 -> 0-5)
            if conviction >= 80:
                level = 5
                reason = f"MAX: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
            elif conviction >= 65:
                level = 4
                reason = f"HIGH: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
            elif conviction >= 50:
                level = 3
                reason = f"GOOD: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
            elif conviction >= 35:
                level = 2
                reason = f"FAIR: {conviction}, 3-6M: {medium_term_gain:.1f}%"
            else:
                level = 0
                reason = f"No signal: {conviction}"
            
            return level, reason, details
            
        except Exception as e:
            self.log_message(f"Error generating consolidation signal for {symbol}: {e}")
            return 0, f"Error: {e}", {}
    
    def get_symbol_data(self, symbol, days_back=250):
        """Get symbol data - same as 5LC approach"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            return bars.df if bars and hasattr(bars, 'df') and len(bars.df) > 0 else None
        except Exception as e:
            self.log_message(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, symbol, price, conviction_level):
        """Calculate position size - based on 5LC approach"""
        try:
            portfolio_value = self.get_portfolio_value()
            
            # Position size by conviction level (optimized for consolidation)
            position_pct = {
                2: 0.15,   # 15% - fair consolidation
                3: 0.20,   # 20% - good consolidation  
                4: 0.28,   # 28% - high consolidation
                5: 0.35    # 35% - max consolidation
            }.get(conviction_level, 0.15)
            
            # Ensure we don't exceed limits
            final_position_pct = min(position_pct, self.max_position_size)
            final_position_pct = max(final_position_pct, self.min_position_size)
            
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
    
    def on_trading_iteration(self):
        """Main trading logic - same structure as 5LC"""
        try:
            current_date = self.get_datetime()
            portfolio_value = self.get_portfolio_value()
            
            # Track performance for Pyfolio (same as 5LC)
            self.track_daily_performance(current_date, portfolio_value)
            
            # Update consolidation leaders periodically
            self.update_consolidation_leaders()
            
            # Check exits first (same as 5LC)
            self.check_consolidation_exits()
            
            # Look for new entries if we have room
            positions = self.get_positions()
            if len(positions) < self.max_positions and self.consolidation_leaders:
                self.scan_for_consolidation_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def track_daily_performance(self, date, portfolio_value):
        """Track daily performance - same as 5LC"""
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
            
            # Get benchmark return (SPY) - same as 5LC
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
    
    def update_consolidation_leaders(self):
        """Update list of consolidation candidates - based on 5LC screening"""
        current_date = self.get_datetime()
        
        # Check if we need to re-screen (same timing as 5LC)
        if (self.last_screening_date is None or 
            (current_date - self.last_screening_date).days >= self.screening_frequency):
            
            self.log_message(f"Screening for consolidation patterns...")
            
            # Sample subset for faster screening (same as 5LC)
            sample_size = min(100, len(self.universe_symbols))
            symbols_to_screen = self.universe_symbols[:sample_size]
            
            leaders = []
            screening_count = 0
            
            for symbol in symbols_to_screen:
                try:
                    self.debug_stats['screening_attempts'] += 1
                    
                    # Get data
                    df = self.get_symbol_data(symbol, days_back=250)
                    if df is None or len(df) < 150:
                        continue
                    
                    current_price = df['close'].iloc[-1]
                    avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                    
                    # Basic filters (same as 5LC approach)
                    if (current_price >= self.min_price and 
                        avg_volume >= self.min_avg_volume):
                        
                        # Check for consolidation pattern
                        conviction, reason, details = self.generate_consolidation_conviction_signal(symbol, df)
                        
                        if conviction >= 2:  # Only conviction level 2+ 
                            leaders.append({
                                'symbol': symbol,
                                'conviction': conviction,
                                'reason': reason,
                                'details': details
                            })
                            self.debug_stats['consolidation_patterns_found'] += 1
                        
                        screening_count += 1
                        
                        # Progress update (same as 5LC)
                        if screening_count % 10 == 0:
                            self.log_message(f"  Screened {screening_count}/{len(symbols_to_screen)} stocks...")
                    
                except Exception as e:
                    continue
            
            # Update leaders list
            self.consolidation_leaders = [leader['symbol'] for leader in leaders]
            self.last_screening_date = current_date
            
            self.log_message(f"Consolidation screening complete:")
            self.log_message(f"  Screened: {screening_count} stocks")
            self.log_message(f"  Consolidation patterns found: {len(self.consolidation_leaders)}")
            
            # Log top consolidation candidates
            for leader in sorted(leaders, key=lambda x: x['conviction'], reverse=True)[:5]:
                details = leader['details']
                self.log_message(f"    {leader['symbol']}: Conv {leader['conviction']} - "
                               f"{details.get('medium_term_gain', 0):.1f}% 3-6M")
    
    def scan_for_consolidation_entries(self):
        """Scan for entries - same structure as 5LC"""
        entries_made = 0
        max_entries_per_day = 2
        
        # Randomize order to avoid bias (same as 5LC)
        import random
        candidates = self.consolidation_leaders.copy()
        random.shuffle(candidates)
        
        for symbol in candidates[:15]:  # Check top 15 consolidation leaders
            try:
                # Skip if already holding
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                # Get fresh data
                df = self.get_symbol_data(symbol, days_back=250)
                if df is None or len(df) < 150:
                    continue
                
                # Generate conviction signal
                self.debug_stats['technical_signals_checked'] += 1
                conviction, reason, details = self.generate_consolidation_conviction_signal(symbol, df)
                
                if conviction >= 2:  # Minimum consolidation conviction
                    self.debug_stats['conviction_signals_generated'] += 1
                    current_price = df['close'].iloc[-1]
                    shares = self.calculate_position_size(symbol, current_price, conviction)
                    
                    if shares > 0:
                        try:
                            # Create and submit order (same as 5LC)
                            self.debug_stats['orders_attempted'] += 1
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, shares, "buy")
                            self.submit_order(order)
                            self.debug_stats['orders_successful'] += 1
                            
                            # Track position (same as 5LC structure)
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
                            
                            self.log_message(f"CONSOLIDATION ENTRY: {symbol} - Conviction {conviction}")
                            self.log_message(f"  {shares} shares @ ${current_price:.2f} ({position_pct:.1f}% position)")
                            self.log_message(f"  Stop: ${stop_price:.2f}, 3-6M gain: {details.get('medium_term_gain', 0):.1f}%")
                            
                            self.log_trade(symbol, "buy", current_price, shares, reason)
                            
                            entries_made += 1
                            if entries_made >= max_entries_per_day:
                                break
                                
                        except Exception as e:
                            self.log_message(f"Order error for {symbol}: {e}")
                            
            except Exception as e:
                continue
    
    def check_consolidation_exits(self):
        """Check exits - same structure as 5LC but optimized for consolidation"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
                # Get position tracking data (same as 5LC)
                if symbol not in self.position_tracker:
                    # Initialize tracking for existing position
                    self.position_tracker[symbol] = {
                        'entry_price': current_price,
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
                
                # 1. Stop Loss (8% for consolidation)
                if pnl_pct < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # 2. Profit Target (40% for consolidation)
                elif pnl_pct > self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'PROFIT TARGET'
                
                # 3. Trailing Stop (after 15% gain for consolidation)
                elif pnl_pct > self.trail_profit_trigger * 100:
                    if not pos_data['trailing']:
                        pos_data['trailing'] = True
                        self.log_message(f"CONSOLIDATION TRAILING activated for {symbol} at {pnl_pct:.1f}% gain")
                    
                    new_stop = highest_price * (1 - self.trail_percent)
                    if new_stop > pos_data['stop_loss']:
                        pos_data['stop_loss'] = new_stop
                    
                    if current_price <= pos_data['stop_loss']:
                        should_exit = True
                        exit_reason = 'Trailing Stop'
                
                # 4. Time Exit (6 months max for consolidation)
                elif days_held > self.max_hold_days:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
                    # Execute exit (same as 5LC)
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.log_message(f"CONSOLIDATION EXIT: {symbol} @ ${current_price:.2f}")
                    self.log_message(f"  P&L: {pnl_pct:.1f}%, Hold: {days_held} days, Reason: {exit_reason}")
                    
                    # Log trade
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"{exit_reason} | P&L: {pnl_pct:.1f}%")
                    
                    # Remove from tracking
                    if symbol in self.position_tracker:
                        del self.position_tracker[symbol]
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trades - same as 5LC"""
        self.trades_log.append({
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value(),
            'strategy': 'consolidation_conviction'
        })
    
    def on_strategy_end(self):
        """Enhanced strategy end - same structure as 5LC"""
        self.log_message("=== CONSOLIDATION CONVICTION STRATEGY COMPLETED ===")
        
        # Save trades CSV (same as 5LC)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            csv_filename = f"consolidation_conviction_trades_{timestamp}.csv"
            trades_df.to_csv(csv_filename, index=False)
            self.log_message(f"Trades saved: {csv_filename}")
        
        # Generate Pyfolio Analysis (same as 5LC)
        if PYFOLIO_AVAILABLE and len(self.daily_returns) > 1:
            try:
                self.generate_pyfolio_analysis(timestamp)
            except Exception as e:
                self.log_message(f"Error generating Pyfolio analysis: {e}")
        
        # Performance summary (same structure as 5LC)
        portfolio_value = self.get_portfolio_value()
        total_trades = len(self.trades_log)
        positions = len(self.get_positions())
        
        self.log_message("=" * 80)
        self.log_message("CONSOLIDATION CONVICTION STRATEGY PERFORMANCE")
        self.log_message("=" * 80)
        self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log_message(f"Active Positions: {positions}")
        self.log_message(f"Total Trades: {total_trades}")
        
        # Debug statistics (same as 5LC)
        self.log_message(f"\nCONSOLIDATION SCREENING STATISTICS:")
        self.log_message(f"  Stocks Screened: {self.debug_stats['screening_attempts']}")
        self.log_message(f"  Consolidation Patterns Found: {self.debug_stats['consolidation_patterns_found']}")
        self.log_message(f"  Technical Signals Checked: {self.debug_stats['technical_signals_checked']}")
        self.log_message(f"  Conviction Signals Generated: {self.debug_stats['conviction_signals_generated']}")
        self.log_message(f"  Orders Attempted: {self.debug_stats['orders_attempted']}")
        self.log_message(f"  Orders Successful: {self.debug_stats['orders_successful']}")
        
        # Calculate return (same as 5LC)
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value * 100
        self.log_message(f"\nPERFORMANCE:")
        self.log_message(f"  Total Return: {total_return:.1f}%")
        
        self.log_message("=" * 80)
        self.log_message("Consolidation Conviction strategy completed")
    
    def generate_pyfolio_analysis(self, timestamp):
        """Generate Pyfolio analysis - same as 5LC"""
        if not PYFOLIO_AVAILABLE:
            return
            
        self.log_message("Generating Pyfolio analysis...")
        
        # Prepare data (same as 5LC)
        returns_series = pd.Series(
            self.daily_returns[1:],
            index=self.dates[1:],
            name='consolidation_conviction_returns'
        )
        
        benchmark_series = pd.Series(
            self.benchmark_returns[1:],
            index=self.dates[1:],
            name='spy_benchmark_returns'
        )
        
        # Create output directory (same as 5LC)
        output_dir = "pyfolio_reports"
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            # Create returns tear sheet (same as 5LC)
            plt.figure(figsize=(16, 12))
            pf.create_returns_tear_sheet(
                returns_series,
                benchmark_rets=benchmark_series,
                live_start_date=None,
                return_fig=False
            )
            plt.savefig(f"{output_dir}/consolidation_conviction_returns_tearsheet_{timestamp}.png", 
                       dpi=300, bbox_inches='tight')
            plt.close('all')
            
            self.log_message(f"Consolidation strategy Pyfolio analysis saved")
            
            # Basic metrics (same as 5LC)
            total_return = (returns_series + 1).prod() - 1
            volatility = returns_series.std() * np.sqrt(252)
            sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252)
            
            self.log_message(f"  Total Return: {total_return:.2%}")
            self.log_message(f"  Volatility: {volatility:.2%}")
            self.log_message(f"  Sharpe Ratio: {sharpe:.2f}")
            
        except Exception as e:
            self.log_message(f"Error creating Pyfolio analysis: {e}")


def run_consolidation_conviction_backtest():
    """Run complete Consolidation Conviction strategy backtest - same structure as 5LC"""
    try:
        print("=" * 80)
        print("CONSOLIDATION CONVICTION STRATEGY BACKTEST")
        print("=" * 80)
        print("Strategy Focus:")
        print("Post-move consolidation pattern detection")
        print("30%+ 3-6 month performance requirement")
        print("ATR contraction analysis for consolidation identification")
        print("Dynamic position sizing (15%-35% based on conviction)")
        print("Enhanced risk management optimized for consolidation")
        print("Tighter stops (8%) and realistic targets (40%)")
        if PYFOLIO_AVAILABLE:
            print("Comprehensive Pyfolio analysis")
        else:
            print("WARNING: Install pyfolio-reloaded for enhanced analysis:")
            print("   pip install pyfolio-reloaded")
        print("=" * 80)
        
        # Backtest parameters (same structure as 5LC)
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2024, 12, 31)
        initial_cash = 100000.0
        
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: ${initial_cash:,.2f}")
        print(f"Benchmark: SPY (S&P500 ETF)")
        print(f"Universe: S&P 500 stocks")
        print("Focus: Post-move consolidation patterns")
        print("Min 3-6M gain: 30%+")
        print("=" * 80)
        
        # Run backtest (exactly same as 5LC)
        results = ConsolidationConvictionStrategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="SPY"
        )
        
        print("\nCONSOLIDATION CONVICTION STRATEGY COMPLETED!")
        print("Trade log exported with consolidation metrics")
        if PYFOLIO_AVAILABLE:
            print("Pyfolio tear sheet generated")
        print("Consolidation pattern analysis completed")
        
        return results
        
    except Exception as e:
        print(f"Error in Consolidation Conviction backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting Consolidation Conviction Strategy Backtest...")
    results = run_consolidation_conviction_backtest()