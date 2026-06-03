"""
Working version based on successful patterns from other Trading System folders
Uses the exact same download methods that work in turtle_sp500.py and backtester.py
"""

import warnings
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt
import time
import logging

warnings.filterwarnings('ignore')

# Setup simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
class StrategyConfig:
    flagpole_period = 60
    flagpole_min_gain = 0.15  # Start with lower threshold
    consolidation_window = 20
    consolidation_volatility_threshold = 0.6
    ma_fast = 10
    ma_medium = 20
    ma_slow = 50
    max_stop_loss = 0.08
    commission = 0.001
    start_date = '2020-01-01'
    end_date = '2023-12-31'
    max_tickers = 30  # Start small

# --- DATA DOWNLOAD (Using working patterns) ---
def get_sp500_symbols():
    """Get S&P 500 symbols - exactly like turtle_sp500.py"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        tickers = table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        print(f"Fetched {len(tickers)} S&P 500 tickers.")
        return tickers
    except Exception as e:
        print(f"Could not fetch S&P 500 tickers: {e}")
        # Fallback to known working symbols
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT',
            'JPM', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'NFLX', 'ADBE', 'CRM', 'COST',
            'PFE', 'KO', 'PEP', 'ABT', 'TMO', 'ABBV', 'ACN', 'MRK', 'DHR', 'LIN'
        ]

def download_data_like_turtle(tickers, start_date, end_date):
    """Download data exactly like turtle_sp500.py (which works)"""
    print(f"Downloading data for {len(tickers)} stocks from {start_date} to {end_date}...")
    
    stock_data = {}
    failed = []
    
    for i, symbol in enumerate(tickers):
        try:
            print(f"Downloading {i+1}/{len(tickers)}: {symbol}")
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if len(data) > 50:  # Need sufficient data like turtle
                stock_data[symbol] = data
                print(f"  ✓ {symbol}: {len(data)} days")
            else:
                failed.append(symbol)
                print(f"  ✗ {symbol}: insufficient data")
                
        except Exception as e:
            failed.append(symbol)
            print(f"  ✗ {symbol}: {e}")
        
        # Brief delay to be nice to the API
        time.sleep(0.1)
    
    print(f"\nSuccessfully downloaded {len(stock_data)} stocks")
    if failed:
        print(f"Failed: {failed}")
    
    return stock_data

def calculate_indicators_simple(stock_data, config):
    """Calculate indicators for each stock individually (avoiding alignment issues)"""
    print(f"Calculating indicators for {len(stock_data)} stocks...")
    
    results = {}
    
    for symbol, data in stock_data.items():
        try:
            # Ensure we have enough data
            if len(data) < config.ma_slow + config.flagpole_period:
                print(f"Skipping {symbol}: insufficient data ({len(data)} days)")
                continue
            
            # Calculate moving averages
            data['MA_Fast'] = data['Close'].rolling(config.ma_fast).mean()
            data['MA_Medium'] = data['Close'].rolling(config.ma_medium).mean()
            data['MA_Slow'] = data['Close'].rolling(config.ma_slow).mean()
            
            # Calculate flagpole (trend strength)
            data['High_60D'] = data['High'].rolling(config.flagpole_period).max()
            data['Low_60D'] = data['Low'].rolling(config.flagpole_period).min()
            data['Flagpole_Gain'] = (data['High_60D'] / data['Low_60D']) - 1
            
            # Calculate consolidation
            data['Consol_High'] = data['High'].rolling(config.consolidation_window).max().shift(1)
            data['Consol_Low'] = data['Low'].rolling(config.consolidation_window).min()
            data['Consol_Range'] = (data['Consol_High'] / data['Consol_Low']) - 1
            
            # Calculate volatility
            data['Returns'] = data['Close'].pct_change()
            data['Volatility'] = data['Returns'].rolling(config.consolidation_window).std()
            data['Avg_Price'] = data['Close'].rolling(config.consolidation_window).mean()
            data['Vol_Ratio'] = data['Volatility'] / (data['Avg_Price'] * 0.01)  # Normalize
            
            # Volume analysis
            data['Volume_MA'] = data['Volume'].rolling(config.consolidation_window).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_MA']
            
            # Entry conditions (simplified)
            conditions = {
                'strong_trend': data['Flagpole_Gain'] > config.flagpole_min_gain,
                'near_highs': data['Close'] > (data['High_60D'] * 0.85),
                'ma_aligned': (data['MA_Fast'] > data['MA_Medium']) & (data['MA_Medium'] > data['MA_Slow']),
                'price_above_ma': data['Close'] > data['MA_Medium'],
                'tight_range': data['Consol_Range'] < 0.20,
                'low_volatility': data['Vol_Ratio'] < config.consolidation_volatility_threshold,
                'volume_surge': data['Volume_Ratio'] > 1.2,
                'breakout': data['Close'] > data['Consol_High']
            }
            
            # Combine conditions
            data['Entry_Signal'] = (
                conditions['strong_trend'] &
                conditions['near_highs'] &
                conditions['ma_aligned'] &
                conditions['price_above_ma'] &
                conditions['tight_range'] &
                conditions['low_volatility'] &
                conditions['volume_surge'] &
                conditions['breakout']
            )
            
            # Exit signal
            data['Exit_Signal'] = data['Close'] < data['MA_Medium']
            
            # Count signals
            entry_count = data['Entry_Signal'].sum()
            print(f"  {symbol}: {entry_count} entry signals")
            
            results[symbol] = data
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            continue
    
    print(f"Indicators calculated for {len(results)} stocks")
    return results

def run_simple_backtest_like_turtle(processed_data, config):
    """Run simple backtest similar to turtle_sp500.py approach"""
    print("\nRunning simple backtest...")
    
    # Portfolio setup
    initial_capital = 100000
    cash = initial_capital
    positions = {}
    all_trades = []
    portfolio_values = []
    
    max_positions = 5
    position_size = 0.05  # 5% per position
    
    # Get common date range
    all_dates = None
    for symbol, data in processed_data.items():
        if all_dates is None:
            all_dates = data.index
        else:
            all_dates = all_dates.intersection(data.index)
    
    if len(all_dates) == 0:
        print("No common dates found!")
        return None
    
    all_dates = sorted(all_dates)
    print(f"Backtesting over {len(all_dates)} days: {all_dates[0]} to {all_dates[-1]}")
    
    # Simple backtest loop
    for i, date in enumerate(all_dates):
        current_portfolio_value = cash
        
        # Check exits first
        positions_to_close = []
        for symbol in list(positions.keys()):
            if symbol in processed_data and date in processed_data[symbol].index:
                if processed_data[symbol].loc[date, 'Exit_Signal']:
                    positions_to_close.append(symbol)
        
        # Close positions
        for symbol in positions_to_close:
            pos = positions[symbol]
            exit_price = processed_data[symbol].loc[date, 'Close']
            proceeds = pos['shares'] * exit_price * (1 - config.commission)
            cash += proceeds
            
            # Record trade
            pnl = proceeds - pos['cost']
            pnl_pct = (exit_price / pos['entry_price'] - 1) * 100
            
            all_trades.append({
                'symbol': symbol,
                'entry_date': pos['entry_date'],
                'exit_date': date,
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'shares': pos['shares'],
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
            print(f"EXIT: {symbol} @ ${exit_price:.2f}, P&L: {pnl_pct:.1f}%")
            del positions[symbol]
        
        # Check entries
        if len(positions) < max_positions:
            for symbol, data in processed_data.items():
                if symbol not in positions and date in data.index:
                    if data.loc[date, 'Entry_Signal'] and not pd.isna(data.loc[date, 'Entry_Signal']):
                        if data.loc[date, 'Entry_Signal']:  # Signal is True
                            price = data.loc[date, 'Close']
                            position_value = (cash + current_portfolio_value) * position_size
                            shares = int(position_value / price)
                            cost = shares * price * (1 + config.commission)
                            
                            if shares > 0 and cost <= cash:
                                cash -= cost
                                positions[symbol] = {
                                    'entry_date': date,
                                    'entry_price': price,
                                    'shares': shares,
                                    'cost': cost
                                }
                                print(f"ENTER: {symbol} @ ${price:.2f}, {shares} shares")
                                
                                if len(positions) >= max_positions:
                                    break
        
        # Calculate portfolio value
        for symbol, pos in positions.items():
            if symbol in processed_data and date in processed_data[symbol].index:
                current_price = processed_data[symbol].loc[date, 'Close']
                current_portfolio_value += pos['shares'] * current_price
        
        portfolio_values.append({
            'date': date,
            'value': current_portfolio_value,
            'cash': cash,
            'positions': len(positions)
        })
        
        # Progress update
        if (i + 1) % 100 == 0:
            print(f"Processed {i+1}/{len(all_dates)} days, Portfolio: ${current_portfolio_value:,.0f}")
    
    # Results
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        final_value = portfolio_values[-1]['value']
        total_return = (final_value / initial_capital - 1) * 100
        
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Initial Capital: ${initial_capital:,}")
        print(f"Final Value: ${final_value:,.0f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Total Trades: {len(all_trades)}")
        
        if len(trades_df) > 0:
            win_rate = (trades_df['pnl_pct'] > 0).mean() * 100
            avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean()
            avg_loss = trades_df[trades_df['pnl_pct'] < 0]['pnl_pct'].mean()
            
            print(f"Win Rate: {win_rate:.1f}%")
            print(f"Avg Win: {avg_win:.2f}%")
            print(f"Avg Loss: {avg_loss:.2f}%")
            
            # Best trades
            print(f"\nTop 5 Trades:")
            best_trades = trades_df.nlargest(5, 'pnl_pct')
            for _, trade in best_trades.iterrows():
                print(f"  {trade['symbol']}: {trade['pnl_pct']:.1f}%")
        
        return {
            'trades': trades_df,
            'portfolio': pd.DataFrame(portfolio_values),
            'final_return': total_return
        }
    else:
        print("\n=== NO TRADES GENERATED ===")
        print("Possible reasons:")
        print(f"1. Flagpole threshold too high: {config.flagpole_min_gain:.1%}")
        print(f"2. Volatility threshold too low: {config.consolidation_volatility_threshold:.1%}")
        print("3. Too many conditions combined")
        
        return None

def main():
    """Main function using working patterns"""
    print("=" * 60)
    print("WORKING TRADING SYSTEM - Based on Successful Patterns")
    print("=" * 60)
    
    config = StrategyConfig()
    
    # Get symbols using working method
    tickers = get_sp500_symbols()
    if config.max_tickers:
        tickers = tickers[:config.max_tickers]
    
    print(f"Testing with {len(tickers)} symbols")
    
    # Download data using turtle method (which works)
    stock_data = download_data_like_turtle(tickers, config.start_date, config.end_date)
    
    if not stock_data:
        print("❌ No data downloaded. Exiting.")
        return
    
    print(f"✓ Downloaded data for {len(stock_data)} stocks")
    
    # Process data
    processed_data = calculate_indicators_simple(stock_data, config)
    
    if not processed_data:
        print("❌ No indicators calculated. Exiting.")
        return
    
    # Run backtest
    results = run_simple_backtest_like_turtle(processed_data, config)
    
    if results:
        print("✅ Backtest completed successfully!")
    else:
        print("⚠️ No trades generated - consider adjusting parameters")

if __name__ == "__main__":
    main()