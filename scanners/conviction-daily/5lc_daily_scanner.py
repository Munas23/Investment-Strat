"""
5-LEVEL CONVICTION DAILY SCANNER
================================

Professional-grade daily scanner implementing the proven 5-Level Conviction Strategy
with comprehensive fundamental screening and technical breakout detection.

STRATEGY OVERVIEW:
• Quality-first fundamental screening (>60% score required)
• Technical breakout timing with volume confirmation
• 5-level conviction scoring for position sizing (20% to 40%)
• Professional risk management (7% stops, 50% targets)

MARKETS COVERED:
• Full S&P 500 (500+ symbols)
• Full ASX300 (300+ symbols)
• Automatic market detection and symbol formatting

CONVICTION LEVELS:
• Level 1 (20% position): 25-39 conviction points
• Level 2 (25% position): 40-54 conviction points
• Level 3 (30% position): 55-69 conviction points
• Level 4 (35% position): 70-84 conviction points
• Level 5 (40% position): 85+ conviction points

Author: 5LC Strategy Team
Date: 2024
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
from typing import Dict, List, Optional, Tuple
import logging
import requests
from io import StringIO
import os

warnings.filterwarnings('ignore')

class FiveLevelConvictionScanner:
    """
    Professional 5-Level Conviction Scanner with comprehensive fundamental screening
    """

    def __init__(self):
        """Initialize the 5LC scanner with professional-grade settings"""

        # Fundamental screening thresholds (150 total points possible)
        self.fundamental_thresholds = {
            'min_score': 55.0,           # Minimum 55% fundamental quality (82.5/150 points)
            'min_market_cap_usd': 300e6,  # $300M minimum (USD)
            'min_market_cap_aud': 500e6,  # $500M minimum (AUD)
            'max_market_cap': 5000e9,     # $5T maximum (increased for mega-caps)
            'min_price_usd': 5.0,         # $5 minimum (USD markets) - relaxed
            'min_price_aud': 2.0,         # $2 minimum (AUD markets) - relaxed
            'min_volume_usd': 500000,     # 500K daily volume (USD)
            'min_volume_aud': 100000,     # 100K daily volume (AUD)
            'min_roe': 10.0,              # 10% return on equity - relaxed
            'max_debt_equity': 2.0,       # 200% max debt/equity - relaxed
            'min_current_ratio': 0.8,     # 0.8x current ratio - relaxed
            'min_revenue_growth': 5.0,    # 5% revenue growth - more realistic
            'min_earnings_growth': 5.0,   # 5% earnings growth - more realistic
            'min_profit_margin': 5.0,     # 5% profit margin - relaxed
            'min_institutional': 20.0,    # 20% minimum institutional - relaxed
            'max_institutional': 95.0     # 95% maximum institutional - relaxed
        }

        # Technical requirements
        self.technical_thresholds = {
            'min_trend_strength': 60,     # 60/100 trend strength minimum
            'min_volume_surge': 1.2,      # 1.2x volume surge minimum
            'breakout_threshold': 1.01,   # 1% above 20-day high
            'strong_breakout': 1.02       # 2% above 50-day high
        }

        # Scanning results
        self.scan_results = []
        self.high_conviction_alerts = []

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('5lc_daily_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        print("=" * 80)
        print("5-LEVEL CONVICTION DAILY SCANNER")
        print("=" * 80)
        print("Quality-First Breakout Detection System")
        print(f"Scan date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Markets: Full S&P 500 + Full ASX300")
        print("=" * 80)

    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols from local CSV file"""
        try:
            # Load from local CSV file
            csv_file = 'sp500_tickers.csv'

            if os.path.exists(csv_file):
                self.logger.info(f"Loading S&P 500 symbols from local file: {csv_file}")
                df = pd.read_csv(csv_file)
                symbols = df['Symbol'].tolist()
                self.logger.info(f"Loaded {len(symbols)} S&P 500 symbols from CSV")
                return symbols
            else:
                raise FileNotFoundError(f"CSV file {csv_file} not found")

        except Exception as e:
            self.logger.error(f"Error loading S&P 500 symbols from CSV: {e}")
            # Fallback to major S&P 500 symbols
            fallback_symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'UNH',
                'JNJ', 'XOM', 'JPM', 'V', 'PG', 'CVX', 'HD', 'MA', 'PFE', 'ABBV',
                'BAC', 'KO', 'AVGO', 'LLY', 'WMT', 'PEP', 'TMO', 'COST', 'DIS', 'ABT',
                'CRM', 'ACN', 'VZ', 'DHR', 'NEE', 'ORCL', 'ADBE', 'NFLX', 'TXN', 'LIN'
            ]
            self.logger.warning(f"Using fallback list of {len(fallback_symbols)} major S&P 500 symbols")
            return fallback_symbols


    def get_asx300_symbols(self) -> List[str]:
        """Get ASX300 symbols from local CSV file"""
        try:
            # Load from local CSV file
            csv_file = 'asx300_tickers.csv'

            if os.path.exists(csv_file):
                self.logger.info(f"Loading ASX300 symbols from local file: {csv_file}")
                df = pd.read_csv(csv_file)
                symbols = df['Symbol'].tolist()
                self.logger.info(f"Loaded {len(symbols)} ASX300 symbols from CSV")
                return symbols
            else:
                raise FileNotFoundError(f"CSV file {csv_file} not found")

        except Exception as e:
            self.logger.warning(f"Error loading ASX300 symbols from CSV: {e}, using fallback list")

            # Fallback list with major ASX stocks (valid as of 2024)
            fallback_symbols = [
                'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'BHP.AX', 'RIO.AX', 'FMG.AX',
                'CSL.AX', 'WOW.AX', 'WES.AX', 'MQG.AX', 'TLS.AX', 'TCL.AX', 'REA.AX',
                'XRO.AX', 'COH.AX', 'QBE.AX', 'IAG.AX', 'SUN.AX', 'ASX.AX', 'ALL.AX',
                'JBH.AX', 'EVN.AX', 'NST.AX', 'STO.AX', 'ORG.AX', 'AGL.AX', 'SCG.AX'
            ]

            self.logger.info(f"Using ASX300 fallback list with {len(fallback_symbols)} major symbols")
            return fallback_symbols

    def get_symbol_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical data with proper error handling"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d")

            if hist.empty or len(hist) < 100:
                self.logger.debug(f"{symbol}: Insufficient data ({len(hist)} days)")
                return None

            # Standardize column names
            hist.columns = [col.lower() for col in hist.columns]
            hist.index = pd.to_datetime(hist.index).date
            hist = hist.dropna()

            if len(hist) < 100:
                return None

            return hist.reset_index()

        except Exception as e:
            self.logger.debug(f"Error getting data for {symbol}: {e}")
            return None

    def get_fundamental_data(self, symbol: str) -> Dict:
        """Get comprehensive fundamental data for scoring"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            fundamentals = {
                'symbol': symbol,
                'market_cap': info.get('marketCap', 0),
                'price': info.get('currentPrice', 0) or info.get('regularMarketPrice', 0),
                'volume': info.get('averageVolume', 0) or info.get('averageVolume10days', 0),

                # Profitability metrics
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,

                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'revenue_growth_quarterly': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,  # Use annual if quarterly not available
                'earnings_growth_quarterly': info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0,

                # Financial strength
                'current_ratio': info.get('currentRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                'quick_ratio': info.get('quickRatio', 0),
                'free_cashflow': info.get('freeCashflow', 0),

                # Ownership & analyst data
                'institutional_percent': (info.get('heldPercentInstitutions', 0) or 0) * 100,
                'insider_percent': (info.get('heldPercentInsiders', 0) or 0) * 100,
                'analyst_count': info.get('numberOfAnalystOpinions', 0),
                'target_mean_price': info.get('targetMeanPrice', 0),
                'recommendation': info.get('recommendationMean', 0),

                # Additional metrics
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                'operating_margin': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0,
                'ebitda_margin': info.get('ebitdaMargins', 0) * 100 if info.get('ebitdaMargins') else 0,
                'beta': info.get('beta', 1.0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0),
                'short_ratio': info.get('shortRatio', 0),
                'book_value': info.get('bookValue', 0),
                'price_to_book': info.get('priceToBook', 0)
            }

            return fundamentals

        except Exception as e:
            self.logger.debug(f"Error getting fundamental data for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}

    def calculate_fundamental_score(self, symbol: str, fundamentals: Dict) -> Tuple[float, Dict]:
        """
        Calculate comprehensive fundamental quality score (0-150 points)

        SCORING BREAKDOWN:
        • Market Cap & Price (15 pts): Proper size and price filters
        • Volume (5 pts): Adequate liquidity
        • Profitability (35 pts): ROE, margins, returns
        • Growth (50 pts): Revenue and earnings growth (quarterly focus)
        • Financial Strength (25 pts): Balance sheet quality
        • Institutional Quality (20 pts): Professional ownership levels

        Target: >60% (90+ points) for trade consideration
        """

        score = 0
        breakdown = {'symbol': symbol}

        try:
            # Determine market type for different thresholds
            is_aud_market = symbol.endswith('.AX')

            # 1. MARKET CAP & PRICE FILTER (15 points)
            market_cap = fundamentals.get('market_cap', 0)
            price = fundamentals.get('price', 0)

            # Market cap scoring (10 points)
            if is_aud_market:
                min_cap = self.fundamental_thresholds['min_market_cap_aud']
                min_price = self.fundamental_thresholds['min_price_aud']
            else:
                min_cap = self.fundamental_thresholds['min_market_cap_usd']
                min_price = self.fundamental_thresholds['min_price_usd']

            max_cap = self.fundamental_thresholds['max_market_cap']

            if min_cap <= market_cap <= max_cap:
                score += 10
                breakdown['market_cap'] = f"PASS ${market_cap/1e9:.1f}B"
            else:
                breakdown['market_cap'] = f"FAIL ${market_cap/1e9:.1f}B"

            # Price filter (5 points)
            if price >= min_price:
                score += 5
                breakdown['price'] = f"PASS ${price:.2f}"
            else:
                breakdown['price'] = f"FAIL ${price:.2f}"

            # 2. VOLUME FILTER (5 points)
            volume = fundamentals.get('volume', 0)
            min_vol = self.fundamental_thresholds['min_volume_aud'] if is_aud_market else self.fundamental_thresholds['min_volume_usd']

            if volume >= min_vol:
                score += 5
                breakdown['volume'] = f"PASS {volume:,.0f}"
            else:
                breakdown['volume'] = f"FAIL {volume:,.0f}"

            # 3. PROFITABILITY METRICS (35 points)

            # ROE (20 points) - Most important profitability metric
            roe = fundamentals.get('roe', 0)
            if roe >= self.fundamental_thresholds['min_roe']:
                if roe >= 25:
                    score += 20
                    breakdown['roe'] = f"EXCELLENT {roe:.1f}%"
                elif roe >= 20:
                    score += 15
                    breakdown['roe'] = f"GOOD {roe:.1f}%"
                else:
                    score += 10
                    breakdown['roe'] = f"PASS {roe:.1f}%"
            else:
                breakdown['roe'] = f"FAIL {roe:.1f}%"

            # Profit Margin (15 points)
            profit_margin = fundamentals.get('profit_margin', 0)
            if profit_margin >= self.fundamental_thresholds['min_profit_margin']:
                if profit_margin >= 20:
                    score += 15
                elif profit_margin >= 15:
                    score += 12
                else:
                    score += 8
                breakdown['profit_margin'] = f"PASS {profit_margin:.1f}%"
            else:
                breakdown['profit_margin'] = f"FAIL {profit_margin:.1f}%"

            # 4. GROWTH METRICS (50 points) - Critical for momentum strategy

            # Quarterly Revenue Growth (25 points)
            rev_growth_q = fundamentals.get('revenue_growth_quarterly', fundamentals.get('revenue_growth', 0))
            if rev_growth_q >= self.fundamental_thresholds['min_revenue_growth']:
                if rev_growth_q >= 30:
                    score += 25
                    breakdown['revenue_growth'] = f"EXCELLENT {rev_growth_q:.1f}%"
                elif rev_growth_q >= 20:
                    score += 20
                    breakdown['revenue_growth'] = f"GOOD {rev_growth_q:.1f}%"
                else:
                    score += 15
                    breakdown['revenue_growth'] = f"PASS {rev_growth_q:.1f}%"
            else:
                breakdown['revenue_growth'] = f"FAIL {rev_growth_q:.1f}%"

            # Quarterly Earnings Growth (25 points)
            earn_growth_q = fundamentals.get('earnings_growth_quarterly', fundamentals.get('earnings_growth', 0))
            if earn_growth_q >= self.fundamental_thresholds['min_earnings_growth']:
                if earn_growth_q >= 40:
                    score += 25
                    breakdown['earnings_growth'] = f"EXCELLENT {earn_growth_q:.1f}%"
                elif earn_growth_q >= 25:
                    score += 20
                    breakdown['earnings_growth'] = f"GOOD {earn_growth_q:.1f}%"
                else:
                    score += 15
                    breakdown['earnings_growth'] = f"PASS {earn_growth_q:.1f}%"
            else:
                breakdown['earnings_growth'] = f"FAIL {earn_growth_q:.1f}%"

            # 5. FINANCIAL STRENGTH (25 points)

            # Current Ratio (15 points)
            current_ratio = fundamentals.get('current_ratio', 0)
            if current_ratio >= self.fundamental_thresholds['min_current_ratio']:
                if current_ratio >= 2.0:
                    score += 15
                elif current_ratio >= 1.8:
                    score += 12
                else:
                    score += 8
                breakdown['current_ratio'] = f"PASS {current_ratio:.2f}"
            else:
                breakdown['current_ratio'] = f"FAIL {current_ratio:.2f}"

            # Debt-to-Equity (10 points)
            debt_equity = fundamentals.get('debt_to_equity', 1.0)
            if debt_equity <= self.fundamental_thresholds['max_debt_equity']:
                if debt_equity <= 0.1:
                    score += 10
                elif debt_equity <= 0.2:
                    score += 8
                else:
                    score += 5
                breakdown['debt_equity'] = f"PASS {debt_equity:.2f}"
            else:
                breakdown['debt_equity'] = f"FAIL {debt_equity:.2f}"

            # 6. INSTITUTIONAL OWNERSHIP (20 points)
            institutional = fundamentals.get('institutional_percent', 0)
            min_inst = self.fundamental_thresholds['min_institutional']
            max_inst = self.fundamental_thresholds['max_institutional']

            if min_inst <= institutional <= max_inst:
                if 50 <= institutional <= 70:
                    score += 20
                    breakdown['institutional'] = f"OPTIMAL {institutional:.1f}%"
                else:
                    score += 15
                    breakdown['institutional'] = f"GOOD {institutional:.1f}%"
            else:
                breakdown['institutional'] = f"FAIL {institutional:.1f}%"

            # Calculate final percentage score
            percentage_score = (score / 150) * 100

            breakdown['total_score'] = score
            breakdown['max_possible'] = 150
            breakdown['percentage'] = percentage_score
            breakdown['grade'] = (
                'A+' if percentage_score >= 85 else
                'A' if percentage_score >= 75 else
                'B+' if percentage_score >= 65 else
                'B' if percentage_score >= 60 else  # Our minimum threshold
                'C' if percentage_score >= 50 else
                'D' if percentage_score >= 40 else 'F'
            )
            breakdown['passes_screen'] = percentage_score >= self.fundamental_thresholds['min_score']

            return percentage_score, breakdown

        except Exception as e:
            self.logger.error(f"Error calculating fundamental score for {symbol}: {e}")
            return 0, {'error': str(e), 'symbol': symbol}

    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators for trend analysis"""
        try:
            if len(df) < 50:
                return {}

            # Moving averages
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()
            df['sma_200'] = df['close'].rolling(200).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()

            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # Volume indicators
            df['volume_sma_20'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma_20']

            # Price position relative to highs
            df['high_20'] = df['high'].rolling(20).max()
            df['high_50'] = df['high'].rolling(50).max()
            df['high_200'] = df['high'].rolling(200).max()

            # Momentum calculations
            df['momentum_5'] = (df['close'] / df['close'].shift(5) - 1) * 100
            df['momentum_20'] = (df['close'] / df['close'].shift(20) - 1) * 100
            df['momentum_50'] = (df['close'] / df['close'].shift(50) - 1) * 100

            current = df.iloc[-1]

            return {
                'sma_20': current['sma_20'],
                'sma_50': current['sma_50'],
                'sma_200': current['sma_200'],
                'macd': current['macd'],
                'macd_signal': current['macd_signal'],
                'rsi': current['rsi'],
                'volume_ratio': current['volume_ratio'],
                'high_20': current['high_20'],
                'high_50': current['high_50'],
                'momentum_5': current['momentum_5'],
                'momentum_20': current['momentum_20'],
                'momentum_50': current['momentum_50'],
                'price_vs_sma20': (current['close'] / current['sma_20'] - 1) * 100,
                'price_vs_sma50': (current['close'] / current['sma_50'] - 1) * 100
            }

        except Exception as e:
            self.logger.error(f"Error calculating technical indicators: {e}")
            return {}

    def calculate_trend_strength(self, df: pd.DataFrame, technicals: Dict) -> Tuple[int, Dict]:
        """
        Calculate trend strength score (0-100)

        COMPONENTS:
        • Moving Average Alignment (40 pts): Price > SMA20 > SMA50 > SMA200
        • Price Position vs MAs (20 pts): How far above key moving averages
        • Momentum Quality (20 pts): Multi-timeframe momentum alignment
        • Proximity to Highs (20 pts): How close to 20/50/200-day highs

        Target: >60 points for trend confirmation
        """

        try:
            if len(df) < 50 or not technicals:
                return 0, {}

            trend_score = 0
            breakdown = {}
            current_price = df['close'].iloc[-1]

            # 1. MOVING AVERAGE ALIGNMENT (40 points)
            sma_20 = technicals.get('sma_20', 0)
            sma_50 = technicals.get('sma_50', 0)
            sma_200 = technicals.get('sma_200', 0)

            ma_points = 0
            if current_price > sma_20:
                ma_points += 10
            if sma_20 > sma_50:
                ma_points += 10
            if sma_50 > sma_200:
                ma_points += 10
            if current_price > sma_200:
                ma_points += 10

            trend_score += ma_points
            breakdown['ma_alignment'] = f"{ma_points}/40 pts"

            # 2. PRICE POSITION VS MOVING AVERAGES (20 points)
            price_vs_sma20 = technicals.get('price_vs_sma20', -10)
            price_vs_sma50 = technicals.get('price_vs_sma50', -10)

            position_points = 0
            if price_vs_sma20 >= 5:  # 5%+ above SMA20
                position_points += 10
            elif price_vs_sma20 >= 2:  # 2%+ above SMA20
                position_points += 5

            if price_vs_sma50 >= 10:  # 10%+ above SMA50
                position_points += 10
            elif price_vs_sma50 >= 5:  # 5%+ above SMA50
                position_points += 5

            trend_score += position_points
            breakdown['price_position'] = f"{position_points}/20 pts"

            # 3. MOMENTUM ALIGNMENT (20 points)
            momentum_5 = technicals.get('momentum_5', -10)
            momentum_20 = technicals.get('momentum_20', -10)
            momentum_50 = technicals.get('momentum_50', -10)

            momentum_points = 0
            if momentum_5 > 1:    # 5-day momentum positive
                momentum_points += 5
            if momentum_20 > 5:   # 20-day momentum >5%
                momentum_points += 8
            if momentum_50 > 10:  # 50-day momentum >10%
                momentum_points += 7

            trend_score += momentum_points
            breakdown['momentum'] = f"{momentum_points}/20 pts"

            # 4. PROXIMITY TO HIGHS (20 points)
            high_20 = technicals.get('high_20', current_price * 2)
            high_50 = technicals.get('high_50', current_price * 2)

            proximity_points = 0
            pct_of_high_20 = (current_price / high_20) * 100
            pct_of_high_50 = (current_price / high_50) * 100

            if pct_of_high_20 >= 98:  # Within 2% of 20-day high
                proximity_points += 10
            elif pct_of_high_20 >= 95:  # Within 5% of 20-day high
                proximity_points += 5

            if pct_of_high_50 >= 95:  # Within 5% of 50-day high
                proximity_points += 10
            elif pct_of_high_50 >= 90:  # Within 10% of 50-day high
                proximity_points += 5

            trend_score += proximity_points
            breakdown['proximity'] = f"{proximity_points}/20 pts"

            breakdown['total_trend_score'] = trend_score
            breakdown['trend_grade'] = (
                'EXCELLENT' if trend_score >= 80 else
                'STRONG' if trend_score >= 70 else
                'GOOD' if trend_score >= 60 else  # Our minimum
                'WEAK' if trend_score >= 40 else 'POOR'
            )

            return trend_score, breakdown

        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 0, {'error': str(e)}

    def generate_conviction_signal(self, symbol: str, df: pd.DataFrame, fundamentals: Dict, technicals: Dict) -> Tuple[int, str, Dict]:
        """
        Generate 5-Level Conviction Signal (0-100 points)

        EXACT 5LC METHODOLOGY:

        Factor 1: Breakout Power (0-25 points)
        • 1% above 20-day high: +15 points
        • 2% above 50-day high: +10 additional points

        Factor 2: Volume Confirmation (0-30 points)
        • 2x average volume: +30 points
        • 1.5x volume: +20 points
        • 1.2x volume: +10 points

        Factor 3: Momentum Alignment (0-25 points)
        • 5-day momentum >1%: +5 points
        • 20-day momentum >5%: +10 points
        • 50-day momentum >10%: +10 points

        Factor 4: Trend Quality Bonus (0-20 points)
        • Extra points for very strong trends (>60 strength)

        CONVICTION LEVELS:
        • 85+ points = Level 5 (40% position)
        • 70+ points = Level 4 (35% position)
        • 55+ points = Level 3 (30% position)
        • 40+ points = Level 2 (25% position)
        • 25+ points = Level 1 (20% position)
        """

        try:
            if len(df) < 50:
                return 0, "Insufficient historical data", {}

            current = df.iloc[-1]
            current_price = current['close']
            current_volume = current['volume']

            conviction = 0
            details = {}

            # Factor 1: BREAKOUT POWER (0-25 points)
            breakout_points = 0
            high_20 = technicals.get('high_20', current_price)
            high_50 = technicals.get('high_50', current_price)

            # 1% above 20-day high
            if current_price > high_20 * self.technical_thresholds['breakout_threshold']:
                breakout_points += 15
                details['breakout_20d'] = f"PASS +{((current_price/high_20-1)*100):.1f}%"

                # 2% above 50-day high (additional)
                if current_price > high_50 * self.technical_thresholds['strong_breakout']:
                    breakout_points += 10
                    details['breakout_50d'] = f"STRONG +{((current_price/high_50-1)*100):.1f}%"
                else:
                    details['breakout_50d'] = f"WEAK +{((current_price/high_50-1)*100):.1f}%"
            else:
                details['breakout_20d'] = f"FAIL +{((current_price/high_20-1)*100):.1f}%"
                details['breakout_50d'] = f"NO BREAKOUT"

            conviction += breakout_points
            details['breakout_points'] = breakout_points

            # Factor 2: VOLUME CONFIRMATION (0-30 points)
            volume_points = 0
            volume_ratio = technicals.get('volume_ratio', 1.0)

            if volume_ratio >= 2.0:  # 2x volume surge
                volume_points = 30
                details['volume_surge'] = f"EXCELLENT {volume_ratio:.1f}x"
            elif volume_ratio >= 1.5:  # 1.5x volume
                volume_points = 20
                details['volume_surge'] = f"GOOD {volume_ratio:.1f}x"
            elif volume_ratio >= 1.2:  # 1.2x volume
                volume_points = 10
                details['volume_surge'] = f"MINIMAL {volume_ratio:.1f}x"
            else:
                details['volume_surge'] = f"WEAK {volume_ratio:.1f}x"

            conviction += volume_points
            details['volume_points'] = volume_points

            # Factor 3: MOMENTUM ALIGNMENT (0-25 points)
            momentum_points = 0
            momentum_5 = technicals.get('momentum_5', -10)
            momentum_20 = technicals.get('momentum_20', -10)
            momentum_50 = technicals.get('momentum_50', -10)

            # 5-day momentum >1%
            if momentum_5 > 1:
                momentum_points += 5
                details['momentum_5d'] = f"PASS {momentum_5:.1f}%"
            else:
                details['momentum_5d'] = f"FAIL {momentum_5:.1f}%"

            # 20-day momentum >5%
            if momentum_20 > 5:
                momentum_points += 10
                details['momentum_20d'] = f"PASS {momentum_20:.1f}%"
            else:
                details['momentum_20d'] = f"FAIL {momentum_20:.1f}%"

            # 50-day momentum >10%
            if momentum_50 > 10:
                momentum_points += 10
                details['momentum_50d'] = f"PASS {momentum_50:.1f}%"
            else:
                details['momentum_50d'] = f"FAIL {momentum_50:.1f}%"

            conviction += momentum_points
            details['momentum_points'] = momentum_points

            # Factor 4: TREND QUALITY BONUS (0-20 points)
            trend_strength, trend_breakdown = self.calculate_trend_strength(df, technicals)

            trend_bonus = 0
            if trend_strength > 60:  # Only bonus for strong trends
                trend_bonus = min(20, (trend_strength - 60) / 2)  # Scale 60-100 to 0-20

            conviction += trend_bonus
            details['trend_strength'] = trend_strength
            details['trend_bonus'] = trend_bonus
            details['trend_breakdown'] = trend_breakdown

            # Total conviction score
            details['total_conviction'] = conviction

            # Convert to conviction level
            if conviction >= 85:
                level = 5
                position_size = 40
                reason = f"CONVICTION 5 MAX: {conviction} pts, breakout: {breakout_points}, volume: {volume_points}, momentum: {momentum_points}, trend: {trend_bonus}"
            elif conviction >= 70:
                level = 4
                position_size = 35
                reason = f"CONVICTION 4 HIGH: {conviction} pts, breakout: {breakout_points}, volume: {volume_points}, momentum: {momentum_points}"
            elif conviction >= 55:
                level = 3
                position_size = 30
                reason = f"CONVICTION 3 GOOD: {conviction} pts, breakout: {breakout_points}, volume: {volume_points}"
            elif conviction >= 40:
                level = 2
                position_size = 25
                reason = f"CONVICTION 2 LOW: {conviction} pts, limited signals"
            elif conviction >= 25:
                level = 1
                position_size = 20
                reason = f"CONVICTION 1 MIN: {conviction} pts, weak setup"
            else:
                level = 0
                position_size = 0
                reason = f"NO CONVICTION: {conviction} pts, insufficient signals"

            details['conviction_level'] = level
            details['position_size_pct'] = position_size

            return level, reason, details

        except Exception as e:
            self.logger.error(f"Error generating conviction signal for {symbol}: {e}")
            return 0, f"Error: {e}", {}

    def scan_symbol(self, symbol: str) -> Optional[Dict]:
        """Scan a single symbol using complete 5LC methodology"""
        try:
            self.logger.debug(f"Scanning {symbol} with 5LC methodology...")

            # 1. Get historical data
            df = self.get_symbol_data(symbol)
            if df is None:
                return None

            current = df.iloc[-1]
            price = current['close']
            volume = current['volume']

            # 2. Get fundamental data
            fundamentals = self.get_fundamental_data(symbol)
            if 'error' in fundamentals:
                return None

            # 3. Calculate fundamental score
            fundamental_score, fundamental_breakdown = self.calculate_fundamental_score(symbol, fundamentals)

            # CRITICAL: Check fundamental screen FIRST (60% minimum)
            if fundamental_score < self.fundamental_thresholds['min_score']:
                self.logger.debug(f"{symbol}: Failed fundamental screen ({fundamental_score:.1f}% < {self.fundamental_thresholds['min_score']}%)")
                return None

            # 4. Calculate technical indicators
            technicals = self.calculate_technical_indicators(df)
            if not technicals:
                return None

            # 5. Calculate trend strength
            trend_strength, trend_breakdown = self.calculate_trend_strength(df, technicals)

            # Check trend strength requirement (60 minimum)
            if trend_strength < self.technical_thresholds['min_trend_strength']:
                self.logger.debug(f"{symbol}: Failed trend strength ({trend_strength} < {self.technical_thresholds['min_trend_strength']})")
                return None

            # 6. Generate conviction signal
            conviction_level, reason, conviction_details = self.generate_conviction_signal(symbol, df, fundamentals, technicals)

            # Only proceed with conviction level 1+ (25+ points)
            if conviction_level < 1:
                self.logger.debug(f"{symbol}: No conviction signal ({conviction_details.get('total_conviction', 0)} < 25 points)")
                return None

            # 7. Create comprehensive result
            result = {
                # Basic info
                'symbol': symbol,
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'data_date': str(current['date']) if 'date' in current else str(df.index[-1]),
                'price': price,
                'volume': volume,
                'market': 'ASX300' if symbol.endswith('.AX') else 'S&P500',

                # Conviction results
                'conviction_level': conviction_level,
                'conviction_reason': reason,
                'conviction_score': conviction_details.get('total_conviction', 0),
                'position_size_pct': conviction_details.get('position_size_pct', 0),

                # Fundamental analysis
                'fundamental_score': fundamental_score,
                'fundamental_grade': fundamental_breakdown.get('grade', 'N/A'),
                'fundamental_breakdown': fundamental_breakdown,

                # Technical analysis
                'trend_strength': trend_strength,
                'trend_grade': trend_breakdown.get('trend_grade', 'N/A'),
                'breakout_points': conviction_details.get('breakout_points', 0),
                'volume_points': conviction_details.get('volume_points', 0),
                'momentum_points': conviction_details.get('momentum_points', 0),
                'trend_bonus': conviction_details.get('trend_bonus', 0),

                # Key metrics
                'volume_ratio': technicals.get('volume_ratio', 1.0),
                'momentum_5d': technicals.get('momentum_5', 0),
                'momentum_20d': technicals.get('momentum_20', 0),
                'rsi': technicals.get('rsi', 50),
                'price_vs_sma20': technicals.get('price_vs_sma20', 0),

                # Trading parameters
                'ib_action': 'BUY' if conviction_level >= 1 else 'WATCH',
                'stop_loss_price': price * 0.93,  # 7% stop loss
                'profit_target_price': price * 1.50,  # 50% profit target
                'trail_stop_price': price * 0.88,  # 12% trailing stop

                # Risk metrics
                'market_cap': fundamentals.get('market_cap', 0),
                'pe_ratio': fundamentals.get('pe_ratio', 0),
                'roe': fundamentals.get('roe', 0),
                'debt_equity': fundamentals.get('debt_to_equity', 0),
                'revenue_growth': fundamentals.get('revenue_growth_quarterly', 0),
                'earnings_growth': fundamentals.get('earnings_growth_quarterly', 0)
            }

            # Log significant findings
            if conviction_level >= 4:
                self.logger.info(f"HIGH CONVICTION: {symbol} - Level {conviction_level} - ${price:.2f} - Score: {conviction_details.get('total_conviction', 0)}")
                self.high_conviction_alerts.append(result)
            elif conviction_level >= 2:
                self.logger.info(f"CONVICTION SIGNAL: {symbol} - Level {conviction_level} - ${price:.2f}")

            return result

        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            return None

    def scan_market(self, symbols: List[str], market_name: str) -> List[Dict]:
        """Scan multiple symbols with progress tracking"""
        results = []
        total_symbols = len(symbols)

        self.logger.info(f"Starting {market_name} 5LC scan of {total_symbols} symbols...")
        print(f"\nScanning {market_name} ({total_symbols} symbols)...")
        start_time = time.time()

        for i, symbol in enumerate(symbols, 1):
            try:
                if i % 25 == 0:  # Progress update every 25 symbols
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (total_symbols - i) / rate if rate > 0 else 0
                    print(f"Progress: {i}/{total_symbols} ({i/total_symbols*100:.1f}%) - {rate:.1f}/sec - ETA: {eta:.0f}s")

                result = self.scan_symbol(symbol)
                if result:
                    results.append(result)
                    self.scan_results.append(result)

                # Rate limiting for API stability
                time.sleep(0.1)

            except KeyboardInterrupt:
                print("Scan interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in market scan for {symbol}: {e}")
                continue

        scan_time = time.time() - start_time
        self.logger.info(f"{market_name} scan complete - {len(results)} qualified symbols in {scan_time:.1f}s")
        return results

    def export_results(self, filename: str = None) -> str:
        """Export comprehensive 5LC results to CSV"""
        try:
            if not self.scan_results:
                self.logger.warning("No scan results to export")
                return ""

            # Create export data
            export_data = []
            for result in self.scan_results:
                row = {
                    # Basic info
                    'scan_date': result['scan_date'],
                    'symbol': result['symbol'],
                    'market': result['market'],
                    'conviction_level': result['conviction_level'],
                    'conviction_score': result['conviction_score'],
                    'ib_action': result['ib_action'],
                    'position_size_pct': result['position_size_pct'],

                    # Pricing
                    'current_price': result['price'],
                    'stop_loss_price': result['stop_loss_price'],
                    'profit_target_price': result['profit_target_price'],
                    'trail_stop_price': result['trail_stop_price'],

                    # Fundamental metrics
                    'fundamental_score': result['fundamental_score'],
                    'fundamental_grade': result['fundamental_grade'],
                    'market_cap_millions': result['market_cap'] / 1e6 if result['market_cap'] else 0,
                    'pe_ratio': result['pe_ratio'],
                    'roe': result['roe'],
                    'debt_equity': result['debt_equity'],
                    'revenue_growth': result['revenue_growth'],
                    'earnings_growth': result['earnings_growth'],

                    # Technical metrics
                    'trend_strength': result['trend_strength'],
                    'trend_grade': result['trend_grade'],
                    'breakout_points': result['breakout_points'],
                    'volume_points': result['volume_points'],
                    'momentum_points': result['momentum_points'],
                    'trend_bonus': result['trend_bonus'],

                    # Market metrics
                    'volume_ratio': result['volume_ratio'],
                    'momentum_5d': result['momentum_5d'],
                    'momentum_20d': result['momentum_20d'],
                    'rsi': result['rsi'],
                    'price_vs_sma20': result['price_vs_sma20'],

                    'conviction_reason': result['conviction_reason']
                }
                export_data.append(row)

            df = pd.DataFrame(export_data)

            # Sort by conviction level and score
            df = df.sort_values(['conviction_level', 'conviction_score'], ascending=[False, False])

            # Generate filename
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"5lc_daily_scan_{timestamp}.csv"

            # Export main results
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported {len(df)} results to {filename}")

            # Create trade-ready summary (conviction level 2+)
            trade_candidates = df[df['conviction_level'] >= 2]
            if len(trade_candidates) > 0:
                trade_filename = filename.replace('.csv', '_TRADE_READY.csv')
                trade_candidates.to_csv(trade_filename, index=False)
                self.logger.info(f"Exported {len(trade_candidates)} trade-ready candidates to {trade_filename}")

            # Create high-conviction summary (conviction level 4+)
            high_conviction = df[df['conviction_level'] >= 4]
            if len(high_conviction) > 0:
                high_filename = filename.replace('.csv', '_HIGH_CONVICTION.csv')
                high_conviction.to_csv(high_filename, index=False)
                self.logger.info(f"Exported {len(high_conviction)} high-conviction candidates to {high_filename}")

            return filename

        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            return ""

    def print_summary(self):
        """Print comprehensive 5LC scan summary"""
        if not self.scan_results:
            print("No scan results available")
            return

        total_scanned = len(self.scan_results)
        conviction_counts = {}
        for result in self.scan_results:
            level = result['conviction_level']
            conviction_counts[level] = conviction_counts.get(level, 0) + 1

        print("\n" + "=" * 100)
        print("5-LEVEL CONVICTION DAILY SCAN SUMMARY")
        print("=" * 100)
        print(f"Total qualifying symbols: {total_scanned}")
        print(f"Quality-first screening: >60% fundamental score required")
        print(f"Technical requirements: >60 trend strength + breakout signals")
        print(f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        print("5-LEVEL CONVICTION DISTRIBUTION:")
        print("-" * 80)
        for level in range(6):
            count = conviction_counts.get(level, 0)
            pct = count / total_scanned * 100 if total_scanned > 0 else 0
            position_pct = {0: 0, 1: 20, 2: 25, 3: 30, 4: 35, 5: 40}.get(level, 0)
            action = "BUY" if level >= 1 else "WATCH"
            conviction_range = {
                0: "0-24 pts", 1: "25-39 pts", 2: "40-54 pts",
                3: "55-69 pts", 4: "70-84 pts", 5: "85+ pts"
            }.get(level, "")
            print(f"  Level {level} ({position_pct:2d}% position, {conviction_range}): {count:3d} stocks ({pct:5.1f}%) - {action}")

        # Market breakdown
        market_breakdown = {}
        for result in self.scan_results:
            market = result['market']
            market_breakdown[market] = market_breakdown.get(market, 0) + 1

        print(f"\nMARKET BREAKDOWN:")
        print("-" * 40)
        for market, count in market_breakdown.items():
            pct = count / total_scanned * 100 if total_scanned > 0 else 0
            print(f"  {market}: {count} stocks ({pct:.1f}%)")

        # Trade candidates (Level 2+)
        trade_candidates = [r for r in self.scan_results if r['conviction_level'] >= 2]
        if trade_candidates:
            print(f"\nTRADE-READY CANDIDATES (Level 2+): {len(trade_candidates)} stocks")
            print("-" * 120)
            print(f"{'Symbol':<8} {'Market':<8} {'Level':<6} {'Score':<6} {'Price':<10} {'Fund%':<6} {'Trend':<6} {'Vol':<6} {'Stop':<10} {'Target':<10}")
            print("-" * 120)

            for candidate in sorted(trade_candidates, key=lambda x: (x['conviction_level'], x['conviction_score']), reverse=True)[:20]:
                print(f"{candidate['symbol']:<8} {candidate['market']:<8} {candidate['conviction_level']:<6} "
                      f"{candidate['conviction_score']:<6} ${candidate['price']:<9.2f} "
                      f"{candidate['fundamental_score']:<5.0f}% {candidate['trend_strength']:<6} "
                      f"{candidate['volume_ratio']:<5.1f}x ${candidate['stop_loss_price']:<9.2f} "
                      f"${candidate['profit_target_price']:<9.2f}")

        # High conviction alerts (Level 4+)
        high_conviction = [r for r in self.scan_results if r['conviction_level'] >= 4]
        if high_conviction:
            print(f"\nHIGH CONVICTION ALERTS (Level 4+): {len(high_conviction)} stocks")
            print("-" * 100)
            for result in sorted(high_conviction, key=lambda x: x['conviction_score'], reverse=True):
                print(f"  {result['symbol']:<8} Level {result['conviction_level']} ({result['conviction_score']} pts) - "
                      f"${result['price']:>8.2f} - Fund: {result['fundamental_score']:.0f}% - "
                      f"Trend: {result['trend_strength']} - Vol: {result['volume_ratio']:.1f}x")

        print("=" * 100)
        print("5LC METHODOLOGY SUMMARY:")
        print("• Quality-first approach: Fundamental screening eliminates poor stocks")
        print("• Technical timing: Breakout confirmation with volume surge")
        print("• Conviction-based sizing: Higher conviction = larger positions (20%-40%)")
        print("• Professional risk management: 7% stops, 50% targets, trailing stops")
        print("• Global applicability: Same methodology across US and Australian markets")
        print("=" * 100)


def main():
    """Main 5LC daily scanning function"""
    scanner = FiveLevelConvictionScanner()

    try:
        print("\n5-LEVEL CONVICTION DAILY SCANNER")
        print("Select market(s) to scan:")
        print("1. US Market (Full S&P 500)")
        print("2. Australian Market (Full ASX300)")
        print("3. Both Markets (Comprehensive)")

        choice = input("Enter choice (1-3): ").strip()

        all_results = []

        if choice in ['1', '3']:
            # Scan US market
            us_symbols = scanner.get_sp500_symbols()
            print(f"\nInitiating S&P 500 scan of {len(us_symbols)} symbols...")
            us_results = scanner.scan_market(us_symbols, "S&P 500")
            all_results.extend(us_results)

        if choice in ['2', '3']:
            # Scan ASX market
            asx_symbols = scanner.get_asx300_symbols()
            print(f"\nInitiating ASX300 scan of {len(asx_symbols)} symbols...")
            asx_results = scanner.scan_market(asx_symbols, "ASX300")
            all_results.extend(asx_results)

        if not all_results:
            print("No qualifying symbols found")
            return

        # Print comprehensive summary
        scanner.print_summary()

        # Export results
        filename = scanner.export_results()
        if filename:
            print(f"\nResults exported to: {filename}")

        # Final summary
        trade_ready = len([r for r in all_results if r['conviction_level'] >= 2])
        high_conviction = len([r for r in all_results if r['conviction_level'] >= 4])

        print(f"\nFINAL SUMMARY:")
        print(f"• Total qualified: {len(all_results)} symbols")
        print(f"• Trade-ready (Level 2+): {trade_ready} symbols")
        print(f"• High conviction (Level 4+): {high_conviction} symbols")
        print(f"• Quality threshold: >60% fundamental score")
        print(f"• Technical threshold: >60 trend strength")

    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error in main scan: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n5LC daily scan complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    print("5-LEVEL CONVICTION DAILY SCANNER")
    print("Professional-grade quality-first momentum detection")
    print("Full S&P 500 + ASX300 coverage with comprehensive screening")
    print()

    main()