"""
Working Data Download - Based on patterns from successful Trading-System implementations
Uses the same simple approach that works in the other folders
"""

import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime

def get_sp500_symbols():
    """Get S&P 500 symbols - exactly like the working versions"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        tickers = table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        print(f"Fetched {len(tickers)} S&P 500 tickers.")
        return tickers
    except Exception as e:
        print(f"Could not fetch S&P 500 tickers: {e}")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'PG']

def download_data_simple(tickers, start_date, end_date):
    """Simple data download - exactly like turtle_sp500.py that works"""
    print(f"Downloading data for {len(tickers)} stocks from {start_date} to {end_date}...")
    
    stock_data = {}
    failed = []
    
    for i, symbol in enumerate(tickers):
        try:
            print(f"Downloading {i+1}/{len(tickers)}: {symbol}")
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if len(data) > 50:  # Need minimum data
                stock_data[symbol] = data
                print(f"  ✓ {symbol}: {len(data)} days")
            else:
                failed.append(symbol)
                print(f"  ✗ {symbol}: insufficient data ({len(data)} days)")
                
        except Exception as e:
            failed.append(symbol)
            print(f"  ✗ {symbol}: {e}")
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    print(f"\nDownload complete:")
    print(f"Successfully downloaded: {len(stock_data)} stocks")
    print(f"Failed: {len(failed)} stocks")
    
    if failed:
        print(f"Failed symbols: {failed[:10]}...")  # Show first 10 failures
    
    return stock_data

def download_data_manual_style(tickers, start_date, end_date):
    """Download data using the manual style from backtester.py"""
    print(f"Starting manual data download for {len(tickers)} tickers...")
    all_dfs = {}
    
    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
            if df.empty: 
                continue
            
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols): 
                continue
                
            # Add ticker column for identification
            df['Ticker'] = ticker
            all_dfs[ticker] = df[required_cols + ['Ticker']]
            
            if (i + 1) % 10 == 0: 
                print(f"--- Progress: Fetched {i+1} of {len(tickers)} tickers ---")
        except Exception as e:
            print(f"({i+1}/{len(tickers)}) Could not download {ticker}: {e}")

    if not all_dfs:
        print("CRITICAL ERROR: No data could be successfully downloaded for any ticker.")
        return None

    print(f"\nAll downloads complete. Got data for {len(all_dfs)} tickers")
    return all_dfs

def simple_test():
    """Test with a few symbols first"""
    print("=== SIMPLE TEST ===")
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    start_date = '2022-01-01'
    end_date = '2023-12-31'
    
    print(f"Testing download with {len(test_symbols)} symbols...")
    
    data = download_data_simple(test_symbols, start_date, end_date)
    
    if data:
        print(f"\n✓ Success! Downloaded data for {len(data)} symbols")
        for symbol, df in data.items():
            print(f"  {symbol}: {len(df)} days, Latest: {df.index[-1]}, Price: ${df['Close'].iloc[-1]:.2f}")
        return True
    else:
        print("\n✗ Test failed - no data downloaded")
        return False

def download_sp500_batch(max_symbols=50):
    """Download S&P 500 data in the working style"""
    print("=== S&P 500 DOWNLOAD ===")
    
    # Get symbols
    symbols = get_sp500_symbols()
    if max_symbols:
        symbols = symbols[:max_symbols]
    
    print(f"Downloading {len(symbols)} S&P 500 symbols...")
    
    start_date = '2020-01-01'
    end_date = '2023-12-31'
    
    # Use the simple method that works
    stock_data = download_data_simple(symbols, start_date, end_date)
    
    if stock_data:
        print(f"\n✓ Successfully downloaded {len(stock_data)} stocks")
        
        # Show some statistics
        total_days = [len(df) for df in stock_data.values()]
        print(f"Average data points per stock: {np.mean(total_days):.0f}")
        print(f"Date range: {min([df.index[0] for df in stock_data.values()])} to {max([df.index[-1] for df in stock_data.values()])}")
        
        # Show sample data
        print("\nSample data:")
        for i, (symbol, df) in enumerate(list(stock_data.items())[:5]):
            latest_price = df['Close'].iloc[-1]
            print(f"  {symbol}: ${latest_price:.2f} ({len(df)} days)")
        
        return stock_data
    else:
        print("\n✗ Failed to download any data")
        return None

def test_yfinance_directly():
    """Test yfinance directly to ensure it's working"""
    print("=== TESTING YFINANCE DIRECTLY ===")
    
    try:
        print("Testing single symbol download...")
        data = yf.download('AAPL', start='2023-01-01', end='2023-12-31', progress=False)
        
        if not data.empty:
            print(f"✓ Direct yfinance test successful!")
            print(f"  Downloaded {len(data)} days for AAPL")
            print(f"  Columns: {list(data.columns)}")
            print(f"  Latest price: ${data['Close'].iloc[-1]:.2f}")
            print(f"  Date range: {data.index[0]} to {data.index[-1]}")
            return True
        else:
            print("✗ No data returned from yfinance")
            return False
            
    except Exception as e:
        print(f"✗ Error testing yfinance: {e}")
        return False

def main():
    """Main test function"""
    print("TESTING DATA DOWNLOAD METHODS")
    print("=" * 50)
    
    # Test 1: Basic yfinance functionality
    print("\n1. Testing basic yfinance functionality...")
    if not test_yfinance_directly():
        print("❌ Basic yfinance test failed - check internet connection")
        return
    
    # Test 2: Simple test with few symbols
    print("\n2. Testing simple download method...")
    if not simple_test():
        print("❌ Simple test failed")
        return
    
    # Test 3: S&P 500 batch download
    print("\n3. Testing S&P 500 batch download...")
    data = download_sp500_batch(max_symbols=20)  # Start with 20 symbols
    
    if data:
        print(f"\n🎉 SUCCESS! All tests passed.")
        print(f"Ready to download larger datasets.")
        
        # Save sample data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for symbol, df in list(data.items())[:3]:  # Save first 3 as examples
            filename = f"sample_data_{symbol}_{timestamp}.csv"
            df.to_csv(filename)
            print(f"Saved sample: {filename}")
    
    else:
        print("❌ S&P 500 test failed")

if __name__ == "__main__":
    main()