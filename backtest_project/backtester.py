import yfinance as yf
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, cross_under
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 1000)

def get_data_manually(tickers, start_date, end_date):
    """Download data for multiple tickers and return combined DataFrame"""
    print(f"Starting manual data download for {len(tickers)} tickers...")
    all_dfs = {}
    
    for i, ticker in enumerate(tickers):
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
            if df.empty: 
                continue
            
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_cols): 
                continue
                
            # Add ticker column for identification
            df['Ticker'] = ticker
            all_dfs[ticker] = df[required_cols + ['Ticker']]
            
            if (i + 1) % 50 == 0: 
                print(f"--- Progress: Fetched {i+1} of {len(tickers)} tickers ---")
        except Exception as e:
            print(f"({i+1}/{len(tickers)}) Could not download {ticker}: {e}")

    if not all_dfs:
        print("CRITICAL ERROR: No data could be successfully downloaded for any ticker.")
        return None

    print("\nAll downloads complete. Concatenating data...")
    # Combine all dataframes
    combined_df = pd.concat(all_dfs.values(), ignore_index=False)
    combined_df = combined_df.sort_index()
    
    print("Data successfully prepared for backtesting.")
    return combined_df

class MultiStockStrategy(Strategy):
    # Strategy parameters
    risk_percent = 0.02
    stop_loss_percent = 0.05
    
    def init(self):
        # Get market data (SPY) for market filter
        spy_data = yf.download('SPY', start='2020-01-01', end='2023-12-31', progress=False, auto_adjust=True)
        self.spy_close = spy_data['Close'].reindex(self.data.index, method='ffill')
        self.spy_ma20 = self.spy_close.rolling(20).mean()
        
        # Calculate indicators for all stocks
        self.atr = talib.ATR(self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.ma20 = talib.SMA(self.data.Close, timeperiod=20)
        self.ma50 = talib.SMA(self.data.Close, timeperiod=50)
        self.ma200 = talib.SMA(self.data.Close, timeperiod=200)
        
        # Pre-calculate rolling statistics for efficiency
        self.close_60_ago = self.data.Close.shift(60)
        self.volume_prev = self.data.Volume.shift(1)
        self.high_40_max = self.data.High.shift(1).rolling(40).max()
        self.atr_40_min = self.atr.rolling(40).min().shift(1)
        self.atr_40_max = self.atr.rolling(40).max().shift(1)
        
        # Track positions per stock
        self.stock_positions = {}
        
    def next(self):
        current_date = self.data.index[-1]
        
        # Market filter: Only trade when SPY > MA20
        if len(self.spy_close) > 0 and len(self.spy_ma20) > 0:
            spy_current = self.spy_close.iloc[-1] if not pd.isna(self.spy_close.iloc[-1]) else 0
            spy_ma20_current = self.spy_ma20.iloc[-1] if not pd.isna(self.spy_ma20.iloc[-1]) else 0
            market_healthy = spy_current > spy_ma20_current
        else:
            market_healthy = True
            
        # Get current values
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        
        # Skip if we don't have enough data
        if len(self.data) < 200:
            return
            
        # Calculate entry conditions
        # 1. Up 30% over 60 days
        if pd.isna(self.close_60_ago[-1]):
            return
        up_30_pct = (current_close / self.close_60_ago[-1] - 1) > 0.3
        
        # 2. ATR in range (volatility filter)
        if pd.isna(self.atr_40_min[-1]) or pd.isna(self.atr_40_max[-1]):
            atr_in_range = False
        else:
            atr_in_range = (self.atr_40_max[-1] / self.atr_40_min[-1] - 1) < 0.40
        
        # 3. Breakout above 40-day high
        if pd.isna(self.high_40_max[-1]):
            breakout = False
        else:
            breakout = current_close > self.high_40_max[-1]
        
        # 4. Volume increased
        if pd.isna(self.volume_prev[-1]):
            volume_increased = False
        else:
            volume_increased = current_volume > self.volume_prev[-1]
        
        # 5. Above moving averages
        above_ma = (current_close > self.ma50[-1]) and (current_close > self.ma200[-1])
        
        # Combined entry signal
        entry_signal = (up_30_pct and atr_in_range and breakout and 
                       volume_increased and above_ma and market_healthy)
        
        # Exit signal: Close below MA20
        exit_signal = current_close < self.ma20[-1]
        
        # Position management
        if entry_signal and not self.position:
            # Calculate position size based on risk
            account_balance = self.equity
            capital_at_risk = account_balance * self.risk_percent
            risk_per_share = current_close * self.stop_loss_percent
            
            if risk_per_share > 0:
                size = capital_at_risk / risk_per_share
                size = min(size, account_balance / current_close)  # Don't exceed available cash
                
                if size > 0:
                    self.buy(size=size, sl=current_close * (1 - self.stop_loss_percent))
                    
        elif exit_signal and self.position:
            self.position.close()

def run_single_stock_backtest(ticker_data, ticker_name):
    """Run backtest for a single stock"""
    try:
        # Prepare data for backtesting.py format
        bt_data = ticker_data.copy()
        bt_data = bt_data.dropna()
        
        if len(bt_data) < 200:  # Need enough data for indicators
            return None
            
        bt = Backtest(bt_data, MultiStockStrategy, cash=100000, commission=0.0)
        stats = bt.run()
        
        return {
            'ticker': ticker_name,
            'stats': stats,
            'backtest': bt
        }
    except Exception as e:
        print(f"Error backtesting {ticker_name}: {e}")
        return None

def run_multi_stock_backtest(combined_data):
    """Run backtest across multiple stocks"""
    print("\n--- RUNNING MULTI-STOCK BACKTEST ---")
    
    results = []
    tickers = combined_data['Ticker'].unique()
    
    for ticker in tickers:
        print(f"Backtesting {ticker}...")
        ticker_data = combined_data[combined_data['Ticker'] == ticker].copy()
        ticker_data = ticker_data.drop('Ticker', axis=1)
        
        result = run_single_stock_backtest(ticker_data, ticker)
        if result:
            results.append(result)
    
    return results

def analyze_results(results):
    """Analyze and display results from multiple backtests"""
    if not results:
        print("No successful backtests to analyze.")
        return
    
    print(f"\n--- ANALYSIS OF {len(results)} SUCCESSFUL BACKTESTS ---")
    
    # Collect statistics
    summary_stats = []
    for result in results:
        stats = result['stats']
        summary_stats.append({
            'Ticker': result['ticker'],
            'Total Return': stats['Return [%]'],
            'Buy & Hold Return': stats['Buy & Hold Return [%]'],
            'Sharpe Ratio': stats['Sharpe Ratio'],
            'Max Drawdown': stats['Max. Drawdown [%]'],
            'Trades': stats['# Trades'],
            'Win Rate': stats['Win Rate [%]'],
            'Best Trade': stats['Best Trade [%]'],
            'Worst Trade': stats['Worst Trade [%]']
        })
    
    summary_df = pd.DataFrame(summary_stats)
    
    # Display top performers
    print("\n--- TOP 10 PERFORMERS BY TOTAL RETURN ---")
    top_performers = summary_df.sort_values('Total Return', ascending=False).head(10)
    print(top_performers.to_string(index=False))
    
    print("\n--- TOP 10 BY SHARPE RATIO ---")
    top_sharpe = summary_df.sort_values('Sharpe Ratio', ascending=False).head(10)
    print(top_sharpe[['Ticker', 'Total Return', 'Sharpe Ratio', 'Max Drawdown', 'Trades']].to_string(index=False))
    
    # Overall statistics
    print("\n--- OVERALL STATISTICS ---")
    print(f"Average Return: {summary_df['Total Return'].mean():.2f}%")
    print(f"Median Return: {summary_df['Total Return'].median():.2f}%")
    print(f"Average Sharpe Ratio: {summary_df['Sharpe Ratio'].mean():.2f}")
    print(f"Average Max Drawdown: {summary_df['Max Drawdown'].mean():.2f}%")
    print(f"Average Trades per Stock: {summary_df['Trades'].mean():.1f}")
    print(f"Average Win Rate: {summary_df['Win Rate'].mean():.2f}%")
    
    # Save detailed results
    summary_df.to_csv('backtest_results_summary.csv', index=False)
    print(f"\nDetailed results saved to 'backtest_results_summary.csv'")
    
    return summary_df

def plot_combined_results(results, start_date, end_date):
    """Plot combined portfolio performance"""
    print("\nCreating combined portfolio visualization...")
    
    # Get SPY data for comparison
    spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False, auto_adjust=True)
    spy_returns = spy_data['Close'].pct_change().dropna()
    spy_cumulative = (1 + spy_returns).cumprod()
    
    # Get VIX data
    vix_data = yf.download('^VIX', start=start_date, end=end_date, progress=False, auto_adjust=True)['Close']
    
    # Create visualization
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=('Portfolio Performance Comparison', 'VIX (Market Volatility)')
    )
    
    # Plot SPY benchmark
    fig.add_trace(
        go.Scatter(
            x=spy_cumulative.index,
            y=(spy_cumulative - 1) * 100,
            name='S&P 500 (SPY)',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # Plot VIX
    fig.add_trace(
        go.Scatter(
            x=vix_data.index,
            y=vix_data.values,
            name='VIX',
            line=dict(color='purple', width=1)
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title='Multi-Stock Strategy Performance Analysis',
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        yaxis2_title='VIX Level',
        height=800,
        showlegend=True
    )
    
    fig.show()

if __name__ == "__main__":
    start_date = "2020-01-01"
    end_date = "2023-12-31"
    
    # Get S&P 500 tickers
    try:
        sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        sp500_table = pd.read_html(sp500_url)
        tickers_to_run = [s.replace('.', '-') for s in sp500_table[0]['Symbol'].tolist()]
    except Exception as e:
        print(f"Could not fetch S&P 500 list: {e}. Using test list.")
        tickers_to_run = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX']
    
    # Limit to first 50 tickers for testing (remove this line for full backtest)
    tickers_to_run = tickers_to_run[:50]
    
    # Download data
    combined_data = get_data_manually(tickers_to_run, start_date, end_date)
    
    if combined_data is not None:
        # Run backtests
        results = run_multi_stock_backtest(combined_data)
        
        # Analyze results
        if results:
            summary_df = analyze_results(results)
            plot_combined_results(results, start_date, end_date)
        else:
            print("No successful backtests completed.")
    else:
        print("Could not run backtest because data fetching failed.")