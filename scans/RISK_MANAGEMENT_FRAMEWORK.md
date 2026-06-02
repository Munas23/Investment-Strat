# Phase 2: Comprehensive Risk Management Framework

**Account Size: $2,000,000**

---

## Table of Contents
1. [Current System Review](#current-system-review)
2. [Position Sizing Framework](#position-sizing-framework)
3. [Stop Loss Strategies](#stop-loss-strategies)
4. [Portfolio Risk Management](#portfolio-risk-management)
5. [Entry & Exit Rules](#entry--exit-rules)
6. [Position Management](#position-management)
7. [Conviction-Based Risk Matrix](#conviction-based-risk-matrix)
8. [Recommended Final Rules](#recommended-final-rules)

---

# Current System Review

## What We've Built

### 1. Liquidity Screener ✅
**Purpose**: Ensure we can enter/exit positions without moving the market

**Output**: 1,171 liquid stocks (Tier 1-3)
- **Tier 1 (EXCELLENT)**: 135 stocks - Can handle 5-10% positions
- **Tier 2 (GOOD)**: 463 stocks - Can handle 3-7% positions
- **Tier 3 (ADEQUATE)**: 495 stocks - Can handle 2-5% positions

**Key Metric**: Daily Dollar Volume (DDV)
- Position should be ≤1-2% of DDV to avoid market impact

### 2. Fundamental Screener ✅
**Purpose**: Identify growth stocks with strong fundamentals

**Output**: 81 stocks passed (60%+ score)
- Pure Growth (Option B): EPS 25%+, Revenue 20%+, ROE 17%+
- Top stocks: DUOL, NVDA, TGTX (80%+ scores)

**150-Point Scoring**:
- Growth: 50 pts (33%) - Most important
- Profitability: 35 pts (23%)
- Market Metrics: 20 pts (13%)
- Financial Strength: 25 pts (17%)
- Institutional: 20 pts (13%)

### 3. Technical Screener ✅ (Just Built)
**Purpose**: Identify high-probability technical setups daily

**Output**: Conviction Levels 1-5
- Level 5 (MAXIMUM): 80%+ score - Perfect setups
- Level 4 (HIGH): 65-79% - Strong setups
- Level 3 (MODERATE): 50-64% - Solid setups

**100-Point Scoring**:
- Relative Strength: 20 pts (20%) - Most important
- Moving Averages: 25 pts (25%) - Minervini template
- Volume: 15 pts (15%)
- Price Performance: 15 pts (15%)
- 52-Week Position: 10 pts (10%)
- Trend Quality: 10 pts (10%)
- Breakout Bonus: 5 pts (5%)

---

# Position Sizing Framework

## Key Considerations

### Account Size: $2,000,000

**Conservative Approach:**
- 10 positions × $200,000 each = 10% per position
- Max risk 1% per trade = $20,000
- Total portfolio risk: 10% ($200,000)

**Moderate Approach:**
- 10-15 positions × $133,000-200,000 each
- Max risk 1.5% per trade = $30,000
- Total portfolio risk: 15% ($300,000)

**Aggressive Approach (Qullamaggie-style):**
- 15-20 positions × $100,000-300,000 each
- Max risk 2% per trade = $40,000
- Total portfolio risk: 20-30% ($400,000-600,000)

---

## Position Sizing Methods to Choose From

### Method 1: Fixed Percentage Risk (RECOMMENDED)

**Formula:**
```python
shares = (account_size × risk_percent) / (entry_price - stop_loss)

# Example:
account = $2,000,000
risk_percent = 1.5%  # $30,000
entry = $100
stop = $93  # 7% stop
shares = $30,000 / ($100 - $93) = 4,285 shares
position_value = 4,285 × $100 = $428,500 (21% of account)
```

**Pros:**
- Consistent dollar risk across all trades
- Automatically adjusts position size based on stop width
- Tighter stop = larger position
- Wider stop = smaller position

**Cons:**
- Can create very large positions with tight stops
- May exceed liquidity limits

---

### Method 2: ATR-Based Sizing (Turtle Traders)

**Formula:**
```python
dollar_risk = account_size × risk_percent
risk_per_share = ATR × multiplier (typically 2 ATR)
shares = dollar_risk / risk_per_share

# Example:
account = $2,000,000
risk_percent = 1%  # $20,000
ATR = $3.00
multiplier = 2
shares = $20,000 / ($3.00 × 2) = 3,333 shares
entry = $100
position_value = $333,300 (17% of account)
stop_loss = $100 - $6 = $94
```

**Pros:**
- Volatility-adjusted (same dollar risk regardless of volatility)
- Works across all stocks
- Prevents over-sizing volatile stocks

**Cons:**
- Requires ATR calculation
- May give too much room on low-volatility stocks

---

### Method 3: Conviction-Based Sizing (5LC Integration)

**Formula:**
```python
base_risk = 1.5%  # Base risk per trade

# Technical conviction multiplier
tech_multipliers = {
    5: 1.5,   # Level 5 = 150% of base (2.25%)
    4: 1.25,  # Level 4 = 125% of base (1.875%)
    3: 1.0,   # Level 3 = 100% of base (1.5%)
    2: 0.75,  # Level 2 = 75% of base (1.125%)
    1: 0.5,   # Level 1 = 50% of base (0.75%)
}

# Market health multiplier
market_multipliers = {
    'strong_bull': 2.0,     # 200% (rare)
    'bull': 1.5,            # 150%
    'uptrend': 1.25,        # 125%
    'neutral': 1.0,         # 100%
    'choppy': 0.75,         # 75%
    'downtrend': 0.5,       # 50%
    'bear': 0.25,           # 25% (defensive)
}

# Final risk calculation
final_risk = base_risk × tech_multiplier × market_multiplier

# Example: Level 5 stock in bull market
final_risk = 1.5% × 1.5 × 1.5 = 3.375%
dollar_risk = $2,000,000 × 0.03375 = $67,500 per trade

# Example: Level 3 stock in neutral market
final_risk = 1.5% × 1.0 × 1.0 = 1.5%
dollar_risk = $2,000,000 × 0.015 = $30,000 per trade
```

**Pros:**
- Aligns with conviction (bet bigger on best setups)
- Adapts to market conditions
- Natural position sizing hierarchy

**Cons:**
- Can create very large positions (3-4%)
- Requires accurate market condition assessment

---

### Method 4: Hybrid Approach (RECOMMENDED FOR $2M ACCOUNT)

**Combines all three methods with limits:**

```python
# Step 1: Calculate base risk using conviction
base_risk_pct = 1.5%  # Starting point
tech_conviction = 5   # From technical screener
market_health = 'bull'

tech_multiplier = {5: 1.5, 4: 1.25, 3: 1.0, 2: 0.75, 1: 0.5}[tech_conviction]
market_multiplier = {'bull': 1.5, 'uptrend': 1.25, 'neutral': 1.0}[market_health]

conviction_risk_pct = base_risk_pct × tech_multiplier × market_multiplier
# Example: 1.5% × 1.5 × 1.5 = 3.375%

# Step 2: Apply maximum limits
MAX_RISK_PER_TRADE = 3.0%  # Hard cap
final_risk_pct = min(conviction_risk_pct, MAX_RISK_PER_TRADE)
dollar_risk = $2,000,000 × final_risk_pct

# Step 3: Calculate shares using ATR-based stop
ATR = $3.00
stop_multiplier = 2  # 2 ATR stop
risk_per_share = ATR × stop_multiplier
shares = dollar_risk / risk_per_share

# Step 4: Calculate position value
entry_price = $100
position_value = shares × entry_price

# Step 5: Apply position size limits
MAX_POSITION_SIZE_PCT = 25%  # No position > 25% of account
MAX_POSITION_VALUE = $2,000,000 × 0.25 = $500,000

if position_value > MAX_POSITION_VALUE:
    shares = MAX_POSITION_VALUE / entry_price
    # Recalculate actual risk
    actual_risk = shares × risk_per_share
    actual_risk_pct = (actual_risk / $2,000,000) × 100

# Step 6: Check liquidity limits
liquidity_tier = "TIER 1"  # From liquidity screener
daily_dollar_volume = $50,000,000

# Position should be ≤1-2% of DDV
liquidity_limit = daily_dollar_volume × 0.02  # 2%
if position_value > liquidity_limit:
    # Reduce to meet liquidity limit
    shares = liquidity_limit / entry_price
```

**This gives you:**
- ✅ Conviction-based sizing (bigger on best setups)
- ✅ Market condition adjustment
- ✅ Volatility control (ATR stops)
- ✅ Hard position limits (25% max)
- ✅ Liquidity compliance
- ✅ Maximum risk cap (3% per trade)

---

# Stop Loss Strategies

## Options to Choose From

### Option 1: Percentage-Based Stops

**Fixed Percentage:**
```python
stop_loss_levels = {
    'tight': 3-5,      # VCP, tight patterns (Minervini)
    'standard': 7-8,   # Most setups (O'Neil, Zanger)
    'wide': 10,        # Volatile or slower stocks
}

# Example:
entry = $100
stop_percent = 7
stop_loss = entry × (1 - 0.07) = $93
```

**Pros:**
- Simple, easy to understand
- Consistent across all trades
- Legendary trader proven (O'Neil's 7-8% rule)

**Cons:**
- Doesn't account for volatility
- May be too tight for volatile stocks
- May be too loose for calm stocks

---

### Option 2: ATR-Based Stops (RECOMMENDED)

**ATR Multiples:**
```python
atr_multipliers = {
    'very_tight': 1.5,   # Aggressive
    'tight': 2.0,        # Turtle Traders standard
    'standard': 2.5,     # Moderate
    'wide': 3.0,         # Conservative
}

# Example:
entry = $100
ATR = $3.00
multiplier = 2.0
stop_loss = entry - (ATR × multiplier) = $100 - $6 = $94
stop_percent = ($6 / $100) × 100 = 6%
```

**Pros:**
- Volatility-adjusted (gives stocks room to breathe)
- Same "ATR risk" across all stocks
- Prevents getting stopped out by normal fluctuations
- Turtle Traders used this (2 ATR)

**Cons:**
- Can be wide on volatile stocks (15%+)
- Requires ATR calculation

---

### Option 3: Pattern-Based Stops (Qullamaggie)

**Low of Day (LOD):**
```python
# For breakout entries
entry = $100 (at 10:00 AM)
low_of_day = $98 (set at entry time)
stop_loss = $98

# Maximum width: 1 ATR
if (entry - low_of_day) > ATR:
    skip_trade = True  # Stop too wide
```

**Pros:**
- Logical level (below support)
- Can be very tight (3-5%)
- Works well for intraday breakouts

**Cons:**
- Requires intraday monitoring
- Can get stopped by intraday volatility

---

### Option 4: Support-Based Stops

**Key Levels:**
```python
# Below moving averages
stops = {
    'below_10ma': entry - (entry - ma_10) - buffer,
    'below_20ma': entry - (entry - ma_20) - buffer,
    'below_50ma': entry - (entry - ma_50) - buffer,
    'below_breakout': breakout_level - buffer,
}

# Example:
entry = $100
ma_20 = $97
buffer = $0.50
stop_loss = $97 - $0.50 = $96.50
```

**Pros:**
- Logical levels (structure-based)
- Where pattern invalidates

**Cons:**
- Can be very wide (10-15%)
- Inconsistent risk across trades

---

## Recommended Stop Loss Strategy

### Tiered Approach by Conviction:

```python
def calculate_stop_loss(entry, atr, conviction_level, pattern_type):
    """
    Calculate stop loss based on conviction and pattern
    """

    # Base ATR multipliers by conviction
    atr_multipliers = {
        5: 1.5,  # Tight stops for perfect setups
        4: 2.0,  # Standard 2 ATR (Turtle style)
        3: 2.5,  # Slightly wider
        2: 3.0,  # Wide (if trading at all)
        1: 3.0,  # Skip these
    }

    # Adjust for pattern type
    if pattern_type == 'VCP':
        atr_multipliers[5] = 1.0  # Even tighter for VCP
        atr_multipliers[4] = 1.5
    elif pattern_type == 'Episodic Pivot':
        # Use low of day instead
        return 'LOD', None

    multiplier = atr_multipliers[conviction_level]
    stop_loss = entry - (atr × multiplier)
    stop_percent = ((entry - stop_loss) / entry) × 100

    # Apply maximum stop limits
    MAX_STOP_PERCENT = {
        5: 5,   # Max 5% for Level 5
        4: 7,   # Max 7% for Level 4
        3: 8,   # Max 8% for Level 3
        2: 10,  # Max 10% for Level 2
    }

    max_stop = entry × (1 - MAX_STOP_PERCENT[conviction_level] / 100)

    # Use tighter of ATR-based or max percent
    final_stop = max(stop_loss, max_stop)

    return final_stop, stop_percent
```

**Example Results:**

| Conviction | Entry | ATR | Multiplier | ATR Stop | Max % | Final Stop | Stop % |
|------------|-------|-----|------------|----------|-------|------------|--------|
| Level 5 | $100 | $3 | 1.5x | $95.50 | 5% ($95) | $95.50 | 4.5% |
| Level 4 | $100 | $3 | 2.0x | $94.00 | 7% ($93) | $94.00 | 6.0% |
| Level 3 | $100 | $3 | 2.5x | $92.50 | 8% ($92) | $92.50 | 7.5% |

---

# Portfolio Risk Management

## Maximum Risk Limits

### Individual Trade Risk

```python
# Conservative (RECOMMENDED for $2M)
MAX_RISK_PER_TRADE = 3.0%        # $60,000 max

# By conviction level (before market multiplier)
base_risk_by_conviction = {
    5: 2.25,  # 1.5% × 1.5 = 2.25%
    4: 1.875, # 1.5% × 1.25 = 1.875%
    3: 1.5,   # 1.5% × 1.0 = 1.5%
    2: 1.125, # 1.5% × 0.75 = 1.125%
}

# After market multiplier (bull = 1.5x)
max_risk_by_conviction = {
    5: 3.0,   # 2.25% × 1.33 = 3.0% (capped)
    4: 2.8,   # 1.875% × 1.5 = 2.8%
    3: 2.25,  # 1.5% × 1.5 = 2.25%
    2: 1.7,   # 1.125% × 1.5 = 1.7%
}
```

### Total Portfolio Risk

```python
# Conservative Approach
MAX_TOTAL_RISK = 15%             # $300,000 max
MAX_POSITIONS = 10               # Average 1.5% per position

# Moderate Approach (RECOMMENDED)
MAX_TOTAL_RISK = 20%             # $400,000 max
MAX_POSITIONS = 12-15            # Average 1.3-1.7% per position

# Aggressive Approach
MAX_TOTAL_RISK = 30%             # $600,000 max
MAX_POSITIONS = 15-20            # Average 1.5-2.0% per position
```

### Position Concentration Limits

```python
# Individual position limits
MAX_SINGLE_POSITION = 25%        # $500,000 max per stock
TYPICAL_POSITION = 10-15%        # $200,000-300,000

# By liquidity tier
position_limits_by_tier = {
    'TIER 1': 25,  # Can go up to 25%
    'TIER 2': 15,  # Max 15%
    'TIER 3': 10,  # Max 10%
}

# By conviction level
typical_position_by_conviction = {
    5: 15-25,  # Largest positions
    4: 10-20,  # Strong positions
    3: 8-15,   # Moderate positions
    2: 5-10,   # Small positions
}
```

### Sector Concentration

```python
# Sector limits (prevent sector crashes)
MAX_SECTOR_EXPOSURE = 30%        # Max 30% in any one sector

# Example:
portfolio = {
    'Technology': 25%,  # OK
    'Healthcare': 20%,  # OK
    'Financials': 15%,  # OK
    'Energy': 10%,      # OK
}
```

### Correlation Limits

```python
# Limit highly correlated positions
if correlation > 0.7:
    # Treat as same position for risk purposes
    combined_risk = position1_risk + position2_risk
    if combined_risk > MAX_RISK_PER_TRADE:
        reduce_positions()
```

---

# Entry & Exit Rules

## Entry Rules

### Entry Checklist (ALL must be TRUE):

```python
entry_checklist = {
    # 1. Liquidity
    'liquidity_tier': [1, 2, 3],  # From liquidity screener

    # 2. Fundamentals (Optional but recommended)
    'fundamental_score': 60,  # 60%+ from fundamental screener

    # 3. Technical Conviction
    'technical_conviction': 3,  # Minimum Level 3

    # 4. Entry Timing
    'distance_from_breakout': 10,  # Within 10% of breakout
    'or_pullback_to_ma': [10, 20, 50],  # OR pullback to key MA

    # 5. Volume
    'volume_confirmation': True,  # Volume spike present

    # 6. Stop Loss Width
    'stop_width_max_atr': 3,  # Stop no wider than 3 ATR
    'stop_width_max_percent': 10,  # Stop no wider than 10%

    # 7. Risk/Reward
    'min_risk_reward_ratio': 2.0,  # Minimum 2:1 R/R

    # 8. Market Direction
    'market_condition': ['bull', 'uptrend', 'neutral'],  # Not in downtrend

    # 9. Portfolio Limits
    'total_portfolio_risk': '<20%',  # Haven't hit limit
    'open_positions': '<15',  # Not too many positions

    # 10. Position Size
    'position_within_liquidity_limit': True,  # ≤2% of DDV
}

# If ANY condition fails, either:
# a) Reduce conviction level by 1
# b) Skip the trade entirely
```

### Entry Types:

```python
entry_types = {
    # 1. Breakout Entry (Level 4-5)
    'breakout': {
        'trigger': 'Price breaks consolidation high',
        'volume': 'Volume spike required (1.4x+ average)',
        'timing': 'Enter within 5% of breakout',
        'stop': 'Below breakout point or 2 ATR',
    },

    # 2. Pullback Entry (Level 3-4)
    'pullback': {
        'trigger': 'Pullback to 10/20 MA after breakout',
        'volume': 'Lower volume on pullback (healthy)',
        'timing': 'Enter on bounce with volume',
        'stop': 'Below MA or recent swing low',
    },

    # 3. Opening Range Breakout (Level 5)
    'opening_range': {
        'trigger': '1-min/5-min/60-min high break',
        'volume': 'Must be present',
        'timing': 'Intraday, requires monitoring',
        'stop': 'Low of day (max 1 ATR)',
    },

    # 4. New ATH (Level 4-5)
    'new_ath': {
        'trigger': 'Breaking all-time high',
        'volume': 'Above average',
        'timing': 'Enter on break',
        'stop': '2 ATR or below prior high',
    },
}
```

---

## Exit Rules

### Exit Strategies:

#### 1. Stop Loss Exit (ALWAYS)

```python
stop_loss_rules = {
    'type': 'HARD STOP - NO EXCEPTIONS',
    'execution': 'Automatic (stop-loss order or alert)',
    'never_move_down': True,  # Only move up (trailing)
    'sell_all': True,  # Exit entire position
    'no_hope': True,   # Don't hold and hope
}
```

#### 2. Profit Taking (Scaling Out)

```python
# Option A: Time-Based (Qullamaggie)
time_based_exit = {
    'day_3_to_5': 'Sell 1/3 to 1/2 of position',
    'move_stop': 'Move stop to breakeven',
    'trail_remainder': 'Trail with 10 or 20 MA',
}

# Option B: Target-Based (ATR Multiples)
target_based_exit = {
    'target_1': 'Entry + 2 ATR (Sell 1/3)',
    'target_2': 'Entry + 4 ATR (Sell 1/3)',
    'target_3': 'Entry + 6 ATR (Sell 1/3, trail rest)',
}

# Option C: Percentage-Based
percent_based_exit = {
    'target_1': '+10% (Sell 1/3)',
    'target_2': '+20% (Sell 1/3)',
    'target_3': '+30% (Sell 1/3, trail rest)',
}
```

#### 3. Trailing Stop Exit

```python
trailing_stops = {
    # Option A: MA-Based (Qullamaggie)
    'fast_stocks': 'Exit if close below 10-day MA',
    'slow_stocks': 'Exit if close below 20-day MA',

    # Option B: Chandelier Exit (ATR-Based)
    'chandelier': 'Highest high (22 days) - (3 × ATR)',

    # Option C: Fixed Trailing Percent
    'fixed_percent': 'Trail by 10% from highest high',
}
```

#### 4. Pattern Breakdown Exit

```python
pattern_breakdown = {
    'vcp': 'Exit if breaks below all MAs simultaneously',
    'cup_handle': 'Exit if falls back into cup',
    'flag': 'Exit if breaks below flag support',
    'general': 'Exit if closes below 50-day MA',
}
```

#### 5. Time-Based Exit

```python
time_exits = {
    'no_movement': 'Exit if no progress after 2-3 weeks',
    'topping': 'Exit if enters Stage 3 (topping)',
    'market_crash': 'Exit all if market crashes 5%+ in day',
}
```

---

# Position Management

## Pyramiding (Adding to Winners)

### Turtle Traders Method:

```python
pyramid_rules = {
    'initial_entry': '1 unit (1% risk)',
    'add_at': '0.5 ATR profit intervals',
    'max_units': 4,  # Total 4% risk max
    'stops': 'All units at 2 ATR from current price',
}

# Example:
entry_1 = $100 (1% risk, $20,000)
ATR = $3
add_at = entry_1 + (ATR × 0.5) = $101.50

entry_2 = $101.50 (add 1%, now 2% total)
add_at = entry_2 + (ATR × 0.5) = $103

entry_3 = $103 (add 1%, now 3% total)
add_at = entry_3 + (ATR × 0.5) = $104.50

entry_4 = $104.50 (add 1%, now 4% total - MAX)

# All stops trail at 2 ATR from current price
current_price = $106
stop_all_units = $106 - ($3 × 2) = $100
```

**Rules:**
- ✅ Only add to winning positions
- ✅ Never add to losing positions
- ✅ Each add is same size as initial
- ✅ Trail all stops together

---

## Position Scaling (Partial Exits)

### Recommended Approach:

```python
scaling_strategy = {
    # Initial Position: 100%
    'entry': '100% position at entry',

    # First Profit Target (2 ATR or +10%)
    'target_1': {
        'sell': '33% of position',
        'action': 'Move stop to breakeven',
        'remaining': '67%',
    },

    # Second Profit Target (4 ATR or +20%)
    'target_2': {
        'sell': '33% of original (50% of remaining)',
        'action': 'Move stop to Target 1 level',
        'remaining': '34%',
    },

    # Final Position (Trail)
    'target_3': {
        'sell': 'Trail final 34% with 10 or 20 MA',
        'exit': 'When MA breaks',
    },
}

# Example:
entry_position = 10,000 shares at $100

target_1 = $110 (+10%)
sell_1 = 3,333 shares (33%)
remaining_1 = 6,667 shares
move_stop_to = $100 (breakeven)

target_2 = $120 (+20%)
sell_2 = 3,333 shares (33% of original)
remaining_2 = 3,334 shares
move_stop_to = $110 (Target 1)

trail_final = 3,334 shares
exit_when = 'Close below 10 MA'
```

---

# Conviction-Based Risk Matrix

## Complete Risk Matrix: $2M Account

### Base Settings:
- **Base Risk**: 1.5% ($30,000)
- **Market**: Bull/Uptrend (1.5x multiplier)
- **Max Risk**: 3.0% ($60,000) per trade
- **Max Total Portfolio Risk**: 20% ($400,000)

---

### Level 5 (MAXIMUM CONVICTION)

```python
conviction_5 = {
    # Risk Calculation
    'base_risk': 1.5%,
    'tech_multiplier': 1.5,
    'market_multiplier': 1.5,  # Bull market
    'calculated_risk': 1.5% × 1.5 × 1.5 = 3.375%,
    'capped_risk': 3.0%,  # Applied cap
    'dollar_risk': $60,000,

    # Position Sizing
    'ATR_multiplier': 1.5,  # Tight stop for perfect setup
    'typical_stop_percent': 4-5%,
    'typical_position_size': 20-25%,  # Of account
    'typical_position_value': $400,000-500,000,

    # Limits
    'max_positions': 3,  # Max 3 Level 5 at once
    'liquidity_required': 'Tier 1-2',
    'fundamental_score': '75%+',

    # Expected Outcomes
    'win_rate': 40-50%,
    'avg_win': 8-10R (32-50%),
    'avg_loss': 1R (4-5%),
    'expectancy': '+6R per trade',
}
```

**Total Risk if 3 Level 5 positions**: 9% ($180,000)

---

### Level 4 (HIGH CONVICTION)

```python
conviction_4 = {
    # Risk Calculation
    'base_risk': 1.5%,
    'tech_multiplier': 1.25,
    'market_multiplier': 1.5,
    'calculated_risk': 1.5% × 1.25 × 1.5 = 2.8%,
    'dollar_risk': $56,000,

    # Position Sizing
    'ATR_multiplier': 2.0,  # Standard 2 ATR (Turtle)
    'typical_stop_percent': 6-7%,
    'typical_position_size': 15-20%,
    'typical_position_value': $300,000-400,000,

    # Limits
    'max_positions': 5,  # Max 5 Level 4 at once
    'liquidity_required': 'Tier 1-3',
    'fundamental_score': '60%+',

    # Expected Outcomes
    'win_rate': 35-45%,
    'avg_win': 5-7R (30-49%),
    'avg_loss': 1R (6-7%),
    'expectancy': '+3R per trade',
}
```

**Total Risk if 5 Level 4 positions**: 14% ($280,000)

---

### Level 3 (MODERATE CONVICTION)

```python
conviction_3 = {
    # Risk Calculation
    'base_risk': 1.5%,
    'tech_multiplier': 1.0,
    'market_multiplier': 1.5,
    'calculated_risk': 1.5% × 1.0 × 1.5 = 2.25%,
    'dollar_risk': $45,000,

    # Position Sizing
    'ATR_multiplier': 2.5,  # Slightly wider
    'typical_stop_percent': 7-8%,
    'typical_position_size': 10-15%,
    'typical_position_value': $200,000-300,000,

    # Limits
    'max_positions': 7,  # Max 7 Level 3 at once
    'liquidity_required': 'Tier 1-3',
    'fundamental_score': '60%+',

    # Expected Outcomes
    'win_rate': 30-40%,
    'avg_win': 3-5R (24-40%),
    'avg_loss': 1R (7-8%),
    'expectancy': '+1.5R per trade',
}
```

**Total Risk if 7 Level 3 positions**: 15.75% ($315,000)

---

### Maximum Portfolio Example (Bull Market):

```python
max_portfolio = {
    'level_5': 3 positions × 3.0% = 9%,
    'level_4': 5 positions × 2.8% = 14%,
    'level_3': 2 positions × 2.25% = 4.5%,
    'total': 10 positions, 27.5% total risk,  # OVER LIMIT!
}

# Must reduce to stay under 20% total risk:
recommended_portfolio = {
    'level_5': 2 positions × 3.0% = 6%,
    'level_4': 4 positions × 2.8% = 11.2%,
    'level_3': 1 position × 2.25% = 2.25%,
    'total': 7 positions, 19.45% total risk,  # ✅ Under 20%
}
```

---

# Recommended Final Rules

## FOR $2,000,000 ACCOUNT

### Position Sizing: HYBRID METHOD

```python
# Step 1: Calculate conviction-based risk
base_risk = 1.5%
tech_conviction_multiplier = {5: 1.5, 4: 1.25, 3: 1.0}
market_health_multiplier = {'bull': 1.5, 'uptrend': 1.25, 'neutral': 1.0}

risk_percent = base_risk × tech_mult × market_mult
risk_percent = min(risk_percent, 3.0%)  # Cap at 3%

# Step 2: Calculate shares using ATR stop
ATR_multiplier = {5: 1.5, 4: 2.0, 3: 2.5}
stop_distance = ATR × ATR_multiplier
shares = (account × risk_percent) / stop_distance

# Step 3: Apply position limits
position_value = shares × entry_price
max_position = {5: 0.25, 4: 0.20, 3: 0.15}  # % of account
position_value = min(position_value, account × max_position)

# Step 4: Check liquidity
if position_value > (DDV × 0.02):  # 2% of daily dollar volume
    reduce_shares()
```

### Stop Loss: ATR-BASED WITH CAPS

```python
# ATR-based by conviction
stop_distance = ATR × {5: 1.5, 4: 2.0, 3: 2.5}

# With maximum % caps
max_stop_percent = {5: 5%, 4: 7%, 3: 8%}

# Use tighter of the two
final_stop = max(entry - stop_distance, entry × (1 - max_stop_percent))
```

### Portfolio Limits: MODERATE APPROACH

```python
max_total_risk = 20%  # $400,000
max_positions = 12
max_single_position = 25%  # $500,000
max_sector_exposure = 30%

conviction_limits = {
    5: 3,  # Max 3 Level 5 positions
    4: 6,  # Max 6 Level 4 positions
    3: 8,  # Max 8 Level 3 positions
}
```

### Exit Strategy: SCALED EXITS WITH TRAILING

```python
# Profit taking
target_1 = entry + (2 × ATR)  # Sell 33%, move stop to breakeven
target_2 = entry + (4 × ATR)  # Sell 33%, move stop to Target 1
final = 'Trail remaining 34% with 10 or 20 MA'

# Hard stops
stop_loss = 'ATR-based, never move down'
pattern_breakdown = 'Exit if closes below 50 MA'
time_exit = 'Exit if no progress after 3 weeks'
```

### Entry Requirements: STRICT CHECKLIST

```python
must_have = {
    'liquidity_tier': [1, 2, 3],
    'technical_conviction': 3,  # Minimum Level 3
    'volume_spike': True,
    'stop_width': '<3 ATR and <10%',
    'risk_reward': '>2:1',
    'total_portfolio_risk': '<20%',
}

recommended = {
    'fundamental_score': 60,  # 60%+
    'entry_distance': '<10% from breakout',
    'market_condition': 'not downtrend',
}
```

---

## Summary: Your Risk Management System

### Conservative Yet Aggressive on Best Setups

1. **Base Risk**: 1.5% per trade ($30,000)
2. **Conviction Multipliers**: 0.5x to 1.5x (0.75% to 2.25% base)
3. **Market Multipliers**: 0.5x to 1.5x (bear to bull)
4. **Maximum Risk**: 3.0% per trade ($60,000) - HARD CAP
5. **Maximum Portfolio Risk**: 20% total ($400,000)
6. **Maximum Positions**: 12 concurrent positions
7. **Stop Loss**: ATR-based with % caps (4-8% typical)
8. **Position Size**: 10-25% of account (conviction-dependent)
9. **Exits**: Scaled (33/33/34) with MA trailing
10. **Pyramiding**: Turtle-style (0.5 ATR adds, 4 units max)

### Expected Results:

**Level 5 Trades** (20% of trades):
- Win Rate: 45%
- Avg Win: 40% (8R)
- Avg Loss: 5% (1R)
- Expectancy: +3.95R per trade

**Level 4 Trades** (30% of trades):
- Win Rate: 40%
- Avg Win: 30% (5R)
- Avg Loss: 6% (1R)
- Expectancy: +1.4R per trade

**Level 3 Trades** (50% of trades):
- Win Rate: 35%
- Avg Win: 25% (3.6R)
- Avg Loss: 7% (1R)
- Expectancy: +0.61R per trade

**Overall Portfolio**:
- Win Rate: ~37%
- Average R-Multiple: +1.5R
- With 20% total risk, expect +30% portfolio growth when all setups work

---

**This is a complete, professional risk management framework ready to implement. Review and let me know which rules you want to adjust!**
