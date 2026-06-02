import vectorbt as vbt
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import concurrent.futures
from functools import partial

warnings.filterwarnings('ignore')

@dataclass
class StrategyConfig:
    """Configuration class for strategy parameters"""
    # Flagpole parameters
    flagpole_period: int = 60
    flagpole_min_gain: float = 0.25  # Reduced from 0.30 for more opportunities
    
    # Consolidation parameters
    consolidation_min_days: int = 10
    consolidation_max_days: int = 40
    consolidation_volatility_threshold: float = 0.4  # Increased from 0.3
    
    # Moving averages
    ma_fast: int = 10
    ma_medium: int = 20
    ma_slow: int = 50
    
    # Risk management
    max_stop_loss: float = 0.08
    min_stop_loss: float = 0.02
    risk_per_trade: float = 0.01
    
    # Position sizing
    max_position_size: float = 0.10
    
    # Exit rules
    partial_profit_days: int = 5
    partial_profit_percentage: float = 0.5
    trailing_stop_ma: int = 20
    
    # Transaction costs
    commission: float = 0.001
    
    # New optimization parameters
    min_volume_ratio: float = 1.0  # Reduced volume requirement
    breakout_strength_threshold: float = 0.6  # Reduced from 0.75
    ma_alignment_buffer: float = 0.02  # Allow 2% deviation in MA alignment

class EnhancedKristjanStrategy:
    """Enhanced implementation of Kristjan Kullamägi's breakout strategy with optimizations"""
    
    def __init__(self, config: StrategyConfig = None, start_date: str = '2020-01-01', 
                 end_date: str = None):
        self.config = config or StrategyConfig()
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.data = {}
        self.results = {}
        
    def get_sp500_tickers(self) -> List[str]:
        """Fetch S&P 500 tickers with better error handling"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            tickers = table['Symbol'].tolist()
            # Handle ticker formatting
            tickers = [ticker.replace('.', '-') for ticker in tickers]
            print(f"Successfully fetched {len(tickers)} S&P 500 tickers")
            return tickers
        except Exception as e:
            print(f"Error fetching S&P 500 tickers: {e}")
            # Enhanced fallback list
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 
                   'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'DIS', 'NFLX',
                   'CRM', 'ADBE', 'PYPL', 'INTC', 'CSCO', 'PFE', 'XOM',
                   'BAC', 'WMT', 'KO', 'MRK', 'ABT', 'COST', 'AVGO', 'TMO']
    
    def download_data_parallel(self, tickers: List[str] = None, max_tickers: int = None, 
                              max_workers: int = 5) -> Dict:
        """Download data with parallel processing for better performance"""
        if tickers is None:
            tickers = self.get_sp500_tickers()
        
        if max_tickers:
            tickers = tickers[:max_tickers]
        
        print(f"Downloading data for {len(tickers)} stocks from {self.start_date} to {self.end_date}")
        
        def download_single_ticker(ticker):
            try:
                ticker_data = yf.download(
                    ticker,
                    start=self.start_date,
                    end=self.end_date,
                    auto_adjust=True,
                    progress=False
                )
                
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                if (not ticker_data.empty and 
                    len(ticker_data) > 100 and 
                    all(col in ticker_data.columns for col in required_columns)):
                    
                    ticker_data = ticker_data.dropna()
                    if len(ticker_data) > 100:
                        return ticker, ticker_data
                return ticker, None
                
            except Exception as e:
                print(f"Error downloading {ticker}: {e}")
                return ticker, None
        
        # Use ThreadPoolExecutor for parallel downloads
        self.data = {}
        failed_downloads = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(download_single_ticker, tickers))
        
        for ticker, data in results:
            if data is not None:
                self.data[ticker] = data
            else:
                failed_downloads.append(ticker)
        
        if failed_downloads:
            print(f"Failed to download data for {len(failed_downloads)} stocks")
        
        print(f"Successfully downloaded data for {len(self.data)} stocks")
        return self.data
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """FIXED: Enhanced technical indicators with proper alignment handling"""
        # Start with a clean copy and ensure proper index
        indicators = df.copy()
        
        # Extract price and volume data as Series (not DataFrames)
        close = df['Close'].copy()
        high = df['High'].copy()
        low = df['Low'].copy()
        volume = df['Volume'].copy()
        
        # Ensure all series have the same index
        common_index = close.index
        high = high.reindex(common_index)
        low = low.reindex(common_index)
        volume = volume.reindex(common_index)
        
        # Moving averages - direct assignment to avoid alignment issues
        indicators.loc[:, 'MA_Fast'] = close.rolling(self.config.ma_fast).mean()
        indicators.loc[:, 'MA_Medium'] = close.rolling(self.config.ma_medium).mean()
        indicators.loc[:, 'MA_Slow'] = close.rolling(self.config.ma_slow).mean()
        
        # Enhanced flagpole analysis
        indicators.loc[:, 'High_60d'] = high.rolling(self.config.flagpole_period).max()
        indicators.loc[:, 'Low_60d'] = low.rolling(self.config.flagpole_period).min()
        
        # Safe division with alignment check
        high_60d = indicators['High_60d']
        low_60d = indicators['Low_60d']
        indicators.loc[:, 'Flagpole_Gain'] = (high_60d / low_60d) - 1
        
        # Multiple timeframe consolidation analysis
        for period in [10, 15, 20, 30]:
            indicators.loc[:, f'High_{period}d'] = high.rolling(period).max()
            indicators.loc[:, f'Low_{period}d'] = low.rolling(period).min()
            high_p = indicators[f'High_{period}d']
            low_p = indicators[f'Low_{period}d']
            indicators.loc[:, f'Range_{period}d'] = (high_p / low_p) - 1
        
        # Enhanced volatility measures
        close_mean_10 = close.rolling(10).mean()
        close_std_10 = close.rolling(10).std()
        indicators.loc[:, 'Volatility_10d'] = close_std_10 / close_mean_10
        
        close_mean_20 = close.rolling(20).mean()
        close_std_20 = close.rolling(20).std()
        indicators.loc[:, 'Volatility_20d'] = close_std_20 / close_mean_20
        
        indicators.loc[:, 'Volatility_Percentile'] = indicators['Volatility_20d'].rolling(60).rank(pct=True)
        
        # Volume analysis - FIXED to avoid alignment issues
        volume_ma_10 = volume.rolling(10).mean()
        volume_ma_20 = volume.rolling(20).mean()
        
        indicators.loc[:, 'Volume_MA_10'] = volume_ma_10
        indicators.loc[:, 'Volume_MA_20'] = volume_ma_20
        
        # Safe division for volume ratios
        indicators.loc[:, 'Volume_Ratio_10'] = volume / volume_ma_10.where(volume_ma_10 > 0, 1)
        indicators.loc[:, 'Volume_Ratio_20'] = volume / volume_ma_20.where(volume_ma_20 > 0, 1)
        
        # Price momentum indicators - using .loc to avoid alignment issues
        indicators.loc[:, 'Price_vs_MA_Fast'] = close / indicators['MA_Fast'] - 1
        indicators.loc[:, 'Price_vs_MA_Medium'] = close / indicators['MA_Medium'] - 1
        indicators.loc[:, 'Price_vs_MA_Slow'] = close / indicators['MA_Slow'] - 1
        
        # RSI calculation - fixed to avoid alignment issues
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.where(loss > 0, 1)  # Avoid division by zero
        indicators.loc[:, 'RSI'] = 100 - (100 / (1 + rs))
        
        # Price position within daily range
        daily_range = high - low
        indicators.loc[:, 'Daily_Range'] = daily_range
        indicators.loc[:, 'Close_Position'] = (close - low) / daily_range.where(daily_range > 0, 1)
        
        # Handle any remaining NaN values
        indicators = indicators.fillna(method='ffill').fillna(0)
        
        return indicators
    
    def identify_flagpole_pattern(self, indicators: pd.DataFrame) -> pd.Series:
        """Enhanced flagpole pattern identification"""
        # Basic flagpole condition
        flagpole_condition = indicators['Flagpole_Gain'] >= self.config.flagpole_min_gain
        
        # Quality filters
        near_highs = indicators['Close'] > (indicators['High_60d'] * 0.80)  # More lenient
        
        # Ensure the move has some consistency (not just a single spike)
        consistent_strength = indicators['Close'] > indicators['MA_Medium']
        
        # Volume should have been elevated during the flagpole formation
        elevated_volume = indicators['Volume_Ratio_20'] > 0.8
        
        return flagpole_condition & near_highs & consistent_strength & elevated_volume
    
    def identify_consolidation_pattern(self, indicators: pd.DataFrame) -> pd.Series:
        """Enhanced consolidation pattern with more flexible criteria"""
        # More flexible MA alignment
        ma_trend = (
            (indicators['MA_Fast'] > indicators['MA_Medium'] * (1 - self.config.ma_alignment_buffer)) & 
            (indicators['MA_Medium'] > indicators['MA_Slow'] * (1 - self.config.ma_alignment_buffer))
        )
        
        # Price above key moving averages but allow some flexibility
        price_above_mas = (
            (indicators['Close'] > indicators['MA_Medium'] * 0.98) &  # Allow 2% below
            (indicators['Close'] > indicators['MA_Slow'] * 0.95)      # Allow 5% below
        )
        
        # Low volatility with multiple confirmations
        low_volatility = (
            (indicators['Volatility_Percentile'] <= self.config.consolidation_volatility_threshold) |
            (indicators['Range_20d'] < 0.25)  # Alternative consolidation measure
        )
        
        # Price not too volatile relative to MAs
        price_stability = (
            (indicators['Price_vs_MA_Medium'].abs() < 0.20) &  # More lenient
            (indicators['Range_15d'] < 0.30)
        )
        
        # RSI in reasonable range (not overbought/oversold)
        rsi_ok = (indicators['RSI'] > 30) & (indicators['RSI'] < 80)
        
        return ma_trend & price_above_mas & low_volatility & price_stability & rsi_ok
    
    def identify_breakout_signals(self, indicators: pd.DataFrame) -> pd.Series:
        """Enhanced breakout signal identification with better confirmation"""
        # Core patterns
        flagpole = self.identify_flagpole_pattern(indicators)
        consolidation = self.identify_consolidation_pattern(indicators)
        
        # Multiple breakout triggers
        breakout_20d = indicators['Close'] > indicators['High_20d'].shift(1)
        breakout_15d = indicators['Close'] > indicators['High_15d'].shift(1)
        breakout_10d = indicators['Close'] > indicators['High_10d'].shift(1)
        
        breakout_trigger = breakout_20d | breakout_15d | breakout_10d
        
        # More flexible volume confirmation
        volume_confirmation = (
            (indicators['Volume_Ratio_10'] > self.config.min_volume_ratio) |
            (indicators['Volume_Ratio_20'] > self.config.min_volume_ratio * 0.8)
        )
        
        # Enhanced momentum confirmation
        strong_close = indicators['Close_Position'] > self.config.breakout_strength_threshold
        price_momentum = indicators['Close'] > indicators['Close'].shift(1)  # Higher close
        
        # RSI momentum (but not overbought)
        rsi_momentum = (indicators['RSI'] > 50) & (indicators['RSI'] < 75)
        
        # Combine all conditions with more flexibility
        entry_signals = (
            flagpole & 
            consolidation & 
            breakout_trigger & 
            volume_confirmation & 
            (strong_close | price_momentum) &  # Either strong close OR momentum
            rsi_momentum
        )
        
        return entry_signals
    
    def generate_enhanced_exit_signals(self, indicators: pd.DataFrame, entries: pd.Series) -> pd.Series:
        """Enhanced exit strategy with multiple conditions"""
        # Basic MA exit
        ma_exit = indicators['Close'] < indicators['MA_Medium']
        
        # RSI overbought exit
        rsi_exit = indicators['RSI'] > 80
        
        # Trailing stop using fast MA
        trailing_exit = indicators['Close'] < indicators['MA_Fast'] * 0.95
        
        # Volatility spike exit (potential reversal)
        vol_exit = indicators['Volatility_Percentile'] > 0.9
        
        # Combine exit conditions
        exits = ma_exit | rsi_exit | trailing_exit | vol_exit
        
        return exits
    
    def backtest_single_stock(self, ticker: str, initial_cash: float = 100000) -> Optional[Dict]:
        """Enhanced backtesting with better signal processing"""
        if ticker not in self.data:
            return None
        
        try:
            ticker_data = self.data[ticker].copy()
            if len(ticker_data) < 150:
                return None
            
            indicators = self.calculate_technical_indicators(ticker_data)
            indicators = indicators.dropna()
            
            if len(indicators) < 100:
                return None
            
            entries = self.identify_breakout_signals(indicators)
            exits = self.generate_enhanced_exit_signals(indicators, entries)
            
            if not entries.any():
                return None
            
            # Ensure alignment - this was a key issue
            close_prices = indicators['Close'].copy()
            entries = entries.reindex(close_prices.index, fill_value=False)
            exits = exits.reindex(close_prices.index, fill_value=False)
            
            # Enhanced portfolio parameters
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices,
                entries=entries,
                exits=exits,
                init_cash=initial_cash,
                size=self.config.max_position_size,
                size_type='percent',
                fees=self.config.commission,
                sl_stop=self.config.max_stop_loss,
                freq='D'
            )
            
            trades = portfolio.trades
            returns = portfolio.returns()
            
            if trades.count() == 0:
                return None
            
            # Enhanced metrics calculation
            winning_trades = trades.returns[trades.returns > 0]
            losing_trades = trades.returns[trades.returns < 0]
            
            if len(losing_trades) > 0:
                profit_factor = winning_trades.sum() / abs(losing_trades.sum())
            else:
                profit_factor = float('inf') if len(winning_trades) > 0 else 0
            
            # Calculate additional metrics
            max_consecutive_losses = self._calculate_max_consecutive_losses(trades.returns)
            
            result = {
                'ticker': ticker,
                'portfolio': portfolio,
                'indicators': indicators,
                'entries': entries,
                'exits': exits,
                'total_return': portfolio.total_return(),
                'annualized_return': portfolio.annualized_return(),
                'sharpe_ratio': portfolio.sharpe_ratio(),
                'sortino_ratio': portfolio.sortino_ratio(),
                'max_drawdown': portfolio.max_drawdown(),
                'calmar_ratio': portfolio.calmar_ratio(),
                'total_trades': trades.count(),
                'win_rate': trades.win_rate(),
                'avg_trade_return': trades.returns.mean(),
                'avg_trade_duration': trades.duration.mean(),
                'best_trade': trades.returns.max(),
                'worst_trade': trades.returns.min(),
                'profit_factor': profit_factor,
                'expectancy': trades.returns.mean(),
                'volatility': returns.std() * np.sqrt(252),
                'max_consecutive_losses': max_consecutive_losses,
            }
            
            return result
            
        except Exception as e:
            print(f"Error backtesting {ticker}: {e}")
            return None
    
    def _calculate_max_consecutive_losses(self, returns: pd.Series) -> int:
        """Calculate maximum consecutive losing trades"""
        if len(returns) == 0:
            return 0
        
        consecutive_losses = 0
        max_consecutive = 0
        
        for ret in returns:
            if ret < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
            else:
                consecutive_losses = 0
        
        return max_consecutive
    
    def backtest_portfolio(self, max_stocks: int = None, debug: bool = False) -> Dict:
        """Enhanced portfolio backtesting"""
        if not self.data:
            print("No data available. Please download data first.")
            return {}
        
        tickers = list(self.data.keys())
        if max_stocks:
            tickers = tickers[:max_stocks]
        
        print(f"Backtesting {len(tickers)} stocks...")
        
        results = {}
        diagnostics = {
            'no_signals': 0,
            'insufficient_data': 0,
            'errors': 0,
            'flagpole_issues': 0,
            'consolidation_issues': 0
        }
        
        for i, ticker in enumerate(tickers):
            result = self.backtest_single_stock(ticker)
            if result is not None:
                results[ticker] = result
                if debug:
                    print(f"✓ {ticker}: {result['total_trades']} trades, {result['total_return']:.2%} return")
            else:
                # Enhanced diagnostics
                if ticker in self.data:
                    try:
                        ticker_data = self.data[ticker]
                        if len(ticker_data) < 150:
                            diagnostics['insufficient_data'] += 1
                            continue
                            
                        indicators = self.calculate_technical_indicators(ticker_data)
                        flagpole = self.identify_flagpole_pattern(indicators)
                        consolidation = self.identify_consolidation_pattern(indicators)
                        entries = self.identify_breakout_signals(indicators)
                        
                        if not entries.any():
                            diagnostics['no_signals'] += 1
                            if not flagpole.any():
                                diagnostics['flagpole_issues'] += 1
                            if not consolidation.any():
                                diagnostics['consolidation_issues'] += 1
                        
                        if debug:
                            print(f"⚠ {ticker}: No signals - Flagpole: {flagpole.sum()}, Consolidation: {consolidation.sum()}")
                            
                    except Exception as e:
                        diagnostics['errors'] += 1
                        if debug:
                            print(f"✗ {ticker}: Error - {e}")
            
            if (i + 1) % 10 == 0:
                print(f"Completed {i + 1}/{len(tickers)} stocks")
        
        self.results = results
        print(f"\nBacktest Summary:")
        print(f"Successfully backtested: {len(results)} stocks")
        print(f"No signals: {diagnostics['no_signals']}")
        print(f"Insufficient data: {diagnostics['insufficient_data']}")
        print(f"Flagpole issues: {diagnostics['flagpole_issues']}")
        print(f"Consolidation issues: {diagnostics['consolidation_issues']}")
        print(f"Errors: {diagnostics['errors']}")
        
        return results
    
    def optimize_parameters(self, param_ranges: Dict, sample_size: int = 10):
        """Parameter optimization using grid search on a sample of stocks"""
        if not self.data:
            print("No data available for optimization")
            return None
        
        sample_tickers = list(self.data.keys())[:sample_size]
        best_params = None
        best_score = -float('inf')
        
        print(f"Optimizing parameters on {len(sample_tickers)} stocks...")
        
        # Simple grid search (can be enhanced with more sophisticated methods)
        from itertools import product
        
        param_combinations = list(product(*param_ranges.values()))
        param_names = list(param_ranges.keys())
        
        for i, param_values in enumerate(param_combinations):
            # Create config with current parameters
            config_dict = dict(zip(param_names, param_values))
            test_config = StrategyConfig(**{**self.config.__dict__, **config_dict})
            
            # Test configuration
            test_strategy = EnhancedKristjanStrategy(test_config, self.start_date, self.end_date)
            test_strategy.data = {ticker: self.data[ticker] for ticker in sample_tickers}
            
            results = test_strategy.backtest_portfolio()
            
            if results:
                # Calculate optimization score (can be customized)
                total_returns = [r['total_return'] for r in results.values()]
                sharpe_ratios = [r['sharpe_ratio'] for r in results.values()]
                win_rates = [r['win_rate'] for r in results.values()]
                
                score = (np.mean(total_returns) * 0.4 + 
                        np.mean(sharpe_ratios) * 0.4 + 
                        np.mean(win_rates) * 0.2)
                
                if score > best_score:
                    best_score = score
                    best_params = config_dict
                    print(f"New best score: {score:.4f} with params: {config_dict}")
            
            if (i + 1) % 5 == 0:
                print(f"Tested {i + 1}/{len(param_combinations)} combinations")
        
        print(f"\nOptimization complete. Best parameters: {best_params}")
        return best_params
    
    def analyze_performance(self) -> pd.DataFrame:
        """Enhanced performance analysis with additional metrics"""
        if not self.results:
            print("No results to analyze. Run backtest first.")
            return pd.DataFrame()
        
        summary_data = []
        for ticker, result in self.results.items():
            summary_data.append({
                'Ticker': ticker,
                'Total_Return': result['total_return'],
                'Annualized_Return': result['annualized_return'],
                'Sharpe_Ratio': result['sharpe_ratio'],
                'Sortino_Ratio': result['sortino_ratio'],
                'Calmar_Ratio': result['calmar_ratio'],
                'Max_Drawdown': result['max_drawdown'],
                'Volatility': result['volatility'],
                'Total_Trades': result['total_trades'],
                'Win_Rate': result['win_rate'],
                'Avg_Trade_Return': result['avg_trade_return'],
                'Avg_Trade_Duration': result['avg_trade_duration'],
                'Best_Trade': result['best_trade'],
                'Worst_Trade': result['worst_trade'],
                'Profit_Factor': result['profit_factor'],
                'Expectancy': result['expectancy'],
                'Max_Consecutive_Losses': result['max_consecutive_losses']
            })
        
        summary_df = pd.DataFrame(summary_data)
        self._print_enhanced_analysis(summary_df)
        
        return summary_df
    
    def _print_enhanced_analysis(self, df: pd.DataFrame):
        """Enhanced performance analysis output"""
        print("=" * 90)
        print("ENHANCED KRISTJAN KULLAMÄGI'S BREAKOUT STRATEGY - PERFORMANCE ANALYSIS")
        print("=" * 90)
        print(f"Analysis Period: {self.start_date} to {self.end_date}")
        print(f"Stocks Analyzed: {len(df)}")
        print(f"Total Trades: {df['Total_Trades'].sum()}")
        print()
        
        # Statistical significance
        profitable_pct = (df['Total_Return'] > 0).mean()
        print("STATISTICAL OVERVIEW:")
        print(f"Profitable Stocks: {(df['Total_Return'] > 0).sum()} ({profitable_pct:.1%})")
        print(f"Average Total Return: {df['Total_Return'].mean():.2%} ± {df['Total_Return'].std():.2%}")
        print(f"Median Total Return: {df['Total_Return'].median():.2%}")
        print(f"Return Distribution: 25th: {df['Total_Return'].quantile(0.25):.2%}, 75th: {df['Total_Return'].quantile(0.75):.2%}")
        print()
        
        # Risk Analysis
        print("RISK ANALYSIS:")
        print(f"Average Sharpe Ratio: {df['Sharpe_Ratio'].mean():.2f}")
        print(f"Average Max Drawdown: {df['Max_Drawdown'].mean():.2%}")
        print(f"Average Max Consecutive Losses: {df['Max_Consecutive_Losses'].mean():.1f}")
        print(f"Risk-Adjusted Return (Sortino): {df['Sortino_Ratio'].mean():.2f}")
        print()
        
        # Strategy Effectiveness
        print("STRATEGY EFFECTIVENESS:")
        print(f"Average Win Rate: {df['Win_Rate'].mean():.1%}")
        print(f"Average Profit Factor: {df['Profit_Factor'].mean():.2f}")
        print(f"Average Trade Duration: {df['Avg_Trade_Duration'].mean():.1f} days")
        print(f"Expectancy per Trade: {df['Expectancy'].mean():.2%}")
        print()
        
        # Top performers with enhanced metrics
        print("TOP 10 PERFORMERS (by Total Return):")
        top_performers = df.nlargest(10, 'Total_Return')[
            ['Ticker', 'Total_Return', 'Sharpe_Ratio', 'Win_Rate', 'Total_Trades', 'Max_Drawdown']
        ]
        print(top_performers.to_string(index=False, formatters={
            'Total_Return': '{:.1%}'.format,
            'Sharpe_Ratio': '{:.2f}'.format,
            'Win_Rate': '{:.1%}'.format,
            'Max_Drawdown': '{:.1%}'.format
        }))

def run_enhanced_strategy():
    """Main function to run the enhanced strategy"""
    print("=" * 60)
    print("ENHANCED KRISTJAN KULLAMÄGI BREAKOUT STRATEGY")
    print("=" * 60)
    
    # Optimized configuration
    config = StrategyConfig(
        flagpole_period=60,
        flagpole_min_gain=0.20,  # More opportunities
        consolidation_volatility_threshold=0.5,  # More flexible
        ma_fast=10,
        ma_medium=20,
        ma_slow=50,
        max_stop_loss=0.08,
        max_position_size=0.10,
        commission=0.001,
        min_volume_ratio=0.8,  # Reduced requirement
        breakout_strength_threshold=0.6,  # More flexible
        ma_alignment_buffer=0.02
    )
    
    strategy = EnhancedKristjanStrategy(
        config=config,
        start_date='2021-01-01',  # More recent period
        end_date='2024-12-31'
    )
    
    # Use parallel download for better performance
    print("Downloading data with parallel processing...")
    strategy.download_data_parallel(max_tickers=50, max_workers=8)
    
    if not strategy.data:
        print("No data downloaded. Please check your internet connection.")
        return None
    
    # Run backtest
    print("Running enhanced backtest...")
    results = strategy.backtest_portfolio(debug=True)
    
    if results:
        print("Analyzing performance...")
        summary = strategy.analyze_performance()
        return strategy, results, summary
    else:
        print("No successful results. Consider adjusting parameters.")
        return strategy, None, None

if __name__ == "__main__":
    strategy, results, summary = run_enhanced_strategy()