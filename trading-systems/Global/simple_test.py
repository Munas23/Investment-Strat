"""
Simple test to verify yfinance is working - no fancy characters
"""

import yfinance as yf
import pandas as pd

def test_basic_download():
    """Test basic yfinance download"""
    print("Testing basic yfinance download...")
    
    try:
        # Test single symbol
        print("Downloading AAPL data...")
        data = yf.download('AAPL', start='2023-01-01', end='2023-12-31', progress=False)
        
        if not data.empty:
            print(f"SUCCESS: Downloaded {len(data)} days for AAPL")
            print(f"Columns: {list(data.columns)}")
            print(f"Latest price: ${data['Close'].iloc[-1]:.2f}")
            print(f"Date range: {data.index[0]} to {data.index[-1]}")
            return True
        else:
            print("ERROR: No data returned")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_multiple_symbols():
    """Test downloading multiple symbols"""
    print("\nTesting multiple symbols...")
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    results = {}
    
    for symbol in symbols:
        try:
            print(f"Downloading {symbol}...")
            data = yf.download(symbol, start='2023-01-01', end='2023-12-31', progress=False)
            
            if not data.empty:
                results[symbol] = data
                print(f"  SUCCESS: {len(data)} days")
            else:
                print(f"  FAILED: No data")
                
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\nResults: {len(results)} out of {len(symbols)} symbols downloaded")
    return results

if __name__ == "__main__":
    print("SIMPLE YFINANCE TEST")
    print("=" * 30)
    
    # Test 1: Single symbol
    success = test_basic_download()
    
    if success:
        # Test 2: Multiple symbols
        data = test_multiple_symbols()
        
        if data:
            print(f"\nAll tests passed! yfinance is working correctly.")
            print("You can now run the full trading system.")
        else:
            print("\nMultiple symbol test failed")
    else:
        print("\nBasic test failed - check internet connection")