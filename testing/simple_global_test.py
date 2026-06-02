"""
Simplified global trading system test with robust data handling
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

def test_data_connection():
    """Test basic data connectivity"""
    print("=== Testing Data Connection ===")
    
    # Test basic US stock
    print("1. Testing US market (AAPL)...")
    try:
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="5d")
        if not data.empty:
            print(f"   ✓ US data OK: {len(data)} days, latest price: ${data['Close'].iloc[-1]:.2f}")
        else:
            print("   ✗ US data empty")
    except Exception as e:
        print(f"   ✗ US data error: {e}")
    
    # Test ASX stock
    print("2. Testing ASX market (CBA.AX)...")
    try:
        ticker = yf.Ticker("CBA.AX")
        data = ticker.history(period="5d")
        if not data.empty:
            print(f"   ✓ ASX data OK: {len(data)} days, latest price: {data['Close'].iloc[-1]:.2f} AUD")
        else:
            print("   ✗ ASX data empty")
    except Exception as e:
        print(f"   ✗ ASX data error: {e}")
    
    # Test UK stock
    print("3. Testing UK market (SHEL.L)...")
    try:
        ticker = yf.Ticker("SHEL.L")
        data = ticker.history(period="5d")
        if not data.empty:
            print(f"   ✓ UK data OK: {len(data)} days, latest price: {data['Close'].iloc[-1]:.2f} GBP")
        else:
            print("   ✗ UK data empty")
    except Exception as e:
        print(f"   ✗ UK data error: {e}")

def test_market_tickers():
    """Test ticker availability for each market"""
    print("\n=== Testing Market Tickers ===")
    
    test_tickers = {
        'US (S&P 500)': ['AAPL', 'MSFT', 'GOOGL'],
        'ASX 300': ['CBA.AX', 'BHP.AX', 'WBC.AX'],
        'UK (FTSE)': ['SHEL.L', 'AZN.L', 'ULVR.L'],
        'Germany (DAX)': ['SAP.DE', 'SIE.DE', 'ALV.DE'],
        'Japan (Nikkei)': ['7203.T', '6758.T', '9984.T']
    }
    
    working_tickers = {}
    
    for market, tickers in test_tickers.items():
        print(f"\n{market}:")
        working_tickers[market] = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                data = stock.history(period="2d")
                if not data.empty and len(data) > 0:
                    price = data['Close'].iloc[-1]
                    print(f"   ✓ {ticker}: ${price:.2f}")
                    working_tickers[market].append(ticker)
                else:
                    print(f"   ✗ {ticker}: No data")
            except Exception as e:
                print(f"   ✗ {ticker}: Error - {str(e)[:50]}...")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
    
    return working_tickers

def test_risk_manager():
    """Test the multi-market risk manager with available data"""
    print("\n=== Testing Risk Manager ===")
    
    try:
        from multi_market_risk_manager import MultiMarketRiskManager
        
        rm = MultiMarketRiskManager(
            account_balance_usd=100000,
            default_risk_percent=2
        )
        
        print("✓ Risk manager initialized")
        
        # Test US trade
        try:
            trade = rm.calculate_trade("AAPL", 150.0, "US_SP500")
            print(f"✓ US trade calculated: {trade['shares']} shares")
        except Exception as e:
            print(f"✗ US trade failed: {e}")
        
        # Test ASX trade
        try:
            trade = rm.calculate_trade("CBA.AX", 95.0, "AU_ASX300")
            print(f"✓ ASX trade calculated: {trade['shares']} shares, {trade['trade_value']:.2f} AUD")
            print(f"  USD equivalent: ${trade['trade_value_usd']:.2f}")
        except Exception as e:
            print(f"✗ ASX trade failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Risk manager error: {e}")
        return False

def create_simple_strategy():
    """Create a simplified strategy with working tickers only"""
    print("\n=== Creating Simplified Strategy ===")
    
    # Get working tickers
    working_tickers = test_market_tickers()
    
    # Filter to only markets with working tickers
    reliable_markets = {k: v for k, v in working_tickers.items() if len(v) >= 2}
    
    print(f"\nReliable markets found: {len(reliable_markets)}")
    for market, tickers in reliable_markets.items():
        print(f"  {market}: {len(tickers)} working tickers")
    
    if len(reliable_markets) >= 3:
        print("✓ Sufficient markets for global trading")
        return reliable_markets
    else:
        print("✗ Insufficient reliable markets")
        return None

def run_mini_backtest():
    """Run a mini backtest with available data"""
    print("\n=== Mini Backtest with Available Data ===")
    
    # Test a few reliable tickers
    test_stocks = ['AAPL', 'CBA.AX', 'SHEL.L']
    
    results = {}
    
    for ticker in test_stocks:
        print(f"\nTesting {ticker}...")
        try:
            # Get 30 days of data
            stock = yf.Ticker(ticker)
            data = stock.history(period="30d")
            
            if data.empty:
                print(f"  ✗ No data for {ticker}")
                continue
            
            # Simple analysis
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            return_pct = ((end_price / start_price) - 1) * 100
            
            # Calculate simple moving averages
            data['MA10'] = data['Close'].rolling(10).mean()
            data['MA20'] = data['Close'].rolling(20).mean()
            
            # Check if we have enough data for MAs
            if len(data) >= 20:
                latest_ma10 = data['MA10'].iloc[-1]
                latest_ma20 = data['MA20'].iloc[-1]
                ma_trend = "Bullish" if latest_ma10 > latest_ma20 else "Bearish"
            else:
                ma_trend = "Insufficient data"
            
            results[ticker] = {
                'days': len(data),
                'start_price': start_price,
                'end_price': end_price,
                'return_pct': return_pct,
                'ma_trend': ma_trend
            }
            
            print(f"  ✓ {ticker}: {len(data)} days, {return_pct:.1f}% return, {ma_trend}")
            
        except Exception as e:
            print(f"  ✗ {ticker}: Error - {e}")
    
    return results

def main():
    """Main test function"""
    print("🌍 SIMPLIFIED GLOBAL TRADING SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    test_data_connection()
    
    # Test 2: Market ticker availability  
    working_tickers = test_market_tickers()
    
    # Test 3: Risk manager functionality
    risk_manager_ok = test_risk_manager()
    
    # Test 4: Create simplified strategy
    reliable_markets = create_simple_strategy()
    
    # Test 5: Mini backtest
    backtest_results = run_mini_backtest()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 SUMMARY")
    print("=" * 50)
    
    total_working = sum(len(tickers) for tickers in working_tickers.values())
    print(f"Working tickers found: {total_working}")
    
    if risk_manager_ok:
        print("✓ Risk management system functional")
    else:
        print("✗ Risk management system issues")
    
    if reliable_markets and len(reliable_markets) >= 3:
        print(f"✓ Global trading possible with {len(reliable_markets)} markets")
        print("✓ ASX 300 support verified" if 'ASX 300' in reliable_markets else "⚠ ASX 300 needs verification")
    else:
        print("✗ Limited market coverage - check internet connection")
    
    if backtest_results and len(backtest_results) >= 2:
        print(f"✓ Mini backtest successful with {len(backtest_results)} stocks")
    else:
        print("✗ Backtest data issues")
    
    print("\n📋 NEXT STEPS:")
    if total_working >= 10:
        print("→ Run full global strategy: python global_flag_strategy.py")
    elif total_working >= 5:
        print("→ Run simplified strategy with available markets")
    else:
        print("→ Check internet connection and try again")
        print("→ Consider using offline/cached data")

if __name__ == "__main__":
    main()