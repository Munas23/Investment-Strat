import warnings
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime
import matplotlib.pyplot as plt
import time

warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
class StrategyConfig:
    flagpole_period = 60
    flagpole_min_gain = 0.20  # Reduced from 0.30
    consolidation_window = 20
    consolidation_volatility_threshold = 0.5  # Increased from 0.3
    ma_fast = 10
    ma_medium = 20
    ma_slow = 50
    max_stop_loss = 0.08
    min_stop_loss = 0.02
    max_position_size = 0.10
    commission = 0.001
    start_date = '2018-01-01'
    end_date = '2023-12-31'
    max_tickers = None

# --- DATA FETCHING ---
def get_sp500_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        tickers = table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        print(f"Fetched {len(tickers)} S&P 500 tickers.")
        return tickers
    except Exception as e:
        print(f"Could not fetch S&P 500 tickers: {e}")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD']

def download_data(tickers, start, end):
    print(f"Downloading data for {len(tickers)} stocks from {start} to {end}...")
    
    retry_count = 3
    while retry_count > 0:
        try:
            # Updated download parameters
            price_data = vbt.YFData.download(
                tickers,
                start=start,
                end=end,
                missing_index='drop'  # Handle missing data
            )
            
            # Verify data quality
            valid_data = price_data.get('Close')
            if valid_data is None or valid_data.empty:
                raise ValueError("No valid data downloaded")
                
            valid_columns = valid_data.dropna(axis=1).columns
            if len(valid_columns) < len(tickers):
                print(f"Warning: Only got data for {len(valid_columns)} out of {len(tickers)} stocks")
            
            if len(valid_columns) == 0:
                raise ValueError("No valid columns in downloaded data")
                
            return price_data
            
        except Exception as e:
            print(f"Error downloading batch: {e}")
            retry_count -= 1
            if retry_count > 0:
                print(f"Retrying... {retry_count} attempts remaining")
                time.sleep(10)  # Increased wait time between retries
    
    print("Failed to download data after multiple attempts")
    return None

def calculate_indicators(price_data, config):
    """Calculate technical indicators with proper DataFrame alignment"""
    # Get OHLCV data and ensure single-level columns
    columns_needed = ['Close', 'Open', 'High', 'Low', 'Volume']
    df_dict = {col: price_data.get(col) for col in columns_needed}
    
    # Clean and align base data
    price = df_dict['Close'].dropna(axis=1)
    tickers = price.columns
    
    # Ensure all base DataFrames have same columns
    for key in df_dict:
        df_dict[key] = df_dict[key][tickers]
    
    # Calculate MAs on clean price data
    ma_windows = {
        'ma_fast': config.ma_fast,
        'ma_medium': config.ma_medium,
        'ma_slow': config.ma_slow
    }
    
    ma_dict = {
        name: vbt.MA.run(price, window=window).ma 
        for name, window in ma_windows.items()
    }
    
    # Ensure all MAs have same index and columns as price
    for ma_name in ma_dict:
        ma_dict[ma_name] = ma_dict[ma_name].reindex_like(price)
    
    # Calculate trend indicators
    highest_high_60d = df_dict['High'].rolling(config.flagpole_period).max()
    lowest_low_60d = df_dict['Low'].rolling(config.flagpole_period).min()
    flagpole_gain = (highest_high_60d / lowest_low_60d) - 1
    
    # Calculate other indicators
    consolidation_high = df_dict['High'].rolling(config.consolidation_window).max().shift(1)
    consolidation_low = df_dict['Low'].rolling(config.consolidation_window).min()
    
    # Generate signals with aligned DataFrames
    strong_uptrend = flagpole_gain > config.flagpole_min_gain
    near_highs = price > (highest_high_60d * 0.85)
    flagpole = strong_uptrend & near_highs
    
    # MA stacking (now with aligned DataFrames)
    ma_stacked = (
        (ma_dict['ma_fast'] > ma_dict['ma_medium']) & 
        (ma_dict['ma_medium'] > ma_dict['ma_slow'])
    )
    
    price_above_mas = (
        (price > ma_dict['ma_fast']) & 
        (price > ma_dict['ma_medium']) & 
        (price > ma_dict['ma_slow'])
    )
    
    # Other conditions
    consolidation_range = (consolidation_high / consolidation_low) - 1
    tight_range = consolidation_range < 0.20
    
    volatility = price.rolling(config.consolidation_window).std() / \
                price.rolling(config.consolidation_window).mean()
    low_volatility = volatility <= config.consolidation_volatility_threshold
    
    price_near_ma = (price / ma_dict['ma_medium'] - 1).abs() < 0.15
    
    volume_ma = df_dict['Volume'].rolling(config.consolidation_window).mean()
    volume_ratio = df_dict['Volume'] / volume_ma
    volume_confirmation = volume_ratio > 1.2
    
    breakout = price > consolidation_high
    
    daily_range = df_dict['High'] - df_dict['Low']
    close_position = (price - df_dict['Low']) / daily_range
    strong_close = close_position > 0.75
    
    # Combine entry conditions
    entries = (
        flagpole &
        ma_stacked &
        price_above_mas &
        tight_range &
        low_volatility &
        price_near_ma &
        breakout &
        volume_confirmation &
        strong_close
    )
    
    # Exit signals
    exits = price.vbt.crossed_below(ma_dict['ma_medium'])
    
    # Return aligned indicators
    return {
        'price': price,
        'ma_fast': ma_dict['ma_fast'],
        'ma_medium': ma_dict['ma_medium'],
        'ma_slow': ma_dict['ma_slow'],
        'entries': entries,
        'exits': exits,
        'high': df_dict['High'],
        'low': df_dict['Low'],
        'volume': df_dict['Volume']
    }
# --- BACKTEST ---
def run_backtest(indicators, config):
    price = indicators['price']
    entries = indicators['entries']
    exits = indicators['exits']

    portfolio = vbt.Portfolio.from_signals(
        close=price,
        entries=entries,
        exits=exits,
        sl_stop=config.max_stop_loss,
        fees=config.commission,
        freq='D',
        init_cash=100000,
        size=config.max_position_size,
        size_type='percent',
        group_by=True
    )
    return portfolio

# --- ANALYSIS ---
def analyze_results(portfolio, config):
    """Analyze and print backtest results with error handling"""
    stats = portfolio.stats()
    print("\n=== Backtest Results ===")
    print(stats)
    
    try:
        total_returns = portfolio.deep_getattr('total_return')
        
        if isinstance(total_returns, pd.Series):
            print("\n=== Trading Statistics ===")
            print(f"Number of stocks traded: {len(total_returns)}")
            print(f"Average return: {total_returns.mean():.2%}")
            print(f"Median return: {total_returns.median():.2%}")
            
            print("\n=== Top 5 Performing Stocks ===")
            top_5 = total_returns.nlargest(5)
            for ticker, ret in top_5.items():
                print(f"{ticker}: {ret:.2%}")
            
            print("\n=== Worst 5 Performing Stocks ===")
            bottom_5 = total_returns.nsmallest(5)
            for ticker, ret in bottom_5.items():
                print(f"{ticker}: {ret:.2%}")
        else:
            print("\nNo trades executed during the backtest period!")
            print("\nCurrent Parameters:")
            print(f"- Flagpole gain threshold: {config.flagpole_min_gain:.2%}")
            print(f"- Volatility threshold: {config.consolidation_volatility_threshold:.2%}")
            print(f"- Stop loss: {config.max_stop_loss:.2%}")
            print("\nSuggested Adjustments:")
            print("1. Decrease flagpole_min_gain to 0.15-0.20")
            print("2. Increase volatility_threshold to 0.4-0.5")
            print("3. Reduce MA alignment requirements")
            print("4. Consider longer date range")
    
    except Exception as e:
        print(f"\nError analyzing results: {str(e)}")
        print("No valid trades found in the backtest period")
    
    return stats

# Also update the plot_best_stock function to handle no-trade cases:
def plot_best_stock(portfolio, indicators):
    """Plot the best performing stock with error handling"""
    try:
        total_returns = portfolio.deep_getattr('total_return')
        
        if not isinstance(total_returns, pd.Series) or len(total_returns) == 0:
            print("\nNo valid trades to plot")
            return
            
        best_stock_symbol = total_returns.idxmax()
        print(f"\nPlotting trades for best performing stock: {best_stock_symbol}")
        
        price = indicators['price'][best_stock_symbol]
        ma_fast = indicators['ma_fast'][best_stock_symbol]
        ma_medium = indicators['ma_medium'][best_stock_symbol]
        ma_slow = indicators['ma_slow'][best_stock_symbol]
        
        # Create plot
        fig = price.vbt.plot(trace_kwargs=dict(name='Price'))
        fig.add_trace(ma_fast.vbt.plot(trace_kwargs=dict(name='MA10')).data[0])
        fig.add_trace(ma_medium.vbt.plot(trace_kwargs=dict(name='MA20')).data[0])
        fig.add_trace(ma_slow.vbt.plot(trace_kwargs=dict(name='MA50')).data[0])
        
        # Plot trades if any exist
        if portfolio[best_stock_symbol].trades.count() > 0:
            portfolio[best_stock_symbol].trades.plot(
                close=price,
                title=f'Trades for {best_stock_symbol}'
            ).show()
        else:
            fig.update_layout(title=f'Price and MAs for {best_stock_symbol} (No Trades)')
            fig.show()
            
    except Exception as e:
        print(f"\nError plotting results: {str(e)}")

# --- MAIN ---
def main():
    config = StrategyConfig()
    tickers = get_sp500_tickers()
    
    chunk_size = 50  # Reduced chunk size for better reliability
    all_indicators = {}
    
    print(f"Processing {len(tickers)} stocks in batches of {chunk_size}...")
    
    for i in range(0, len(tickers), chunk_size):
        batch_tickers = tickers[i:i+chunk_size]
        print(f"\nBatch {i//chunk_size + 1}: Processing stocks {i+1} to {min(i+chunk_size, len(tickers))}")
        
        batch_data = download_data(batch_tickers, config.start_date, config.end_date)
        if batch_data is None:
            print(f"Skipping batch {i//chunk_size + 1} due to download failure")
            continue
            
        try:
            batch_indicators = calculate_indicators(batch_data, config)
            if batch_indicators:
                all_indicators.update(batch_indicators)
        except Exception as e:
            print(f"Error processing batch: {e}")
            continue
    
    if not all_indicators:
        print("No data could be processed. Exiting.")
        return
        
    portfolio = run_backtest(all_indicators, config)
    analyze_results(portfolio, config)
    plot_best_stock(portfolio, all_indicators)

if __name__ == "__main__":
    main()
