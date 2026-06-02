# Breakout & Conviction Technical Criteria Summary

A comprehensive synthesis of technical setups from legendary traders, organized by conviction level and breakout quality.

---

## Table of Contents
1. [Conviction Levels Framework](#conviction-levels-framework)
2. [Stage Analysis - Primary Filter](#stage-analysis---primary-filter)
3. [Moving Average Alignment](#moving-average-alignment)
4. [Chart Patterns & Setups](#chart-patterns--setups)
5. [Volume Analysis](#volume-analysis)
6. [Relative Strength](#relative-strength)
7. [Entry Timing & Triggers](#entry-timing--triggers)
8. [Complete Screening Criteria by Conviction](#complete-screening-criteria-by-conviction)

---

# Conviction Levels Framework

## How to Assign Conviction Levels (1-5)

### Level 5: MAXIMUM CONVICTION (Rare - Only Perfect Setups)
**All criteria must be met:**
- ✅ Stage 2 confirmed (all MAs aligned)
- ✅ Perfect pattern (VCP final contraction OR tight cup-handle OR HTF)
- ✅ RS Rating 90+ (top 10% of market)
- ✅ Explosive volume on breakout (100%+ above average)
- ✅ Fundamentals: EPS 40%+, Revenue 30%+
- ✅ Breaking to new 52-week high or ATH
- ✅ All 8 Minervini trend template criteria met
- ✅ Entry within 5% of breakout point

**Risk Parameters:**
- Stop: 3-5% (VCP tight)
- Expected R:R: 4:1 to 8:1
- Win Rate: 35-45%

### Level 4: HIGH CONVICTION (Strong Setups)
**Most criteria met:**
- ✅ Stage 2 confirmed
- ✅ Good pattern (VCP OR cup-handle OR flag)
- ✅ RS Rating 85+ (top 15%)
- ✅ Strong volume on breakout (50-100% above average)
- ✅ Fundamentals: EPS 25%+, Revenue 20%+
- ✅ Within 25% of 52-week high
- ✅ 6-7 of Minervini criteria met
- ⚠️ Entry within 5-10% of breakout

**Risk Parameters:**
- Stop: 5-7%
- Expected R:R: 3:1 to 5:1
- Win Rate: 30-40%

### Level 3: MODERATE CONVICTION (Solid Setups)
**Core criteria met:**
- ✅ Stage 2 (may be early or mid-stage)
- ✅ Acceptable pattern (flags, triangles, flat base)
- ✅ RS Rating 80+ (top 20%)
- ✅ Good volume (40-50% above average)
- ✅ Fundamentals: EPS 20%+, Revenue 15%+
- ✅ 5-6 of Minervini criteria met
- ⚠️ Entry up to 10% above breakout

**Risk Parameters:**
- Stop: 7-8%
- Expected R:R: 2:1 to 3:1
- Win Rate: 25-35%

### Level 2: LOW CONVICTION (Speculative)
**Minimal criteria:**
- ⚠️ Stage 2 questionable or early
- ⚠️ Pattern acceptable but not ideal
- ⚠️ RS Rating 70-79
- ⚠️ Volume average or slightly above
- ⚠️ Fundamentals: EPS 15%+
- ⚠️ 4-5 of Minervini criteria met
- ❌ Entry extended (10-15% above breakout)

**Risk Parameters:**
- Stop: 8-10%
- Expected R:R: 1.5:1 to 2:1
- Win Rate: 20-30%

### Level 1: MINIMAL CONVICTION (Avoid or Very Small)
**Few criteria met:**
- ❌ Stage unclear or Stage 3
- ❌ Weak pattern or no pattern
- ❌ RS Rating <70
- ❌ Low volume breakout
- ❌ Weak fundamentals
- ❌ Extended entry (>15% from breakout)

**Risk Parameters:**
- Stop: 10%+
- Expected R:R: 1:1 to 1.5:1
- Win Rate: <20%
- **Action: SKIP THESE TRADES**

---

# Stage Analysis - Primary Filter

## Stage 2: The ONLY Buy Zone

**All legendary traders focus exclusively on Stage 2 stocks.**

### Stage 2 Criteria (Stan Weinstein)

```python
# Weekly Chart Analysis
stage_2_criteria = {
    # Price Position
    "price_above_30w_ma": True,
    "making_higher_highs": True,
    "making_higher_lows": True,  # CRITICAL - both required

    # 30-Week MA Behavior
    "30w_ma_rising": True,
    "30w_ma_below_price": True,

    # Volume
    "breakout_volume": "2-3x average minimum",

    # Action
    "recommendation": "BUY ZONE - Primary buying area"
}
```

### Daily Chart Confirmation

```python
# Minervini's 8-Point Trend Template
trend_template = {
    1: "price > 150_day_ma AND price > 200_day_ma",
    2: "150_day_ma > 200_day_ma",
    3: "200_day_ma trending up (1+ months)",
    4: "50_day_ma > 150_day_ma AND 50_day_ma > 200_day_ma",
    5: "price > 50_day_ma",
    6: "price > 30% above 52_week_low",
    7: "price within 25% of 52_week_high",
    8: "rs_rating >= 85"
}

# ALL 8 must be TRUE for maximum conviction
# 6-7 = High conviction
# 5-6 = Moderate conviction
# <5 = Low conviction (avoid)
```

### Qullamaggie's MA Alignment

```python
# During Consolidation (Pre-Breakout)
qullamaggie_mas = {
    "10_day_ma": "Price surfing above (respecting)",
    "20_day_ma": "Price surfing above (respecting)",
    "50_day_ma": "Rising and close behind price",
    "all_mas_rising": True,
    "higher_lows": True,
    "tightening_range": True
}

# Exit Signals
exit_fast_stocks = "Close below 10-day MA"
exit_slow_stocks = "Close below 20-day MA"
```

---

# Moving Average Alignment

## Critical MA Configurations

### Perfect Alignment (Level 5 Conviction)

```
Price (breaking out)
  ↑
50-day MA (rising, slope >15°)
  ↑
150-day MA (rising)
  ↑
200-day MA (rising for 1+ months)

All MAs rising + price above all = PERFECT
```

### Good Alignment (Level 4 Conviction)

```
Price above 50/150/200 MA
50 MA above 150/200 MA
Most MAs rising
May have slight flatten in 150/200 MA = OK
```

### Acceptable Alignment (Level 3 Conviction)

```
Price above most MAs
50 MA above 200 MA
200 MA flat or slightly rising
Stage 2 confirmed but not perfect
```

### Weak Alignment (Level 1-2 - AVOID)

```
Price below any major MA
MAs crossed or tangled
200 MA declining
Stage 3 or Stage 4 = DO NOT BUY
```

## Specific MA Rules by Trader

| Trader | Primary MAs | Key Rule |
|--------|-------------|----------|
| **Minervini** | 50, 150, 200 (SMA) | All 8 criteria template |
| **O'Neil** | 50, 200 (SMA) | Price > 50 MA during base |
| **Qullamaggie** | 10, 20, 50 (SMA) | Surfing 10/20, exit below |
| **Schwartz** | 10 (EMA) | Above = long only, below = short only |
| **Weinstein** | 30-week (~150-day) | Above = Stage 2, below = Stage 4 |

---

# Chart Patterns & Setups

## Tier 1: Highest Conviction Patterns

### 1. Volatility Contraction Pattern (VCP) - Minervini

**Conviction: Level 4-5**

```python
vcp_criteria = {
    # Prior Trend
    "prior_uptrend": "Required - must have established uptrend",

    # Pullback Sequence
    "pullback_1": "15-25% depth",
    "pullback_2": "10-15% depth (smaller than #1)",
    "pullback_3": "5-10% depth (smaller than #2)",
    "final_pullback": "3-8% depth (tightest)",

    # Duration
    "total_pattern": "4-12 weeks typical",
    "pullbacks": "2-6 pullbacks minimum",

    # Volume
    "volume_behavior": "Decreasing with each pullback",
    "volume_breakout": "Explosive expansion",

    # Line of Least Resistance
    "price_action": "Tightening left to right on chart",
    "higher_lows": True,
    "contracting_range": True,

    # Entry
    "entry_point": "Break of final tight pivot",
    "entry_distance": "Within 5% of breakout",

    # Stop
    "stop_loss": "3-5% below entry (tight)"
}

# Why Highest Conviction:
# - Pattern shows controlled selling (smart money accumulation)
# - Decreasing volatility = coiling spring
# - Final breakout = explosive move likely
# - Tight stop = excellent risk/reward (4:1 to 8:1)
```

### 2. Cup-with-Handle - O'Neil

**Conviction: Level 4-5**

```python
cup_with_handle = {
    # Cup Formation
    "cup_shape": "U-shaped preferred (not V)",
    "cup_depth": "12-33% of prior advance (max 50% in volatile markets)",
    "cup_duration": "7-65 weeks",
    "prior_advance": "Minimum 30% from last low",

    # Handle Formation
    "handle_depth": "10-30% of cup height (max 1/3)",
    "handle_duration": "Days to weeks (shorter than cup)",
    "handle_volume": "Declining (CRITICAL)",
    "handle_shape": "Tight, low-volume pullback",

    # Entry
    "entry_trigger": "Break above handle resistance",
    "entry_volume": "40%+ above average (1.4x minimum, 2x+ ideal)",
    "entry_distance": "Within 5% of breakout ideal",

    # Stop
    "stop_loss": "7-8% below entry (O'Neil's hard rule)"
}

# Why High Conviction:
# - Proven pattern (decades of data)
# - Institutional accumulation during cup
# - Handle shakes out weak hands
# - Volume expansion confirms breakout
```

### 3. High Tight Flag (HTF) - O'Neil/Qullamaggie

**Conviction: Level 5 (when perfect)**

```python
high_tight_flag = {
    # Prior Move (CRITICAL)
    "prior_move": "90-100%+ in short period (1-3 months)",
    "move_characteristic": "Nearly vertical advance",

    # Flag/Consolidation
    "consolidation_depth": "15-25% retracement from peak",
    "consolidation_duration": "2-8 weeks",
    "volume_during_flag": "Diminished significantly",

    # Pattern Signal
    "market_sentiment": "Latent bullish pressure",
    "tightening": "Price range contracting",

    # Entry
    "entry": "Breakout from tight flag on volume",

    # Why Rare But Powerful:
    "rarity": "Uncommon - only strongest stocks",
    "expectation": "Continuation of prior strong move",
    "typical_gain": "Another 50-100%+ possible"
}

# Why Maximum Conviction:
# - Only strongest momentum stocks form HTF
# - Proves extraordinary strength
# - Short consolidation = eager buyers
# - Historical win rate very high on perfect setups
```

## Tier 2: High Conviction Patterns

### 4. Flat Base - O'Neil

**Conviction: Level 3-4**

```python
flat_base = {
    "duration": "5-6 weeks minimum",
    "price_movement": "Sideways trading (10-15% max correction)",
    "volume": "Generally lower during base",
    "breakout": "Volume expansion required",
    "characteristic": "Tight, orderly consolidation"
}
```

### 5. Episodic Pivot (EP) - Qullamaggie

**Conviction: Level 4-5 (if all criteria met)**

```python
episodic_pivot = {
    # Pre-Event
    "lookback": "3-6 months flat/inactive",

    # Catalyst
    "gap": "10%+ gap on news",
    "catalyst_types": ["earnings surprise", "FDA approval", "analyst upgrade"],

    # Volume (CRITICAL)
    "volume_multiplier": "5-10x average daily volume",
    "first_30_min": "Massive volume (ideally ADV in first 15-20 min)",
    "absolute_minimum": "100,000 shares",

    # Float
    "float_ideal": "20-50% (GREEN zone)",
    "float_avoid": "<20% (RED - manipulation risk)",

    # Fundamentals
    "earnings_growth": "50-100%+ YoY (triple digits ideal)",
    "sales_growth": "50-100%+ YoY",

    # Entry
    "entry_timing": "Break of early day high (20-60 min after open)",
    "entry_style": "Full position immediately",

    # Quick Exit Rule
    "if_no_momentum": "Exit within 20 minutes if no acceleration"
}

# Why High Conviction (when perfect):
# - Explosive fundamental catalyst
# - Massive volume = institutional buying
# - Gap shows urgency/FOMO
# - Can produce 50-200%+ gains in days/weeks
```

### 6. Ascending Triangle

**Conviction: Level 3-4**

```python
ascending_triangle = {
    "resistance": "Flat top (horizontal resistance)",
    "support": "Rising lows (higher lows)",
    "duration": "4+ weeks",
    "volume": "Decreasing during triangle, expanding on breakout",
    "breakout": "Above flat resistance on volume",
    "psychology": "Buyers increasingly aggressive"
}
```

### 7. Darvas Box

**Conviction: Level 3-4**

```python
darvas_box = {
    "upper_boundary": "High tested 3+ times but not exceeded",
    "lower_boundary": "Support level established",
    "box_confirmation": "Price oscillates between boundaries",
    "entry": "Close above upper boundary on volume",
    "stop": "Bottom of box (mechanical)",
    "trend_requirement": "Only rising boxes (Stage 2)",
    "new_boxes": "Each box higher than previous"
}
```

## Tier 3: Moderate Conviction Patterns

### 8. Bull Flags

**Conviction: Level 3**

```python
bull_flag = {
    "pole": "Strong momentum move (30%+ in 1-4 weeks)",
    "flag": "Tight 2-4 week consolidation",
    "flag_slope": "Slight downward drift or flat",
    "flag_depth": "10-20% retracement of pole",
    "volume": "Low during flag, expansion on breakout",
    "entry": "Break above flag resistance"
}
```

### 9. Symmetrical Triangles

**Conviction: Level 2-3**

```python
symmetrical_triangle = {
    "pattern": "Lower highs AND higher lows converging",
    "duration": "4+ weeks",
    "breakout_direction": "Can go either way (watch carefully)",
    "volume": "Decreasing as triangle forms",
    "entry": "Confirmed break in either direction with volume",
    "caution": "False breakouts common - wait for confirmation"
}
```

## Pattern Quality Checklist

### Perfect Pattern (Level 5):
- ✅ Clean, textbook formation
- ✅ All criteria met precisely
- ✅ Volume behavior perfect (decrease in pattern, explosion on breakout)
- ✅ Stage 2 confirmed
- ✅ Tight risk (3-5% stop)

### Good Pattern (Level 4):
- ✅ Recognizable formation
- ✅ Most criteria met
- ✅ Volume good (50%+ on breakout)
- ✅ Stage 2 confirmed
- ✅ Moderate risk (5-7% stop)

### Acceptable Pattern (Level 3):
- ⚠️ Pattern present but not perfect
- ⚠️ Core criteria met
- ⚠️ Volume acceptable (40%+ on breakout)
- ⚠️ Stage 2 likely
- ⚠️ Normal risk (7-8% stop)

### Weak Pattern (Level 1-2):
- ❌ Pattern unclear or sloppy
- ❌ Many criteria missing
- ❌ Volume weak
- ❌ Stage questionable
- ❌ Wide stop (8%+)
- **Action: SKIP**

---

# Volume Analysis

## Volume Conviction Levels

### Level 5: EXPLOSIVE VOLUME
```python
volume_multiplier = 2.0  # 100%+ above average (2x+)
characteristics = "Massive institutional buying"
examples = "NVDA breakouts, DUOL IPO follow-through"
conviction_impact = "+2 levels"
```

### Level 4: VERY STRONG VOLUME
```python
volume_multiplier = 1.5  # 50-100% above average
characteristics = "Strong institutional interest"
examples = "Quality O'Neil cup-handle breakouts"
conviction_impact = "+1 level"
```

### Level 3: GOOD VOLUME
```python
volume_multiplier = 1.4  # 40-50% above average
characteristics = "Acceptable confirmation"
examples = "Minimum O'Neil requirement"
conviction_impact = "Neutral (meets minimum)"
```

### Level 2: MARGINAL VOLUME
```python
volume_multiplier = 1.1-1.3  # 10-30% above average
characteristics = "Weak confirmation"
examples = "Questionable breakouts"
conviction_impact = "-1 level (reduce conviction)"
```

### Level 1: LOW VOLUME
```python
volume_multiplier = <1.1  # Below or slightly above average
characteristics = "NO confirmation - likely false breakout"
examples = "Failed breakouts, bull traps"
conviction_impact = "-2 levels (SKIP TRADE)"
```

## Volume Thresholds by Trader

| Trader | Minimum Volume | Ideal Volume | Notes |
|--------|---------------|--------------|-------|
| **O'Neil** | 40% above avg (1.4x) | 100%+ (2x) | Hard minimum 40% |
| **Minervini** | "Explosive" | 100%+ | Decreasing during VCP critical |
| **Zanger** | 50% above 20-day avg | 300% (3x) | Uses 20-day MA baseline |
| **Ryan** | 50%+ | 100%+ | Should be profitable first day |
| **Qullamaggie** | Above average | 5-10x for EP setups | Context-dependent |
| **Stage Analysis** | 2-3x average | 3x+ | Stage 2 breakout requirement |

## Volume Pattern Analysis

### During Pattern Formation:

```python
# VCP (Minervini)
vcp_volume = {
    "pullback_1": "Above average (selling)",
    "pullback_2": "Lower than pullback 1",
    "pullback_3": "Lower than pullback 2",
    "final_pullback": "Lowest volume (dry up)",
    "breakout": "EXPLOSIVE expansion"
}

# Cup-with-Handle (O'Neil)
cup_handle_volume = {
    "cup_formation": "Average to above average",
    "handle_formation": "DECLINING (critical)",
    "handle_low_volume": "Must dry up",
    "breakout": "Minimum 40% expansion, ideal 100%+"
}

# Flag Patterns
flag_volume = {
    "pole": "Very high volume",
    "flag": "Declining volume",
    "breakout": "Volume expansion"
}
```

### Volume + Price Analysis:

```python
# Bullish Combinations (Higher Conviction)
bullish_volume = {
    "price_up_volume_up": "Strong buying (best)",
    "price_up_volume_declining": "Healthy consolidation",
    "breakout_on_volume": "Confirmation (required)"
}

# Bearish Combinations (Lower Conviction)
bearish_volume = {
    "price_up_volume_low": "Weak advance (questionable)",
    "price_down_volume_up": "Distribution (avoid)",
    "breakout_no_volume": "False breakout likely (skip)"
}
```

## Special Volume Situations

### Episodic Pivot (Qullamaggie):
```python
ep_volume = {
    "first_30_minutes": "5-10x average daily volume",
    "ideal": "Entire ADV traded in first 15-20 minutes",
    "absolute_minimum": "100,000 shares",
    "conviction": "Level 5 if 8-10x, Level 4 if 5-7x, Level 3 if 3-5x"
}
```

### New ATH Breakouts:
```python
ath_volume = {
    "requirement": "Above average minimum",
    "ideal": "2x+ average",
    "reasoning": "Less resistance = less volume needed than normal base"
}
```

---

# Relative Strength

## RS Rating Conviction Levels

### Level 5: ELITE (RS 95-99)
```python
rs_characteristics = {
    "percentile": "Top 5% of all stocks",
    "description": "Market leaders, extreme strength",
    "examples": "NVDA 2023, TSLA 2020, SHOP 2016",
    "conviction_bonus": "+1 level if all other criteria met",
    "expected_behavior": "Leads market rallies, outperforms corrections"
}
```

### Level 4: EXCELLENT (RS 90-94)
```python
rs_characteristics = {
    "percentile": "Top 6-10% of stocks",
    "description": "Strong leaders",
    "minervini_requirement": "Minimum for SEPA method",
    "oneil_ideal": "Ideal range for CAN SLIM",
    "conviction": "Full conviction if other criteria met"
}
```

### Level 3: VERY GOOD (RS 85-89)
```python
rs_characteristics = {
    "percentile": "Top 11-15% of stocks",
    "description": "Above average strength",
    "minervini_minimum": "Absolute minimum for consideration",
    "oneil_acceptable": "Acceptable but prefers 90+",
    "conviction": "Moderate to high depending on other factors"
}
```

### Level 2: GOOD (RS 80-84)
```python
rs_characteristics = {
    "percentile": "Top 16-20% of stocks",
    "description": "Good but not great",
    "oneil_minimum": "Minimum acceptable",
    "conviction": "Lower conviction, reduce position size",
    "risk": "May lag in strong markets"
}
```

### Level 1: AVERAGE OR BELOW (RS <80)
```python
rs_characteristics = {
    "percentile": "Below top 20%",
    "description": "Laggards, followers, weak",
    "trader_consensus": "AVOID - all legendary traders skip these",
    "conviction": "Level 1 maximum (typically skip entirely)",
    "risk": "High failure rate, underperformance likely"
}
```

## RS Calculation (IBD Method)

```python
def calculate_rs_rating(stock_data):
    """
    IBD Relative Strength Rating calculation

    Weighted heavily toward recent performance:
    - 40% weight: Last 3 months
    - 20% weight: Each prior quarter (3 quarters)
    """
    recent_3m = stock_data['return_3m'] * 0.40
    quarter_1 = stock_data['return_q1'] * 0.20
    quarter_2 = stock_data['return_q2'] * 0.20
    quarter_3 = stock_data['return_q3'] * 0.20

    weighted_return = recent_3m + quarter_1 + quarter_2 + quarter_3

    # Percentile rank vs all stocks
    rs_rating = percentile_rank(weighted_return, all_stocks)

    return rs_rating  # 1-99 scale
```

## RS Line Analysis

```python
# RS Line = Stock Price / Market Index (S&P 500)
# Rising RS Line = Outperforming market
# Falling RS Line = Underperforming market

rs_line_signals = {
    "new_high_with_price": "Best signal - leading stock",
    "new_high_before_price": "Early strength signal (bullish)",
    "divergence_lower": "Weakness - relative underperformance (bearish)",
    "flat_in_uptrend": "Neutral - matching market (acceptable)",
    "declining": "Avoid - losing to market"
}
```

---

# Entry Timing & Triggers

## Entry Conviction by Type

### Level 5: PERFECT ENTRY
```python
perfect_entry = {
    "timing": "Within first 5% of breakout",
    "pattern": "Clean pivot point break",
    "volume": "Explosive (2x+ average)",
    "intraday": "Opening range high break (1-min, 5-min, 60-min)",
    "confirmation": "Multiple timeframes aligned",
    "stop_width": "Tight (3-5%)",
    "risk_reward": "4:1 to 8:1 minimum"
}
```

### Level 4: EXCELLENT ENTRY
```python
excellent_entry = {
    "timing": "Within 5-10% of breakout",
    "pattern": "Clear breakout point",
    "volume": "Strong (1.5x+ average)",
    "pullback": "OR first pullback to 10/20 MA after breakout",
    "confirmation": "Daily chart confirmed",
    "stop_width": "Moderate (5-7%)",
    "risk_reward": "3:1 to 5:1"
}
```

### Level 3: GOOD ENTRY
```python
good_entry = {
    "timing": "Within 10% of breakout",
    "pattern": "Breakout clear but some extension",
    "volume": "Acceptable (1.4x average)",
    "pullback": "OR pullback to 50 MA after breakout",
    "stop_width": "Normal (7-8%)",
    "risk_reward": "2:1 to 3:1"
}
```

### Level 2: MARGINAL ENTRY (Reduce Size)
```python
marginal_entry = {
    "timing": "10-15% above breakout",
    "pattern": "Extended from ideal entry",
    "volume": "May be fading",
    "risk": "Chasing - vulnerable to pullback",
    "stop_width": "Wider (8-10%)",
    "risk_reward": "1.5:1 to 2:1",
    "action": "Reduce position size by 50% or wait for pullback"
}
```

### Level 1: POOR ENTRY (SKIP)
```python
poor_entry = {
    "timing": ">15% above breakout",
    "pattern": "Extended, late",
    "risk": "High - likely near-term top",
    "stop_width": "Very wide (10%+)",
    "risk_reward": "<1.5:1",
    "action": "DO NOT ENTER - Wait for next setup"
}
```

## Entry Triggers by Timeframe

### Daily Chart Triggers:

```python
daily_triggers = {
    # Conservative
    "conservative": "Close above resistance with volume",

    # Standard
    "standard": "Intraday break above resistance",

    # Aggressive
    "aggressive": "Pre-market gap above resistance",

    # Re-entry
    "reentry": "Pullback to breakout point or key MA"
}
```

### Intraday Triggers (Qullamaggie Method):

```python
# Opening Range Breakout
opening_range_triggers = {
    "1_minute": {
        "timing": "First 1-minute high breaks",
        "conviction": "Level 5 (highest conviction)",
        "risk": "Lowest - earliest entry",
        "stop": "Low of day",
        "usage": "Best setups only"
    },

    "5_minute": {
        "timing": "First 5-minute high breaks",
        "conviction": "Level 4 (high conviction)",
        "risk": "Low - early entry",
        "stop": "Low of day",
        "usage": "Most common for Qullamaggie"
    },

    "60_minute": {
        "timing": "First 60-minute high breaks",
        "conviction": "Level 3 (moderate)",
        "risk": "Moderate - some extension",
        "stop": "Low of day or below 60-min low",
        "usage": "Lower conviction setups"
    },

    "daily": {
        "timing": "Daily chart breakout",
        "conviction": "Level 2-3",
        "risk": "Higher - may be extended intraday",
        "stop": "Below breakout point or key MA",
        "usage": "Longer timeframe traders"
    }
}
```

### Pullback Entries (Lower Risk):

```python
pullback_entries = {
    "first_pullback_10ma": {
        "timing": "After breakout, first touch of 10-day MA",
        "conviction": "Level 4-5 if bounce",
        "volume": "Should be lower on pullback",
        "trigger": "Bounce off MA on increased volume",
        "trader": "Qullamaggie, Minervini"
    },

    "first_pullback_20ma": {
        "timing": "After breakout, first touch of 20-day MA",
        "conviction": "Level 3-4 if bounce",
        "deeper": "Deeper than 10 MA but still healthy",
        "trigger": "Bounce with volume",
        "trader": "O'Neil, Qullamaggie"
    },

    "breakout_point_retest": {
        "timing": "Return to original breakout level",
        "conviction": "Level 3-4 if holds",
        "volume": "Must be lower than breakout volume",
        "trigger": "Hold and bounce",
        "trader": "All traders (second chance entry)"
    },

    "50ma_pullback": {
        "timing": "Deeper pullback to 50-day MA",
        "conviction": "Level 2-3 (depends on context)",
        "caution": "Could signal weakening",
        "trigger": "Strong bounce required",
        "trader": "Longer-term position traders"
    }
}
```

## Entry Checklist

### Before Entry - ALL Must Be TRUE:

```python
entry_checklist = {
    # Stage & Trend
    "stage_2_confirmed": "✅ Weekly and daily",
    "mas_aligned": "✅ Per trader's method",

    # Pattern
    "pattern_identified": "✅ Recognizable setup",
    "pattern_quality": "✅ Meets criteria",

    # Volume
    "volume_confirmation": "✅ Minimum threshold met",

    # RS
    "relative_strength": "✅ RS > 80 minimum (85+ ideal)",

    # Entry Quality
    "entry_timing": "✅ Not extended (within 10% of breakout)",
    "stop_defined": "✅ Clear stop loss level",
    "stop_width": "✅ Acceptable (3-8% range)",

    # Risk/Reward
    "risk_reward_ratio": "✅ Minimum 2:1 (prefer 3:1+)",

    # Liquidity
    "liquidity_tier": "✅ Tier 1-3 (from your screener)",

    # Fundamentals
    "fundamental_score": "✅ 60%+ (from your screener)",

    # Market
    "market_direction": "✅ Uptrend or neutral (not downtrend)"
}

# If ANY item is ❌, reduce conviction by 1 level
# If 3+ items are ❌, SKIP the trade
```

---

# Complete Screening Criteria by Conviction

## Level 5 Screen: MAXIMUM CONVICTION

```python
level_5_criteria = {
    # Stage Analysis
    "stage": "Stage 2 confirmed (weekly + daily)",
    "price_above_30w_ma": True,
    "30w_ma_rising": True,
    "higher_highs_and_lows": True,

    # Minervini Template (ALL 8)
    "price_above_50_150_200_ma": True,
    "50_above_150_above_200": True,
    "200_ma_trending_up_1m": True,
    "price_30pct_above_52w_low": True,
    "price_within_25pct_52w_high": True,
    "rs_rating": ">=90",

    # Pattern
    "pattern_type": ["VCP (final contraction)", "HTF", "Perfect Cup-Handle"],
    "pattern_quality": "Textbook",
    "vcp_contractions": ">=3 with decreasing depth",

    # Volume
    "breakout_volume": ">=100% above average (2x)",
    "volume_during_pattern": "Decreasing (for VCP/Cup)",

    # Relative Strength
    "rs_rating_min": 90,
    "rs_line": "New high with price",

    # Entry
    "entry_distance": "Within 5% of breakout",
    "entry_trigger": "1-min or 5-min OR high break",
    "entry_volume": "Explosive",

    # Stop
    "stop_width": "3-5% maximum",

    # Fundamentals (from your screener)
    "fundamental_score": ">=75% (EXCELLENT tier)",
    "eps_growth": ">=40%",
    "revenue_growth": ">=30%",

    # Liquidity (from your screener)
    "liquidity_tier": "1 or 2 (EXCELLENT or GOOD)",

    # Position Sizing
    "base_risk": "1.5-2.25% (Level 5 conviction × market health)"
}
```

## Level 4 Screen: HIGH CONVICTION

```python
level_4_criteria = {
    # Stage Analysis
    "stage": "Stage 2 confirmed",
    "price_above_30w_ma": True,
    "30w_ma_rising": True,

    # Minervini Template (6-7 of 8)
    "minervini_score": ">=6",
    "price_above_50_ma": True,
    "rs_rating": ">=85",

    # Pattern
    "pattern_type": ["VCP", "Cup-Handle", "HTF", "EP", "Flag"],
    "pattern_quality": "Good to excellent",

    # Volume
    "breakout_volume": ">=50% above average",

    # Relative Strength
    "rs_rating_min": 85,
    "rs_line": "Rising",

    # Entry
    "entry_distance": "Within 5-10% of breakout",

    # Stop
    "stop_width": "5-7%",

    # Fundamentals
    "fundamental_score": ">=60% (QUALITY tier)",
    "eps_growth": ">=25%",
    "revenue_growth": ">=20%",

    # Liquidity
    "liquidity_tier": "1, 2, or 3",

    # Position Sizing
    "base_risk": "1.125-1.875% (Level 4 × market)"
}
```

## Level 3 Screen: MODERATE CONVICTION

```python
level_3_criteria = {
    # Stage Analysis
    "stage": "Stage 2 (may be early or mid)",
    "price_above_50_ma": True,

    # Minervini Template (5-6 of 8)
    "minervini_score": ">=5",
    "rs_rating": ">=80",

    # Pattern
    "pattern_type": ["Flags", "Triangles", "Flat Base", "Darvas Box"],
    "pattern_quality": "Acceptable",

    # Volume
    "breakout_volume": ">=40% above average",

    # Relative Strength
    "rs_rating_min": 80,

    # Entry
    "entry_distance": "Within 10% of breakout",

    # Stop
    "stop_width": "7-8%",

    # Fundamentals
    "fundamental_score": ">=60%",
    "eps_growth": ">=20%",

    # Liquidity
    "liquidity_tier": "1, 2, or 3",

    # Position Sizing
    "base_risk": "0.75-1.5% (Level 3 × market)"
}
```

## Level 2 Screen: LOW CONVICTION (Speculative)

```python
level_2_criteria = {
    # Stage Analysis
    "stage": "Stage 2 questionable",
    "price_above_50_ma": "Preferred",

    # Minervini Template (4-5 of 8)
    "minervini_score": ">=4",
    "rs_rating": ">=70",

    # Pattern
    "pattern_quality": "Marginal",

    # Volume
    "breakout_volume": ">=20% above average",

    # Entry
    "entry_distance": "10-15% above breakout",

    # Stop
    "stop_width": "8-10%",

    # Fundamentals
    "fundamental_score": ">=50%",

    # Position Sizing
    "base_risk": "0.5625-1.125% (Level 2 × market)",

    # Action
    "recommendation": "Small positions only OR wait for better setup"
}
```

## Level 1 Screen: MINIMAL (AVOID)

```python
level_1_criteria = {
    # Characteristics
    "stage": "Unclear or Stage 3",
    "pattern": "Weak or absent",
    "volume": "Low",
    "rs_rating": "<70",

    # Action
    "recommendation": "SKIP - Do not trade",
    "reasoning": "High failure rate, poor risk/reward"
}
```

---

# Quick Reference: Conviction Assignment

## Conviction Calculator

```python
def calculate_conviction(stock):
    """
    Quick conviction level calculator
    Returns: 1-5 conviction level
    """
    score = 0

    # Stage Analysis (0-2 points)
    if all_8_minervini_criteria_met():
        score += 2
    elif 6_to_7_criteria_met():
        score += 1.5
    elif 5_to_6_criteria_met():
        score += 1
    else:
        score += 0  # SKIP if <5

    # Pattern Quality (0-2 points)
    if pattern_type in ["VCP final", "HTF", "Perfect C&H"]:
        score += 2
    elif pattern_type in ["VCP", "C&H", "EP", "Flag"]:
        score += 1.5
    elif pattern_type in ["Flat Base", "Triangle", "Box"]:
        score += 1
    else:
        score += 0

    # Volume (0-1 points)
    if breakout_volume >= 2.0:  # 100%+
        score += 1
    elif breakout_volume >= 1.5:  # 50%+
        score += 0.75
    elif breakout_volume >= 1.4:  # 40%+
        score += 0.5
    else:
        score += 0

    # RS Rating (0-1 points)
    if rs_rating >= 90:
        score += 1
    elif rs_rating >= 85:
        score += 0.75
    elif rs_rating >= 80:
        score += 0.5
    else:
        score += 0

    # Entry Quality (0-1 points)
    if entry_distance <= 5:  # Within 5%
        score += 1
    elif entry_distance <= 10:  # 5-10%
        score += 0.5
    else:
        score += 0

    # Convert to Conviction Level
    # 6-7 points = Level 5
    # 5-5.99 = Level 4
    # 4-4.99 = Level 3
    # 3-3.99 = Level 2
    # <3 = Level 1 (Skip)

    if score >= 6:
        return 5
    elif score >= 5:
        return 4
    elif score >= 4:
        return 3
    elif score >= 3:
        return 2
    else:
        return 1
```

---

# Summary: Building Your Technical Screener

## Recommended Approach

### Phase 1: Filter for Stage 2 Only
- Eliminate 70-80% of stocks immediately
- Only Stage 2 = buyable

### Phase 2: Apply Pattern Recognition
- Identify VCP, Cup-Handle, HTF, EP, Flags
- Score pattern quality

### Phase 3: Volume Confirmation
- Minimum 40% above average (Level 3)
- Ideal 50-100%+ (Level 4-5)

### Phase 4: RS Filter
- Minimum RS 80
- Ideal RS 85+
- Best RS 90+

### Phase 5: Entry Timing
- Calculate distance from breakout
- Score 1-5 based on extension

### Phase 6: Calculate Conviction
- Use formula above
- Assign 1-5 level

### Phase 7: Integrate with Existing Screeners
- Cross-reference liquidity tier (yours)
- Cross-reference fundamental score (yours)
- Final conviction = Technical × Fundamental × Liquidity

---

## Integration with Your Existing System

```python
final_conviction_formula = {
    # Your Current Screeners
    "liquidity_tier": "1-5 (from liquidity_screener.py)",
    "fundamental_score": "0-150 (from fundamental_screener.py)",

    # New Technical Screener
    "technical_conviction": "1-5 (from this document)",

    # Combined Score
    "final_trade_rating": """
        IF liquidity_tier in [1,2,3]:
            IF fundamental_score >= 90 (60%):
                IF technical_conviction >= 4:
                    TRADE = "Level 5 - Maximum conviction"
                ELIF technical_conviction == 3:
                    TRADE = "Level 4 - High conviction"
                ELIF technical_conviction == 2:
                    TRADE = "Level 3 - Moderate conviction"
                ELSE:
                    TRADE = "Skip - weak technical setup"
            ELIF fundamental_score >= 75:
                # Reduce 1 level
            ELSE:
                TRADE = "Skip - weak fundamentals"
        ELSE:
            TRADE = "Skip - illiquid"
    """
}
```

This gives you a complete framework to assign conviction levels based on technical criteria that can be integrated with your existing liquidity and fundamental screeners!
