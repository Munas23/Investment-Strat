"""
Final Working Version - Downloads symbols individually like successful patterns
Based on exact patterns from turtle_sp500.py and backtester.py
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

def download_stocks_individually(symbols, start_date, end_date, max_stocks=20):
    """
    Download stocks one by one - EXACTLY like turtle_sp500.py
    This is the pattern that works in the other folders
    """
    print(f"Downloading {min(len(symbols), max_stocks)} stocks individually...")
    
    stock_data = {}
    failed = []
    
    test_symbols = symbols[:max_stocks]
    
    for i, symbol in enumerate(test_symbols):
        try:
            print(f"  {i+1}/{len(test_symbols)}: {symbol}")
            
            # Download ONE symbol at a time - this avoids multi-level columns
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if not data.empty and len(data) > 50:
                # When downloading one symbol, columns are simple: Open, High, Low, Close, Volume
                stock_data[symbol] = data
                print(f"    SUCCESS: {len(data)} days, columns: {list(data.columns)}")
            else:
                failed.append(symbol)
                print(f"    FAILED: {len(data) if not data.empty else 0} days")
                
        except Exception as e:
            failed.append(symbol)
            print(f"    ERROR: {e}")
        
        # Small delay to be nice to the API
        time.sleep(0.1)
    
    print(f"\nDownload Results:")
    print(f"  Successful: {len(stock_data)}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print(f"  Failed symbols: {failed}")
    
    return stock_data

def calculate_simple_momentum(stock_data):
    """Calculate momentum indicators for each stock"""
    print(f"\nCalculating momentum for {len(stock_data)} stocks...")
    
    results = {}
    total_signals = 0
    
    for symbol, data in stock_data.items():
        try:
            print(f"  Processing {symbol}...")
            
            # Verify we have the right columns (single-level)
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_cols):
                print(f"    ERROR: Missing columns. Has: {list(data.columns)}")
                continue
            
            # Calculate indicators on single-level columns
            data['MA_10'] = data['Close'].rolling(10).mean()
            data['MA_20'] = data['Close'].rolling(20).mean()
            data['MA_50'] = data['Close'].rolling(50).mean()
            
            # Momentum (20-day return)
            data['Momentum_20'] = data['Close'] / data['Close'].shift(20) - 1
            
            # Volume analysis
            data['Volume_MA_20'] = data['Volume'].rolling(20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_MA_20']
            
            # Price relative to recent high
            data['High_20'] = data['High'].rolling(20).max()
            data['Near_High'] = data['Close'] / data['High_20']
            
            # Simple entry conditions
            data['Strong_Momentum'] = data['Momentum_20'] > 0.08  # 8%+ gain
            data['Above_MA10'] = data['Close'] > data['MA_10']
            data['MA_Aligned'] = data['MA_10'] > data['MA_20']
            data['Volume_Surge'] = data['Volume_Ratio'] > 1.3
            data['Near_Highs'] = data['Near_High'] > 0.9  # Within 10% of 20-day high
            
            # Combine conditions
            data['Entry_Signal'] = (
                data['Strong_Momentum'] &
                data['Above_MA10'] &
                data['MA_Aligned'] &
                data['Volume_Surge'] &
                data['Near_Highs']
            )
            
            # Exit: Close below MA10
            data['Exit_Signal'] = data['Close'] < data['MA_10']
            
            # Count signals
            signals = data['Entry_Signal'].sum()
            total_signals += signals
            
            print(f"    SUCCESS: {signals} entry signals")
            results[symbol] = data
            
        except Exception as e:
            print(f"    ERROR processing {symbol}: {e}")
            continue
    
    print(f"\nProcessing complete:")
    print(f"  Processed: {len(results)} stocks")
    print(f"  Total signals: {total_signals}")
    
    return results

def run_momentum_backtest(processed_data):
    """Run backtest like turtle_sp500.py pattern"""
    print(f"\nRunning backtest...")
    
    # Portfolio setup
    initial_capital = 100000
    cash = initial_capital
    positions = {}  # {symbol: {'shares': x, 'entry_price': y, 'entry_date': z}}
    trades = []
    
    max_positions = 5
    position_size_pct = 0.20  # 20% per position
    
    # Get common trading dates
    all_dates = None
    for symbol, data in processed_data.items():
        if all_dates is None:
            all_dates = data.index
        else:
            all_dates = all_dates.intersection(data.index)
    
    all_dates = sorted(all_dates)
    print(f"Backtesting {len(all_dates)} days: {all_dates[0]} to {all_dates[-1]}")
    
    # Process each trading day
    for i, date in enumerate(all_dates):
        # Check exits first
        positions_to_close = []
        for symbol in positions.keys():
            if symbol in processed_data and date in processed_data[symbol].index:
                if processed_data[symbol].loc[date, 'Exit_Signal']:
                    positions_to_close.append(symbol)
        
        # Execute exits
        for symbol in positions_to_close:
            pos = positions[symbol]
            exit_price = processed_data[symbol].loc[date, 'Close']
            proceeds = pos['shares'] * exit_price
            cash += proceeds
            
            # Calculate P&L
            pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
            
            trades.append({
                'symbol': symbol,
                'entry_date': pos['entry_date'],
                'exit_date': date,
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'pnl_pct': pnl,
                'hold_days': (date - pos['entry_date']).days
            })
            
            print(f"EXIT {symbol}: ${exit_price:.2f}, P&L: {pnl:.1f}%")
            del positions[symbol]
        
        # Check for new entries
        if len(positions) < max_positions:
            for symbol, data in processed_data.items():
                if symbol not in positions and date in data.index:
                    if data.loc[date, 'Entry_Signal']:
                        price = data.loc[date, 'Close']
                        
                        # Calculate position size
                        current_portfolio_value = cash
                        for s, pos in positions.items():
                            current_price = processed_data[s].loc[date, 'Close']
                            current_portfolio_value += pos['shares'] * current_price
                        
                        position_value = current_portfolio_value * position_size_pct
                        shares = int(position_value / price)
                        cost = shares * price
                        
                        if shares > 0 and cost <= cash:
                            cash -= cost
                            positions[symbol] = {
                                'shares': shares,
                                'entry_price': price,
                                'entry_date': date
                            }
                            
                            print(f"ENTER {symbol}: ${price:.2f}, {shares} shares")
                            
                            if len(positions) >= max_positions:
                                break
        
        # Progress update
        if (i + 1) % 50 == 0:
            total_value = cash
            for symbol, pos in positions.items():
                if symbol in processed_data and date in processed_data[symbol].index:
                    current_price = processed_data[symbol].loc[date, 'Close']
                    total_value += pos['shares'] * current_price
            
            print(f"  Day {i+1}/{len(all_dates)}: Portfolio ${total_value:,.0f}, Positions: {len(positions)}")
    
    # Final results
    if trades:
        trades_df = pd.DataFrame(trades)
        
        # Calculate final portfolio value
        final_value = cash
        for symbol, pos in positions.items():
            final_price = processed_data[symbol]['Close'].iloc[-1]
            final_value += pos['shares'] * final_price
        
        total_return = (final_value / initial_capital - 1) * 100
        
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Initial Capital: ${initial_capital:,}")
        print(f"Final Value: ${final_value:,.0f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Number of Trades: {len(trades)}")
        
        # Trade statistics
        win_rate = (trades_df['pnl_pct'] > 0).mean() * 100
        avg_return = trades_df['pnl_pct'].mean()
        avg_winner = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean()
        avg_loser = trades_df[trades_df['pnl_pct'] < 0]['pnl_pct'].mean()
        avg_hold = trades_df['hold_days'].mean()
        
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average Return: {avg_return:.2f}%")
        print(f"Average Winner: {avg_winner:.2f}%")
        print(f"Average Loser: {avg_loser:.2f}%")
        print(f"Average Hold Days: {avg_hold:.1f}")
        
        # Show best trades
        if len(trades_df) >= 5:
            print(f"\nTop 5 Trades:")
            best_trades = trades_df.nlargest(5, 'pnl_pct')
            for _, trade in best_trades.iterrows():
                print(f"  {trade['symbol']}: {trade['pnl_pct']:.1f}% ({trade['hold_days']} days)")
        
        return {
            'trades': trades_df,
            'final_return': total_return,
            'win_rate': win_rate
        }
    
    else:
        print(f"\n=== NO TRADES GENERATED ===")
        print("This means the strategy conditions are too strict.")
        print("Try adjusting parameters:")
        print("- Lower momentum threshold (current: 8%)")
        print("- Lower volume surge requirement (current: 30%)")
        print("- Different date range")
        return None

def main():
    """Main function"""
    print("FINAL WORKING TRADING SYSTEM")
    print("Using exact patterns from successful implementations")
    print("=" * 60)
    
    # Configuration
    start_date = '2022-01-01'
    end_date = '2023-12-31'
    max_stocks = 20  # Start with 20 stocks
    
    print(f"Period: {start_date} to {end_date}")
    print(f"Max stocks: {max_stocks}")
    
    # Step 1: Get symbols
    symbols = get_sp500_symbols()
    
    # Step 2: Download data (one by one like turtle_sp500.py)
    stock_data = download_stocks_individually(symbols, start_date, end_date, max_stocks)
    
    if not stock_data:
        print("❌ No data downloaded! Check internet connection.")
        return
    
    print(f"✅ Successfully downloaded {len(stock_data)} stocks")
    
    # Step 3: Calculate momentum indicators
    processed_data = calculate_simple_momentum(stock_data)
    
    if not processed_data:
        print("❌ No data processed!")
        return
    
    print(f"✅ Successfully processed {len(processed_data)} stocks")
    
    # Step 4: Run backtest
    results = run_momentum_backtest(processed_data)
    
    if results:
        print(f"\n🎉 BACKTEST COMPLETED SUCCESSFULLY!")
        print(f"The system is working correctly!")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results['trades'].to_csv(f"momentum_trades_{timestamp}.csv", index=False)
        print(f"Results saved to: momentum_trades_{timestamp}.csv")
    else:
        print(f"\n⚠️ No trades generated")
        print("The download and processing worked, but strategy needs adjustment")

if __name__ == "__main__":
    main()