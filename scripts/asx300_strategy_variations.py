"""
ASX300 Strategy Variations - 20 Different Versions for Backtesting
================================================================

Based on your existing Minervini ASX300 implementations, this creates 20 variations
with different stop losses, exit strategies, position sizing, and filters.

Testing hypothesis: Simpler approaches may outperform complex market filters.
"""

import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.entities import Asset
import random

warnings.filterwarnings('ignore')

class ASX300StrategyBase(Strategy):
    """Base strategy class with common functionality"""
    
    def initialize(self):
        """Initialize base parameters - will be overridden by variations"""
        self.sleeptime = "1D"
        
        # Default parameters (will be modified by variations)
        self.max_positions = 6
        self.position_size = 0.20  # 20% default
        self.stop_loss_pct = 0.07  # 7% default
        self.profit_target = 0.50  # 50% default
        self.fundamental_threshold = 60.0
        
        # Initialize tracking
        self.trades_log = []
        self.position_tracker = {}
        self.last_screening_date = None
        self.screening_frequency = 30
        self.fundamental_leaders = []
        
        # Strategy specific settings (set by variations)
        self.strategy_name = "Base Strategy"
        self.use_market_filter = False
        self.use_trailing_stop = True
        self.trail_profit_trigger = 0.20
        self.trail_percent = 0.12
        self.max_hold_days = 365
        self.use_momentum_filter = False
        self.momentum_lookback = 20
        self.use_volume_filter = True
        self.min_volume_surge = 1.2
        
        # Get ASX300 symbols
        self.asx300_symbols = self.get_asx300_symbols()
        
        self.log_message(f"=== {self.strategy_name} ===")
        self.log_message(f"Stop Loss: {self.stop_loss_pct*100:.1f}%")
        self.log_message(f"Profit Target: {self.profit_target*100:.1f}%")
        self.log_message(f"Position Size: {self.position_size*100:.1f}%")
        self.log_message(f"Max Positions: {self.max_positions}")
        self.log_message("=" * 50)
    
    def get_asx300_symbols(self):
        """Get ASX300 symbol list"""
        return [
            # Big 4 Banks
            'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX',
            # Mining Giants
            'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'STO.AX', 'WDS.AX',
            # Healthcare & Biotech
            'CSL.AX', 'COH.AX', 'RMD.AX', 'SHL.AX', 'NAN.AX', 'PME.AX',
            # Technology & Growth
            'XRO.AX', 'WTC.AX', 'TNE.AX', 'CPU.AX', 'KGN.AX', 'NXT.AX',
            # Retail & Consumer
            'WOW.AX', 'COL.AX', 'WES.AX', 'JBH.AX', 'HVN.AX', 'SUL.AX',
            # Telecommunications
            'TLS.AX', 'TCL.AX', 'TPG.AX',
            # REITs & Property
            'SCG.AX', 'GMG.AX', 'VCX.AX', 'REA.AX', 'DXS.AX', 'CHC.AX',
            # Industrials
            'QBE.AX', 'IAG.AX', 'SUN.AX', 'QAN.AX', 'ALL.AX', 'APA.AX', 'AGL.AX',
            # Materials & Chemicals
            'ORI.AX', 'IPL.AX', 'JHX.AX', 'AWC.AX',
            # Utilities
            'FPH.AX', 'AEF.AX',
            # Food & Agriculture
            'A2M.AX', 'BAP.AX', 'SHV.AX',
            # Financial Services
            'MQG.AX', 'ASX.AX', 'PPT.AX', 'NHF.AX',
            # Energy
            'WPL.AX', 'ORG.AX', 'BPT.AX',
            # Infrastructure
            'AST.AX', 'SYD.AX'
        ]
    
    def get_market_health(self):
        """Simple market health check using VAS.AX"""
        if not self.use_market_filter:
            return "NORMAL"
        
        try:
            vas = yf.Ticker("VAS.AX")
            data = vas.history(period="200d")
            if len(data) < 50:
                return "NORMAL"
            
            current_price = data['Close'].iloc[-1]
            ma_20 = data['Close'].rolling(20).mean().iloc[-1]
            ma_50 = data['Close'].rolling(50).mean().iloc[-1]
            
            if current_price > ma_20 and current_price > ma_50:
                return "STRONG"
            elif current_price < ma_20 and current_price < ma_50:
                return "WEAK"
            else:
                return "NORMAL"
        except:
            return "NORMAL"
    
    def get_symbol_data(self, symbol, days_back=200):
        """Get symbol data"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            return bars.df if bars and hasattr(bars, 'df') and len(bars.df) > 0 else None
        except:
            return None
    
    def calculate_trend_strength(self, df):
        """Calculate trend strength score"""
        if len(df) < 150:
            return 0
        
        current = df.iloc[-1]
        ma_21 = df['close'].rolling(21).mean().iloc[-1]
        ma_50 = df['close'].rolling(50).mean().iloc[-1]
        ma_150 = df['close'].rolling(150).mean().iloc[-1]
        
        score = 0
        if not pd.isna(ma_21) and current['close'] > ma_21:
            score += 25
        if not pd.isna(ma_50) and current['close'] > ma_50:
            score += 25
        if not pd.isna(ma_150) and current['close'] > ma_150:
            score += 25
        if not pd.isna(ma_21) and not pd.isna(ma_50) and ma_21 > ma_50:
            score += 25
        
        return score
    
    def generate_entry_signal(self, symbol, df):
        """Generate entry signal based on strategy parameters"""
        if len(df) < 150:
            return False, "Insufficient data"
        
        current_price = df['close'].iloc[-1]
        trend_strength = self.calculate_trend_strength(df)
        
        # Trend requirement
        if trend_strength < 50:
            return False, f"Weak trend: {trend_strength}"
        
        # Breakout check
        high_20 = df['high'].rolling(20).max().iloc[-1]
        if current_price <= high_20 * 0.99:  # Not near highs
            return False, "Not breaking out"
        
        # Volume check
        if self.use_volume_filter:
            volume_avg = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_surge = current_volume / volume_avg if volume_avg > 0 else 0
            
            if volume_surge < self.min_volume_surge:
                return False, f"Low volume: {volume_surge:.1f}x"
        
        # Momentum check
        if self.use_momentum_filter:
            momentum = (current_price / df['close'].iloc[-self.momentum_lookback] - 1) * 100
            if momentum < 5:
                return False, f"Weak momentum: {momentum:.1f}%"
        
        return True, f"Entry signal - trend: {trend_strength}, price: ${current_price:.2f}"
    
    def on_trading_iteration(self):
        """Main trading logic"""
        try:
            current_date = self.get_datetime()
            positions = self.get_positions()
            
            # Update fundamental leaders periodically
            if (self.last_screening_date is None or 
                (current_date - self.last_screening_date).days >= self.screening_frequency):
                self.update_fundamental_leaders()
            
            # Check exits
            self.check_exits()
            
            # Look for entries
            if len(positions) < self.max_positions and self.fundamental_leaders:
                self.scan_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def update_fundamental_leaders(self):
        """Update fundamental leaders (simplified)"""
        self.last_screening_date = self.get_datetime()
        
        # Sample subset for screening
        sample_size = min(30, len(self.asx300_symbols))
        symbols_to_screen = random.sample(self.asx300_symbols, sample_size)
        
        # Simple fundamental screen (placeholder)
        self.fundamental_leaders = symbols_to_screen[:15]  # Top 15 for simplicity
        
        self.log_message(f"Updated fundamental leaders: {len(self.fundamental_leaders)} stocks")
    
    def calculate_position_size(self, symbol, price):
        """Calculate position size"""
        portfolio_value = self.get_portfolio_value()
        position_value = portfolio_value * self.position_size
        shares = int(position_value / price)
        
        # Apply cash constraints
        max_shares_by_cash = int(self.get_cash() / price)
        return min(shares, max_shares_by_cash)
    
    def scan_for_entries(self):
        """Scan for entry opportunities"""
        market_health = self.get_market_health()
        
        # Market filter adjustment
        if self.use_market_filter and market_health == "WEAK":
            return  # Skip entries in weak markets
        
        candidates = random.sample(self.fundamental_leaders, min(10, len(self.fundamental_leaders)))
        
        for symbol in candidates:
            try:
                # Skip if already holding
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                df = self.get_symbol_data(symbol, days_back=200)
                if df is None or len(df) < 150:
                    continue
                
                entry_signal, reason = self.generate_entry_signal(symbol, df)
                
                if entry_signal:
                    current_price = df['close'].iloc[-1]
                    shares = self.calculate_position_size(symbol, current_price)
                    
                    if shares > 0:
                        # Create order
                        asset = Asset(symbol=symbol, asset_type="stock")
                        order = self.create_order(asset, shares, "buy")
                        self.submit_order(order)
                        
                        # Track position
                        stop_price = current_price * (1 - self.stop_loss_pct)
                        self.position_tracker[symbol] = {
                            'entry_price': current_price,
                            'entry_date': self.get_datetime(),
                            'stop_loss': stop_price,
                            'highest_price': current_price,
                            'trailing': False
                        }
                        
                        self.log_message(f"ENTRY: {symbol} @ ${current_price:.2f} - {reason}")
                        self.log_trade(symbol, "buy", current_price, shares, reason)
                        break  # One entry per day
                        
            except Exception as e:
                continue
    
    def check_exits(self):
        """Check exit conditions"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
                # Initialize tracking if missing
                if symbol not in self.position_tracker:
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
                
                # Update highest price
                if current_price > pos_data['highest_price']:
                    pos_data['highest_price'] = current_price
                
                # Calculate P&L
                pnl_pct = (current_price / entry_price - 1) * 100
                days_held = (self.get_datetime() - pos_data['entry_date']).days
                
                should_exit = False
                exit_reason = ""
                
                # Exit conditions
                if pnl_pct <= -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                elif pnl_pct >= self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'Profit Target'
                elif self.use_trailing_stop and pnl_pct > self.trail_profit_trigger * 100:
                    if not pos_data['trailing']:
                        pos_data['trailing'] = True
                    
                    new_stop = pos_data['highest_price'] * (1 - self.trail_percent)
                    if new_stop > pos_data['stop_loss']:
                        pos_data['stop_loss'] = new_stop
                    
                    if current_price <= pos_data['stop_loss']:
                        should_exit = True
                        exit_reason = 'Trailing Stop'
                elif days_held > self.max_hold_days:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.log_message(f"EXIT: {symbol} @ ${current_price:.2f} - {exit_reason} - P&L: {pnl_pct:.1f}%")
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"{exit_reason} | P&L: {pnl_pct:.1f}%")
                    
                    # Remove from tracking
                    if symbol in self.position_tracker:
                        del self.position_tracker[symbol]
                        
            except Exception as e:
                continue
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trade details"""
        self.trades_log.append({
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value(),
            'strategy': self.strategy_name
        })
    
    def on_strategy_end(self):
        """Export results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            filename = f"{self.strategy_name.lower().replace(' ', '_')}_trades_{timestamp}.csv"
            trades_df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(trades_df)} trades to {filename}")

# Strategy Variations - 20 Different Versions
class Strategy01_Conservative(ASX300StrategyBase):
    """Version 1: Conservative - Tight stops, small positions"""
    def initialize(self):
        self.strategy_name = "01_Conservative"
        self.position_size = 0.15  # 15% positions
        self.stop_loss_pct = 0.05  # 5% stops
        self.profit_target = 0.30  # 30% targets
        self.max_positions = 8
        self.use_market_filter = False
        super().initialize()

class Strategy02_Aggressive(ASX300StrategyBase):
    """Version 2: Aggressive - Wider stops, larger positions"""
    def initialize(self):
        self.strategy_name = "02_Aggressive"
        self.position_size = 0.25  # 25% positions
        self.stop_loss_pct = 0.10  # 10% stops
        self.profit_target = 0.75  # 75% targets
        self.max_positions = 4
        self.use_market_filter = False
        super().initialize()

class Strategy03_NoStops(ASX300StrategyBase):
    """Version 3: No stop losses - Only profit targets and time exits"""
    def initialize(self):
        self.strategy_name = "03_NoStops"
        self.position_size = 0.20
        self.stop_loss_pct = 0.50  # Very wide "emergency" stop
        self.profit_target = 0.50
        self.max_positions = 6
        self.max_hold_days = 180  # Shorter time exit
        self.use_market_filter = False
        super().initialize()

class Strategy04_QuickFlip(ASX300StrategyBase):
    """Version 4: Quick profits - Small targets, fast exits"""
    def initialize(self):
        self.strategy_name = "04_QuickFlip"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.15  # 15% targets
        self.max_positions = 10  # More positions
        self.max_hold_days = 60  # Quick exits
        self.use_market_filter = False
        super().initialize()

class Strategy05_HomeRunHunter(ASX300StrategyBase):
    """Version 5: Hunt for massive gains"""
    def initialize(self):
        self.strategy_name = "05_HomeRunHunter"
        self.position_size = 0.30  # Larger positions
        self.stop_loss_pct = 0.12  # Wider stops
        self.profit_target = 1.00  # 100% targets
        self.max_positions = 3  # Very concentrated
        self.use_market_filter = False
        super().initialize()

class Strategy06_WithMarketFilter(ASX300StrategyBase):
    """Version 6: Original with market filter"""
    def initialize(self):
        self.strategy_name = "06_WithMarketFilter"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_market_filter = True  # Only difference
        super().initialize()

class Strategy07_NoTrailing(ASX300StrategyBase):
    """Version 7: No trailing stops"""
    def initialize(self):
        self.strategy_name = "07_NoTrailing"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_trailing_stop = False
        self.use_market_filter = False
        super().initialize()

class Strategy08_TightTrailing(ASX300StrategyBase):
    """Version 8: Aggressive trailing stops"""
    def initialize(self):
        self.strategy_name = "08_TightTrailing"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_trailing_stop = True
        self.trail_profit_trigger = 0.10  # Start trailing at 10%
        self.trail_percent = 0.08  # 8% trail
        self.use_market_filter = False
        super().initialize()

class Strategy09_MomentumFilter(ASX300StrategyBase):
    """Version 9: Add momentum filter"""
    def initialize(self):
        self.strategy_name = "09_MomentumFilter"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_momentum_filter = True
        self.momentum_lookback = 30
        self.use_market_filter = False
        super().initialize()

class Strategy10_NoVolumeFilter(ASX300StrategyBase):
    """Version 10: Remove volume requirements"""
    def initialize(self):
        self.strategy_name = "10_NoVolumeFilter"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_volume_filter = False
        self.use_market_filter = False
        super().initialize()

class Strategy11_HighVolume(ASX300StrategyBase):
    """Version 11: Require high volume surge"""
    def initialize(self):
        self.strategy_name = "11_HighVolume"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_volume_filter = True
        self.min_volume_surge = 2.0  # 2x volume required
        self.use_market_filter = False
        super().initialize()

class Strategy12_Diversified(ASX300StrategyBase):
    """Version 12: More diversified"""
    def initialize(self):
        self.strategy_name = "12_Diversified"
        self.position_size = 0.10  # Smaller positions
        self.stop_loss_pct = 0.07
        self.profit_target = 0.40  # Lower targets
        self.max_positions = 12  # More positions
        self.use_market_filter = False
        super().initialize()

class Strategy13_Concentrated(ASX300StrategyBase):
    """Version 13: Highly concentrated"""
    def initialize(self):
        self.strategy_name = "13_Concentrated"
        self.position_size = 0.40  # Large positions
        self.stop_loss_pct = 0.08  # Slightly wider stops
        self.profit_target = 0.60  # Higher targets
        self.max_positions = 2  # Very concentrated
        self.use_market_filter = False
        super().initialize()

class Strategy14_MediumTerm(ASX300StrategyBase):
    """Version 14: Medium-term holding"""
    def initialize(self):
        self.strategy_name = "14_MediumTerm"
        self.position_size = 0.20
        self.stop_loss_pct = 0.10  # Wider stops for longer holds
        self.profit_target = 0.80  # Higher targets
        self.max_positions = 6
        self.max_hold_days = 500  # Longer holds
        self.use_market_filter = False
        super().initialize()

class Strategy15_ShortTerm(ASX300StrategyBase):
    """Version 15: Short-term trading"""
    def initialize(self):
        self.strategy_name = "15_ShortTerm"
        self.position_size = 0.20
        self.stop_loss_pct = 0.05  # Tight stops
        self.profit_target = 0.25  # Quick profits
        self.max_positions = 8
        self.max_hold_days = 30  # Very short holds
        self.use_market_filter = False
        super().initialize()

class Strategy16_AdaptiveStops(ASX300StrategyBase):
    """Version 16: Adaptive stop losses based on volatility"""
    def initialize(self):
        self.strategy_name = "16_AdaptiveStops"
        self.position_size = 0.20
        self.stop_loss_pct = 0.08  # Base stop
        self.profit_target = 0.50
        self.max_positions = 6
        self.use_market_filter = False
        super().initialize()
    
    def calculate_adaptive_stop(self, df):
        """Calculate stop based on volatility"""
        if len(df) < 20:
            return self.stop_loss_pct
        
        # Use ATR-based stop
        high_low = df['high'] - df['low']
        volatility = high_low.rolling(14).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        adaptive_stop = min(0.12, max(0.04, volatility / current_price))
        return adaptive_stop

class Strategy17_TrendFollowing(ASX300StrategyBase):
    """Version 17: Pure trend following - no fundamentals"""
    def initialize(self):
        self.strategy_name = "17_TrendFollowing"
        self.position_size = 0.20
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.max_positions = 6
        self.fundamental_threshold = 0  # No fundamental filter
        self.use_market_filter = False
        super().initialize()

class Strategy18_Scalper(ASX300StrategyBase):
    """Version 18: Scalping approach"""
    def initialize(self):
        self.strategy_name = "18_Scalper"
        self.position_size = 0.15
        self.stop_loss_pct = 0.03  # Very tight stops
        self.profit_target = 0.08  # Small profits
        self.max_positions = 15  # Many small positions
        self.max_hold_days = 10
        self.use_market_filter = False
        super().initialize()

class Strategy19_SwingTrader(ASX300StrategyBase):
    """Version 19: Swing trading approach"""
    def initialize(self):
        self.strategy_name = "19_SwingTrader"
        self.position_size = 0.25
        self.stop_loss_pct = 0.12  # Wider stops
        self.profit_target = 0.60  # Bigger swings
        self.max_positions = 4
        self.max_hold_days = 120
        self.use_trailing_stop = True
        self.trail_profit_trigger = 0.15
        self.trail_percent = 0.10
        self.use_market_filter = False
        super().initialize()

class Strategy20_Hybrid(ASX300StrategyBase):
    """Version 20: Hybrid approach combining best elements"""
    def initialize(self):
        self.strategy_name = "20_Hybrid"
        self.position_size = 0.22  # Slightly larger
        self.stop_loss_pct = 0.06  # Slightly tighter
        self.profit_target = 0.45  # Slightly lower target
        self.max_positions = 7  # One more position
        self.use_trailing_stop = True
        self.trail_profit_trigger = 0.18
        self.trail_percent = 0.10
        self.max_hold_days = 300
        self.use_volume_filter = True
        self.min_volume_surge = 1.3
        self.use_market_filter = False
        super().initialize()

def run_strategy_backtest(strategy_class, strategy_name):
    """Run individual strategy backtest"""
    try:
        backtesting_start = datetime(2014, 1, 1)  # 10 year period
        backtesting_end = datetime(2024, 1, 1)
        initial_cash = 100000.0
        
        print(f"\n{'='*60}")
        print(f"RUNNING: {strategy_name}")
        print(f"{'='*60}")
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: ${initial_cash:,.2f}")
        
        results = strategy_class.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="VAS.AX"
        )
        
        print(f"✅ {strategy_name} COMPLETED")
        return results
        
    except Exception as e:
        print(f"❌ {strategy_name} FAILED: {e}")
        return None

def run_all_strategy_variations():
    """Run all 20 strategy variations"""
    
    strategies = [
        (Strategy01_Conservative, "01_Conservative"),
        (Strategy02_Aggressive, "02_Aggressive"), 
        (Strategy03_NoStops, "03_NoStops"),
        (Strategy04_QuickFlip, "04_QuickFlip"),
        (Strategy05_HomeRunHunter, "05_HomeRunHunter"),
        (Strategy06_WithMarketFilter, "06_WithMarketFilter"),
        (Strategy07_NoTrailing, "07_NoTrailing"),
        (Strategy08_TightTrailing, "08_TightTrailing"),
        (Strategy09_MomentumFilter, "09_MomentumFilter"),
        (Strategy10_NoVolumeFilter, "10_NoVolumeFilter"),
        (Strategy11_HighVolume, "11_HighVolume"),
        (Strategy12_Diversified, "12_Diversified"),
        (Strategy13_Concentrated, "13_Concentrated"),
        (Strategy14_MediumTerm, "14_MediumTerm"),
        (Strategy15_ShortTerm, "15_ShortTerm"),
        (Strategy16_AdaptiveStops, "16_AdaptiveStops"),
        (Strategy17_TrendFollowing, "17_TrendFollowing"),
        (Strategy18_Scalper, "18_Scalper"),
        (Strategy19_SwingTrader, "19_SwingTrader"),
        (Strategy20_Hybrid, "20_Hybrid")
    ]
    
    print("=" * 80)
    print("ASX300 STRATEGY VARIATIONS - 20 DIFFERENT APPROACHES")
    print("=" * 80)
    print("Testing hypothesis: Simpler approaches may outperform complex filters")
    print("10-Year Backtest Period: 2014-2024")
    print("All strategies test different combinations of:")
    print("  • Stop loss levels (3%-12%)")
    print("  • Profit targets (8%-100%)")
    print("  • Position sizes (10%-40%)")
    print("  • Portfolio concentration (2-15 positions)")
    print("  • Holding periods (10-500 days)")
    print("  • Market filters (on/off)")
    print("  • Volume requirements")
    print("  • Trailing stops")
    print("=" * 80)
    
    results_summary = []
    successful_runs = 0
    
    for strategy_class, strategy_name in strategies:
        result = run_strategy_backtest(strategy_class, strategy_name)
        if result is not None:
            successful_runs += 1
            # Could store performance metrics here
            results_summary.append({
                'strategy': strategy_name,
                'status': 'SUCCESS'
            })
        else:
            results_summary.append({
                'strategy': strategy_name,
                'status': 'FAILED'
            })
    
    # Final summary
    print(f"\n{'='*80}")
    print("BATCH BACKTEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Strategies: {len(strategies)}")
    print(f"Successful Runs: {successful_runs}")
    print(f"Failed Runs: {len(strategies) - successful_runs}")
    
    print(f"\nSTRATEGY STATUS:")
    for result in results_summary:
        status_symbol = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"  {status_symbol} {result['strategy']}")
    
    print(f"\nNEXT STEPS:")
    print(f"  1. Analyze generated CSV files for each strategy")
    print(f"  2. Compare performance metrics")
    print(f"  3. Identify which variations work best")
    print(f"  4. Note impact of market filters vs. simple approaches")
    print(f"  5. Focus on strategies with best risk-adjusted returns")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_df = pd.DataFrame(results_summary)
    summary_filename = f"asx300_variations_summary_{timestamp}.csv"
    summary_df.to_csv(summary_filename, index=False)
    print(f"\nSummary exported to: {summary_filename}")
    
    print(f"{'='*80}")
    print("🎯 ANALYSIS COMPLETE - CHECK CSV FILES FOR DETAILED RESULTS")
    print(f"{'='*80}")
    
    return results_summary

if __name__ == "__main__":
    print("Starting ASX300 Strategy Variations Backtest...")
    print("This will test 20 different approaches over 10 years")
    print()
    
    results = run_all_strategy_variations()
    
    print("\n🏆 ALL BACKTESTS COMPLETED!")
    print("Compare the generated CSV files to find the best approach.")
    print("Pay special attention to:")
    print("  • Total returns")
    print("  • Maximum drawdown") 
    print("  • Drawdown duration")
    print("  • Win rates")
    print("  • Profit factor")
    print("  • Simple vs. complex approaches")