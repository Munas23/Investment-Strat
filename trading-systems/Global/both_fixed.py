"""
Fixed version of both.py that addresses "no data skipping" issues
Includes robust error handling and individual symbol processing
"""

import warnings
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
import time
import logging
from typing import Dict, List, Optional

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
class StrategyConfig:
    flagpole_period = 60
    flagpole_min_gain = 0.15  # Reduced from 0.20 for more signals
    consolidation_window = 20
    consolidation_volatility_threshold = 0.6  # Increased for more signals
    ma_fast = 10
    ma_medium = 20
    ma_slow = 50
    max_stop_loss = 0.08
    min_stop_loss = 0.02
    max_position_size = 0.10
    commission = 0.001
    start_date = '2020-01-01'  # Shorter period for testing
    end_date = '2023-12-31'
    min_price = 5.0  # Minimum stock price
    min_volume = 100000  # Minimum daily volume
    max_tickers = 50  # Limit for testing

# --- ROBUST DATA FETCHING ---
def download_single_symbol(symbol: str, start_date: str, end_date: str, max_retries: int = 3) -> Optional[pd.DataFrame]:
    """Download data for a single symbol with retry logic"""
    for attempt in range(max_retries):
        try:
            # Clean symbol
            clean_symbol = symbol.replace('.', '-').replace('/', '-')
            
            # Download data
            data = yf.download(clean_symbol, start=start_date, end=end_date, 
                             progress=False, auto_adjust=True)
            
            if data.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Validate data quality
            if len(data) < 100:  # Need sufficient data
                raise ValueError(f"Insufficient data for {symbol}: {len(data)} days")
            
            # Check for valid prices
            if (data['Close'] <= 0).any() or data['Close'].isnull().all():
                raise ValueError(f"Invalid price data for {symbol}")
            
            # Check volume requirements
            avg_volume = data['Volume'].mean()
            if avg_volume < 50000:  # Minimum liquidity
                raise ValueError(f"Low volume for {symbol}: {avg_volume:,.0f}")
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            logger.debug(f"✓ Downloaded {symbol}: {len(data)} days")
            return data
            
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))  # Exponential backoff
    
    logger.error(f"✗ Failed to download {symbol} after {max_retries} attempts")
    return None

def get_sp500_symbols_safe() -> List[str]:
    """Get S&P 500 symbols with fallback"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        symbols = table['Symbol'].tolist()
        symbols = [s.replace('.', '-') for s in symbols if isinstance(s, str) and len(s) <= 5]
        logger.info(f"Fetched {len(symbols)} S&P 500 symbols")
        return symbols
    except Exception as e:
        logger.error(f"Could not fetch S&P 500 symbols: {e}")
        # Fallback to reliable symbols
        fallback = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT',
            'JPM', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'NFLX', 'ADBE', 'CRM', 'COST',
            'PFE', 'KO', 'PEP', 'ABT', 'TMO', 'ABBV', 'ACN', 'MRK', 'DHR', 'LIN'
        ]
        logger.info(f"Using fallback list of {len(fallback)} symbols")
        return fallback

def download_data_robust(symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
    """Download data for multiple symbols with robust error handling"""
    logger.info(f"Downloading data for {len(symbols)} symbols...")
    
    successful_data = {}
    failed_symbols = []
    
    for i, symbol in enumerate(symbols):
        logger.info(f"Processing {i+1}/{len(symbols)}: {symbol}")
        
        data = download_single_symbol(symbol, start_date, end_date)
        
        if data is not None:
            successful_data[symbol] = data
        else:
            failed_symbols.append(symbol)
        
        # Brief pause to avoid rate limiting
        if i < len(symbols) - 1:
            time.sleep(0.1)
        
        # Progress update
        if (i + 1) % 10 == 0:
            success_rate = len(successful_data) / (i + 1) * 100
            logger.info(f"Progress: {i+1}/{len(symbols)} ({success_rate:.1f}% success rate)")
    
    logger.info(f"Download completed: {len(successful_data)} successful, {len(failed_symbols)} failed")
    
    if failed_symbols:
        logger.info(f"Failed symbols: {failed_symbols[:10]}...")  # Show first 10
    
    return successful_data

def calculate_indicators_safe(data_dict: Dict[str, pd.DataFrame], config: StrategyConfig) -> Dict[str, Dict]:
    """Calculate indicators for each symbol individually to avoid alignment issues"""
    logger.info(f"Calculating indicators for {len(data_dict)} symbols...")
    
    indicators = {}
    successful_calcs = 0
    
    for symbol, data in data_dict.items():
        try:
            # Ensure we have enough data
            if len(data) < max(config.flagpole_period, config.ma_slow) + 10:
                logger.warning(f"Insufficient data for {symbol}: {len(data)} days")
                continue
            
            # Calculate moving averages
            ma_fast = data['close'].rolling(config.ma_fast).mean()
            ma_medium = data['close'].rolling(config.ma_medium).mean()
            ma_slow = data['close'].rolling(config.ma_slow).mean()
            
            # Calculate trend indicators
            highest_high_60d = data['high'].rolling(config.flagpole_period).max()
            lowest_low_60d = data['low'].rolling(config.flagpole_period).min()
            flagpole_gain = (highest_high_60d / lowest_low_60d) - 1
            
            # Entry conditions
            strong_uptrend = flagpole_gain > config.flagpole_min_gain
            near_highs = data['close'] > (highest_high_60d * 0.85)
            flagpole = strong_uptrend & near_highs
            
            # MA alignment
            ma_stacked = (ma_fast > ma_medium) & (ma_medium > ma_slow)
            price_above_mas = (data['close'] > ma_fast) & (data['close'] > ma_medium) & (data['close'] > ma_slow)
            
            # Consolidation
            consolidation_high = data['high'].rolling(config.consolidation_window).max().shift(1)
            consolidation_low = data['low'].rolling(config.consolidation_window).min()
            consolidation_range = (consolidation_high / consolidation_low) - 1
            tight_range = consolidation_range < 0.20
            
            # Volatility
            volatility = data['close'].rolling(config.consolidation_window).std() / \
                        data['close'].rolling(config.consolidation_window).mean()
            low_volatility = volatility <= config.consolidation_volatility_threshold
            
            # Price near MA
            price_near_ma = (data['close'] / ma_medium - 1).abs() < 0.15
            
            # Volume
            volume_ma = data['volume'].rolling(config.consolidation_window).mean()
            volume_ratio = data['volume'] / volume_ma
            volume_confirmation = volume_ratio > 1.2
            
            # Breakout
            breakout = data['close'] > consolidation_high
            
            # Strong close
            daily_range = data['high'] - data['low']
            close_position = (data['close'] - data['low']) / daily_range
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
            exits = data['close'] < ma_medium
            
            # Store indicators for this symbol
            indicators[symbol] = {
                'data': data,
                'ma_fast': ma_fast,
                'ma_medium': ma_medium,
                'ma_slow': ma_slow,
                'entries': entries,
                'exits': exits,
                'flagpole_gain': flagpole_gain,
                'volume_ratio': volume_ratio,
                'volatility': volatility
            }
            
            successful_calcs += 1
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            continue
    
    logger.info(f"Indicators calculated for {successful_calcs} symbols")
    return indicators

def run_simple_backtest(indicators: Dict[str, Dict], config: StrategyConfig) -> Dict:
    """Run a simple backtest without vectorbt dependency"""
    logger.info("Running simple backtest...")
    
    results = {}
    portfolio_value = 100000
    max_positions = 10
    position_size = 0.05  # 5% per position
    
    all_trades = []
    positions = {}
    
    # Get common date range
    all_dates = None
    for symbol, ind in indicators.items():
        if all_dates is None:
            all_dates = ind['data'].index
        else:
            all_dates = all_dates.intersection(ind['data'].index)
    
    if len(all_dates) == 0:
        logger.error("No common date range found")
        return {}
    
    all_dates = sorted(all_dates)
    logger.info(f"Backtesting over {len(all_dates)} days from {all_dates[0]} to {all_dates[-1]}")
    
    # Simple backtest loop
    for date in all_dates:
        # Check exits
        positions_to_close = []
        for symbol in list(positions.keys()):
            if symbol in indicators and date in indicators[symbol]['exits'].index:
                if indicators[symbol]['exits'].loc[date]:
                    positions_to_close.append(symbol)
        
        # Close positions
        for symbol in positions_to_close:
            if symbol in indicators and date in indicators[symbol]['data'].index:
                exit_price = indicators[symbol]['data'].loc[date, 'close']
                entry_info = positions[symbol]
                shares = entry_info['shares']
                pnl = (exit_price - entry_info['price']) * shares
                
                all_trades.append({
                    'symbol': symbol,
                    'entry_date': entry_info['date'],
                    'exit_date': date,
                    'entry_price': entry_info['price'],
                    'exit_price': exit_price,
                    'shares': shares,
                    'pnl': pnl,
                    'return_pct': (exit_price / entry_info['price'] - 1) * 100
                })
                
                del positions[symbol]
        
        # Check entries
        if len(positions) < max_positions:
            for symbol, ind in indicators.items():
                if symbol not in positions and date in ind['entries'].index:
                    if ind['entries'].loc[date] and not pd.isna(ind['entries'].loc[date]):
                        price = ind['data'].loc[date, 'close']
                        position_value = portfolio_value * position_size
                        shares = int(position_value / price)
                        
                        if shares > 0:
                            positions[symbol] = {
                                'date': date,
                                'price': price,
                                'shares': shares
                            }
                            
                            if len(positions) >= max_positions:
                                break
    
    # Calculate results
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        total_pnl = trades_df['pnl'].sum()
        total_return = total_pnl / portfolio_value * 100
        win_rate = (trades_df['return_pct'] > 0).mean() * 100
        avg_return = trades_df['return_pct'].mean()
        
        results = {
            'total_trades': len(all_trades),
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'win_rate_pct': win_rate,
            'avg_return_pct': avg_return,
            'trades': trades_df
        }
        
        logger.info(f"Backtest Results:")
        logger.info(f"  Total Trades: {len(all_trades)}")
        logger.info(f"  Total Return: {total_return:.2f}%")
        logger.info(f"  Win Rate: {win_rate:.1f}%")
        logger.info(f"  Average Return per Trade: {avg_return:.2f}%")
    else:
        logger.warning("No trades generated during backtest period")
        results = {
            'total_trades': 0,
            'total_pnl': 0,
            'total_return_pct': 0,
            'win_rate_pct': 0,
            'avg_return_pct': 0,
            'trades': pd.DataFrame()
        }
    
    return results

def analyze_no_trade_reasons(indicators: Dict[str, Dict], config: StrategyConfig):
    """Analyze why no trades were generated"""
    logger.info("Analyzing why no trades were generated...")
    
    condition_failures = {
        'flagpole_gain': 0,
        'ma_stacked': 0,
        'price_above_mas': 0,
        'tight_range': 0,
        'low_volatility': 0,
        'price_near_ma': 0,
        'breakout': 0,
        'volume_confirmation': 0,
        'strong_close': 0
    }
    
    total_checks = 0
    
    for symbol, ind in indicators.items():
        for date in ind['data'].index[-252:]:  # Check last year
            if date in ind['entries'].index:
                total_checks += 1
                
                # Check individual conditions (simplified)
                if date in ind['flagpole_gain'].index:
                    if ind['flagpole_gain'].loc[date] <= config.flagpole_min_gain:
                        condition_failures['flagpole_gain'] += 1
                
                # Check volatility
                if date in ind['volatility'].index:
                    if ind['volatility'].loc[date] > config.consolidation_volatility_threshold:
                        condition_failures['low_volatility'] += 1
    
    logger.info(f"Condition failure analysis (last 252 days, {total_checks} total checks):")
    for condition, failures in condition_failures.items():
        if total_checks > 0:
            failure_rate = failures / total_checks * 100
            logger.info(f"  {condition}: {failure_rate:.1f}% failure rate")

# --- MAIN FUNCTION ---
def main():
    logger.info("Starting improved backtesting system...")
    
    config = StrategyConfig()
    
    # Get symbols
    symbols = get_sp500_symbols_safe()
    if config.max_tickers:
        symbols = symbols[:config.max_tickers]
    
    logger.info(f"Testing with {len(symbols)} symbols")
    
    # Download data with robust error handling
    data_dict = download_data_robust(symbols, config.start_date, config.end_date)
    
    if not data_dict:
        logger.error("No data could be downloaded. Exiting.")
        return
    
    logger.info(f"Successfully downloaded data for {len(data_dict)} symbols")
    
    # Calculate indicators
    indicators = calculate_indicators_safe(data_dict, config)
    
    if not indicators:
        logger.error("No indicators could be calculated. Exiting.")
        return
    
    # Run backtest
    results = run_simple_backtest(indicators, config)
    
    # Analyze results
    if results['total_trades'] == 0:
        logger.warning("No trades generated!")
        logger.info("Possible reasons:")
        logger.info(f"1. Flagpole gain threshold too high: {config.flagpole_min_gain:.1%}")
        logger.info(f"2. Volatility threshold too low: {config.consolidation_volatility_threshold:.1%}")
        logger.info("3. Too many conditions required simultaneously")
        
        # Analyze why no trades
        analyze_no_trade_reasons(indicators, config)
        
        logger.info("\nSuggested fixes:")
        logger.info("1. Reduce flagpole_min_gain to 0.10")
        logger.info("2. Increase consolidation_volatility_threshold to 0.8")
        logger.info("3. Simplify entry conditions")
    else:
        logger.info("Backtest completed successfully!")
        
        # Show best trades
        if not results['trades'].empty:
            best_trades = results['trades'].nlargest(5, 'return_pct')
            logger.info("\nTop 5 trades:")
            for _, trade in best_trades.iterrows():
                logger.info(f"  {trade['symbol']}: {trade['return_pct']:.1f}% "
                          f"({trade['entry_date'].strftime('%Y-%m-%d')} to {trade['exit_date'].strftime('%Y-%m-%d')})")

if __name__ == "__main__":
    main()