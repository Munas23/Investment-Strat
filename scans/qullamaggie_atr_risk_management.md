# Technical Screener Research: Comprehensive Guide

## Table of Contents
1. [Qullamaggie (Kristjan Kullamägi) Trading Methodology](#1-qullamaggie-kristjan-kullamägi-trading-methodology)
2. [ATR (Average True Range)](#2-atr-average-true-range)
3. [Risk Management Systems](#3-risk-management-systems)

---

# 1. Qullamaggie (Kristjan Kullamägi) Trading Methodology

## Overview
Kristjan Kullamägi, known as **Qullamaggie**, is a Swedish swing trader who has gained significant attention for reportedly turning a small account into tens of millions through disciplined trading strategies. His approach focuses on momentum-driven swing trading, primarily in U.S. equities.

## Core Philosophy
- **Focus**: Momentum-driven swing trading
- **Timeframe**: Daily charts for setup identification, 1-minute/5-minute/60-minute for entries
- **Win Rate**: Approximately 25% (high failure rate but massive winners compensate)
- **Portfolio Size**: No more than 15-20 positions at any time (30+ positions signals market top)

---

## Primary Trading Setups

### Setup 1: Breakout Strategy (Primary)

#### Pre-Breakout Requirements

**Initial Move (Lookback Period):**
```python
# Screening Criteria
lookback_period = 12  # weeks (1-3 months)
initial_move_min = 30  # percent
initial_move_max = 100  # percent
move_duration_min = "few days"
move_duration_max = "few weeks"
```

**Consolidation Phase:**
```python
# Consolidation Criteria
consolidation_min = 2  # weeks
consolidation_max = 8  # weeks (can extend to 2 months)

# Pattern Requirements
pattern = {
    "higher_lows": True,
    "tightening_range": True,
    "price_surfs_10_day_ma": True,
    "price_surfs_20_day_ma": True,
    "50_day_ma_not_far_behind": True,
    "all_mas_rising": True
}
```

**Moving Average Configuration:**
```python
# During consolidation, price must:
# - Surf (stay above and respect) rising 10-day MA
# - Surf rising 20-day MA
# - Have 50-day MA trending upward and close behind
# - All MAs should be rising

ma_10_day = "Simple Moving Average"
ma_20_day = "Simple Moving Average"
ma_50_day = "Simple Moving Average"

# Exit when price closes below:
exit_ma_fast_stocks = 10  # day MA
exit_ma_slow_stocks = 20  # day MA
```

#### Entry Criteria

**Opening Range Breakout:**
```python
# Entry Methods (choose one based on conviction)
entry_timeframes = [
    "1-minute opening range high",
    "5-minute opening range high",
    "60-minute opening range high",
    "daily chart breakout"
]

# Entry Trigger
entry_trigger = "Break of high of opening range bar"
entry_execution = "Enter on break of high with limit order"

# Alternative simple method
simple_entry = "Enter when stock breaks out on daily chart"
```

**Stop Loss Placement:**
```python
# Initial Stop
stop_loss = "Low of the day"

# Stop Loss Validation
stop_loss_max_width = "1 ATR or 1 ADR (Average Daily Range)"

# If stop is wider than ATR/ADR, skip the trade
if stop_loss_width > ATR or stop_loss_width > ADR:
    skip_trade = True
```

#### Position Sizing

```python
# Position Size Range
min_position_size = 5   # percent of portfolio
max_position_size = 25  # percent of portfolio
typical_position = 10   # percent (most common)
high_conviction = 15    # percent

# Factors affecting size:
factors = {
    "liquidity": "Higher liquidity = larger position",
    "conviction": "Higher conviction = larger position",
    "risk_level": "Lower risk = larger position"
}

# Liquidity Rule (for large accounts like $100M)
max_position_liquidity = 0.01  # 1% of stock's daily dollar volume
```

#### Exit Strategy

**Partial Profit Taking:**
```python
# Time-based partial exit
days_to_partial = [3, 4, 5]  # 3-5 days
partial_size = [1/3, 1/2]     # Sell 33-50% of position

# Example
if days_in_trade in days_to_partial:
    sell_shares = position_size * 0.33  # or 0.50
    move_stop_to_breakeven = True
```

**Trailing Stop for Remainder:**
```python
# Choose based on stock speed
if stock_speed == "fast":
    trailing_ma = 10  # day MA
elif stock_speed == "slow":
    trailing_ma = 20  # day MA

# Exit Rule
if close_price < trailing_ma:
    exit_position = True

# Alternative: Trail stop at low of candle that crosses MA
if candle_crosses_ma:
    new_stop = candle_low
```

**Early Exit Signals:**
```python
# Break of consolidation
if close_below_10_ma and close_below_20_ma:
    momentum_broken = True
    exit_position = True

# Failed breakout
if breakout_fails_quickly:
    exit_position = True
```

---

### Setup 2: High Tight Flag (HTF)

#### Criteria

```python
# Prior Move
prior_move_percent = 90  # minimum
prior_move_max = 100     # approximately
prior_move_duration = "short period"

# Consolidation/Flag
consolidation_retracement_min = 15  # percent from peak
consolidation_retracement_max = 25  # percent from peak
consolidation_volume = "diminished"  # lower than average

# Signal
market_sentiment = "latent bullish"

# Entry
entry_trigger = "Breakout from tight flag pattern"
```

---

### Setup 3: Episodic Pivot (EP)

#### Fundamental Requirements

```python
# Pre-Event Conditions
price_action_lookback = [3, 4, 5, 6]  # months
pre_event_pattern = "flat or inactive"

# Earnings/Sales Growth (Ideal)
earnings_growth_ideal = 100  # percent YoY (triple digit)
sales_growth_ideal = 100     # percent YoY (triple digit)

# Acceptable Growth
earnings_growth_min = 50     # percent YoY (mid/high double digits)
sales_growth_min = 50        # percent YoY
```

#### Gap and Volume Requirements

```python
# Gap Criteria
gap_percent_min = 10         # percent minimum
gap_time_window = [20, 30, 40, 50, 60]  # minutes after open

# Catalyst Types
catalysts = [
    "earnings surprise",
    "FDA approval",
    "analyst upgrade",
    "unexpected good news"
]

# Volume Requirements
volume_requirement_1 = "Massive volume near open"
volume_ideal = "Average daily volume traded in first 15-20 minutes"

# Alternative Volume Metrics
volume_multiple_min = 5      # 5-10x average daily volume
volume_multiple_max = 10     # for gaps
volume_alternative_min = 2   # 2-4x average minimum
volume_alternative_max = 4
volume_absolute_min = 100000 # shares (100k minimum)

# First Half Hour
first_30_min_volume = "heavy trading volume"
```

#### Float Criteria

```python
# Float Percentage Thresholds
float_manipulation_risk = 20   # percent (below = high risk)
float_ideal_min = 20           # percent
float_ideal_max = 50           # percent (ideal breakout range)

# Color Coding for Screener
if float_percent < 20:
    flag = "RED"    # manipulation risk
elif 20 <= float_percent <= 50:
    flag = "GREEN"  # ideal breakout range
else:
    flag = "YELLOW" # higher float
```

#### Entry Rules

```python
# Wait for early day high break
entry_condition = "Stock moves above early day high"
entry_timing = "Within 20-60 minutes of market open"

# Entry Method
entry_style = "Full position at entry (no scaling in)"

# Alternative conservative entry
conservative_entry = "Wait for pullback to 10 or 21 DMA after breakout"
```

#### Exit Strategy

```python
# Quick Exit if No Follow-Through
if time_in_trade < 20:  # minutes
    if not sharp_acceleration:
        exit_immediately = True
        reason = "No immediate momentum - trade likely wrong"

# Stop Loss
stop_loss_ep = "Low of the day"
```

---

### Setup 4: New ATH (All-Time High) Strategy

#### Criteria

```python
# Entry
entry_condition = "Stock breaking to new all-time high"
volume_confirmation = "Above average volume"
moving_average_support = "Price above rising 10, 20, 50 day MAs"

# Same management rules as breakout strategy apply
```

---

## Risk Management Framework

### Win Rate Reality

```python
# Historical Performance
typical_win_rate = 25        # percent (roughly 1 in 4 trades win)
strategy_characteristic = "High failure rate, massive winners"

# Why Low Win Rate Works
win_loss_ratio_typical = 4   # Winners are 4x+ larger than losers
position_sizing = "Tight stops keep losses small"
winners = "Let winners run with trailing stops"
```

### Position Management Rules

```python
# Number of Positions
max_positions_normal = 20
max_positions_warning = 30   # Market pullback indicator

# Position Entry
entry_style = "Full position at entry (no scaling in)"
scaling_in = False

# Position Exit
scale_out_winners = True
exit_losers = "All at once when stop hit"

# Re-entry After Pullback
reentry_opportunity = "Pullback to support levels"
support_levels = [
    "Original breakout point",
    "Significant moving averages (10, 20, 50)"
]
pullback_volume = "Lower volume = healthy pause"
```

---

## Complete Screening Criteria (Code-Ready)

### Breakout Screener

```python
def qullamaggie_breakout_screener(stock):
    """
    Complete Qullamaggie breakout screening criteria
    """
    criteria = {
        # Prior Move (1-3 months)
        "prior_move_12w_pct": (30, 100),

        # Consolidation (2-8 weeks)
        "consolidation_weeks": (2, 8),
        "higher_lows": True,
        "tightening_range": True,

        # Moving Averages
        "price_above_ma10": True,
        "price_above_ma20": True,
        "ma10_rising": True,
        "ma20_rising": True,
        "ma50_rising": True,
        "ma10_above_ma20": True,
        "ma20_above_ma50": True,

        # Entry Signal
        "breaking_consolidation_high": True,
        "volume_above_average": True,

        # Risk Parameters
        "stop_width_max_atr": 1,  # Stop no wider than 1 ATR

        # Liquidity (for large accounts)
        "position_max_pct_daily_volume": 1  # percent
    }
    return criteria


def qullamaggie_ep_screener(stock):
    """
    Complete Qullamaggie Episodic Pivot screening criteria
    """
    criteria = {
        # Pre-Event
        "flat_prior_3_6_months": True,

        # Gap
        "gap_percent_min": 10,

        # Volume
        "volume_first_30min_ratio": (5, 10),  # 5-10x ADV
        "volume_absolute_min": 100000,

        # Float
        "float_percent_min": 20,
        "float_percent_max": 50,

        # Fundamentals
        "earnings_growth_yoy_min": 50,
        "sales_growth_yoy_min": 50,

        # Entry
        "breaking_early_day_high": True,
        "time_since_open_max_minutes": 60,

        # Catalyst
        "has_catalyst": True  # earnings, FDA, upgrade, etc.
    }
    return criteria
```

---

# 2. ATR (Average True Range)

## Definition

**Average True Range (ATR)** is a technical indicator that measures market volatility by calculating the average of true ranges over a specified period. It does NOT indicate price direction, only volatility.

---

## Calculation

### True Range (TR)

The **True Range** is the largest of three values:

```python
def calculate_true_range(high, low, previous_close):
    """
    Calculate True Range for a single period
    """
    range1 = high - low
    range2 = abs(high - previous_close)
    range3 = abs(previous_close - low)

    true_range = max(range1, range2, range3)
    return true_range

# Formula breakdown:
# TR = MAX(
#     Current High - Current Low,
#     |Current High - Previous Close|,
#     |Previous Close - Current Low|
# )
```

### Average True Range (ATR)

```python
def calculate_atr(true_ranges, period=14):
    """
    Calculate ATR using exponential moving average method

    Formula: ATR = [(Previous ATR × (n-1)) + Current TR] ÷ n
    """
    atr_values = []

    # First ATR is simple average
    first_atr = sum(true_ranges[:period]) / period
    atr_values.append(first_atr)

    # Subsequent ATRs use smoothed formula
    for i in range(period, len(true_ranges)):
        current_atr = (
            (atr_values[-1] * (period - 1)) + true_ranges[i]
        ) / period
        atr_values.append(current_atr)

    return atr_values

# Alternative: Simple Moving Average (SMA) method
def calculate_atr_sma(true_ranges, period=14):
    """
    Calculate ATR using simple moving average
    """
    atr_values = []
    for i in range(period - 1, len(true_ranges)):
        atr = sum(true_ranges[i-period+1:i+1]) / period
        atr_values.append(atr)
    return atr_values
```

---

## Period Settings

### Standard Periods

```python
# Most Common
standard_period = 14  # days (default for most platforms)

# For Recent Volatility (Short-term)
short_term_min = 2
short_term_max = 10
short_term_typical = 7

# For Long-term Volatility
long_term_min = 20
long_term_max = 50
long_term_typical = 22  # (approximately 1 trading month)

# Timeframe Application
timeframes = {
    "intraday": "14 periods (5-min, 15-min, hourly bars)",
    "daily": "14 days",
    "weekly": "14 weeks",
    "monthly": "14 months"
}
```

### Period Selection Guide

```python
def select_atr_period(trading_style):
    """
    Select appropriate ATR period based on trading style
    """
    periods = {
        "scalping": (2, 5),
        "day_trading": (7, 14),
        "swing_trading": (14, 20),
        "position_trading": (20, 50)
    }
    return periods.get(trading_style, 14)
```

---

## Applications in Trading

### 1. Stop Loss Placement

#### Basic ATR Stop Formula

```python
def calculate_atr_stop_loss(entry_price, atr, multiplier, position_type):
    """
    Calculate stop loss using ATR

    Args:
        entry_price: Entry price for the trade
        atr: Current ATR value
        multiplier: ATR multiplier (typically 1.5 to 4)
        position_type: "long" or "short"

    Returns:
        stop_loss_price: Calculated stop loss price
    """
    if position_type == "long":
        stop_loss = entry_price - (atr * multiplier)
    elif position_type == "short":
        stop_loss = entry_price + (atr * multiplier)

    return stop_loss

# Example:
# Entry: $50
# ATR: $2
# Multiplier: 2x
# Long Stop: $50 - ($2 * 2) = $46
# Short Stop: $50 + ($2 * 2) = $54
```

#### ATR Multiplier Guide

```python
# Common ATR Multipliers for Stop Loss
multipliers = {
    "tight_stops": 1.5,      # Aggressive, more stop-outs
    "standard": 2.0,         # Most common (Turtle Traders)
    "moderate": 2.5,
    "loose": 3.0,            # More room for volatility
    "very_loose": 4.0        # Long-term positions
}

# By Trading Style
trading_style_multipliers = {
    "day_trading": (1.5, 2.0),
    "swing_trading": (2.0, 3.0),
    "position_trading": (3.0, 4.0)
}

# By Asset Volatility
volatility_multipliers = {
    "low_volatility": 1.5,     # Blue chips, stable stocks
    "medium_volatility": 2.0,  # Most stocks
    "high_volatility": 3.0,    # Tech stocks, small caps
    "very_high_volatility": 4.0  # Penny stocks, crypto
}
```

---

### 2. Position Sizing with ATR

#### The Turtle Traders Method

```python
def turtle_position_sizing(account_size, atr, risk_percent=1, atr_multiplier=2):
    """
    Calculate position size using Turtle Traders methodology

    Turtle Rule: 1 Unit = position where 1N move = 1% of account

    Args:
        account_size: Total trading capital
        atr: Average True Range (called "N" by Turtles)
        risk_percent: Percentage of account to risk (default 1%)
        atr_multiplier: ATR multiple for stop (default 2)

    Returns:
        Dictionary with position sizing details
    """
    # Dollar risk per trade
    dollar_risk = account_size * (risk_percent / 100)

    # Risk per share (2 ATR for Turtles)
    risk_per_share = atr * atr_multiplier

    # Number of shares (1 Unit)
    shares = dollar_risk / risk_per_share

    return {
        "shares": int(shares),
        "dollar_risk": dollar_risk,
        "risk_per_share": risk_per_share,
        "atr": atr,
        "account_risk_percent": risk_percent
    }

# Example:
# Account: $100,000
# ATR: $2.50
# Risk: 1%
# Multiplier: 2x (Turtle standard)
#
# Dollar Risk = $100,000 * 0.01 = $1,000
# Risk per Share = $2.50 * 2 = $5.00
# Shares = $1,000 / $5.00 = 200 shares
```

#### Generic ATR Position Sizing

```python
def atr_position_sizing(account_size, entry_price, atr,
                        risk_percent, atr_multiplier):
    """
    Generic ATR-based position sizing

    This equalizes risk across stocks with different volatility:
    - High volatility (large ATR) = smaller position
    - Low volatility (small ATR) = larger position
    """
    # Calculate dollar risk
    dollar_risk = account_size * (risk_percent / 100)

    # Calculate risk per share
    risk_per_share = atr * atr_multiplier

    # Calculate shares
    shares = dollar_risk / risk_per_share

    # Calculate position value
    position_value = shares * entry_price

    # Calculate position as percent of account
    position_percent = (position_value / account_size) * 100

    return {
        "shares": int(shares),
        "position_value": position_value,
        "position_percent": position_percent,
        "dollar_risk": dollar_risk,
        "risk_per_share": risk_per_share,
        "stop_loss_price": entry_price - risk_per_share  # for longs
    }
```

---

### 3. Practical ATR Examples

#### Example 1: Low Volatility Stock

```python
# Stock A: Low Volatility Blue Chip
stock_a = {
    "price": $100,
    "atr": $1.50,
    "type": "low volatility"
}

account = $100,000
risk_percent = 2  # 2% risk per trade
multiplier = 2    # 2 ATR stop

# Calculation
dollar_risk = $100,000 * 0.02 = $2,000
risk_per_share = $1.50 * 2 = $3.00
shares = $2,000 / $3.00 = 666 shares
position_value = 666 * $100 = $66,600
stop_loss = $100 - $3.00 = $97.00

# Result:
# - Buy 666 shares at $100 = $66,600 position (66.6% of account)
# - Stop loss at $97
# - If stopped out, lose exactly $2,000 (2% of account)
```

#### Example 2: High Volatility Stock

```python
# Stock B: High Volatility Tech Stock
stock_b = {
    "price": $100,
    "atr": $6.00,
    "type": "high volatility"
}

account = $100,000
risk_percent = 2  # Same 2% risk
multiplier = 2    # Same 2 ATR stop

# Calculation
dollar_risk = $100,000 * 0.02 = $2,000
risk_per_share = $6.00 * 2 = $12.00
shares = $2,000 / $12.00 = 166 shares
position_value = 166 * $100 = $16,600
stop_loss = $100 - $12.00 = $88.00

# Result:
# - Buy 166 shares at $100 = $16,600 position (16.6% of account)
# - Stop loss at $88
# - If stopped out, lose exactly $2,000 (2% of account)

# Notice: Same dollar risk, but:
# - Low volatility = larger position (666 shares, tighter stop)
# - High volatility = smaller position (166 shares, wider stop)
# This is the power of ATR position sizing!
```

#### Example 3: Real-World ATR = $2.00

```python
# What does ATR = $2.00 mean?
atr_meaning = """
ATR = $2.00 means:
- On average, the stock's true range is $2.00 per period
- If daily ATR, the stock typically moves $2 from high to low each day
- This is a VOLATILITY measure, not direction
- A stock at $50 with $2 ATR is more volatile than one at $100 with $2 ATR
  (4% vs 2% daily range)
"""

# Position Sizing with $2 ATR
example_trade = {
    "account_size": $50,000,
    "entry_price": $45,
    "atr": $2.00,
    "risk_percent": 1.5,
    "multiplier": 2.5
}

dollar_risk = $50,000 * 0.015 = $750
risk_per_share = $2.00 * 2.5 = $5.00
shares = $750 / $5.00 = 150
position_value = 150 * $45 = $6,750
stop_loss = $45 - $5.00 = $40

# Output:
# - Buy 150 shares at $45
# - Position value: $6,750 (13.5% of account)
# - Stop loss: $40 (2.5 ATR below entry)
# - Risk: $750 if stopped out (1.5% of account)
```

---

### 4. Profit Targets Using ATR

```python
def calculate_atr_profit_targets(entry_price, atr, position_type="long"):
    """
    Calculate profit targets using ATR multiples
    """
    targets = {}

    multipliers = [1, 2, 3, 4, 5]

    for mult in multipliers:
        if position_type == "long":
            target = entry_price + (atr * mult)
        else:  # short
            target = entry_price - (atr * mult)

        targets[f"{mult}_atr"] = round(target, 2)

    return targets

# Example:
# Entry: $50 (long)
# ATR: $2
#
# Targets:
# 1 ATR: $52 (quick profit)
# 2 ATR: $54 (standard)
# 3 ATR: $56 (extended)
# 4 ATR: $58 (strong move)
# 5 ATR: $60 (exceptional)

# Turtle Traders Pyramiding
# - Initial entry: Full unit
# - Add 0.5 unit every 0.5 ATR move in favor
# - Maximum 4-5 units total
```

---

### 5. ATR-Based Trailing Stops

#### Fixed ATR Trailing Stop

```python
def atr_trailing_stop(current_price, highest_price_since_entry,
                      atr, multiplier, position_type="long"):
    """
    Calculate trailing stop using ATR

    For longs: Stop trails up as price makes new highs
    For shorts: Stop trails down as price makes new lows
    """
    if position_type == "long":
        trailing_stop = highest_price_since_entry - (atr * multiplier)
    else:  # short
        trailing_stop = lowest_price_since_entry + (atr * multiplier)

    return trailing_stop

# Example (Long Position):
# Entry: $50
# ATR: $2
# Multiplier: 3x
#
# Price moves to $60 (new high)
# Trailing Stop = $60 - ($2 * 3) = $54
#
# Price moves to $65 (new high)
# Trailing Stop = $65 - ($2 * 3) = $59
#
# Price pulls back to $62
# Stop stays at $59 (doesn't move down)
#
# Price moves to $70 (new high)
# Trailing Stop = $70 - ($2 * 3) = $64
```

#### Chandelier Exit (Advanced ATR Trailing)

```python
def chandelier_exit(highs, lows, atr_values, period=22, multiplier=3):
    """
    Chandelier Exit: ATR trailing stop using highest high/lowest low

    Developed by Charles Le Beau
    Featured in Alexander Elder's books

    Args:
        highs: Array of high prices
        lows: Array of low prices
        atr_values: Array of ATR values
        period: Lookback period for highest high/lowest low (default 22)
        multiplier: ATR multiplier (default 3)

    Returns:
        chandelier_long: Long position stop levels
        chandelier_short: Short position stop levels
    """
    chandelier_long = []
    chandelier_short = []

    for i in range(period - 1, len(highs)):
        # Get highest high and lowest low over period
        highest_high = max(highs[i - period + 1:i + 1])
        lowest_low = min(lows[i - period + 1:i + 1])

        # Current ATR
        current_atr = atr_values[i]

        # Calculate stops
        long_stop = highest_high - (current_atr * multiplier)
        short_stop = lowest_low + (current_atr * multiplier)

        chandelier_long.append(long_stop)
        chandelier_short.append(short_stop)

    return chandelier_long, chandelier_short

# Recommended Settings (Charles Le Beau):
# - Period: 22 (approximately 1 trading month)
# - Multiplier: 3
#
# For volatile tech stocks:
# - Multiplier: 5 (allows more breathing room)
#
# For less volatile stocks:
# - Multiplier: 2-2.5
```

---

### 6. Comparing Volatility Across Stocks

```python
def compare_stock_volatility(stocks):
    """
    Compare volatility across different stocks using ATR

    Use ATR Percent: (ATR / Price) * 100
    This normalizes ATR across different price levels
    """
    results = []

    for stock in stocks:
        atr_percent = (stock['atr'] / stock['price']) * 100

        results.append({
            'symbol': stock['symbol'],
            'price': stock['price'],
            'atr': stock['atr'],
            'atr_percent': round(atr_percent, 2),
            'volatility_rank': None  # Set after sorting
        })

    # Sort by ATR percent (highest volatility first)
    results.sort(key=lambda x: x['atr_percent'], reverse=True)

    # Assign ranks
    for i, result in enumerate(results):
        result['volatility_rank'] = i + 1

    return results

# Example:
stocks = [
    {'symbol': 'AAPL', 'price': 150, 'atr': 3.00},
    {'symbol': 'TSLA', 'price': 250, 'atr': 12.50},
    {'symbol': 'KO', 'price': 60, 'atr': 1.20}
]

# Results:
# TSLA: ATR% = (12.50 / 250) * 100 = 5.00% (Rank 1 - Most volatile)
# AAPL: ATR% = (3.00 / 150) * 100 = 2.00% (Rank 2)
# KO:   ATR% = (1.20 / 60) * 100 = 2.00% (Rank 3 - Least volatile)
```

---

### 7. ATR for Entry Timing

```python
def atr_entry_signals(current_atr, atr_sma, threshold=1.5):
    """
    Use ATR expansion/contraction for entry timing

    ATR Expansion: Volatility increasing (breakout likely)
    ATR Contraction: Volatility decreasing (consolidation)

    Args:
        current_atr: Current ATR value
        atr_sma: Moving average of ATR (e.g., 20-period MA of ATR)
        threshold: Expansion threshold (e.g., 1.5 = 50% above average)

    Returns:
        Signal: 'expansion', 'contraction', or 'normal'
    """
    ratio = current_atr / atr_sma

    if ratio >= threshold:
        return 'expansion'  # High volatility - breakout/trend
    elif ratio <= (1 / threshold):
        return 'contraction'  # Low volatility - consolidation
    else:
        return 'normal'

# Trading Strategy:
# - ATR Contraction: Stock is coiling, potential breakout coming
#   → Wait for expansion to enter
# - ATR Expansion: Breakout occurring, volatility increasing
#   → Enter if other criteria met
# - ATR at extreme highs: Potential reversal/exhaustion
#   → Be cautious

# Example:
# ATR SMA (20): $2.00
# Current ATR: $3.00
# Ratio: 3.00 / 2.00 = 1.50
# Signal: EXPANSION (volatility 50% above average)
```

---

## Complete ATR Reference Functions

```python
class ATRCalculator:
    """
    Complete ATR calculator with all methods
    """

    def __init__(self, period=14):
        self.period = period

    def true_range(self, high, low, prev_close):
        """Calculate True Range"""
        return max(
            high - low,
            abs(high - prev_close),
            abs(prev_close - low)
        )

    def atr(self, highs, lows, closes):
        """Calculate ATR using Wilder's smoothing"""
        trs = []
        for i in range(1, len(closes)):
            tr = self.true_range(highs[i], lows[i], closes[i-1])
            trs.append(tr)

        # First ATR
        atr = sum(trs[:self.period]) / self.period
        atrs = [atr]

        # Subsequent ATRs (Wilder's smoothing)
        for i in range(self.period, len(trs)):
            atr = ((atrs[-1] * (self.period - 1)) + trs[i]) / self.period
            atrs.append(atr)

        return atrs

    def atr_percent(self, atr, price):
        """Calculate ATR as percentage of price"""
        return (atr / price) * 100

    def position_size(self, account_size, entry_price, atr,
                     risk_percent, multiplier):
        """Calculate position size using ATR"""
        dollar_risk = account_size * (risk_percent / 100)
        risk_per_share = atr * multiplier
        shares = int(dollar_risk / risk_per_share)

        return {
            'shares': shares,
            'position_value': shares * entry_price,
            'dollar_risk': dollar_risk,
            'stop_loss': entry_price - risk_per_share
        }

    def stop_loss(self, entry_price, atr, multiplier, position_type='long'):
        """Calculate ATR-based stop loss"""
        if position_type == 'long':
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)

    def profit_targets(self, entry_price, atr, multiples=[1,2,3,4,5]):
        """Calculate profit targets at ATR multiples"""
        return {
            f"{m}x_atr": entry_price + (atr * m)
            for m in multiples
        }

    def chandelier_exit(self, highs, lows, atr, period=22, multiplier=3):
        """Calculate Chandelier Exit"""
        highest_high = max(highs[-period:])
        lowest_low = min(lows[-period:])

        return {
            'long_stop': highest_high - (atr * multiplier),
            'short_stop': lowest_low + (atr * multiplier)
        }

# Usage Example:
"""
calc = ATRCalculator(period=14)

# Calculate ATR from price data
atr_values = calc.atr(highs, lows, closes)
current_atr = atr_values[-1]

# Position sizing
position = calc.position_size(
    account_size=100000,
    entry_price=50,
    atr=current_atr,
    risk_percent=2,
    multiplier=2
)

print(f"Buy {position['shares']} shares")
print(f"Stop loss at ${position['stop_loss']:.2f}")
print(f"Risk ${position['dollar_risk']:.2f}")
"""
```

---

# 3. Risk Management Systems

## Overview

Risk management is the cornerstone of long-term trading success. Proper risk management ensures:
- No single trade can destroy your account
- Emotional control through predefined rules
- Consistent position sizing across different setups
- Portfolio-level protection

---

## Position Sizing Methods

### 1. Fixed Percentage Risk

**Most Common Method Used by Professional Traders**

```python
def fixed_percentage_position_sizing(account_size, entry_price,
                                     stop_loss, risk_percent):
    """
    Calculate position size risking fixed percentage of account

    This is the #1 most recommended method for retail traders

    Args:
        account_size: Total trading capital
        entry_price: Entry price per share
        stop_loss: Stop loss price
        risk_percent: Percentage of account to risk (typically 1-2%)

    Returns:
        Dictionary with position details
    """
    # Calculate dollar risk
    dollar_risk = account_size * (risk_percent / 100)

    # Calculate risk per share
    risk_per_share = abs(entry_price - stop_loss)

    # Calculate shares
    shares = int(dollar_risk / risk_per_share)

    # Calculate position value
    position_value = shares * entry_price

    # Calculate position as percent of account
    position_percent = (position_value / account_size) * 100

    return {
        'shares': shares,
        'position_value': position_value,
        'position_percent': position_percent,
        'dollar_risk': dollar_risk,
        'risk_per_share': risk_per_share,
        'max_loss_if_stopped': dollar_risk
    }

# Professional Risk Percentages:
risk_levels = {
    "ultra_conservative": 0.5,   # 0.5% per trade
    "conservative": 1.0,          # 1% per trade (RECOMMENDED)
    "moderate": 1.5,              # 1.5% per trade
    "standard": 2.0,              # 2% per trade (MAXIMUM RECOMMENDED)
    "aggressive": 3.0,            # 3% per trade (risky)
    "very_aggressive": 5.0        # 5% per trade (very risky)
}

# Example:
account = 100_000
entry = 50
stop = 47
risk = 1.5  # 1.5%

dollar_risk = 100_000 * 0.015 = 1_500
risk_per_share = 50 - 47 = 3
shares = 1_500 / 3 = 500
position_value = 500 * 50 = 25_000

# Result: Buy 500 shares, risk $1,500 (1.5% of account)
```

---

### 2. ATR-Based Position Sizing

**Volatility-Adjusted Sizing (Turtle Traders Method)**

```python
def atr_position_sizing(account_size, entry_price, atr,
                        risk_percent=1, atr_multiplier=2):
    """
    ATR-based position sizing (Turtle Traders method)

    Automatically adjusts for volatility:
    - High volatility = smaller position
    - Low volatility = larger position

    This ensures consistent DOLLAR RISK across all trades
    regardless of individual stock volatility
    """
    # Dollar risk
    dollar_risk = account_size * (risk_percent / 100)

    # Risk per share (ATR-based stop)
    risk_per_share = atr * atr_multiplier

    # Shares
    shares = int(dollar_risk / risk_per_share)

    # Position value
    position_value = shares * entry_price

    # Stop loss
    stop_loss = entry_price - risk_per_share

    return {
        'shares': shares,
        'position_value': position_value,
        'dollar_risk': dollar_risk,
        'stop_loss': stop_loss,
        'risk_per_share': risk_per_share,
        'atr': atr,
        'atr_multiplier': atr_multiplier
    }

# Turtle Traders Specific Rules:
turtle_rules = {
    "risk_per_trade": 2,          # 2% max (but 1% typical)
    "stop_loss_atr": 2,           # 2 ATR stop (2N)
    "initial_position": 0.5,      # Start with 0.5% risk
    "pyramid_increment": 0.5,     # Add 0.5 ATR increments
    "max_units": 4,               # Maximum 4 units per trade
    "pyramid_trigger": 0.5        # Add at 0.5 ATR profit intervals
}
```

---

### 3. Kelly Criterion

**Mathematical Optimization of Position Size**

```python
def kelly_criterion(win_rate, avg_win, avg_loss):
    """
    Calculate optimal position size using Kelly Criterion

    Formula: Kelly % = W - [(1 - W) / R]
    Where:
        W = Win rate (probability of winning)
        R = Win/Loss ratio (average win / average loss)

    WARNING: Full Kelly can lead to 50-70% drawdowns
    Most traders use fractional Kelly (1/2 or 1/4)
    """
    # Win/Loss ratio
    win_loss_ratio = avg_win / avg_loss

    # Kelly percentage
    kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)

    # Fractional Kelly (safer)
    half_kelly = kelly_pct / 2
    quarter_kelly = kelly_pct / 4

    return {
        'full_kelly': max(0, kelly_pct * 100),  # Never go negative
        'half_kelly': max(0, half_kelly * 100),
        'quarter_kelly': max(0, quarter_kelly * 100),
        'recommended': 'half_kelly'  # Most pros use 1/2 Kelly
    }

# Example 1: Good System
win_rate = 0.40        # 40% win rate
avg_win = 1000         # Average win $1,000
avg_loss = 400         # Average loss $400

kelly = kelly_criterion(0.40, 1000, 400)
# Full Kelly: 40 - ((1-0.40) / 2.5) = 40 - 24 = 16%
# Half Kelly: 8%
# Quarter Kelly: 4%

# Example 2: Qullamaggie-style System
win_rate = 0.25        # 25% win rate
avg_win = 4000         # Big winners
avg_loss = 500         # Small losses

kelly = kelly_criterion(0.25, 4000, 500)
# Full Kelly: 25 - ((1-0.25) / 8) = 25 - 9.375 = 15.625%
# Half Kelly: 7.8%
# Quarter Kelly: 3.9%

# Kelly Criterion Warnings:
warnings = """
1. Requires accurate win rate and avg win/loss data
2. Full Kelly can cause 50-70% drawdowns
3. Most pros use 1/2 or 1/4 Kelly
4. Not suitable for new traders
5. Better for systems with extensive backtesting
"""
```

---

### 4. Equal Dollar Weighting vs Risk Weighting

```python
def equal_dollar_weighting(account_size, num_positions):
    """
    Equal dollar weighting: Each position gets same $ amount

    Simple but ignores risk differences between stocks
    """
    position_size = account_size / num_positions
    position_percent = (1 / num_positions) * 100

    return {
        'position_size': position_size,
        'position_percent': position_percent,
        'num_positions': num_positions
    }

# Example:
# $100,000 account, 10 positions
# Each position: $10,000 (10% of account)
# Simple but doesn't account for different stop distances


def risk_weighted_sizing(account_size, trades, risk_percent=1):
    """
    Risk weighting: Each trade risks same $ amount
    But position sizes vary based on stop distance

    This is SUPERIOR to equal dollar weighting
    """
    positions = []

    dollar_risk_per_trade = account_size * (risk_percent / 100)

    for trade in trades:
        entry = trade['entry']
        stop = trade['stop']

        risk_per_share = abs(entry - stop)
        shares = int(dollar_risk_per_trade / risk_per_share)
        position_value = shares * entry

        positions.append({
            'symbol': trade['symbol'],
            'shares': shares,
            'position_value': position_value,
            'entry': entry,
            'stop': stop,
            'dollar_risk': dollar_risk_per_trade
        })

    return positions

# Example:
# $100,000 account, 1% risk per trade = $1,000 risk each

trades = [
    {'symbol': 'AAPL', 'entry': 150, 'stop': 147},  # $3 stop
    {'symbol': 'TSLA', 'entry': 250, 'stop': 240},  # $10 stop
]

# AAPL: $1,000 / $3 = 333 shares = $49,950 position
# TSLA: $1,000 / $10 = 100 shares = $25,000 position

# Both risk same $1,000, but position sizes differ based on risk
```

---

### 5. Conviction-Based Sizing (5LC System Integration)

```python
def conviction_based_sizing(account_size, base_risk_percent, conviction_level):
    """
    Scale position size based on conviction (1-5 scale)

    Integration with 5LC (5 Level Conviction) system:
    - Level 1: Lowest conviction (0.5x base risk)
    - Level 2: Below average (0.75x base risk)
    - Level 3: Average conviction (1.0x base risk)
    - Level 4: Above average (1.25x base risk)
    - Level 5: Highest conviction (1.5x base risk)
    """
    conviction_multipliers = {
        1: 0.50,   # Half size
        2: 0.75,   # 3/4 size
        3: 1.00,   # Full size
        4: 1.25,   # 1.25x size
        5: 1.50    # 1.5x size
    }

    multiplier = conviction_multipliers.get(conviction_level, 1.0)
    adjusted_risk = base_risk_percent * multiplier

    # Cap at maximum (e.g., 3%)
    max_risk = 3.0
    final_risk = min(adjusted_risk, max_risk)

    return {
        'base_risk_percent': base_risk_percent,
        'conviction_level': conviction_level,
        'multiplier': multiplier,
        'final_risk_percent': final_risk,
        'dollar_risk': account_size * (final_risk / 100)
    }

# Example with $2M account:
account = 2_000_000
base_risk = 1.0  # 1% base

# Level 5 conviction trade:
high_conviction = conviction_based_sizing(account, base_risk, 5)
# Result: 1.5% risk = $30,000 risk

# Level 1 conviction trade:
low_conviction = conviction_based_sizing(account, base_risk, 1)
# Result: 0.5% risk = $10,000 risk

# This allows you to "press" high-conviction setups
# while taking smaller positions on lower-conviction trades
```

---

## Stop Loss Strategies

### 1. Percentage-Based Stops

```python
def percentage_stop_loss(entry_price, stop_percent, position_type='long'):
    """
    Calculate stop loss as percentage from entry

    Common percentages:
    - 3-5%: Tight stops (Minervini)
    - 7-8%: Standard stops (William O'Neil)
    - 10-12%: Loose stops (longer-term positions)
    """
    if position_type == 'long':
        stop_price = entry_price * (1 - stop_percent / 100)
    else:  # short
        stop_price = entry_price * (1 + stop_percent / 100)

    return round(stop_price, 2)

# Famous Trader Stop Percentages:
trader_stops = {
    "minervini": (3, 5),      # 3-5% stops (SEPA method)
    "oneil": (7, 8),          # 7-8% max loss rule (CANSLIM)
    "zanger": 8,              # 8% stop
    "weinstein": 6,           # 6% stop
    "ryan": (3, 5)            # 3-5% stops
}

# Example: William O'Neil 7-8% Rule
entry = 50
stop_7pct = 50 * (1 - 0.07) = 46.50
stop_8pct = 50 * (1 - 0.08) = 46.00

# O'Neil's Rule: NO EXCEPTIONS
# If stock drops 7-8%, sell immediately
```

---

### 2. ATR-Based Stops

*(See ATR section above for detailed formulas)*

```python
# Quick Reference
def atr_stop(entry, atr, multiplier, position='long'):
    if position == 'long':
        return entry - (atr * multiplier)
    else:
        return entry + (atr * multiplier)

# Multiplier guide:
# 1.5 ATR: Tight (day trading)
# 2.0 ATR: Standard (Turtle Traders, swing trading)
# 2.5 ATR: Moderate
# 3.0 ATR: Loose (position trading)
# 4.0 ATR: Very loose (long-term)
```

---

### 3. Support/Resistance-Based Stops

```python
def support_resistance_stop(entry_price, support_level,
                           buffer_percent=0.5, position_type='long'):
    """
    Place stop below support (for longs) or above resistance (for shorts)

    Add buffer to avoid false breakouts/stop hunts

    Args:
        entry_price: Entry price
        support_level: Support price level
        buffer_percent: Additional % buffer below support (default 0.5%)
        position_type: 'long' or 'short'
    """
    if position_type == 'long':
        # Stop below support with buffer
        stop = support_level * (1 - buffer_percent / 100)
    else:  # short
        # Stop above resistance with buffer
        stop = support_level * (1 + buffer_percent / 100)

    # Validation: Don't risk more than max%
    max_risk_percent = 10  # Maximum 10% risk
    actual_risk_percent = abs((entry_price - stop) / entry_price) * 100

    if actual_risk_percent > max_risk_percent:
        return {
            'stop_price': None,
            'valid': False,
            'reason': f'Risk too high: {actual_risk_percent:.1f}%'
        }

    return {
        'stop_price': round(stop, 2),
        'valid': True,
        'risk_percent': actual_risk_percent,
        'support_level': support_level,
        'buffer_percent': buffer_percent
    }

# Example:
entry = 52
support = 50

stop_result = support_resistance_stop(entry, support, buffer_percent=0.5)
# Support: $50
# Buffer: 0.5% = $0.25
# Stop: $50 - $0.25 = $49.75
# Risk: (52 - 49.75) / 52 = 4.3%
```

---

### 4. Time-Based Stops

```python
def time_based_stop(entry_date, max_days_in_trade):
    """
    Exit trade after maximum time period

    Used when trade isn't working out (not hitting profit OR stop)
    Frees up capital for better opportunities

    Common time stops:
    - Day trading: End of day
    - Swing trading: 5-10 days
    - Position trading: 30-60 days
    """
    import datetime

    if isinstance(entry_date, str):
        entry_date = datetime.datetime.strptime(entry_date, '%Y-%m-%d')

    exit_date = entry_date + datetime.timedelta(days=max_days_in_trade)

    return {
        'entry_date': entry_date.strftime('%Y-%m-%d'),
        'max_exit_date': exit_date.strftime('%Y-%m-%d'),
        'max_days': max_days_in_trade
    }

# Dan Zanger Example:
# If stock doesn't accelerate quickly from base (within 20 minutes),
# sell immediately regardless of profit/loss
# "If trade isn't working, it must be wrong"

# William O'Neil Example:
# If stock is flat/sideways for several weeks after breakout,
# sell and redeploy capital

time_stop_rules = {
    "zanger_intraday": 20,     # minutes
    "swing_trade": 10,         # days
    "position_trade": 60,      # days
    "dead_money": 14           # days (stock going nowhere)
}
```

---

### 5. Trailing Stops

#### A. Fixed Percentage Trailing Stop

```python
def fixed_percentage_trailing_stop(current_price, highest_price_since_entry,
                                   trailing_percent, position_type='long'):
    """
    Trailing stop that moves with price but never moves against you

    For longs: Stop trails up, never down
    For shorts: Stop trails down, never up
    """
    if position_type == 'long':
        trailing_stop = highest_price_since_entry * (1 - trailing_percent / 100)
    else:  # short
        trailing_stop = lowest_price_since_entry * (1 + trailing_percent / 100)

    return round(trailing_stop, 2)

# Example (Long):
# Entry: $50
# Trailing %: 10%
#
# Price -> $60 (new high)
# Stop: $60 * 0.90 = $54
#
# Price -> $70 (new high)
# Stop: $70 * 0.90 = $63
#
# Price drops to $65
# Stop stays at $63 (doesn't move down)
#
# Price hits $63 -> EXIT

# Common trailing percentages:
trailing_percentages = {
    "tight": 5,       # 5% trailing
    "moderate": 10,   # 10% trailing
    "loose": 15,      # 15% trailing
    "very_loose": 20  # 20% trailing
}
```

#### B. ATR Trailing Stop

*(See ATR section for Chandelier Exit)*

```python
def atr_trailing_stop(highest_price, atr, multiplier=3):
    """
    Trailing stop using ATR (volatility-adjusted)

    Automatically adjusts to market volatility:
    - High volatility = wider stop
    - Low volatility = tighter stop
    """
    return highest_price - (atr * multiplier)

# Advantages over fixed %:
# - Adapts to volatility
# - Tighter in calm markets
# - Wider in volatile markets
```

#### C. Moving Average Trailing Stop

```python
def ma_trailing_stop(close_prices, ma_period=20, ma_type='SMA'):
    """
    Trailing stop using moving average

    Common MAs:
    - 10-day SMA: Fast stocks (Qullamaggie)
    - 20-day SMA: Slower stocks (Qullamaggie)
    - 21-day EMA: Minervini
    - 50-day SMA: Longer-term trends
    - 200-day SMA: Very long-term
    """
    if ma_type == 'SMA':
        ma = sum(close_prices[-ma_period:]) / ma_period
    elif ma_type == 'EMA':
        # Simplified EMA calculation
        multiplier = 2 / (ma_period + 1)
        ma = close_prices[-1]  # Placeholder
        # Full EMA calculation would go here

    return ma

# Qullamaggie Method:
# - Fast stocks: 10-day MA
# - Slow stocks: 20-day MA
# - Exit when close BELOW MA
# - Optional: Trail stop at LOW of candle that crosses MA

# Minervini Method:
# - Uses 21-day EMA
# - Exit on close below 21 EMA
# - Part of SEPA method
```

---

### 6. Breakeven Stops

```python
def breakeven_stop_strategy(entry_price, current_price,
                            profit_target_hit, buffer=0):
    """
    Move stop to breakeven after reaching profit target

    Common strategies:
    1. After 1:1 R/R, move to breakeven
    2. After taking partial profits, move to breakeven
    3. After specific price target hit

    Args:
        entry_price: Original entry price
        current_price: Current market price
        profit_target_hit: Has first profit target been hit?
        buffer: Optional buffer above/below entry (e.g., +$0.10 or -0.10)
    """
    if profit_target_hit:
        # Move to breakeven (with optional buffer)
        new_stop = entry_price + buffer
        return {
            'stop_price': new_stop,
            'moved_to_breakeven': True,
            'risk_eliminated': True
        }
    else:
        return {
            'stop_price': None,  # Keep original stop
            'moved_to_breakeven': False,
            'risk_eliminated': False
        }

# Example:
# Entry: $50
# Initial Stop: $47 (3% = $3 risk)
# Target 1: $53 (3% = $3 profit, 1:1 R/R)
#
# Price hits $53:
# - Take 1/3 profit
# - Move stop to $50.10 (breakeven + $0.10 buffer)
# - Now trading with "house money"
# - Worst case: Small profit or scratch
# - Best case: Big winner continues

# Qullamaggie Example:
# - After 3-5 days, take 1/3 to 1/2 profit
# - Move stop to breakeven
# - Trail remainder with 10 or 20-day MA
```

---

## Portfolio Risk Management

### 1. Maximum Total Portfolio Risk

```python
def calculate_total_portfolio_risk(positions):
    """
    Calculate total risk across all open positions

    Industry Standards:
    - Conservative: 6% max total risk
    - Moderate: 10% max total risk
    - Aggressive: 20% max total risk

    Args:
        positions: List of dicts with position details

    Returns:
        Total risk metrics
    """
    total_risk_dollars = sum(pos['dollar_risk'] for pos in positions)
    account_size = positions[0]['account_size']  # Assume same for all
    total_risk_percent = (total_risk_dollars / account_size) * 100

    # Risk limits
    limits = {
        'conservative': 6,
        'moderate': 10,
        'aggressive': 20
    }

    # Determine risk level
    if total_risk_percent <= limits['conservative']:
        risk_level = 'conservative'
    elif total_risk_percent <= limits['moderate']:
        risk_level = 'moderate'
    elif total_risk_percent <= limits['aggressive']:
        risk_level = 'aggressive'
    else:
        risk_level = 'excessive'

    return {
        'total_risk_dollars': total_risk_dollars,
        'total_risk_percent': round(total_risk_percent, 2),
        'risk_level': risk_level,
        'num_positions': len(positions),
        'avg_risk_per_position': round(total_risk_percent / len(positions), 2)
    }

# Example:
# 10 positions, each risking 1% = 10% total portfolio risk (MODERATE)
# If 5 positions stop out = 5% account loss
# This is acceptable and normal

# Example 2:
# 20 positions, each risking 2% = 40% total portfolio risk (EXCESSIVE!)
# If half stop out = 20% account loss
# This is catastrophic risk management
```

---

### 2. Correlation Risk

```python
def check_correlation_risk(positions, max_correlated_positions=3):
    """
    Ensure positions aren't too correlated

    Correlation risks:
    - All positions in same sector (Tech, Energy, etc.)
    - All positions with same market cap (Small cap)
    - All positions with same style (Growth)

    If all positions are correlated, they'll all lose together
    """
    # Group positions by sector
    sector_counts = {}
    for pos in positions:
        sector = pos.get('sector', 'Unknown')
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    # Check for concentration
    warnings = []
    for sector, count in sector_counts.items():
        if count > max_correlated_positions:
            warnings.append({
                'sector': sector,
                'count': count,
                'warning': f'Too many positions in {sector}'
            })

    return {
        'sector_distribution': sector_counts,
        'warnings': warnings,
        'is_diversified': len(warnings) == 0
    }

# Correlation Guidelines:
correlation_rules = {
    "max_same_sector": 3,           # Max 3 positions in same sector
    "max_same_market_cap": 5,       # Max 5 small caps
    "max_same_style": 5,            # Max 5 growth stocks
    "max_same_industry": 2          # Max 2 in same industry (e.g., semiconductors)
}

# Example POOR Diversification:
# 10 positions, all tech stocks, all small cap
# If tech sells off, ALL positions lose
# Correlation = 1.0 (worst case)

# Example GOOD Diversification:
# 10 positions across: Tech, Healthcare, Consumer, Industrial, Energy
# Small, mid, and large cap mix
# Growth and value mix
# If one sector sells off, others may hold up
```

---

### 3. Sector Exposure Limits

```python
def calculate_sector_exposure(positions, account_size, max_sector_pct=20):
    """
    Limit exposure to individual sectors

    Standard limits:
    - Individual security: 5% max
    - Single sector: 20% max
    - Single geography: 35% max
    """
    sector_exposure = {}

    for pos in positions:
        sector = pos.get('sector', 'Unknown')
        position_value = pos.get('position_value', 0)

        if sector not in sector_exposure:
            sector_exposure[sector] = 0

        sector_exposure[sector] += position_value

    # Calculate percentages
    sector_pcts = {}
    violations = []

    for sector, value in sector_exposure.items():
        pct = (value / account_size) * 100
        sector_pcts[sector] = round(pct, 2)

        if pct > max_sector_pct:
            violations.append({
                'sector': sector,
                'exposure_pct': pct,
                'max_allowed': max_sector_pct,
                'excess': round(pct - max_sector_pct, 2)
            })

    return {
        'sector_exposures': sector_pcts,
        'violations': violations,
        'is_compliant': len(violations) == 0
    }

# Exposure Limits:
exposure_limits = {
    "individual_stock": 5,      # 5% max in any one stock
    "sector": 20,               # 20% max in any sector
    "geography": 35,            # 35% max in any region
    "market_cap": 30            # 30% max in small caps
}

# Example Violation:
# Account: $1M
# Tech Sector: $300k (30%)
# Violation: 10% over limit
# Action: Reduce tech exposure or increase account size
```

---

### 4. Individual Position Limits

```python
def validate_position_limits(position_value, account_size, symbol):
    """
    Ensure individual position doesn't exceed limits

    Standard: No more than 5-10% of account in single position
    (Based on position VALUE, not risk)
    """
    position_pct = (position_value / account_size) * 100

    limits = {
        'conservative': 5,      # 5% max
        'moderate': 10,         # 10% max
        'aggressive': 15,       # 15% max (Qullamaggie typical)
        'very_aggressive': 25   # 25% max (Qullamaggie high conviction)
    }

    # Determine if within limits
    if position_pct <= limits['conservative']:
        status = 'conservative'
    elif position_pct <= limits['moderate']:
        status = 'moderate'
    elif position_pct <= limits['aggressive']:
        status = 'aggressive'
    elif position_pct <= limits['very_aggressive']:
        status = 'very_aggressive'
    else:
        status = 'excessive'

    return {
        'symbol': symbol,
        'position_value': position_value,
        'position_pct': round(position_pct, 2),
        'status': status,
        'is_acceptable': status != 'excessive'
    }

# Note the difference:
# - Position RISK: 1-2% (how much you'll lose if stopped)
# - Position SIZE: 5-15% (total value of position)
#
# Example:
# $100k account
# Position SIZE: $15k (15% of account)
# Position RISK: $1k (1% of account)
# Stop is 6.7% from entry
```

---

### 5. Scaling In/Out Strategies

#### Scaling Out (Taking Profits)

```python
def scaling_out_strategy(total_shares, scale_levels):
    """
    Scale out of winning positions at predetermined levels

    Common strategies:
    1. Thirds: 1/3 at each target level
    2. Halves: 1/2 at first target, rest trails
    3. Quarters: 1/4 increments

    Args:
        total_shares: Total shares in position
        scale_levels: List of target levels with percentages

    Returns:
        Scaling plan
    """
    remaining_shares = total_shares
    scale_plan = []

    for level in scale_levels:
        shares_to_sell = int(total_shares * level['percent'])
        remaining_shares -= shares_to_sell

        scale_plan.append({
            'target': level['target'],
            'shares_to_sell': shares_to_sell,
            'remaining_shares': remaining_shares,
            'action': level.get('action', 'sell')
        })

    return scale_plan

# Example: Qullamaggie Method
total = 1000  # shares

qulla_scale = scaling_out_strategy(1000, [
    {'target': '3-5 days', 'percent': 0.33, 'action': 'Take 1/3 profit'},
    {'target': 'Trail with 10/20 MA', 'percent': 0.67, 'action': 'Trail stop'}
])

# Day 4: Sell 333 shares (1/3)
# Remaining: 667 shares trail with MA stop

# Example: Classic Thirds
classic_scale = scaling_out_strategy(1000, [
    {'target': '1R (1:1)', 'percent': 0.33},
    {'target': '2R (2:1)', 'percent': 0.33},
    {'target': '3R+ (3:1+)', 'percent': 0.34}
])

# Hit 1R: Sell 333 shares, move stop to breakeven
# Hit 2R: Sell 333 shares, trail remaining
# Hit 3R: Sell remaining 334 shares or trail
```

#### Scaling In (Pyramiding)

```python
def pyramiding_strategy(initial_shares, pyramid_levels, max_units=4):
    """
    Add to winning positions (pyramiding/scaling in)

    Turtle Traders Method:
    - Initial: 1 unit (0.5% risk)
    - Add: 0.5 unit at each 0.5 ATR profit
    - Maximum: 4 units total

    CRITICAL RULES:
    1. ONLY add to WINNERS (never add to losers)
    2. Each addition should be SMALLER than previous
    3. Move stop up as you add
    4. Maximum total position size limit

    Args:
        initial_shares: Initial position size
        pyramid_levels: Profit levels where to add
        max_units: Maximum number of units (default 4)
    """
    positions = [{
        'level': 0,
        'trigger': 'Initial entry',
        'shares': initial_shares,
        'total_shares': initial_shares
    }]

    total_shares = initial_shares

    for i, level in enumerate(pyramid_levels):
        if i + 1 >= max_units:
            break

        # Each addition is smaller (or equal)
        additional_shares = initial_shares  # Same size for Turtles
        # Alternative: additional_shares = initial_shares / (i + 2)  # Decreasing

        total_shares += additional_shares

        positions.append({
            'level': i + 1,
            'trigger': level['trigger'],
            'shares': additional_shares,
            'total_shares': total_shares,
            'new_stop': level.get('new_stop', 'Move up to protect profit')
        })

    return positions

# Turtle Traders Example:
turtle_pyramid = pyramiding_strategy(
    initial_shares=200,
    pyramid_levels=[
        {'trigger': '0.5 ATR profit', 'new_stop': 'Entry - 0.5 ATR'},
        {'trigger': '1.0 ATR profit', 'new_stop': 'Entry + 0.5 ATR'},
        {'trigger': '1.5 ATR profit', 'new_stop': 'Entry + 1.0 ATR'}
    ],
    max_units=4
)

# Level 0: 200 shares (initial)
# Level 1: +200 shares at 0.5 ATR profit = 400 total
# Level 2: +200 shares at 1.0 ATR profit = 600 total
# Level 3: +200 shares at 1.5 ATR profit = 800 total

# WARNING: Pyramiding increases risk!
# Only for strong trends with strict stop management
```

---

### 6. Market Condition Adjustments

```python
def adjust_for_market_conditions(base_risk_percent, market_condition):
    """
    Adjust position sizes based on market conditions

    Market conditions affect win rates and risk
    """
    adjustments = {
        'strong_bull': 1.5,      # Increase size 50%
        'bull': 1.25,            # Increase size 25%
        'neutral': 1.0,          # Normal size
        'choppy': 0.75,          # Reduce size 25%
        'bear': 0.5,             # Reduce size 50%
        'crash': 0.0             # No new positions
    }

    multiplier = adjustments.get(market_condition, 1.0)
    adjusted_risk = base_risk_percent * multiplier

    # Cap at maximum
    max_risk = 3.0
    final_risk = min(adjusted_risk, max_risk)

    return {
        'base_risk': base_risk_percent,
        'market_condition': market_condition,
        'multiplier': multiplier,
        'adjusted_risk': final_risk
    }

# Example:
# Base risk: 2%
# Strong bull market: 2% * 1.5 = 3% per trade
# Bear market: 2% * 0.5 = 1% per trade

# Market Condition Indicators:
market_indicators = {
    "sp500_above_200ma": "Bull signal",
    "sp500_below_200ma": "Bear signal",
    "high_vix": "High volatility, reduce size",
    "low_vix": "Low volatility, can increase size",
    "many_new_highs": "Strong market, increase size",
    "many_new_lows": "Weak market, reduce size"
}
```

---

## Risk/Reward Ratios

### 1. Minimum R:R Requirements

```python
def calculate_risk_reward_ratio(entry_price, stop_loss, target_price):
    """
    Calculate risk/reward ratio for a trade

    Formula: R:R = (Target - Entry) / (Entry - Stop)

    Common requirements:
    - Minimum 2:1 (make $2 for every $1 risked)
    - Ideal 3:1 or higher
    - Some traders require 4:1 or 5:1
    """
    risk = abs(entry_price - stop_loss)
    reward = abs(target_price - entry_price)

    if risk == 0:
        return None

    ratio = reward / risk

    # Determine if acceptable
    quality_levels = {
        'poor': (0, 1.5),
        'acceptable': (1.5, 2.5),
        'good': (2.5, 3.5),
        'excellent': (3.5, float('inf'))
    }

    quality = 'poor'
    for level, (min_r, max_r) in quality_levels.items():
        if min_r <= ratio < max_r:
            quality = level
            break

    return {
        'entry': entry_price,
        'stop': stop_loss,
        'target': target_price,
        'risk_dollars': risk,
        'reward_dollars': reward,
        'ratio': round(ratio, 2),
        'ratio_string': f"{ratio:.1f}:1",
        'quality': quality,
        'is_acceptable': ratio >= 2.0
    }

# Example 1: Good R:R
rr = calculate_risk_reward_ratio(
    entry_price=50,
    stop_loss=47,
    target_price=56
)
# Risk: $3 ($50 - $47)
# Reward: $6 ($56 - $50)
# R:R: 2:1 (acceptable)

# Example 2: Excellent R:R
rr = calculate_risk_reward_ratio(
    entry_price=50,
    stop_loss=47,
    target_price=62
)
# Risk: $3
# Reward: $12
# R:R: 4:1 (excellent)
```

---

### 2. Expected Value (Expectancy)

```python
def calculate_expectancy(win_rate, avg_win, avg_loss):
    """
    Calculate expected value per trade

    Formula: Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)

    This tells you average $ profit per trade over many trades

    Positive expectancy = profitable system
    Negative expectancy = losing system
    """
    loss_rate = 1 - win_rate

    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    # Calculate expectancy ratio (avg win / avg loss)
    expectancy_ratio = avg_win / avg_loss if avg_loss != 0 else 0

    # Calculate minimum win rate needed to break even
    breakeven_win_rate = avg_loss / (avg_win + avg_loss)

    return {
        'expectancy_dollars': round(expectancy, 2),
        'expectancy_ratio': round(expectancy_ratio, 2),
        'win_rate': win_rate,
        'loss_rate': loss_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'breakeven_win_rate': round(breakeven_win_rate * 100, 2),
        'is_profitable': expectancy > 0
    }

# Example 1: Qullamaggie-Style System
qulla_expectancy = calculate_expectancy(
    win_rate=0.25,      # 25% win rate
    avg_win=4000,       # $4,000 average win
    avg_loss=500        # $500 average loss
)
# Expectancy = (0.25 × $4,000) - (0.75 × $500)
# Expectancy = $1,000 - $375 = $625 per trade
# Profitable despite low win rate!

# Example 2: High Win Rate System
high_wr_expectancy = calculate_expectancy(
    win_rate=0.60,      # 60% win rate
    avg_win=500,        # $500 average win
    avg_loss=400        # $400 average loss
)
# Expectancy = (0.60 × $500) - (0.40 × $400)
# Expectancy = $300 - $160 = $140 per trade
# Lower expectancy than Qullamaggie style!
```

---

### 3. Win Rate vs R:R Tradeoffs

```python
def win_rate_rr_tradeoffs():
    """
    Demonstrate relationship between win rate and R:R ratio

    Key insight: Lower win rate OK if R:R is high
    High win rate needed if R:R is low
    """
    scenarios = [
        {
            'name': 'Qullamaggie Style',
            'win_rate': 0.25,
            'rr_ratio': 8.0,  # $4,000 win / $500 loss
            'avg_win': 4000,
            'avg_loss': 500
        },
        {
            'name': 'Balanced',
            'win_rate': 0.50,
            'rr_ratio': 2.0,
            'avg_win': 1000,
            'avg_loss': 500
        },
        {
            'name': 'High Win Rate',
            'win_rate': 0.70,
            'rr_ratio': 1.5,
            'avg_win': 600,
            'avg_loss': 400
        }
    ]

    results = []
    for scenario in scenarios:
        exp = calculate_expectancy(
            scenario['win_rate'],
            scenario['avg_win'],
            scenario['avg_loss']
        )
        results.append({
            'name': scenario['name'],
            'win_rate_pct': scenario['win_rate'] * 100,
            'rr_ratio': scenario['rr_ratio'],
            'expectancy': exp['expectancy_dollars']
        })

    return results

# Results:
# 1. Qullamaggie: 25% WR, 8:1 R:R = $625 expectancy
# 2. Balanced: 50% WR, 2:1 R:R = $250 expectancy
# 3. High WR: 70% WR, 1.5:1 R:R = $300 expectancy

# Lesson: High R:R with low win rate can be MORE profitable
# than high win rate with low R:R!
```

---

### 4. Required Win Rate for Profitability

```python
def calculate_required_win_rate(risk_reward_ratio):
    """
    Calculate minimum win rate needed to break even

    Formula: Required WR = 1 / (1 + R:R)

    This tells you minimum win % needed based on your R:R
    """
    required_wr = 1 / (1 + risk_reward_ratio)

    # Calculate for various win rates
    win_rates = [0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70]
    scenarios = []

    for wr in win_rates:
        lr = 1 - wr
        expectancy = (wr * risk_reward_ratio) - lr

        scenarios.append({
            'win_rate_pct': wr * 100,
            'expectancy_r': round(expectancy, 2),
            'profitable': expectancy > 0
        })

    return {
        'rr_ratio': risk_reward_ratio,
        'required_win_rate': round(required_wr * 100, 2),
        'scenarios': scenarios
    }

# Example: 3:1 R:R
rr_3to1 = calculate_required_win_rate(3)
# Required WR = 1 / (1 + 3) = 1/4 = 25%
# Need only 25% win rate to break even!

# If win rate is 30%:
# Expectancy = (0.30 × 3) - 0.70 = 0.90 - 0.70 = +0.20R per trade
# Profitable!

# Example: 1:1 R:R
rr_1to1 = calculate_required_win_rate(1)
# Required WR = 1 / (1 + 1) = 50%
# Need 50% win rate to break even

# Conclusion: Higher R:R = Lower win rate needed
```

---

## Examples from Legendary Traders

### 1. Turtle Traders

```python
turtle_system = {
    "risk_per_trade": 2,          # 2% max (but typically 1%)
    "stop_loss": "2 ATR (2N)",    # 2 ATR from entry
    "position_sizing": "ATR-based",
    "initial_position": 0.5,      # Start with 0.5% risk
    "pyramiding": True,
    "pyramid_increment": 0.5,     # Add 0.5 ATR increments
    "max_units": 4,               # Max 4 units per trade
    "max_correlated_units": 6,    # Max 6 units in correlated markets
    "max_total_risk": 12          # 12% max across all positions
}

def turtle_position_size_example():
    """
    Turtle Traders position sizing example
    """
    account = 100_000
    atr = 2.50
    risk_percent = 1  # 1% typical

    # Calculate 1 unit
    dollar_risk = account * 0.01  # $1,000
    stop_distance = atr * 2       # $5.00
    shares_per_unit = dollar_risk / stop_distance  # 200 shares

    # Initial entry
    initial_units = 1
    initial_shares = 200

    # Pyramid schedule
    pyramid = [
        {'profit': '0.5 ATR', 'add_shares': 200, 'total_shares': 400},
        {'profit': '1.0 ATR', 'add_shares': 200, 'total_shares': 600},
        {'profit': '1.5 ATR', 'add_shares': 200, 'total_shares': 800}
    ]

    return {
        'initial_shares': initial_shares,
        'pyramid_schedule': pyramid,
        'max_shares': 800,
        'max_risk_percent': 2  # 4 units × 0.5% each
    }
```

---

### 2. Mark Minervini (SEPA)

```python
minervini_system = {
    "method": "SEPA (Specific Entry Point Analysis)",
    "stop_loss": "3-5%",          # Tight stops
    "max_loss_threshold": "7-8%", # Maximum single loss
    "risk_per_trade": "1-2%",     # Preferably ≤1%
    "position_sizing": "Risk-based",
    "entry_timing": "VCP breakout",
    "exit_ma": "21-day EMA",
    "philosophy": "Defense wins championships"
}

def minervini_position_size_example():
    """
    Mark Minervini SEPA position sizing
    """
    account = 200_000
    entry = 45.00
    stop = 43.50         # 3.3% stop (tight)
    risk_percent = 1.0   # 1% risk

    # Calculate position
    dollar_risk = account * 0.01      # $2,000
    risk_per_share = entry - stop     # $1.50
    shares = dollar_risk / risk_per_share  # 1,333 shares
    position_value = shares * entry   # $59,985

    return {
        'shares': int(shares),
        'position_value': position_value,
        'position_pct': (position_value / account) * 100,  # 30%
        'dollar_risk': dollar_risk,
        'stop_pct': 3.3,
        'note': 'Tight stop allows larger position size'
    }

# Minervini Key Points:
# 1. Buy at "point of least resistance" (tight consolidation)
# 2. Tight 3-5% stops minimize risk
# 3. Risk 1% or less per trade
# 4. Never let winner turn into loser
# 5. Exit on break of 21 EMA
```

---

### 3. William O'Neil (CANSLIM)

```python
oneil_system = {
    "method": "CANSLIM",
    "stop_loss": "7-8%",          # Hard rule, NO EXCEPTIONS
    "tighter_stops": "3-4%",      # In volatile markets
    "position_sizing": "Concentrated",  # Fewer positions, larger size
    "typical_positions": "5-8",   # Not many positions
    "philosophy": "Cut losses quickly, let winners run"
}

def oneil_position_size_example():
    """
    William O'Neil CANSLIM position sizing
    """
    account = 100_000
    entry = 52.00
    stop = 48.00         # 7.7% stop
    risk_percent = 2.0   # 2% risk (concentrated approach)

    # Calculate position
    dollar_risk = account * 0.02      # $2,000
    risk_per_share = entry - stop     # $4.00
    shares = dollar_risk / risk_per_share  # 500 shares
    position_value = shares * entry   # $26,000

    return {
        'shares': int(shares),
        'position_value': position_value,
        'position_pct': (position_value / account) * 100,  # 26%
        'dollar_risk': dollar_risk,
        'stop_pct': 7.7,
        'rule': 'MUST sell at 7-8% loss, NO EXCEPTIONS'
    }

# O'Neil Key Points:
# 1. 7-8% stop loss is ABSOLUTE RULE
# 2. If wrong, get out quickly
# 3. If right, stock should go up immediately
# 4. Concentrated positions (5-8 stocks)
# 5. Buy cup-and-handle breakouts
```

---

### 4. Dan Zanger

```python
zanger_system = {
    "risk_per_trade": "1%",       # 1% portfolio risk per trade
    "stop_loss": "8%",            # 8% stop
    "position_size": "10-25%",    # Very concentrated
    "high_conviction": "15%",     # Up to 15% in single stock
    "extreme_conviction": "25%",  # 25% max (with 2:1 margin)
    "exit_rule": "If no immediate move, exit quickly (20 min)",
    "philosophy": "If it's not working immediately, it's wrong"
}

def zanger_position_size_example():
    """
    Dan Zanger position sizing
    """
    account = 500_000
    entry = 35.00
    stop = 32.20         # 8% stop
    risk_percent = 1.0   # 1% portfolio risk

    # Calculate position
    dollar_risk = account * 0.01      # $5,000
    risk_per_share = entry - stop     # $2.80
    shares = dollar_risk / risk_per_share  # 1,786 shares
    position_value = shares * entry   # $62,500

    return {
        'shares': int(shares),
        'position_value': position_value,
        'position_pct': (position_value / account) * 100,  # 12.5%
        'dollar_risk': dollar_risk,
        'stop_pct': 8.0,
        'conviction': 'Medium',
        'note': 'High conviction could be 15-25% of account'
    }

# Zanger Key Points:
# 1. 1% portfolio risk BUT large position sizes
# 2. If stock doesn't move immediately, EXIT
# 3. Very concentrated (10-25% positions)
# 4. Charts must show explosive potential
# 5. Earnings growth 100%+ YoY ideal
```

---

## Practical Implementation: $2M Account

### Complete Position Sizing Examples

```python
def position_sizing_2m_account_examples():
    """
    Complete position sizing examples for $2M account
    """
    account_size = 2_000_000

    # Example 1: Conservative (1% risk, tight stop)
    example1 = {
        'name': 'Conservative Minervini-Style',
        'account': account_size,
        'risk_percent': 1.0,
        'entry': 100.00,
        'stop': 96.00,  # 4% stop

        # Calculations
        'dollar_risk': 2_000_000 * 0.01,  # $20,000
        'risk_per_share': 100 - 96,       # $4
        'shares': 20_000 / 4,             # 5,000 shares
        'position_value': 5_000 * 100,    # $500,000
        'position_pct': 25.0              # 25% of account
    }

    # Example 2: Moderate (1.5% risk, standard stop)
    example2 = {
        'name': 'Moderate Qullamaggie-Style',
        'account': account_size,
        'risk_percent': 1.5,
        'entry': 50.00,
        'stop': 47.00,  # 6% stop

        # Calculations
        'dollar_risk': 2_000_000 * 0.015,  # $30,000
        'risk_per_share': 50 - 47,         # $3
        'shares': 30_000 / 3,              # 10,000 shares
        'position_value': 10_000 * 50,     # $500,000
        'position_pct': 25.0               # 25% of account
    }

    # Example 3: ATR-based (2% risk, 2 ATR stop)
    example3 = {
        'name': 'ATR-Based Turtle-Style',
        'account': account_size,
        'risk_percent': 2.0,
        'entry': 75.00,
        'atr': 3.00,
        'stop': 75 - (3 * 2),  # $69 (2 ATR stop)

        # Calculations
        'dollar_risk': 2_000_000 * 0.02,   # $40,000
        'risk_per_share': 6.00,            # 2 ATR
        'shares': 40_000 / 6,              # 6,666 shares
        'position_value': 6_666 * 75,      # $499,950
        'position_pct': 25.0               # 25% of account
    }

    # Example 4: High Conviction (2% risk, wider stop)
    example4 = {
        'name': 'High Conviction Zanger-Style',
        'account': account_size,
        'risk_percent': 2.0,
        'entry': 40.00,
        'stop': 36.80,  # 8% stop

        # Calculations
        'dollar_risk': 2_000_000 * 0.02,   # $40,000
        'risk_per_share': 40 - 36.80,      # $3.20
        'shares': 40_000 / 3.20,           # 12,500 shares
        'position_value': 12_500 * 40,     # $500,000
        'position_pct': 25.0               # 25% of account
    }

    # Portfolio Example: 10 positions
    portfolio = {
        'account': account_size,
        'num_positions': 10,
        'risk_per_trade': 1.0,  # 1% each

        'total_portfolio_risk': 10.0,  # 10% total
        'total_capital_deployed': 1_200_000,  # ~60% of account
        'cash_reserve': 800_000,  # 40% cash

        'risk_level': 'MODERATE',
        'note': '10 positions × 1% risk = 10% total risk (acceptable)'
    }

    return {
        'examples': [example1, example2, example3, example4],
        'portfolio': portfolio
    }

# Key Observations for $2M Account:
#
# 1. Dollar risk per trade: $20k-$40k (1-2%)
# 2. Position sizes: Often $400k-$600k (20-30% of account)
# 3. This is NORMAL - large positions with tight stops
# 4. The key is DOLLAR RISK, not position size
# 5. With 10 positions: $4M-$6M deployed (2-3x account with margin)
```

---

### Scaling Based on 5LC System

```python
def position_sizing_2m_with_5lc():
    """
    Position sizing for $2M account using 5LC conviction levels
    """
    account = 2_000_000
    base_risk = 1.0  # 1% base risk

    conviction_examples = []

    # Level 1: Low Conviction
    level1 = {
        'conviction': 1,
        'multiplier': 0.5,
        'risk_percent': 0.5,
        'dollar_risk': 2_000_000 * 0.005,  # $10,000
        'example_entry': 50,
        'example_stop': 48,
        'shares': 10_000 / 2,  # 5,000
        'position_value': 5_000 * 50,  # $250,000
        'use_case': 'Lower-quality setup, testing the waters'
    }
    conviction_examples.append(level1)

    # Level 3: Normal Conviction
    level3 = {
        'conviction': 3,
        'multiplier': 1.0,
        'risk_percent': 1.0,
        'dollar_risk': 2_000_000 * 0.01,  # $20,000
        'example_entry': 50,
        'example_stop': 48,
        'shares': 20_000 / 2,  # 10,000
        'position_value': 10_000 * 50,  # $500,000
        'use_case': 'Standard setup meeting all criteria'
    }
    conviction_examples.append(level3)

    # Level 5: High Conviction
    level5 = {
        'conviction': 5,
        'multiplier': 1.5,
        'risk_percent': 1.5,
        'dollar_risk': 2_000_000 * 0.015,  # $30,000
        'example_entry': 50,
        'example_stop': 48,
        'shares': 30_000 / 2,  # 15,000
        'position_value': 15_000 * 50,  # $750,000
        'use_case': 'Perfect setup, all stars aligned'
    }
    conviction_examples.append(level5)

    return conviction_examples

# 5LC Integration Summary:
# - Level 1-2: Reduce position size (0.5x - 0.75x)
# - Level 3: Standard size (1.0x)
# - Level 4-5: Increase size (1.25x - 1.5x)
#
# This allows you to "press" winners and go light on marginal setups
```

---

## Summary: Complete Risk Management Checklist

```python
risk_management_checklist = {
    "position_level": {
        "risk_per_trade": "1-2% max",
        "position_sizing_method": "Fixed % or ATR-based",
        "stop_loss_type": "ATR, %, or support-based",
        "profit_targets": "ATR multiples or R:R based",
        "min_rr_ratio": "2:1 minimum",
        "max_position_size": "5-25% of account (by value)"
    },

    "portfolio_level": {
        "max_total_risk": "6-10% conservative, 20% aggressive",
        "max_correlated_risk": "Limit same-sector exposure",
        "num_positions": "5-20 positions typical",
        "sector_limits": "20% max per sector",
        "individual_stock_limit": "5-10% max (by value)"
    },

    "market_condition": {
        "bull_market": "Increase size 25-50%",
        "bear_market": "Reduce size 50% or cash",
        "choppy_market": "Reduce size 25%",
        "high_vix": "Reduce size or use wider stops"
    },

    "execution": {
        "never_move_stop_against": "Stops only move in your favor",
        "take_partial_profits": "1/3 to 1/2 at targets",
        "trail_winners": "Use MA or ATR trailing stops",
        "cut_losers_quickly": "No exceptions to stop loss",
        "pyramid_only_winners": "Never add to losers"
    }
}
```

---

## Code-Ready Formulas Summary

### Position Sizing Formula

```python
shares = (account_size * risk_percent / 100) / abs(entry_price - stop_loss)
```

### ATR Stop Loss

```python
stop_loss_long = entry_price - (atr * multiplier)
stop_loss_short = entry_price + (atr * multiplier)
```

### Risk/Reward Ratio

```python
rr_ratio = (target_price - entry_price) / (entry_price - stop_loss)
```

### Expected Value (Expectancy)

```python
expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
```

### Kelly Criterion

```python
kelly_percent = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
```

### Total Portfolio Risk

```python
total_risk_percent = sum(position_risk_percent for each position)
```

---

# Sources

**Qullamaggie (Kristjan Kullamägi):**
- [Deep Dive into Kristjan Kullamägi's Swing Trading Strategies](https://medium.com/@refikberkol/deep-dive-into-kristjan-kullam%C3%A4gis-swing-trading-strategies-an-in-depth-guide-7872e7f1a0cb)
- [3 TIMELESS setups that have made me TENS OF MILLIONS!](https://qullamaggie.com/my-3-timeless-setups-that-have-made-me-tens-of-millions/)
- [Breakout Setup Qullamaggie Style](https://www.mastertradingflow.com/breakouts/)
- [Interview Notes: Qullamaggie on Chat With Traders (Part 1)](https://tradingresourcehub.substack.com/p/interview-qullamaggie-chat-with-traders-part1)
- [Frequently Asked Questions - Qullamaggie](https://qullamaggie.com/faq/)
- [Mastering the Qullamaggie Episodic Pivot Setup](https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/494-Mastering-the-Qullamaggie-Episodic-Pivot-Setup-A-Flexible-Stock-Screening-Approach)

**ATR (Average True Range):**
- [Average True Range (ATR) - Fidelity](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr)
- [Average True Range: Dynamic Stop Loss Levels](https://www.luxalgo.com/blog/average-true-range-dynamic-stop-loss-levels/)
- [ATR: Technical Indicator - FTMO Academy](https://academy.ftmo.com/lesson/atr-technical-indicator/)
- [How to Use ATR in Position Sizing](https://therobusttrader.com/how-to-use-atr-in-position-sizing/)
- [ATR and How Top Traders Size their Positions](https://raposa.trade/blog/atr-and-how-top-traders-size-their-positions/)

**Risk Management - Turtle Traders:**
- [Position Sizing in a Turtle Trading system](https://www.quantifiedstrategies.com/position-sizing-in-a-turtle-trading-system/)
- [The 5 Money Management And Position Sizing Secrets Of The Turtle Traders](https://tradeciety.com/money-management-turtle-traders)
- [Turtle Trading Strategy](https://www.quantifiedstrategies.com/turtle-trading-strategy/)

**Risk Management - Kelly Criterion:**
- [Kelly Criterion and other common position-sizing methods](https://www.tradingview.com/chart/BTCUSDT/CQBmk3MW-Kelly-Criterion-and-other-common-position-sizing-methods/)
- [Kelly Criterion Position Sizing for Optimal Returns](https://www.quantifiedstrategies.com/kelly-criterion-position-sizing/)
- [Kelly's Criterion - Varsity by Zerodha](https://zerodha.com/varsity/chapter/kellys-criterion/)

**Risk Management - Mark Minervini:**
- [Mark Minervini Strategy - ChartMill](https://www.chartmill.com/documentation/stock-screener/fundamental-analysis-investing-strategies/464-Mark-Minervini-Strategy-Think-and-Trade-Like-a-Champion-Part-1)
- [Mark Minervini: The Complete Guide to the SEPA Master](https://www.mavianalytics.com/mark-minervini-the-complete-guide-to-the-sepa-master-and-his-trading-philosophy-2025-edition/)
- [Unlocking the Champion Trader: Mark Minervini's SEPA Growth Stock Strategy](https://www.aminext.blog/en/post/mark-minervini-sepa-strategy-analysis-1)

**Risk Management - William O'Neil:**
- [When To Sell Stocks - A Technical Perspective](https://www.stockopedia.com/content/when-to-sell-stocks-a-technical-perspective-63746/)
- [A Stock-Picker's Guide to William O'Neil's CAN SLIM System](https://blog.portfolio123.com/a-stock-pickers-guide-to-william-oneils-can-slim-system/)
- [O'Neil's Strategies: Trading Tactics Explained](https://www.luxalgo.com/blog/oneils-strategies-trading-tactics-explained/)

**Risk Management - Dan Zanger:**
- [Mastering the Market: The Dan Zanger Story](https://medium.com/@refikberkol/mastering-the-market-the-dan-zanger-story-of-strategy-discipline-and-unyielding-resilience-016d2fa792dd)
- [Dan Zanger – The Trader Who Turned $10,000 Into Millions](https://www.financialwisdomtv.com/post/dan-zanger)

**Trailing Stops:**
- [5 ATR Stop-Loss Strategies for Risk Control](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/)
- [Chandelier Exit - StockCharts](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit)
- [Chandelier Exit Strategy: A Trader's Guide](https://www.quantifiedstrategies.com/chandelier-exit-strategy/)

**Portfolio Risk:**
- [Portfolio Risk Management - Financial Edge](https://www.fe.training/free-resources/portfolio-management/portfolio-risk-management/)
- [Portfolio-Level Risk Constraints](https://breakingalpha.io/insights/portfolio-level-risk-constraints)
- [Sector Weighting: Optimizing Portfolio Weight](https://fastercapital.com/content/Sector-Weighting--Optimizing-Portfolio-Weight-based-on-Industry-Exposure.html)

**Risk/Reward Ratios:**
- [Win Rate and Risk/Reward: Connection Explained](https://www.luxalgo.com/blog/win-rate-and-riskreward-connection-explained/)
- [How To Use The Reward Risk Ratio Like A Professional](https://tradeciety.com/how-to-use-reward-risk-ratio-guide/)
- [Risk/Reward vs. Win Ratio](https://steadyoptions.com/articles/riskreward-vs-win-ratio-r713/)

**Position Sizing Calculators:**
- [Position Sizing in Trading: How to Calculate & Examples](https://www.britannica.com/money/calculating-position-size)
- [Position Sizing, Formula, Tips, and Strategies](https://www.aquafunded.com/blogs/position-size-formula)
- [Position Size Calculator for Stocks](https://www.shiftingshares.com/position-size-calculator/)
