"""
Global Breakout Strategy
Identifies breakout patterns across ASX300, S&P500, Russell2000, FTSE, DAX markets
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, Any
import sys
import os

# Add parent directory to path to import base strategy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.base_strategy import BaseStrategy

class GlobalBreakoutStrategy(BaseStrategy):
    """
    Multi-market breakout strategy that identifies stocks breaking out from 
    consolidation patterns with volume confirmation
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        # Breakout Parameters
        self.lookback_period = 20          # Period to find highs/lows
        self.consolidation_period = 10     # Period for consolidation check
        self.min_consolidation_days = 5    # Minimum consolidation days
        self.max_consolidation_depth = 0.15 # Max 15% depth in consolidation
        
        # Volume Parameters  
        self.volume_period = 20            # Volume average period
        self.volume_surge_threshold = 1.5  # 50% above average volume
        self.volume_trend_period = 5       # Recent volume trend period
        
        # Technical Filters
        self.atr_period = 14               # ATR period
        self.atr_threshold = 0.03          # Min 3% daily ATR
        self.ma_filter_period = 50         # MA trend filter
        self.rsi_period = 14               # RSI period
        
        # Risk Management
        self.stop_loss_atr_multiple = 2.0  # Stop loss = 2x ATR
        self.min_stop_loss = 0.05          # Minimum 5% stop loss
        self.max_stop_loss = 0.12          # Maximum 12% stop loss
        
        # Pattern Recognition
        self.min_price = 1.0               # Minimum stock price
        self.min_volume = 100000           # Minimum daily volume
        
        self.logger.info(f"Initialized {self.name}")
        self.logger.info(f"Lookback period: {self.lookback_period} days")
        self.logger.info(f"Volume surge threshold: {self.volume_surge_threshold}x")
        self.logger.info(f"ATR-based stops: {self.stop_loss_atr_multiple}x ATR")
    
    def is_in_consolidation(self, data: pd.DataFrame) -> tuple[bool, float, float]:
        """
        Check if stock is in consolidation pattern
        Returns: (is_consolidating, consolidation_depth, resistance_level)
        """
        if len(data) < self.consolidation_period:
            return False, 0.0, 0.0
        
        try:
            # Get recent data for consolidation analysis
            recent_data = data.tail(self.consolidation_period)
            
            # Find high and low in consolidation period
            high_price = recent_data['high'].max()
            low_price = recent_data['low'].min()
            
            if high_price <= 0:
                return False, 0.0, 0.0
            
            # Calculate consolidation depth
            depth = (high_price - low_price) / high_price
            
            # Check if consolidation is tight enough
            is_tight = depth <= self.max_consolidation_depth
            
            # Check if price has been near highs recently
            current_price = data['close'].iloc[-1]
            near_highs = current_price >= high_price * 0.90  # Within 10% of highs
            
            # Check for sideways movement (price not trending strongly)
            price_change = (current_price / recent_data['close'].iloc[0] - 1)
            is_sideways = abs(price_change) < 0.10  # Less than 10% move overall
            
            is_consolidating = is_tight and near_highs and is_sideways
            
            return is_consolidating, depth, high_price
            
        except Exception as e:
            self.logger.error(f"Error checking consolidation: {e}")
            return False, 0.0, 0.0
    
    def check_volume_breakout(self, data: pd.DataFrame) -> tuple[bool, float]:
        """
        Check for volume breakout confirmation
        Returns: (has_volume_breakout, volume_ratio)
        """
        if len(data) < self.volume_period:
            return False, 0.0
        
        try:
            # Current volume
            current_volume = data['volume'].iloc[-1]
            
            # Average volume over period
            avg_volume = data['volume'].rolling(self.volume_period).mean().iloc[-1]
            
            # Volume ratio
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Check for volume surge
            has_surge = volume_ratio >= self.volume_surge_threshold
            
            # Check minimum volume requirement
            meets_min_volume = current_volume >= self.min_volume
            
            return has_surge and meets_min_volume, volume_ratio
            
        except Exception as e:
            self.logger.error(f"Error checking volume breakout: {e}")
            return False, 0.0
    
    def calculate_atr_stop(self, data: pd.DataFrame, entry_price: float) -> float:
        """Calculate ATR-based stop loss"""
        if len(data) < self.atr_period:
            return entry_price * (1 - self.min_stop_loss)
        
        try:
            # Calculate ATR
            atr = talib.ATR(
                data['high'].values,
                data['low'].values, 
                data['close'].values,
                timeperiod=self.atr_period
            )[-1]
            
            # ATR-based stop
            atr_stop_distance = atr * self.stop_loss_atr_multiple
            atr_stop_pct = atr_stop_distance / entry_price
            
            # Apply min/max constraints
            stop_pct = max(self.min_stop_loss, min(self.max_stop_loss, atr_stop_pct))
            
            return entry_price * (1 - stop_pct)
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR stop: {e}")
            return entry_price * (1 - self.min_stop_loss)
    
    def check_technical_filters(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check various technical filters"""
        if len(data) < max(self.ma_filter_period, self.rsi_period):
            return {'passed': False, 'reason': 'Insufficient data'}
        
        try:
            current_price = data['close'].iloc[-1]
            
            # 1. Price filter
            if current_price < self.min_price:
                return {'passed': False, 'reason': f'Price too low: ${current_price:.2f}'}
            
            # 2. ATR filter (sufficient volatility)
            atr = talib.ATR(
                data['high'].values,
                data['low'].values,
                data['close'].values,
                timeperiod=self.atr_period
            )[-1]
            
            atr_pct = atr / current_price
            if atr_pct < self.atr_threshold:
                return {'passed': False, 'reason': f'Low volatility: {atr_pct:.1%}'}
            
            # 3. Moving average trend filter
            ma_50 = data['close'].rolling(self.ma_filter_period).mean().iloc[-1]
            above_ma = current_price > ma_50
            
            # 4. RSI filter (not extremely overbought)
            rsi = talib.RSI(data['close'].values, timeperiod=self.rsi_period)[-1]
            rsi_ok = rsi < 85  # Not extremely overbought
            
            # 5. Recent momentum (last 5 days positive)
            if len(data) >= 5:
                recent_momentum = (current_price / data['close'].iloc[-5] - 1)
                momentum_ok = recent_momentum > -0.05  # Not falling fast
            else:
                momentum_ok = True
            
            all_passed = above_ma and rsi_ok and momentum_ok
            
            return {
                'passed': all_passed,
                'above_ma': above_ma,
                'rsi': rsi,
                'rsi_ok': rsi_ok,
                'recent_momentum': recent_momentum if len(data) >= 5 else 0,
                'momentum_ok': momentum_ok,
                'atr_pct': atr_pct
            }
            
        except Exception as e:
            self.logger.error(f"Error checking technical filters: {e}")
            return {'passed': False, 'reason': f'Error: {e}'}
    
    def generate_signals(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate breakout trading signals"""
        if len(data) < max(self.lookback_period, self.ma_filter_period):
            return {'action': 'hold', 'confidence': 0.0, 'reason': 'Insufficient data'}
        
        try:
            current_price = data['close'].iloc[-1]
            current_high = data['high'].iloc[-1]
            
            # 1. Check if in consolidation
            is_consolidating, depth, resistance = self.is_in_consolidation(data)
            
            # 2. Check for price breakout
            lookback_high = data['high'].rolling(self.lookback_period).max().iloc[-2]  # Exclude today
            price_breakout = current_high > lookback_high
            
            # 3. Check volume confirmation
            has_volume_breakout, volume_ratio = self.check_volume_breakout(data)
            
            # 4. Check technical filters
            tech_filters = self.check_technical_filters(data)
            
            # BUY SIGNAL - All conditions must be met
            if (price_breakout and                    # Price breakout
                has_volume_breakout and               # Volume confirmation  
                tech_filters['passed'] and            # Technical filters
                (is_consolidating or depth < 0.20)):  # Consolidation or reasonable depth
                
                # Calculate confidence based on multiple factors
                confidence = 0.5  # Base confidence
                
                # Boost confidence for tight consolidation
                if is_consolidating and depth < 0.10:
                    confidence += 0.2
                
                # Boost for strong volume
                if volume_ratio > 2.0:
                    confidence += 0.15
                
                # Boost for good RSI
                if 50 < tech_filters.get('rsi', 50) < 75:
                    confidence += 0.1
                
                # Boost for momentum
                if tech_filters.get('recent_momentum', 0) > 0.02:
                    confidence += 0.05
                
                confidence = min(confidence, 1.0)
                
                reason = (f"Breakout: Price>${lookback_high:.2f}, Vol:{volume_ratio:.1f}x, "
                         f"Consol:{depth:.1%}, RSI:{tech_filters.get('rsi', 0):.0f}")
                
                return {
                    'action': 'buy',
                    'confidence': confidence,
                    'reason': reason,
                    'breakout_level': lookback_high,
                    'volume_ratio': volume_ratio,
                    'consolidation_depth': depth,
                    'resistance_level': resistance
                }
            
            # SELL SIGNAL (for existing positions)
            elif current_price < data['close'].rolling(10).mean().iloc[-1]:  # Below 10-day MA
                return {
                    'action': 'sell',
                    'confidence': 0.8,
                    'reason': 'Below 10-day moving average',
                    'current_price': current_price
                }
            
            # HOLD
            else:
                hold_reason = []
                if not price_breakout:
                    hold_reason.append("No price breakout")
                if not has_volume_breakout:
                    hold_reason.append(f"Low volume ({volume_ratio:.1f}x)")
                if not tech_filters['passed']:
                    hold_reason.append(tech_filters.get('reason', 'Tech filters failed'))
                
                return {
                    'action': 'hold',
                    'confidence': 0.0,
                    'reason': '; '.join(hold_reason) if hold_reason else 'Waiting for setup',
                    'volume_ratio': volume_ratio,
                    'consolidation_depth': depth
                }
                
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            return {'action': 'hold', 'confidence': 0.0, 'reason': f'Error: {e}'}
    
    def get_stop_loss_percent(self, symbol: str) -> float:
        """Get stop loss percentage using ATR method"""
        if symbol in self.market_data:
            data = self.market_data[symbol]
            entry_price = data['close'].iloc[-1]
            atr_stop = self.calculate_atr_stop(data, entry_price)
            stop_pct = (entry_price - atr_stop) / entry_price
            return stop_pct
        return self.min_stop_loss
    
    def enter_position(self, symbol: str, price: float, shares: int, signal_info: Dict):
        """Enhanced position entry with ATR-based stops"""
        if shares <= 0:
            return False
        
        # Calculate ATR-based stop loss
        if symbol in self.market_data:
            atr_stop = self.calculate_atr_stop(self.market_data[symbol], price)
        else:
            atr_stop = price * (1 - self.min_stop_loss)
        
        cost = shares * price * (1 + self.commission)
        
        if cost > self.cash:
            return False
        
        # Update cash and positions
        self.cash -= cost
        
        self.positions[symbol] = {
            'shares': shares,
            'entry_price': price,
            'entry_date': self.current_date,
            'entry_value': shares * price,
            'stop_loss': atr_stop,
            'signal_info': signal_info,
            'atr_stop': True  # Flag for ATR-based stop
        }
        
        # Record trade
        trade = {
            'symbol': symbol,
            'action': 'buy',
            'date': self.current_date,
            'price': price,
            'shares': shares,
            'value': shares * price,
            'commission': shares * price * self.commission,
            'stop_loss': atr_stop,
            'stop_pct': (price - atr_stop) / price * 100,
            'reason': signal_info.get('reason', 'Breakout signal'),
            'confidence': signal_info.get('confidence', 1.0),
            'volume_ratio': signal_info.get('volume_ratio', 0),
            'breakout_level': signal_info.get('breakout_level', price)
        }
        self.trades.append(trade)
        
        self.logger.info(f"ENTER: {symbol} - {shares} shares @ ${price:.2f} | Stop: ${atr_stop:.2f} | {signal_info.get('reason', '')}")
        return True

# Example usage
if __name__ == "__main__":
    # Create strategy instance
    strategy = GlobalBreakoutStrategy(
        name="Global_Breakout_Strategy",
        config_path="../config/strategy_config.json"
    )
    
    print(f"Strategy: {strategy.name}")
    print("Strategy initialized successfully!")
    print(f"Lookback period: {strategy.lookback_period} days")
    print(f"Volume threshold: {strategy.volume_surge_threshold}x")
    print(f"ATR stop multiple: {strategy.stop_loss_atr_multiple}x")