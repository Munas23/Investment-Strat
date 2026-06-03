"""
Simple Optimized Flag Strategy - Using proven working approach from both3.py
with optimized parameters from your results
"""

import warnings
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime
import time

warnings.filterwarnings('ignore')

class OptimizedConfig:
    """Optimized parameters from your backtesting results"""
    # Best performing parameters from optimization_results.csv
    flagpole_period = 60
    flagpole_min_gain = 0.15          # 15% (best performer)
    
    # Best MA configuration (5/20/60)
    ma_fast = 5
    ma_medium = 20
    ma_slow = 60
    
    consolidation_window = 20
    consolidation_volatility_threshold = 0.3
    
    # Optimized risk parameters
    max_stop_loss = 0.08              # 8% stop loss
    max_position_size = 0.15          # 15% position size (best return: 46%)
    commission = 0.001
    
    start_date = '2020-01-01'         # Shorter period for reliability
    end_date = '2023-12-31'

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
    """Using the exact working method from both3.py"""
    print(f"Downloading data for {len(tickers)} stocks from {start} to {end}...")
    
    # Filter out problematic tickers
    filtered_tickers = [t for t in tickers if not t.startswith('$')]
    if len(filtered_tickers) < len(tickers):
        print(f"Filtered out {len(tickers) - len(filtered_tickers)} invalid tickers")
    
    retry_count = 3
    while retry_count > 0:
        try:
            # Download in smaller sub-batches
            batch_size = 25
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
    """Using exact method from both3.py with optimized parameters"""
    try:
        print(f"Initial data shape: Close={price_data.get('Close').shape}")
        
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
        
        # Calculate MAs with OPTIMIZED PERIODS (5/20/60)
        print("Calculating moving averages with optimized periods...")
        ma_fast = vbt.MA.run(close, window=config.ma_fast).ma
        ma_medium = vbt.MA.run(close, window=config.ma_medium).ma
        ma_slow = vbt.MA.run(close, window=config.ma_slow).ma
        
        # Handle MultiIndex columns
        def fix_ma_columns(ma_df):
            if isinstance(ma_df.columns, pd.MultiIndex):
                ma_df.columns = ma_df.columns.get_level_values(-1)
            return ma_df
        
        ma_fast = fix_ma_columns(ma_fast)
        ma_medium = fix_ma_columns(ma_medium)
        ma_slow = fix_ma_columns(ma_slow)
        
        # Align MAs
        ma_index = ma_fast.index.intersection(ma_medium.index).intersection(ma_slow.index)
        ma_cols = ma_fast.columns.intersection(ma_medium.columns).intersection(ma_slow.columns)
        
        print(f"MA alignment - Index length: {len(ma_index)}, Columns: {len(ma_cols)}")
        
        if len(ma_cols) == 0:
            print("Error: No common columns found after MA calculation")
            return None
        
        # Align MAs and data
        ma_fast = ma_fast.loc[ma_index, ma_cols]
        ma_medium = ma_medium.loc[ma_index, ma_cols]
        ma_slow = ma_slow.loc[ma_index, ma_cols]
        
        close = close.loc[ma_index, ma_cols]
        high = high.loc[ma_index, ma_cols]
        low = low.loc[ma_index, ma_cols]
        volume = volume.loc[ma_index, ma_cols]
        
        print(f"Final aligned data shape: {close.shape}")
        
        # Calculate trend indicators
        print("Calculating trend indicators...")
        
        # Calculate trend gain (optimized 15% threshold)
        high_max = high.rolling(window=config.flagpole_period, min_periods=1).max()
        low_min = low.rolling(window=config.flagpole_period, min_periods=1).min()
        trend_gain = (high_max / low_min - 1)
        
        # Calculate consolidation volatility
        price_std = close.rolling(window=config.consolidation_window, min_periods=1).std()
        price_mean = close.rolling(window=config.consolidation_window, min_periods=1).mean()
        volatility_ratio = price_std / price_mean
        
        # Calculate volume average
        volume_avg = volume.rolling(window=config.consolidation_window, min_periods=1).mean()
        
        # Generate entry conditions with OPTIMIZED parameters
        print("Generating optimized entry signals...")
        
        trend_cond = trend_gain > config.flagpole_min_gain  # 15% threshold
        highs_cond = close > (high_max * 0.75)
        ma_cond1 = ma_fast > (ma_medium * 0.98)
        ma_cond2 = ma_medium > (ma_slow * 0.98)
        vol_cond = volatility_ratio < config.consolidation_volatility_threshold
        volume_cond = volume > volume_avg
        
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
        
        print(f"Successfully processed {len(ma_cols)} stocks")
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
    """Using exact method from both3.py with optimized parameters"""
    price = indicators['price']
    entries = indicators['entries']
    exits = indicators['exits']

    print("\nBacktest Summary:")
    print(f"Total stocks analyzed: {len(price.columns)}")
    print(f"Date range: {price.index[0]} to {price.index[-1]}")
    print(f"Total entry signals: {entries.sum().sum()}")
    print(f"Total exit signals: {exits.sum().sum()}")

    # Data cleaning for VectorBT compatibility
    def clean_dataframe_for_numba(df, name):
        print(f"Cleaning {name} - Original shape: {df.shape}, dtype: {df.dtypes.unique()}")
        
        # Convert to appropriate types
        if name in ['price', 'ma_fast', 'ma_medium', 'ma_slow']:
            df = df.astype('float64')
        elif name in ['entries', 'exits']:
            df = df.astype('bool')
        
        # Remove timezone for compatibility
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Ensure string columns
        df.columns = df.columns.astype(str)
        
        # Handle NaN values
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
        
        # Create portfolio with OPTIMIZED PARAMETERS
        portfolio = vbt.Portfolio.from_signals(
            close=price,
            entries=entries,
            exits=exits,
            sl_stop=config.max_stop_loss,        # 8% stop loss (optimized)
            fees=config.commission,
            freq='D',
            init_cash=100000.0,
            size=config.max_position_size,       # 15% position size (best performer)
            size_type='percent',
            group_by=True,
            cash_sharing=True,
            call_seq='auto'
        )
        
        print("Portfolio created successfully with optimized parameters!")
        return portfolio
        
    except Exception as e:
        print(f"Error creating portfolio: {e}")
        print("Attempting fallback approach...")
        
        # Fallback: simpler parameters
        try:
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
            return None

def analyze_results(portfolio, config):
    """Enhanced analysis with optimized parameter context"""
    if portfolio is None:
        print("No portfolio to analyze - backtest failed")
        return None
        
    try:
        stats = portfolio.stats()
        print("\n" + "="*60)
        print("OPTIMIZED FLAG PATTERN STRATEGY RESULTS")
        print("="*60)
        print(f"Optimized Parameters Used:")
        print(f"  MA Configuration: {config.ma_fast}/{config.ma_medium}/{config.ma_slow}")
        print(f"  Flagpole Threshold: {config.flagpole_min_gain:.0%}")
        print(f"  Position Size: {config.max_position_size:.0%}")
        print(f"  Stop Loss: {config.max_stop_loss:.0%}")
        print("\nPerformance Results:")
        print(stats)
        
    except Exception as e:
        print(f"Error getting portfolio stats: {e}")
        return None
    
    # Check for trades
    if portfolio.trades.count() == 0:
        print("\nNo trades were executed during the backtest period!")
        print("Consider adjusting parameters for more opportunities")
        return stats
            
    try:
        # Enhanced trade analysis
        trades_df = pd.DataFrame(portfolio.trades.records)
        tickers = portfolio.close.columns
        trades_df['Ticker'] = tickers[trades_df['col']]
        
        # Calculate P&L per stock
        stock_pnl = trades_df.groupby('Ticker')['pnl'].sum()

        if not stock_pnl.empty:
            print(f"\n=== TRADING STATISTICS ===")
            print(f"Total Trades: {portfolio.trades.count()}")
            print(f"Stocks with Trades: {len(stock_pnl)}")
            print(f"Win Rate: {portfolio.trades.win_rate():.1%}")
            print(f"Average Trade Return: {portfolio.trades.returns.mean():.2%}")
            print(f"Best Trade: {portfolio.trades.returns.max():.2%}")
            print(f"Worst Trade: {portfolio.trades.returns.min():.2%}")
            
            print(f"\n=== TOP 5 PERFORMING STOCKS ===")
            top_5 = stock_pnl.nlargest(5)
            for ticker, pnl in top_5.items():
                print(f"{ticker}: ${pnl:,.2f}")
        
    except Exception as e:
        print(f"\nError in detailed analysis: {e}")
    
    return stats

def main():
    """Main execution with optimized parameters"""
    print("Starting Simple Optimized Flag Strategy...")
    print("Using best parameters from optimization results:")
    print("- MA(5/20/60) configuration")
    print("- 15% flagpole threshold") 
    print("- 15% position size")
    print("- 8% stop loss")
    
    config = OptimizedConfig()
    tickers = get_sp500_tickers()
    
    # Test with smaller set for reliability
    test_tickers = tickers[:50]  # First 50 stocks
    print(f"Testing with first {len(test_tickers)} S&P 500 stocks")
    
    # Download data
    raw_data = download_data(test_tickers, config.start_date, config.end_date)
    if raw_data is None:
        print("Data download failed")
        return
    
    # Calculate indicators
    indicators = calculate_indicators(raw_data, config)
    if indicators is None:
        print("Indicator calculation failed")
        return
    
    # Run backtest
    portfolio = run_backtest(indicators, config)
    if portfolio is None:
        print("Backtest failed")
        return
    
    # Analyze results
    results = analyze_results(portfolio, config)
    
    # Export trades
    try:
        if portfolio.trades.count() > 0:
            trades_df = pd.DataFrame(portfolio.trades.records)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simple_optimized_trades_{timestamp}.csv"
            trades_df.to_csv(filename, index=False)
            print(f"\nTrades exported to: {filename}")
    except Exception as e:
        print(f"Export failed: {e}")
    
    print("\nBacktest completed!")
    return portfolio, indicators, results

if __name__ == "__main__":
    main()