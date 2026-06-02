"""
Global Multi-Market Backtesting Engine
Supports ASX300, S&P500, Russell2000, FTSE, DAX markets
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from utils.market_data import MarketDataHandler
from utils.base_strategy import BaseStrategy

class GlobalBacktester:
    """
    Multi-market backtesting engine that can test strategies across
    ASX300, S&P500, Russell2000, FTSE, and DAX markets
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.market_config_path = os.path.join(config_dir, "markets.json")
        self.strategy_config_path = os.path.join(config_dir, "strategy_config.json")
        
        # Initialize components
        self.data_handler = MarketDataHandler(self.market_config_path)
        self.logger = self._setup_logging()
        
        # Load configurations
        self.market_config = self._load_config(self.market_config_path)
        self.strategy_config = self._load_config(self.strategy_config_path)
        
        # Results storage
        self.results = {}
        self.benchmark_data = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the backtester"""
        logger = logging.getLogger("global_backtester")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            os.makedirs('logs', exist_ok=True)
            file_handler = logging.FileHandler('logs/backtester.log')
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config from {config_path}: {e}")
            return {}
    
    def download_market_data(self, markets: List[str], start_date: str, end_date: str,
                           max_symbols_per_market: int = 50, save_data: bool = True) -> Dict[str, Dict]:
        """
        Download data for multiple markets
        
        Args:
            markets: List of market names (SP500, ASX300, etc.)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_symbols_per_market: Maximum symbols to download per market
            save_data: Whether to save data to files
        
        Returns:
            Dictionary of market data
        """
        self.logger.info(f"Starting data download for markets: {markets}")
        self.logger.info(f"Date range: {start_date} to {end_date}")
        self.logger.info(f"Max symbols per market: {max_symbols_per_market}")
        
        all_market_data = {}
        
        for market in markets:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"DOWNLOADING {market.upper()} DATA")
            self.logger.info(f"{'='*60}")
            
            try:
                # Download market data
                market_data = self.data_handler.download_market_data(
                    market=market,
                    start_date=start_date,
                    end_date=end_date,
                    max_symbols=max_symbols_per_market
                )
                
                if market_data:
                    all_market_data[market] = market_data
                    
                    # Download benchmark data
                    benchmark_data = self.data_handler.get_benchmark_data(
                        market=market,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if benchmark_data is not None:
                        self.benchmark_data[market] = benchmark_data
                    
                    # Save data if requested
                    if save_data:
                        os.makedirs('data', exist_ok=True)
                        self.data_handler.save_market_data(market, 'data')
                    
                    self.logger.info(f"✓ {market} data download completed: {len(market_data)} symbols")
                    
                else:
                    self.logger.error(f"✗ Failed to download {market} data")
                    
            except Exception as e:
                self.logger.error(f"Error downloading {market} data: {e}")
                continue
        
        self.logger.info(f"\nData download completed for {len(all_market_data)} markets")
        return all_market_data
    
    def run_strategy_backtest(self, strategy: BaseStrategy, market: str, 
                            market_data: Dict[str, pd.DataFrame],
                            start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Run backtest for a single strategy on a single market
        
        Args:
            strategy: Strategy instance
            market: Market name
            market_data: Market data dictionary
            start_date: Start date
            end_date: End date
        
        Returns:
            Backtest results
        """
        self.logger.info(f"Running {strategy.name} on {market}...")
        
        try:
            # Initialize strategy
            strategy.initialize()
            
            # Get trading symbols
            symbols = list(market_data.keys())
            
            # Create trading calendar from benchmark or first symbol
            if market in self.benchmark_data:
                trading_dates = self.benchmark_data[market].index
            else:
                # Use first symbol's dates as proxy
                first_symbol_data = next(iter(market_data.values()))
                trading_dates = first_symbol_data.index
            
            # Filter dates to backtest period
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            trading_dates = trading_dates[(trading_dates >= start_dt) & (trading_dates <= end_dt)]
            
            self.logger.info(f"Trading period: {trading_dates[0]} to {trading_dates[-1]} ({len(trading_dates)} days)")
            
            # Run backtest day by day
            for i, date in enumerate(trading_dates):
                # Update market data for this date
                for symbol in symbols:
                    if symbol in market_data and date in market_data[symbol].index:
                        # Get data up to current date
                        symbol_data = market_data[symbol].loc[:date]
                        strategy.update_market_data(symbol, symbol_data)
                
                # Process trading day
                strategy.process_day(date, symbols)
                
                # Progress update
                if (i + 1) % 50 == 0:
                    self.logger.info(f"  Processed {i + 1}/{len(trading_dates)} days...")
            
            # Get performance stats
            performance_stats = strategy.get_performance_stats()
            
            # Add market info
            performance_stats['market'] = market
            performance_stats['strategy'] = strategy.name
            performance_stats['start_date'] = start_date
            performance_stats['end_date'] = end_date
            performance_stats['trading_days'] = len(trading_dates)
            
            # Calculate benchmark comparison if available
            if market in self.benchmark_data:
                benchmark_return = self._calculate_benchmark_return(
                    self.benchmark_data[market], start_date, end_date
                )
                performance_stats['benchmark_return_pct'] = benchmark_return
                performance_stats['excess_return_pct'] = performance_stats['total_return_pct'] - benchmark_return
            
            self.logger.info(f"✓ {strategy.name} on {market} completed")
            self.logger.info(f"  Total Return: {performance_stats['total_return_pct']:.2f}%")
            self.logger.info(f"  Sharpe Ratio: {performance_stats['sharpe_ratio']:.2f}")
            self.logger.info(f"  Max Drawdown: {performance_stats['max_drawdown_pct']:.2f}%")
            
            return performance_stats
            
        except Exception as e:
            self.logger.error(f"Error running {strategy.name} on {market}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _calculate_benchmark_return(self, benchmark_data: pd.DataFrame, 
                                   start_date: str, end_date: str) -> float:
        """Calculate benchmark return for period"""
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            period_data = benchmark_data[(benchmark_data.index >= start_dt) & 
                                       (benchmark_data.index <= end_dt)]
            
            if len(period_data) < 2:
                return 0.0
            
            start_price = period_data['close'].iloc[0]
            end_price = period_data['close'].iloc[-1]
            
            return (end_price / start_price - 1) * 100
            
        except Exception:
            return 0.0
    
    def run_multi_market_backtest(self, strategies: List[BaseStrategy], 
                                 markets: List[str], start_date: str, end_date: str,
                                 max_symbols_per_market: int = 50,
                                 download_fresh_data: bool = True) -> Dict[str, Any]:
        """
        Run backtest across multiple strategies and markets
        
        Args:
            strategies: List of strategy instances
            markets: List of market names
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_symbols_per_market: Maximum symbols per market
            download_fresh_data: Whether to download fresh data
        
        Returns:
            Comprehensive results dictionary
        """
        self.logger.info("\n" + "="*80)
        self.logger.info("GLOBAL MULTI-MARKET BACKTESTING ENGINE")
        self.logger.info("="*80)
        self.logger.info(f"Strategies: {[s.name for s in strategies]}")
        self.logger.info(f"Markets: {markets}")
        self.logger.info(f"Period: {start_date} to {end_date}")
        self.logger.info("="*80)
        
        # Download market data if needed
        if download_fresh_data:
            all_market_data = self.download_market_data(
                markets=markets,
                start_date=start_date,
                end_date=end_date,
                max_symbols_per_market=max_symbols_per_market
            )
        else:
            self.logger.info("Using existing market data...")
            all_market_data = self.data_handler.market_data
        
        # Run backtests
        all_results = {}
        
        for strategy in strategies:
            strategy_results = {}
            
            for market in markets:
                if market not in all_market_data:
                    self.logger.warning(f"No data available for {market}, skipping...")
                    continue
                
                # Run single backtest
                result = self.run_strategy_backtest(
                    strategy=strategy,
                    market=market,
                    market_data=all_market_data[market],
                    start_date=start_date,
                    end_date=end_date
                )
                
                if result:
                    strategy_results[market] = result
                
                # Export strategy results
                os.makedirs('results', exist_ok=True)
                strategy.export_results('results')
            
            all_results[strategy.name] = strategy_results
        
        # Store results
        self.results = all_results
        
        # Generate summary report
        self._generate_summary_report(all_results)
        
        return all_results
    
    def _generate_summary_report(self, results: Dict[str, Any]):
        """Generate comprehensive summary report"""
        self.logger.info("\n" + "="*80)
        self.logger.info("BACKTEST SUMMARY REPORT")
        self.logger.info("="*80)
        
        # Create summary DataFrame
        summary_data = []
        
        for strategy_name, strategy_results in results.items():
            for market, result in strategy_results.items():
                summary_data.append({
                    'Strategy': strategy_name,
                    'Market': market,
                    'Total Return (%)': result.get('total_return_pct', 0),
                    'Annualized Return (%)': result.get('annualized_return_pct', 0),
                    'Sharpe Ratio': result.get('sharpe_ratio', 0),
                    'Max Drawdown (%)': result.get('max_drawdown_pct', 0),
                    'Win Rate (%)': result.get('win_rate_pct', 0),
                    'Total Trades': result.get('num_trades', 0),
                    'Final Value': result.get('final_value', 0),
                    'Benchmark Return (%)': result.get('benchmark_return_pct', 0),
                    'Excess Return (%)': result.get('excess_return_pct', 0)
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            
            # Display summary
            print("\nPERFORMANCE SUMMARY:")
            print(summary_df.round(2).to_string(index=False))
            
            # Save summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_file = f"results/backtest_summary_{timestamp}.csv"
            summary_df.to_csv(summary_file, index=False)
            self.logger.info(f"\nSummary report saved to: {summary_file}")
            
            # Generate charts
            self._create_performance_charts(summary_df, timestamp)
        
        self.logger.info("\n" + "="*80)
        self.logger.info("BACKTEST COMPLETED")
        self.logger.info("="*80)
    
    def _create_performance_charts(self, summary_df: pd.DataFrame, timestamp: str):
        """Create performance visualization charts"""
        try:
            plt.style.use('default')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Global Multi-Market Backtest Results', fontsize=16, fontweight='bold')
            
            # 1. Total Return by Strategy and Market
            pivot_returns = summary_df.pivot(index='Strategy', columns='Market', values='Total Return (%)')
            sns.heatmap(pivot_returns, annot=True, fmt='.1f', cmap='RdYlGn', 
                       center=0, ax=axes[0,0], cbar_kws={'label': 'Total Return (%)'})
            axes[0,0].set_title('Total Returns by Strategy & Market')
            
            # 2. Sharpe Ratio comparison
            pivot_sharpe = summary_df.pivot(index='Strategy', columns='Market', values='Sharpe Ratio')
            sns.heatmap(pivot_sharpe, annot=True, fmt='.2f', cmap='viridis', 
                       ax=axes[0,1], cbar_kws={'label': 'Sharpe Ratio'})
            axes[0,1].set_title('Sharpe Ratios by Strategy & Market')
            
            # 3. Return vs Risk scatter
            axes[1,0].scatter(summary_df['Max Drawdown (%)'], summary_df['Total Return (%)'], 
                            c=summary_df['Sharpe Ratio'], cmap='plasma', s=100, alpha=0.7)
            axes[1,0].set_xlabel('Max Drawdown (%)')
            axes[1,0].set_ylabel('Total Return (%)')
            axes[1,0].set_title('Risk vs Return')
            
            # Add colorbar for scatter plot
            scatter = axes[1,0].collections[0]
            plt.colorbar(scatter, ax=axes[1,0], label='Sharpe Ratio')
            
            # 4. Win Rate vs Average Trade
            if 'Win Rate (%)' in summary_df.columns and summary_df['Total Trades'].sum() > 0:
                axes[1,1].bar(range(len(summary_df)), summary_df['Win Rate (%)'], 
                            color='skyblue', alpha=0.7)
                axes[1,1].set_xlabel('Strategy-Market Combination')
                axes[1,1].set_ylabel('Win Rate (%)')
                axes[1,1].set_title('Win Rates')
                axes[1,1].set_xticks(range(len(summary_df)))
                axes[1,1].set_xticklabels([f"{row['Strategy']}-{row['Market']}" 
                                          for _, row in summary_df.iterrows()], 
                                         rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Save chart
            chart_file = f"results/performance_chart_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Performance charts saved to: {chart_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating charts: {e}")
    
    def get_available_markets(self) -> List[str]:
        """Get list of available markets"""
        if 'markets' in self.market_config:
            return list(self.market_config['markets'].keys())
        return []
    
    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """Validate date range"""
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            if start_dt >= end_dt:
                self.logger.error("Start date must be before end date")
                return False
            
            if end_dt > pd.Timestamp.now():
                self.logger.warning("End date is in the future")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Invalid date format: {e}")
            return False