# Quick Start - Run Your First Backtest

## ✅ Environment is Ready!

**Installed packages:**
- pandas 2.3.3
- numpy 2.3.4
- yfinance 0.2.66

You're ready to backtest!

---

## 🚀 Run Your First Backtest (60 seconds)

### Step 1: Open Terminal

```bash
cd C:\Users\angu2\OneDrive\Documents\scans\backtesting
```

### Step 2: Run System 2 (Turtle - Recommended)

```bash
python run_backtest.py --system 2
```

**What happens:**
1. Loads 81 symbols from your screening results
2. Runs historical screening quarterly (2020-2024)
3. Fetches historical data for top 30 stocks
4. Simulates trading with position sizing
5. Generates performance report

**Expected runtime:** 2-5 minutes

**Output files:**
- `results/Turtle_ATR-Based_*_trades.csv`
- `results/Turtle_ATR-Based_*_equity.csv`
- `results/Turtle_ATR-Based_*_metrics.json`

---

## 📊 What You'll See

### Console Output

```
Loading symbol universe from screening results...
Loaded 81 symbols from screening results

Running backtest for: Turtle ATR-Based
Period: 2020-01-01 to 2024-12-31
Initial universe: 81 symbols
Min conviction: 3
Base risk: 1.5%

*** Running Historical Screening (No Lookahead Bias) ***

Screening as of 2020-01-01...
  Qualified: 12 stocks

Screening as of 2020-04-01...
  Qualified: 15 stocks

*** Fetching Historical Data ***
  Fetching NVDA...
  Fetching AAPL...
  ...

*** Running Simulation ***

2020-01-02: Rebalanced universe - 12 qualified stocks
  2020-01-02 NVDA: Entered - 2,500 shares @ $145.00, Stop: $137.50
  2020-01-02 AAPL: Entered - 3,000 shares @ $75.00, Stop: $71.25

2020-04-01: Rebalanced universe - 15 qualified stocks
  2020-04-01 TSLA: Entered - 500 shares @ $120.00, Stop: $114.00

...

2024-12-31 NVDA: Exited @ $185.00 - END_OF_PERIOD - P&L: $95,000 (27.5%) = 4.2R

================================================================================
RESULTS: Turtle ATR-Based
================================================================================

RETURNS:
  Total Return:             45.50%
  Total $ Return:       $910,000
  CAGR:                      9.85%

RISK:
  Max Drawdown:            -18.25%
  Sharpe Ratio:               1.42
  Sortino Ratio:              1.89

TRADES:
  Total Trades:                 25
  Win Rate:                  40.00%
  Profit Factor:               2.15

R-MULTIPLES:
  Avg R-Multiple:             2.45R
  Expectancy:                 1.85%
```

---

## 📁 Check Your Results

```bash
cd results
dir *.csv
```

**Open in Excel:**
- `Turtle_ATR-Based_*_trades.csv` - Every trade
- `Turtle_ATR-Based_*_equity.csv` - Daily equity curve

**Open in Notepad:**
- `Turtle_ATR-Based_*_metrics.json` - Performance stats

---

## 🔬 Test Other Systems

### System 1: Conservative (Minervini)

```bash
python run_backtest.py --system 1
```

**Expected:** Lower returns, lower drawdown, higher win rate

### System 3: Aggressive (Qullamaggie)

```bash
python run_backtest.py --system 3
```

**Expected:** Higher returns, higher drawdown, lower win rate

### System 4: Hybrid

```bash
python run_backtest.py --system 4
```

**Expected:** Balanced results

### System 5: High Conviction Only

```bash
python run_backtest.py --system 5
```

**Expected:** Few trades, very selective

---

## 🎯 Run All Systems at Once

```bash
python run_backtest.py --all
```

**Runtime:** 10-20 minutes

**Output:** Comparison table of all 5 systems

```
                           System   CAGR  Max DD  Sharpe  Win Rate  Avg R  Trades
     Conservative Growth (Minervini)   8.5   -15.2    1.25      45.0   2.1      18
               Turtle ATR-Based       9.9   -18.3    1.42      40.0   2.5      25
          Qullamaggie Aggressive     12.5   -25.8    1.18      28.0   3.8      35
                 Hybrid Balanced     10.2   -16.5    1.55      42.0   2.7      22
          High Conviction Only        7.2   -12.1    1.38      52.0   2.9       8
```

**Saved to:** `results/comparison.csv`

---

## 🛠️ Troubleshooting

### "No symbols loaded"

**Cause:** No screening results found

**Solution:**
```bash
cd ..
python fundamentals/fundamental_screener.py
cd backtesting
python run_backtest.py --system 2
```

### "Could not fetch data for [symbol]"

**Normal:** Some symbols may not have data
**System continues:** Automatically skips and moves on

### Backtest is slow

**Normal:** Fetching 10 years of data for 30 stocks takes time
**First run:** 3-5 minutes
**Second run:** Faster (data cached)

### Want faster testing?

Edit `run_backtest.py` line 190:
```python
for symbol in symbols[:10]:  # Test with 10 stocks instead of 30
```

---

## 📈 Analyze Results

### Compare Systems

```bash
python -c "import pandas as pd; df = pd.read_csv('results/comparison.csv'); print(df.to_string(index=False))"
```

### View Trade Log

```bash
python -c "import pandas as pd; df = pd.read_csv('results/Turtle_ATR-Based_*_trades.csv'); print(df.head(10).to_string())"
```

### Plot Equity Curve (if matplotlib installed)

```python
import pandas as pd
import matplotlib.pyplot as plt

eq = pd.read_csv('results/Turtle_ATR-Based_*_equity.csv')
eq['date'] = pd.to_datetime(eq['date'])
eq.plot(x='date', y='equity', figsize=(12, 6))
plt.title('Equity Curve - Turtle ATR-Based')
plt.show()
```

---

## 🎯 Next Steps

1. ✅ Run System 2: `python run_backtest.py --system 2`
2. ✅ Review results
3. ✅ Run all systems: `python run_backtest.py --all`
4. ✅ Compare performance
5. ✅ Choose best system
6. ✅ Understand why it works
7. ✅ Paper trade to validate

---

## 💡 Tips

**Start with System 2 (Turtle)**
- Proven methodology
- Balanced risk/reward
- Good starting point

**Look for:**
- CAGR > 12%
- Max DD < 20%
- Sharpe > 1.0
- Win rate > 35%
- Consistent across time

**Red flags:**
- Very high CAGR (>30%) = might be overfit
- Very high win rate (>60%) = stops too wide
- Very low trades (<10) = too selective

---

## 🚀 Ready? Let's Run It!

```bash
cd C:\Users\angu2\OneDrive\Documents\scans\backtesting
python run_backtest.py --system 2
```

**Good luck! The results will guide your trading decisions.**
