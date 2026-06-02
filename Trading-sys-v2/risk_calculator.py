"""
Risk-Based Position Sizing Calculator
Professional risk management for trading strategies
"""

def calculate_trade(ticker, current_price, account_balance=10000, risk_percent=2, stop_loss_percent=5):
    """
    Calculate optimal position size based on risk management principles
    
    Parameters:
    - ticker: Stock symbol
    - current_price: Current stock price
    - account_balance: Total account value
    - risk_percent: Percentage of account to risk (default 2%)
    - stop_loss_percent: Percentage below current price for stop loss (default 5%)
    
    Returns:
    - Dictionary with trade details
    """
    # Calculate capital to risk
    capital_to_risk = account_balance * (risk_percent / 100)
    
    # Calculate stop loss price
    stop_loss = current_price * (1 - stop_loss_percent / 100)
    
    # Risk per share
    risk_per_share = current_price - stop_loss
    
    # Number of shares to buy (rounded down to nearest whole share)
    shares = int(capital_to_risk / risk_per_share) if risk_per_share > 0 else 0
    
    # Total trade value
    trade_value = shares * current_price
    
    # Calculate actual risk percentage
    actual_risk_amount = shares * risk_per_share
    actual_risk_percent = (actual_risk_amount / account_balance) * 100
    
    print(f"Trade Analysis for {ticker}:")
    print(f"  Shares to buy: {shares} at ${current_price:.2f}")
    print(f"  Trade value: ${trade_value:.2f} ({(trade_value/account_balance)*100:.1f}% of account)")
    print(f"  Stop loss: ${stop_loss:.2f} ({stop_loss_percent}% below entry)")
    print(f"  Risk per share: ${risk_per_share:.2f}")
    print(f"  Total risk: ${actual_risk_amount:.2f} ({actual_risk_percent:.2f}% of account)")
    print(f"  Reward/Risk ratio potential: {((current_price * 0.10) / risk_per_share):.2f}:1 (assuming 10% gain)")
    print("-" * 50)

    return {
        "ticker": ticker,
        "shares": shares,
        "current_price": current_price,
        "trade_value": trade_value,
        "stop_loss": stop_loss,
        "risk_per_share": risk_per_share,
        "total_risk": actual_risk_amount,
        "risk_percent": actual_risk_percent,
        "position_percent": (trade_value/account_balance)*100
    }

def calculate_multiple_trades(trades_list, account_balance=10000, risk_percent=2):
    """
    Calculate position sizes for multiple potential trades
    
    Parameters:
    - trades_list: List of tuples (ticker, price, stop_loss_percent)
    - account_balance: Total account value
    - risk_percent: Percentage of account to risk per trade
    
    Returns:
    - List of trade dictionaries
    """
    results = []
    total_exposure = 0
    total_risk = 0
    
    print(f"Portfolio Analysis - Account Balance: ${account_balance:,.2f}")
    print(f"Risk per trade: {risk_percent}%")
    print("=" * 60)
    
    for ticker, price, stop_loss_pct in trades_list:
        trade = calculate_trade(ticker, price, account_balance, risk_percent, stop_loss_pct)
        results.append(trade)
        total_exposure += trade['trade_value']
        total_risk += trade['total_risk']
    
    print(f"PORTFOLIO SUMMARY:")
    print(f"  Total positions: {len(results)}")
    print(f"  Total exposure: ${total_exposure:.2f} ({(total_exposure/account_balance)*100:.1f}% of account)")
    print(f"  Total risk: ${total_risk:.2f} ({(total_risk/account_balance)*100:.1f}% of account)")
    print(f"  Cash remaining: ${account_balance - total_exposure:.2f}")
    print("=" * 60)
    
    return results

def optimize_portfolio_risk(trades_list, account_balance=10000, max_portfolio_risk=10):
    """
    Optimize position sizes to stay within maximum portfolio risk
    
    Parameters:
    - trades_list: List of tuples (ticker, price, stop_loss_percent)
    - account_balance: Total account value  
    - max_portfolio_risk: Maximum percentage of account to risk across all positions
    
    Returns:
    - Optimized list of trade dictionaries
    """
    # Calculate initial trades with equal risk
    equal_risk_per_trade = max_portfolio_risk / len(trades_list)
    
    print(f"Portfolio Risk Optimization")
    print(f"Max portfolio risk: {max_portfolio_risk}%")
    print(f"Risk per trade: {equal_risk_per_trade:.2f}%")
    print("=" * 60)
    
    results = []
    for ticker, price, stop_loss_pct in trades_list:
        trade = calculate_trade(ticker, price, account_balance, equal_risk_per_trade, stop_loss_pct)
        results.append(trade)
    
    return results

# Example usage and testing
if __name__ == "__main__":
    print("Risk-Based Position Sizing Calculator")
    print("=" * 50)
    
    # Single trade example
    print("\n1. SINGLE TRADE EXAMPLE:")
    trade1 = calculate_trade("AAPL", 150.00, account_balance=100000, risk_percent=2, stop_loss_percent=8)
    
    print("\n2. MULTIPLE TRADES EXAMPLE:")
    # Multiple trades with different stop losses
    potential_trades = [
        ("AAPL", 150.00, 8),   # Apple, $150, 8% stop loss
        ("MSFT", 300.00, 6),   # Microsoft, $300, 6% stop loss  
        ("GOOGL", 120.00, 10), # Google, $120, 10% stop loss
        ("TSLA", 200.00, 12),  # Tesla, $200, 12% stop loss
        ("NVDA", 400.00, 8)    # Nvidia, $400, 8% stop loss
    ]
    
    trades = calculate_multiple_trades(potential_trades, account_balance=100000, risk_percent=1.5)
    
    print("\n3. OPTIMIZED PORTFOLIO RISK:")
    optimized_trades = optimize_portfolio_risk(potential_trades, account_balance=100000, max_portfolio_risk=8)
    
    print("\n4. RISK SCENARIOS:")
    print("Testing different risk percentages for AAPL at $150:")
    for risk_pct in [1, 2, 3, 5]:
        print(f"\nRisk {risk_pct}%:")
        calculate_trade("AAPL", 150.00, 100000, risk_pct, 8)