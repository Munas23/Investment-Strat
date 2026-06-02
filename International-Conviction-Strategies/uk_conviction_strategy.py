"""
5-Level Conviction Trading Strategy - UK Market (FTSE 100/250)
===============================================================

Adapts our proven quality-first methodology for UK markets:
1. Fundamental screening (quality stocks >60% score)
2. Technical breakout timing (conviction-based entries)
3. Professional risk management (7% stops, 50% targets)

Tests on FTSE 100/250 universe with VUKE.L (FTSE 100 ETF) as benchmark.
"""

import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.entities import Asset

warnings.filterwarnings('ignore')

class UKConvictionStrategy(Strategy):
    """
    5-Level Conviction Strategy for UK Markets (FTSE 100/250)
    
    Combines fundamental screening + technical timing + professional risk management
    Tests on UK stock universe with GBP-based calculations
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        self.sleeptime = "1D"
        
        # Strategy parameters (adapted for UK market)
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
        
        # UK market specifics
        self.min_price = 2.0  # GBP minimum (adjusted for UK market)
        self.min_volume = 50000  # Lower volume threshold for UK
        self.min_market_cap = 200e6  # £200M minimum market cap
        self.max_market_cap = 100e9  # £100B maximum market cap
        
        # Get UK stock universe
        self.uk_symbols = self.get_uk_symbols()
        
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
        
        self.log_message("=== UK CONVICTION STRATEGY (FTSE 100/250) ===")
        self.log_message(f"Universe: UK Stocks ({len(self.uk_symbols)} stocks)")
        self.log_message(f"Benchmark: VUKE.L (FTSE 100 ETF)")
        self.log_message(f"Currency: GBP")
        self.log_message(f"Fundamental Threshold: >{self.fundamental_threshold}%")
        self.log_message(f"Position Size: {self.min_position_size*100:.0f}%-{self.max_position_size*100:.0f}%")
        self.log_message("=" * 60)
    
    def get_uk_symbols(self):
        """Get UK stock symbols (FTSE 100/250 major stocks)"""
        # Major UK stocks across sectors with .L suffix for Yahoo Finance
        uk_stocks = [
            # FTSE 100 Blue Chips
            'AZN.L',    # AstraZeneca
            'SHEL.L',   # Shell
            'BP.L',     # BP
            'ULVR.L',   # Unilever
            'GSK.L',    # GSK
            'HSBA.L',   # HSBC
            'VOD.L',    # Vodafone
            'RIO.L',    # Rio Tinto
            'BHP.L',    # BHP Group
            'LLOY.L',   # Lloyds Banking Group
            'BARC.L',   # Barclays
            'NWG.L',    # NatWest Group
            'RBS.L',    # Royal Bank of Scotland
            'BT-A.L',   # BT Group
            'GLEN.L',   # Glencore
            'AAL.L',    # Anglo American
            'LSEG.L',   # London Stock Exchange Group
            'RELX.L',   # RELX
            'DGE.L',    # Diageo
            'BA.L',     # BAE Systems
            'RR.L',     # Rolls-Royce
            'IAG.L',    # International Airlines Group
            'EZJ.L',    # easyJet
            'TSCO.L',   # Tesco
            'SBRY.L',   # Sainsbury's
            'MRW.L',    # Morrison's
            'M&S.L',    # Marks & Spencer
            'NEXT.L',   # Next
            'JD.L',     # JD Sports
            'FERG.L',   # Ferguson
            'CRH.L',    # CRH
            'LAND.L',   # Land Securities
            'BNZL.L',   # Bunzl
            'SMIN.L',   # Smiths Group
            'WPP.L',    # WPP
            'ITV.L',    # ITV
            'PSN.L',    # Persimmon
            'BDEV.L',   # Barratt Developments
            'TW.L',     # Taylor Wimpey
            'REL.L',    # RELX
            'LGEN.L',   # Legal & General
            'PRU.L',    # Prudential
            'AV.L',     # Aviva
            'RSA.L',    # RSA Insurance Group
            'III.L',    # 3i Group
            'HIK.L',    # Hikma Pharmaceuticals
            'AHT.L',    # Ashtead Group
            'RTO.L',    # Rentokil Initial
            'EXPN.L',   # Experian
            'SAGA.L',   # Saga
            'SGE.L',    # Sage Group
            'AUTO.L',   # Auto Trader Group
            'MNDI.L',   # Mondi
            'SMT.L',    # Scottish Mortgage Investment Trust
            'OCDO.L',   # Ocado Group
            'JET.L',    # Just Eat Takeaway
            'POLY.L',   # Polymetal International
            'FRES.L',   # Fresnillo
            'KGF.L',    # Kingfisher
            'WEIR.L',   # Weir Group
            'RMV.L',    # Rightmove
            'ZTF.L',    # Zotefoams
            'DCC.L',    # DCC
            'CPG.L',    # Compass Group
            'SSE.L',    # SSE
            'NG.L',     # National Grid
            'UU.L',     # United Utilities
            'SVT.L',    # Severn Trent
            'ITRK.L',   # Intertek Group
            'SGC.L',    # SGS SA
            'RS1.L',    # RS Group
            'PSON.L',   # Pearson
            'REL.L',    # RELX
            'EDV.L',    # Endeavour Mining
            'PTEC.L',   # Playtech
            'BATS.L',   # British American Tobacco
            'IMB.L',    # Imperial Brands
        ]
        
        self.log_message(f"Loaded {len(uk_stocks)} UK major stocks")
        return uk_stocks
    
    def get_fundamental_data_uk(self, symbol):
        """Get fundamental data for UK stocks with GBP adjustments"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # UK market adjustments
            fundamentals = {
                'symbol': symbol,
                'market_cap': info.get('marketCap', 0),
                'price': info.get('currentPrice', 0),
                'volume': info.get('averageVolume', 0),
                'currency': 'GBP',
                
                # Profitability metrics
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                
                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                
                # Financial strength
                'current_ratio': info.get('currentRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                
                # Valuation
                'pe_ratio': info.get('trailingPE', 0),
                'price_to_book': info.get('priceToBook', 0),
                
                # Market data
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
            }
            
            return fundamentals
            
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def screen_uk_fundamentals(self, fundamentals):
        """Screen UK stocks with adapted criteria"""
        if 'error' in fundamentals:
            return {'symbol': fundamentals['symbol'], 'error': fundamentals['error']}
        
        symbol = fundamentals['symbol']
        screening = {'symbol': symbol, 'criteria': {}, 'total_score': 0, 'max_score': 0}
        
        # UK market cap filter (£200M - £100B)
        market_cap = fundamentals.get('market_cap', 0)
        criterion_1 = self.min_market_cap <= market_cap <= self.max_market_cap
        screening['criteria']['market_cap'] = {'value': market_cap, 'pass': criterion_1, 'weight': 10}
        
        # UK price filter (>£2)
        price = fundamentals.get('price', 0)
        criterion_2 = price >= self.min_price
        screening['criteria']['price'] = {'value': price, 'pass': criterion_2, 'weight': 5}
        
        # UK volume filter (>50K for smaller market)
        volume = fundamentals.get('volume', 0)
        criterion_3 = volume >= self.min_volume
        screening['criteria']['volume'] = {'value': volume, 'pass': criterion_3, 'weight': 5}
        
        # Standard quality metrics
        roe = fundamentals.get('roe', 0)
        screening['criteria']['roe'] = {'value': roe, 'pass': roe >= 15, 'weight': 20}
        
        revenue_growth = fundamentals.get('revenue_growth', 0)
        screening['criteria']['revenue_growth'] = {'value': revenue_growth, 'pass': revenue_growth >= 10, 'weight': 25}
        
        earnings_growth = fundamentals.get('earnings_growth', 0)
        screening['criteria']['earnings_growth'] = {'value': earnings_growth, 'pass': earnings_growth >= 15, 'weight': 25}
        
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        screening['criteria']['debt_to_equity'] = {'value': debt_to_equity, 'pass': debt_to_equity <= 0.4, 'weight': 15}
        
        current_ratio = fundamentals.get('current_ratio', 0)
        screening['criteria']['current_ratio'] = {'value': current_ratio, 'pass': current_ratio >= 1.2, 'weight': 10}
        
        profit_margin = fundamentals.get('profit_margin', 0)
        screening['criteria']['profit_margin'] = {'value': profit_margin, 'pass': profit_margin >= 8, 'weight': 20}
        
        # Calculate score
        total_score = sum(data['weight'] for data in screening['criteria'].values() if data['pass'])
        max_score = sum(data['weight'] for data in screening['criteria'].values())
        
        screening['total_score'] = total_score
        screening['max_score'] = max_score
        screening['score_percentage'] = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Rating
        score_pct = screening['score_percentage']
        if score_pct >= 80:
            screening['rating'] = 'EXCELLENT'
        elif score_pct >= 60:
            screening['rating'] = 'GOOD'
        elif score_pct >= 40:
            screening['rating'] = 'FAIR'
        else:
            screening['rating'] = 'POOR'
        
        return screening
    
    def on_trading_iteration(self):
        """Main trading logic"""
        try:
            current_date = self.get_datetime()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            positions = self.get_positions()
            
            self.log_message(f"Date: {current_date.date()}")
            self.log_message(f"Portfolio: £{portfolio_value:,.0f}, Cash: £{cash:,.0f}, Positions: {len(positions)}")
            
            # Update fundamental leaders
            self.update_fundamental_leaders()
            
            # Check exits
            self.check_exits()
            
            # Look for entries
            if len(positions) < self.max_positions and self.fundamental_leaders:
                self.scan_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def update_fundamental_leaders(self):
        """Update list of fundamental leaders for UK market"""
        current_date = self.get_datetime()
        
        if (self.last_screening_date is None or 
            (current_date - self.last_screening_date).days >= self.screening_frequency):
            
            self.log_message(f"Updating UK fundamental screening...")
            
            # Screen subset of UK stocks
            sample_size = min(30, len(self.uk_symbols))
            symbols_to_screen = self.uk_symbols[:sample_size]
            
            leaders = []
            screening_count = 0
            
            for symbol in symbols_to_screen:
                try:
                    self.debug_stats['screening_attempts'] += 1
                    
                    fundamentals = self.get_fundamental_data_uk(symbol)
                    
                    if 'error' not in fundamentals:
                        screening = self.screen_uk_fundamentals(fundamentals)
                        
                        if ('error' not in screening and 
                            screening['score_percentage'] >= self.fundamental_threshold):
                            leaders.append({
                                'symbol': symbol,
                                'score': screening['score_percentage'],
                                'rating': screening['rating']
                            })
                            self.debug_stats['fundamental_leaders_found'] += 1
                        
                        screening_count += 1
                        
                        if screening_count % 10 == 0:
                            self.log_message(f"  Screened {screening_count}/{len(symbols_to_screen)} UK stocks...")
                    
                except Exception as e:
                    continue
            
            self.fundamental_leaders = [leader['symbol'] for leader in leaders]
            self.last_screening_date = current_date
            
            self.log_message(f"UK fundamental screening complete:")
            self.log_message(f"  Screened: {screening_count} stocks")
            self.log_message(f"  Leaders found: {len(self.fundamental_leaders)}")
            
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
            if distance_from_high > -10:
                score += 20
        
        return score
    
    def generate_conviction_signal(self, symbol, df):
        """Generate conviction-based entry signal (0-5)"""
        try:
            if len(df) < 150:
                return 0, "Insufficient data"
            
            current_price = df['close'].iloc[-1]
            
            # Base requirement: Strong trend
            trend_strength = self.calculate_trend_strength(df)
            if trend_strength < 60:
                return 0, f"Weak trend: {trend_strength}"
            
            conviction = 0
            
            # Factor 1: Breakout power (0-25 points)
            high_20 = df['high'].rolling(20).max().iloc[-1]
            high_50 = df['high'].rolling(50).max().iloc[-1]
            
            if current_price > high_20 * 1.01:
                conviction += 15
                if current_price > high_50 * 1.02:
                    conviction += 10
            
            # Factor 2: Volume confirmation (0-30 points) - adjusted for UK
            volume_avg = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_surge = current_volume / volume_avg if volume_avg > 0 else 0
            
            if volume_surge > 1.8:  # Slightly lower threshold for UK
                conviction += 30
            elif volume_surge > 1.4:
                conviction += 20
            elif volume_surge > 1.1:
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
            
            # Convert to conviction level
            if conviction >= 80:  # Slightly lower for UK market
                return 5, f"MAX conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 65:
                return 4, f"HIGH conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 50:
                return 3, f"STANDARD conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 35:
                return 2, f"LOW conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            elif conviction >= 20:
                return 1, f"MINIMAL conviction: {conviction}, trend: {trend_strength}, vol: {volume_surge:.1f}x"
            
            return 0, f"No conviction: {conviction}, trend: {trend_strength}"
            
        except Exception as e:
            return 0, f"Error: {e}"
    
    def calculate_position_size(self, symbol, price, conviction_level):
        """Calculate position size based on conviction level"""
        try:
            portfolio_value = self.get_portfolio_value()
            
            base_position_pct = {
                1: 0.20, 2: 0.25, 3: 0.30, 4: 0.35, 5: 0.40
            }.get(conviction_level, 0.20)
            
            position_value = portfolio_value * base_position_pct
            shares = int(position_value / price)
            
            max_shares_by_cash = int(self.get_cash() / price)
            final_shares = min(shares, max_shares_by_cash)
            return max(final_shares, 0)
            
        except Exception as e:
            self.log_message(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def check_exits(self):
        """Check exits using professional risk management"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
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
                highest_price = pos_data['highest_price']
                
                if current_price > highest_price:
                    pos_data['highest_price'] = current_price
                    highest_price = current_price
                
                pnl_pct = (current_price / entry_price - 1) * 100
                days_held = (self.get_datetime() - pos_data['entry_date']).days
                
                should_exit = False
                exit_reason = ""
                
                # Stop loss
                if pnl_pct < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # Profit target
                elif pnl_pct > self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'PROFIT TARGET'
                
                # Trailing stop
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
                
                # Time exit
                elif days_held > self.max_hold_days:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.log_message(f"EXIT: {symbol} @ £{current_price:.2f}")
                    self.log_message(f"  P&L: {pnl_pct:.1f}%, Hold: {days_held} days, Reason: {exit_reason}")
                    
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"{exit_reason} | P&L: {pnl_pct:.1f}%")
                    
                    if symbol in self.position_tracker:
                        del self.position_tracker[symbol]
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def scan_for_entries(self):
        """Scan fundamental leaders for entry setups"""
        entries_made = 0
        max_entries_per_day = 2
        
        import random
        candidates = self.fundamental_leaders.copy()
        random.shuffle(candidates)
        
        for symbol in candidates[:10]:
            try:
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                df = self.get_symbol_data(symbol, days_back=200)
                if df is None or len(df) < 150:
                    continue
                
                self.debug_stats['technical_signals_checked'] += 1
                conviction, reason = self.generate_conviction_signal(symbol, df)
                
                if conviction > 0:
                    self.debug_stats['conviction_signals_generated'] += 1
                    current_price = df['close'].iloc[-1]
                    shares = self.calculate_position_size(symbol, current_price, conviction)
                    
                    if shares > 0:
                        try:
                            self.debug_stats['orders_attempted'] += 1
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, shares, "buy")
                            self.submit_order(order)
                            self.debug_stats['orders_successful'] += 1
                            
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
                            self.log_message(f"  {shares} shares @ £{current_price:.2f} ({position_pct:.1f}% position)")
                            self.log_message(f"  Stop: £{stop_price:.2f}, {reason}")
                            
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
        self.log_message("=== UK CONVICTION STRATEGY COMPLETED ===")
        
        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            filename = f"uk_conviction_trades_{timestamp}.csv"
            trades_df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(trades_df)} trades to {filename}")
        else:
            empty_df = pd.DataFrame(columns=[
                'timestamp', 'symbol', 'action', 'price', 'quantity', 
                'value', 'reason', 'portfolio_value'
            ])
            filename = f"uk_conviction_trades_{timestamp}_NO_TRADES.csv"
            empty_df.to_csv(filename, index=False)
            self.log_message(f"No trades executed - Created empty CSV: {filename}")
        
        # Performance summary
        portfolio_value = self.get_portfolio_value()
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value * 100
        
        self.log_message("=" * 60)
        self.log_message("UK CONVICTION STRATEGY PERFORMANCE")
        self.log_message("=" * 60)
        self.log_message(f"Final Portfolio Value: £{portfolio_value:,.2f}")
        self.log_message(f"Total Return: {total_return:.1f}%")
        self.log_message(f"Total Trades: {len(self.trades_log)}")
        self.log_message("=" * 60)


def run_uk_conviction_backtest():
    """Run UK conviction strategy backtest"""
    try:
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2024, 1, 1)
        initial_cash = 100000.0
        
        print("=" * 70)
        print("5-LEVEL CONVICTION STRATEGY - UK MARKET (FTSE)")
        print("=" * 70)
        print("METHODOLOGY:")
        print("✓ Quality-First Screening: UK stocks with strong fundamentals")
        print("✓ Technical Timing: Conviction-based breakout entries")
        print("✓ Risk Management: 7% stops, 50% targets")
        print("✓ Universe: FTSE 100/250 major stocks")
        print("✓ Benchmark: VUKE.L (FTSE 100 ETF)")
        print("✓ Currency: GBP")
        print("=" * 70)
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: £{initial_cash:,.2f}")
        print("=" * 70)
        
        results = UKConvictionStrategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="VUKE.L"
        )
        
        print("\n=== UK CONVICTION STRATEGY BACKTEST COMPLETED ===")
        print("✓ UK market fundamental screening applied")
        print("✓ Technical breakout timing implemented")
        print("✓ Professional risk management executed")
        print("✓ Results exported to CSV")
        
        return results
        
    except Exception as e:
        print(f"Error in UK backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting UK Conviction Strategy...")
    print("Testing our proven methodology on FTSE 100/250 stocks")
    print()
    
    results = run_uk_conviction_backtest()
    
    if results:
        print("\n🇬🇧 UK CONVICTION STRATEGY SUCCESSFUL!")
        print("Check the generated CSV file for detailed UK market analysis")
    else:
        print("❌ UK backtest failed - check error messages above")