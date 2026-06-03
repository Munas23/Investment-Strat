Okay, here is the Python code demonstrated in the video for the three different lot/trade sizing methods using the backtesting.py library.

The code assumes you have the necessary libraries installed (pandas, pandas_ta, numpy, backtesting, plotly, seaborn, matplotlib). You can install them using pip:
pip install pandas pandas_ta numpy backtesting plotly seaborn matplotlib

It also assumes you have the historical data CSV file (EURUSD Candlestick 5 M BID 01.02.2023-17.02.2024.csv) in the same directory as your script or notebook.

import pandas as pd
import numpy as np
import pandas_ta as ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
# For plotting if needed (not strictly required for backtesting logic)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt

# --- 1. Data Loading and Preprocessing ---
# (Code from ~8:01)
df = pd.read_csv("EURUSD Candlestick 5 M BID 01.02.2023-17.02.2024.csv") # Make sure this file path is correct
# Clean column name and format datetime
df["Gmt time"]=df["Gmt time"].str.replace(".000","")
df['Gmt time']=pd.to_datetime(df['Gmt time'], format='%d.%m.%Y %H:%M:%S')
# Rename columns for clarity if needed (backtesting.py expects 'Open', 'High', 'Low', 'Close')
# df.rename(columns={'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Gmt time': 'Time'}, inplace=True) # Optional renaming if columns differ
df = df.set_index('Gmt time')
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
def calculate_rsi_signal_windowed(rsi_series):
    rsi_signal = np.zeros(len(rsi_series))
    window_size = 5 # Example window size
    for i in range(len(rsi_series)):
        window_start = max(0, i - window_size + 1) # Adjusting to get correct window size
        window = rsi_series[window_start:i+1] # Includes the current value, as intended
        # Apply conditions within the window
        if not window.empty and (window > 50.1).all():
            rsi_signal[i] = 2 # Uptrend signal
        elif not window.empty and (window < 49.9).all():
            rsi_signal[i] = 1 # Downtrend signal
        else:
             rsi_signal[i] = 0 # Else, it remains 0
    return rsi_signal

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
        # Calculate stop loss and take profit levels
        slatr = self.slcoef * self.data.ATR[-1]
        TPSLRatio = self.TPSLRatio

        # Trading logic
        if self.signal1 == 2 and len(self.trades) == 0: # Buy Signal and no open trade
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            # The 'size' parameter will change based on the sizing method
            # self.buy(sl=sl1, tp=tp1, size=calculated_size) # Placeholder

        elif self.signal1 == 1 and len(self.trades) == 0: # Sell Signal and no open trade
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            # The 'size' parameter will change based on the sizing method
            # self.sell(sl=sl1, tp=tp1, size=calculated_size) # Placeholder

# --- Method 1: Fixed Lot/Trade Size ---
# (Code from ~10:15)
class FixedSizeStrategy(BaseStrategy):
    mysize = 3000 # Fixed trade size (e.g., 0.03 lots in MT4/5 if 1 lot = 100,000)

    def next(self):
        slatr = self.slcoef * self.data.ATR[-1]
        TPSLRatio = self.TPSLRatio

        if self.signal1 == 2 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.mysize) # Use fixed size

        elif self.signal1 == 1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.mysize) # Use fixed size

print("\n--- Backtesting Method 1: Fixed Size ---")
# Select a smaller slice for faster backtesting/optimization if desired
dfopt = df[-10000:-5000] # Example slice
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

        if self.signal1 == 2 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] - slatr
            tp1 = self.data.Close[-1] + slatr * TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.mysize) # Use equity percentage size

        elif self.signal1 == 1 and len(self.trades) == 0:
            sl1 = self.data.Close[-1] + slatr
            tp1 = self.data.Close[-1] - slatr * TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.mysize) # Use equity percentage size

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
        slatr = self.slcoef * self.data.ATR[-1] # Stop loss distance in price points
        TPSLRatio = self.TPSLRatio

        # --- Lot sizing considering risk --- (Code from ~16:31)
        # Pip value calculation depends on the quote currency and account currency.
        # Assuming EUR/USD and USD account: 1 pip = 0.0001 USD per unit for mini lots?
        # More accurately, pip value changes with price. A simplified approximation:
        # Pip size for most pairs (adjust for JPY pairs)
        pip_size = 1e-4
        # Value of 1 pip for 1 standard lot (100,000 units) in account currency (USD assumed)
        # This is an approximation and might need adjustment based on broker/pair specifics
        # The video's formula seems slightly off, this is a common way:
        # pip_value_per_lot = pip_size / self.data.Close[-1] * 100000 # More complex, needs account currency consideration
        # Simpler approach for EURUSD on USD account: pip value is often ~$10 per standard lot
        # Let's use the formula derived in the video for consistency, although it mixes concepts:
        # It calculates the value of 1 pip movement for a STANDARD LOT (100k) in the quote currency (USD)
        # then converts it to account currency (assuming USD). Needs careful checking for other pairs.
        pip_value = (pip_size / self.data.Close[-1]) * 100000 # Value of 1 pip for 1 standard lot in USD (for EURUSD)
        # This might need refinement based on exact broker pip value calculation.
        # The video uses 1e-4 / price * 1e5 which simplifies to 10 / price
        pip_value = 10 / self.data.Close[-1] # Simplified approximation based on video formula interpretation for EURUSD/USD Account

        # Calculate the size based on risk percentage
        # Risk Amount = risk_perc * equity
        # Size in Lots = Risk Amount / (StopLossDistance_in_pips * PipValue_per_Lot)
        # StopLossDistance_in_pips = slatr / pip_size
        # Size in Lots = (risk_perc * equity) / ( (slatr / pip_size) * pip_value_per_lot)
        # Size in Units = Size in Lots * 100000
        # Size in Units = (risk_perc * equity) / (slatr * pip_value_per_unit)
        # where pip_value_per_unit = pip_value_per_lot / 100000 = pip_size / self.data.Close[-1] (for USD quote)

        # Let's stick to the video's apparent formula for size in UNITS:
        # Size = Risk Amount (in currency) / Amount lost per unit if SL hit (in currency)
        # Risk Amount = self.risk_perc * self.equity
        # Amount lost per unit if SL hit = slatr (stop distance in price)
        # Size = (self.risk_perc * self.equity) / slatr --- THIS IS INCORRECT, mixes currency and price points.

        # Correcting the approach based on the formula shown at 5:10 and 16:33:
        # Lot Size (Units) = (Risk Amount in currency) / (Stop Loss distance in currency PER UNIT)
        # Risk Amount = self.risk_perc * self.equity
        # Stop Loss distance in currency PER UNIT = slatr (distance in price) * value_of_one_price_point_per_unit
        # For non-JPY pairs on MT4/5, 1 point = 0.00001, value is approx point_size / price * units_per_lot / units_per_lot
        # Stop Loss distance in pips = slatr / pip_size
        # Stop Loss distance in currency = Stop Loss distance in pips * pip_value
        # size_in_units = (self.risk_perc * self.equity) / (slatr * pip_value / 100000) # Incorrect pip_value definition

        # RE-INTERPRETING the formula at 16:33 (size = int(self.risk_perc * self.equity / (slatr * pip_value)))
        # This implies 'pip_value' is the monetary value of the SL distance *per unit*.
        # Let's redefine pip_value more clearly:
        # Value of 1 pip (0.0001) movement for 1 unit of base currency (EUR) in account currency (USD)
        pip_value_per_unit = pip_size / self.data.Close[-1] # Approx for EURUSD quote=USD, account=USD
        # Total risk in currency for 1 unit if SL is hit
        risk_per_unit_currency = slatr * pip_value_per_unit # This is incorrect - slatr is price points, pip_value_per_unit needs price points

        # LET'S USE THE VIDEO'S DERIVED FORMULA directly (5:10) and definition (16:33) assuming it works in backtesting.py's context
        # Lot Size = (Risk Amount / (Stop Loss in pips * Pip Value)) -- Here Pip Value is likely per Standard Lot
        # Size in Units = int ( (self.risk_perc * self.equity) / ( (slatr / pip_size) * pip_value_per_lot ) ) * 100000
        # Let's use the direct formula shown being implemented, which seems to calculate size in UNITS
        # size = int(self.risk_perc * self.equity / (slatr * pip_value_per_unit)) -- This assumes pip_value was per unit.
        # Trying the code as shown:
        pip_value = (pip_size / self.data.Close[-1]) * 1e5 # Pip value per standard lot (as interpreted from video)
        size = int(self.risk_perc * self.equity / (slatr * pip_value / 1e5) ) # Calculate size in UNITS, dividing pip_value back to per unit basis.
        # The formula int(self.risk_perc * self.equity / (slatr * pip_value)) in the video looks like it assumes pip_value IS per unit risk. Let's try that.
        # Re-calculating pip value as value of 1 point (1e-5) for 1 unit:
        point_size = 1e-5
        value_per_point_per_unit = point_size / self.data.Close[-1] # For EURUSD/USD account
        # Monetary risk if SL is hit for 1 unit
        sl_risk_per_unit = slatr * value_per_point_per_unit # THIS IS STILL WRONG. slatr needs to be points, not ATR value directly.

        # FINAL ATTEMPT - Trusting the formula structure shown at 16:33, assuming `slatr` represents the currency risk per unit for the SL distance.
        # This seems conceptually flawed but might be how the library handles it internally or how the speaker simplified it.
        # Let's stick to the code shown: calculate size in units based on fixed risk %
        # This part requires careful verification based on the specific asset and account currency.
        # The formula from the video at 16:33 seems to be: size = int(self.risk_perc * self.equity / (slatr * pip_value))
        # Where pip_value was defined earlier. Let's assume pip_value = 1 for simplicity here, as the video doesn't fully clarify its calculation within the class.
        # Correct implementation requires converting SL distance (slatr) into currency loss per unit.
        # Let's define pip_value more robustly for EURUSD/USD account:
        pip_value_per_lot = 10 # Approx $10 per pip per standard lot
        # Convert slatr (price difference) to pips
        slatr_pips = slatr / pip_size
        # Calculate total currency risk if SL is hit for 1 lot
        risk_currency_per_lot = slatr_pips * pip_value_per_lot
        # Calculate desired risk amount in currency
        risk_amount_target = self.risk_perc * self.equity
        # Calculate lot size needed
        # size_in_lots = risk_amount_target / risk_currency_per_lot
        # Calculate size in units for backtesting.py (lots * 100k)
        # size_in_units = size_in_lots * 100000
        # size = int( (risk_amount_target / risk_currency_per_lot) * 100000 )
        size = int( (self.risk_perc * self.equity) / (slatr_pips * pip_value_per_lot) * 100000 )

        # Prevent division by zero or negative size
        if size <= 0 or slatr <=0:
             return

        # # Print statement from video for debugging (optional)
        # print(self.equity, slatr, self.data.Close[-1], size)

        # Check TP/SL Ratio Condition (Optional filter from ~6:12)
        tp_distance = slatr * TPSLRatio
        current_tpsl_ratio = tp_distance / slatr if slatr > 0 else 0
        min_tpsl_ratio = 1.5 # Example minimum ratio

        # Original trading logic without TP/SL ratio check first
        # if self.signal1 == 2 and len(self.trades) == 0:
        #     sl1 = self.data.Close[-1] - slatr
        #     tp1 = self.data.Close[-1] + slatr * TPSLRatio
        #     self.buy(sl=sl1, tp=tp1, size=size) # Use calculated risk-based size

        # elif self.signal1 == 1 and len(self.trades) == 0:
        #     sl1 = self.data.Close[-1] + slatr
        #     tp1 = self.data.Close[-1] - slatr * TPSLRatio
        #     self.sell(sl=sl1, tp=tp1, size=size) # Use calculated risk-based size

        # Trading logic WITH TP/SL ratio check (as suggested at 7:01)
        # Note: In this specific strategy setup, TP is defined BY the SL ratio,
        # so the check current_tpsl_ratio >= min_tpsl_ratio is always true if TPSLRatio >= min_tpsl_ratio.
        # This check becomes relevant if TP is determined independently (e.g., targeting a resistance level).
        # For this code, we'll stick to the simpler execution based on the signal.

        if self.signal1 == 2 and len(self.trades) == 0:
             sl1 = self.data.Close[-1] - slatr
             tp1 = self.data.Close[-1] + slatr * TPSLRatio
             # Ensure size is calculated correctly before buying
             if size > 0: # Only trade if size is valid
                 self.buy(sl=sl1, tp=tp1, size=size)

        elif self.signal1 == 1 and len(self.trades) == 0:
             sl1 = self.data.Close[-1] + slatr
             tp1 = self.data.Close[-1] - slatr * TPSLRatio
             # Ensure size is calculated correctly before selling
             if size > 0: # Only trade if size is valid
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


Explanation and Important Notes:

Data: Ensure the CSV file path is correct and the columns are named 'Open', 'High', 'Low', 'Close', and the index is a DatetimeIndex named 'Gmt time' (or adjust the code accordingly). The data needs cleaning as shown.

Indicators: Bollinger Bands (BBL_15_1.5, BBU_15_1.5) and ATR column names are generated by pandas_ta. Make sure these names match in the bollinger_signal function and the next method.

Signals: The TotalSignal combines the RSI trend filter and the Bollinger Band entry condition. 2 means buy, 1 means sell, 0 means no signal.

Backtesting Library: This code uses backtesting.py. Key concepts:

Strategy class: Defines your trading logic.

init(): Runs once at the start. Good for precomputing indicators using self.I().

next(): Runs for each bar/candle. Contains the core logic for entry, exit, SL, TP, and sizing.

self.data: Accesses the OHLCV and indicator data. [-1] gets the most recent completed bar's value.

self.equity: Current account equity.

self.trades: List of currently open trades.

self.buy()/self.sell(): Place orders. The size parameter is crucial for lot sizing.

Method 1 (Fixed Size): The size parameter in self.buy/self.sell is set to a fixed number (self.mysize = 3000). This represents a fixed number of units (or contracts, depending on the asset). For Forex, 3000 units is 0.03 standard lots.

Method 2 (Equity %): The size parameter is set to a value between 0 and 1 (e.g., self.mysize = 0.3). backtesting.py interprets this as a percentage of the available equity (considering margin) to use for the trade. 0.3 means 30%.

Method 3 (Risk %): This is the most complex.

You define a risk_perc (e.g., 0.02 for 2%).

Inside next(), you calculate the required trade size (in units) so that if the stop loss (slatr) is hit, the loss equals risk_perc * self.equity.

The calculation involves the stop loss distance (slatr converted to pips), the target risk amount in currency (risk_perc * self.equity), and the value of one pip per lot (pip_value_per_lot). The final size needs to be converted back to units (multiply by 100,000 for standard lots).

Pip Value: The calculation of pip_value_per_lot is critical and depends heavily on the traded pair and the account currency. The example uses $10 which is a common approximation for EUR/USD with a USD account. You might need a more precise function for other pairs.

The calculated size is then used in self.buy/self.sell.

Optimization: The commented-out optimization section shows how to find the best slcoef and TPSLRatio for the fixed size strategy based on maximizing returns. You could adapt this for other methods as well.

Commissions/Slippage: Realistic backtesting should include commission and potentially slippage. I've added a basic commission (0.0002 or 0.02%).

Remember to adjust file paths, column names, and potentially the pip value calculation based on your specific data and broker conditions.