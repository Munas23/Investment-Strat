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
    # Trend Detection
    flagpole_period = 60        # How far back to look for trend (days)
    flagpole_min_gain = 0.15    # Minimum price increase required (15%)
    
    # Moving Averages
    ma_fast = 10               # Fast MA period
    ma_medium = 20            # Medium MA period
    ma_slow = 50             # Slow MA period
    
    # Consolidation/Volatility
    consolidation_window = 20                    # Days to check for consolidation
    consolidation_volatility_threshold = 0.6     # Maximum allowed volatility
    
    # Risk Management
    max_stop_loss = 0.08        # 8% stop loss
    min_stop_loss = 0.02        # 2% minimum stop
    max_position_size = 0.10    # 10% max position size
    commission = 0.001          # 0.1% commission per trade
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
    """Download data with improved error handling and filtering"""
    print(f"Downloading data for {len(tickers)} stocks from {start} to {end}...")
    
    # Filter out problematic tickers
    filtered_tickers = [t for t in tickers if not t.startswith('$')]
    if len(filtered_tickers) < len(tickers):
        print(f"Filtered out {len(tickers) - len(filtered_tickers)} invalid tickers")
    
    retry_count = 3
    while retry_count > 0:
        try:
            # Download in smaller sub-batches
            batch_size = 25  # Reduced from 50
            all_data = {}
            
            for i in range(0, len(filtered_tickers), batch_size):
                sub_batch = filtered_tickers[i:i+batch_size]
                try:
                    data = vbt.YFData.download(
                        sub_batch,
                        start=start,
                        end=end,
                        missing_index='drop'
                    )
                    
                    if data is not None:
                        # Verify data quality for each ticker
                        close_data = data.get('Close')
                        valid_cols = close_data.columns[close_data.count() > 250]  # At least 1 year of data
                        if len(valid_cols) > 0:
                            for col in ['Close', 'High', 'Low', 'Volume']:
                                all_data[col] = pd.concat([all_data.get(col, pd.DataFrame()), 
                                                         data.get(col)[valid_cols]], axis=1)
                    
                except Exception as e:
                    print(f"Error in sub-batch {i//batch_size + 1}: {e}")
                    continue
                    
            if not all_data:
                raise ValueError("No valid data downloaded")
                
            # Verify overall data quality
            actual_start = all_data['Close'].index[0]
            actual_end = all_data['Close'].index[-1]
            expected_days = (pd.to_datetime(end) - pd.to_datetime(start)).days
            actual_days = (actual_end - actual_start).days
            
            print(f"Downloaded data for {all_data['Close'].shape[1]} stocks")
            print(f"Date range: {actual_start} to {actual_end} ({actual_days} days)")
            
            if actual_days < expected_days * 0.9:
                print("Warning: Got significantly less data than expected")
                retry_count -= 1
                continue
                
            return all_data
            
        except Exception as e:
            print(f"Error downloading batch: {e}")
            retry_count -= 1
            if retry_count > 0:
                print(f"Retrying... {retry_count} attempts remaining")
                time.sleep(10)
    
    return None

def calculate_indicators(price_data, config):
    """Calculate technical indicators with proper DataFrame alignment"""
    try:
        # Debug data quality
        print(f"Initial data shape: Close={price_data.get('Close').shape}")
        
        # Extract and clean OHLCV data with validation
        def clean_and_validate_df(df, name):
            if df is None:
                raise ValueError(f"Missing {name} data")
            if isinstance(df.columns, pd.MultiIndex):
                df = df.copy()
                df.columns = df.columns.get_level_values(-1)
            # Remove columns with >50% NaN values
            valid_cols = df.columns[df.isna().mean() < 0.5]
            if len(valid_cols) == 0:
                raise ValueError(f"No valid columns in {name} after NaN filtering")
            return df[valid_cols]
        
        # Clean individual DataFrames
        close = clean_and_validate_df(price_data.get('Close'), 'Close')
        high = clean_and_validate_df(price_data.get('High'), 'High')
        low = clean_and_validate_df(price_data.get('Low'), 'Low')
        volume = clean_and_validate_df(price_data.get('Volume'), 'Volume')
        
        # Find common valid columns across all DataFrames
        common_cols = close.columns
        for df in [high, low, volume]:
            common_cols = common_cols.intersection(df.columns)
            
        print(f"Common valid columns: {len(common_cols)}")
        if len(common_cols) == 0:
            raise ValueError("No common valid columns across OHLCV data")
            
        # Align all DataFrames to common columns and index
        close = close[common_cols]
        high = high[common_cols]
        low = low[common_cols]
        volume = volume[common_cols]
        
        # Get common index
        common_index = close.index
        for df in [high, low, volume]:
            common_index = common_index.intersection(df.index)
        
        # Reindex all DataFrames to common index
        close = close.loc[common_index]
        high = high.loc[common_index]
        low = low.loc[common_index]
        volume = volume.loc[common_index]
        
        # Handle NaN values
        for df_name, df in [('close', close), ('high', high), ('low', low), ('volume', volume)]:
            if df.isna().any().any():
                print(f"Filling NaN values in {df_name}")
                df.fillna(method='ffill', inplace=True)
                df.fillna(method='bfill', inplace=True)
        
        # Calculate MAs with explicit alignment
        print("Calculating moving averages...")
        ma_fast = vbt.MA.run(close, window=config.ma_fast).ma
        ma_medium = vbt.MA.run(close, window=config.ma_medium).ma
        ma_slow = vbt.MA.run(close, window=config.ma_slow).ma
        
        # FIX: Handle MultiIndex columns in MAs
        def fix_ma_columns(ma_df):
            """Convert MultiIndex columns to simple string columns"""
            if isinstance(ma_df.columns, pd.MultiIndex):
                # Extract just the symbol names (second level of MultiIndex)
                ma_df.columns = ma_df.columns.get_level_values(-1)
            return ma_df
        
        ma_fast = fix_ma_columns(ma_fast)
        ma_medium = fix_ma_columns(ma_medium)
        ma_slow = fix_ma_columns(ma_slow)
        
        # Debug MA shapes after column fix
        print(f"MA shapes after column fix - Fast: {ma_fast.shape}, Medium: {ma_medium.shape}, Slow: {ma_slow.shape}")
        print(f"MA columns after fix - Fast: {list(ma_fast.columns)[:5]}...")  # Show first 5
        
        # Ensure all MAs have the same index and columns
        print("Aligning moving averages...")
        ma_index = ma_fast.index.intersection(ma_medium.index).intersection(ma_slow.index)
        ma_cols = ma_fast.columns.intersection(ma_medium.columns).intersection(ma_slow.columns)
        
        print(f"MA alignment - Index length: {len(ma_index)}, Columns: {len(ma_cols)}")
        
        # Verify we have valid columns
        if len(ma_cols) == 0:
            print("Error: No common columns found after MA calculation")
            print(f"Fast MA columns: {list(ma_fast.columns)}")
            print(f"Medium MA columns: {list(ma_medium.columns)}")
            print(f"Slow MA columns: {list(ma_slow.columns)}")
            return None
        
        # Align MAs to common index and columns
        ma_fast = ma_fast.loc[ma_index, ma_cols]
        ma_medium = ma_medium.loc[ma_index, ma_cols]
        ma_slow = ma_slow.loc[ma_index, ma_cols]
        
        # Align all data to MA dimensions (since MAs will be shorter due to rolling windows)
        final_index = ma_index
        final_cols = ma_cols
        
        # Ensure the close data columns match the MA columns
        available_close_cols = close.columns.intersection(final_cols)
        if len(available_close_cols) == 0:
            print("Error: No matching columns between close data and MAs")
            print(f"Close columns: {list(close.columns)}")
            print(f"MA columns: {list(final_cols)}")
            return None
        
        final_cols = available_close_cols
        
        close = close.loc[final_index, final_cols]
        high = high.loc[final_index, final_cols]
        low = low.loc[final_index, final_cols]
        volume = volume.loc[final_index, final_cols]
        
        # Re-align MAs to the final columns
        ma_fast = ma_fast.loc[final_index, final_cols]
        ma_medium = ma_medium.loc[final_index, final_cols]
        ma_slow = ma_slow.loc[final_index, final_cols]
        
        print(f"Final aligned data shape: {close.shape}")
        print(f"MA shapes - Fast: {ma_fast.shape}, Medium: {ma_medium.shape}, Slow: {ma_slow.shape}")
        
        # Calculate trend indicators with aligned data
        print("Calculating trend indicators...")
        
        # For rolling calculations, we need to ensure we have enough data
        min_periods = max(config.flagpole_period, config.consolidation_window)
        if len(final_index) < min_periods:
            raise ValueError(f"Not enough data points. Need at least {min_periods}, got {len(final_index)}")
        
        # Calculate trend gain
        high_max = high.rolling(window=config.flagpole_period, min_periods=1).max()
        low_min = low.rolling(window=config.flagpole_period, min_periods=1).min()
        trend_gain = (high_max / low_min - 1)
        
        # Calculate consolidation volatility
        price_std = close.rolling(window=config.consolidation_window, min_periods=1).std()
        price_mean = close.rolling(window=config.consolidation_window, min_periods=1).mean()
        volatility_ratio = price_std / price_mean
        
        # Calculate volume average
        volume_avg = volume.rolling(window=config.consolidation_window, min_periods=1).mean()
        
        # Generate entry conditions with proper alignment
        print("Generating entry signals...")
        
        # All conditions must have the same shape
        trend_cond = trend_gain > config.flagpole_min_gain
        highs_cond = close > (high_max * 0.75)
        ma_cond1 = ma_fast > (ma_medium * 0.98)
        ma_cond2 = ma_medium > (ma_slow * 0.98)
        vol_cond = volatility_ratio < config.consolidation_volatility_threshold
        volume_cond = volume > volume_avg
        
        # Verify all conditions have the same shape
        shapes = [cond.shape for cond in [trend_cond, highs_cond, ma_cond1, ma_cond2, vol_cond, volume_cond]]
        if not all(shape == shapes[0] for shape in shapes):
            print(f"Warning: Condition shapes don't match: {shapes}")
            raise ValueError("Condition DataFrames have misaligned shapes")
        
        # Combine conditions
        entries = (
            trend_cond &
            highs_cond &
            ma_cond1 &
            ma_cond2 &
            vol_cond &
            volume_cond
        )
        
        exits = close < ma_medium
        
        # Final cleanup
        entries = entries.fillna(False)
        exits = exits.fillna(False)
        
        print(f"Successfully processed {len(final_cols)} stocks")
        print(f"Found {entries.sum().sum()} entry signals")
        print(f"Found {exits.sum().sum()} exit signals")
        
        return {
            'price': close,
            'ma_fast': ma_fast,
            'ma_medium': ma_medium,
            'ma_slow': ma_slow,
            'entries': entries,
            'exits': exits,
            'high': high,
            'low': low,
            'volume': volume
        }
        
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        import traceback
        print("Stack trace:", traceback.format_exc())
        return None

def run_backtest(indicators, config):
    """Run backtest with proper timezone handling"""
    price = indicators['price']
    entries = indicators['entries']
    exits = indicators['exits']

    # Validate date range with timezone handling
    date_range = price.index
    start_dt = pd.to_datetime(config.start_date).tz_localize('UTC')
    end_dt = pd.to_datetime(config.end_date).tz_localize('UTC')
    
    # Convert date_range to UTC if it has a different timezone
    if date_range.tz is not None and date_range.tz != 'UTC':
        date_range = date_range.tz_convert('UTC')
    elif date_range.tz is None:
        date_range = date_range.tz_localize('UTC')
    
    if date_range[0] > start_dt or date_range[-1] < end_dt:
        print("\nWarning: Data range doesn't match configuration:")
        print(f"Config range: {start_dt} to {end_dt}")
        print(f"Actual range: {date_range[0]} to {date_range[-1]}")
    
    # Add debug info
    print("\nBacktest Summary:")
    print(f"Total stocks analyzed: {len(price.columns)}")
    print(f"Date range: {date_range[0]} to {date_range[-1]}")
    print(f"Total entry signals: {entries.sum().sum()}")
    print(f"Total exit signals: {exits.sum().sum()}")

    # ... rest of existing run_backtest code ...
    
    # Check if we have any data to work with
    if len(price.columns) == 0:
        print("Error: No stocks available for backtesting!")
        return None
        
    print(f"Date range: {price.index[0]} to {price.index[-1]}")
    print(f"Total entry signals: {entries.sum().sum()}")
    print(f"Total exit signals: {exits.sum().sum()}")

    # FIX: Ensure all data has consistent types for Numba
    def clean_dataframe_for_numba(df, name):
        """Clean DataFrame for VectorBT/Numba compatibility"""
        print(f"Cleaning {name} - Original shape: {df.shape}, dtype: {df.dtypes.unique()}")
        
        # Convert to float64 for numeric data
        if name in ['price', 'ma_fast', 'ma_medium', 'ma_slow']:
            df = df.astype('float64')
        # Convert to bool for signal data
        elif name in ['entries', 'exits']:
            df = df.astype('bool')
        
        # Reset index to DatetimeIndex without timezone for compatibility
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Ensure column names are strings
        df.columns = df.columns.astype(str)
        
        # Handle any remaining NaN values
        if name in ['entries', 'exits']:
            df = df.fillna(False)
        else:
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0.0)
        
        print(f"Cleaned {name} - Final shape: {df.shape}, dtype: {df.dtypes.unique()}")
        return df

    try:
        # Clean all DataFrames
        price = clean_dataframe_for_numba(price.copy(), 'price')
        entries = clean_dataframe_for_numba(entries.copy(), 'entries')
        exits = clean_dataframe_for_numba(exits.copy(), 'exits')
        
        # Verify data alignment
        assert price.shape == entries.shape == exits.shape, "DataFrames must have same shape"
        assert price.index.equals(entries.index) and price.index.equals(exits.index), "Indices must match"
        assert list(price.columns) == list(entries.columns) == list(exits.columns), "Columns must match"
        
        print(f"Data verification passed - Shape: {price.shape}")
        print(f"Price range: {price.min().min():.2f} to {price.max().max():.2f}")
        print(f"Entry signals per stock: {entries.sum().describe()}")
        
        # Create portfolio with explicit parameters
        portfolio = vbt.Portfolio.from_signals(
            close=price,
            entries=entries,
            exits=exits,
            sl_stop=config.max_stop_loss,
            fees=config.commission,
            freq='D',
            init_cash=100000.0,  # Explicit float
            size=config.max_position_size,  # This should be a float between 0 and 1
            size_type='percent',
            group_by=True,  # Group all columns together
            cash_sharing=True,  # Enable cash sharing across assets
            call_seq='auto'  # Let VectorBT optimize call sequence
        )
        
        print("Portfolio created successfully!")
        return portfolio
        
    except Exception as e:
        print(f"Error creating portfolio: {e}")
        print("Attempting fallback approach...")
        
        # Fallback: Try with simpler parameters
        try:
            # More conservative approach
            portfolio = vbt.Portfolio.from_signals(
                close=price,
                entries=entries,
                exits=exits,
                fees=config.commission,
                freq='D',
                init_cash=100000.0
            )
            print("Portfolio created with fallback approach!")
            return portfolio
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            
            # Debug information
            print("\nDebugging information:")
            print(f"Price DataFrame info:")
            print(f"  - Shape: {price.shape}")
            print(f"  - Index type: {type(price.index)}")
            print(f"  - Column type: {type(price.columns)}")
            print(f"  - Data types: {price.dtypes.unique()}")
            print(f"  - Has NaN: {price.isna().any().any()}")
            print(f"  - Sample values: {price.iloc[0, 0]}")
            
            print(f"Entries DataFrame info:")
            print(f"  - Shape: {entries.shape}")
            print(f"  - Data types: {entries.dtypes.unique()}")
            print(f"  - Has NaN: {entries.isna().any().any()}")
            print(f"  - Sample values: {entries.iloc[0, 0]}")
            
            return None

def combine_batch_data(all_batch_results):
    """Combine results from multiple batches with improved data handling"""
    if not all_batch_results:
        return None
    
    print(f"Combining data from {len(all_batch_results)} batches...")
    
    # Initialize combined dictionaries
    combined = {}
    
    # Get all keys from first batch
    keys = all_batch_results[0].keys()
    
    for key in keys:
        # Combine DataFrames horizontally (by columns)
        dfs_to_combine = [batch[key] for batch in all_batch_results if key in batch and not batch[key].empty]
        
        if dfs_to_combine:
            # Ensure all DataFrames have the same index before concatenating
            common_index = dfs_to_combine[0].index
            for df in dfs_to_combine[1:]:
                common_index = common_index.intersection(df.index)
            
            # Reindex all DataFrames to common index
            aligned_dfs = []
            for df in dfs_to_combine:
                aligned_df = df.loc[common_index]
                aligned_dfs.append(aligned_df)
            
            # Concatenate along columns (axis=1)
            combined[key] = pd.concat(aligned_dfs, axis=1, sort=False)
            print(f"Combined {key}: {combined[key].shape}")
        else:
            # Create empty DataFrame with proper structure if no data
            print(f"Warning: No data to combine for {key}")
            if all_batch_results:
                # Use the structure from the first batch even if empty
                sample_df = all_batch_results[0][key]
                combined[key] = pd.DataFrame(index=sample_df.index, columns=[])
    
    # Check if we have any actual data
    total_stocks = combined.get('price', pd.DataFrame()).shape[1] if 'price' in combined else 0
    if total_stocks == 0:
        print("Warning: No stocks successfully processed across all batches!")
        return None
    
    return combined

# --- ANALYSIS ---
def analyze_results(portfolio, config):
    """Analyze and print backtest results with error handling"""
    if portfolio is None:
        print("No portfolio to analyze - backtest failed")
        return None
        
    try:
        stats = portfolio.stats()
        print("\n=== Backtest Results ===")
        print(stats)
    except Exception as e:
        print(f"Error getting portfolio stats: {e}")
        return None
    
    try:
        total_returns = portfolio.deep_getattr('total_return')
        
        if isinstance(total_returns, pd.Series) and len(total_returns) > 0:
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
            print("1. Decrease flagpole_min_gain to 0.10-0.15")
            print("2. Increase volatility_threshold to 0.8-1.0")
            print("3. Reduce MA alignment requirements")
            print("4. Consider longer date range")
    
    except Exception as e:
        print(f"\nError analyzing results: {str(e)}")
        print("No valid trades found in the backtest period")
    
    return stats

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
    
    # Validate configuration dates
    try:
        start_dt = pd.to_datetime(config.start_date)
        end_dt = pd.to_datetime(config.end_date)
        min_days = 252  # Minimum 1 year of data
        if (end_dt - start_dt).days < min_days:
            print(f"Warning: Date range less than {min_days} days")
    except Exception as e:
        print(f"Date configuration error: {e}")
        return
    
    print(f"\nBacktesting from {config.start_date} to {config.end_date}")
    # ... rest of main function code ...
    tickers = get_sp500_tickers()
    
    chunk_size = 50  # Reduced chunk size for better reliability
    all_batch_results = []
    
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
            if batch_indicators and batch_indicators['price'].shape[1] > 0:
                all_batch_results.append(batch_indicators)
                print(f"Successfully processed batch {i//chunk_size + 1} with {batch_indicators['price'].shape[1]} stocks")
            else:
                print(f"Batch {i//chunk_size + 1} resulted in no valid stocks")
        except Exception as e:
            print(f"Error processing batch {i//chunk_size + 1}: {e}")
            continue
    
    if not all_batch_results:
        print("No data could be processed. Exiting.")
        return
    
    # Combine all batch results
    print("\nCombining all batch results...")
    combined_indicators = combine_batch_data(all_batch_results)
    
    if combined_indicators is None:
        print("Failed to combine batch results. Exiting.")
        return
    
    # Additional check for empty data
    if combined_indicators['price'].shape[1] == 0:
        print("No valid stock data after processing all batches.")
        print("This could be due to:")
        print("1. All stocks being filtered out during data cleaning")
        print("2. Moving average alignment issues")
        print("3. Data download problems")
        return
        
    print(f"\nFinal combined data:")
    print(f"Total stocks: {combined_indicators['price'].shape[1]}")
    print(f"Date range: {combined_indicators['price'].index[0]} to {combined_indicators['price'].index[-1]}")
    
    portfolio = run_backtest(combined_indicators, config)
    if portfolio is not None:
        analyze_results(portfolio, config)
        plot_best_stock(portfolio, combined_indicators)
    else:
        print("Backtest failed - no portfolio created")

if __name__ == "__main__":
    main()