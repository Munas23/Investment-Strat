"""
Universal Strategy Framework for Global Multi-Market Backtesting
Supports ASX300, S&P500, Russell2000, FTSE, DAX markets
"""

import pandas as pd
import numpy as np
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional, Any

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    Provides common functionality for multi-market trading
    """
    
    def __init__(self, name: str, config_path: str = None):
        self.name = name
        self.config = self._load_config(config_path)
        self.positions = {}  # {symbol: position_info}
        self.trades = []
        self.portfolio_value = []
        self.current_date = None
        self.market_data = {}
        
        # Initialize from config
        self.initial_capital = self.config.get('initial_capital', 100000)
        self.cash = self.initial_capital
        self.commission = self.config.get('commission', 0.001)
        self.max_positions = self.config.get('max_positions', 20)
        self.risk_per_trade = self.config.get('risk_per_trade', 0.02)
        
        # Setup logging
        self.logger = self._setup_logging()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load strategy configuration"""
        if config_path:
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Setup strategy logging"""
        logger = logging.getLogger(f"{self.name}_strategy")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    def initialize(self):
        """Initialize strategy parameters - must be implemented by subclass"""
        pass
    
    @abstractmethod
    def generate_signals(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signals for a symbol
        Returns: {'action': 'buy'/'sell'/'hold', 'confidence': float, 'reason': str}
        """
        pass
    
    def calculate_position_size(self, symbol: str, price: float, signal_confidence: float = 1.0) -> int:
        """Calculate position size based on risk management"""
        try:
            # Get current portfolio value
            portfolio_value = self.get_portfolio_value()
            
            # Risk-based position sizing
            risk_amount = portfolio_value * self.risk_per_trade * signal_confidence
            
            # Estimate stop loss (can be overridden by strategy)
            stop_loss_pct = self.get_stop_loss_percent(symbol)
            risk_per_share = price * stop_loss_pct
            
            if risk_per_share <= 0:
                return 0
            
            # Calculate shares based on risk
            shares = int(risk_amount / risk_per_share)
            
            # Apply position limits
            max_position_value = portfolio_value * self.config.get('max_position_size', 0.10)
            max_shares_by_position = int(max_position_value / price)
            max_shares_by_cash = int(self.cash / price)
            
            final_shares = min(shares, max_shares_by_position, max_shares_by_cash)
            return max(final_shares, 0)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def get_stop_loss_percent(self, symbol: str) -> float:
        """Get stop loss percentage for symbol (can be overridden)"""
        return 0.08  # Default 8% stop loss
    
    def enter_position(self, symbol: str, price: float, shares: int, signal_info: Dict):
        """Enter a new position"""
        if shares <= 0:
            return False
        
        cost = shares * price * (1 + self.commission)
        
        if cost > self.cash:
            self.logger.warning(f"Insufficient cash for {symbol}: need ${cost:.2f}, have ${self.cash:.2f}")
            return False
        
        # Update cash and positions
        self.cash -= cost
        
        self.positions[symbol] = {
            'shares': shares,
            'entry_price': price,
            'entry_date': self.current_date,
            'entry_value': shares * price,
            'stop_loss': price * (1 - self.get_stop_loss_percent(symbol)),
            'signal_info': signal_info
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
            'reason': signal_info.get('reason', 'Signal generated'),
            'confidence': signal_info.get('confidence', 1.0)
        }
        self.trades.append(trade)
        
        self.logger.info(f"ENTER: {symbol} - {shares} shares @ ${price:.2f} | {signal_info.get('reason', '')}")
        return True
    
    def exit_position(self, symbol: str, price: float, reason: str = "Exit signal"):
        """Exit an existing position"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        shares = position['shares']
        proceeds = shares * price * (1 - self.commission)
        
        # Update cash
        self.cash += proceeds
        
        # Calculate P&L
        entry_value = position['entry_value']
        pnl = proceeds - entry_value
        pnl_pct = (price / position['entry_price'] - 1) * 100
        
        # Record trade
        trade = {
            'symbol': symbol,
            'action': 'sell',
            'date': self.current_date,
            'price': price,
            'shares': shares,
            'value': shares * price,
            'commission': shares * price * self.commission,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'hold_days': (self.current_date - position['entry_date']).days,
            'reason': reason
        }
        self.trades.append(trade)
        
        # Remove position
        del self.positions[symbol]
        
        self.logger.info(f"EXIT: {symbol} - {shares} shares @ ${price:.2f} | P&L: {pnl_pct:.1f}% | {reason}")
        return True
    
    def get_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            if symbol in self.market_data:
                current_price = self.market_data[symbol]['close'].iloc[-1]
                total_value += position['shares'] * current_price
        
        return total_value
    
    def check_exits(self):
        """Check exit conditions for all positions"""
        positions_to_exit = []
        
        for symbol, position in self.positions.items():
            if symbol not in self.market_data:
                continue
            
            current_price = self.market_data[symbol]['close'].iloc[-1]
            
            # Stop loss check
            if current_price <= position['stop_loss']:
                positions_to_exit.append((symbol, current_price, "Stop loss"))
                continue
            
            # Strategy-specific exit signal
            signal = self.generate_signals(symbol, self.market_data[symbol])
            if signal['action'] == 'sell':
                positions_to_exit.append((symbol, current_price, signal['reason']))
        
        # Execute exits
        for symbol, price, reason in positions_to_exit:
            self.exit_position(symbol, price, reason)
    
    def scan_for_entries(self, market_symbols: List[str]):
        """Scan for new entry opportunities"""
        if len(self.positions) >= self.max_positions:
            return
        
        candidates = []
        
        for symbol in market_symbols:
            # Skip if already holding
            if symbol in self.positions:
                continue
            
            # Skip if no data
            if symbol not in self.market_data:
                continue
            
            # Generate signal
            signal = self.generate_signals(symbol, self.market_data[symbol])
            
            if signal['action'] == 'buy':
                current_price = self.market_data[symbol]['close'].iloc[-1]
                candidates.append((symbol, current_price, signal))
        
        # Sort by confidence and enter best opportunities
        candidates.sort(key=lambda x: x[2]['confidence'], reverse=True)
        
        entries_made = 0
        max_entries_per_day = 3
        
        for symbol, price, signal in candidates:
            if entries_made >= max_entries_per_day:
                break
            
            if len(self.positions) >= self.max_positions:
                break
            
            shares = self.calculate_position_size(symbol, price, signal['confidence'])
            
            if self.enter_position(symbol, price, shares, signal):
                entries_made += 1
    
    def update_market_data(self, symbol: str, data: pd.DataFrame):
        """Update market data for a symbol"""
        self.market_data[symbol] = data
    
    def process_day(self, date: datetime, market_symbols: List[str]):
        """Process a single trading day"""
        self.current_date = date
        
        # Record portfolio value
        portfolio_value = self.get_portfolio_value()
        self.portfolio_value.append({
            'date': date,
            'value': portfolio_value,
            'cash': self.cash,
            'positions': len(self.positions)
        })
        
        # Check exits first
        self.check_exits()
        
        # Look for new entries
        self.scan_for_entries(market_symbols)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        if not self.portfolio_value:
            return {}
        
        df = pd.DataFrame(self.portfolio_value)
        df.set_index('date', inplace=True)
        
        # Calculate returns
        returns = df['value'].pct_change().dropna()
        
        # Basic stats
        total_return = (df['value'].iloc[-1] / self.initial_capital - 1) * 100
        annualized_return = ((df['value'].iloc[-1] / self.initial_capital) ** (252/len(df)) - 1) * 100
        
        # Risk metrics
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annualized_return / 100) / (volatility / 100) if volatility > 0 else 0
        
        # Drawdown
        rolling_max = df['value'].expanding().max()
        drawdown = (df['value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Trade stats
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            buy_trades = trades_df[trades_df['action'] == 'buy']
            sell_trades = trades_df[trades_df['action'] == 'sell']
            
            num_trades = len(sell_trades)
            win_rate = (sell_trades['pnl_pct'] > 0).mean() * 100 if num_trades > 0 else 0
            avg_win = sell_trades[sell_trades['pnl_pct'] > 0]['pnl_pct'].mean() if num_trades > 0 else 0
            avg_loss = sell_trades[sell_trades['pnl_pct'] < 0]['pnl_pct'].mean() if num_trades > 0 else 0
        else:
            num_trades = win_rate = avg_win = avg_loss = 0
        
        return {
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'volatility_pct': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'num_trades': num_trades,
            'win_rate_pct': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'final_value': df['value'].iloc[-1],
            'cash': self.cash,
            'active_positions': len(self.positions)
        }
    
    def export_results(self, output_dir: str):
        """Export strategy results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export trades
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_file = f"{output_dir}/{self.name}_trades_{timestamp}.csv"
            trades_df.to_csv(trades_file, index=False)
            self.logger.info(f"Trades exported to {trades_file}")
        
        # Export portfolio value
        if self.portfolio_value:
            portfolio_df = pd.DataFrame(self.portfolio_value)
            portfolio_file = f"{output_dir}/{self.name}_portfolio_{timestamp}.csv"
            portfolio_df.to_csv(portfolio_file, index=False)
            self.logger.info(f"Portfolio data exported to {portfolio_file}")
        
        # Export performance stats
        stats = self.get_performance_stats()
        stats_file = f"{output_dir}/{self.name}_stats_{timestamp}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        self.logger.info(f"Performance stats exported to {stats_file}")