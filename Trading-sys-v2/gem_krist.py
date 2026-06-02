import yfinance as yf
import vectorbt as vbt
import numpy as np
import pandas as pd
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# Suppress warnings that are not critical for this backtest
warnings.simplefilter('ignore', ConvergenceWarning)
warnings.simplefilter('ignore', UserWarning)

def get_sp500_tickers():
    """Scrapes the list of S&P 500 tickers from Wikipedia."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        tickers = table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        print(f"Successfully fetched {len(tickers)} S&P 500 tickers.")
        return tickers
    except Exception as e:
        print(f"Could not fetch S&P 500 tickers due to an error: {e}")
        print("Falling back to a static list of tickers.")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD']

# --- 1. Robust Data Fetching ---
print("Fetching S&P 500 component data from Yahoo Finance (individual download)...")
tickers = get_sp500_tickers()
start_date = '2018-01-01'
end_date = '2023-12-31'

# Define parameters BEFORE the loop
fast_ma_window = 10
medium_ma_window = 20
slow_ma_window = 50
initial_move_window = 60
consolidation_window = 20

# Create lists to hold the data series for each stock
all_closes = []
all_highs = []
all_lows = []
successful_tickers = []
total_tickers = len(tickers)

for i, ticker in enumerate(tickers):
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        if not data.empty and len(data) > slow_ma_window:
            all_closes.append(data['Close'])
            all_highs.append(data['High'])
            all_lows.append(data['Low'])
            successful_tickers.append(ticker)
    except Exception as e:
        pass # Silently skip failed downloads

print(f"\nFinished processing. {len(successful_tickers)} of {total_tickers} tickers had valid data.")
print("Combining all successful downloads into final dataframes...")

if not successful_tickers:
    print("No data could be downloaded. Exiting.")
    exit()

# Concatenate each list of series into a single DataFrame.
# This process naturally aligns them by date.
price = pd.concat(all_closes, axis=1, keys=successful_tickers)
high = pd.concat(all_highs, axis=1, keys=successful_tickers)
low = pd.concat(all_lows, axis=1, keys=successful_tickers)

# --- THE FIX: REMOVED THE ERRONEOUS align_func LINE ---
# The pd.concat step above is sufficient for alignment.

print(f"Data prepared. Proceeding with {price.shape[1]} stocks that have full history.")


# --- 2. Calculate Indicators ---
print("Calculating indicators...")
ma_fast = vbt.MA.run(price, window=fast_ma_window)
ma_medium = vbt.MA.run(price, window=medium_ma_window)
ma_slow = vbt.MA.run(price, window=slow_ma_window)

# --- 3. Generate Entry and Exit Signals ---
print("Generating trading signals based on Kullamägi's rules...")
# Rule 1: Strong Prior Uptrend
highest_high_60d = high.rolling(initial_move_window).max()
lowest_low_60d = low.rolling(initial_move_window).min()
prior_move_pct = (highest_high_60d / lowest_low_60d) - 1
strong_uptrend = prior_move_pct > 0.30

# Rule 2: Moving Average Confirmation
ma_stacked_up = (ma_fast.ma > ma_medium.ma) & (ma_medium.ma > ma_slow.ma)

# Rule 3: Breakout Trigger
consolidation_high = high.rolling(consolidation_window).max().shift(1)
breakout = price > consolidation_high

# Rule 4: Tight Consolidation
price_near_ma = (price / ma_medium.ma - 1).abs() < 0.15

# Combine all entry conditions
entries = strong_uptrend & ma_stacked_up & breakout & price_near_ma

# Exit Signal
exits = price.vbt.crossed_below(ma_medium.ma)

# --- 4. Run the Backtest ---
print("Running portfolio backtest...")
portfolio = vbt.Portfolio.from_signals(
    close=price,
    entries=entries,
    exits=exits,
    sl_stop=0.08,
    fees=0.001,
    freq='D',
    init_cash=100000,
    size=0.10,
    size_type='percent',
    group_by=True
)

# --- 5. Analyze and Print Results ---
print("\n--- Backtest Results ---")
print(portfolio.stats())

print("\n--- Top 5 Performing Stocks ---")
print(portfolio.deep_getattr('total_return').nlargest(5))

print("\n--- Worst 5 Performing Stocks ---")
print(portfolio.deep_getattr('total_return').nsmallest(5))

print("\nPlotting overall portfolio performance...")
portfolio.plot(title="Kristjan Kullamägi Breakout Strategy on S&P 500").show()

# Plot the best performing stock to visualize the trades
best_stock_symbol = portfolio.deep_getattr('total_return').idxmax()
print(f"\nPlotting trades for the best performing stock: {best_stock_symbol}")

price[best_stock_symbol].vbt.plot(
    trace_kwargs=dict(name='Price')
).add_trace(
    ma_fast.ma[best_stock_symbol].vbt.plot(trace_kwargs=dict(name='MA10')).data[0]
).add_trace(
    ma_medium.ma[best_stock_symbol].vbt.plot(trace_kwargs=dict(name='MA20')).data[0]
).add_trace(
    ma_slow.ma[best_stock_symbol].vbt.plot(trace_kwargs=dict(name='MA50')).data[0]
)
portfolio[best_stock_symbol].trades.plot(
    close=price[best_stock_symbol],
    title=f'Trades for {best_stock_symbol}'
).show()