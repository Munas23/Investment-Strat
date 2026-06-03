"""
Global Momentum Strategy
Works across all markets: ASX300, S&P500, Russell2000, FTSE, DAX
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

class GlobalMomentumStrategy(BaseStrategy):
    """
    Multi-market momentum strategy that identifies stocks with strong price momentum
    and favorable technical indicators across global markets
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        # Momentum Parameters
        self.momentum_period = 20           # Period for momentum calculation
        self.momentum_threshold = 0.05      # 5% minimum momentum required
        self.volume_period = 20             # Period for volume analysis
        self.volume_threshold = 1.2         # 20% above average volume required
        
        # Technical Indicators
        self.rsi_period = 14               # RSI period
        self.rsi_oversold = 30             # RSI oversold level
        self.rsi_overbought = 70           # RSI overbought level
        self.ma_short = 10                 # Short MA period
        self.ma_long = 50                  # Long MA period
        
        # Risk Management
        self.stop_loss_pct = 0.08          # 8% stop loss
        self.take_profit_pct = 0.25        # 25% take profit
        self.trail_stop_pct = 0.12         # 12% trailing stop
        
        # Position Management
        self.max_sector_exposure = 0.30    # Max 30% in any sector
        self.rebalance_frequency = 5       # Rebalance every 5 days
        
        self.logger.info(f"Initialized {self.name} with momentum threshold: {self.momentum_threshold:.1%}")
        self.logger.info(f"RSI range: {self.rsi_oversold}-{self.rsi_overbought}")
        self.logger.info(f"MA periods: {self.ma_short}/{self.ma_long}")
    
    def calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """Calculate comprehensive momentum score for a stock"""
        if len(data) < max(self.momentum_period, self.ma_long, self.rsi_period):
            return 0.0
        
        try:
            current_price = data['close'].iloc[-1]
            
            # 1. Price momentum (primary factor)
            price_momentum = (current_price / data['close'].iloc[-self.momentum_period] - 1)
            
            # 2. Moving average alignment
            ma_short = data['close'].rolling(self.ma_short).mean().iloc[-1]
            ma_long = data['close'].rolling(self.ma_long).mean().iloc[-1]
            
            ma_alignment = 1.0 if current_price > ma_short > ma_long else 0.0
            
            # 3. RSI momentum (not oversold, not extremely overbought)
            rsi = talib.RSI(data['close'].values, timeperiod=self.rsi_period)[-1]
            rsi_score = 1.0 if self.rsi_oversold < rsi < 85 else 0.0
            
            # 4. Volume confirmation
            avg_volume = data['volume'].rolling(self.volume_period).mean().iloc[-1]
            current_volume = data['volume'].iloc[-1]
            volume_score = 1.0 if current_volume > avg_volume * self.volume_threshold else 0.5
            
            # 5. Recent strength (last 5 days)
            recent_strength = (current_price / data['close'].iloc[-5] - 1) if len(data) >= 5 else 0
            recent_score = max(0, recent_strength * 10)  # Scale recent strength
            
            # 6. Volatility check (prefer moderate volatility)
            returns = data['close'].pct_change().dropna()
            if len(returns) >= 20:
                volatility = returns.rolling(20).std().iloc[-1]
                vol_score = 1.0 if 0.01 < volatility < 0.05 else 0.5  # 1-5% daily vol preferred
            else:
                vol_score = 0.5
            
            # Combine scores with weights
            momentum_score = (
                price_momentum * 0.40 +      # 40% weight on price momentum
                ma_alignment * 0.20 +        # 20% weight on MA alignment
                rsi_score * 0.15 +           # 15% weight on RSI
                volume_score * 0.10 +        # 10% weight on volume
                recent_score * 0.10 +        # 10% weight on recent strength
                vol_score * 0.05             # 5% weight on volatility
            )
            
            return momentum_score
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum score: {e}")
            return 0.0
    
    def generate_signals(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on momentum analysis"""
        if len(data) < max(self.momentum_period, self.ma_long, self.rsi_period):
            return {'action': 'hold', 'confidence': 0.0, 'reason': 'Insufficient data'}
        
        try:
            current_price = data['close'].iloc[-1]
            
            # Calculate momentum score
            momentum_score = self.calculate_momentum_score(data)
            
            # Calculate individual indicators for decision making
            price_momentum = (current_price / data['close'].iloc[-self.momentum_period] - 1)
            
            # RSI for overbought/oversold
            rsi = talib.RSI(data['close'].values, timeperiod=self.rsi_period)[-1]
            
            # Moving averages
            ma_short = data['close'].rolling(self.ma_short).mean().iloc[-1]
            ma_long = data['close'].rolling(self.ma_long).mean().iloc[-1]
            
            # Volume analysis
            avg_volume = data['volume'].rolling(self.volume_period).mean().iloc[-1]
            current_volume = data['volume'].iloc[-1]
            
            # BUY SIGNAL
            if (momentum_score > 0.6 and                    # Strong momentum score
                price_momentum > self.momentum_threshold and # Strong price momentum
                current_price > ma_short > ma_long and      # MA alignment
                rsi > self.rsi_oversold and rsi < 80 and    # RSI in good range
                current_volume > avg_volume * self.volume_threshold):  # Volume confirmation
                
                confidence = min(momentum_score, 1.0)
                reason = f"Strong momentum: {price_momentum:.1%}, RSI: {rsi:.1f}, Score: {momentum_score:.2f}"
                
                return {
                    'action': 'buy',
                    'confidence': confidence,
                    'reason': reason,
                    'momentum_score': momentum_score,
                    'price_momentum': price_momentum,
                    'rsi': rsi
                }
            
            # SELL SIGNAL (for existing positions)
            elif (momentum_score < 0.3 or                   # Weakening momentum
                  price_momentum < -0.02 or                 # Negative momentum
                  current_price < ma_short or               # Below short MA
                  rsi > self.rsi_overbought):               # Overbought
                
                reason = f"Momentum weakening: {price_momentum:.1%}, RSI: {rsi:.1f}, Score: {momentum_score:.2f}"
                
                return {
                    'action': 'sell',
                    'confidence': 0.8,
                    'reason': reason,
                    'momentum_score': momentum_score,
                    'price_momentum': price_momentum,
                    'rsi': rsi
                }
            
            # HOLD
            else:
                return {
                    'action': 'hold',
                    'confidence': momentum_score,
                    'reason': f"Neutral: momentum {price_momentum:.1%}, RSI {rsi:.1f}",
                    'momentum_score': momentum_score,
                    'price_momentum': price_momentum,
                    'rsi': rsi
                }
                
        except Exception as e:
            self.logger.error(f"Error generating signals for {symbol}: {e}")
            return {'action': 'hold', 'confidence': 0.0, 'reason': f'Error: {e}'}
    
    def get_stop_loss_percent(self, symbol: str) -> float:
        """Get stop loss percentage - can be customized per symbol/market"""
        return self.stop_loss_pct
    
    def calculate_position_size(self, symbol: str, price: float, signal_confidence: float = 1.0) -> int:
        """Enhanced position sizing based on momentum confidence"""
        base_size = super().calculate_position_size(symbol, price, signal_confidence)
        
        # Adjust size based on confidence
        if signal_confidence > 0.8:
            adjusted_size = int(base_size * 1.2)  # Increase size for high confidence
        elif signal_confidence < 0.6:
            adjusted_size = int(base_size * 0.8)  # Decrease size for low confidence
        else:
            adjusted_size = base_size
        
        return adjusted_size
    
    def check_exits(self):
        """Enhanced exit checking with trailing stops"""
        positions_to_exit = []
        
        for symbol, position in self.positions.items():
            if symbol not in self.market_data:
                continue
            
            current_price = self.market_data[symbol]['close'].iloc[-1]
            entry_price = position['entry_price']
            
            # Calculate current P&L
            current_pnl = (current_price / entry_price - 1)
            
            # 1. Stop loss check
            if current_price <= position['stop_loss']:
                positions_to_exit.append((symbol, current_price, "Stop loss"))
                continue
            
            # 2. Take profit check
            if current_pnl >= self.take_profit_pct:
                positions_to_exit.append((symbol, current_price, "Take profit"))
                continue
            
            # 3. Trailing stop (if position is profitable)
            if current_pnl > 0.1:  # Only trail if 10%+ profit
                # Update trailing stop
                trail_price = current_price * (1 - self.trail_stop_pct)
                if trail_price > position['stop_loss']:
                    position['stop_loss'] = trail_price
                    self.logger.info(f"Updated trailing stop for {symbol}: ${trail_price:.2f}")
            
            # 4. Signal-based exit
            signal = self.generate_signals(symbol, self.market_data[symbol])
            if signal['action'] == 'sell' and signal['confidence'] > 0.7:
                positions_to_exit.append((symbol, current_price, signal['reason']))
        
        # Execute exits
        for symbol, price, reason in positions_to_exit:
            self.exit_position(symbol, price, reason)

# Example usage and testing
if __name__ == "__main__":
    # Create strategy instance
    strategy = GlobalMomentumStrategy(
        name="Global_Momentum_Strategy",
        config_path="../config/strategy_config.json"
    )
    
    print(f"Strategy: {strategy.name}")
    print("Strategy initialized successfully!")
    print(f"Momentum threshold: {strategy.momentum_threshold:.1%}")
    print(f"Risk per trade: {strategy.risk_per_trade:.1%}")
    print(f"Max positions: {strategy.max_positions}")