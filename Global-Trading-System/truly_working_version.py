"""
Truly Working Version - Handles the multi-level column issue properly
Based on analysis of what's actually happening with yfinance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import time
warnings.filterwarnings('ignore')

def get_sp500_symbols():
    """Get S&P 500 symbols"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        tickers = table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        print(f"Fetched {len(tickers)} S&P 500 tickers")
        return tickers
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT']

def download_and_fix_columns(symbol, start_date, end_date):
    """Download single symbol and fix the column structure"""
    try:
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None
        
        # Fix the multi-level columns that yfinance creates
        if isinstance(data.columns, pd.MultiIndex):
            # Flatten multi-level columns - take only the first level (the actual OHLCV names)
            data.columns = [col[0] for col in data.columns]
        
        # Ensure we have the standard columns
        expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in expected_cols):
            print(f"    Missing columns for {symbol}. Has: {list(data.columns)}")
            return None
        
        return data
        
    except Exception as e:
        print(f"    Error downloading {symbol}: {e}")
        return None

def download_stocks_fixed(symbols, start_date, end_date, max_stocks=20):
    """Download stocks with proper column handling"""
    print(f"Downloading {min(len(symbols), max_stocks)} stocks...")
    
    stock_data = {}
    failed = []
    
    test_symbols = symbols[:max_stocks]
    
    for i, symbol in enumerate(test_symbols):
        print(f"  {i+1}/{len(test_symbols)}: {symbol}")
        
        data = download_and_fix_columns(symbol, start_date, end_date)
        
        if data is not None and len(data) > 50:
            stock_data[symbol] = data
            print(f"    SUCCESS: {len(data)} days, columns: {list(data.columns)}")
        else:
            failed.append(symbol)
            print(f"    FAILED")
        
        time.sleep(0.1)  # Be nice to API
    
    print(f"\nDownload Results:")
    print(f"  Successful: {len(stock_data)}")
    print(f"  Failed: {len(failed)}")
    
    return stock_data

def calculate_momentum_fixed(stock_data):
    """Calculate momentum with proper column handling"""
    print(f"\nCalculating momentum for {len(stock_data)} stocks...")
    
    results = {}
    total_signals = 0
    
    for symbol, data in stock_data.items():
        try:
            print(f"  Processing {symbol}...")
            
            # Now we should have clean single-level columns
            print(f"    Columns: {list(data.columns)}")
            
            # Verify columns
            if 'Close' not in data.columns:
                print(f"    ERROR: No Close column")
                continue
            
            # Calculate indicators
            data['MA_10'] = data['Close'].rolling(10).mean()
            data['MA_20'] = data['Close'].rolling(20).mean()
            data['MA_50'] = data['Close'].rolling(50).mean()
            
            # Momentum
            data['Momentum_20'] = data['Close'] / data['Close'].shift(20) - 1
            
            # Volume
            data['Volume_MA_20'] = data['Volume'].rolling(20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_MA_20']
            
            # Near highs
            data['High_20'] = data['High'].rolling(20).max()
            data['Near_High'] = data['Close'] / data['High_20']
            
            # Entry conditions
            data['Strong_Momentum'] = data['Momentum_20'] > 0.08
            data['Above_MA10'] = data['Close'] > data['MA_10']
            data['MA_Aligned'] = data['MA_10'] > data['MA_20']
            data['Volume_Surge'] = data['Volume_Ratio'] > 1.3
            data['Near_Highs'] = data['Near_High'] > 0.9
            
            # Combined entry signal
            data['Entry_Signal'] = (
                data['Strong_Momentum'] &
                data['Above_MA10'] &
                data['MA_Aligned'] &
                data['Volume_Surge'] &
                data['Near_Highs']
            )
            
            # Exit signal
            data['Exit_Signal'] = data['Close'] < data['MA_10']
            
            # Count signals
            signals = data['Entry_Signal'].sum()
            total_signals += signals
            
            print(f"    SUCCESS: {signals} entry signals")
            results[symbol] = data
            
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
    
    print(f"\nProcessing Results:")
    print(f"  Processed: {len(results)} stocks")
    print(f"  Total signals: {total_signals}")
    
    return results

def run_backtest_simple(processed_data):
    """Simple backtest"""
    print(f"\nRunning backtest on {len(processed_data)} stocks...")
    
    # Setup
    initial_capital = 100000
    cash = initial_capital
    positions = {}
    trades = []
    max_positions = 5
    
    # Get trading dates
    all_dates = None
    for symbol, data in processed_data.items():
        if all_dates is None:
            all_dates = data.index
        else:
            all_dates = all_dates.intersection(data.index)
    
    all_dates = sorted(all_dates)
    print(f"Trading period: {len(all_dates)} days ({all_dates[0]} to {all_dates[-1]})")
    
    # Backtest loop
    for i, date in enumerate(all_dates):
        # Check exits
        for symbol in list(positions.keys()):
            if symbol in processed_data and date in processed_data[symbol].index:
                if processed_data[symbol].loc[date, 'Exit_Signal']:
                    # Exit
                    pos = positions[symbol]
                    exit_price = processed_data[symbol].loc[date, 'Close']
                    proceeds = pos['shares'] * exit_price
                    cash += proceeds
                    
                    pnl_pct = (exit_price / pos['entry_price'] - 1) * 100
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_price': pos['entry_price'],
                        'exit_price': exit_price,
                        'pnl_pct': pnl_pct,
                        'hold_days': (date - pos['entry_date']).days
                    })
                    
                    print(f"EXIT {symbol}: {pnl_pct:.1f}%")
                    del positions[symbol]
        
        # Check entries
        if len(positions) < max_positions:
            for symbol, data in processed_data.items():
                if symbol not in positions and date in data.index:
                    if data.loc[date, 'Entry_Signal']:
                        price = data.loc[date, 'Close']
                        position_value = 20000  # Fixed $20k position
                        shares = int(position_value / price)
                        cost = shares * price
                        
                        if cost <= cash and shares > 0:
                            cash -= cost
                            positions[symbol] = {
                                'entry_price': price,
                                'shares': shares,
                                'entry_date': date
                            }
                            print(f"ENTER {symbol}: ${price:.2f}")
                            
                            if len(positions) >= max_positions:
                                break
        
        # Progress
        if (i + 1) % 100 == 0:
            print(f"  Day {i+1}/{len(all_dates)}")
    
    # Results
    if trades:
        trades_df = pd.DataFrame(trades)
        
        print(f"\n=== RESULTS ===")
        print(f"Total trades: {len(trades)}")
        print(f"Average return: {trades_df['pnl_pct'].mean():.2f}%")
        print(f"Win rate: {(trades_df['pnl_pct'] > 0).mean() * 100:.1f}%")
        print(f"Best trade: {trades_df['pnl_pct'].max():.1f}%")
        print(f"Worst trade: {trades_df['pnl_pct'].min():.1f}%")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_results_{timestamp}.csv"
        trades_df.to_csv(filename, index=False)
        print(f"Results saved: {filename}")
        
        return trades_df
    else:
        print(f"\nNo trades generated!")
        print("Strategy conditions may be too strict.")
        return None

def main():
    """Main function"""
    print("TRULY WORKING TRADING SYSTEM")
    print("Handles yfinance column issues properly")
    print("=" * 50)
    
    # Get symbols
    symbols = get_sp500_symbols()
    
    # Download (start small)
    stock_data = download_stocks_fixed(symbols, '2022-01-01', '2023-12-31', max_stocks=15)
    
    if not stock_data:
        print("No data downloaded!")
        return
    
    print(f"Downloaded {len(stock_data)} stocks successfully")
    
    # Process
    processed = calculate_momentum_fixed(stock_data)
    
    if not processed:
        print("No data processed!")
        return
    
    print(f"Processed {len(processed)} stocks successfully")
    
    # Backtest
    results = run_backtest_simple(processed)
    
    if results is not None:
        print("\nSUCCESS! System is working!")
    else:
        print("\nSystem works but no trades generated")

if __name__ == "__main__":
    main()