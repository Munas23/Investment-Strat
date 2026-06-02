"""
Simple data connection diagnostic
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def test_basic_connection():
    """Test basic Yahoo Finance connection"""
    print("=== DATA CONNECTION TEST ===")
    
    test_symbols = [
        ('AAPL', 'US Stock'),
        ('CBA.AX', 'ASX Stock'),
        ('SHEL.L', 'UK Stock')
    ]
    
    working_count = 0
    
    for symbol, description in test_symbols:
        print(f"\nTesting {symbol} ({description})...")
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="5d")
            
            if not data.empty:
                latest_price = data['Close'].iloc[-1]
                print(f"  [OK] Got {len(data)} days of data")
                print(f"  [OK] Latest price: {latest_price:.2f}")
                working_count += 1
            else:
                print(f"  [ERROR] No data returned")
                
        except Exception as e:
            print(f"  [ERROR] {str(e)[:60]}...")
    
    print(f"\nResult: {working_count}/{len(test_symbols)} symbols working")
    return working_count >= 2

def test_asx_specifically():
    """Test ASX stocks specifically"""
    print("\n=== ASX 300 SPECIFIC TEST ===")
    
    asx_stocks = ['CBA.AX', 'BHP.AX', 'WBC.AX', 'ANZ.AX', 'CSL.AX']
    working_asx = []
    
    for stock in asx_stocks:
        print(f"Testing {stock}...")
        try:
            ticker = yf.Ticker(stock)
            data = ticker.history(period="2d")
            
            if not data.empty:
                price = data['Close'].iloc[-1]
                print(f"  [OK] {stock}: {price:.2f} AUD")
                working_asx.append(stock)
            else:
                print(f"  [ERROR] {stock}: No data")
                
        except Exception as e:
            print(f"  [ERROR] {stock}: {str(e)[:40]}...")
        
        time.sleep(0.2)  # Small delay
    
    print(f"\nASX Result: {len(working_asx)} working stocks")
    for stock in working_asx:
        print(f"  - {stock}")
    
    return len(working_asx) >= 2

def test_risk_manager_basic():
    """Test basic risk manager functionality"""
    print("\n=== RISK MANAGER TEST ===")
    
    try:
        from multi_market_risk_manager import MultiMarketRiskManager
        
        rm = MultiMarketRiskManager(account_balance_usd=50000)
        print("[OK] Risk manager imported and created")
        
        # Test basic calculation
        trade = rm.calculate_trade("TEST", 100.0, "US_SP500")
        print(f"[OK] Basic trade calculation: {trade['shares']} shares")
        
        # Test ASX calculation
        asx_trade = rm.calculate_trade("TEST.AX", 50.0, "AU_ASX300")
        print(f"[OK] ASX trade calculation: {asx_trade['shares']} shares AUD")
        print(f"[OK] USD equivalent: ${asx_trade['trade_value_usd']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Risk manager failed: {e}")
        return False

def run_offline_demo():
    """Run the offline strategy demo"""
    print("\n=== RUNNING OFFLINE DEMO ===")
    
    try:
        print("Starting offline simulation...")
        exec(open('offline_strategy.py').read())
        return True
    except Exception as e:
        print(f"[ERROR] Offline demo failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("GLOBAL TRADING SYSTEM DIAGNOSTIC")
    print("="*40)
    
    results = {}
    
    # Test 1: Basic data connection
    results['data_connection'] = test_basic_connection()
    
    # Test 2: ASX specific
    results['asx_working'] = test_asx_specifically()
    
    # Test 3: Risk manager
    results['risk_manager'] = test_risk_manager_basic()
    
    # Summary and recommendations
    print("\n" + "="*40)
    print("DIAGNOSTIC SUMMARY")
    print("="*40)
    
    if results['data_connection']:
        print("[OK] Basic data connection working")
    else:
        print("[ERROR] Data connection issues detected")
    
    if results['asx_working']:
        print("[OK] ASX 300 data available")
    else:
        print("[ERROR] ASX 300 data issues")
    
    if results['risk_manager']:
        print("[OK] Risk management system functional")
    else:
        print("[ERROR] Risk management issues")
    
    # Recommendations
    print("\nRECOMMENDATIONS:")
    
    if all(results.values()):
        print("-> All systems working! Try full backtest:")
        print("   python global_flag_strategy.py")
    elif results['risk_manager']:
        if not results['data_connection']:
            print("-> Data issues detected. Try offline mode:")
            print("   python offline_strategy.py")
        else:
            print("-> Some data working. Try simplified version:")
            print("   python offline_strategy.py")
    else:
        print("-> System issues detected. Check:")
        print("   1. Internet connection")
        print("   2. Python package installations")
        print("   3. Try offline mode: python offline_strategy.py")

if __name__ == "__main__":
    main()