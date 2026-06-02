from datetime import datetime
import logging
from typing import Dict, List, Optional
from market_config import MAJOR_MARKETS, MarketConfig, convert_to_usd, convert_from_usd

class MultiMarketRiskManager:
    """
    Enhanced risk management system for multiple international markets
    with currency conversion and market-specific rules
    """
    
    def __init__(self, account_balance_usd=100000, default_risk_percent=2, 
                 max_position_size=0.08, max_positions_per_market=5, max_total_positions=25):
        self.account_balance_usd = account_balance_usd  # Base currency USD
        self.default_risk_percent = default_risk_percent
        self.max_position_size = max_position_size  # 8% max per position (lower for international)
        self.max_positions_per_market = max_positions_per_market
        self.max_total_positions = max_total_positions
        self.active_positions = {}  # ticker -> position_data
        self.market_configs = MAJOR_MARKETS
        
        # Track exposure by market and currency
        self.market_exposure = {market: 0.0 for market in self.market_configs.keys()}
        self.currency_exposure = {}
        
        logging.info(f"Multi-market risk manager initialized with ${account_balance_usd:,.0f} USD")
        
    def validate_inputs(self, ticker, current_price, market_code, risk_percent=None, stop_loss_percent=None):
        """Validate all inputs including market-specific rules"""
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
            
        if market_code not in self.market_configs:
            raise ValueError(f"Unknown market code: {market_code}")
            
        market_config = self.market_configs[market_code]
        
        if current_price <= 0:
            raise ValueError("Current price must be positive")
            
        # Market-specific minimum price checks
        if current_price < market_config.min_price:
            raise ValueError(f"Price ${current_price:.2f} below minimum for {market_config.name} (${market_config.min_price:.2f})")
            
        if risk_percent is not None and (risk_percent <= 0 or risk_percent > 25):  # Lower max for international
            raise ValueError("Risk percent must be between 0 and 25")
            
        if stop_loss_percent is not None and (stop_loss_percent <= 0 or stop_loss_percent > 25):
            raise ValueError("Stop loss percent must be between 0 and 25")
    
    def get_market_from_ticker(self, ticker: str) -> Optional[str]:
        """Determine market from ticker suffix"""
        for market_code, config in self.market_configs.items():
            if config.suffix and ticker.endswith(config.suffix):
                return market_code
            elif not config.suffix and '.' not in ticker:  # US stocks (no suffix)
                if market_code.startswith('US_'):
                    return market_code
        return None
    
    def calculate_available_capital_usd(self) -> float:
        """Calculate available capital in USD"""
        total_exposure_usd = 0.0
        for position in self.active_positions.values():
            # Convert position value to USD
            position_value_usd = convert_to_usd(
                position['trade_value'], 
                position['currency']
            )
            total_exposure_usd += position_value_usd
        
        return self.account_balance_usd - total_exposure_usd
    
    def check_market_limits(self, market_code: str) -> None:
        """Check if market-specific limits are exceeded"""
        positions_in_market = sum(1 for pos in self.active_positions.values() 
                                if pos['market_code'] == market_code)
        
        if positions_in_market >= self.max_positions_per_market:
            raise ValueError(f"Maximum positions in {market_code} ({self.max_positions_per_market}) already reached")
        
        if len(self.active_positions) >= self.max_total_positions:
            raise ValueError(f"Maximum total positions ({self.max_total_positions}) already reached")
    
    def calculate_trade(self, ticker: str, current_price: float, market_code: str = None, 
                       risk_percent: float = None, stop_loss_percent: float = 8):
        """
        Calculate trade with multi-market and currency considerations
        """
        # Auto-detect market if not provided
        if market_code is None:
            market_code = self.get_market_from_ticker(ticker)
            if market_code is None:
                raise ValueError(f"Cannot determine market for ticker {ticker}")
        
        # Use default risk percent if not provided
        if risk_percent is None:
            risk_percent = self.default_risk_percent
            
        # Validate inputs
        self.validate_inputs(ticker, current_price, market_code, risk_percent, stop_loss_percent)
        
        # Check if we already have this position
        if ticker in self.active_positions:
            raise ValueError(f"Already have an active position in {ticker}")
        
        # Check market limits
        self.check_market_limits(market_code)
        
        market_config = self.market_configs[market_code]
        
        # Get available capital in USD
        available_capital_usd = self.calculate_available_capital_usd()
        
        # Convert to local currency for calculation
        available_capital_local = convert_from_usd(available_capital_usd, market_config.currency)
        
        # Calculate capital to risk in local currency
        capital_to_risk_local = available_capital_local * (risk_percent / 100)
        
        # Calculate stop loss price
        stop_loss = current_price * (1 - stop_loss_percent / 100)
        
        # Risk per share in local currency
        risk_per_share = current_price - stop_loss
        
        if risk_per_share <= 0:
            raise ValueError("Invalid stop loss calculation - risk per share is zero or negative")
        
        # Calculate position size limits
        max_position_value_usd = available_capital_usd * self.max_position_size
        max_position_value_local = convert_from_usd(max_position_value_usd, market_config.currency)
        
        # Check if even 1 share exceeds position limit
        if current_price > max_position_value_local:
            raise ValueError(f"Stock price {current_price:.2f} {market_config.currency} exceeds maximum position size {max_position_value_local:.2f} {market_config.currency}")
        
        # Calculate shares by both risk and position size limits
        shares_by_risk = max(1, round(capital_to_risk_local / risk_per_share))
        shares_by_position_limit = max(1, int(max_position_value_local / current_price))
        
        # Use the smaller of the two limits
        shares = min(shares_by_risk, shares_by_position_limit)
        
        # Total trade value in local currency
        trade_value_local = shares * current_price
        
        # Convert to USD for portfolio tracking
        trade_value_usd = convert_to_usd(trade_value_local, market_config.currency)
        
        # Final validation - ensure we have enough capital
        if trade_value_usd > available_capital_usd:
            raise ValueError(f"Insufficient capital. Need ${trade_value_usd:.2f} USD, have ${available_capital_usd:.2f} USD")
        
        trade_data = {
            "ticker": ticker,
            "market_code": market_code,
            "market_name": market_config.name,
            "currency": market_config.currency,
            "shares": shares,
            "current_price": current_price,
            "trade_value": trade_value_local,  # Local currency
            "trade_value_usd": trade_value_usd,  # USD equivalent
            "stop_loss": stop_loss,
            "risk_per_share": risk_per_share,
            "capital_risked": shares * risk_per_share,
            "timestamp": datetime.now(),
            "risk_percent": risk_percent,
            "stop_loss_percent": stop_loss_percent,
            "exchange_rate": convert_to_usd(1.0, market_config.currency)  # Rate when trade was made
        }
        
        logging.info(f"Trade calculated for {ticker} ({market_config.name}): {shares} shares at {current_price:.2f} {market_config.currency}")
        logging.info(f"Trade value: {trade_value_local:.2f} {market_config.currency} (${trade_value_usd:.2f} USD)")
        
        return trade_data
    
    def add_position(self, trade_data: Dict) -> None:
        """Add a position to active tracking"""
        ticker = trade_data["ticker"]
        market_code = trade_data["market_code"]
        
        self.active_positions[ticker] = trade_data
        
        # Update market exposure
        self.market_exposure[market_code] += trade_data["trade_value_usd"]
        
        # Update currency exposure
        currency = trade_data["currency"]
        if currency not in self.currency_exposure:
            self.currency_exposure[currency] = 0.0
        self.currency_exposure[currency] += trade_data["trade_value_usd"]
        
        logging.info(f"Added position: {ticker} in {market_code}")
    
    def remove_position(self, ticker: str) -> None:
        """Remove a position from active tracking"""
        if ticker not in self.active_positions:
            return
            
        position = self.active_positions[ticker]
        market_code = position["market_code"]
        currency = position["currency"]
        
        # Update exposures
        self.market_exposure[market_code] -= position["trade_value_usd"]
        self.currency_exposure[currency] -= position["trade_value_usd"]
        
        # Clean up zero exposures
        if self.currency_exposure[currency] <= 0:
            del self.currency_exposure[currency]
        
        del self.active_positions[ticker]
        logging.info(f"Removed position: {ticker}")
    
    def get_portfolio_exposure(self) -> Dict:
        """Get comprehensive portfolio exposure breakdown"""
        total_value_usd = sum(pos['trade_value_usd'] for pos in self.active_positions.values())
        exposure_percent = (total_value_usd / self.account_balance_usd) * 100
        
        # Market breakdown
        market_breakdown = {}
        for market, exposure in self.market_exposure.items():
            if exposure > 0:
                market_breakdown[market] = {
                    'exposure_usd': exposure,
                    'percentage': (exposure / self.account_balance_usd) * 100,
                    'positions': sum(1 for pos in self.active_positions.values() 
                                   if pos['market_code'] == market)
                }
        
        # Currency breakdown
        currency_breakdown = {}
        for currency, exposure in self.currency_exposure.items():
            currency_breakdown[currency] = {
                'exposure_usd': exposure,
                'percentage': (exposure / self.account_balance_usd) * 100
            }
        
        return {
            'total_value_usd': total_value_usd,
            'exposure_percent': exposure_percent,
            'available_capital_usd': self.calculate_available_capital_usd(),
            'active_positions': len(self.active_positions),
            'market_breakdown': market_breakdown,
            'currency_breakdown': currency_breakdown,
            'max_positions_per_market': self.max_positions_per_market,
            'max_total_positions': self.max_total_positions
        }
    
    def check_stop_loss(self, ticker: str, current_price: float) -> bool:
        """Check if a position should be stopped out with currency consideration"""
        if ticker not in self.active_positions:
            return False
            
        position = self.active_positions[ticker]
        return current_price <= position['stop_loss']
    
    def update_account_balance(self, new_balance_usd: float) -> None:
        """Update account balance in USD"""
        if new_balance_usd <= 0:
            raise ValueError("Account balance must be positive")
        self.account_balance_usd = new_balance_usd
    
    def get_positions_by_market(self, market_code: str) -> List[Dict]:
        """Get all positions in a specific market"""
        return [pos for pos in self.active_positions.values() 
                if pos['market_code'] == market_code]
    
    def get_currency_risk_summary(self) -> Dict:
        """Get currency risk exposure summary"""
        total_exposure = sum(self.currency_exposure.values())
        
        currency_risk = {}
        for currency, exposure in self.currency_exposure.items():
            currency_risk[currency] = {
                'exposure_usd': exposure,
                'percentage_of_portfolio': (exposure / self.account_balance_usd) * 100,
                'percentage_of_positions': (exposure / total_exposure) * 100 if total_exposure > 0 else 0
            }
        
        return {
            'total_foreign_exposure': total_exposure,
            'foreign_exposure_percentage': (total_exposure / self.account_balance_usd) * 100,
            'currency_breakdown': currency_risk,
            'number_of_currencies': len(self.currency_exposure)
        }