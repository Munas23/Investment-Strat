# 5LC (5 Level Conviction) Trading Strategies

## Overview

The 5LC strategies are enhanced versions of Mark Minervini's championship methodology, featuring:

1. **Halved Conviction Percentages** - More conservative position sizing (5%-10% vs original 10%-20%)
2. **Market Health Overlay** - Dynamic position sizing based on market conditions
3. **Enhanced Risk Management** - Professional-grade risk controls and analysis

## Key Features

### Position Sizing (Original Minervini Sizes)
- **Conviction 1 (Minimal)**: 10%
- **Conviction 2 (Low)**: 12.5%
- **Conviction 3 (Standard)**: 15%
- **Conviction 4 (High)**: 17.5%
- **Conviction 5 (Maximum)**: 20%

### Market Health Overlay

Dynamic position sizing based on market conditions:

**S&P500 Strategy (SPY-based):**
- **WEAK** (SPY < 20MA AND < 50MA): **0.5x** positions (halve position sizes)
- **STRONG** (SPY > 20MA AND > 50MA AND > 200MA): **2.0x** positions (double position sizes)
- **NORMAL** (other conditions): **1.0x** positions (normal sizing)

**ASX300 Strategy (VAS.AX-based):**
- **WEAK** (VAS.AX < 20MA AND < 50MA): **0.5x** positions
- **STRONG** (VAS.AX > 20MA AND > 50MA AND > 200MA): **2.0x** positions
- **NORMAL** (other conditions): **1.0x** positions

## Strategies Included

### 1. minervini_5lc_sp500_strategy.py
- **Market**: S&P 500 stocks
- **Market Health Indicator**: SPY
- **Benchmark**: SPY
- **Universe**: 500+ US large-cap stocks

### 2. minervini_5lc_asx300_strategy.py  
- **Market**: ASX 300 stocks
- **Market Health Indicator**: VAS.AX
- **Benchmark**: VAS.AX (ASX300 ETF)
- **Universe**: 300+ Australian large-cap stocks

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Ensure you have the fundamental screening module:
```bash
# Copy minervini_fundamentals.py from the parent strategy folder
cp ../Minervini-Complete-Strategy/minervini_fundamentals.py .
```

## Usage

### Running S&P500 Strategy
```python
from minervini_5lc_sp500_strategy import run_5lc_sp500_backtest

results = run_5lc_sp500_backtest()
```

### Running ASX300 Strategy
```python
from minervini_5lc_asx300_strategy import run_5lc_asx300_backtest

results = run_5lc_asx300_backtest()
```

## Expected Improvements

With the market health overlay (0.5x/2.0x multipliers) and original position sizing:

- **Original Minervini position sizes** (10%-20%) with market health adjustments
- **Risk reduction** during market downturns (50% position reduction = 5%-10%)
- **Opportunity maximization** during strong bull markets (100% increase = 20%-40%)
- **Dynamic range**: 5%-40% depending on market conditions and conviction

### Benefits:
- **Market timing integration** with proven Minervini methodology
- **Adaptive position sizing** based on market health
- **Risk management** during bear markets while capturing bull market gains
- **Minimum price filter** set to $1 (market cap determines company size)

## Key Differences from Original Minervini Strategy

### 1. Market Health Adaptive Position Sizing
- **Original**: Static 10-20% position sizes
- **5LC**: Dynamic 5-40% position sizes based on market health
- **Benefit**: Risk reduction in bear markets, opportunity capture in bull markets

### 2. Enhanced Fundamentals Screening
- **Original**: Various minimum price thresholds
- **5LC**: $1 minimum price (market cap determines quality)
- **Benefit**: More opportunities while maintaining quality via market cap filter

### 3. Market Health Integration
- **Original**: No market timing overlay
- **5LC**: SPY/VAS.AX moving average analysis for position sizing
- **Benefit**: Systematic risk management and opportunity capture

## Output Files

Each strategy generates:
- **CSV trade logs**: `5lc_[market]_trades_[timestamp].csv`
- **Pyfolio tear sheets**: Professional performance analysis charts
- **Performance metrics**: Detailed statistics and risk analysis

## Market Regime Analysis

The strategies track and report:
- **Regime changes**: When market health status shifts
- **Trades by regime**: Performance breakdown by market conditions
- **Position sizing impact**: How market health affects actual position sizes

## Risk Management

Enhanced risk controls include:
- **7% stop losses** (unchanged from original)
- **50% profit targets** (home run exits)
- **20% trailing stops** (after 20% gains)
- **12-month maximum hold periods**
- **Dynamic position sizing** based on market health
- **Maximum 6 positions** at any time

## Performance Tracking

Comprehensive analysis includes:
- **Pyfolio integration** for professional tear sheets
- **Benchmark comparison** (SPY for US, VAS.AX for Australia)
- **Risk-adjusted metrics** (Sharpe ratio, max drawdown, volatility)
- **Market regime correlation** analysis

## Historical Performance Context

The market health overlay is particularly effective during:
- **2018 Volatility**: Reduced exposure during -9.6% SPY decline
- **2020 COVID Crash**: Halved positions during initial -9.9% decline
- **2020-2021 Recovery**: Doubled positions during +72.4% SPY rally
- **2022 Inflation Bear**: Reduced exposure during -18.2% SPY decline

## Best Practices

1. **Start Conservative**: Begin with 1.5x/0.75x multipliers instead of 2.0x/0.5x
2. **Monitor Regime Changes**: Watch for market health status shifts
3. **Regular Rebalancing**: Adjust positions as market conditions change
4. **Risk Management**: Never override stop-loss discipline regardless of market regime

## Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **yfinance**: Yahoo Finance data access
- **lumibot**: Backtesting framework
- **pyfolio-reloaded**: Performance analysis and visualization
- **matplotlib**: Plotting and charting

## Support

For questions or issues:
1. Check the original Minervini strategy documentation
2. Review the debug statistics in strategy output
3. Examine the CSV trade logs for detailed trade information
4. Use the Pyfolio reports for performance analysis

## License

This is an enhanced version of the Minervini trading strategies for educational and research purposes. Use at your own risk and always perform thorough testing before live trading.