import pandas as pd
import numpy as np
import pandas_ta as ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import matplotlib.pyplot as plt  # Used for optimization heatmap

# --- 1. Data Loading and Preprocessing ---
# (Code from ~8:01)
df = pd.read_csv("EURUSD Candlestick 5 M BID 01.02.2023-17.02.2024.csv")

# Parse datetime and set as index (required by backtesting.py)
df['Gmt time'] = pd.to_datetime(df['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f')
df.set_index('Gmt time', inplace=True)
df.index.name = 'datetime'

# Ensure correct data types
df['High'] = pd.to_numeric(df['High'], errors='coerce')
df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
df.dropna(inplace=True) # Drop rows with NaN values that might result from coercion

# --- 2. Indicator Calculation ---
# (Code from ~8:12)
df['RSI'] = ta.rsi(df.Close, length=10)
my_bbands = ta.bbands(df.Close, length=15, std=1.5) # Using df.Close directly
df['ATR'] = ta.atr(df.High, df.Low, df.Close, length=7)
# Join Bollinger Bands - ensure correct column names from ta.bbands output
# Common names are BBL_15_1.5, BBM_15_1.5, BBU_15_1.5, BBB_15_1.5, BBP_15_1.5
df = df.join(my_bbands)
df.dropna(inplace=True) # Drop NaNs created by indicators

# --- 3. Signal Generation Functions ---
# (Code from ~8:17) Bollinger Signal
def bollinger_signal(df):
    # Ensure column names match the output of ta.bbands
    lower_band_col = f'BBL_15_1.5' # Adjust if your ta.bbands names columns differently
    upper_band_col = f'BBU_15_1.5' # Adjust if your ta.bbands names columns differently
    condition_buy = df['Close'] < df[lower_band_col]
    condition_sell = df['Close'] > df[upper_band_col]
    df['bollinger_Signal'] = 0  # Default no signal
    df.loc[condition_buy, 'bollinger_Signal'] = 2 # Buy Signal
    df.loc[condition_sell, 'bollinger_Signal'] = 1 # Sell Signal
    return df

df = bollinger_signal(df)

# (Code from ~8:37) RSI Windowed Signal
def calculate_rsi_signal_windowed(rsi_series, window_size=5):
    roll_min = rsi_series.rolling(window_size, min_periods=window_size).min()
    roll_max = rsi_series.rolling(window_size, min_periods=window_size).max()
    return np.where(roll_min > 50.1, 2, np.where(roll_max < 49.9, 1, 0))

# Apply the function to calculate RSI_signal
df['RSI_signal'] = calculate_rsi_signal_windowed(df['RSI'])

# Combine Signals (Code from ~9:04)
df['TotalSignal'] = df.apply(lambda row: row['bollinger_Signal'] if row['bollinger_Signal'] == row['RSI_signal'] else 0, axis=1)

# --- 4. Backtesting Strategy Definition ---

# Base Strategy Class Structure (will be adapted for each method)
class BaseStrategy(Strategy):
    # Define strategy parameters
    slcoef = 1.1 # Stop Loss Coefficient based on ATR
    TPSLRatio = 1.5 # Take Profit / Stop Loss Ratio

    def init(self):
        # Precompute the signal series
        self.signal1 = self.I(lambda x: x, self.data.TotalSignal) # Pass TotalSignal directly

    def next(self):
        pass  # Subclasses implement sizing and trade execution

# --- Method 1: Fixed Lot/Trade Size ---
# (Code from ~10:15)
class FixedSizeStrategy(BaseStrategy):
    mysize = 3000 # Fixed trade size (e.g., 0.03 lots in MT4/5 if 1 lot = 100,000)

    def next(self):
        slatr = self.slcoef * self.data.ATR[-1]
        TPSLRatio = self.TPSLRatio

        if self.signal1[-1] == 2 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.mysize)

        elif self.signal1[-1] == 1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.mysize)

print("\n--- Backtesting Method 1: Fixed Size ---")
# Select a smaller slice for faster backtesting/optimization if desired
dfopt = df[-10000:-5000].copy()  # Slice for faster backtesting/optimization
bt_fixed = Backtest(dfopt, FixedSizeStrategy, cash=250, margin=1/30, commission=0.0002) # Added commission
stats_fixed = bt_fixed.run()
print(stats_fixed)
# bt_fixed.plot() # Optional plot

# --- Method 2: Equity Percentage Lot/Trade Size ---
# (Code from ~14:16)
class EquityPercentageStrategy(BaseStrategy):
    # Size < 1 is interpreted by backtesting.py as a percentage of equity
    mysize = 0.3 # Example: 30% of available equity per trade

    def next(self):
        slatr = self.slcoef * self.data.ATR[-1]
        TPSLRatio = self.TPSLRatio

        if self.signal1[-1] == 2 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.mysize)

        elif self.signal1[-1] == 1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.mysize)

print("\n--- Backtesting Method 2: Equity Percentage ---")
bt_equity = Backtest(dfopt, EquityPercentageStrategy, cash=250, margin=1/30, commission=0.0002)
stats_equity = bt_equity.run()
print(stats_equity)
# bt_equity.plot() # Optional plot


# --- Method 3: Risk Related Lot/Trade Size ---
# (Code from ~15:46)
class RiskBasedStrategy(BaseStrategy):
    risk_perc = 0.02 # Risk 2% of equity per trade

    def next(self):
        slatr = self.slcoef * self.data.ATR[-1]
        TPSLRatio = self.TPSLRatio

        # Risk-based lot sizing for EURUSD / USD account
        # size_in_units = (risk_amount) / (sl_pips * pip_value_per_lot) * 100_000
        pip_size = 1e-4
        pip_value_per_lot = 10  # ~$10 per pip per standard lot (EURUSD/USD account)
        slatr_pips = slatr / pip_size
        size = int((self.risk_perc * self.equity) / (slatr_pips * pip_value_per_lot) * 100000)

        if size <= 0 or slatr <= 0:
            return

        if self.signal1[-1] == 2 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=size)

        elif self.signal1[-1] == 1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=size)


print("\n--- Backtesting Method 3: Risk Based (2% Risk) ---")
bt_risk_2 = Backtest(dfopt, RiskBasedStrategy, cash=250, margin=1/30, commission=0.0002)
stats_risk_2 = bt_risk_2.run()
print(stats_risk_2)
# bt_risk_2.plot() # Optional plot

# Example with 5% risk
class RiskBasedStrategy_5(RiskBasedStrategy): # Inherit and override risk_perc
    risk_perc = 0.05

print("\n--- Backtesting Method 3: Risk Based (5% Risk) ---")
bt_risk_5 = Backtest(dfopt, RiskBasedStrategy_5, cash=250, margin=1/30, commission=0.0002)
stats_risk_5 = bt_risk_5.run()
print(stats_risk_5)
# bt_risk_5.plot() # Optional plot


# --- Optimization Example (as shown in video for fixed size) ---
# Note: Optimization is shown for Method 1 in the video, but can be adapted.
# print("\n--- Optimizing Method 1 ---")
# stats_opt, heatmap = bt_fixed.optimize(
#     slcoef=[i/10 for i in range(10, 26)], # Range 1.0 to 2.5
#     TPSLRatio=[i/10 for i in range(10, 26)], # Range 1.0 to 2.5
#     maximize='Return [%]',
#     max_tries=300, # Adjust as needed
#     random_state=0,
#     return_heatmap=True)

# print("Optimized Fixed Size Strategy Parameters:")
# print(stats_opt._strategy)
# print("Optimized Fixed Size Strategy Stats:")
# print(stats_opt)

# # Plot heatmap if desired
# if heatmap is not None:
#     heatmap_df = heatmap.unstack()
#     plt.figure(figsize=(12, 10))
#     sns.heatmap(heatmap_df, annot=True, cmap='viridis', fmt='.1f')
#     plt.show()


# #Explanation and Important Notes:
# #Data: Ensure the CSV file path is correct and the columns are named 'Open', 'High', 'Low', 'Close', and the index is a DatetimeIndex named 'Gmt time' (or adjust the code accordingly). The data needs cleaning as shown.
# #Indicators: Bollinger Bands (BBL_15_1.5, BBU_15_1.5) and ATR column names are generated by pandas_ta. Make sure these names match in the bollinger_signal function and the next method.
# #Signals: The TotalSignal combines the RSI trend filter and the Bollinger Band entry condition. 2 means buy, 1 means sell, 0 means no signal.

# Backtesting Library: This code uses backtesting.py. Key concepts:

# Strategy class: Defines your trading logic.

# init(): Runs once at the start. Good for precomputing indicators using self.I().

# next(): Runs for each bar/candle. Contains the core logic for entry, exit, SL, TP, and sizing.

# self.data: Accesses the OHLCV and indicator data. [-1] gets the most recent completed bar's value.

# self.equity: Current account equity.

# self.trades: List of currently open trades.

# self.buy()/self.sell(): Place orders. The size parameter is crucial for lot sizing.

# Method 1 (Fixed Size): The size parameter in self.buy/self.sell is set to a fixed number (self.mysize = 3000). This represents a fixed number of units (or contracts, depending on the asset). For Forex, 3000 units is 0.03 standard lots.

# Method 2 (Equity %): The size parameter is set to a value between 0 and 1 (e.g., self.mysize = 0.3). backtesting.py interprets this as a percentage of the available equity (considering margin) to use for the trade. 0.3 means 30%.

# Method 3 (Risk %): This is the most complex.

# You define a risk_perc (e.g., 0.02 for 2%).

# Inside next(), you calculate the required trade size (in units) so that if the stop loss (slatr) is hit, the loss equals risk_perc * self.equity.

# The calculation involves the stop loss distance (slatr converted to pips), the target risk amount in currency (risk_perc * self.equity), and the value of one pip per lot (pip_value_per_lot). The final size needs to be converted back to units (multiply by 100,000 for standard lots).

# Pip Value: The calculation of pip_value_per_lot is critical and depends heavily on the traded pair and the account currency. The example uses $10 which is a common approximation for EUR/USD with a USD account. You might need a more precise function for other pairs.

# The calculated size is then used in self.buy/self.sell.

# Optimization: The commented-out optimization section shows how to find the best slcoef and TPSLRatio for the fixed size strategy based on maximizing returns. You could adapt this for other methods as well.

# Commissions/Slippage: Realistic backtesting should include commission and potentially slippage. I've added a basic commission (0.0002 or 0.02%).

# Remember to adjust file paths, column names, and potentially the pip value calculation based on your specific data and broker conditions.