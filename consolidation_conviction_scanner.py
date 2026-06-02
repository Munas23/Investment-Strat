"""
Consolidation Conviction Scanner - Post-Move Consolidation Detector
================================================================

Specialized scanner focused on catching stocks AFTER their big moves, during consolidation periods.
This scanner looks for stocks that have had strong 3-6 month performance (30%+ gains) but are 
currently consolidating with low or shrinking ATR over the last 2-6 weeks.

Key Philosophy:
- Catch stocks after the big move, not during it
- Look for consolidation patterns (low ATR relative to stock's own history)
- Focus on strong 3-6 month performers that are digesting gains
- Reduced weight on recent momentum (last 2 weeks)

Features:
- 3-6 month performance filter (30%+ required)
- Shrinking/low ATR analysis for consolidation detection
- Reduced recent momentum weighting
- Post-breakout consolidation identification
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

class ConsolidationConvictionScanner:
    """
    Scanner focused on post-move consolidation patterns with strong medium-term performance
    """
    
    def __init__(self):
        """Initialize the consolidation scanner"""
        
        # Scanner settings - more selective for consolidation patterns
        self.fundamental_threshold = 50.0  # Lower threshold for post-move stocks
        self.min_price = 1.00  # Higher minimum price for quality stocks
        self.min_avg_volume = 50000  # Higher volume requirement
        self.min_market_cap = 500e6  # Higher market cap requirement ($500M+)
        self.max_market_cap = 50000e9  # High cap limit
        
        # Consolidation-specific criteria
        self.min_3month_gain = 30.0  # Minimum 30% gain over 3-6 months
        self.max_recent_atr_percentile = 60  # ATR should be in lower 60% recently
        self.atr_shrinkage_threshold = 0.8  # Recent ATR should be 80% or less of longer-term ATR
        
        # Scanning results
        self.scan_results = []
        self.consolidation_alerts = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('consolidation_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        print("=" * 60)
        print("CONSOLIDATION CONVICTION SCANNER")
        print("=" * 60)
        print("Post-Move Consolidation Pattern Detection")
        print(f"Scan date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def get_symbol_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d")
            
            if hist.empty or len(hist) < 200:  # Need more data for consolidation analysis
                self.logger.debug(f"{symbol}: Insufficient data ({len(hist)} days)")
                return None
            
            # Standardize column names
            hist.columns = [col.lower() for col in hist.columns]
            hist.index = pd.to_datetime(hist.index).date
            hist = hist.dropna()
            
            if len(hist) < 200:
                return None
            
            return hist.reset_index()
            
        except Exception as e:
            self.logger.debug(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_atr_series(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR series for trend analysis"""
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
            self.logger.error(f"Error calculating ATR series: {e}")
            return pd.Series(index=df.index, dtype=float)
    
    def analyze_consolidation_pattern(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze consolidation characteristics focusing on ATR patterns
        """
        try:
            if len(df) < 100:
                return {'consolidation_score': 0, 'details': 'Insufficient data'}
            
            current_price = df['close'].iloc[-1]
            
            # Calculate ATR series
            atr_14 = self.calculate_atr_series(df, 14)
            atr_21 = self.calculate_atr_series(df, 21)
            
            # Get recent periods for analysis
            recent_2weeks = slice(-10, None)  # Last 10 trading days (~2 weeks)
            recent_4weeks = slice(-20, None)  # Last 20 trading days (~4 weeks)
            recent_6weeks = slice(-30, None)  # Last 30 trading days (~6 weeks)
            older_period = slice(-90, -30)     # 30-90 days ago for comparison
            
            # ATR Analysis - Key consolidation indicator
            recent_atr_2w = atr_14.iloc[recent_2weeks].mean() if len(atr_14.iloc[recent_2weeks]) > 0 else 0
            recent_atr_4w = atr_14.iloc[recent_4weeks].mean() if len(atr_14.iloc[recent_4weeks]) > 0 else 0
            recent_atr_6w = atr_14.iloc[recent_6weeks].mean() if len(atr_14.iloc[recent_6weeks]) > 0 else 0
            older_atr = atr_14.iloc[older_period].mean() if len(atr_14.iloc[older_period]) > 0 else 0
            
            # ATR as percentage of price
            recent_atr_pct_2w = (recent_atr_2w / current_price * 100) if current_price > 0 else 0
            recent_atr_pct_4w = (recent_atr_4w / current_price * 100) if current_price > 0 else 0
            recent_atr_pct_6w = (recent_atr_6w / current_price * 100) if current_price > 0 else 0
            older_atr_pct = (older_atr / current_price * 100) if current_price > 0 else 0
            
            # Calculate ATR contraction ratios
            atr_contraction_2w = recent_atr_2w / older_atr if older_atr > 0 else 1
            atr_contraction_4w = recent_atr_4w / older_atr if older_atr > 0 else 1
            atr_contraction_6w = recent_atr_6w / older_atr if older_atr > 0 else 1
            
            # Medium-term performance (3-6 months)
            if len(df) >= 90:  # ~3 months
                price_3m_ago = df['close'].iloc[-90]
                gain_3m = ((current_price / price_3m_ago) - 1) * 100
            else:
                gain_3m = 0
                
            if len(df) >= 130:  # ~6 months
                price_6m_ago = df['close'].iloc[-130]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100
            else:
                gain_6m = gain_3m
            
            # Recent performance (should be lower for consolidation)
            if len(df) >= 10:  # 2 weeks
                price_2w_ago = df['close'].iloc[-10]
                gain_2w = ((current_price / price_2w_ago) - 1) * 100
            else:
                gain_2w = 0
                
            if len(df) >= 20:  # 4 weeks
                price_4w_ago = df['close'].iloc[-20]
                gain_4w = ((current_price / price_4w_ago) - 1) * 100
            else:
                gain_4w = 0
            
            # Price stability analysis
            recent_high = df['high'].iloc[recent_4weeks].max()
            recent_low = df['low'].iloc[recent_4weeks].min()
            recent_range_pct = ((recent_high / recent_low) - 1) * 100 if recent_low > 0 else 100
            
            # Volume analysis
            avg_volume_recent = df['volume'].iloc[recent_4weeks].mean()
            avg_volume_older = df['volume'].iloc[older_period].mean()
            volume_ratio = avg_volume_recent / avg_volume_older if avg_volume_older > 0 else 1
            
            return {
                'consolidation_score': 0,  # Will be calculated in main analysis
                'gain_3m': gain_3m,
                'gain_6m': gain_6m,
                'gain_2w': gain_2w,
                'gain_4w': gain_4w,
                'recent_atr_pct_2w': recent_atr_pct_2w,
                'recent_atr_pct_4w': recent_atr_pct_4w,
                'recent_atr_pct_6w': recent_atr_pct_6w,
                'older_atr_pct': older_atr_pct,
                'atr_contraction_2w': atr_contraction_2w,
                'atr_contraction_4w': atr_contraction_4w,
                'atr_contraction_6w': atr_contraction_6w,
                'recent_range_pct': recent_range_pct,
                'volume_ratio': volume_ratio,
                'current_atr_14': atr_14.iloc[-1] if len(atr_14) > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing consolidation pattern: {e}")
            return {'consolidation_score': 0, 'error': str(e)}
    
    def generate_consolidation_signal(self, symbol: str, df: pd.DataFrame) -> Tuple[int, str, Dict]:
        """
        Generate consolidation-focused conviction signal (0-5)
        Emphasizes post-move consolidation patterns
        """
        try:
            if len(df) < 150:
                return 0, "Insufficient historical data", {}
            
            current = df.iloc[-1]
            current_price = current['close']
            
            # Get consolidation analysis
            consolidation_data = self.analyze_consolidation_pattern(df)
            
            # Check primary filter: 3-6 month performance
            medium_term_gain = max(consolidation_data.get('gain_3m', 0), consolidation_data.get('gain_6m', 0))
            if medium_term_gain < self.min_3month_gain:
                return 0, f"Insufficient 3-6M gain: {medium_term_gain:.1f}% < {self.min_3month_gain}%", consolidation_data
            
            conviction = 0
            details = consolidation_data.copy()
            
            # Factor 1: Medium-term Performance Strength (0-30 points)
            # This is our primary filter - reward strong 3-6 month performance
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
            
            # Factor 2: ATR Consolidation Analysis (0-35 points) - MOST IMPORTANT
            # Reward contracting/low ATR indicating consolidation
            atr_points = 0
            
            # ATR contraction (recent vs older period)
            best_contraction = min(
                consolidation_data.get('atr_contraction_2w', 1),
                consolidation_data.get('atr_contraction_4w', 1),
                consolidation_data.get('atr_contraction_6w', 1)
            )
            
            if best_contraction <= 0.6:  # ATR contracted to 60% or less
                atr_points += 20
            elif best_contraction <= 0.8:  # ATR contracted to 80% or less
                atr_points += 15
            elif best_contraction <= 1.0:  # ATR staying same or lower
                atr_points += 10
            elif best_contraction <= 1.2:  # ATR only slightly higher
                atr_points += 5
            
            # Absolute ATR level (should be reasonable, not too high)
            recent_atr_pct = consolidation_data.get('recent_atr_pct_4w', 10)
            if recent_atr_pct <= 2.0:  # Very low volatility
                atr_points += 10
            elif recent_atr_pct <= 3.5:  # Low-moderate volatility
                atr_points += 8
            elif recent_atr_pct <= 5.0:  # Moderate volatility
                atr_points += 5
            elif recent_atr_pct <= 7.0:  # Higher volatility but acceptable
                atr_points += 2
            
            # Recent range analysis
            recent_range = consolidation_data.get('recent_range_pct', 20)
            if recent_range <= 10:  # Tight range
                atr_points += 5
            elif recent_range <= 15:  # Reasonable range
                atr_points += 3
            elif recent_range <= 25:  # Moderate range
                atr_points += 1
            
            conviction += atr_points
            details['atr_points'] = atr_points
            details['best_atr_contraction'] = best_contraction
            
            # Factor 3: Recent Momentum Dampening (0-20 points)
            # REWARD LOW recent momentum (indicating consolidation, not continuation)
            momentum_points = 0
            recent_gain_2w = consolidation_data.get('gain_2w', 0)
            recent_gain_4w = consolidation_data.get('gain_4w', 0)
            
            # Reward LOW recent momentum
            avg_recent_gain = (abs(recent_gain_2w) + abs(recent_gain_4w)) / 2
            
            if avg_recent_gain <= 2:  # Very low recent movement
                momentum_points = 20
            elif avg_recent_gain <= 5:  # Low recent movement
                momentum_points = 15
            elif avg_recent_gain <= 8:  # Moderate recent movement
                momentum_points = 10
            elif avg_recent_gain <= 12:  # Some recent movement
                momentum_points = 5
            # No points for high recent momentum - that's not consolidation
            
            conviction += momentum_points
            details['momentum_points'] = momentum_points
            details['avg_recent_gain'] = avg_recent_gain
            
            # Factor 4: Volume Pattern Analysis (0-15 points)
            # Look for normal or decreasing volume during consolidation
            volume_points = 0
            volume_ratio = consolidation_data.get('volume_ratio', 1)
            
            if 0.7 <= volume_ratio <= 1.3:  # Normal volume
                volume_points = 15
            elif 0.5 <= volume_ratio <= 1.5:  # Reasonable volume
                volume_points = 10
            elif 0.3 <= volume_ratio <= 1.8:  # Acceptable volume
                volume_points = 5
            # Extreme volume changes get no points
            
            conviction += volume_points
            details['volume_points'] = volume_points
            details['volume_ratio'] = volume_ratio
            
            details['total_conviction'] = conviction
            
            # Convert to conviction level (0-100 -> 0-5)
            if conviction >= 80:
                level = 5
                reason = f"CONSOLIDATION MAX: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR contraction: {best_contraction:.2f}, recent: {avg_recent_gain:.1f}%"
            elif conviction >= 65:
                level = 4
                reason = f"CONSOLIDATION HIGH: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR contraction: {best_contraction:.2f}, recent: {avg_recent_gain:.1f}%"
            elif conviction >= 50:
                level = 3
                reason = f"CONSOLIDATION GOOD: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR contraction: {best_contraction:.2f}, recent: {avg_recent_gain:.1f}%"
            elif conviction >= 35:
                level = 2
                reason = f"CONSOLIDATION FAIR: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR contraction: {best_contraction:.2f}"
            elif conviction >= 20:
                level = 1
                reason = f"CONSOLIDATION WEAK: {conviction}, 3-6M: {medium_term_gain:.1f}%"
            else:
                level = 0
                reason = f"No consolidation: {conviction}"
            
            return level, reason, details
            
        except Exception as e:
            self.logger.error(f"Error generating consolidation signal for {symbol}: {e}")
            return 0, f"Error: {e}", {}
    
    def get_fundamental_data(self, symbol: str) -> Dict:
        """Get fundamental data using Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            fundamentals = {
                'symbol': symbol,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'current_ratio': info.get('currentRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                'free_cashflow': info.get('freeCashflow', 0),
                'target_mean_price': info.get('targetMeanPrice', 0)
            }
            
            return fundamentals
            
        except Exception as e:
            self.logger.debug(f"Error getting fundamental data for {symbol}: {e}")
            return {}
    
    def calculate_fundamental_score(self, fundamentals: Dict) -> Tuple[float, Dict]:
        """Calculate basic fundamental score for post-move consolidation stocks"""
        score = 0
        breakdown = {}
        
        try:
            # Simplified scoring for post-move stocks (may have stretched valuations)
            
            # Growth metrics (40 points)
            revenue_growth = fundamentals.get('revenue_growth', 0)
            earnings_growth = fundamentals.get('earnings_growth', 0)
            
            if revenue_growth >= 10:
                score += 20
                breakdown['revenue_growth'] = f"PASS {revenue_growth:.1f}%"
            elif revenue_growth >= 5:
                score += 10
                breakdown['revenue_growth'] = f"PARTIAL {revenue_growth:.1f}%"
            else:
                breakdown['revenue_growth'] = f"WEAK {revenue_growth:.1f}%"
            
            if earnings_growth >= 10:
                score += 20
                breakdown['earnings_growth'] = f"PASS {earnings_growth:.1f}%"
            elif earnings_growth >= 5:
                score += 10
                breakdown['earnings_growth'] = f"PARTIAL {earnings_growth:.1f}%"
            else:
                breakdown['earnings_growth'] = f"WEAK {earnings_growth:.1f}%"
            
            # Profitability (30 points)
            roe = fundamentals.get('roe', 0)
            profit_margin = fundamentals.get('profit_margin', 0)
            
            if roe >= 15:
                score += 15
            elif roe >= 10:
                score += 10
            elif roe >= 5:
                score += 5
            
            if profit_margin >= 10:
                score += 15
            elif profit_margin >= 5:
                score += 10
            elif profit_margin >= 2:
                score += 5
            
            # Financial strength (30 points)
            current_ratio = fundamentals.get('current_ratio', 0)
            debt_to_equity = fundamentals.get('debt_to_equity', 0)
            
            if current_ratio >= 1.5:
                score += 15
            elif current_ratio >= 1.0:
                score += 10
            elif current_ratio >= 0.8:
                score += 5
            
            if debt_to_equity <= 0.3:
                score += 15
            elif debt_to_equity <= 0.5:
                score += 10
            elif debt_to_equity <= 1.0:
                score += 5
            
            breakdown['total_score'] = score
            breakdown['grade'] = (
                'A' if score >= 70 else
                'B' if score >= 50 else  
                'C' if score >= 30 else
                'D' if score >= 15 else 'F'
            )
            
            return score, breakdown
            
        except Exception as e:
            self.logger.error(f"Error calculating fundamental score: {e}")
            return 0, {'error': str(e)}
    
    def scan_symbol(self, symbol: str) -> Optional[Dict]:
        """Scan a single symbol for consolidation patterns"""
        try:
            self.logger.debug(f"Scanning {symbol} for consolidation...")
            
            # Get data
            df = self.get_symbol_data(symbol)
            if df is None:
                return None
            
            current = df.iloc[-1]
            price = current['close']
            volume = current['volume']
            
            # Basic filters
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
                self.logger.debug(f"{symbol}: Market cap too low (${market_cap/1e6:.0f}M)")
                return None
            
            # Generate consolidation conviction signal
            conviction_level, reason, details = self.generate_consolidation_signal(symbol, df)
            
            # Calculate current ATR for reference
            atr_current = details.get('current_atr_14', 0)
            atr_percentage = (atr_current / price * 100) if price > 0 else 0
            
            # Create result
            result = {
                'symbol': symbol,
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'data_date': str(current['date']) if 'date' in current else str(df.index[-1]),
                'price': price,
                'volume': volume,
                'avg_volume_20d': df['volume'].rolling(20).mean().iloc[-1],
                
                # Consolidation-specific metrics
                'conviction_level': conviction_level,
                'conviction_reason': reason,
                'conviction_details': details,
                
                # Performance metrics
                'gain_3m_pct': details.get('gain_3m', 0),
                'gain_6m_pct': details.get('gain_6m', 0),
                'gain_2w_pct': details.get('gain_2w', 0),
                'gain_4w_pct': details.get('gain_4w', 0),
                'medium_term_gain': details.get('medium_term_gain', 0),
                
                # ATR and consolidation analysis
                'current_atr_14': atr_current,
                'atr_percentage': atr_percentage,
                'recent_atr_pct_2w': details.get('recent_atr_pct_2w', 0),
                'recent_atr_pct_4w': details.get('recent_atr_pct_4w', 0),
                'atr_contraction_2w': details.get('atr_contraction_2w', 1),
                'atr_contraction_4w': details.get('atr_contraction_4w', 1),
                'best_atr_contraction': details.get('best_atr_contraction', 1),
                'recent_range_pct': details.get('recent_range_pct', 0),
                
                # Trading parameters
                'position_size_pct': {
                    1: 15, 2: 20, 3: 25, 4: 30, 5: 35
                }.get(conviction_level, 0),
                'ib_action': 'BUY' if conviction_level >= 2 else 'WATCH',
                'stop_loss_price': price * 0.92,  # 8% stop (tighter for consolidation)
                'profit_target_price': price * 1.40,  # 40% target
                
                # Fundamental data
                'fundamental_score': fundamental_score,
                'fundamental_grade': fundamental_breakdown.get('grade', 'N/A'),
                'market_cap': fundamentals.get('market_cap', 0),
                'pe_ratio': fundamentals.get('pe_ratio', 0),
                'roe': fundamentals.get('roe', 0),
                'revenue_growth': fundamentals.get('revenue_growth', 0),
                'earnings_growth': fundamentals.get('earnings_growth', 0),
                
                # Detailed scoring
                'performance_points': details.get('performance_points', 0),
                'atr_points': details.get('atr_points', 0),
                'momentum_points': details.get('momentum_points', 0),
                'volume_points': details.get('volume_points', 0),
                'total_conviction_score': details.get('total_conviction', 0)
            }
            
            # Log significant findings
            if conviction_level >= 3:
                self.logger.info(f"HIGH CONSOLIDATION: {symbol} - Level {conviction_level} - ${price:.2f} - 3-6M: {details.get('medium_term_gain', 0):.1f}% - ATR: {details.get('best_atr_contraction', 1):.2f}")
                self.consolidation_alerts.append(result)
            elif conviction_level >= 2:
                self.logger.info(f"CONSOLIDATION CANDIDATE: {symbol} - Level {conviction_level} - ${price:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            return None
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbol list (sample for testing)"""
        # Start with major liquid names for testing
        return [
            # Technology leaders
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'ADBE',
            'CRM', 'ORCL', 'AVGO', 'AMD', 'QCOM', 'TXN', 'INTC', 'IBM', 'AMAT', 'ADI',
            'CSCO', 'ACN', 'INTU', 'NOW', 'PANW', 'ANET', 'MU', 'LRCX', 'KLAC', 'CDNS',
            
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'LLY', 'MDT', 'BMY', 'AMGN',
            'GILD', 'CVS', 'CI', 'HUM', 'BDX', 'SYK', 'BSX', 'EW', 'DHR', 'ISRG',
            'REGN', 'VRTX', 'ZTS', 'DXCM', 'BIIB', 'ILMN', 'IQV', 'A', 'RMD', 'ALGN',
            
            # Financials
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'SPGI',
            'CME', 'ICE', 'MCO', 'COF', 'TRV', 'PGR', 'AFL', 'ALL', 'MET', 'PRU',
            'USB', 'PNC', 'FIS', 'AIG', 'TFC', 'BK', 'STT', 'FITB', 'AMP', 'TROW',
            
            # Consumer Discretionary
            'HD', 'MCD', 'NKE', 'SBUX', 'TJX', 'LOW', 'TGT', 'DIS', 'BKNG', 'MAR',
            'GM', 'F', 'ABNB', 'EBAY', 'ETSY', 'EXPE', 'HLT', 'LVS', 'MGM', 'NCLH',
            'RCL', 'CCL', 'WYNN', 'YUM', 'CMG', 'POOL', 'GPC', 'ORLY', 'AAP', 'AZO',
            
            # Consumer Staples  
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'EL', 'CL', 'KMB', 'GIS',
            'MDLZ', 'KHC', 'KR', 'SYY', 'ADM', 'TSN', 'K', 'CAG', 'CPB', 'HRL',
            
            # Industrials
            'UPS', 'HON', 'BA', 'UNP', 'RTX', 'LMT', 'CAT', 'DE', 'MMM', 'GE',
            'FDX', 'LUV', 'AAL', 'DAL', 'UAL', 'JBHT', 'CSX', 'NSC', 'EMR', 'ETN',
            
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY', 'HAL',
            
            # Utilities
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'XEL', 'SRE', 'PEG', 'ED', 'FE',
            
            # Communication Services
            'VZ', 'T', 'CMCSA', 'CHTR', 'TMUS', 'PARA', 'WBD', 'FOXA', 'FOX', 'OMC',
            
            # Materials
            'LIN', 'APD', 'ECL', 'DD', 'DOW', 'SHW', 'FCX', 'NEM', 'PPG', 'IFF',
            
            # Real Estate
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'DLR', 'O', 'SBAC', 'EXR'
        ]
    
    def get_asx300_symbols(self) -> List[str]:
        """Get ASX300 symbol list (sample for testing)"""
        return [
            # Major banks and financials
            'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'ASX.AX', 'AMP.AX',
            'QBE.AX', 'IAG.AX', 'SUN.AX', 'BOQ.AX', 'BEN.AX',
            
            # Major miners
            'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'S32.AX', 'WSA.AX', 'IGO.AX',
            'MIN.AX', 'NST.AX', 'EVN.AX', 'RRL.AX', 'OZL.AX', 'LYC.AX', 'PLS.AX',
            
            # Healthcare leaders
            'CSL.AX', 'COH.AX', 'RMD.AX', 'SHL.AX', 'NAN.AX', 'PME.AX', 'FPH.AX',
            'RHC.AX', 'IMP.AX', 'NEU.AX', 'SIP.AX',
            
            # Technology and growth
            'XRO.AX', 'WTC.AX', 'TNE.AX', 'CPU.AX', 'KGN.AX', 'NXT.AX', 'APX.AX',
            'REA.AX', 'CAR.AX', 'SEK.AX', 'NEA.AX',
            
            # Retail and consumer
            'WOW.AX', 'COL.AX', 'WES.AX', 'JBH.AX', 'HVN.AX', 'SUL.AX', 'KMD.AX',
            'A2M.AX', 'BAP.AX', 'SHV.AX', 'CCL.AX',
            
            # Industrials and infrastructure
            'QAN.AX', 'ALL.AX', 'APA.AX', 'AGL.AX', 'ORE.AX', 'AST.AX', 'SYD.AX',
            'TLS.AX', 'TCL.AX', 'AZJ.AX',
            
            # REITs and property
            'SCG.AX', 'GMG.AX', 'VCX.AX', 'DXS.AX', 'CHC.AX', 'MGR.AX', 'GPT.AX',
            'BWP.AX', 'SCP.AX', 'CMW.AX',
            
            # Oil and gas
            'STO.AX', 'WDS.AX', 'ORG.AX', 'BPT.AX', 'SXY.AX', 'COE.AX'
        ]
    
    def scan_market(self, symbols: List[str], market_name: str) -> List[Dict]:
        """Scan multiple symbols for consolidation patterns"""
        results = []
        total_symbols = len(symbols)
        
        self.logger.info(f"Starting {market_name} consolidation scan of {total_symbols} symbols...")
        start_time = time.time()
        
        for i, symbol in enumerate(symbols, 1):
            try:
                if i % 10 == 0:  # Progress update
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total_symbols - i) / rate if rate > 0 else 0
                    self.logger.info(f"Progress: {i}/{total_symbols} ({i/total_symbols*100:.1f}%) - {rate:.1f} symbols/sec - ETA: {eta:.0f}s")
                
                result = self.scan_symbol(symbol)
                if result:
                    results.append(result)
                    self.scan_results.append(result)
                
                # Rate limiting
                time.sleep(0.15)  # Slightly slower for more thorough analysis
                
            except KeyboardInterrupt:
                self.logger.info("Scan interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in market scan for {symbol}: {e}")
                continue
        
        scan_time = time.time() - start_time
        self.logger.info(f"{market_name} consolidation scan complete - {len(results)} symbols processed in {scan_time:.1f}s")
        return results
    
    def export_results(self, filename: str = None) -> str:
        """Export consolidation scan results to CSV"""
        try:
            if not self.scan_results:
                self.logger.warning("No scan results to export")
                return ""
            
            # Create DataFrame
            export_data = []
            for result in self.scan_results:
                row = {
                    # Basic info
                    'scan_date': result['scan_date'],
                    'symbol': result['symbol'],
                    'conviction_level': result['conviction_level'],
                    'ib_action': result['ib_action'],
                    'position_size_pct': result['position_size_pct'],
                    'current_price': result['price'],
                    'stop_loss_price': result['stop_loss_price'],
                    'profit_target_price': result['profit_target_price'],
                    
                    # Consolidation metrics
                    'medium_term_gain_pct': result['medium_term_gain'],
                    'gain_3m_pct': result['gain_3m_pct'],
                    'gain_6m_pct': result['gain_6m_pct'],
                    'gain_2w_pct': result['gain_2w_pct'],
                    'gain_4w_pct': result['gain_4w_pct'],
                    
                    # ATR analysis
                    'current_atr_pct': result['atr_percentage'],
                    'recent_atr_2w_pct': result['recent_atr_pct_2w'],
                    'recent_atr_4w_pct': result['recent_atr_pct_4w'],
                    'atr_contraction_2w': result['atr_contraction_2w'],
                    'atr_contraction_4w': result['atr_contraction_4w'],
                    'best_atr_contraction': result['best_atr_contraction'],
                    'recent_range_pct': result['recent_range_pct'],
                    
                    # Scoring breakdown
                    'total_conviction_score': result['total_conviction_score'],
                    'performance_points': result['performance_points'],
                    'atr_points': result['atr_points'],
                    'momentum_points': result['momentum_points'],
                    'volume_points': result['volume_points'],
                    
                    # Volume and fundamentals
                    'volume': result['volume'],
                    'avg_volume_20d': result['avg_volume_20d'],
                    'fundamental_score': result['fundamental_score'],
                    'fundamental_grade': result['fundamental_grade'],
                    'market_cap': result['market_cap'],
                    'pe_ratio': result['pe_ratio'],
                    'roe': result['roe'],
                    
                    'conviction_reason': result['conviction_reason']
                }
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            
            # Sort by conviction level and total score
            df = df.sort_values(['conviction_level', 'total_conviction_score'], ascending=[False, False])
            
            # Generate filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"consolidation_conviction_scan_{timestamp}.csv"
            
            # Export
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported {len(df)} results to {filename}")
            
            # Create trade-ready summary
            trade_candidates = df[df['ib_action'] == 'BUY']
            if len(trade_candidates) > 0:
                trade_filename = filename.replace('.csv', '_TRADE_READY.csv')
                trade_candidates.to_csv(trade_filename, index=False)
                self.logger.info(f"Exported {len(trade_candidates)} consolidation trade candidates to {trade_filename}")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            return ""
    
    def print_summary(self):
        """Print consolidation scan summary"""
        if not self.scan_results:
            print("No scan results available")
            return
        
        total_scanned = len(self.scan_results)
        conviction_counts = {}
        for result in self.scan_results:
            level = result['conviction_level']
            conviction_counts[level] = conviction_counts.get(level, 0) + 1
        
        print("\n" + "=" * 80)
        print("CONSOLIDATION CONVICTION SCAN SUMMARY")
        print("=" * 80)
        print(f"Total symbols scanned: {total_scanned}")
        print(f"Focus: Post-move consolidation patterns with 30%+ 3-6M gains")
        print(f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("CONSOLIDATION CONVICTION LEVELS:")
        for level in range(6):
            count = conviction_counts.get(level, 0)
            pct = count / total_scanned * 100 if total_scanned > 0 else 0
            position_pct = {0: 0, 1: 15, 2: 20, 3: 25, 4: 30, 5: 35}.get(level, 0)
            action = "BUY" if level >= 2 else "WATCH"
            print(f"  Level {level} ({position_pct:2d}% position): {count:3d} stocks ({pct:5.1f}%) - {action}")
        
        # Consolidation candidates
        consolidation_candidates = [r for r in self.scan_results if r['conviction_level'] >= 2]
        if consolidation_candidates:
            print(f"\nCONSOLIDATION TRADE CANDIDATES ({len(consolidation_candidates)} stocks):")
            print("-" * 140)
            print(f"{'Symbol':<8} {'Level':<6} {'Price':<10} {'3-6M%':<8} {'2W%':<7} {'ATR Cont':<9} {'ATR%':<7} {'Stop':<10} {'Target':<10}")
            print("-" * 140)
            
            for candidate in sorted(consolidation_candidates, key=lambda x: x['conviction_level'], reverse=True)[:15]:
                print(f"{candidate['symbol']:<8} {candidate['conviction_level']:<6} "
                      f"${candidate['price']:<9.2f} {candidate['medium_term_gain']:>6.1f}% "
                      f"{candidate['gain_2w_pct']:>5.1f}% {candidate['best_atr_contraction']:>7.2f} "
                      f"{candidate['atr_percentage']:>5.1f}% ${candidate['stop_loss_price']:<9.2f} "
                      f"${candidate['profit_target_price']:<9.2f}")
        
        # High conviction alerts
        high_conviction = [r for r in self.scan_results if r['conviction_level'] >= 3]
        if high_conviction:
            print(f"\nHIGH CONSOLIDATION CONVICTION ({len(high_conviction)} stocks):")
            print("-" * 120)
            for result in sorted(high_conviction, key=lambda x: x['conviction_level'], reverse=True):
                print(f"  {result['symbol']:<8} Level {result['conviction_level']} - "
                      f"${result['price']:>8.2f} - 3-6M: {result['medium_term_gain']:>6.1f}% - "
                      f"ATR Contraction: {result['best_atr_contraction']:.2f} - "
                      f"Recent 2W: {result['gain_2w_pct']:>5.1f}%")
        
        print("=" * 80)
        print("CONSOLIDATION STRATEGY NOTES:")
        print("• Targeting stocks AFTER big moves during consolidation")
        print("• 30%+ gains in 3-6 months required")
        print("• Low/contracting ATR indicates consolidation, not breakout")
        print("• Reduced recent momentum weight (we want low recent movement)")
        print("• Tighter stops (8%) due to consolidation nature")
        print("=" * 80)


def main():
    """Main consolidation scanning function"""
    scanner = ConsolidationConvictionScanner()
    
    try:
        print("\nSelect market to scan for consolidation patterns:")
        print("1. US Market (S&P 500 sample)")
        print("2. ASX Market (ASX300 sample)")  
        print("3. Both markets")
        
        choice = input("Enter choice (1-3): ").strip()
        
        all_results = []
        
        if choice in ['1', '3']:
            # Scan US market
            us_symbols = scanner.get_sp500_symbols()
            print(f"\nScanning {len(us_symbols)} US stocks for consolidation...")
            us_results = scanner.scan_market(us_symbols, "US Market")
            all_results.extend(us_results)
        
        if choice in ['2', '3']:
            # Scan ASX market
            asx_symbols = scanner.get_asx300_symbols()
            print(f"\nScanning {len(asx_symbols)} ASX stocks for consolidation...")
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
        
        # Show summary
        consolidation_picks = [r for r in all_results if r['conviction_level'] >= 2]
        if consolidation_picks:
            print(f"\nSUMMARY: {len(consolidation_picks)} consolidation candidates identified")
            print("Stocks with strong 3-6M performance now in consolidation phase")
        else:
            print("\nNo high-conviction consolidation patterns found")
    
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error in main scan: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nConsolidation scan complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    print("CONSOLIDATION CONVICTION SCANNER")
    print("Post-Move Consolidation Pattern Detection")
    print("Targets stocks with strong 3-6 month gains now consolidating")
    print()
    
    main()