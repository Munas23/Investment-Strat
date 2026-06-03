"""
Working Simple Trading System - Based on successful download patterns
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def test_download():
    """Test that downloads are working"""
    print("Testing download...")
    data = yf.download('AAPL', start='2023-01-01', end='2023-12-31', progress=False)
    print(f"Downloaded {len(data)} days for AAPL")
    print("Data columns:", list(data.columns))
    return not data.empty

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

def download_stocks(symbols, start_date, end_date, max_stocks=20):
    """Download stock data - using the exact pattern from turtle_sp500.py"""
    print(f"Downloading {min(len(symbols), max_stocks)} stocks...")
    
    stock_data = {}
    failed = []
    
    # Limit symbols for testing
    test_symbols = symbols[:max_stocks]
    
    for i, symbol in enumerate(test_symbols):
        try:
            print(f"  {i+1}/{len(test_symbols)}: {symbol}")
            
            # Download exactly like turtle_sp500.py
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if len(data) > 50:  # Need sufficient data
                stock_data[symbol] = data
                print(f"    SUCCESS: {len(data)} days")
            else:
                failed.append(symbol)
                print(f"    FAILED: Only {len(data)} days")
                
        except Exception as e:
            failed.append(symbol)
            print(f"    ERROR: {e}")
    
    print(f"\nDownload complete:")
    print(f"  Successful: {len(stock_data)}")
    print(f"  Failed: {len(failed)}")
    
    return stock_data

def simple_momentum_strategy(stock_data):
    """Simple momentum strategy"""
    print(f"\nCalculating momentum signals for {len(stock_data)} stocks...")
    
    results = {}
    total_signals = 0
    
    for symbol, data in stock_data.items():
        try:
            # Simple momentum indicators
            data['MA_20'] = data['Close'].rolling(20).mean()
            data['MA_50'] = data['Close'].rolling(50).mean()
            
            # Price momentum (20-day return)
            data['Momentum'] = data['Close'] / data['Close'].shift(20) - 1
            
            # Volume surge
            data['Volume_MA'] = data['Volume'].rolling(20).mean()
            data['Volume_Surge'] = data['Volume'] / data['Volume_MA']
            
            # Simple entry: Strong momentum + Above MA + Volume surge
            data['Entry_Signal'] = (
                (data['Momentum'] > 0.10) &  # 10%+ momentum
                (data['Close'] > data['MA_20']) &  # Above MA20
                (data['MA_20'] > data['MA_50']) &  # MA alignment
                (data['Volume_Surge'] > 1.5)  # Volume 50% above average
            )
            
            # Exit: Below MA20
            data['Exit_Signal'] = data['Close'] < data['MA_20']
            
            signals = data['Entry_Signal'].sum()
            total_signals += signals
            
            print(f"  {symbol}: {signals} signals")
            results[symbol] = data
            
        except Exception as e:
            print(f"  Error processing {symbol}: {e}")
    
    print(f"\nTotal entry signals found: {total_signals}")
    return results

def simple_backtest(processed_data):
    """Simple backtest"""
    print(f"\nRunning backtest on {len(processed_data)} stocks...")
    
    # Portfolio settings
    initial_cash = 100000
    cash = initial_cash
    positions = {}
    trades = []
    max_positions = 5
    
    # Get common dates
    all_dates = None
    for symbol, data in processed_data.items():
        if all_dates is None:
            all_dates = data.index
        else:
            all_dates = all_dates.intersection(data.index)
    
    all_dates = sorted(all_dates)
    print(f"Backtesting {len(all_dates)} days: {all_dates[0]} to {all_dates[-1]}")
    
    for date in all_dates:
        # Check exits
        for symbol in list(positions.keys()):
            if symbol in processed_data and date in processed_data[symbol].index:
                if processed_data[symbol].loc[date, 'Exit_Signal']:
                    # Exit position
                    pos = positions[symbol]
                    exit_price = processed_data[symbol].loc[date, 'Close']
                    proceeds = pos['shares'] * exit_price
                    cash += proceeds
                    
                    pnl_pct = (exit_price / pos['entry_price'] - 1) * 100
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_price': pos['entry_price'],
                        'exit_price': exit_price,
                        'pnl_pct': pnl_pct
                    })
                    
                    print(f"EXIT {symbol}: {pnl_pct:.1f}%")
                    del positions[symbol]
        
        # Check entries
        if len(positions) < max_positions:
            for symbol, data in processed_data.items():
                if symbol not in positions and date in data.index:
                    if data.loc[date, 'Entry_Signal']:
                        price = data.loc[date, 'Close']
                        position_size = 20000  # $20k per position
                        shares = int(position_size / price)
                        cost = shares * price
                        
                        if cost <= cash and shares > 0:
                            cash -= cost
                            positions[symbol] = {
                                'entry_price': price,
                                'shares': shares
                            }
                            print(f"ENTER {symbol}: ${price:.2f}")
                            
                            if len(positions) >= max_positions:
                                break
    
    # Results
    if trades:
        trades_df = pd.DataFrame(trades)
        total_return = trades_df['pnl_pct'].mean()
        win_rate = (trades_df['pnl_pct'] > 0).mean() * 100
        
        print(f"\n=== RESULTS ===")
        print(f"Total trades: {len(trades)}")
        print(f"Average return: {total_return:.2f}%")
        print(f"Win rate: {win_rate:.1f}%")
        
        if len(trades) >= 5:
            print(f"\nBest trades:")
            best = trades_df.nlargest(5, 'pnl_pct')
            for _, trade in best.iterrows():
                print(f"  {trade['symbol']}: {trade['pnl_pct']:.1f}%")
        
        return trades_df
    else:
        print(f"\nNo trades generated!")
        return None

def main():
    """Main function"""
    print("SIMPLE WORKING TRADING SYSTEM")
    print("=" * 40)
    
    # Test download first
    if not test_download():
        print("Download test failed!")
        return
    
    # Get symbols
    symbols = get_sp500_symbols()
    
    # Download data (start with small number)
    stock_data = download_stocks(symbols, '2022-01-01', '2023-12-31', max_stocks=15)
    
    if not stock_data:
        print("No data downloaded!")
        return
    
    # Process with strategy
    processed = simple_momentum_strategy(stock_data)
    
    if not processed:
        print("No data processed!")
        return
    
    # Run backtest
    results = simple_backtest(processed)
    
    if results is not None:
        print("\nSUCCESS! The system is working.")
    else:
        print("\nNo trades generated - try different parameters.")

if __name__ == "__main__":
    main()