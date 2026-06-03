# Daily Conviction Scanner - Yahoo Finance Edition

**End-of-day market scanner using free Yahoo Finance data for next-day Interactive Brokers execution**

## Overview

This scanner uses **free Yahoo Finance data** to identify high-conviction trading setups using the proven Minervini methodology, then generates actionable trade signals for execution on Interactive Brokers the next trading day.

### Why This Approach Works

- ✅ **Cost-effective**: Free Yahoo Finance data vs. $40+ monthly for IB subscriptions
- ✅ **Complete daily data**: Full OHLCV bars vs. incomplete intraday data  
- ✅ **End-of-day analysis**: Scan after market close with settled data
- ✅ **Execution flexibility**: Review signals overnight, place orders next day
- ✅ **Proven methodology**: Same 5-level conviction system from your backtests

## Market Coverage

- **S&P 500**: 100+ major US stocks across all sectors
- **ASX300**: 80+ major Australian stocks including Big 4 banks, miners, healthcare
- **Global capability**: Easy to add other Yahoo Finance supported markets

## Workflow

```
1. Market Close (4:00 PM EST / 4:00 PM AEST)
   ↓
2. Run Daily Scanner (5-10 minutes)
   ↓  
3. Review High-Conviction Signals
   ↓
4. Plan Trades for Next Day
   ↓
5. Execute on Interactive Brokers
```

## Installation

```bash
pip install yfinance pandas numpy
```

## Quick Start

### 1. Test the Scanner
```bash
python test_daily_scanner.py
```

### 2. Run Full Scan
```bash
python daily_conviction_scanner.py
```

### 3. Choose Market
- **Option 1**: US Market (S&P 500)
- **Option 2**: ASX Market (ASX300) 
- **Option 3**: Both markets

## Output Files

### Main Results: `daily_conviction_scan_YYYYMMDD_HHMMSS.csv`
Contains all scanned stocks with:
- Conviction levels (0-5)
- Current prices and volume
- Technical indicators
- Reasoning

### Trade Ready: `daily_conviction_scan_YYYYMMDD_HHMMSS_TRADE_READY.csv`  
Filtered to Level 2+ conviction stocks with:
- **IB Action**: BUY orders ready for placement
- **Position Size**: 20-40% based on conviction level
- **Stop Loss Price**: 7% below entry (automatic)
- **Profit Target**: 50% above entry (automatic)

## Conviction Levels

| Level | Position Size | Action | Description |
|-------|---------------|--------|-------------|
| **5** | 40% | BUY | Maximum conviction - Perfect setup |
| **4** | 35% | BUY | High conviction - Strong breakout |  
| **3** | 30% | BUY | Standard conviction - Good setup |
| **2** | 25% | BUY | Low conviction - Trade candidate |
| **1** | 20% | WATCH | Minimal conviction - Watchlist |
| **0** | 0% | IGNORE | No conviction - Skip |

## Example Output

```
HIGH CONVICTION ALERTS (3 stocks):
  AAPL     Level 4 - $225.58 - HIGH conviction: 72, trend: 90, vol: 1.8x, daily: 2.1%
  BHP.AX   Level 3 - $42.15  - STANDARD conviction: 58, trend: 85, vol: 1.4x, daily: 1.8%
  MSFT     Level 3 - $415.75 - STANDARD conviction: 56, trend: 80, vol: 1.2x, daily: 0.9%

TRADE CANDIDATES FOR NEXT DAY (5 stocks):
Symbol   Level  Price      Stop       Target     Daily%   Reason
AAPL     4      $225.58    $209.79    $338.37    2.1%     HIGH conviction: 72, trend: 90...
BHP.AX   3      $42.15     $39.20     $63.23     1.8%     STANDARD conviction: 58, trend...
MSFT     3      $415.75    $386.65    $623.63    0.9%     STANDARD conviction: 56, trend...
GOOGL    2      $165.32    $153.75    $247.98    0.5%     LOW conviction: 42, trend: 75...
CBA.AX   2      $118.50    $110.21    $177.75    1.2%     LOW conviction: 40, trend: 70...
```

## Interactive Brokers Execution

### Next Trading Day:
1. **Review CSV results** from previous evening's scan
2. **Place BUY orders** for Level 2+ conviction stocks:
   - Use **market open** or **limit orders** at/near closing price
   - Set **stop loss** at provided price (7% below)
   - Set **profit target** at provided price (50% above)
   - Use **position sizing** as recommended (20-40%)

### Order Management:
- **Entry**: Market open or breakout above resistance
- **Stop Loss**: 7% below entry price (tight risk control)
- **Profit Target**: 50% above entry (hunt for home runs)
- **Time Exit**: 1 year maximum hold (from backtests)

## Technical Details

### Data Source
- **Yahoo Finance API** via `yfinance` library
- **Daily OHLCV data** with 1-year history minimum
- **Real-time after market close** (data available ~5-10 minutes after close)

### Filtering Criteria
- **Minimum Price**: $5.00 (avoid penny stocks)
- **Minimum Volume**: 100,000 average daily volume
- **Trend Strength**: >60 (strong uptrend required)
- **Historical Data**: 150+ days minimum

### Conviction Scoring Algorithm
```
Base Requirement: Trend Strength > 60 (0-100 scale)

Factor 1: Breakout Power (0-25 points)
- Above 20-day high: +15 points
- Above 50-day high: +10 points

Factor 2: Volume Confirmation (0-30 points)  
- 2x average volume: +30 points
- 1.5x average volume: +20 points
- 1.2x average volume: +10 points

Factor 3: Momentum (0-25 points)
- Daily change >1%: +5 points
- 5-day momentum >2%: +5 points  
- 20-day momentum >5%: +10 points
- 50-day momentum >10%: +5 points

Factor 4: Trend Quality Bonus (0-20 points)
- Extra points for trend strength >60

Total: 0-100 → Converted to 0-5 conviction levels
```

## Automation Options

### Daily Scheduling (Windows)
```cmd
schtasks /create /tn "Daily Scanner" /tr "python C:\path\to\daily_conviction_scanner.py" /sc daily /st 17:00
```

### Daily Scheduling (macOS/Linux)
```bash
# Add to crontab
0 17 * * 1-5 cd /path/to/scanner && python daily_conviction_scanner.py
```

## Comparison vs. Live IB Scanner

| Feature | Daily Yahoo Scanner | Live IB Scanner |
|---------|-------------------|-----------------|
| **Cost** | Free | $40+ monthly |
| **Data Quality** | Complete daily bars | Incomplete ticks |
| **Market Coverage** | Global (ASX, US, EU, Asia) | Subscription dependent |
| **Analysis Time** | End-of-day leisure | Real-time pressure |
| **Execution Timing** | Next day planned | Immediate reactive |
| **Backtesting** | Perfect for development | Limited historical |

## Files Structure

```
Daily-Conviction-Scanner/
├── daily_conviction_scanner.py    # Main scanner
├── test_daily_scanner.py          # Quick verification
├── README.md                      # This documentation
├── daily_scanner.log             # Execution log
└── Output Files/
    ├── daily_conviction_scan_*.csv     # Full results
    └── *_TRADE_READY.csv              # Filtered trade candidates
```

## Best Practices

### Timing
- **Run after market close** (5:00 PM EST / 5:00 PM AEST or later)
- **Review results same evening** for next-day preparation
- **Place orders before market open** or at market open

### Risk Management  
- **Never exceed recommended position sizes** (20-40% max)
- **Always use stop losses** at provided levels
- **Take profits at targets** or use trailing stops
- **Maximum 6 positions** active at once (portfolio concentration)

### Monitoring
- **Check Level 1 stocks daily** for upgrades to Level 2+
- **Review conviction logic** for any surprising results
- **Track performance** of executed trades vs. signals

## Support

For issues or questions:
1. Check `daily_scanner.log` for error messages
2. Verify internet connection and Yahoo Finance access
3. Test with `test_daily_scanner.py` first
4. Review symbol formats (US: AAPL, ASX: CBA.AX)

---

**This scanner implements the same proven methodology from your 312% winning backtest, but with the convenience and cost-effectiveness of free data and next-day execution planning.**