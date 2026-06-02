# Benchmark Comparison - Beat the Market

## Overview

The backtester now automatically compares your systems against **SPY (S&P 500) buy-and-hold** to determine if active trading beats passive investing.

---

## What Gets Benchmarked

### SPY Buy-and-Hold Baseline

**Strategy:** Buy SPY at start, hold until end
- No rebalancing
- No stock picking
- No timing
- Minimal effort

**This is what you need to beat!**

If your system doesn't beat SPY, you're better off just buying the index.

---

## How It Works

### 1. Benchmark Calculation

At the start of every backtest:
```
BENCHMARK: SPY Buy-and-Hold
SPY Total Return: 95.50%
SPY CAGR:         14.25%

Your systems need to beat 14.25% CAGR to outperform SPY!
```

### 2. System Comparison

Each system shows **Alpha** (outperformance vs SPY):

```
RESULTS: Turtle ATR-Based

RETURNS:
  CAGR:                     16.85%
  Benchmark (SPY):          14.25%
  Alpha vs SPY:             +2.60%  ✓

Your system beat SPY by 2.60% per year!
```

### 3. Comparison Table

When running all systems:

```
                        System   CAGR   Alpha  Max DD  Sharpe  Win Rate  Avg R  Trades
           SPY (Buy & Hold)     14.25    0.00    0.00    0.00      0.00   0.00       0
  Conservative Growth (M)        8.50   -5.75  -15.20    1.25     45.00   2.10      18
        Turtle ATR-Based        16.85   +2.60  -18.30    1.42     40.00   2.50      25
   Qullamaggie Aggressive       18.50   +4.25  -25.80    1.18     28.00   3.80      35
          Hybrid Balanced       17.20   +2.95  -16.50    1.55     42.00   2.70      22
   High Conviction Only         12.20   -2.05  -12.10    1.38     52.00   2.90       8
```

**Alpha Column:**
- Positive (+) = Beats SPY ✓
- Negative (-) = Underperforms ✗

---

## Interpreting Results

### Good Alpha (System Worth Using)

**Example:**
```
System CAGR:      18.5%
SPY CAGR:         14.25%
Alpha:            +4.25%  ✓
```

**Means:**
- You make 4.25% more per year than SPY
- On $2M: Extra $85,000/year
- Worth the effort!

### Bad Alpha (Just Buy SPY)

**Example:**
```
System CAGR:       8.5%
SPY CAGR:         14.25%
Alpha:            -5.75%  ✗
```

**Means:**
- You make 5.75% LESS per year than SPY
- On $2M: Lose $115,000/year vs SPY
- Not worth it - just buy index!

---

## Risk-Adjusted Alpha

**Alpha alone isn't enough - consider risk:**

### System A:
```
CAGR:        18.5%
Alpha:       +4.25%
Max DD:      -25.8%
Sharpe:       1.18
```

### System B:
```
CAGR:        16.0%
Alpha:       +1.75%
Max DD:      -15.2%
Sharpe:       1.55
```

**Which is better?**
- System A: Higher alpha BUT higher risk
- System B: Lower alpha BUT much safer

**Answer:** Depends on your risk tolerance!

---

## SPY Historical Performance

**Typical SPY Returns (2020-2024):**

| Period | SPY CAGR | Notes |
|--------|----------|-------|
| 2020-2024 | ~12-15% | Bull market with 2022 correction |
| 2010-2020 | ~13% | Long bull run |
| 2000-2020 | ~7% | Includes 2 crashes |

**Your backtester tests:** 2020-2024 (recent period)

---

## Minimum Alpha Targets

### To Justify Active Trading:

**After costs:**
- Minimum: +2% alpha (worth effort)
- Good: +3-5% alpha (solid system)
- Excellent: +5%+ alpha (great system)

**Why?**
- Trading takes time
- Execution slippage
- Stress and monitoring
- Tax implications (short-term gains)

**If alpha < 2%:** Just buy SPY and save yourself the work!

---

## Example Output

### Single System Backtest

```bash
$ python run_backtest.py --system 2

================================================================================
BENCHMARK: SPY Buy-and-Hold
================================================================================
SPY Total Return: 95.50%
SPY CAGR:         14.25%

Your systems need to beat 14.25% CAGR to outperform SPY!
================================================================================

Running backtest for: Turtle ATR-Based
...

================================================================================
RESULTS: Turtle ATR-Based
================================================================================

RETURNS:
  Total Return:           118.50%
  Total $ Return:      $2,370,000
  CAGR:                    16.85%
  Benchmark (SPY):         14.25%
  Alpha vs SPY:            +2.60%  ✓

RISK:
  Max Drawdown:            -18.30%
  Sharpe Ratio:               1.42

✓ System beats SPY by 2.6% per year!
✓ On $2M, that's $52,000 extra per year
```

### All Systems Comparison

```bash
$ python run_backtest.py --all

...runs all 5 systems...

Comparison saved to backtesting/results/comparison.csv

                        System   CAGR   Alpha  Max DD  Sharpe  Win Rate  Avg R  Trades
           SPY (Buy & Hold)     14.25    0.00    0.00    0.00      0.00   0.00       0
  Conservative Growth (M)        8.50   -5.75  -15.20    1.25     45.00   2.10      18  ✗
        Turtle ATR-Based        16.85   +2.60  -18.30    1.42     40.00   2.50      25  ✓
   Qullamaggie Aggressive       18.50   +4.25  -25.80    1.18     28.00   3.80      35  ✓
          Hybrid Balanced       17.20   +2.95  -16.50    1.55     42.00   2.70      22  ✓
   High Conviction Only         12.20   -2.05  -12.10    1.38     52.00   2.90       8  ✗

Winner: Qullamaggie Aggressive (+4.25% alpha)
```

---

## Decision Framework

### Step 1: Check Alpha
```
If Alpha > +2%: Continue evaluation
If Alpha < +2%: Just buy SPY (not worth it)
```

### Step 2: Check Risk-Adjusted
```
If Sharpe > 1.0 AND Max DD < 25%: Good system
If Sharpe < 1.0 OR Max DD > 30%: Too risky
```

### Step 3: Check Consistency
```
If Win Rate > 35% AND Profit Factor > 1.5: Reliable
If Win Rate < 30% OR Profit Factor < 1.2: Unreliable
```

### Step 4: Decide
```
All checks pass: Use this system
Any check fails: Keep SPY or refine system
```

---

## Common Scenarios

### Scenario 1: System Beats SPY

```
System CAGR:  17.5%
SPY CAGR:     14.25%
Alpha:        +3.25%
Max DD:       -18%
Sharpe:        1.45
```

**Decision:** ✓ Use this system!
- Outperforms benchmark
- Acceptable risk
- Good risk-adjusted returns

---

### Scenario 2: Higher Return, Too Risky

```
System CAGR:  22%
SPY CAGR:     14.25%
Alpha:        +7.75%
Max DD:       -42%
Sharpe:        0.85
```

**Decision:** ✗ Too risky, use SPY
- Great alpha BUT
- Drawdown unbearable (-42%)
- Low Sharpe (poor risk-adjusted)
- Could lose half your capital

---

### Scenario 3: Lower Risk, Lower Return

```
System CAGR:  11%
SPY CAGR:     14.25%
Alpha:        -3.25%
Max DD:       -8%
Sharpe:        1.65
```

**Decision:** ✗ Underperforms, use SPY
- Lower risk BUT
- Negative alpha
- Missing out on returns
- SPY better choice

---

### Scenario 4: Close Call

```
System CAGR:  15.5%
SPY CAGR:     14.25%
Alpha:        +1.25%
Max DD:       -16%
Sharpe:        1.28
```

**Decision:** ⚠️ Marginal - depends on you
- Slight outperformance
- But extra work and taxes
- Maybe not worth it
- SPY safer choice

---

## Why This Matters

**Without benchmark:**
- "My system made 15% CAGR - great!"
- But SPY made 18% - you lost money vs index!

**With benchmark:**
- "My system made 15% vs SPY's 12% - +3% alpha"
- Beating market by 3% = success!

**The goal isn't high returns - it's beating the benchmark!**

---

## Tax Implications (Important!)

### SPY Buy-and-Hold:
- No taxes until you sell
- Long-term capital gains (lower rate)
- Tax-efficient

### Active Trading:
- Taxes on every trade
- Short-term capital gains (higher rate)
- Less tax-efficient

**Example:**
```
Trading System Alpha: +2%
Tax drag:             -1.5%
Net Alpha:            +0.5%  (barely worth it!)

Better to just buy SPY and avoid the hassle.
```

**Minimum alpha after taxes: +3-4%**

---

## Summary

✅ **Backtester now includes:**
- SPY buy-and-hold benchmark
- Alpha calculation (outperformance vs SPY)
- Automatic comparison in results
- Benchmark row in comparison table

✅ **Look for:**
- Alpha > +2-3%
- Sharpe > 1.0
- Max DD < 25%
- Consistent performance

✅ **Remember:**
- Beating SPY is the minimum bar
- Factor in taxes and effort
- Risk-adjusted returns matter
- Simple often wins (SPY is fine!)

---

**If your system doesn't beat SPY by 2%+, just buy SPY and sleep well!**
