from datetime import datetime
import logging

class RiskManager:
    """
    Enhanced risk management system integrating place_trade.py logic
    with proper validation and portfolio-level controls
    """
    
    def __init__(self, account_balance=10000, default_risk_percent=2, 
                 max_position_size=0.10, max_positions=10):
        self.account_balance = account_balance
        self.default_risk_percent = default_risk_percent
        self.max_position_size = max_position_size
        self.max_positions = max_positions
        self.active_positions = {}
        
    def validate_inputs(self, ticker, current_price, risk_percent=None, stop_loss_percent=None):
        """Validate all inputs before trade calculation"""
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
            
        if current_price <= 0:
            raise ValueError("Current price must be positive")
            
        if risk_percent is not None and (risk_percent <= 0 or risk_percent > 50):
            raise ValueError("Risk percent must be between 0 and 50")
            
        if stop_loss_percent is not None and (stop_loss_percent <= 0 or stop_loss_percent > 50):
            raise ValueError("Stop loss percent must be between 0 and 50")
    
    def calculate_trade(self, ticker, current_price, risk_percent=None, stop_loss_percent=5):
        """
        Enhanced version of place_trade.py with proper validation and portfolio checks
        """
        # Use default risk percent if not provided
        if risk_percent is None:
            risk_percent = self.default_risk_percent
            
        # Validate inputs
        self.validate_inputs(ticker, current_price, risk_percent, stop_loss_percent)
        
        # Check if we already have this position
        if ticker in self.active_positions:
            raise ValueError(f"Already have an active position in {ticker}")
            
        # Check if we're at max positions
        if len(self.active_positions) >= self.max_positions:
            raise ValueError(f"Maximum positions ({self.max_positions}) already reached")
        
        # Calculate available capital (account balance minus current position values)
        current_exposure = sum(pos['trade_value'] for pos in self.active_positions.values())
        available_capital = self.account_balance - current_exposure
        
        # Calculate capital to risk
        capital_to_risk = available_capital * (risk_percent / 100)
        
        # Calculate stop loss price
        stop_loss = current_price * (1 - stop_loss_percent / 100)
        
        # Risk per share
        risk_per_share = current_price - stop_loss
        
        if risk_per_share <= 0:
            raise ValueError("Invalid stop loss calculation - risk per share is zero or negative")
        
        # Calculate maximum position value first
        max_position_value = available_capital * self.max_position_size
        
        # Check if even 1 share exceeds position limit
        if current_price > max_position_value:
            raise ValueError(f"Stock price ${current_price:.2f} exceeds maximum position size ${max_position_value:.2f}")
        
        # Number of shares to buy (proper rounding instead of truncating)
        shares_by_risk = max(1, round(capital_to_risk / risk_per_share))
        shares_by_position_limit = max(1, int(max_position_value / current_price))
        
        # Use the smaller of the two limits
        shares = min(shares_by_risk, shares_by_position_limit)
        
        # Total trade value
        trade_value = shares * current_price
        
        # Final validation - ensure we have enough capital
        if trade_value > available_capital:
            raise ValueError(f"Insufficient capital. Need ${trade_value:.2f}, have ${available_capital:.2f}")
        
        trade_data = {
            "ticker": ticker,
            "shares": shares,
            "current_price": current_price,
            "trade_value": trade_value,
            "stop_loss": stop_loss,
            "risk_per_share": risk_per_share,
            "capital_risked": shares * risk_per_share,
            "timestamp": datetime.now(),
            "risk_percent": risk_percent,
            "stop_loss_percent": stop_loss_percent
        }
        
        logging.info(f"Trade calculated for {ticker}: {shares} shares at ${current_price:.2f}")
        logging.info(f"Trade value: ${trade_value:.2f}, Stop loss: ${stop_loss:.2f}")
        
        return trade_data
    
    def add_position(self, trade_data):
        """Add a position to active tracking"""
        ticker = trade_data["ticker"]
        self.active_positions[ticker] = trade_data
        logging.info(f"Added position: {ticker}")
    
    def remove_position(self, ticker):
        """Remove a position from active tracking"""
        if ticker in self.active_positions:
            del self.active_positions[ticker]
            logging.info(f"Removed position: {ticker}")
    
    def get_portfolio_exposure(self):
        """Get current portfolio exposure"""
        total_value = sum(pos['trade_value'] for pos in self.active_positions.values())
        exposure_percent = (total_value / self.account_balance) * 100
        return {
            'total_value': total_value,
            'exposure_percent': exposure_percent,
            'available_capital': self.account_balance - total_value,
            'active_positions': len(self.active_positions)
        }
    
    def check_stop_loss(self, ticker, current_price):
        """Check if a position should be stopped out"""
        if ticker not in self.active_positions:
            return False
            
        position = self.active_positions[ticker]
        return current_price <= position['stop_loss']
    
    def update_account_balance(self, new_balance):
        """Update account balance"""
        if new_balance <= 0:
            raise ValueError("Account balance must be positive")
        self.account_balance = new_balance