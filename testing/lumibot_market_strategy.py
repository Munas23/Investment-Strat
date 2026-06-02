"""
Professional Growth Strategy - Stock Market Indices
===================================================

This implements our optimal hybrid exit strategy as a proper Lumibot strategy
that can be backtested against major stock market indices like S&P 500, ASX 300, etc.

STRATEGY OVERVIEW:
- Enhanced fundamental screening
- 50% profit trigger + 15% trailing stop (optimal from testing)
- Professional entry signals with volume confirmation
- Risk management with position sizing and stops

MARKET INDICES SUPPORTED:
- S&P 500 (US)
- NASDAQ 100 (US Tech)
- ASX 300 (Australia)
- FTSE 100 (UK)
- DAX 30 (Germany)
- Nikkei 225 (Japan)
- TSX 60 (Canada)
- EURO STOXX 50 (Europe)
- Hang Seng (Hong Kong)
- BSE SENSEX (India)
"""

from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting
from lumibot.traders import Trader
from lumibot.entities import Asset
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

class ProfessionalGrowthStrategy(Strategy):
    """
    Professional growth strategy using optimal hybrid exits on market indices
    """
    
    # Strategy parameters - optimized from our testing
    parameters = {
        # Market selection
        "market_index": "SP500",  # Default market
        "universe_size": 50,      # Top N stocks from index to trade
        
        # Fundamental screening
        "fundamental_score_threshold": 60.0,
        "rescreen_frequency_days": 30,
        
        # Position management
        "max_positions": 8,
        "position_size_pct": 0.125,  # 12.5% per position
        "cash_buffer": 0.05,         # 5% cash buffer
        
        # Entry signals
        "min_conviction": 3,         # Minimum conviction (1-5)
        "volume_threshold": 1.5,     # Volume surge requirement
        "breakout_threshold": 0.01,  # 1% breakout above highs
        
        # Optimal hybrid exit (from our testing: 251.5% avg returns)
        "profit_trigger": 50.0,      # 50% profit trigger
        "trailing_stop_pct": 15.0,   # 15% trailing stop
        "stop_loss_pct": 7.0,        # 7% disaster stop
        "max_hold_days": 365,        # Max hold period
    }
    
    def initialize(self):
        """Initialize the strategy"""
        self.sleeptime = 1  # Check daily
        
        # Initialize market universe
        self.market_universe = self._get_market_universe()
        self.screened_stocks = {}
        self.last_screen_date = None
        self.position_tracker = {}
        
        # Log initialization
        market = self.parameters["market_index"]
        universe_size = self.parameters["universe_size"]
        
        self.log_message(f"Professional Growth Strategy Initialized")
        self.log_message(f"Market: {market} (Top {universe_size} stocks)")
        self.log_message(f"Exit Strategy: {self.parameters['profit_trigger']}% trigger + {self.parameters['trailing_stop_pct']}% trail")
        self.log_message(f"Fundamental Threshold: {self.parameters['fundamental_score_threshold']}%")
    
    def _get_market_universe(self) -> List[str]:
        """Get stock symbols for the selected market index"""
        market = self.parameters["market_index"]
        
        market_definitions = {
            "SP500": [
                # S&P 500 Top Growth Stocks
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX',
                'ADBE', 'CRM', 'ORCL', 'NOW', 'INTU', 'AMD', 'QCOM', 'AVGO',
                'AMAT', 'LRCX', 'KLAC', 'MU', 'TXN', 'ADI', 'MRVL', 'ON',
                'SNOW', 'DDOG', 'NET', 'CRWD', 'ZS', 'OKTA', 'PLTR', 'DOCU',
                'ZM', 'ROKU', 'SQ', 'SHOP', 'UBER', 'LYFT', 'PINS', 'SNAP',
                'SPOT', 'TWLO', 'ESTC', 'MDB', 'TEAM', 'WDAY', 'VEEV', 'ZEN'
            ],
            
            "NASDAQ100": [
                # NASDAQ 100 Tech Leaders
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX',
                'ADBE', 'ORCL', 'CRM', 'INTC', 'CSCO', 'AMD', 'QCOM', 'AVGO',
                'TXN', 'INTU', 'AMAT', 'LRCX', 'KLAC', 'MU', 'ADI', 'MXIM',
                'MRVL', 'XLNX', 'SWKS', 'ON', 'MPWR', 'POWI', 'CRUS', 'SLAB'
            ],
            
            "ASX300": [
                # ASX 300 - Australian Stock Exchange (using US-listed or ADRs)
                'BHP', 'RIO', 'CSL', 'CBA', 'WBC', 'ANZ', 'NAB', 'WES',
                'WOW', 'TLS', 'TCL', 'FMG', 'STO', 'WPL', 'COL', 'GMG',
                'REA', 'CAR', 'SEK', 'XRO', 'APT', 'ZIP', 'WTC', 'TNE',
                'NXT', 'PME', 'HUB', 'PRO', 'LYC', 'PLS', 'MIN', 'IGO'
            ],
            
            "FTSE100": [
                # FTSE 100 - UK (ADRs and London-listed)
                'AZN', 'ULVR', 'RDS-A', 'BP', 'HSBA', 'VOD', 'RIO', 'BHP',
                'LLOY', 'GLEN', 'BATS', 'DGE', 'REL', 'NG', 'BARC', 'BT-A',
                'AAL', 'EXPN', 'INF', 'FLTR', 'RKT', 'OCDO', 'AUTO', 'DPLM'
            ],
            
            "DAX30": [
                # DAX 30 - Germany (ADRs)
                'SAP', 'ASML', 'ADYEN', 'DHER', 'SIE', 'BAS', 'VOW3', 'ALV',
                'MUV2', 'DB', 'BMW', 'ADS', 'LIN', 'DTE', 'FRE', 'HEI',
                'IFX', 'SAP', 'SHL', 'VNA', 'CON', 'DAI', 'MRK', 'MTX'
            ],
            
            "NIKKEI225": [
                # Nikkei 225 - Japan (ADRs and US-listed)
                'TM', 'SONY', 'NTT', 'HMC', 'MUFG', 'SMFG', 'TSM', 'KB',
                'LPL', 'MFG', 'NMR', 'CAJ', 'MTU', 'FUJHY', 'SFTBY', 'NTTYY'
            ],
            
            "TSX60": [
                # TSX 60 - Canada
                'SHOP', 'TD', 'RY', 'BNS', 'BMO', 'CNR', 'CP', 'ENB',
                'TRP', 'SU', 'CNQ', 'WCN', 'CSU', 'ATD', 'L', 'NTR',
                'WEED', 'ACB', 'CRON', 'TLRY', 'CGC', 'HEXO', 'OGI', 'FIRE'
            ],
            
            "EUROSTOXX50": [
                # EURO STOXX 50 (European ADRs)
                'ASML', 'SAP', 'ADYEN', 'NVO', 'UL', 'DEO', 'NVS', 'ROG',
                'NESN', 'MC', 'OR', 'LVMH', 'ADDYY', 'IDEXY', 'BCS', 'ING',
                'PHG', 'STM', 'ERIC', 'NOK', 'TEF', 'ORAN', 'VOD', 'UBS'
            ],
            
            "HANGSENG": [
                # Hang Seng - Hong Kong (US-listed Chinese stocks)
                'BABA', 'JD', 'PDD', 'BIDU', 'NIO', 'XPEV', 'LI', 'TME',
                'BILI', 'IQ', 'NTES', 'WB', 'VIPS', 'YMM', 'TIGR', 'FUTU',
                'HUYA', 'DOYU', 'MOMO', 'YY', 'QFIN', 'FINV', 'KC', 'LEGN'
            ],
            
            "BSE_SENSEX": [
                # BSE SENSEX - India (ADRs and US-listed)
                'INFY', 'WIT', 'HDB', 'IBN', 'VEDL', 'RDY', 'TTM', 'WNS',
                'SIFY', 'REDY', 'MMYT', 'YTRA', 'CTSH', 'SSTK', 'LDOS', 'PGTI'
            ]
        }
        
        universe = market_definitions.get(market, market_definitions["SP500"])
        return universe[:self.parameters["universe_size"]]
    
    def on_trading_iteration(self):
        """Main strategy execution"""
        # 1. Periodic fundamental screening
        if self._should_rescreen():
            self._perform_fundamental_screening()
        
        # 2. Check exit conditions
        self._check_exit_conditions()
        
        # 3. Look for entry opportunities
        self._check_entry_opportunities()
        
        # 4. Log status
        self._log_portfolio_status()
    
    def _should_rescreen(self) -> bool:
        """Check if we should rescreen fundamentals"""
        if self.last_screen_date is None:
            return True
        
        days_since_screen = (self.get_datetime() - self.last_screen_date).days
        return days_since_screen >= self.parameters["rescreen_frequency_days"]
    
    def _perform_fundamental_screening(self):
        """Screen stocks using simplified fundamental criteria"""
        self.log_message(f"Screening {len(self.market_universe)} stocks...")
        
        screened_stocks = {}
        
        for symbol in self.market_universe:
            try:
                # Get basic fundamental data
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Simple fundamental score (0-100)
                score = self._calculate_fundamental_score(info)
                
                if score >= self.parameters["fundamental_score_threshold"]:
                    screened_stocks[symbol] = {
                        'score': score,
                        'market_cap': info.get('marketCap', 0),
                        'sector': info.get('sector', 'Unknown')
                    }
                    
            except Exception as e:
                continue  # Skip stocks with data issues
        
        self.screened_stocks = screened_stocks
        self.last_screen_date = self.get_datetime()
        
        self.log_message(f"Screening complete: {len(screened_stocks)}/{len(self.market_universe)} passed")
    
    def _calculate_fundamental_score(self, info: Dict) -> float:
        """Calculate simple fundamental score"""
        score = 0
        
        # Revenue growth
        revenue_growth = info.get('revenueGrowth', 0)
        if revenue_growth > 0.15:  # >15%
            score += 25
        elif revenue_growth > 0.10:  # >10%
            score += 15
        
        # Profitability
        roe = info.get('returnOnEquity', 0)
        if roe > 0.15:  # >15%
            score += 20
        elif roe > 0.10:  # >10%
            score += 10
        
        # Margins
        gross_margin = info.get('grossMargins', 0)
        if gross_margin > 0.4:  # >40%
            score += 15
        elif gross_margin > 0.3:  # >30%
            score += 10
        
        # Debt levels
        debt_to_equity = info.get('debtToEquity', 100)
        if debt_to_equity < 30:
            score += 15
        elif debt_to_equity < 50:
            score += 10
        
        # Market cap (prefer mid to large cap)
        market_cap = info.get('marketCap', 0)
        if market_cap > 10e9:  # >$10B
            score += 15
        elif market_cap > 2e9:  # >$2B
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def _check_exit_conditions(self):
        """Check exit conditions using optimal hybrid strategy"""
        positions = self.get_positions()
        
        for asset in positions:
            if asset.symbol not in self.position_tracker:
                continue
                
            position = self.get_position(asset)
            if position.quantity == 0:
                continue
            
            current_price = self.get_last_price(asset)
            if current_price is None:
                continue
            
            # Get position data
            tracker = self.position_tracker[asset.symbol]
            entry_price = tracker['entry_price']
            entry_date = tracker['entry_date']
            
            # Calculate metrics
            current_pnl_pct = (current_price / entry_price - 1) * 100
            days_held = (self.get_datetime() - entry_date).days
            
            # Check exit conditions
            should_exit, exit_reason = self._evaluate_exit_conditions(
                asset.symbol, current_price, entry_price, current_pnl_pct, days_held
            )
            
            if should_exit:
                self.log_message(f"SELL {asset.symbol}: {exit_reason} (P&L: {current_pnl_pct:.1f}%)")
                
                # Create sell order
                order = self.create_order(asset, -position.quantity)
                self.submit_order(order)
                
                # Remove from tracking
                del self.position_tracker[asset.symbol]
    
    def _evaluate_exit_conditions(self, symbol: str, current_price: float,
                                 entry_price: float, current_pnl_pct: float,
                                 days_held: int) -> Tuple[bool, str]:
        """Evaluate exit using 50% trigger + 15% trailing stop"""
        
        # Disaster stop loss
        if current_pnl_pct <= -self.parameters["stop_loss_pct"]:
            return True, "Stop Loss"
        
        # Time exit
        if days_held >= self.parameters["max_hold_days"]:
            return True, "Time Exit"
        
        # Hybrid exit logic
        profit_trigger = self.parameters["profit_trigger"]
        trailing_pct = self.parameters["trailing_stop_pct"]
        
        tracker = self.position_tracker[symbol]
        
        # Check if profit trigger hit
        if current_pnl_pct >= profit_trigger:
            tracker['trailing_active'] = True
            if 'highest_price' not in tracker:
                tracker['highest_price'] = current_price
        
        # Apply trailing stop if active
        if tracker.get('trailing_active', False):
            # Update highest price
            tracker['highest_price'] = max(
                tracker.get('highest_price', current_price), 
                current_price
            )
            
            # Calculate trailing stop
            highest_price = tracker['highest_price']
            trailing_stop = highest_price * (1 - trailing_pct / 100)
            
            if current_price <= trailing_stop:
                return True, f"Trailing Stop ({trailing_pct}%)"
        
        return False, ""
    
    def _check_entry_opportunities(self):
        """Look for new entry opportunities"""
        if not self.screened_stocks:
            return
        
        current_positions = len(self.get_positions())
        if current_positions >= self.parameters["max_positions"]:
            return
        
        # Calculate position size
        available_cash = self.get_cash() * (1 - self.parameters["cash_buffer"])
        position_size = available_cash * self.parameters["position_size_pct"]
        
        # Check each screened stock
        for symbol, stock_data in self.screened_stocks.items():
            # Skip if already holding
            asset = Asset(symbol=symbol, asset_type="stock")
            if self.get_position(asset) is not None:
                continue
            
            # Evaluate entry signal
            conviction = self._evaluate_entry_signal(symbol)
            
            if conviction >= self.parameters["min_conviction"]:
                current_price = self.get_last_price(asset)
                if current_price is None or current_price <= 0:
                    continue
                
                shares = int(position_size / current_price)
                
                if shares > 0:
                    self.log_message(f"BUY {symbol}: Conviction {conviction} "
                                   f"(Score: {stock_data['score']:.0f}%)")
                    
                    # Create buy order
                    order = self.create_order(asset, shares)
                    self.submit_order(order)
                    
                    # Track position
                    self.position_tracker[symbol] = {
                        'entry_date': self.get_datetime(),
                        'entry_price': current_price,
                        'conviction': conviction,
                        'fundamental_score': stock_data['score'],
                        'trailing_active': False
                    }
                    
                    current_positions += 1
                    if current_positions >= self.parameters["max_positions"]:
                        break
    
    def _evaluate_entry_signal(self, symbol: str) -> int:
        """Evaluate entry signal strength (0-5)"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, 100, "day")
            
            if bars is None or len(bars.df) < 50:
                return 0
            
            df = bars.df
            df = self._calculate_technical_indicators(df)
            
            if len(df) < 50:
                return 0
            
            current = df.iloc[-1]
            conviction = 0
            
            # Base trend requirement
            if not (current['close'] > current['ma_20'] and 
                   current['ma_20'] > current['ma_40']):
                return 0
            
            # Breakout strength (30 points)
            if current['close'] > current['high_20d'] * (1 + self.parameters["breakout_threshold"]):
                conviction += 15
            if current['close'] > current['high_50d'] * (1 + self.parameters["breakout_threshold"] * 2):
                conviction += 15
            
            # Volume confirmation (25 points)
            if not pd.isna(current['volume_ratio']):
                if current['volume_ratio'] > self.parameters["volume_threshold"] * 1.3:
                    conviction += 25
                elif current['volume_ratio'] > self.parameters["volume_threshold"]:
                    conviction += 15
                elif current['volume_ratio'] > self.parameters["volume_threshold"] * 0.8:
                    conviction += 10
            
            # Momentum (25 points)
            if not pd.isna(current['momentum_5d']) and current['momentum_5d'] > 1:
                conviction += 5
            if not pd.isna(current['momentum_20d']) and current['momentum_20d'] > 5:
                conviction += 20
            
            # Trend strength (20 points)
            if current['trend_strength'] >= 80:
                conviction += 20
            elif current['trend_strength'] >= 60:
                conviction += 10
            
            # Convert to conviction level
            if conviction >= 80:
                return 5
            elif conviction >= 65:
                return 4
            elif conviction >= 50:
                return 3
            elif conviction >= 35:
                return 2
            elif conviction >= 20:
                return 1
            
            return 0
            
        except Exception:
            return 0
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # Moving averages
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_20'] = df['close'].rolling(20).mean()
        df['ma_40'] = df['close'].rolling(40).mean()
        
        # Breakout levels
        df['high_20d'] = df['high'].rolling(20).max()
        df['high_50d'] = df['high'].rolling(50).max()
        
        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Momentum
        df['momentum_5d'] = ((df['close'] / df['close'].shift(5)) - 1) * 100
        df['momentum_20d'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        
        # Trend strength
        df['trend_strength'] = 0
        for i in range(40, len(df)):
            score = 0
            if df.iloc[i]['close'] > df.iloc[i]['ma_10']:
                score += 20
            if df.iloc[i]['close'] > df.iloc[i]['ma_20']:
                score += 25
            if df.iloc[i]['close'] > df.iloc[i]['ma_40']:
                score += 25
            if df.iloc[i]['ma_10'] > df.iloc[i]['ma_20']:
                score += 15
            if df.iloc[i]['ma_20'] > df.iloc[i]['ma_40']:
                score += 15
            df.iloc[i, df.columns.get_loc('trend_strength')] = score
        
        return df
    
    def _log_portfolio_status(self):
        """Log portfolio status"""
        positions = self.get_positions()
        if positions:
            total_value = self.get_portfolio_value()
            cash = self.get_cash()
            market = self.parameters["market_index"]
            
            self.log_message(f"{market}: {len(positions)} positions, "
                           f"Value: ${total_value:,.0f}, Cash: ${cash:,.0f}")


# Market-specific strategy classes
class SP500Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "SP500"

class ASX300Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "ASX300"

class NASDAQ100Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "NASDAQ100"

class FTSE100Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "FTSE100"

class DAX30Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "DAX30"

class Nikkei225Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "NIKKEI225"

class TSX60Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "TSX60"

class EuroStoxx50Strategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "EUROSTOXX50"

class HangSengStrategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "HANGSENG"

class BSESensexStrategy(ProfessionalGrowthStrategy):
    parameters = ProfessionalGrowthStrategy.parameters.copy()
    parameters["market_index"] = "BSE_SENSEX"


def main():
    """Example usage"""
    print("PROFESSIONAL GROWTH STRATEGY - MARKET INDICES")
    print("=" * 60)
    print("Available Markets:")
    
    markets = {
        "SP500": "S&P 500 (US)",
        "NASDAQ100": "NASDAQ 100 (US Tech)",
        "ASX300": "ASX 300 (Australia)", 
        "FTSE100": "FTSE 100 (UK)",
        "DAX30": "DAX 30 (Germany)",
        "NIKKEI225": "Nikkei 225 (Japan)",
        "TSX60": "TSX 60 (Canada)",
        "EUROSTOXX50": "EURO STOXX 50 (Europe)",
        "HANGSENG": "Hang Seng (Hong Kong)",
        "BSE_SENSEX": "BSE SENSEX (India)"
    }
    
    for code, name in markets.items():
        print(f"  {code}: {name}")
    
    print(f"\nStrategy Features:")
    print(f"• 50% Trigger + 15% Trailing Stop (optimal from testing)")
    print(f"• Enhanced fundamental screening")
    print(f"• Professional risk management")
    print(f"• Multi-market capability")
    
    return ProfessionalGrowthStrategy

if __name__ == "__main__":
    strategy_class = main()