"""
Live Conviction Scanner - IB Order Creator
==========================================

Reads Live Conviction Scanner CSV results and creates IB orders with stop losses.
Simply enter stock symbols to create orders with pre-calculated stops and targets.

Usage:
1. Enter stock symbols from the latest Live Conviction Scanner CSV
2. Script automatically finds the stock data and creates bracket orders
3. Review and execute orders in TWS/IB Gateway
"""

import pandas as pd
from ib_insync import *
import os
from datetime import datetime
from typing import List, Dict, Optional

class IBOrderCreator:
    """Create IB orders from Daily Conviction Scanner results"""
    
    def __init__(self):
        self.ib = IB()
        self.orders_created = []
        
        print("=" * 70)
        print("LIVE CONVICTION SCANNER - IB ORDER CREATOR")
        print("=" * 70)
        print("Create orders by entering stock symbols from latest scan")
        print("=" * 70)
    
    def connect_ib(self, port: int = 7497) -> bool:
        """Connect to IB TWS or Gateway"""
        try:
            print(f"Connecting to IB on port {port}...")
            self.ib.connect('127.0.0.1', port, clientId=1)
            print("✓ Connected to Interactive Brokers")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to IB: {e}")
            print("Make sure TWS or IB Gateway is running")
            return False
    
    def disconnect_ib(self):
        """Disconnect from IB"""
        if self.ib.isConnected():
            self.ib.disconnect()
            print("Disconnected from IB")
    
    def create_stock_contract(self, symbol: str) -> Contract:
        """Create stock contract for US or ASX stocks"""
        contract = Stock(symbol.replace('.AX', ''), 'SMART', 'USD')
        
        # Handle ASX stocks
        if '.AX' in symbol:
            contract = Stock(symbol.replace('.AX', ''), 'ASX', 'AUD')
        
        return contract
    
    def create_market_order(self, symbol: str, quantity: int, action: str) -> Order:
        """Create market buy order"""
        order = MarketOrder(action, quantity)
        order.tif = 'DAY'  # Good for day
        order.transmit = False  # Don't transmit yet (for bracket orders)
        return order
    
    def create_bracket_order(self, symbol: str, quantity: int, entry_price: float, 
                           stop_price: float, target_price: float) -> List[Order]:
        """Create bracket order (entry + stop loss + profit target)"""
        
        # Parent order (market buy)
        parent = MarketOrder('BUY', quantity)
        parent.orderId = self.ib.client.getReqId()
        parent.transmit = False
        
        # Stop loss order
        stop_loss = StopOrder('SELL', quantity, stop_price)
        stop_loss.orderId = self.ib.client.getReqId()  
        stop_loss.parentId = parent.orderId
        stop_loss.transmit = False
        
        # Profit target order  
        profit_target = LimitOrder('SELL', quantity, target_price)
        profit_target.orderId = self.ib.client.getReqId()
        profit_target.parentId = parent.orderId
        profit_target.transmit = True  # Transmit all orders together
        
        return [parent, stop_loss, profit_target]
    
    def calculate_position_size(self, conviction_level: int, account_value: float, 
                              price: float) -> int:
        """Calculate position size based on conviction level and account value"""
        position_pct = {
            1: 0.20, 2: 0.25, 3: 0.30, 4: 0.35, 5: 0.40
        }.get(conviction_level, 0.20)
        
        position_value = account_value * position_pct
        quantity = int(position_value / price)
        
        return max(1, quantity)  # Minimum 1 share
    
    def find_latest_csv(self) -> str:
        """Find the latest Live Conviction Scanner CSV file"""
        try:
            csv_files = [f for f in os.listdir('.') if f.endswith('_TRADE_READY.csv') and 'daily_conviction_scan' in f]
            if not csv_files:
                # Try regular CSV files
                csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'daily_conviction_scan' in f]
            
            if csv_files:
                # Sort by modification time to get latest
                csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return csv_files[0]
            return ""
        except Exception:
            return ""
    
    def load_csv_results(self, filename: str = None) -> pd.DataFrame:
        """Load Live Conviction Scanner CSV results"""
        try:
            if filename is None:
                filename = self.find_latest_csv()
                if not filename:
                    print("✗ No Live Conviction Scanner CSV files found")
                    return pd.DataFrame()
            
            if not os.path.exists(filename):
                print(f"✗ CSV file not found: {filename}")
                return pd.DataFrame()
            
            df = pd.read_csv(filename)
            
            # Filter for BUY signals only
            trade_candidates = df[df['ib_action'] == 'BUY'].copy()
            
            print(f"✓ Loaded {len(trade_candidates)} trade candidates from {filename}")
            return trade_candidates
            
        except Exception as e:
            print(f"✗ Error loading CSV: {e}")
            return pd.DataFrame()
    
    def preview_orders(self, trade_data: pd.DataFrame, account_value: float):
        """Preview orders before creating them"""
        if trade_data.empty:
            print("No trade candidates to preview")
            return
        
        print(f"\nORDER PREVIEW (Account Value: ${account_value:,.0f})")
        print("=" * 90)
        print(f"{'Symbol':<8} {'Level':<6} {'Price':<8} {'Qty':<6} {'Stop':<8} {'Target':<8} {'Risk':<8} {'Reward':<8}")
        print("-" * 90)
        
        total_risk = 0
        total_reward = 0
        
        for _, row in trade_data.iterrows():
            symbol = row['symbol']
            price = row['current_price']
            stop = row['stop_loss_price']
            target = row['profit_target_price']
            conviction = row['conviction_level']
            
            qty = self.calculate_position_size(conviction, account_value, price)
            risk = (price - stop) * qty
            reward = (target - price) * qty
            
            total_risk += risk
            total_reward += reward
            
            print(f"{symbol:<8} {conviction:<6} ${price:<7.2f} {qty:<6} ${stop:<7.2f} ${target:<7.2f} ${risk:<7.0f} ${reward:<7.0f}")
        
        print("-" * 90)
        print(f"TOTALS: {len(trade_data)} orders, Risk: ${total_risk:,.0f}, Reward: ${total_reward:,.0f}")
        print(f"Risk/Reward Ratio: 1:{total_reward/total_risk:.1f}" if total_risk > 0 else "")
        print("=" * 90)
    
    def create_orders_from_csv(self, filename: str, account_value: float, 
                              preview_only: bool = True) -> List[Dict]:
        """Create IB orders from CSV file"""
        
        # Load trade candidates
        trade_data = self.load_csv_results(filename)
        if trade_data.empty:
            return []
        
        # Preview orders
        self.preview_orders(trade_data, account_value)
        
        if preview_only:
            print("\nPREVIEW MODE - No orders created")
            print("Set preview_only=False to create actual orders")
            return []
        
        # Confirm order creation
        confirm = input(f"\nCreate {len(trade_data)} orders in IB? (y/n): ").lower()
        if confirm != 'y':
            print("Order creation cancelled")
            return []
        
        # Connect to IB
        if not self.connect_ib():
            return []
        
        created_orders = []
        
        try:
            print(f"\nCreating {len(trade_data)} bracket orders...")
            print("-" * 50)
            
            for i, (_, row) in enumerate(trade_data.iterrows()):
                symbol = row['symbol']
                price = row['current_price']
                stop = row['stop_loss_price']
                target = row['profit_target_price']
                conviction = row['conviction_level']
                
                # Calculate position size
                qty = self.calculate_position_size(conviction, account_value, price)
                
                # Create contract
                contract = self.create_stock_contract(symbol)
                
                # Create bracket orders
                orders = self.create_bracket_order(symbol, qty, price, stop, target)
                
                # Place orders
                for order in orders:
                    trade = self.ib.placeOrder(contract, order)
                    self.ib.sleep(0.5)  # Small delay between orders
                
                created_orders.append({
                    'symbol': symbol,
                    'quantity': qty,
                    'entry_price': price,
                    'stop_price': stop,
                    'target_price': target,
                    'conviction_level': conviction,
                    'orders_created': len(orders)
                })
                
                print(f"✓ {i+1:2d}. {symbol:<8} - {qty:4d} shares - Stop: ${stop:.2f} Target: ${target:.2f}")
            
            print(f"\n✓ Successfully created {len(created_orders)} bracket orders")
            
        except Exception as e:
            print(f"✗ Error creating orders: {e}")
        
        finally:
            self.disconnect_ib()
        
        return created_orders
    
    def symbol_based_order_entry(self, account_value: float):
        """Enter stock symbols to create orders from latest scan data"""
        print("\nSYMBOL-BASED ORDER ENTRY")
        print("-" * 30)
        
        # Load latest CSV data
        scan_data = self.load_csv_results()
        if scan_data.empty:
            print("No scan data available. Cannot create orders.")
            return
        
        print(f"Using data from latest scan: {self.find_latest_csv()}")
        print(f"Available symbols: {len(scan_data)} stocks")
        print("\nEnter stock symbols (one per line, press Enter twice to finish):")
        
        symbols = []
        while True:
            symbol = input("Symbol: ").strip().upper()
            if not symbol:
                break
            symbols.append(symbol)
        
        if not symbols:
            print("No symbols entered.")
            return
        
        # Find matching stocks in scan data
        selected_stocks = []
        for symbol in symbols:
            matches = scan_data[scan_data['symbol'].str.upper() == symbol]
            if not matches.empty:
                # Take the first match (highest conviction if duplicates)
                selected_stocks.append(matches.iloc[0])
                print(f"✓ Found {symbol}")
            else:
                print(f"✗ {symbol} not found in scan data")
        
        if not selected_stocks:
            print("No valid symbols found in scan data.")
            return
        
        # Convert to DataFrame
        selected_df = pd.DataFrame(selected_stocks)
        
        # Preview and create orders
        self.preview_orders(selected_df, account_value)
        
        confirm = input(f"\nCreate {len(selected_df)} bracket orders? (y/n): ").lower()
        if confirm == 'y':
            self.create_orders_from_dataframe(selected_df, account_value)
        else:
            print("Order creation cancelled")
    
    def create_orders_from_dataframe(self, trade_data: pd.DataFrame, account_value: float):
        """Create IB orders from DataFrame"""
        if not self.connect_ib():
            return []
        
        created_orders = []
        
        try:
            print(f"\nCreating {len(trade_data)} bracket orders...")
            print("-" * 50)
            
            for i, (_, row) in enumerate(trade_data.iterrows()):
                symbol = row['symbol']
                price = row['current_price']
                stop = row['stop_loss_price']
                target = row['profit_target_price']
                conviction = row['conviction_level']
                
                # Calculate position size
                qty = self.calculate_position_size(conviction, account_value, price)
                
                # Create contract
                contract = self.create_stock_contract(symbol)
                
                # Create bracket orders
                orders = self.create_bracket_order(symbol, qty, price, stop, target)
                
                # Place orders
                for order in orders:
                    trade = self.ib.placeOrder(contract, order)
                    self.ib.sleep(0.5)  # Small delay between orders
                
                created_orders.append({
                    'symbol': symbol,
                    'quantity': qty,
                    'entry_price': price,
                    'stop_price': stop,
                    'target_price': target,
                    'conviction_level': conviction,
                    'orders_created': len(orders)
                })
                
                print(f"✓ {i+1:2d}. {symbol:<8} - {qty:4d} shares - Stop: ${stop:.2f} Target: ${target:.2f}")
            
            print(f"\n✓ Successfully created {len(created_orders)} bracket orders")
            
        except Exception as e:
            print(f"✗ Error creating orders: {e}")
        
        finally:
            self.disconnect_ib()
        
        return created_orders

    def manual_order_entry(self, account_value: float):
        """Manual order entry for single stocks"""
        print("\nMANUAL ORDER ENTRY")
        print("-" * 30)
        
        try:
            symbol = input("Symbol (e.g., AAPL or CBA.AX): ").strip().upper()
            price = float(input("Current price: $"))
            stop = float(input("Stop loss price: $"))
            target = float(input("Profit target price: $"))
            conviction = int(input("Conviction level (1-5): "))
            
            # Calculate position size
            qty = self.calculate_position_size(conviction, account_value, price)
            
            # Preview order
            risk = (price - stop) * qty
            reward = (target - price) * qty
            position_value = price * qty
            
            print(f"\nORDER PREVIEW:")
            print(f"Symbol: {symbol}")
            print(f"Quantity: {qty} shares")
            print(f"Position Value: ${position_value:,.0f}")
            print(f"Entry: ${price:.2f}")
            print(f"Stop Loss: ${stop:.2f}")
            print(f"Profit Target: ${target:.2f}")
            print(f"Risk: ${risk:,.0f} ({(risk/account_value)*100:.1f}% of account)")
            print(f"Reward: ${reward:,.0f}")
            print(f"Risk/Reward: 1:{reward/risk:.1f}" if risk > 0 else "")
            
            # Confirm and create
            confirm = input(f"\nCreate bracket order for {symbol}? (y/n): ").lower()
            if confirm == 'y':
                if not self.connect_ib():
                    return
                
                try:
                    contract = self.create_stock_contract(symbol)
                    orders = self.create_bracket_order(symbol, qty, price, stop, target)
                    
                    for order in orders:
                        self.ib.placeOrder(contract, order)
                        self.ib.sleep(0.5)
                    
                    print(f"✓ Bracket order created for {symbol}")
                    
                except Exception as e:
                    print(f"✗ Error creating order: {e}")
                finally:
                    self.disconnect_ib()
            else:
                print("Order cancelled")
                
        except ValueError as e:
            print(f"✗ Invalid input: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")


def main():
    """Main order creation interface"""
    creator = IBOrderCreator()
    
    try:
        # Get account value
        print("\nAccount Configuration:")
        account_value = float(input("Enter account value ($): "))
        
        print("\nOrder Creation Options:")
        print("1. Symbol-based entry (recommended)")
        print("2. Create orders from all CSV entries")
        print("3. Manual order entry")
        print("4. Preview CSV orders only")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            # Symbol-based entry (recommended)
            creator.symbol_based_order_entry(account_value)
        
        elif choice == '2':
            # CSV order creation (all entries)
            latest_file = creator.find_latest_csv()
            if latest_file:
                creator.create_orders_from_csv(latest_file, account_value, preview_only=False)
            else:
                print("No Live Conviction Scanner CSV files found")
        
        elif choice == '3':
            # Manual entry
            creator.manual_order_entry(account_value)
        
        elif choice == '4':
            # Preview only
            latest_file = creator.find_latest_csv()
            if latest_file:
                creator.create_orders_from_csv(latest_file, account_value, preview_only=True)
            else:
                print("No Live Conviction Scanner CSV files found")
        
        else:
            print("Invalid choice")
    
    except ValueError:
        print("Invalid account value")
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()