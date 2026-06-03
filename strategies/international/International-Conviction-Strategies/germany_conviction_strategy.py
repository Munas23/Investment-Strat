"""
5-Level Conviction Trading Strategy - Germany Market (DAX)
=========================================================

Adapts our proven quality-first methodology for German markets:
1. Fundamental screening (quality stocks >60% score)
2. Technical breakout timing (conviction-based entries)
3. Professional risk management (7% stops, 50% targets)

Tests on DAX universe with EXS1.DE (EURO STOXX 50 ETF) as benchmark.
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

class GermanyConvictionStrategy(Strategy):
    """
    5-Level Conviction Strategy for German Markets (DAX)
    
    Combines fundamental screening + technical timing + professional risk management
    Tests on German stock universe with EUR-based calculations
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        self.sleeptime = "1D"
        
        # Strategy parameters (adapted for German market)
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
        
        # German market specifics
        self.min_price = 5.0  # EUR minimum (higher for DAX quality)
        self.min_volume = 100000  # Volume threshold for German market
        self.min_market_cap = 500e6  # €500M minimum market cap
        self.max_market_cap = 150e9  # €150B maximum market cap
        
        # Get German stock universe
        self.germany_symbols = self.get_germany_symbols()
        
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
        
        self.log_message("=== GERMANY CONVICTION STRATEGY (DAX) ===")
        self.log_message(f"Universe: German Stocks ({len(self.germany_symbols)} stocks)")
        self.log_message(f"Benchmark: EXS1.DE (EURO STOXX 50 ETF)")
        self.log_message(f"Currency: EUR")
        self.log_message(f"Fundamental Threshold: >{self.fundamental_threshold}%")
        self.log_message(f"Position Size: {self.min_position_size*100:.0f}%-{self.max_position_size*100:.0f}%")
        self.log_message("=" * 60)
    
    def get_germany_symbols(self):
        """Get German stock symbols (DAX major stocks)"""
        # Major German stocks with .DE suffix for Yahoo Finance
        german_stocks = [
            # DAX 40 Major Components
            'SAP.DE',     # SAP SE
            'ASME.DE',    # ASML Holding
            'SIE.DE',     # Siemens AG
            'ADS.DE',     # Adidas AG
            'ALV.DE',     # Allianz SE
            'BAS.DE',     # BASF SE
            'BAYN.DE',    # Bayer AG
            'BMW.DE',     # BMW AG
            'CON.DE',     # Continental AG
            'DAI.DE',     # Mercedes-Benz Group AG
            'DB1.DE',     # Deutsche Börse AG
            'DBK.DE',     # Deutsche Bank AG
            'DTE.DE',     # Deutsche Telekom AG
            'DWNI.DE',    # Deutsche Wohnen SE
            'EOAN.DE',    # E.ON SE
            'FRE.DE',     # Fresenius SE
            'FME.DE',     # Fresenius Medical Care
            'HEI.DE',     # HeidelbergCement AG
            'HEN3.DE',    # Henkel AG
            'IFX.DE',     # Infineon Technologies AG
            'LIN.DE',     # Linde plc
            'MRK.DE',     # Merck KGaA
            'MTX.DE',     # MTU Aero Engines AG
            'MUV2.DE',    # Munich Re
            'RWE.DE',     # RWE AG
            'VOW3.DE',    # Volkswagen AG
            'VNA.DE',     # Vonovia SE
            'WDI.DE',     # Wirecard AG
            'ZAL.DE',     # Zalando SE
            
            # MDAX Major Stocks
            'AIXA.DE',    # Aixtron SE
            'EVK.DE',     # Evonik Industries AG
            'GXI.DE',     # GERRESHEIMER AG
            'HAB.DE',     # Hapag-Lloyd AG
            'HDD.DE',     # Heidelberg Druckmaschinen AG
            'LEG.DE',     # LEG Immobilien SE
            'LXS.DE',     # LANXESS AG
            'PUM.DE',     # PUMA SE
            'RAA.DE',     # RATIONAL AG
            'SHL.DE',     # Siemens Healthineers AG
            'TKA.DE',     # ThyssenKrupp AG
            'VAR1.DE',    # Varta AG
            'WAC.DE',     # Wacker Chemie AG
            'WCH.DE',     # Wacker Chemie AG
            
            # TecDAX Tech Stocks
            'COP.DE',     # CompuGroup Medical SE
            'DRW3.DE',    # Drägerwerk AG
            'EVD.DE',     # CTS Eventim AG
            'NEM.DE',     # Nemetschek SE
            'O2D.DE',     # Telefónica Deutschland
            'QIA.DE',     # Qiagen N.V.
            'S92.DE',     # SMA Solar Technology AG
            'SIX2.DE',    # Sixt SE
            'SOW.DE',     # Software AG
            'TEG.DE',     # Talanx AG
            'TIM.DE',     # TeamViewer AG
            'UTDI.DE',    # United Internet AG
            'VAR1.DE',    # Varta AG
            '1COV.DE',    # Covestro AG
            'AFX.DE',     # Carl Zeiss Meditec AG
            'BC8.DE',     # Bechtle AG
            'BNR.DE',     # Brenntag SE
            'DUE.DE',     # Dürr AG
            'G1A.DE',     # GEA Group AG
            'HHFA.DE',    # Hamburger Hafen
            'HOT.DE',     # Hochtief AG
            'JUN3.DE',    # Jungheinrich AG
            'KGX.DE',     # KION Group AG
            'PFV.DE',     # Pfeiffer Vacuum
            'RHM.DE',     # Rheinmetall AG
            'SDF.DE',     # K+S AG
            'SHA.DE',     # Schaeffler AG
            'SY1.DE',     # Symrise AG
        ]
        
        self.log_message(f"Loaded {len(german_stocks)} German major stocks")
        return german_stocks
    
    def get_fundamental_data_germany(self, symbol):
        """Get fundamental data for German stocks with EUR adjustments"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # German market adjustments
            fundamentals = {
                'symbol': symbol,
                'market_cap': info.get('marketCap', 0),
                'price': info.get('currentPrice', 0),
                'volume': info.get('averageVolume', 0),
                'currency': 'EUR',
                
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
    
    def screen_germany_fundamentals(self, fundamentals):
        """Screen German stocks with adapted criteria"""
        if 'error' in fundamentals:
            return {'symbol': fundamentals['symbol'], 'error': fundamentals['error']}
        
        symbol = fundamentals['symbol']
        screening = {'symbol': symbol, 'criteria': {}, 'total_score': 0, 'max_score': 0}
        
        # German market cap filter (€500M - €150B)
        market_cap = fundamentals.get('market_cap', 0)
        criterion_1 = self.min_market_cap <= market_cap <= self.max_market_cap
        screening['criteria']['market_cap'] = {'value': market_cap, 'pass': criterion_1, 'weight': 10}
        
        # German price filter (>€5)
        price = fundamentals.get('price', 0)
        criterion_2 = price >= self.min_price
        screening['criteria']['price'] = {'value': price, 'pass': criterion_2, 'weight': 5}
        
        # German volume filter (>100K for DAX quality)
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
            self.log_message(f"Portfolio: €{portfolio_value:,.0f}, Cash: €{cash:,.0f}, Positions: {len(positions)}")
            
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
        """Update list of fundamental leaders for German market"""
        current_date = self.get_datetime()
        
        if (self.last_screening_date is None or 
            (current_date - self.last_screening_date).days >= self.screening_frequency):
            
            self.log_message(f"Updating German fundamental screening...")
            
            # Screen subset of German stocks
            sample_size = min(30, len(self.germany_symbols))
            symbols_to_screen = self.germany_symbols[:sample_size]
            
            leaders = []
            screening_count = 0
            
            for symbol in symbols_to_screen:
                try:
                    self.debug_stats['screening_attempts'] += 1
                    
                    fundamentals = self.get_fundamental_data_germany(symbol)
                    
                    if 'error' not in fundamentals:
                        screening = self.screen_germany_fundamentals(fundamentals)
                        
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
                            self.log_message(f"  Screened {screening_count}/{len(symbols_to_screen)} German stocks...")
                    
                except Exception as e:
                    continue
            
            self.fundamental_leaders = [leader['symbol'] for leader in leaders]
            self.last_screening_date = current_date
            
            self.log_message(f"German fundamental screening complete:")
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
            
            # Factor 2: Volume confirmation (0-30 points) - standard for DAX
            volume_avg = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            volume_surge = current_volume / volume_avg if volume_avg > 0 else 0
            
            if volume_surge > 2.0:
                conviction += 30
            elif volume_surge > 1.5:
                conviction += 20
            elif volume_surge > 1.2:
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
            if conviction >= 85:  # Standard thresholds for DAX
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
                    
                    self.log_message(f"EXIT: {symbol} @ €{current_price:.2f}")
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
                            self.log_message(f"  {shares} shares @ €{current_price:.2f} ({position_pct:.1f}% position)")
                            self.log_message(f"  Stop: €{stop_price:.2f}, {reason}")
                            
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
        self.log_message("=== GERMANY CONVICTION STRATEGY COMPLETED ===")
        
        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            filename = f"germany_conviction_trades_{timestamp}.csv"
            trades_df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(trades_df)} trades to {filename}")
        else:
            empty_df = pd.DataFrame(columns=[
                'timestamp', 'symbol', 'action', 'price', 'quantity', 
                'value', 'reason', 'portfolio_value'
            ])
            filename = f"germany_conviction_trades_{timestamp}_NO_TRADES.csv"
            empty_df.to_csv(filename, index=False)
            self.log_message(f"No trades executed - Created empty CSV: {filename}")
        
        # Performance summary
        portfolio_value = self.get_portfolio_value()
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value * 100
        
        self.log_message("=" * 60)
        self.log_message("GERMANY CONVICTION STRATEGY PERFORMANCE")
        self.log_message("=" * 60)
        self.log_message(f"Final Portfolio Value: €{portfolio_value:,.2f}")
        self.log_message(f"Total Return: {total_return:.1f}%")
        self.log_message(f"Total Trades: {len(self.trades_log)}")
        self.log_message("=" * 60)


def run_germany_conviction_backtest():
    """Run Germany conviction strategy backtest"""
    try:
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2024, 1, 1)
        initial_cash = 100000.0
        
        print("=" * 70)
        print("5-LEVEL CONVICTION STRATEGY - GERMANY MARKET (DAX)")
        print("=" * 70)
        print("METHODOLOGY:")
        print("✓ Quality-First Screening: German stocks with strong fundamentals")
        print("✓ Technical Timing: Conviction-based breakout entries")
        print("✓ Risk Management: 7% stops, 50% targets")
        print("✓ Universe: DAX major stocks")
        print("✓ Benchmark: EXS1.DE (EURO STOXX 50 ETF)")
        print("✓ Currency: EUR")
        print("=" * 70)
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: €{initial_cash:,.2f}")
        print("=" * 70)
        
        results = GermanyConvictionStrategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="EXS1.DE"
        )
        
        print("\n=== GERMANY CONVICTION STRATEGY BACKTEST COMPLETED ===")
        print("✓ German market fundamental screening applied")
        print("✓ Technical breakout timing implemented")
        print("✓ Professional risk management executed")
        print("✓ Results exported to CSV")
        
        return results
        
    except Exception as e:
        print(f"Error in Germany backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting Germany Conviction Strategy...")
    print("Testing our proven methodology on DAX stocks")
    print()
    
    results = run_germany_conviction_backtest()
    
    if results:
        print("\n🇩🇪 GERMANY CONVICTION STRATEGY SUCCESSFUL!")
        print("Check the generated CSV file for detailed German market analysis")
    else:
        print("❌ Germany backtest failed - check error messages above")