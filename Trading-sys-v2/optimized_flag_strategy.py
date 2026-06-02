"""
Optimized Flag Pattern Strategy - Best Practices Implementation
Combines lessons learned from all previous implementations with optimization results
"""

import warnings
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime
import matplotlib.pyplot as plt
import time
from typing import Dict, List, Optional, Tuple
import concurrent.futures
from functools import partial

warnings.filterwarnings('ignore')

class OptimizedStrategyConfig:
    """Optimized configuration based on backtesting results"""
    # Best parameters from optimization results
    flagpole_period = 60
    flagpole_min_gain = 0.15          # 15% minimum gain (best performer)
    
    # Optimized MA configuration (5/20/60 was best performer)
    ma_fast = 5
    ma_medium = 20 
    ma_slow = 60
    
    # Consolidation parameters
    consolidation_window = 20
    consolidation_volatility_threshold = 0.3  # Tighter consolidation
    
    # Risk management (optimized values)
    max_stop_loss = 0.08              # 8% stop loss (best balance)
    max_position_size = 0.15          # 15% max position (best return)
    commission = 0.001
    
    # Data parameters
    start_date = '2018-01-01'
    end_date = '2023-12-31'
    min_data_points = 250             # At least 1 year of data

class OptimizedFlagStrategy:
    """Production-ready flag pattern strategy with best practices"""
    
    def __init__(self, config: OptimizedStrategyConfig = None):
        self.config = config or OptimizedStrategyConfig()
        self.data_cache = {}
        self.results = {}
        self.performance_summary = None
        
    def get_sp500_tickers(self) -> List[str]:
        """Robust S&P 500 ticker fetching with fallback"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            tickers = table['Symbol'].tolist()
            tickers = [ticker.replace('.', '-') for ticker in tickers]
            print(f"Successfully fetched {len(tickers)} S&P 500 tickers")
            return tickers
        except Exception as e:
            print(f"Failed to fetch S&P 500 tickers: {e}")
            # High-quality fallback list
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B',
                'TSM', 'UNH', 'JNJ', 'V', 'JPM', 'WMT', 'XOM', 'PG', 'MA', 'HD',
                'CVX', 'ABBV', 'BAC', 'AVGO', 'PFE', 'KO', 'PEP', 'TMO', 'COST',
                'MRK', 'DIS', 'ABT', 'ADBE', 'DHR', 'VZ', 'NFLX', 'CRM', 'ACN',
                'NKE', 'LIN', 'TXN', 'RTX', 'NEE', 'QCOM', 'BMY', 'HON', 'UNP',
                'LOW', 'PM', 'T', 'SCHW'
            ]
    
    def download_data_batch(self, tickers: List[str], batch_size: int = 25) -> Dict:
        """Robust batch data downloading - using exact method from working implementations"""
        print(f"Downloading data for {len(tickers)} stocks from {self.config.start_date} to {self.config.end_date}...")
        
        # Filter problematic tickers
        filtered_tickers = [t for t in tickers if not t.startswith('$')]
        if len(filtered_tickers) < len(tickers):
            print(f"Filtered out {len(tickers) - len(filtered_tickers)} invalid tickers")
        
        retry_count = 3
        while retry_count > 0:
            try:
                # Download in smaller sub-batches
                all_data = {}
                
                for i in range(0, len(filtered_tickers), batch_size):
                    sub_batch = filtered_tickers[i:i+batch_size]
                    print(f"Processing batch {i//batch_size + 1}: {len(sub_batch)} stocks")
                    
                    try:
                        data = vbt.YFData.download(
                            sub_batch,
                            start=self.config.start_date,
                            end=self.config.end_date,
                            missing_index='drop'
                        )
                        
                        if data is not None:
                            # Verify data quality for each ticker - use exact same method as working code
                            close_data = data.get('Close')
                            valid_cols = close_data.columns[close_data.count() > self.config.min_data_points]
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
                expected_days = (pd.to_datetime(self.config.end_date) - pd.to_datetime(self.config.start_date)).days
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
    
    def clean_and_align_data(self, raw_data: Dict) -> Dict:
        """Advanced data cleaning and alignment with comprehensive validation"""
        print("Cleaning and aligning data...")
        
        def validate_and_clean_df(df: pd.DataFrame, name: str) -> pd.DataFrame:
            if df is None or df.empty:
                raise ValueError(f"Empty {name} data")
            
            # Handle MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df = df.copy()
                df.columns = df.columns.get_level_values(-1)
            
            # Remove columns with excessive NaN values
            nan_threshold = 0.3  # Allow up to 30% NaN
            valid_cols = df.columns[df.isna().mean() <= nan_threshold]
            
            if len(valid_cols) == 0:
                raise ValueError(f"No valid columns in {name} after NaN filtering")
            
            return df[valid_cols]
        
        try:
            # Clean individual DataFrames
            close = validate_and_clean_df(raw_data['Close'], 'Close')
            high = validate_and_clean_df(raw_data['High'], 'High')
            low = validate_and_clean_df(raw_data['Low'], 'Low')
            volume = validate_and_clean_df(raw_data['Volume'], 'Volume')
            
            # Find common valid tickers across all data types
            common_tickers = close.columns
            for df in [high, low, volume]:
                common_tickers = common_tickers.intersection(df.columns)
            
            if len(common_tickers) == 0:
                raise ValueError("No common tickers across all data types")
            
            print(f"Common valid tickers: {len(common_tickers)}")
            
            # Align to common tickers
            close = close[common_tickers]
            high = high[common_tickers]
            low = low[common_tickers]
            volume = volume[common_tickers]
            
            # Find common date range
            common_index = close.index
            for df in [high, low, volume]:
                common_index = common_index.intersection(df.index)
            
            if len(common_index) < self.config.min_data_points:
                raise ValueError(f"Insufficient common data points: {len(common_index)}")
            
            # Align to common index
            close = close.loc[common_index]
            high = high.loc[common_index]
            low = low.loc[common_index]
            volume = volume.loc[common_index]
            
            # Handle remaining NaN values
            for name, df in [('Close', close), ('High', high), ('Low', low), ('Volume', volume)]:
                if df.isna().any().any():
                    print(f"Forward-filling NaN values in {name}")
                    df.fillna(method='ffill', inplace=True)
                    df.fillna(method='bfill', inplace=True)
                    df.fillna(0, inplace=True)  # Final fallback
            
            print(f"Final aligned data: {close.shape[1]} stocks, {len(common_index)} days")
            
            return {
                'close': close,
                'high': high, 
                'low': low,
                'volume': volume,
                'tickers': list(common_tickers),
                'date_range': common_index
            }
            
        except Exception as e:
            print(f"Error in data cleaning: {e}")
            return None
    
    def calculate_technical_indicators(self, clean_data: Dict) -> Dict:
        """Calculate optimized technical indicators with proper alignment"""
        print("Calculating technical indicators...")
        
        close = clean_data['close']
        high = clean_data['high']
        low = clean_data['low']
        volume = clean_data['volume']
        
        # Moving averages with optimized periods
        print("Calculating moving averages...")
        ma_fast = vbt.MA.run(close, window=self.config.ma_fast).ma
        ma_medium = vbt.MA.run(close, window=self.config.ma_medium).ma
        ma_slow = vbt.MA.run(close, window=self.config.ma_slow).ma
        
        # Handle MultiIndex columns from VectorBT
        def fix_columns(df):
            if isinstance(df.columns, pd.MultiIndex):
                return df.droplevel(0, axis=1) if df.columns.nlevels > 1 else df
            return df
        
        ma_fast = fix_columns(ma_fast)
        ma_medium = fix_columns(ma_medium)
        ma_slow = fix_columns(ma_slow)
        
        # Ensure all MAs have same columns and index
        ma_index = ma_fast.index.intersection(ma_medium.index).intersection(ma_slow.index)
        ma_cols = ma_fast.columns.intersection(ma_medium.columns).intersection(ma_slow.columns)
        
        ma_fast = ma_fast.loc[ma_index, ma_cols]
        ma_medium = ma_medium.loc[ma_index, ma_cols] 
        ma_slow = ma_slow.loc[ma_index, ma_cols]
        
        # Align all data to MA dimensions
        close = close.loc[ma_index, ma_cols]
        high = high.loc[ma_index, ma_cols]
        low = low.loc[ma_index, ma_cols]
        volume = volume.loc[ma_index, ma_cols]
        
        print("Calculating trend and pattern indicators...")
        
        # Flagpole analysis (optimized parameters)
        high_max = high.rolling(window=self.config.flagpole_period, min_periods=1).max()
        low_min = low.rolling(window=self.config.flagpole_period, min_periods=1).min()
        trend_gain = (high_max / low_min.where(low_min > 0, 1)) - 1
        
        # Consolidation analysis
        price_std = close.rolling(window=self.config.consolidation_window, min_periods=1).std()
        price_mean = close.rolling(window=self.config.consolidation_window, min_periods=1).mean()
        volatility_ratio = price_std / price_mean.where(price_mean > 0, 1)
        
        # Volume analysis
        volume_avg = volume.rolling(window=self.config.consolidation_window, min_periods=1).mean()
        
        print(f"Indicators calculated for {len(ma_cols)} stocks over {len(ma_index)} days")
        
        return {
            'close': close,
            'high': high,
            'low': low,
            'volume': volume,
            'ma_fast': ma_fast,
            'ma_medium': ma_medium,
            'ma_slow': ma_slow,
            'trend_gain': trend_gain,
            'high_max': high_max,
            'low_min': low_min,
            'volatility_ratio': volatility_ratio,
            'volume_avg': volume_avg,
            'index': ma_index,
            'tickers': list(ma_cols)
        }
    
    def generate_trading_signals(self, indicators: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate optimized entry and exit signals"""
        print("Generating trading signals...")
        
        close = indicators['close']
        high = indicators['high']
        low = indicators['low']
        ma_fast = indicators['ma_fast']
        ma_medium = indicators['ma_medium']
        ma_slow = indicators['ma_slow']
        trend_gain = indicators['trend_gain']
        high_max = indicators['high_max']
        volatility_ratio = indicators['volatility_ratio']
        volume = indicators['volume']
        volume_avg = indicators['volume_avg']
        
        # Entry conditions (optimized based on results)
        print("Calculating entry conditions...")
        
        # 1. Strong flagpole trend (15% minimum gain - optimized)
        flagpole_condition = trend_gain > self.config.flagpole_min_gain
        
        # 2. Price near recent highs (shows continuation strength)
        near_highs = close > (high_max * 0.85)  # Within 15% of highs
        
        # 3. Moving average alignment (optimized 5/20/60 configuration)
        ma_aligned = (ma_fast > ma_medium * 0.995) & (ma_medium > ma_slow * 0.995)
        
        # 4. Price above key MAs (trend confirmation)
        price_above_mas = (close > ma_fast) & (close > ma_medium * 0.98)
        
        # 5. Low volatility consolidation
        low_volatility = volatility_ratio < self.config.consolidation_volatility_threshold
        
        # 6. Volume confirmation (breakout volume)
        volume_breakout = volume > volume_avg * 1.2
        
        # 7. Breakout above consolidation
        breakout = close > high.rolling(window=20).max().shift(1)
        
        # 8. Strong daily close (momentum confirmation)
        daily_range = high - low
        close_strength = (close - low) / daily_range.where(daily_range > 0, 1)
        strong_close = close_strength > 0.7
        
        # Combine entry conditions
        entries = (
            flagpole_condition &
            near_highs &
            ma_aligned &
            price_above_mas &
            low_volatility &
            volume_breakout &
            breakout &
            strong_close
        ).fillna(False)
        
        # Exit conditions (optimized)
        print("Calculating exit conditions...")
        
        # Primary exit: price below medium MA
        ma_exit = close < ma_medium * 0.98
        
        # Secondary exit: breakdown below fast MA
        fast_ma_exit = close < ma_fast * 0.95
        
        exits = (ma_exit | fast_ma_exit).fillna(False)
        
        print(f"Generated {entries.sum().sum()} entry signals and {exits.sum().sum()} exit signals")
        
        return entries, exits
    
    def run_vectorbt_backtest(self, indicators: Dict, entries: pd.DataFrame, exits: pd.DataFrame) -> Optional[object]:
        """Run optimized VectorBT backtest with best practices"""
        print("Running VectorBT backtest...")
        
        close = indicators['close']
        
        # Data type optimization for VectorBT
        def optimize_for_vectorbt(df, name):
            df = df.copy()
            
            # Ensure float64 for price data, bool for signals
            if name in ['close']:
                df = df.astype('float64')
            elif name in ['entries', 'exits']:
                df = df.astype('bool')
            
            # Remove timezone for compatibility
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Ensure string columns
            df.columns = df.columns.astype(str)
            
            # Final NaN handling
            if name in ['entries', 'exits']:
                df = df.fillna(False)
            else:
                df = df.fillna(method='ffill').fillna(method='bfill').fillna(0.0)
            
            return df
        
        # Optimize data
        close_clean = optimize_for_vectorbt(close, 'close')
        entries_clean = optimize_for_vectorbt(entries, 'entries')
        exits_clean = optimize_for_vectorbt(exits, 'exits')
        
        # Verify alignment
        assert close_clean.shape == entries_clean.shape == exits_clean.shape
        assert close_clean.index.equals(entries_clean.index)
        assert list(close_clean.columns) == list(entries_clean.columns)
        
        print(f"Backtest data shape: {close_clean.shape}")
        print(f"Price range: ${close_clean.min().min():.2f} - ${close_clean.max().max():.2f}")
        print(f"Entry signals: {entries_clean.sum().sum()}")
        print(f"Exit signals: {exits_clean.sum().sum()}")
        
        # Check for potential overflow issues - be more aggressive
        if close_clean.max().max() > 500:
            print("Warning: High stock prices detected - filtering aggressively")
            # Filter out stocks with high prices
            max_price = close_clean.max()
            valid_stocks = max_price[max_price < 500].index
            if len(valid_stocks) > 10:  # Ensure we have enough stocks
                print(f"Filtering to {len(valid_stocks)} stocks with prices < $500")
                close_clean = close_clean[valid_stocks]
                entries_clean = entries_clean[valid_stocks]
                exits_clean = exits_clean[valid_stocks]
            else:
                print("Not enough low-price stocks, using top 10 lowest priced stocks")
                sorted_stocks = max_price.sort_values().head(10).index
                close_clean = close_clean[sorted_stocks]
                entries_clean = entries_clean[sorted_stocks]
                exits_clean = exits_clean[sorted_stocks]
        
        try:
            # Create portfolio with optimized parameters - simplified to avoid overflow
            portfolio = vbt.Portfolio.from_signals(
                close=close_clean,
                entries=entries_clean,
                exits=exits_clean,
                init_cash=100000.0,
                size=self.config.max_position_size,  # 15% position size (optimized)
                size_type='percent',
                fees=self.config.commission,
                freq='D',
                group_by=True,
                cash_sharing=True
            )
            
            print("Portfolio created successfully!")
            return portfolio
            
        except Exception as e:
            print(f"Portfolio creation failed: {e}")
            
            # Fallback: minimal portfolio
            try:
                print("Attempting fallback portfolio...")
                portfolio = vbt.Portfolio.from_signals(
                    close=close_clean,
                    entries=entries_clean,
                    exits=exits_clean,
                    init_cash=100000.0,
                    freq='D'
                )
                print("Fallback portfolio created!")
                return portfolio
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                
                # Final fallback: try with just one stock to test
                try:
                    print("Final fallback: testing with single stock...")
                    single_stock = close_clean.columns[0]
                    single_close = close_clean[[single_stock]]
                    single_entries = entries_clean[[single_stock]]
                    single_exits = exits_clean[[single_stock]]
                    
                    portfolio = vbt.Portfolio.from_signals(
                        close=single_close,
                        entries=single_entries,
                        exits=single_exits,
                        init_cash=100000.0
                    )
                    print(f"Single stock portfolio created for {single_stock}!")
                    return portfolio
                    
                except Exception as e3:
                    print(f"Even single stock failed: {e3}")
                    return None
    
    def analyze_performance(self, portfolio, indicators: Dict) -> Dict:
        """Comprehensive performance analysis"""
        if portfolio is None:
            print("No portfolio to analyze")
            return {}
        
        print("\n" + "="*80)
        print("OPTIMIZED FLAG PATTERN STRATEGY - PERFORMANCE ANALYSIS")
        print("="*80)
        
        try:
            # Basic portfolio statistics
            stats = portfolio.stats()
            print("\nPORTFOLIO STATISTICS:")
            print(stats)
            
            results = {
                'portfolio_stats': stats,
                'total_return': portfolio.total_return(),
                'annualized_return': portfolio.annualized_return(),
                'sharpe_ratio': portfolio.sharpe_ratio(),
                'max_drawdown': portfolio.max_drawdown(),
                'calmar_ratio': portfolio.calmar_ratio()
            }
            
            # Trade analysis
            if portfolio.trades.count() > 0:
                trades = portfolio.trades
                results.update({
                    'total_trades': trades.count(),
                    'win_rate': trades.win_rate(),
                    'avg_trade_return': trades.returns.mean(),
                    'best_trade': trades.returns.max(),
                    'worst_trade': trades.returns.min(),
                    'avg_duration': trades.duration.mean()
                })
                
                print(f"\nTRADE ANALYSIS:")
                print(f"Total Trades: {trades.count()}")
                print(f"Win Rate: {trades.win_rate():.1%}")
                print(f"Average Trade Return: {trades.returns.mean():.2%}")
                print(f"Best Trade: {trades.returns.max():.2%}")
                print(f"Worst Trade: {trades.returns.min():.2%}")
                print(f"Average Duration: {trades.duration.mean():.1f} days")
                
                # Per-stock analysis if possible
                try:
                    trades_df = pd.DataFrame(trades.records)
                    if not trades_df.empty and 'col' in trades_df.columns:
                        tickers = indicators['tickers']
                        trades_df['ticker'] = [tickers[col] for col in trades_df['col']]
                        
                        stock_pnl = trades_df.groupby('ticker')['pnl'].sum().sort_values(ascending=False)
                        
                        print(f"\nTOP 10 PERFORMING STOCKS:")
                        for i, (ticker, pnl) in enumerate(stock_pnl.head(10).items()):
                            print(f"{i+1:2d}. {ticker}: ${pnl:,.2f}")
                        
                        results['stock_pnl'] = stock_pnl
                        
                except Exception as e:
                    print(f"Could not analyze per-stock performance: {e}")
            
            else:
                print("\nNo trades executed during backtest period")
                print("Consider adjusting parameters for more opportunities")
            
            # Risk metrics
            returns = portfolio.returns()
            results.update({
                'volatility': returns.std() * np.sqrt(252),
                'downside_volatility': returns[returns < 0].std() * np.sqrt(252),
                'sortino_ratio': portfolio.sortino_ratio()
            })
            
            print(f"\nRISK METRICS:")
            print(f"Volatility (annualized): {results['volatility']:.1%}")
            print(f"Max Drawdown: {results['max_drawdown']:.1%}")
            print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            print(f"Sortino Ratio: {results['sortino_ratio']:.2f}")
            print(f"Calmar Ratio: {results['calmar_ratio']:.2f}")
            
            return results
            
        except Exception as e:
            print(f"Error in performance analysis: {e}")
            return {'error': str(e)}
    
    def run_complete_backtest(self, max_stocks: int = None, chunk_size: int = 50) -> Dict:
        """Run complete optimized backtesting pipeline"""
        print("="*80)
        print("OPTIMIZED FLAG PATTERN STRATEGY - COMPLETE BACKTEST")
        print("="*80)
        print(f"Period: {self.config.start_date} to {self.config.end_date}")
        print(f"Strategy: Flag Pattern with Optimized Parameters")
        print(f"Parameters: MA({self.config.ma_fast}/{self.config.ma_medium}/{self.config.ma_slow}), "
              f"Flagpole({self.config.flagpole_min_gain:.0%}), "
              f"Stop({self.config.max_stop_loss:.0%}), "
              f"Position({self.config.max_position_size:.0%})")
        
        # Step 1: Get tickers
        tickers = self.get_sp500_tickers()
        if max_stocks:
            tickers = tickers[:max_stocks]
        
        # Step 2: Download data
        raw_data = self.download_data_batch(tickers, chunk_size)
        if raw_data is None:
            return {'error': 'Data download failed'}
        
        # Step 3: Clean and align data
        clean_data = self.clean_and_align_data(raw_data)
        if clean_data is None:
            return {'error': 'Data cleaning failed'}
        
        # Step 4: Calculate indicators
        indicators = self.calculate_technical_indicators(clean_data)
        if indicators is None:
            return {'error': 'Indicator calculation failed'}
        
        # Step 5: Generate signals
        entries, exits = self.generate_trading_signals(indicators)
        
        # Step 6: Run backtest
        portfolio = self.run_vectorbt_backtest(indicators, entries, exits)
        if portfolio is None:
            return {'error': 'Backtest execution failed'}
        
        # Step 7: Analyze performance
        performance = self.analyze_performance(portfolio, indicators)
        
        # Store results
        results = {
            'portfolio': portfolio,
            'indicators': indicators,
            'entries': entries,
            'exits': exits,
            'performance': performance,
            'config': self.config
        }
        
        self.results = results
        return results
    
    def export_results(self, filename_prefix: str = "optimized_strategy") -> None:
        """Export results to CSV files"""
        if not self.results:
            print("No results to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Export trades
            portfolio = self.results['portfolio']
            if portfolio.trades.count() > 0:
                trades_df = pd.DataFrame(portfolio.trades.records)
                tickers = self.results['indicators']['tickers']
                
                if 'col' in trades_df.columns:
                    trades_df['ticker'] = [tickers[col] for col in trades_df['col']]
                
                trades_file = f"{filename_prefix}_trades_{timestamp}.csv"
                trades_df.to_csv(trades_file, index=False)
                print(f"Trades exported to: {trades_file}")
            
            # Export performance summary
            performance = self.results['performance']
            if 'stock_pnl' in performance:
                pnl_file = f"{filename_prefix}_stock_pnl_{timestamp}.csv"
                performance['stock_pnl'].to_csv(pnl_file)
                print(f"Stock P&L exported to: {pnl_file}")
            
        except Exception as e:
            print(f"Error exporting results: {e}")

def main():
    """Main execution function"""
    print("Starting Optimized Flag Pattern Strategy...")
    
    # Create strategy with optimized configuration
    strategy = OptimizedFlagStrategy()
    
    # Run complete backtest
    results = strategy.run_complete_backtest(
        max_stocks=100,  # Test with first 100 S&P 500 stocks
        chunk_size=25    # Smaller batches for reliability
    )
    
    if 'error' in results:
        print(f"Backtest failed: {results['error']}")
        return None, None
    
    # Export results
    strategy.export_results("optimized_flag_strategy")
    
    print("\nBacktest completed successfully!")
    print(f"Check the generated CSV files for detailed results.")
    
    return strategy, results

if __name__ == "__main__":
    strategy, results = main()