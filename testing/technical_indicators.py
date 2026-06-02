"""
Technical indicators for strategy testing framework
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional

class TechnicalIndicators:
    """Comprehensive technical indicators for trading strategies"""
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = TechnicalIndicators.sma(data, window)
        std = data.rolling(window=window).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        return k_percent, d_percent
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(window=window).mean()
    
    @staticmethod
    def volume_sma(volume: pd.Series, window: int) -> pd.Series:
        """Volume Simple Moving Average"""
        return volume.rolling(window=window).mean()
    
    @staticmethod
    def price_change_percent(data: pd.Series, periods: int) -> pd.Series:
        """Price change percentage over periods"""
        return ((data / data.shift(periods)) - 1) * 100
    
    @staticmethod
    def volatility(data: pd.Series, window: int = 20) -> pd.Series:
        """Price volatility (rolling standard deviation)"""
        returns = data.pct_change()
        return returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
    
    @staticmethod
    def is_new_high(data: pd.Series, window: int) -> pd.Series:
        """Check if current price is new high over window"""
        rolling_max = data.rolling(window=window).max()
        return data >= rolling_max
    
    @staticmethod
    def is_new_low(data: pd.Series, window: int) -> pd.Series:
        """Check if current price is new low over window"""
        rolling_min = data.rolling(window=window).min()
        return data <= rolling_min
    
    @staticmethod
    def gap_up(open_price: pd.Series, prev_close: pd.Series, threshold: float = 0.02) -> pd.Series:
        """Detect gap up (open > previous close by threshold)"""
        return (open_price / prev_close.shift(1) - 1) > threshold
    
    @staticmethod
    def higher_highs_lows(high: pd.Series, low: pd.Series, window: int = 5) -> Tuple[pd.Series, pd.Series]:
        """Detect higher highs and higher lows pattern"""
        higher_highs = (high > high.shift(window)) & (high.shift(window) > high.shift(window*2))
        higher_lows = (low > low.shift(window)) & (low.shift(window) > low.shift(window*2))
        return higher_highs, higher_lows

class StrategyConditions:
    """Strategy condition checkers"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.indicators = TechnicalIndicators()
        self._calculate_all_indicators()
    
    def _calculate_all_indicators(self):
        """Pre-calculate commonly used indicators"""
        close = self.data['close']
        high = self.data['high']
        low = self.data['low']
        volume = self.data['volume']
        
        # Moving averages
        self.data['sma_10'] = self.indicators.sma(close, 10)
        self.data['sma_20'] = self.indicators.sma(close, 20)
        self.data['sma_50'] = self.indicators.sma(close, 50)
        self.data['sma_200'] = self.indicators.sma(close, 200)
        self.data['ema_12'] = self.indicators.ema(close, 12)
        self.data['ema_26'] = self.indicators.ema(close, 26)
        
        # Technical indicators
        self.data['rsi'] = self.indicators.rsi(close)
        macd, signal, histogram = self.indicators.macd(close)
        self.data['macd'] = macd
        self.data['macd_signal'] = signal
        self.data['macd_histogram'] = histogram
        
        upper_bb, middle_bb, lower_bb = self.indicators.bollinger_bands(close)
        self.data['bb_upper'] = upper_bb
        self.data['bb_middle'] = middle_bb
        self.data['bb_lower'] = lower_bb
        
        k_stoch, d_stoch = self.indicators.stochastic(high, low, close)
        self.data['stoch_k'] = k_stoch
        self.data['stoch_d'] = d_stoch
        
        # Price metrics
        self.data['price_change_5d'] = self.indicators.price_change_percent(close, 5)
        self.data['price_change_10d'] = self.indicators.price_change_percent(close, 10)
        self.data['price_change_20d'] = self.indicators.price_change_percent(close, 20)
        self.data['price_change_60d'] = self.indicators.price_change_percent(close, 60)
        
        # Volume
        self.data['volume_sma_20'] = self.indicators.volume_sma(volume, 20)
        self.data['volume_ratio'] = volume / self.data['volume_sma_20']
        
        # Volatility
        self.data['volatility_20'] = self.indicators.volatility(close, 20)
        
        # New highs/lows
        self.data['new_high_20'] = self.indicators.is_new_high(close, 20)
        self.data['new_high_60'] = self.indicators.is_new_high(close, 60)
        
    def golden_cross(self) -> pd.Series:
        """Strategy 1: Golden Cross (50MA > 200MA)"""
        return (self.data['sma_50'] > self.data['sma_200']) & \
               (self.data['close'] > self.data['sma_50'])
    
    def fast_ma_cross(self) -> pd.Series:
        """Strategy 2: Fast MA Cross (10MA > 20MA)"""
        return (self.data['sma_10'] > self.data['sma_20']) & \
               (self.data['close'] > self.data['sma_10'])
    
    def triple_ma_alignment(self) -> pd.Series:
        """Strategy 3: Triple MA Alignment (10 > 20 > 50)"""
        return (self.data['sma_10'] > self.data['sma_20']) & \
               (self.data['sma_20'] > self.data['sma_50']) & \
               (self.data['close'] > self.data['sma_10'])
    
    def ema_cross(self) -> pd.Series:
        """Strategy 4: EMA Cross (EMA12 > EMA26)"""
        return (self.data['ema_12'] > self.data['ema_26']) & \
               (self.data['close'] > self.data['ema_12'])
    
    def strong_momentum(self) -> pd.Series:
        """Strategy 5: Strong Momentum (Up 40% in 60 days)"""
        return (self.data['price_change_60d'] > 40) & \
               (self.data['close'] > self.data['sma_20'])
    
    def moderate_momentum(self) -> pd.Series:
        """Strategy 6: Moderate Momentum (Up 10% in 20 days)"""
        return (self.data['price_change_20d'] > 10) & \
               (self.data['close'] > self.data['sma_10'])
    
    def momentum_ma_confirmation(self) -> pd.Series:
        """Strategy 7: Momentum + MA (Up 15% + above 50MA)"""
        return (self.data['price_change_20d'] > 15) & \
               (self.data['close'] > self.data['sma_50'])
    
    def acceleration_pattern(self) -> pd.Series:
        """Strategy 8: Acceleration (5% in 5 days + 15% in 30 days)"""
        price_change_30d = self.indicators.price_change_percent(self.data['close'], 30)
        return (self.data['price_change_5d'] > 5) & \
               (price_change_30d > 15)
    
    def volume_breakout(self) -> pd.Series:
        """Strategy 9: Volume Breakout (New 20-day high + 2x volume)"""
        return self.data['new_high_20'] & \
               (self.data['volume_ratio'] > 2.0)
    
    def volatility_breakout(self) -> pd.Series:
        """Strategy 10: Volatility Breakout (Low vol + breakout)"""
        low_vol = self.data['volatility_20'] < self.data['volatility_20'].rolling(60).quantile(0.25)
        return low_vol.shift(1) & self.data['new_high_20']
    
    def range_breakout(self) -> pd.Series:
        """Strategy 11: Range Breakout (Break 60-day range)"""
        return self.data['new_high_60'] & \
               (self.data['close'] > self.data['sma_20'])
    
    def gap_up_follow_through(self) -> pd.Series:
        """Strategy 12: Gap Up + Follow Through"""
        gap = self.indicators.gap_up(self.data['open'], self.data['close'])
        follow_through = self.data['close'] > self.data['open']
        return gap & follow_through
    
    def rsi_recovery(self) -> pd.Series:
        """Strategy 13: RSI Recovery (RSI < 30 then > 50)"""
        oversold = self.data['rsi'].shift(5) < 30
        recovery = self.data['rsi'] > 50
        return oversold & recovery
    
    def macd_bullish_cross(self) -> pd.Series:
        """Strategy 14: MACD Bullish Cross"""
        bullish_cross = (self.data['macd'] > self.data['macd_signal']) & \
                       (self.data['macd'].shift(1) <= self.data['macd_signal'].shift(1))
        return bullish_cross & (self.data['macd'] < 0)  # Cross above zero line
    
    def bollinger_squeeze(self) -> pd.Series:
        """Strategy 15: Bollinger Band Squeeze"""
        bb_width = (self.data['bb_upper'] - self.data['bb_lower']) / self.data['bb_middle']
        squeeze = bb_width < bb_width.rolling(20).quantile(0.1)
        breakout = self.data['close'] > self.data['bb_upper']
        return squeeze.shift(1) & breakout
    
    def stochastic_oversold_recovery(self) -> pd.Series:
        """Strategy 16: Stochastic Oversold Recovery"""
        oversold = self.data['stoch_k'].shift(3) < 20
        recovery = (self.data['stoch_k'] > 50) & (self.data['stoch_k'] > self.data['stoch_d'])
        return oversold & recovery
    
    def pullback_entry(self) -> pd.Series:
        """Strategy 17: Pullback Entry (Up 20%, pullback 8%, resume)"""
        strong_move = self.indicators.price_change_percent(self.data['close'], 30) > 20
        pullback = self.data['price_change_10d'] < -5
        resume = self.data['price_change_5d'] > 3
        return strong_move & pullback.shift(5) & resume
    
    def cup_and_handle(self) -> pd.Series:
        """Strategy 18: Cup and Handle Pattern (simplified)"""
        # Look for U-shaped recovery + small pullback + breakout
        price_60_ago = self.data['close'].shift(60)
        price_30_ago = self.data['close'].shift(30)
        price_10_ago = self.data['close'].shift(10)
        
        cup_formation = (price_30_ago < price_60_ago * 0.9) & \
                       (price_10_ago > price_30_ago * 1.05)
        handle_breakout = self.data['close'] > price_60_ago
        return cup_formation & handle_breakout
    
    def higher_highs_lows_trend(self) -> pd.Series:
        """Strategy 19: Higher Highs/Higher Lows Trend"""
        hh, hl = self.indicators.higher_highs_lows(self.data['high'], self.data['low'])
        return hh & hl & (self.data['close'] > self.data['sma_20'])
    
    def support_resistance_breakout(self) -> pd.Series:
        """Strategy 20: Support/Resistance Breakout"""
        # Identify resistance level (multiple touches at similar price)
        resistance_level = self.data['high'].rolling(20).max()
        near_resistance = np.abs(self.data['close'] - resistance_level) / resistance_level < 0.02
        breakout = self.data['close'] > resistance_level * 1.01
        return near_resistance.shift(3) & breakout