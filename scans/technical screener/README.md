# Technical Screener - 5-Level Conviction System

## Overview

The Technical Screener analyzes liquid stocks (from `liquidity_screener.py`) and assigns conviction levels 1-5 based on technical criteria. This is designed to be run **daily** to identify high-probability setups.

**Integration:**
- **Input**: Uses TRADEABLE stocks from liquidity screener (Tier 1-3)
- **Output**: Stocks scored 1-5 by technical conviction
- **Frequency**: Daily (unlike liquidity/fundamental which run weekly/monthly)
- **Results**: Saved monthly in `results_YYYY-MM/` folders

---

## Conviction Levels

### Level 5: MAXIMUM CONVICTION (80%+ score)
**Characteristics:**
- Perfect technical setup
- All criteria aligned
- RS Rating 90+
- Explosive volume (2x average)
- 50%+ gain in 3 months
- All moving averages perfectly aligned
- Near 52-week highs
- Breakout confirmed

**Expected Win Rate:** 40-50%
**Expected R:R:** 4:1 to 8:1
**Position Size:** Maximum (2.0-2.25% risk with 5LC multipliers)

### Level 4: HIGH CONVICTION (65-79% score)
**Characteristics:**
- Strong technical setup
- Most criteria met
- RS Rating 85+
- Strong volume (1.5x average)
- 40%+ gain in 3 months
- Good MA alignment
- Within 25% of 52-week high

**Expected Win Rate:** 35-45%
**Expected R:R:** 3:1 to 5:1
**Position Size:** High (1.5-1.875% risk)

### Level 3: MODERATE CONVICTION (50-64% score)
**Characteristics:**
- Solid technical setup
- Core criteria met
- RS Rating 80+
- Good volume (1.4x average)
- 30%+ gain in 3 months (your minimum)
- Acceptable MA alignment

**Expected Win Rate:** 30-40%
**Expected R:R:** 2:1 to 3:1
**Position Size:** Moderate (1.0-1.5% risk)

### Level 2: LOW CONVICTION (35-49% score)
**Characteristics:**
- Weak setup
- Minimal criteria met
- Consider smaller size or skip

**Position Size:** Small (0.5-1.125% risk) or wait for better setup

### Level 1: MINIMAL CONVICTION (<35% score)
**Characteristics:**
- Very weak setup
- **Action: SKIP**

---

## Screening Criteria (Adjustable)

All criteria can be modified in the `self.criteria` dictionary at the top of `technical_screener.py`.

### Base Requirements (Your Specifications)

```python
# YOUR REQUIREMENTS
volume_spike: 1.4x+ average (40%+)  # Volume up
rs_rating: 80+                      # RS over 80
gain_3m: 30%+                       # Stock up 30%+ in 3 months
min_price: $5+                      # Avoid penny stocks
```

### Additional Criteria (Built In)

#### 1. Volume Analysis (15 points)
```python
'volume': {
    'min_avg_volume': 100000,           # Min daily volume
    'recent_period': 20,                # Days for average
    'volume_spike_excellent': 2.0,      # 100%+ = 15 pts
    'volume_spike_good': 1.5,           # 50%+ = 12 pts
    'volume_spike_pass': 1.4,           # 40%+ = 9 pts (O'Neil minimum)
}
```

#### 2. Relative Strength (20 points)
```python
'relative_strength': {
    'rs_excellent': 90,  # Top 10% = 20 pts
    'rs_good': 85,       # Top 15% = 17 pts
    'rs_pass': 80,       # Top 20% = 14 pts (your minimum)
    'rs_minimum': 70,    # Below = skip
}
```

#### 3. Price Performance (15 points)
```python
'price_performance': {
    'period_days': 63,           # ~3 months
    'gain_excellent': 50,        # 50%+ = 15 pts
    'gain_good': 40,             # 40%+ = 13 pts
    'gain_pass': 30,             # 30%+ = 11 pts (your minimum)
    'gain_minimum': 20,          # 20%+ = 8 pts
}
```

#### 4. Moving Average Alignment (25 points - Minervini Template)
```python
'moving_averages': {
    'ma_10': 10,
    'ma_20': 20,
    'ma_50': 50,
    'ma_150': 150,
    'ma_200': 200,
    'use_minervini_template': True,  # 8-point trend template
}

# Checks (8 total):
# 1. Price > 150 MA AND Price > 200 MA
# 2. 150 MA > 200 MA
# 3. 200 MA trending up
# 4. 50 MA > 150 MA AND 50 MA > 200 MA
# 5. Price > 50 MA
# 6. Price > all short-term MAs (10, 20, 50)
# 7. Price > 20 MA and 50 MA
# 8. MA alignment (10 > 20 > 50)

# Score: 25 points × (checks_met / 8)
```

#### 5. 52-Week Position (10 points)
```python
'52_week': {
    'min_from_low': 30,       # Min 30% above 52-week low (Minervini)
    'max_from_high': 25,      # Within 25% of 52-week high (Minervini)
    'new_high_bonus': True,   # Bonus for new highs
}

# Scoring:
# - Within 5% of high: +5 pts
# - Within 25% of high: +4 pts
# - 50%+ above low: +5 pts
# - 30%+ above low: +4 pts
```

#### 6. Trend Quality (10 points)
```python
# Analyzes:
# - Consecutive up days (3+ days = 4 pts)
# - Higher highs (3 pts)
# - Higher lows (3 pts)
```

#### 7. Breakout Bonus (5 points)
```python
'patterns': {
    'detect_breakout': True,
    'breakout_lookback': 20,  # 20-day high breakout
}

# +5 points if breaking 20-day high on volume
```

#### 8. ATR Filter (Volatility)
```python
'atr': {
    'period': 14,
    'calculate': True,
    'max_atr_percent': 15,  # Skip if ATR > 15% (too volatile)
}
```

---

## Scoring System

### Total Points: 100

| Criterion | Max Points | Weight |
|-----------|------------|--------|
| Volume | 15 | 15% |
| **Relative Strength** | **20** | **20% (Most Important)** |
| Price Performance | 15 | 15% |
| **Moving Averages** | **25** | **25% (Minervini Template)** |
| 52-Week Position | 10 | 10% |
| Trend Quality | 10 | 10% |
| Breakout Bonus | 5 | 5% |

### Conviction Thresholds

| Level | Score | Name | Action |
|-------|-------|------|--------|
| 5 | 80-100 | MAXIMUM | Full position, tight stop |
| 4 | 65-79 | HIGH | Strong position |
| 3 | 50-64 | MODERATE | Standard position |
| 2 | 35-49 | LOW | Small or skip |
| 1 | 0-34 | MINIMAL | Skip |

---

## Output Files

### Monthly Results Folder: `results_YYYY-MM/`

Each run creates timestamped files:

1. **`technical_screen_YYYYMMDD_HHMMSS_FULL.csv`**
   - All stocks that passed base criteria
   - All conviction levels included

2. **`technical_screen_YYYYMMDD_HHMMSS_LEVEL5_MAXIMUM.csv`**
   - Only Level 5 stocks (80%+ score)
   - Highest conviction setups

3. **`technical_screen_YYYYMMDD_HHMMSS_LEVEL4_HIGH.csv`**
   - Only Level 4 stocks (65-79% score)
   - High conviction setups

4. **`technical_screen_YYYYMMDD_HHMMSS_LEVEL3_MODERATE.csv`**
   - Only Level 3 stocks (50-64% score)
   - Moderate conviction setups

5. **`technical_screen_YYYYMMDD_HHMMSS_TOP_CANDIDATES.csv`**
   - Combined Level 4 & 5 stocks
   - Your trading watchlist

### CSV Columns

| Column | Description |
|--------|-------------|
| symbol | Stock ticker |
| conviction_level | 1-5 conviction rating |
| total_score | Score out of 100 |
| price | Current price |
| gain_3m_pct | 3-month gain % |
| rs_rating | Relative Strength 1-99 |
| volume_ratio | Recent volume / avg volume |
| avg_volume | 20-day average volume |
| ma_10, ma_20, ma_50, ma_150, ma_200 | Moving averages |
| high_52w, low_52w | 52-week high/low |
| pct_from_high | % below 52-week high |
| pct_from_low | % above 52-week low |
| atr | Average True Range |
| atr_percent | ATR as % of price |
| consecutive_up_days | Recent up days |
| higher_highs, higher_lows | Trend direction |
| is_breakout | Breaking 20-day high |
| liquidity_tier | From liquidity screener |

---

## Usage

### Daily Workflow

1. **Run Liquidity Screener** (weekly/monthly):
   ```bash
   cd scans
   python "liquidity screener/liquidity_screener.py"
   ```

2. **Run Fundamental Screener** (weekly/monthly):
   ```bash
   cd scans
   python fundamentals/fundamental_screener.py
   ```

3. **Run Technical Screener** (daily):
   ```bash
   cd scans
   python "technical screener/technical_screener.py"
   ```

### What to Look For

**Best Setups (Level 4-5):**
- Open `technical_screen_*_TOP_CANDIDATES.csv`
- Focus on stocks with:
  - conviction_level = 4 or 5
  - liquidity_tier = "TIER 1" or "TIER 2"
  - is_breakout = True (bonus)
  - pct_from_high < 10 (near highs)

**Chart Confirmation:**
- Pull up chart for each candidate
- Look for VCP, Cup-with-Handle, Flag patterns
- Confirm volume spike on breakout
- Check MA alignment visually

**Fundamental Cross-Check:**
- Compare with fundamental screener results
- Stocks in BOTH technical (Level 4-5) AND fundamental (60%+) are best
- Triple confirmation: Liquid + Strong Fundamentals + Technical Setup

---

## Customization Guide

### Adjusting Criteria (Easy)

Open `technical_screener.py` and modify the `self.criteria` dictionary:

```python
# Example: Raise RS requirement to 85
'relative_strength': {
    'rs_pass': 85,  # Changed from 80
}

# Example: Require 40% 3-month gain instead of 30%
'price_performance': {
    'gain_pass': 40,  # Changed from 30
}

# Example: Require 2x volume instead of 1.4x
'volume': {
    'volume_spike_pass': 2.0,  # Changed from 1.4
}
```

### Adjusting Scoring Weights

Modify the `self.scoring` dictionary:

```python
# Example: Make RS even more important
self.scoring = {
    'volume': 10,              # Reduced from 15
    'relative_strength': 30,    # Increased from 20
    'price_performance': 15,
    'moving_averages': 25,
    '52_week_position': 10,
    'trend_quality': 5,         # Reduced from 10
    'breakout_setup': 5,
}
```

### Adjusting Conviction Thresholds

Modify the `self.conviction_levels` dictionary:

```python
# Example: Make Level 5 harder to achieve
self.conviction_levels = {
    5: 85,  # Changed from 80 (now need 85%+ score)
    4: 70,  # Changed from 65
    3: 55,  # Changed from 50
    2: 40,  # Changed from 35
    1: 0,
}
```

---

## Integration with 5LC System

### Position Sizing Formula

```python
# From your 5LC system
base_risk = 1.5%  # Base risk per trade

# Technical conviction multiplier
tech_multipliers = {
    5: 1.5,   # Level 5 = 1.5x base
    4: 1.25,  # Level 4 = 1.25x base
    3: 1.0,   # Level 3 = 1.0x base
    2: 0.75,  # Level 2 = 0.75x base
    1: 0.5,   # Level 1 = 0.5x base (or skip)
}

# Market health multiplier (from 5LC)
market_multipliers = {
    'bull': 2.0,
    'uptrend': 1.5,
    'neutral': 1.0,
    'downtrend': 0.75,
    'bear': 0.5,
}

# Final position risk
final_risk = base_risk × tech_multiplier × market_multiplier

# Example: Level 5 stock in uptrend
# 1.5% × 1.5 × 1.5 = 3.375% risk per trade
```

### Combined Scoring Matrix

| Liquidity | Fundamental | Technical | Final Conviction | Action |
|-----------|-------------|-----------|------------------|--------|
| Tier 1-2 | 75%+ | Level 5 | **LEVEL 5** | Maximum size |
| Tier 1-2 | 60%+ | Level 4 | **LEVEL 4** | Strong size |
| Tier 1-3 | 60%+ | Level 3 | **LEVEL 3** | Standard size |
| Tier 1-3 | <60% | Level 4-5 | **LEVEL 2-3** | Reduced (weak fundamentals) |
| Tier 4-5 | Any | Any | **SKIP** | Illiquid |
| Any | <60% | <3 | **SKIP** | Too weak |

---

## Performance Tracking

### Recommended Metrics to Track

After running the screener daily, track:

1. **Hit Rate by Conviction Level**
   - How often do Level 5 stocks work out?
   - Adjust thresholds if win rate too low/high

2. **Average Gain by Level**
   - Level 5 should produce largest gains
   - If not, scoring may need adjustment

3. **False Breakouts**
   - Track stocks with `is_breakout = True` that fail
   - May need to raise volume requirement

4. **Optimal Entry Timing**
   - Track how far stocks run before you enter
   - Use `pct_from_high` to avoid chasing

### Monthly Review

At month end:
1. Review all files in `results_YYYY-MM/`
2. Identify which criteria worked best
3. Adjust thresholds in `self.criteria`
4. Re-run historical months to backtest changes

---

## Tips for Daily Use

1. **Run After Market Close**
   - Gets complete daily data
   - No intraday volatility

2. **Focus on New Entries**
   - Compare today's results with yesterday's
   - Look for stocks newly appearing in Level 4-5
   - These are fresh setups

3. **Watch for Upgrades**
   - Stock moving from Level 3 → Level 4 = gaining momentum
   - Stock moving from Level 4 → Level 5 = perfect setup forming

4. **Check Multiple Days**
   - Stock showing Level 4-5 for 2-3 days = more reliable
   - One-day spike may be false signal

5. **Volume Confirmation**
   - On entry day, verify volume spike holds
   - Use `volume_ratio` column

6. **Breakout Timing**
   - `is_breakout = True` = breaking out NOW
   - These are immediate entry candidates
   - Set alerts or buy at open next day

---

## Troubleshooting

### "No stocks passed the screen"

**Possible causes:**
- Criteria too strict (lower thresholds)
- Market in downtrend (few stocks meet 30% gain + RS 80)
- Liquidity screener hasn't run (no input data)

**Solutions:**
- Lower `gain_pass` from 30% to 20%
- Lower `rs_pass` from 80 to 75
- Check that liquidity screener has recent data

### "All stocks are Level 1-2"

**Possible causes:**
- Scoring too harsh
- Conviction thresholds too high

**Solutions:**
- Lower conviction thresholds:
  ```python
  self.conviction_levels = {
      5: 75,  # From 80
      4: 60,  # From 65
      3: 45,  # From 50
  }
  ```

### "Takes too long to run"

**Optimizations:**
- Reduce rate limiting: Change `time.sleep(0.1)` to `0.05`
- Filter liquid stocks to Tier 1-2 only
- Run on smaller subset for testing

---

## Next Steps

### Phase 2: Risk Management Integration

After validating technical screener:
1. Add ATR-based position sizing
2. Calculate stop loss levels
3. Calculate profit targets (ATR multiples)
4. Add risk/reward ratios
5. Integrate with 5LC conviction multipliers

### Phase 3: Pattern Recognition

Add specific pattern detection:
- VCP (Volatility Contraction Pattern)
- Cup-with-Handle
- High Tight Flag
- Episodic Pivot
- Flags and triangles

### Phase 4: Alerting System

- Email/SMS alerts for Level 5 setups
- Daily summary reports
- Watchlist management

---

## Version History

**v1.0 - 2026-01-02**
- Initial release
- 5-level conviction system
- Base criteria: Volume, RS, 3-month gain
- Minervini MA template
- 52-week positioning
- Breakout detection
- Monthly result folders

---

## Support

For questions or issues:
1. Check criteria settings in `technical_screener.py`
2. Review README troubleshooting section
3. Verify input data from liquidity screener exists
4. Check logs for specific error messages

---

**Remember:** This is a DRAFT system. Adjust criteria based on your testing and results. The goal is to find what works best for YOUR trading style and market conditions.

Run daily. Review weekly. Adjust monthly. Profit consistently.
