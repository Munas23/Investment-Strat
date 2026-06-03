"""
5-Level Conviction Trading Strategy - ASX300 Implementation
===========================================================

This implements our complete quality-first methodology using systematic backtesting:
1. Fundamental screening (only trade quality stocks >60% score)
2. Technical breakout timing (conviction-based entries)
3. Professional risk management (7% stops, 50% targets, concentrated positions)

Runs on the ASX300 universe for comprehensive testing.
"""

import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.entities import Asset

# Import our fundamental screening
from quality_fundamentals import QualityFundamentals

warnings.filterwarnings('ignore')

class ConvictionASX300Strategy(Strategy):
    """
    5-Level Conviction Strategy for ASX300
    
    Combines fundamental screening + technical timing + professional risk management
    Tests on ASX300 universe with VAS.AX benchmark
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        self.sleeptime = "1D"
        
        # Strategy parameters
        self.max_positions = 6
        self.min_position_size = 0.20
        self.max_position_size = 0.40
        self.stop_loss_pct = 0.07
        self.profit_target = 0.50
        self.fundamental_threshold = 60.0
        
        # Risk management
        self.trail_profit_trigger = 0.20
        self.trail_percent = 0.12
        self.max_hold_days = 360
        
        # Initialize screener
        self.fundamental_screener = QualityFundamentals()
        self.asx300_symbols = self.get_asx300_symbols()
        
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
            'orders_successful': 0
        }
        
        self.log_message("=== 5-LEVEL CONVICTION STRATEGY - ASX300 ===")
        self.log_message(f"Universe: ASX300 ({len(self.asx300_symbols)} stocks)")
        self.log_message(f"Benchmark: VAS.AX (Vanguard Australian Shares Index ETF)")
        self.log_message(f"Fundamental Threshold: >{self.fundamental_threshold}%")
        self.log_message(f"Position Size: {self.min_position_size*100:.0f}%-{self.max_position_size*100:.0f}%")
        self.log_message(f"Max Positions: {self.max_positions}")
        self.log_message(f"Stop Loss: {self.stop_loss_pct*100:.0f}%")
        self.log_message(f"Profit Target: {self.profit_target*100:.0f}%")
        self.log_message("=" * 60)
    
    def get_asx300_symbols(self):
        """Get ASX300 symbol list (sample of major stocks)"""
        # ASX300 major stocks across sectors
        asx300_sample = [
            # Big 4 Banks
            'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX',
            
            # Mining Giants
            'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'STO.AX', 'WDS.AX', 'OZL.AX', 'IGO.AX',
            
            # Healthcare & Biotech
            'CSL.AX', 'COH.AX', 'RMD.AX', 'SHL.AX', 'NAN.AX', 'PME.AX', 'RHC.AX',
            
            # Technology & Growth
            'APT.AX', 'XRO.AX', 'WTC.AX', 'TNE.AX', 'CPU.AX', 'KGN.AX', 'NXT.AX', 'CAR.AX',
            
            # Retail & Consumer
            'WOW.AX', 'COL.AX', 'WES.AX', 'JBH.AX', 'HVN.AX', 'SUL.AX', 'LOV.AX',
            
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
            'WTC.AX', 'A2M.AX', 'BAP.AX', 'SHV.AX',
            
            # Financial Services
            'MQG.AX', 'ASX.AX', 'PPT.AX', 'NHF.AX',
            
            # Energy
            'WPL.AX', 'ORG.AX', 'STO.AX', 'BPT.AX',
            
            # Infrastructure
            'TCL.AX', 'AST.AX', 'SYD.AX'
        ]
        
        self.log_message(f"Loaded {len(asx300_sample)} ASX300 major stocks")
        return asx300_sample
    
    def on_trading_iteration(self):
        """Main trading logic"""
        try:
            current_date = self.get_datetime()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            positions = self.get_positions()
            
            self.log_message(f"Date: {current_date.date()}")
            self.log_message(f"Portfolio: ${portfolio_value:,.0f}, Cash: ${cash:,.0f}, Positions: {len(positions)}")
            
            # Update fundamental leaders
            self.update_fundamental_leaders()
            
            # Check exits first
            self.check_exits()
            
            # Look for new entries
            if len(positions) < self.max_positions and self.fundamental_leaders:
                self.scan_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def update_fundamental_leaders(self):
        """Update list of fundamental leaders"""
        current_date = self.get_datetime()
        
        # Check if we need to re-screen
        if (self.last_screening_date is None or 
            (current_date - self.last_screening_date).days >= self.screening_frequency):
            
            self.log_message(f"Updating fundamental screening...")
            
            # Sample subset for faster screening
            sample_size = min(50, len(self.asx300_symbols))  # Screen 50 stocks at a time
            symbols_to_screen = self.asx300_symbols[:sample_size]
            
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
            
            # Log top leaders
            for leader in sorted(leaders, key=lambda x: x['score'], reverse=True)[:3]:
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
        """Calculate trend strength score (0-100)"""
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
        """Generate conviction-based entry signal (0-5)"""
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
            
            # Convert to conviction level (0-100 -> 0-5)
            if conviction >= 85:
                return 5, f"MAX conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 70:
                return 4, f"HIGH conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 55:
                return 3, f"STANDARD conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 40:
                return 2, f"LOW conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 25:
                return 1, f"MINIMAL conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            
            return 0, f"No conviction: {conviction}, trend: {trend_strength}"
            
        except Exception as e:
            return 0, f"Error: {e}"
    
    def calculate_position_size(self, symbol, price, conviction_level):
        """Calculate position size based on conviction level"""
        try:
            portfolio_value = self.get_portfolio_value()
            
            # Base position size by conviction level
            base_position_pct = {
                1: 0.20,  # 20% - minimal conviction
                2: 0.25,  # 25% - low conviction  
                3: 0.30,  # 30% - standard conviction
                4: 0.35,  # 35% - high conviction
                5: 0.40   # 40% - maximum conviction
            }.get(conviction_level, 0.20)
            
            # Calculate position value
            position_value = portfolio_value * base_position_pct
            shares = int(position_value / price)
            
            # Apply cash constraints
            max_shares_by_cash = int(self.get_cash() / price)
            
            final_shares = min(shares, max_shares_by_cash)
            return max(final_shares, 0)
            
        except Exception as e:
            self.log_message(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def check_exits(self):
        """Check exits using professional risk management rules"""
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
                
                # 2. Profit Target (50%)
                elif pnl_pct > self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'PROFIT TARGET'
                
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
                
                # 4. Time Exit (1 year max)
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
    
    def scan_for_entries(self):
        """Scan fundamental leaders for entry setups"""
        entries_made = 0
        max_entries_per_day = 2
        
        # Randomize order to avoid bias
        import random
        candidates = self.fundamental_leaders.copy()
        random.shuffle(candidates)
        
        for symbol in candidates[:15]:  # Check top 15 leaders
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
                            
                            self.log_message(f"ENTRY: {symbol} - Conviction {conviction}")
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
            'portfolio_value': self.get_portfolio_value()
        })
    
    def on_strategy_end(self):
        """Strategy completion summary"""
        self.log_message("=== 5-LEVEL CONVICTION STRATEGY COMPLETED ===\")
        
        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            filename = f"conviction_asx300_trades_{timestamp}.csv"
            trades_df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(trades_df)} trades to {filename}")
        else:
            # Create empty CSV
            empty_df = pd.DataFrame(columns=[
                'timestamp', 'symbol', 'action', 'price', 'quantity', 
                'value', 'reason', 'portfolio_value'
            ])
            filename = f"conviction_asx300_trades_{timestamp}_NO_TRADES.csv"
            empty_df.to_csv(filename, index=False)
            self.log_message(f"No trades executed - Created empty CSV: {filename}")
        
        # Performance summary
        portfolio_value = self.get_portfolio_value()
        total_trades = len(self.trades_log)
        positions = len(self.get_positions())
        
        self.log_message("=" * 80)
        self.log_message("5-LEVEL CONVICTION STRATEGY PERFORMANCE")
        self.log_message("=" * 80)
        self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log_message(f"Active Positions: {positions}")
        self.log_message(f"Total Trades: {total_trades}")
        
        # Debug statistics
        self.log_message(f"\nDEBUG STATISTICS:")
        self.log_message(f"  Stocks Screened: {self.debug_stats['screening_attempts']}")
        self.log_message(f"  Fundamental Leaders: {self.debug_stats['fundamental_leaders_found']}")
        self.log_message(f"  Technical Signals Checked: {self.debug_stats['technical_signals_checked']}")
        self.log_message(f"  Conviction Signals Generated: {self.debug_stats['conviction_signals_generated']}")
        self.log_message(f"  Orders Attempted: {self.debug_stats['orders_attempted']}")
        self.log_message(f"  Orders Successful: {self.debug_stats['orders_successful']}")
        
        # Calculate return
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value * 100
        self.log_message(f"\nPERFORMANCE:")
        self.log_message(f"  Total Return: {total_return:.1f}%")
        
        self.log_message("=" * 80)


def run_conviction_asx300_backtest():
    """Run 5-Level Conviction strategy backtest on ASX300"""
    try:
        # Backtest period
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2024, 1, 1)
        initial_cash = 100000.0
        
        print("=" * 80)
        print("5-LEVEL CONVICTION TRADING STRATEGY - ASX300")
        print("=" * 80)
        print("METHODOLOGY:")
        print("✓ Quality-First Screening: Only trade superior stocks (>60% score)")
        print("✓ Technical Timing: Conviction-based breakout entries (1-5 levels)")
        print("✓ Risk Management: 7% stops, 50% targets, concentrated positions")
        print("✓ Universe: ASX300 major stocks")
        print("✓ Benchmark: VAS.AX (Vanguard Australian Shares Index ETF)")
        print("=" * 80)
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: ${initial_cash:,.2f}")
        print("=" * 80)
        
        print("Starting 5-Level Conviction strategy backtest...")
        
        results = ConvictionASX300Strategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="VAS.AX"
        )
        
        print("\n=== 5-LEVEL CONVICTION ASX300 BACKTEST COMPLETED ===")
        print("✓ Quality-first screening applied to ASX300")
        print("✓ Technical breakout timing implemented")
        print("✓ Professional risk management executed")
        print("✓ Results exported to CSV")
        print("\nThis represents our complete quality-first methodology:")
        print("  Superior stocks + Perfect timing + Risk management = Success")
        
        return results
        
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting 5-Level Conviction Trading Strategy...")
    print("Combining quality-first screening + technical timing + risk management")
    print("Testing on ASX300 universe with systematic backtesting")
    print()
    
    results = run_conviction_asx300_backtest()
    
    if results:
        print("\n🏆 5-LEVEL CONVICTION STRATEGY BACKTEST SUCCESSFUL!")
        print("Check the generated CSV file for detailed trade analysis")
        print("This implementation demonstrates our complete systematic methodology")
    else:
        print("❌ Backtest failed - check error messages above")