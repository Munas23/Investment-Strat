"""
Daily Conviction Scanner - Yahoo Finance Edition
===============================================

End-of-day scanner using free Yahoo Finance data to identify high-conviction setups
for next-day execution on Interactive Brokers.

Features:
- Free Yahoo Finance data (no subscriptions needed)
- ASX300 and S&P500 coverage
- Same 5-level conviction scoring
- Complete daily OHLCV data
- CSV export for trade planning
- Run daily after market close

Workflow:
1. Run scanner after market close
2. Review high-conviction signals
3. Place orders next trading day on IB
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
from typing import Dict, List, Optional, Tuple
import logging

warnings.filterwarnings('ignore')

class DailyConvictionScanner:
    """
    Daily market scanner using Yahoo Finance for end-of-day conviction analysis
    """
    
    def __init__(self):
        """Initialize the daily scanner"""
        
        # Scanner settings
        self.fundamental_threshold = 60.0
        self.min_price = 0.01  # Accept all stocks (no minimum price filter)
        self.min_avg_volume = 10000  # Lower volume threshold for full coverage
        self.min_market_cap = 100e6  # Minimum market cap of $100M
        self.max_market_cap = 10000e9  # Very high cap limit (essentially no limit)
        
        # Scanning results
        self.scan_results = []
        self.conviction_alerts = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        print("=" * 60)
        print("DAILY CONVICTION SCANNER - YAHOO FINANCE EDITION")
        print("=" * 60)
        print("End-of-day analysis for next-day IB execution")
        print(f"Scan date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def get_symbol_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Get historical data from Yahoo Finance
        
        Parameters:
        - symbol: Stock symbol (AAPL, CBA.AX, etc.)
        - period: Data period (1y, 6mo, etc.)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period, interval="1d")
            
            if hist.empty or len(hist) < 150:
                self.logger.debug(f"{symbol}: Insufficient data ({len(hist)} days)")
                return None
            
            # Standardize column names
            hist.columns = [col.lower() for col in hist.columns]
            
            # Remove any timezone info and ensure we have clean data
            hist.index = pd.to_datetime(hist.index).date
            hist = hist.dropna()
            
            if len(hist) < 150:
                return None
            
            return hist.reset_index()
            
        except Exception as e:
            self.logger.debug(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range (ATR) for volatility measurement"""
        try:
            if len(df) < period + 1:
                return 0
            
            # Calculate True Range components
            df = df.copy()
            df['prev_close'] = df['close'].shift(1)
            
            # True Range = max(high-low, high-prev_close, prev_close-low)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['prev_close'] - df['low'])
            df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Calculate ATR (simple moving average of True Range)
            atr = df['true_range'].rolling(period).mean().iloc[-1]
            
            return atr if not pd.isna(atr) else 0
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {e}")
            return 0
    
    def calculate_percentage_gains(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate percentage gains for different time periods"""
        try:
            if len(df) < 2:
                return {'week_gain': 0, 'month_gain': 0}
            
            current_price = df['close'].iloc[-1]
            gains = {}
            
            # Weekly gain (5 trading days)
            if len(df) >= 6:
                week_ago_price = df['close'].iloc[-6]
                gains['week_gain'] = ((current_price / week_ago_price) - 1) * 100
            else:
                gains['week_gain'] = 0
            
            # Monthly gain (22 trading days)
            if len(df) >= 23:
                month_ago_price = df['close'].iloc[-23]
                gains['month_gain'] = ((current_price / month_ago_price) - 1) * 100
            else:
                gains['month_gain'] = 0
            
            return gains
            
        except Exception as e:
            self.logger.error(f"Error calculating percentage gains: {e}")
            return {'week_gain': 0, 'month_gain': 0}

    def calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength score (0-100) using daily data"""
        try:
            if len(df) < 150:
                return 0
            
            current = df.iloc[-1]
            
            # Calculate moving averages
            df['ma_21'] = df['close'].rolling(21).mean()
            df['ma_50'] = df['close'].rolling(50).mean()
            df['ma_150'] = df['close'].rolling(150).mean()
            
            ma_21 = df['ma_21'].iloc[-1]
            ma_50 = df['ma_50'].iloc[-1]
            ma_150 = df['ma_150'].iloc[-1]
            
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
            
        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 0
    
    def generate_conviction_signal(self, symbol: str, df: pd.DataFrame) -> Tuple[int, str, Dict]:
        """
        Generate daily conviction signal (0-5) using yesterday's complete data
        
        Returns:
        - conviction_level: 0-5 
        - reason: Explanation
        - details: Scoring breakdown
        """
        try:
            if len(df) < 150:
                return 0, "Insufficient historical data", {}
            
            current = df.iloc[-1]  # Yesterday's complete bar
            prev = df.iloc[-2]     # Day before yesterday
            
            current_price = current['close']
            
            # Base requirement: Strong trend (score >60)
            trend_strength = self.calculate_trend_strength(df)
            if trend_strength < 60:
                return 0, f"Weak trend: {trend_strength:.0f}", {'trend_strength': trend_strength}
            
            conviction = 0
            details = {'trend_strength': trend_strength}
            
            # Factor 1: Breakout power (0-25 points)
            high_20 = df['high'].rolling(20).max().iloc[-2]  # Exclude current day
            high_50 = df['high'].rolling(50).max().iloc[-2]
            
            breakout_points = 0
            if current_price > high_20 * 1.01:  # 1% above 20-day high
                breakout_points += 15
                if current_price > high_50 * 1.02:  # 2% above 50-day high
                    breakout_points += 10
            
            conviction += breakout_points
            details['breakout_power'] = breakout_points
            details['high_20'] = high_20
            details['high_50'] = high_50
            
            # Factor 2: Volume confirmation (0-30 points)
            volume_avg_20 = df['volume'].rolling(20).mean().iloc[-2]  # Exclude current day
            current_volume = current['volume']
            volume_surge = current_volume / volume_avg_20 if volume_avg_20 > 0 else 0
            
            volume_points = 0
            if volume_surge > 2.0:  # 2x volume
                volume_points = 30
            elif volume_surge > 1.5:  # 1.5x volume
                volume_points = 20
            elif volume_surge > 1.2:  # 1.2x volume
                volume_points = 10
            
            conviction += volume_points
            details['volume_surge'] = volume_surge
            details['volume_points'] = volume_points
            details['current_volume'] = current_volume
            details['avg_volume'] = volume_avg_20
            
            # Factor 3: Daily momentum (0-25 points)
            daily_change = ((current_price / prev['close']) - 1) * 100
            momentum_5d = ((current_price / df['close'].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0
            momentum_20d = ((current_price / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
            momentum_50d = ((current_price / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
            
            momentum_points = 0
            if daily_change > 1:  # Strong daily move
                momentum_points += 5
            if momentum_5d > 2:
                momentum_points += 5
            if momentum_20d > 5:
                momentum_points += 10
            if momentum_50d > 10:
                momentum_points += 5
            
            conviction += momentum_points
            details['daily_change'] = daily_change
            details['momentum_5d'] = momentum_5d
            details['momentum_20d'] = momentum_20d
            details['momentum_50d'] = momentum_50d
            details['momentum_points'] = momentum_points
            
            # Factor 4: Trend quality bonus (0-20 points)
            trend_bonus = min(20, int((trend_strength - 60) / 2))
            conviction += trend_bonus
            details['trend_bonus'] = trend_bonus
            details['total_conviction'] = conviction
            
            # Convert to conviction level (0-100 -> 0-5)
            if conviction >= 85:
                level = 5
                reason = f"MAX conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 70:
                level = 4
                reason = f"HIGH conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 55:
                level = 3
                reason = f"STANDARD conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 40:
                level = 2
                reason = f"LOW conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x, daily: {daily_change:.1f}%"
            elif conviction >= 25:
                level = 1
                reason = f"MINIMAL conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            else:
                level = 0
                reason = f"No conviction: {conviction}, trend: {trend_strength:.0f}"
            
            return level, reason, details
            
        except Exception as e:
            self.logger.error(f"Error generating conviction signal for {symbol}: {e}")
            return 0, f"Error: {e}", {}
    
    def get_fundamental_data(self, symbol: str) -> Dict:
        """
        Get comprehensive fundamental data using Yahoo Finance
        Includes all Minervini fundamental criteria
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            fundamentals = {
                'symbol': symbol,
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                
                # Profitability metrics
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                'operating_margin': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0,
                
                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0,
                'revenue_quarterly_growth': info.get('revenueQuarterlyGrowth', 0) * 100 if info.get('revenueQuarterlyGrowth') else 0,
                
                # Financial strength
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                'total_debt_to_equity': info.get('totalDebtToEquity', 0) / 100 if info.get('totalDebtToEquity') else 0,
                
                # Cash flow
                'free_cashflow': info.get('freeCashflow', 0),
                'operating_cashflow': info.get('operatingCashflow', 0),
                
                # Other metrics
                'book_value': info.get('bookValue', 0),
                'price_to_book': info.get('priceToBook', 0),
                'enterprise_to_revenue': info.get('enterpriseToRevenue', 0),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda', 0),
                
                # Analyst data
                'target_high_price': info.get('targetHighPrice', 0),
                'target_low_price': info.get('targetLowPrice', 0),
                'target_mean_price': info.get('targetMeanPrice', 0),
                'recommendation_mean': info.get('recommendationMean', 0),
                'number_of_analyst_opinions': info.get('numberOfAnalystOpinions', 0)
            }
            
            return fundamentals
            
        except Exception as e:
            self.logger.debug(f"Error getting fundamental data for {symbol}: {e}")
            return {}
    
    def calculate_fundamental_score(self, fundamentals: Dict) -> Tuple[float, Dict]:
        """
        Calculate Minervini fundamental score (0-100) 
        Based on his key criteria adapted for both US and ASX stocks
        """
        score = 0
        breakdown = {}
        
        try:
            # Criterion 1: ROE >= 15% (20 points)
            roe = fundamentals.get('roe', 0)
            if roe >= 15:
                score += 20
                breakdown['roe'] = f"PASS {roe:.1f}% (>15%)"
            elif roe >= 10:
                score += 10
                breakdown['roe'] = f"PARTIAL {roe:.1f}% (>10%)"
            else:
                breakdown['roe'] = f"FAIL {roe:.1f}% (<10%)"
            
            # Criterion 2: Earnings Growth >= 18% (20 points)
            earnings_growth = max(
                fundamentals.get('earnings_growth', 0),
                fundamentals.get('earnings_quarterly_growth', 0)
            )
            if earnings_growth >= 18:
                score += 20
                breakdown['earnings_growth'] = f"PASS {earnings_growth:.1f}% (>18%)"
            elif earnings_growth >= 10:
                score += 10
                breakdown['earnings_growth'] = f"PARTIAL {earnings_growth:.1f}% (>10%)"
            else:
                breakdown['earnings_growth'] = f"FAIL {earnings_growth:.1f}% (<10%)"
            
            # Criterion 3: Revenue Growth >= 15% (15 points)
            revenue_growth = max(
                fundamentals.get('revenue_growth', 0),
                fundamentals.get('revenue_quarterly_growth', 0)
            )
            if revenue_growth >= 15:
                score += 15
                breakdown['revenue_growth'] = f"PASS {revenue_growth:.1f}% (>15%)"
            elif revenue_growth >= 8:
                score += 8
                breakdown['revenue_growth'] = f"PARTIAL {revenue_growth:.1f}% (>8%)"
            else:
                breakdown['revenue_growth'] = f"FAIL {revenue_growth:.1f}% (<8%)"
            
            # Criterion 4: Debt-to-Equity <= 0.3 (15 points)
            debt_to_equity = fundamentals.get('debt_to_equity', 0)
            if debt_to_equity <= 0.3 and debt_to_equity > 0:
                score += 15
                breakdown['debt_to_equity'] = f"PASS {debt_to_equity:.2f} (<0.3)"
            elif debt_to_equity <= 0.5:
                score += 8
                breakdown['debt_to_equity'] = f"PARTIAL {debt_to_equity:.2f} (<0.5)"
            else:
                breakdown['debt_to_equity'] = f"FAIL {debt_to_equity:.2f} (>0.5)"
            
            # Criterion 5: Profit Margin >= 10% (10 points)
            profit_margin = fundamentals.get('profit_margin', 0)
            if profit_margin >= 10:
                score += 10
                breakdown['profit_margin'] = f"PASS {profit_margin:.1f}% (>10%)"
            elif profit_margin >= 5:
                score += 5
                breakdown['profit_margin'] = f"PARTIAL {profit_margin:.1f}% (>5%)"
            else:
                breakdown['profit_margin'] = f"FAIL {profit_margin:.1f}% (<5%)"
            
            # Criterion 6: Current Ratio >= 1.5 (10 points)
            current_ratio = fundamentals.get('current_ratio', 0)
            if current_ratio >= 1.5:
                score += 10
                breakdown['current_ratio'] = f"PASS {current_ratio:.2f} (>1.5)"
            elif current_ratio >= 1.0:
                score += 5
                breakdown['current_ratio'] = f"PARTIAL {current_ratio:.2f} (>1.0)"
            else:
                breakdown['current_ratio'] = f"FAIL {current_ratio:.2f} (<1.0)"
            
            # Criterion 7: PE Ratio reasonable (10 points)
            pe_ratio = fundamentals.get('pe_ratio', 0)
            if 10 <= pe_ratio <= 30:
                score += 10
                breakdown['pe_ratio'] = f"PASS {pe_ratio:.1f} (10-30)"
            elif 5 <= pe_ratio <= 50:
                score += 5
                breakdown['pe_ratio'] = f"PARTIAL {pe_ratio:.1f} (5-50)"
            else:
                breakdown['pe_ratio'] = f"FAIL {pe_ratio:.1f} (extreme)"
            
            breakdown['total_score'] = score
            breakdown['grade'] = (
                'A' if score >= 80 else
                'B' if score >= 60 else  
                'C' if score >= 40 else
                'D' if score >= 20 else 'F'
            )
            
            return score, breakdown
            
        except Exception as e:
            self.logger.error(f"Error calculating fundamental score: {e}")
            return 0, {'error': str(e)}
    
    def scan_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Scan a single symbol for conviction signals using daily data
        """
        try:
            self.logger.debug(f"Scanning {symbol}...")
            
            # Get daily data
            df = self.get_symbol_data(symbol)
            if df is None:
                return None
            
            current = df.iloc[-1]
            price = current['close']
            volume = current['volume']
            
            # Basic filters (minimal filtering for full coverage)
            if price < self.min_price:
                self.logger.debug(f"{symbol}: Price too low (${price:.2f})")
                return None
            
            # Check average volume
            if len(df) >= 20:
                avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                if avg_volume < self.min_avg_volume:
                    self.logger.debug(f"{symbol}: Average volume too low ({avg_volume:,.0f})")
                    return None
            
            # Get fundamental analysis
            fundamentals = self.get_fundamental_data(symbol)
            fundamental_score, fundamental_breakdown = self.calculate_fundamental_score(fundamentals)
            
            # Check market cap filter
            market_cap = fundamentals.get('market_cap', 0)
            if market_cap > 0 and market_cap < self.min_market_cap:
                self.logger.debug(f"{symbol}: Market cap too low (${market_cap/1e6:.0f}M < ${self.min_market_cap/1e6:.0f}M)")
                return None
            
            # Generate conviction signal
            conviction_level, reason, details = self.generate_conviction_signal(symbol, df)
            
            # Calculate new metrics
            atr = self.calculate_atr(df)
            atr_percentage = (atr / price * 100) if price > 0 else 0
            percentage_gains = self.calculate_percentage_gains(df)
            
            # Create result with comprehensive fundamental data
            result = {
                'symbol': symbol,
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'data_date': str(current['date']) if 'date' in current else str(df.index[-1]),
                'price': price,
                'volume': volume,
                'avg_volume_20d': df['volume'].rolling(20).mean().iloc[-1],
                'daily_change_pct': ((price / df['close'].iloc[-2]) - 1) * 100 if len(df) >= 2 else 0,
                'week_gain_pct': percentage_gains['week_gain'],
                'month_gain_pct': percentage_gains['month_gain'],
                'atr': atr,
                'atr_percentage': atr_percentage,
                'conviction_level': conviction_level,
                'conviction_reason': reason,
                'conviction_details': details,
                'position_size_pct': {
                    1: 20, 2: 25, 3: 30, 4: 35, 5: 40
                }.get(conviction_level, 0),
                'ib_action': 'BUY' if conviction_level >= 2 else 'WATCH',
                'stop_loss_price': price * 0.93,  # 7% stop
                'profit_target_price': price * 1.50,  # 50% target
                
                # Fundamental Analysis (All Minervini Criteria)
                'fundamental_score': fundamental_score,
                'fundamental_grade': fundamental_breakdown.get('grade', 'N/A'),
                'market_cap': fundamentals.get('market_cap', 0),
                'pe_ratio': fundamentals.get('pe_ratio', 0),
                'forward_pe': fundamentals.get('forward_pe', 0),
                'peg_ratio': fundamentals.get('peg_ratio', 0),
                
                # Profitability
                'roe': fundamentals.get('roe', 0),
                'roa': fundamentals.get('roa', 0),
                'profit_margin': fundamentals.get('profit_margin', 0),
                'gross_margin': fundamentals.get('gross_margin', 0),
                'operating_margin': fundamentals.get('operating_margin', 0),
                
                # Growth
                'revenue_growth': fundamentals.get('revenue_growth', 0),
                'earnings_growth': fundamentals.get('earnings_growth', 0),
                'earnings_quarterly_growth': fundamentals.get('earnings_quarterly_growth', 0),
                'revenue_quarterly_growth': fundamentals.get('revenue_quarterly_growth', 0),
                
                # Financial Strength
                'current_ratio': fundamentals.get('current_ratio', 0),
                'quick_ratio': fundamentals.get('quick_ratio', 0),
                'debt_to_equity': fundamentals.get('debt_to_equity', 0),
                'total_debt_to_equity': fundamentals.get('total_debt_to_equity', 0),
                
                # Cash Flow
                'free_cashflow': fundamentals.get('free_cashflow', 0),
                'operating_cashflow': fundamentals.get('operating_cashflow', 0),
                
                # Valuation
                'book_value': fundamentals.get('book_value', 0),
                'price_to_book': fundamentals.get('price_to_book', 0),
                'enterprise_to_revenue': fundamentals.get('enterprise_to_revenue', 0),
                'enterprise_to_ebitda': fundamentals.get('enterprise_to_ebitda', 0),
                
                # Analyst Coverage
                'target_mean_price': fundamentals.get('target_mean_price', 0),
                'target_high_price': fundamentals.get('target_high_price', 0),
                'target_low_price': fundamentals.get('target_low_price', 0),
                'recommendation_mean': fundamentals.get('recommendation_mean', 0),
                'number_of_analyst_opinions': fundamentals.get('number_of_analyst_opinions', 0),
                
                # Technical Analysis Breakdown
                'trend_strength': details.get('trend_strength', 0),
                'breakout_power': details.get('breakout_power', 0),
                'volume_surge': details.get('volume_surge', 0),
                'momentum_points': details.get('momentum_points', 0),
                'total_conviction_score': details.get('total_conviction', 0),
                
                # Fundamental Breakdown Summary
                'fundamental_breakdown': fundamental_breakdown
            }
            
            # Log significant findings
            if conviction_level >= 3:
                self.logger.info(f"HIGH CONVICTION: {symbol} - Level {conviction_level} - ${price:.2f} - {reason}")
                self.conviction_alerts.append(result)
            elif conviction_level >= 2:
                self.logger.info(f"TRADE CANDIDATE: {symbol} - Level {conviction_level} - ${price:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            return None
    
    def get_sp500_symbols(self) -> List[str]:
        """Get COMPLETE S&P 500 symbol list for full market scanning"""
        return [
            # Technology (Complete)
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'ADBE',
            'CRM', 'ORCL', 'AVGO', 'AMD', 'QCOM', 'TXN', 'INTC', 'IBM', 'AMAT', 'ADI',
            'CSCO', 'ACN', 'INTU', 'NOW', 'PANW', 'ANET', 'PLTR', 'MU', 'LRCX', 'KLAC',
            'CDNS', 'SNPS', 'FTNT', 'TEAM', 'ADSK', 'WDAY', 'MCHP', 'ENPH', 'FSLR', 'ON',
            
            # Healthcare (Complete)
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'LLY', 'MDT', 'BMY', 'AMGN',
            'GILD', 'CVS', 'CI', 'ANTM', 'HUM', 'BDX', 'SYK', 'BSX', 'EW', 'DHR',
            'ISRG', 'REGN', 'VRTX', 'ZTS', 'DXCM', 'BIIB', 'ILMN', 'IQV', 'A', 'RMD',
            'ALGN', 'MRNA', 'TECH', 'HOLX', 'IDXX', 'WAT', 'DGX', 'LH', 'SOLV', 'PKI',
            'BAX', 'BIO', 'XRAY', 'ZBH', 'WST', 'PODD', 'VTRS', 'RVTY', 'CAH', 'COR',
            
            # Financials (Complete) 
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'SPGI',
            'CME', 'ICE', 'MCO', 'COF', 'TRV', 'PGR', 'AFL', 'ALL', 'MET', 'PRU',
            'USB', 'PNC', 'FIS', 'AIG', 'TFC', 'BK', 'STT', 'FITB', 'AMP', 'TROW',
            'DFS', 'SYF', 'NTRS', 'RF', 'CFG', 'KEY', 'WRB', 'L', 'CINF', 'HBAN',
            'FDS', 'RJF', 'BRO', 'CBOE', 'IVZ', 'ZION', 'ETFC', 'JKHY', 'MKTX', 'NDAQ',
            
            # Consumer Discretionary (Complete)
            'HD', 'MCD', 'NKE', 'SBUX', 'TJX', 'LOW', 'TGT', 'DIS', 'BKNG', 'MAR',
            'GM', 'F', 'ABNB', 'EBAY', 'ETSY', 'EXPE', 'HLT', 'LVS', 'MGM', 'NCLH',
            'RCL', 'CCL', 'WYNN', 'YUM', 'CMG', 'DDOG', 'POOL', 'TPG', 'GPC', 'ORLY',
            'AAP', 'AZO', 'BBY', 'ULTA', 'DPZ', 'QSR', 'ROST', 'TJX', 'DECK', 'NVR',
            'PHM', 'LEN', 'DHI', 'TOL', 'KBH', 'TPX', 'MHK', 'WHR', 'LZB', 'GRMN',
            
            # Consumer Staples (Complete)
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'EL', 'CL', 'KMB', 'GIS',
            'MDLZ', 'KHC', 'KR', 'SYY', 'ADM', 'TSN', 'K', 'CAG', 'CPB', 'HRL',
            'HSY', 'MKC', 'CLX', 'CHD', 'SJM', 'LW', 'TAP', 'BF-B', 'PM', 'MO',
            
            # Industrials (Complete)
            'UPS', 'HON', 'BA', 'UNP', 'RTX', 'LMT', 'CAT', 'DE', 'MMM', 'GE',
            'FDX', 'LUV', 'AAL', 'DAL', 'UAL', 'JBHT', 'CSX', 'NSC', 'KSU', 'CNI',
            'EMR', 'ETN', 'ITW', 'PH', 'ROK', 'DOV', 'FTV', 'IR', 'GNRC', 'PWR',
            'JCI', 'CARR', 'OTIS', 'PCAR', 'CMI', 'WAB', 'ALK', 'CHRW', 'EXPD', 'LDOS',
            'LHX', 'NOC', 'GD', 'TXT', 'ALLE', 'AXON', 'HUBB', 'PAYC', 'RSG', 'WM',
            'URI', 'VRSK', 'FAST', 'J', 'SWK', 'IEX', 'XYL', 'AOS', 'PNR', 'RHI',
            
            # Energy (Complete)
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
            'KMI', 'WMB', 'OKE', 'TRGP', 'EPD', 'MPLX', 'BKR', 'DVN', 'FANG', 'MRO',
            'APA', 'HES', 'CTRA', 'EQT', 'CNP', 'FTI', 'NOV', 'RIG', 'HP', 'CHK',
            
            # Utilities (Complete)
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'XEL', 'SRE', 'PEG', 'ED', 'FE',
            'ETR', 'ES', 'AWK', 'DTE', 'PPL', 'WEC', 'LNT', 'CMS', 'EVRG', 'CNP',
            'NI', 'PCG', 'IDA', 'AES', 'NRG', 'VST', 'PNW', 'ATO', 'CEG', 'UGI',
            
            # Communication Services (Complete)
            'VZ', 'T', 'CMCSA', 'CHTR', 'TMUS', 'NFLX', 'GOOGL', 'GOOG', 'META', 'DIS',
            'PARA', 'WBD', 'FOXA', 'FOX', 'DISH', 'OMC', 'IPG', 'TTWO', 'EA', 'ATVI',
            'MTCH', 'PINS', 'SNAP', 'TWTR', 'LUMN', 'SIRI', 'TKO', 'LYV', 'NWSA', 'NWS',
            
            # Materials (Complete)
            'LIN', 'APD', 'ECL', 'DD', 'DOW', 'SHW', 'FCX', 'NEM', 'PPG', 'IFF',
            'LYB', 'CF', 'FMC', 'ALB', 'EMN', 'MOS', 'VMC', 'MLM', 'PKG', 'BALL',
            'AMCR', 'AVY', 'IP', 'CE', 'WRK', 'KNX', 'SEE', 'CCK', 'SON', 'SMG',
            
            # Real Estate (Complete)
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'DLR', 'O', 'SBAC', 'EXR',
            'AVB', 'EQR', 'VTR', 'ESS', 'MAA', 'UDR', 'CPT', 'HST', 'REG', 'BXP',
            'KIM', 'SPG', 'FRT', 'SLG', 'VNO', 'BRX', 'KRC', 'HIW', 'PEAK', 'CUZ',
            
            # Additional S&P 500 Companies
            'GOOG', 'GOOGL', 'BRK-A', 'BRK-B', 'UNH', 'XOM', 'JNJ', 'CVX', 'PG', 'LLY',
            'HD', 'BAC', 'ABBV', 'PFE', 'KO', 'MRK', 'AVGO', 'PEP', 'TMO', 'WMT',
            'ABT', 'CRM', 'ACN', 'VZ', 'DHR', 'TXN', 'LIN', 'NEE', 'CMCSA', 'RTX',
            'AMD', 'QCOM', 'WFC', 'PM', 'SPGI', 'T', 'UNP', 'LOW', 'HON', 'UPS',
            'CAT', 'SBUX', 'AXP', 'GS', 'DE', 'BKNG', 'BLK', 'SYK', 'LMT', 'GILD',
            'ADI', 'MDLZ', 'TJX', 'CVS', 'ADP', 'CI', 'C', 'REGN', 'CB', 'MCD',
            'SO', 'SCHW', 'PGR', 'ISRG', 'MMM', 'MU', 'ZTS', 'EOG', 'DUK', 'BSX',
            'ICE', 'ANTM', 'APD', 'CSX', 'SLB', 'PYPL', 'CME', 'ITW', 'COP', 'ECL',
            'PNC', 'AON', 'FCX', 'USB', 'GM', 'MSI', 'WM', 'HUM', 'MAR', 'TGT',
            'F', 'MCO', 'KLAC', 'AEP', 'NFLX', 'EMR', 'SHW', 'GD', 'ADSK', 'JCI',
            'DIS', 'PSX', 'ORLY', 'TFC', 'ANET', 'NKE', 'AZO', 'DXCM', 'EW', 'FIS',
            'NSC', 'ROP', 'ROST', 'CTSH', 'CARR', 'KMB', 'FAST', 'PAYX', 'ODFL',
            'YUM', 'EA', 'VRTX', 'KR', 'EL', 'LRCX', 'OTIS', 'CTAS', 'VRSK', 'IDXX',
            'GWW', 'A', 'CMG', 'XEL', 'MSCI', 'MNST', 'FTNT', 'CTVA', 'GLW', 'HCA',
            'PCAR', 'ALL', 'AIG', 'TRV', 'AFL', 'WELL', 'PSA', 'MET', 'PRU', 'AJG'
        ]
    
    def get_asx300_symbols(self) -> List[str]:
        """Get COMPLETE ASX300 symbol list for full market scanning"""
        return [
            # Big 4 Banks
            'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX',
            
            # Regional Banks & Finance
            'BOQ.AX', 'BEN.AX', 'AMP.AX', 'IFL.AX', 'PDL.AX', 'CCP.AX', 'AUB.AX', 'HUB.AX',
            'PNI.AX', 'FSF.AX', 'PTM.AX', 'CKF.AX', 'MYR.AX', 'PPT.AX', 'NHF.AX', 'MOT.AX',
            
            # Mining - Iron Ore & Steel
            'BHP.AX', 'RIO.AX', 'FMG.AX', 'MIN.AX', 'CIA.AX', 'AGO.AX', 'GWR.AX', 'IOH.AX',
            'BCI.AX', 'MGX.AX', 'CAP.AX', 'MRC.AX', 'BC8.AX', 'ROC.AX', 'AHQ.AX', 'FEX.AX',
            
            # Mining - Gold
            'NCM.AX', 'NST.AX', 'EVN.AX', 'RRL.AX', 'RED.AX', 'SBM.AX', 'RSG.AX', 'SAR.AX',
            'OGC.AX', 'GOR.AX', 'DCN.AX', 'PNR.AX', 'GCY.AX', 'WAF.AX', 'BGL.AX', 'DEG.AX',
            'AVL.AX', 'TMZ.AX', 'KLA.AX', 'AQG.AX', 'TRY.AX', 'OZL.AX', 'SLR.AX', 'PRU.AX',
            
            # Mining - Base Metals & Resources
            'S32.AX', 'WSA.AX', 'IGO.AX', 'ALD.AX', 'SFR.AX', 'MAH.AX', 'IXR.AX', 'PAN.AX',
            'MLX.AX', 'HMY.AX', 'PXG.AX', 'VMC.AX', 'POL.AX', 'CHN.AX', 'AAU.AX', 'ARE.AX',
            'MMI.AX', 'SIH.AX', 'NIC.AX', 'CXO.AX', 'LYC.AX', 'PLS.AX', 'AGY.AX', 'PIL.AX',
            
            # Mining - Coal & Energy
            'WHC.AX', 'NHC.AX', 'YAL.AX', 'TER.AX', 'BKW.AX', 'CKA.AX', 'COK.AX', 'GRL.AX',
            'STX.AX', 'MGH.AX', 'EHE.AX', 'CZI.AX', 'TNE.AX', 'WHE.AX', 'WCN.AX', 'WEL.AX',
            
            # Oil & Gas
            'STO.AX', 'WDS.AX', 'ORG.AX', 'BWP.AX', 'BPT.AX', 'DLS.AX', 'SXY.AX', 'COE.AX',
            'CVN.AX', 'ADN.AX', 'SEA.AX', 'EPW.AX', 'STX.AX', 'PZE.AX', 'GAS.AX', 'KEY.AX',
            'BRU.AX', 'FAR.AX', 'TDO.AX', 'ESG.AX', 'OSH.AX', 'MHI.AX', 'AGK.AX', 'STN.AX',
            
            # Healthcare & Biotech - Major
            'CSL.AX', 'COH.AX', 'RMD.AX', 'SHL.AX', 'NAN.AX', 'PME.AX', 'FPH.AX', 'RHC.AX',
            'IMP.AX', 'NEU.AX', 'SIP.AX', 'ONT.AX', 'IMU.AX', 'MP1.AX', 'PRR.AX', 'EBO.AX',
            
            # Healthcare & Biotech - Mid/Small Cap
            'MEB.AX', 'CGC.AX', 'VHT.AX', 'SOM.AX', 'MSB.AX', 'PTB.AX', 'RAC.AX', 'API.AX',
            'VCX.AX', 'CSC.AX', 'IPD.AX', 'KSC.AX', 'TIE.AX', 'SRX.AX', 'PAB.AX', 'LBT.AX',
            'VAH.AX', 'HLS.AX', 'GUD.AX', 'AVH.AX', 'ACR.AX', 'ALG.AX', 'BNO.AX', 'IMU.AX',
            
            # Technology & Growth - Major
            'XRO.AX', 'WTC.AX', 'TNE.AX', 'CPU.AX', 'KGN.AX', 'NXT.AX', 'APX.AX', 'ZIP.AX',
            'CRO.AX', 'CAR.AX', 'REA.AX', 'SEK.AX', 'IRI.AX', 'PBH.AX', 'NEA.AX', 'DTL.AX',
            
            # Technology & Growth - Emerging
            'BRN.AX', 'LKE.AX', 'BYE.AX', 'AR9.AX', 'SYA.AX', 'FFG.AX', 'PNV.AX', 'KTD.AX',
            'MNY.AX', 'EML.AX', 'DW8.AX', 'IOU.AX', 'Z1P.AX', 'SZL.AX', 'LYV.AX', 'RNY.AX',
            'HUB.AX', 'AD8.AX', 'FLT.AX', 'WEB.AX', 'CLV.AX', 'MSV.AX', 'EOS.AX', 'TNT.AX',
            
            # Telecommunications
            'TLS.AX', 'TCL.AX', 'TPG.AX', 'VOC.AX', 'SPK.AX', 'SVW.AX', 'MYX.AX', 'CM8.AX',
            
            # Retail & Consumer - Major
            'WOW.AX', 'COL.AX', 'WES.AX', 'JBH.AX', 'HVN.AX', 'SUL.AX', 'KMD.AX', 'DMP.AX',
            'MYR.AX', 'PMV.AX', 'BBN.AX', 'KAR.AX', 'AMI.AX', 'BRG.AX', 'HSN.AX', 'LOV.AX',
            
            # Food & Agriculture
            'A2M.AX', 'BAP.AX', 'SHV.AX', 'BKL.AX', 'TRY.AX', 'CCL.AX', 'PFG.AX', 'GNC.AX',
            'FGR.AX', 'AAC.AX', 'AHY.AX', 'CMD.AX', 'FFG.AX', 'RFG.AX', 'CLV.AX', 'CUV.AX',
            'GFF.AX', 'MHG.AX', 'RIC.AX', 'SCA.AX', 'SDF.AX', 'TGR.AX', 'WBA.AX', 'WHO.AX',
            
            # Industrials & Infrastructure - Major
            'QBE.AX', 'IAG.AX', 'SUN.AX', 'QAN.AX', 'ALL.AX', 'APA.AX', 'AGL.AX', 'ORE.AX',
            'AST.AX', 'SYD.AX', 'AZJ.AX', 'TUA.AX', 'SGP.AX', 'SKI.AX', 'ALU.AX', 'BLD.AX',
            
            # Industrials & Infrastructure - Mid Cap
            'WOR.AX', 'DOW.AX', 'FBU.AX', 'NWL.AX', 'CSR.AX', 'JHX.AX', 'BSL.AX', 'DXS.AX',
            'ABC.AX', 'ALQ.AX', 'AWC.AX', 'BKW.AX', 'BOC.AX', 'BXB.AX', 'CNU.AX', 'DTL.AX',
            'ERD.AX', 'FSA.AX', 'GOZ.AX', 'GWA.AX', 'IPL.AX', 'IRE.AX', 'LEI.AX', 'MND.AX',
            'NUF.AX', 'ORA.AX', 'ORI.AX', 'PMP.AX', 'QUB.AX', 'RWC.AX', 'SIG.AX', 'UGL.AX',
            
            # REITs & Property - Major
            'SCG.AX', 'GMG.AX', 'VCX.AX', 'DXS.AX', 'CHC.AX', 'MGR.AX', 'GPT.AX', 'LLC.AX',
            'URW.AX', 'BWP.AX', 'SCP.AX', 'CMW.AX', 'HSO.AX', 'AOF.AX', 'CQR.AX', 'HMC.AX',
            
            # REITs & Property - Diversified
            'GOZ.AX', 'FKP.AX', 'AVJ.AX', 'CIP.AX', 'CNI.AX', 'CLW.AX', 'CWN.AX', 'DJW.AX',
            'EHL.AX', 'FLT.AX', 'GDI.AX', 'HPI.AX', 'IOF.AX', 'NSR.AX', 'PWH.AX', 'RNT.AX',
            'SLF.AX', 'SPL.AX', 'SRV.AX', 'TOT.AX', 'UOS.AX', 'WLE.AX', 'WPR.AX', 'ARF.AX',
            
            # Financial Services - Diversified
            'MQG.AX', 'ASX.AX', 'PPT.AX', 'NHF.AX', 'HUB.AX', 'PNI.AX', 'FSF.AX', 'PTM.AX',
            'CKF.AX', 'MOT.AX', 'NVT.AX', 'CLH.AX', 'CRN.AX', 'PPS.AX', 'RFF.AX', 'VYS.AX',
            
            # Materials & Chemicals
            'ORI.AX', 'IPL.AX', 'JHX.AX', 'AWC.AX', 'NUF.AX', 'IPH.AX', 'BOC.AX', 'CSR.AX',
            'BSL.AX', 'KWS.AX', 'ABC.AX', 'BLD.AX', 'CWN.AX', 'IRE.AX', 'LEI.AX', 'ORA.AX',
            
            # Utilities & Energy Infrastructure
            'AEF.AX', 'AGL.AX', 'GPU.AX', 'AST.AX', 'SKI.AX', 'SPN.AX', 'CNI.AX', 'DUE.AX',
            'ENE.AX', 'EPW.AX', 'GAS.AX', 'KEY.AX', 'LGP.AX', 'NGE.AX', 'PWH.AX', 'TAG.AX',
            
            # Media & Entertainment
            'SWM.AX', 'NEC.AX', 'IVC.AX', 'PRT.AX', 'TEN.AX', 'WIN.AX', 'NWS.AX', 'TEL.AX',
            
            # Transport & Logistics
            'CTX.AX', 'TNT.AX', 'MMS.AX', 'STG.AX', 'FLT.AX', 'AUF.AX', 'CLH.AX', 'GUD.AX',
            
            # Education & Training
            'IEL.AX', 'MMS.AX', 'VET.AX', 'TOP.AX', 'BAL.AX', 'RED.AX',
            
            # Tourism & Leisure
            'SRG.AX', 'CWN.AX', 'SYD.AX', 'FLT.AX', 'WEB.AX', 'CTD.AX', 'CLV.AX',
            
            # Small Caps with Potential
            'PBH.AX', 'FFG.AX', 'RNY.AX', 'EMR.AX', 'BRN.AX', 'LKE.AX', 'AGY.AX', 'PIL.AX',
            'VUL.AX', 'CXO.AX', 'LYC.AX', 'PLS.AX', 'TMZ.AX', 'DEG.AX', 'WAF.AX', 'BGL.AX',
            'AVL.AX', 'KLA.AX', 'AQG.AX', 'SLR.AX', 'PRU.AX', 'CAP.AX', 'MRC.AX', 'ROC.AX'
        ]
    
    def scan_market(self, symbols: List[str], market_name: str) -> List[Dict]:
        """
        Scan multiple symbols for daily conviction signals
        """
        results = []
        total_symbols = len(symbols)
        
        self.logger.info(f"Starting {market_name} scan of {total_symbols} symbols...")
        start_time = time.time()
        
        for i, symbol in enumerate(symbols, 1):
            try:
                if i % 10 == 0:  # Progress update every 10 symbols
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total_symbols - i) / rate if rate > 0 else 0
                    self.logger.info(f"Progress: {i}/{total_symbols} ({i/total_symbols*100:.1f}%) - {rate:.1f} symbols/sec - ETA: {eta:.0f}s")
                
                result = self.scan_symbol(symbol)
                if result:
                    results.append(result)
                    self.scan_results.append(result)
                
                # Rate limiting - be respectful to Yahoo Finance
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                self.logger.info("Scan interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in market scan for {symbol}: {e}")
                continue
        
        scan_time = time.time() - start_time
        self.logger.info(f"{market_name} scan complete - {len(results)} symbols processed in {scan_time:.1f}s")
        return results
    
    def export_results(self, filename: str = None) -> str:
        """Export scan results to CSV for IB trade planning"""
        try:
            if not self.scan_results:
                self.logger.warning("No scan results to export")
                return ""
            
            # Create DataFrame with comprehensive trading and fundamental information
            export_data = []
            for result in self.scan_results:
                row = {
                    # Trading Information
                    'scan_date': result['scan_date'],
                    'data_date': result['data_date'],
                    'symbol': result['symbol'],
                    'ib_action': result['ib_action'],
                    'conviction_level': result['conviction_level'],
                    'position_size_pct': result['position_size_pct'],
                    'current_price': result['price'],
                    'stop_loss_price': result['stop_loss_price'],
                    'profit_target_price': result['profit_target_price'],
                    'daily_change_pct': result['daily_change_pct'],
                    'week_gain_pct': result.get('week_gain_pct', 0),
                    'month_gain_pct': result.get('month_gain_pct', 0),
                    'atr': result.get('atr', 0),
                    'atr_percentage': result.get('atr_percentage', 0),
                    'volume': result['volume'],
                    'avg_volume_20d': result['avg_volume_20d'],
                    'conviction_reason': result['conviction_reason'],
                    
                    # Fundamental Analysis (All Minervini Criteria)
                    'fundamental_score': result.get('fundamental_score', 0),
                    'fundamental_grade': result.get('fundamental_grade', 'N/A'),
                    'market_cap': result.get('market_cap', 0),
                    'pe_ratio': result.get('pe_ratio', 0),
                    'forward_pe': result.get('forward_pe', 0),
                    'peg_ratio': result.get('peg_ratio', 0),
                    
                    # Profitability Metrics
                    'roe': result.get('roe', 0),
                    'roa': result.get('roa', 0),
                    'profit_margin': result.get('profit_margin', 0),
                    'gross_margin': result.get('gross_margin', 0),
                    'operating_margin': result.get('operating_margin', 0),
                    
                    # Growth Metrics
                    'revenue_growth': result.get('revenue_growth', 0),
                    'earnings_growth': result.get('earnings_growth', 0),
                    'earnings_quarterly_growth': result.get('earnings_quarterly_growth', 0),
                    'revenue_quarterly_growth': result.get('revenue_quarterly_growth', 0),
                    
                    # Financial Strength
                    'current_ratio': result.get('current_ratio', 0),
                    'quick_ratio': result.get('quick_ratio', 0),
                    'debt_to_equity': result.get('debt_to_equity', 0),
                    'total_debt_to_equity': result.get('total_debt_to_equity', 0),
                    
                    # Cash Flow
                    'free_cashflow': result.get('free_cashflow', 0),
                    'operating_cashflow': result.get('operating_cashflow', 0),
                    
                    # Valuation Metrics
                    'book_value': result.get('book_value', 0),
                    'price_to_book': result.get('price_to_book', 0),
                    'enterprise_to_revenue': result.get('enterprise_to_revenue', 0),
                    'enterprise_to_ebitda': result.get('enterprise_to_ebitda', 0),
                    
                    # Analyst Coverage
                    'target_mean_price': result.get('target_mean_price', 0),
                    'target_high_price': result.get('target_high_price', 0),
                    'target_low_price': result.get('target_low_price', 0),
                    'recommendation_mean': result.get('recommendation_mean', 0),
                    'number_of_analyst_opinions': result.get('number_of_analyst_opinions', 0)
                }
                
                # Add technical analysis details
                details = result.get('conviction_details', {})
                row.update({
                    'trend_strength': details.get('trend_strength', 0),
                    'breakout_power': details.get('breakout_power', 0),
                    'volume_surge': details.get('volume_surge', 0),
                    'momentum_points': details.get('momentum_points', 0),
                    'total_conviction_score': details.get('total_conviction', 0)
                })
                
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            
            # Sort by conviction level and total score
            df = df.sort_values(['conviction_level', 'total_conviction_score'], ascending=[False, False])
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"daily_conviction_scan_{timestamp}.csv"
            
            # Export
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported {len(df)} results to {filename}")
            
            # Also create a trade-ready summary
            trade_candidates = df[df['ib_action'] == 'BUY']
            if len(trade_candidates) > 0:
                trade_filename = filename.replace('.csv', '_TRADE_READY.csv')
                trade_candidates.to_csv(trade_filename, index=False)
                self.logger.info(f"Exported {len(trade_candidates)} trade candidates to {trade_filename}")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            return ""
    
    def print_summary(self):
        """Print scan summary with trading focus"""
        if not self.scan_results:
            print("No scan results available")
            return
        
        # Summary statistics
        total_scanned = len(self.scan_results)
        conviction_counts = {}
        for result in self.scan_results:
            level = result['conviction_level']
            conviction_counts[level] = conviction_counts.get(level, 0) + 1
        
        print("\n" + "=" * 80)
        print("DAILY CONVICTION SCAN SUMMARY")
        print("=" * 80)
        print(f"Total symbols scanned: {total_scanned}")
        print(f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("CONVICTION LEVEL DISTRIBUTION:")
        for level in range(6):
            count = conviction_counts.get(level, 0)
            pct = count / total_scanned * 100 if total_scanned > 0 else 0
            position_pct = {0: 0, 1: 20, 2: 25, 3: 30, 4: 35, 5: 40}.get(level, 0)
            action = "BUY" if level >= 2 else "WATCH"
            print(f"  Level {level} ({position_pct:2d}% position): {count:3d} stocks ({pct:5.1f}%) - {action}")
        
        # Trade candidates
        trade_candidates = [r for r in self.scan_results if r['conviction_level'] >= 2]
        if trade_candidates:
            print(f"\nTRADE CANDIDATES FOR NEXT DAY ({len(trade_candidates)} stocks):")
            print("-" * 120)
            print(f"{'Symbol':<8} {'Level':<6} {'Price':<10} {'Daily%':<8} {'Week%':<8} {'Month%':<8} {'ATR%':<7} {'Stop':<10} {'Target':<10} {'Reason':<25}")
            print("-" * 120)
            for candidate in sorted(trade_candidates, key=lambda x: x['conviction_level'], reverse=True)[:15]:
                print(f"{candidate['symbol']:<8} {candidate['conviction_level']:<6} "
                      f"${candidate['price']:<9.2f} {candidate['daily_change_pct']:>6.1f}% "
                      f"{candidate.get('week_gain_pct', 0):>6.1f}% {candidate.get('month_gain_pct', 0):>7.1f}% "
                      f"{candidate.get('atr_percentage', 0):>5.1f}% ${candidate['stop_loss_price']:<9.2f} "
                      f"${candidate['profit_target_price']:<9.2f} {candidate['conviction_reason'][:25]}")
        
        # High conviction alerts
        high_conviction = [r for r in self.scan_results if r['conviction_level'] >= 3]
        if high_conviction:
            print(f"\nHIGH CONVICTION ALERTS ({len(high_conviction)} stocks):")
            print("-" * 120)
            print(f"{'Symbol':<8} {'Level':<6} {'Price':<10} {'Daily%':<8} {'Week%':<8} {'Month%':<8} {'ATR%':<7} {'Reason':<25}")
            print("-" * 120)
            for result in sorted(high_conviction, key=lambda x: x['conviction_level'], reverse=True):
                print(f"  {result['symbol']:<8} Level {result['conviction_level']} - "
                      f"${result['price']:>8.2f} {result['daily_change_pct']:>6.1f}% "
                      f"{result.get('week_gain_pct', 0):>6.1f}% {result.get('month_gain_pct', 0):>7.1f}% "
                      f"{result.get('atr_percentage', 0):>5.1f}% - {result['conviction_reason'][:25]}")
        
        print("=" * 80)
        print("NEXT STEPS:")
        print("1. Review trade candidates in exported CSV")
        print("2. Set up orders in Interactive Brokers for Level 2+ stocks")
        print("3. Use stop loss and profit target prices provided")
        print("4. Monitor Level 1 stocks for future breakouts")
        print("=" * 80)


def main():
    """Main daily scanning function"""
    scanner = DailyConvictionScanner()
    
    try:
        print("\nSelect market to scan:")
        print("1. US Market (S&P 500)")
        print("2. ASX Market (ASX300)")
        print("3. Both markets")
        
        choice = input("Enter choice (1-3): ").strip()
        
        all_results = []
        
        if choice in ['1', '3']:
            # Scan US market
            us_symbols = scanner.get_sp500_symbols()
            print(f"\nScanning {len(us_symbols)} S&P 500 stocks...")
            us_results = scanner.scan_market(us_symbols, "US Market")
            all_results.extend(us_results)
        
        if choice in ['2', '3']:
            # Scan ASX market
            asx_symbols = scanner.get_asx300_symbols()
            print(f"\nScanning {len(asx_symbols)} ASX300 stocks...")
            asx_results = scanner.scan_market(asx_symbols, "ASX Market")
            all_results.extend(asx_results)
        
        if not all_results:
            print("No symbols scanned")
            return
        
        # Print summary
        scanner.print_summary()
        
        # Export results
        filename = scanner.export_results()
        if filename:
            print(f"\nResults exported to: {filename}")
            print("Import this CSV into your trade planning system")
        
        # Show top picks summary
        top_picks = [r for r in all_results if r['conviction_level'] >= 2]
        if top_picks:
            print(f"\nSUMMARY: {len(top_picks)} trade candidates identified")
            print("Ready for next-day execution on Interactive Brokers")
        else:
            print("\nNo high-conviction trade candidates found today")
            print("Monitor watchlist for future opportunities")
    
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error in main scan: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nDaily scan complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    print("DAILY CONVICTION SCANNER")
    print("End-of-day analysis using free Yahoo Finance data")
    print("Identifies high-conviction setups for next-day IB execution")
    print()
    
    main()