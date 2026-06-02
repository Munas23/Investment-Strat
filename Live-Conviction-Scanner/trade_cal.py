"""
Trade Calculator
================

Simple calculator for position sizing, stop loss, and target amounts.
Just enter portfolio value and stock price to get trade calculations.

Usage:
1. Enter your portfolio value
2. Enter stock price
3. Get position size, stop loss amount, and target amount
"""

import sys

class TradeCalculator:
    """Simple trade calculator for risk-based position sizing"""
    
    def __init__(self):
        # Default settings (can be customized)
        self.stop_loss_pct = 7.0    # 7% stop loss
        self.target_pct = 15.0      # 15% profit target
        self.risk_pct = 2.0         # 2% of portfolio at risk per trade
        
        print("=" * 60)
        print("TRADE CALCULATOR")
        print("=" * 60)
        print("Calculate position size using risk-based methodology")
        print("=" * 60)
    
    def calculate_trade(self, portfolio_value: float, stock_price: float, 
                       custom_risk_pct: float = None) -> dict:
        """Calculate all trade parameters using risk-based position sizing"""
        
        # Use custom risk percentage if provided
        risk_pct = custom_risk_pct if custom_risk_pct else self.risk_pct
        
        # Calculate capital to risk (based on place_trade.py methodology)
        capital_to_risk = portfolio_value * (risk_pct / 100)
        
        # Calculate stop loss price
        stop_loss_price = stock_price * (1 - self.stop_loss_pct / 100)
        
        # Risk per share
        risk_per_share = stock_price - stop_loss_price
        
        # Number of shares to buy (rounded down to nearest whole share)
        shares_to_buy = int(capital_to_risk / risk_per_share) if risk_per_share > 0 else 0
        
        # Actual position value
        actual_position_value = shares_to_buy * stock_price
        
        # Actual risk amount (should equal capital_to_risk)
        actual_risk_amount = (stock_price - stop_loss_price) * shares_to_buy
        
        # Calculate profit target
        target_price = stock_price * (1 + self.target_pct / 100)
        target_amount = (target_price - stock_price) * shares_to_buy
        
        # Calculate percentages of portfolio
        actual_risk_pct = (actual_risk_amount / portfolio_value) * 100
        target_portfolio_pct = (target_amount / portfolio_value) * 100
        actual_position_pct = (actual_position_value / portfolio_value) * 100
        
        return {
            'shares_to_buy': shares_to_buy,
            'actual_position_value': actual_position_value,
            'actual_position_pct': actual_position_pct,
            'stop_loss_price': stop_loss_price,
            'stop_loss_amount': actual_risk_amount,
            'stop_loss_portfolio_pct': actual_risk_pct,
            'target_price': target_price,
            'target_amount': target_amount,
            'target_portfolio_pct': target_portfolio_pct,
            'risk_per_share': risk_per_share,
            'capital_to_risk': capital_to_risk,
            'risk_reward_ratio': target_amount / actual_risk_amount if actual_risk_amount > 0 else 0
        }
    
    def print_trade_summary(self, portfolio_value: float, stock_price: float, 
                           symbol: str = "STOCK", results: dict = None):
        """Print formatted trade summary"""
        
        if results is None:
            results = self.calculate_trade(portfolio_value, stock_price)
        
        print(f"\nTRADE CALCULATION FOR {symbol}")
        print("=" * 50)
        print(f"Portfolio Value:     ${portfolio_value:,.0f}")
        print(f"Stock Price:         ${stock_price:.2f}")
        print(f"Risk Per Trade:      {self.risk_pct}% of portfolio")
        print(f"Capital to Risk:     ${results['capital_to_risk']:,.0f}")
        print()
        
        print("POSITION DETAILS:")
        print("-" * 30)
        print(f"Risk per Share:      ${results['risk_per_share']:.2f}")
        print(f"Shares to Buy:       {results['shares_to_buy']:,} shares")
        print(f"Position Value:      ${results['actual_position_value']:,.0f}")
        print(f"Position Size:       {results['actual_position_pct']:.1f}% of portfolio")
        print()
        
        print("STOP LOSS:")
        print("-" * 30)
        print(f"Stop Loss Price:     ${results['stop_loss_price']:.2f}")
        print(f"Stop Loss Amount:    ${results['stop_loss_amount']:,.0f}")
        print(f"Risk (% of portfolio): {results['stop_loss_portfolio_pct']:.1f}%")
        print()
        
        print("PROFIT TARGET:")
        print("-" * 30)
        print(f"Target Price:        ${results['target_price']:.2f}")
        print(f"Target Amount:       ${results['target_amount']:,.0f}")
        print(f"Reward (% of portfolio): {results['target_portfolio_pct']:.1f}%")
        print()
        
        print("RISK/REWARD ANALYSIS:")
        print("-" * 30)
        print(f"Risk/Reward Ratio:   1:{results['risk_reward_ratio']:.1f}")
        print(f"Win Rate Needed:     {100/(1+results['risk_reward_ratio']):.1f}%")
        print("=" * 50)
    
    def interactive_calculator(self):
        """Interactive calculator mode"""
        
        try:
            while True:
                print("\nENTER TRADE DETAILS:")
                print("-" * 25)
                
                # Get portfolio value
                portfolio_input = input("Portfolio Value ($): ").strip().replace(',', '').replace('$', '')
                if not portfolio_input:
                    print("Exiting calculator...")
                    break
                    
                portfolio_value = float(portfolio_input)
                
                # Get stock price
                price_input = input("Stock Price ($): ").strip().replace('$', '')
                stock_price = float(price_input)
                
                # Optional: Get symbol
                symbol = input("Symbol (optional): ").strip().upper()
                if not symbol:
                    symbol = "STOCK"
                
                # Optional: Custom risk percentage
                risk_input = input(f"Risk % (default {self.risk_pct}%): ").strip()
                custom_risk_pct = None
                if risk_input:
                    custom_risk_pct = float(risk_input)
                
                # Calculate and display results
                results = self.calculate_trade(portfolio_value, stock_price, custom_risk_pct)
                self.print_trade_summary(portfolio_value, stock_price, symbol, results)
                
                # Ask if user wants to continue
                continue_calc = input("\nCalculate another trade? (y/n): ").strip().lower()
                if continue_calc != 'y':
                    break
                    
        except ValueError as e:
            print(f"Error: Invalid number format. Please enter valid numbers.")
        except KeyboardInterrupt:
            print("\nCalculator interrupted by user")
        except Exception as e:
            print(f"Error: {e}")
    
    def quick_calculation(self, portfolio_value: float, stock_price: float, symbol: str = ""):
        """Quick calculation without interaction"""
        results = self.calculate_trade(portfolio_value, stock_price)
        self.print_trade_summary(portfolio_value, stock_price, symbol or "STOCK", results)
        return results
    
    def batch_calculator(self, trades_list: list):
        """Calculate multiple trades at once"""
        print("\nBATCH TRADE CALCULATIONS")
        print("=" * 60)
        
        total_position_value = 0
        total_risk = 0
        total_reward = 0
        
        for i, trade in enumerate(trades_list, 1):
            portfolio_value = trade['portfolio_value']
            stock_price = trade['stock_price']
            symbol = trade.get('symbol', f'STOCK{i}')
            
            results = self.calculate_trade(portfolio_value, stock_price)
            
            total_position_value += results['actual_position_value']
            total_risk += results['stop_loss_amount']
            total_reward += results['target_amount']
            
            print(f"\n{i}. {symbol}:")
            print(f"   Shares: {results['shares_to_buy']:,}")
            print(f"   Position: ${results['actual_position_value']:,.0f}")
            print(f"   Risk: ${results['stop_loss_amount']:,.0f}")
            print(f"   Reward: ${results['target_amount']:,.0f}")
        
        print(f"\nBATCH SUMMARY:")
        print("-" * 30)
        print(f"Total Position Value: ${total_position_value:,.0f}")
        print(f"Total Risk:           ${total_risk:,.0f}")
        print(f"Total Reward:         ${total_reward:,.0f}")
        print(f"Overall Risk/Reward:  1:{total_reward/total_risk:.1f}" if total_risk > 0 else "")
        print("=" * 60)

def main():
    """Main calculator interface"""
    
    calculator = TradeCalculator()
    
    # Check if command line arguments provided
    if len(sys.argv) >= 3:
        try:
            portfolio_value = float(sys.argv[1])
            stock_price = float(sys.argv[2])
            symbol = sys.argv[3] if len(sys.argv) > 3 else ""
            
            print("COMMAND LINE CALCULATION:")
            calculator.quick_calculation(portfolio_value, stock_price, symbol)
            return
            
        except (ValueError, IndexError):
            print("Invalid command line arguments. Using interactive mode.")
    
    # Interactive mode
    print("Interactive Mode - Enter values or press Enter on portfolio value to exit")
    calculator.interactive_calculator()
    
    print("\nThank you for using Trade Calculator!")

if __name__ == "__main__":
    main()