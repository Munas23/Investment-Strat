"""
TECHNICAL SCREENER - 5-Level Conviction System
===============================================

Screens liquid stocks (from liquidity_screener.py) for technical setups.
Assigns conviction levels 1-5 based on technical criteria.

Run daily to identify high-probability setups.
Results saved monthly in results_YYYY-MM folders.

Author: Trading System
Date: 2026-01-02
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import time
import logging
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class TechnicalScreener:
    """
    Technical screener with 5-level conviction system

    Conviction Levels:
    - Level 5: MAXIMUM (all criteria perfect)
    - Level 4: HIGH (most criteria strong)
    - Level 3: MODERATE (core criteria met)
    - Level 2: LOW (weak setup)
    - Level 1: MINIMAL (avoid)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # =====================================================================
        # ADJUSTABLE SCREENING CRITERIA - MODIFY THESE TO EXPERIMENT
        # =====================================================================

        self.criteria = {
            # VOLUME (Average Volume Analysis)
            'volume': {
                'min_avg_volume': 100000,  # Minimum average daily volume
                'recent_period': 20,        # Days for recent volume average
                'volume_spike_excellent': 2.0,  # 100%+ above average
                'volume_spike_good': 1.5,       # 50%+ above average
                'volume_spike_pass': 1.4,       # 40%+ above average (O'Neil minimum)
            },

            # RELATIVE STRENGTH (IBD-style RS Rating)
            'relative_strength': {
                'rs_excellent': 90,  # Top 10% (Level 5)
                'rs_good': 85,       # Top 15% (Level 4)
                'rs_pass': 80,       # Top 20% (Level 3)
                'rs_minimum': 70,    # Below this = avoid
            },

            # PRICE PERFORMANCE (3-month momentum)
            'price_performance': {
                'period_days': 63,        # ~3 months (trading days)
                'gain_excellent': 50,     # 50%+ gain = excellent
                'gain_good': 40,          # 40%+ gain = good
                'gain_pass': 30,          # 30%+ gain = minimum (your requirement)
                'gain_minimum': 20,       # Below 20% = weak
            },

            # MOVING AVERAGES (Trend alignment)
            'moving_averages': {
                'ma_10': 10,
                'ma_20': 20,
                'ma_50': 50,
                'ma_150': 150,
                'ma_200': 200,
                # Minervini-style alignment scoring
                'use_minervini_template': True,
            },

            # 52-WEEK RANGE (Price position)
            '52_week': {
                'min_from_low': 30,       # Min % above 52-week low (Minervini: 30%)
                'max_from_high': 25,      # Max % below 52-week high (Minervini: 25%)
                'new_high_bonus': True,   # Bonus points for new highs
            },

            # ATR (Average True Range for volatility)
            'atr': {
                'period': 14,
                'calculate': True,
                'max_atr_percent': 15,    # Skip if ATR > 15% of price (too volatile)
            },

            # PRICE FILTERS
            'price': {
                'min_price': 5,           # Minimum stock price (avoid penny stocks)
                'max_price': 9999,        # Maximum price (no limit)
            },

            # PATTERN DETECTION (Basic)
            'patterns': {
                'detect_consolidation': True,
                'consolidation_weeks': [2, 8],    # 2-8 week consolidation
                'detect_breakout': True,
                'breakout_lookback': 20,          # Days to look back for breakout
            },
        }

        # =====================================================================
        # CONVICTION SCORING WEIGHTS (Total = 100 points)
        # =====================================================================

        self.scoring = {
            'volume': 15,              # 15 points max
            'relative_strength': 20,    # 20 points max (most important)
            'price_performance': 15,    # 15 points max
            'moving_averages': 25,      # 25 points max (Minervini template)
            '52_week_position': 10,     # 10 points max
            'trend_quality': 10,        # 10 points max
            'breakout_setup': 5,        # 5 points max (bonus)
        }

        # Conviction thresholds (% of max 100 points)
        self.conviction_levels = {
            5: 80,  # 80%+ = Level 5 (MAXIMUM)
            4: 65,  # 65-79% = Level 4 (HIGH)
            3: 50,  # 50-64% = Level 3 (MODERATE)
            2: 35,  # 35-49% = Level 2 (LOW)
            1: 0,   # <35% = Level 1 (MINIMAL)
        }

        self.logger.info("TECHNICAL SCREENER - 5-LEVEL CONVICTION SYSTEM")
        self.logger.info("=" * 80)
        self.logger.info("SCREENING CRITERIA:")
        self.logger.info(f"  Volume Spike: {self.criteria['volume']['volume_spike_pass']}x average minimum")
        self.logger.info(f"  RS Rating: {self.criteria['relative_strength']['rs_pass']}+ minimum")
        self.logger.info(f"  3-Month Gain: {self.criteria['price_performance']['gain_pass']}%+ minimum")
        self.logger.info(f"  Price Range: ${self.criteria['price']['min_price']}+")
        self.logger.info("")
        self.logger.info("CONVICTION LEVELS:")
        self.logger.info(f"  Level 5 (MAXIMUM):  {self.conviction_levels[5]}%+ score")
        self.logger.info(f"  Level 4 (HIGH):     {self.conviction_levels[4]}-{self.conviction_levels[5]-1}% score")
        self.logger.info(f"  Level 3 (MODERATE): {self.conviction_levels[3]}-{self.conviction_levels[4]-1}% score")
        self.logger.info(f"  Level 2 (LOW):      {self.conviction_levels[2]}-{self.conviction_levels[3]-1}% score")
        self.logger.info(f"  Level 1 (MINIMAL):  <{self.conviction_levels[2]}% score")
        self.logger.info("=" * 80)

    def find_latest_download_folder(self) -> Optional[Path]:
        """Find the most recent downloads folder in the scans directory"""
        script_dir = Path(__file__).parent
        scans_path = script_dir.parent

        download_folders = list(scans_path.glob('downloads_*'))

        if not download_folders:
            self.logger.error("No download folders found in scans directory")
            return None

        latest_folder = max(download_folders, key=lambda p: p.name)
        self.logger.info(f"Using data from: {latest_folder}")

        return latest_folder

    def load_liquid_stocks(self, download_folder: Path) -> pd.DataFrame:
        """Load liquid stocks from liquidity screener results"""
        # Look for TRADEABLE file (Tier 1-3 stocks)
        tradeable_files = list(download_folder.glob('liquidity_screen_*_TRADEABLE.csv'))

        if not tradeable_files:
            self.logger.error("No TRADEABLE liquidity screen file found")
            return pd.DataFrame()

        latest_file = max(tradeable_files, key=lambda p: p.name)
        self.logger.info(f"Loading liquid stocks from: {latest_file.name}")

        df = pd.read_csv(latest_file)
        self.logger.info(f"Loaded {len(df)} liquid stocks (Tier 1-3)")

        # Show tier breakdown
        if 'liquidity_tier' in df.columns:
            tier_counts = df['liquidity_tier'].value_counts().sort_index()
            for tier, count in tier_counts.items():
                tier_name = tier.split(' - ')[1] if ' - ' in tier else tier
                self.logger.info(f"  {tier}: {count} stocks")

        return df

    def calculate_atr(self, highs: List[float], lows: List[float],
                     closes: List[float], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(closes) < period + 1:
            return 0.0

        trs = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            trs.append(tr)

        if len(trs) < period:
            return 0.0

        # Wilder's smoothing
        atr = sum(trs[:period]) / period
        for i in range(period, len(trs)):
            atr = ((atr * (period - 1)) + trs[i]) / period

        return atr

    def calculate_rs_rating(self, stock_returns: Dict[str, float],
                           all_returns: List[Dict[str, float]]) -> int:
        """
        Calculate IBD-style Relative Strength Rating (1-99)

        Weighted: 40% last 3 months, 20% each prior quarter
        """
        # Calculate weighted return
        weighted_return = (
            stock_returns.get('3m', 0) * 0.40 +
            stock_returns.get('q1', 0) * 0.20 +
            stock_returns.get('q2', 0) * 0.20 +
            stock_returns.get('q3', 0) * 0.20
        )

        # Calculate percentile rank
        all_weighted = [
            (r.get('3m', 0) * 0.40 +
             r.get('q1', 0) * 0.20 +
             r.get('q2', 0) * 0.20 +
             r.get('q3', 0) * 0.20)
            for r in all_returns
        ]

        rank = sum(1 for r in all_weighted if r < weighted_return)
        percentile = (rank / len(all_weighted)) * 100 if all_weighted else 0

        return int(min(99, max(1, percentile)))

    def score_volume(self, recent_volume: float, avg_volume: float) -> float:
        """Score volume (0-15 points)"""
        max_points = self.scoring['volume']

        if avg_volume == 0:
            return 0

        volume_ratio = recent_volume / avg_volume

        if volume_ratio >= self.criteria['volume']['volume_spike_excellent']:
            return max_points  # 15 pts
        elif volume_ratio >= self.criteria['volume']['volume_spike_good']:
            return max_points * 0.80  # 12 pts
        elif volume_ratio >= self.criteria['volume']['volume_spike_pass']:
            return max_points * 0.60  # 9 pts
        elif volume_ratio >= 1.2:
            return max_points * 0.40  # 6 pts
        elif volume_ratio >= 1.0:
            return max_points * 0.20  # 3 pts
        else:
            return 0

    def score_rs_rating(self, rs_rating: int) -> float:
        """Score RS rating (0-20 points)"""
        max_points = self.scoring['relative_strength']

        if rs_rating >= self.criteria['relative_strength']['rs_excellent']:
            return max_points  # 20 pts
        elif rs_rating >= self.criteria['relative_strength']['rs_good']:
            return max_points * 0.85  # 17 pts
        elif rs_rating >= self.criteria['relative_strength']['rs_pass']:
            return max_points * 0.70  # 14 pts
        elif rs_rating >= self.criteria['relative_strength']['rs_minimum']:
            return max_points * 0.50  # 10 pts
        else:
            # Linear scale below 70
            return max_points * (rs_rating / 100) * 0.50

    def score_price_performance(self, gain_pct: float) -> float:
        """Score 3-month price performance (0-15 points)"""
        max_points = self.scoring['price_performance']

        if gain_pct >= self.criteria['price_performance']['gain_excellent']:
            return max_points  # 15 pts
        elif gain_pct >= self.criteria['price_performance']['gain_good']:
            return max_points * 0.85  # 13 pts
        elif gain_pct >= self.criteria['price_performance']['gain_pass']:
            return max_points * 0.70  # 11 pts
        elif gain_pct >= self.criteria['price_performance']['gain_minimum']:
            return max_points * 0.50  # 8 pts
        elif gain_pct > 0:
            return max_points * (gain_pct / self.criteria['price_performance']['gain_pass']) * 0.70
        else:
            return 0

    def score_moving_averages(self, price: float, mas: Dict[str, float]) -> float:
        """
        Score moving average alignment (0-25 points)
        Uses Minervini's 8-point trend template concept
        """
        max_points = self.scoring['moving_averages']
        score = 0
        checks_met = 0
        total_checks = 8

        # Check 1: Price > 150 MA AND Price > 200 MA
        if price > mas.get('ma_150', 0) and price > mas.get('ma_200', 0):
            checks_met += 1

        # Check 2: 150 MA > 200 MA
        if mas.get('ma_150', 0) > mas.get('ma_200', 0):
            checks_met += 1

        # Check 3: 200 MA trending up (approximate: 200 MA > value from 20 days ago)
        # We'll give credit if 200 MA exists and price is well above it
        if price > mas.get('ma_200', 0) * 1.05:  # 5% above as proxy for uptrend
            checks_met += 1

        # Check 4: 50 MA > 150 MA AND 50 MA > 200 MA
        if mas.get('ma_50', 0) > mas.get('ma_150', 0) and mas.get('ma_50', 0) > mas.get('ma_200', 0):
            checks_met += 1

        # Check 5: Price > 50 MA
        if price > mas.get('ma_50', 0):
            checks_met += 1

        # Check 6: Price > 30% above 52-week low (checked separately)
        # Will give credit here if price is above all MAs
        if (price > mas.get('ma_10', 0) and price > mas.get('ma_20', 0) and
            price > mas.get('ma_50', 0)):
            checks_met += 1

        # Check 7: Price within 25% of 52-week high (checked separately)
        # Give credit if above 20 MA and 50 MA
        if price > mas.get('ma_20', 0) and price > mas.get('ma_50', 0):
            checks_met += 1

        # Check 8: All short-term MAs aligned (10 > 20 > 50)
        if (mas.get('ma_10', 0) > mas.get('ma_20', 0) and
            mas.get('ma_20', 0) > mas.get('ma_50', 0)):
            checks_met += 1

        # Score based on checks met
        score = max_points * (checks_met / total_checks)

        return score

    def score_52_week_position(self, price: float, high_52w: float, low_52w: float) -> float:
        """Score 52-week price position (0-10 points)"""
        max_points = self.scoring['52_week_position']

        if high_52w == 0 or low_52w == 0:
            return 0

        # Distance from 52-week low
        pct_from_low = ((price - low_52w) / low_52w) * 100

        # Distance from 52-week high
        pct_from_high = ((high_52w - price) / high_52w) * 100

        score = 0

        # Bonus for being near highs
        if pct_from_high <= 5:  # Within 5% of 52-week high
            score += max_points * 0.50  # 5 pts
        elif pct_from_high <= self.criteria['52_week']['max_from_high']:  # Within 25%
            score += max_points * 0.40  # 4 pts
        elif pct_from_high <= 40:
            score += max_points * 0.25  # 2.5 pts

        # Bonus for being well above lows
        if pct_from_low >= 50:  # 50%+ above lows
            score += max_points * 0.50  # 5 pts
        elif pct_from_low >= self.criteria['52_week']['min_from_low']:  # 30%+ above
            score += max_points * 0.40  # 4 pts
        elif pct_from_low >= 20:
            score += max_points * 0.25  # 2.5 pts

        return min(max_points, score)

    def score_trend_quality(self, consecutive_up_days: int,
                           higher_highs: bool, higher_lows: bool) -> float:
        """Score trend quality (0-10 points)"""
        max_points = self.scoring['trend_quality']
        score = 0

        # Higher highs and higher lows (classic uptrend)
        if higher_highs and higher_lows:
            score += max_points * 0.60  # 6 pts
        elif higher_highs or higher_lows:
            score += max_points * 0.30  # 3 pts

        # Recent momentum (consecutive up days)
        if consecutive_up_days >= 3:
            score += max_points * 0.40  # 4 pts
        elif consecutive_up_days >= 2:
            score += max_points * 0.20  # 2 pts

        return min(max_points, score)

    def detect_breakout(self, prices: List[float], volumes: List[float],
                       lookback: int = 20) -> bool:
        """Detect if stock is breaking out (simple version)"""
        if len(prices) < lookback + 1:
            return False

        current_price = prices[-1]
        recent_high = max(prices[-lookback:-1])

        # Breakout = current price > recent high
        is_breakout = current_price > recent_high

        # Volume confirmation (current volume > average)
        if len(volumes) >= lookback:
            avg_volume = sum(volumes[-lookback:-1]) / (lookback - 1)
            current_volume = volumes[-1]
            volume_confirmed = current_volume > avg_volume
        else:
            volume_confirmed = False

        return is_breakout and volume_confirmed

    def analyze_stock(self, symbol: str, all_returns: List[Dict]) -> Optional[Dict]:
        """Analyze a single stock and return technical metrics + conviction score"""
        try:
            # Download data (6 months for calculations)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)

            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)

            if hist.empty or len(hist) < 65:  # Need at least 3 months
                return None

            # Current price
            current_price = hist['Close'].iloc[-1]

            # Price filter
            if current_price < self.criteria['price']['min_price']:
                return None

            # Calculate 3-month return
            if len(hist) >= 63:
                price_3m_ago = hist['Close'].iloc[-63]
                gain_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
            else:
                gain_3m = 0

            # Skip if doesn't meet minimum 3-month gain
            if gain_3m < self.criteria['price_performance']['gain_pass']:
                return None

            # Calculate returns for RS rating
            returns = {'3m': gain_3m}

            # Moving averages
            mas = {}
            for ma_name, ma_period in [('ma_10', 10), ('ma_20', 20), ('ma_50', 50),
                                       ('ma_150', 150), ('ma_200', 200)]:
                if len(hist) >= ma_period:
                    mas[ma_name] = hist['Close'].rolling(window=ma_period).mean().iloc[-1]
                else:
                    mas[ma_name] = 0

            # Volume analysis
            avg_volume_20 = hist['Volume'].tail(20).mean()
            recent_volume = hist['Volume'].tail(5).mean()  # Last 5 days average

            # Skip if below minimum volume
            if avg_volume_20 < self.criteria['volume']['min_avg_volume']:
                return None

            # 52-week high/low
            high_52w = hist['High'].tail(252).max() if len(hist) >= 252 else hist['High'].max()
            low_52w = hist['Low'].tail(252).min() if len(hist) >= 252 else hist['Low'].min()

            # ATR
            if self.criteria['atr']['calculate'] and len(hist) >= 15:
                atr = self.calculate_atr(
                    hist['High'].tolist(),
                    hist['Low'].tolist(),
                    hist['Close'].tolist(),
                    period=self.criteria['atr']['period']
                )
                atr_percent = (atr / current_price) * 100

                # Skip if too volatile
                if atr_percent > self.criteria['atr']['max_atr_percent']:
                    return None
            else:
                atr = 0
                atr_percent = 0

            # Calculate RS rating (approximation without full market data)
            rs_rating = self.calculate_rs_rating(returns, all_returns)

            # Skip if RS too low
            if rs_rating < self.criteria['relative_strength']['rs_pass']:
                return None

            # Trend analysis
            prices_10d = hist['Close'].tail(10).tolist()
            consecutive_up = 0
            for i in range(len(prices_10d) - 1, 0, -1):
                if prices_10d[i] > prices_10d[i-1]:
                    consecutive_up += 1
                else:
                    break

            # Higher highs and lows (last 20 days)
            if len(hist) >= 20:
                prices_20d = hist['Close'].tail(20).tolist()
                mid_point = len(prices_20d) // 2
                first_half_high = max(prices_20d[:mid_point])
                second_half_high = max(prices_20d[mid_point:])
                first_half_low = min(prices_20d[:mid_point])
                second_half_low = min(prices_20d[mid_point:])

                higher_highs = second_half_high > first_half_high
                higher_lows = second_half_low > first_half_low
            else:
                higher_highs = False
                higher_lows = False

            # Breakout detection
            is_breakout = self.detect_breakout(
                hist['Close'].tolist(),
                hist['Volume'].tolist(),
                self.criteria['patterns']['breakout_lookback']
            )

            # ========================================
            # CONVICTION SCORING
            # ========================================

            score = 0

            # 1. Volume (15 points)
            score += self.score_volume(recent_volume, avg_volume_20)

            # 2. RS Rating (20 points)
            score += self.score_rs_rating(rs_rating)

            # 3. Price Performance (15 points)
            score += self.score_price_performance(gain_3m)

            # 4. Moving Averages (25 points)
            score += self.score_moving_averages(current_price, mas)

            # 5. 52-Week Position (10 points)
            score += self.score_52_week_position(current_price, high_52w, low_52w)

            # 6. Trend Quality (10 points)
            score += self.score_trend_quality(consecutive_up, higher_highs, higher_lows)

            # 7. Breakout Bonus (5 points)
            if is_breakout:
                score += self.scoring['breakout_setup']

            # Total score (out of 100)
            total_score = min(100, score)

            # Assign conviction level
            conviction = 1
            for level in sorted(self.conviction_levels.keys(), reverse=True):
                if total_score >= self.conviction_levels[level]:
                    conviction = level
                    break

            # Calculate distances from 52-week levels
            pct_from_high = ((high_52w - current_price) / high_52w) * 100
            pct_from_low = ((current_price - low_52w) / low_52w) * 100

            return {
                'symbol': symbol,
                'conviction_level': conviction,
                'total_score': round(total_score, 1),
                'price': round(current_price, 2),
                'gain_3m_pct': round(gain_3m, 1),
                'rs_rating': rs_rating,
                'volume_ratio': round(recent_volume / avg_volume_20, 2),
                'avg_volume': int(avg_volume_20),
                'ma_10': round(mas['ma_10'], 2),
                'ma_20': round(mas['ma_20'], 2),
                'ma_50': round(mas['ma_50'], 2),
                'ma_150': round(mas['ma_150'], 2),
                'ma_200': round(mas['ma_200'], 2),
                'high_52w': round(high_52w, 2),
                'low_52w': round(low_52w, 2),
                'pct_from_high': round(pct_from_high, 1),
                'pct_from_low': round(pct_from_low, 1),
                'atr': round(atr, 2),
                'atr_percent': round(atr_percent, 2),
                'consecutive_up_days': consecutive_up,
                'higher_highs': higher_highs,
                'higher_lows': higher_lows,
                'is_breakout': is_breakout,
            }

        except Exception as e:
            self.logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    def screen_stocks(self, liquid_stocks: pd.DataFrame) -> pd.DataFrame:
        """Screen all liquid stocks and assign conviction levels"""
        symbols = liquid_stocks['symbol'].tolist()
        results = []

        self.logger.info(f"Screening {len(symbols)} liquid stocks for technical setups...")

        # First pass: collect all returns for RS calculation
        all_returns = []
        for i, symbol in enumerate(symbols, 1):
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=180)
                hist = yf.download(symbol, start=start_date, end=end_date, progress=False)

                if not hist.empty and len(hist) >= 63:
                    current = hist['Close'].iloc[-1]
                    price_3m = hist['Close'].iloc[-63] if len(hist) >= 63 else current
                    gain_3m = ((current - price_3m) / price_3m) * 100
                    all_returns.append({'3m': gain_3m, 'q1': 0, 'q2': 0, 'q3': 0})
                else:
                    all_returns.append({'3m': 0, 'q1': 0, 'q2': 0, 'q3': 0})
            except:
                all_returns.append({'3m': 0, 'q1': 0, 'q2': 0, 'q3': 0})

            if i % 50 == 0:
                self.logger.info(f"Collecting market data: {i}/{len(symbols)} ({i/len(symbols)*100:.1f}%)")

            time.sleep(0.1)  # Rate limiting

        self.logger.info("Market data collection complete. Analyzing stocks...")

        # Second pass: analyze each stock
        for i, symbol in enumerate(symbols, 1):
            result = self.analyze_stock(symbol, all_returns)

            if result:
                # Add liquidity tier from original data
                if 'liquidity_tier' in liquid_stocks.columns:
                    liq_data = liquid_stocks[liquid_stocks['symbol'] == symbol]
                    if not liq_data.empty:
                        result['liquidity_tier'] = liq_data.iloc[0]['liquidity_tier']

                results.append(result)

            if i % 50 == 0:
                passed = len(results)
                self.logger.info(f"Progress: {i}/{len(symbols)} ({i/len(symbols)*100:.1f}%) - {passed} passed")

            time.sleep(0.1)  # Rate limiting

        if not results:
            self.logger.warning("No stocks passed the technical screen")
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Sort by conviction level (descending) then total score (descending)
        df = df.sort_values(['conviction_level', 'total_score'], ascending=[False, False])

        return df

    def save_results(self, df: pd.DataFrame) -> None:
        """Save screening results to monthly folder"""
        if df.empty:
            self.logger.warning("No results to save")
            return

        # Get current month folder
        script_dir = Path(__file__).parent
        current_month = datetime.now().strftime('%Y-%m')
        results_folder = script_dir / f'results_{current_month}'
        results_folder.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save all results
        full_file = results_folder / f'technical_screen_{timestamp}_FULL.csv'
        df.to_csv(full_file, index=False)
        self.logger.info(f"Saved full results to: {full_file}")

        # Save by conviction level
        for level in [5, 4, 3]:
            level_df = df[df['conviction_level'] == level]
            if not level_df.empty:
                level_name = {5: 'MAXIMUM', 4: 'HIGH', 3: 'MODERATE'}[level]
                level_file = results_folder / f'technical_screen_{timestamp}_LEVEL{level}_{level_name}.csv'
                level_df.to_csv(level_file, index=False)
                self.logger.info(f"Saved Level {level} ({level_name}): {len(level_df)} stocks -> {level_file.name}")

        # Save top candidates (Level 4-5)
        top_df = df[df['conviction_level'] >= 4]
        if not top_df.empty:
            top_file = results_folder / f'technical_screen_{timestamp}_TOP_CANDIDATES.csv'
            top_df.to_csv(top_file, index=False)
            self.logger.info(f"Saved top candidates (Level 4-5): {len(top_df)} stocks -> {top_file.name}")

        self.logger.info(f"\nAll results saved to: {results_folder}")

    def print_summary(self, df: pd.DataFrame) -> None:
        """Print screening summary statistics"""
        if df.empty:
            return

        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("TECHNICAL SCREENING SUMMARY")
        self.logger.info("=" * 80)

        # Conviction level breakdown
        self.logger.info("\nCONVICTION LEVEL DISTRIBUTION:")
        for level in sorted(df['conviction_level'].unique(), reverse=True):
            count = len(df[df['conviction_level'] == level])
            pct = (count / len(df)) * 100
            level_name = {5: 'MAXIMUM', 4: 'HIGH', 3: 'MODERATE', 2: 'LOW', 1: 'MINIMAL'}
            self.logger.info(f"  Level {level} ({level_name.get(level, 'UNKNOWN')}): {count} stocks ({pct:.1f}%)")

        # Score statistics
        self.logger.info(f"\nSCORE STATISTICS:")
        self.logger.info(f"  Mean Score: {df['total_score'].mean():.1f}/100")
        self.logger.info(f"  Median Score: {df['total_score'].median():.1f}/100")
        self.logger.info(f"  Min Score: {df['total_score'].min():.1f}/100")
        self.logger.info(f"  Max Score: {df['total_score'].max():.1f}/100")

        # Top 10 stocks
        self.logger.info(f"\nTOP 10 STOCKS BY CONVICTION SCORE:")
        top_10 = df.head(10)
        for idx, row in top_10.iterrows():
            self.logger.info(
                f"  {row['symbol']:6s} - Score: {row['total_score']:5.1f} (Level {row['conviction_level']}) - "
                f"Price: ${row['price']:7.2f} - 3M Gain: {row['gain_3m_pct']:+6.1f}% - RS: {row['rs_rating']}"
            )

        self.logger.info("=" * 80)


def main():
    """Main execution function"""
    screener = TechnicalScreener()

    # Find latest download folder
    download_folder = screener.find_latest_download_folder()
    if not download_folder:
        return

    # Load liquid stocks
    liquid_stocks = screener.load_liquid_stocks(download_folder)
    if liquid_stocks.empty:
        return

    # Screen stocks
    results_df = screener.screen_stocks(liquid_stocks)

    if results_df.empty:
        screener.logger.warning("No stocks passed the technical screen")
        return

    # Save results
    screener.save_results(results_df)

    # Print summary
    screener.print_summary(results_df)

    screener.logger.info("\nTECHNICAL SCREENING COMPLETE!")


if __name__ == "__main__":
    main()
