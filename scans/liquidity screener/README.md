# Liquidity Screener for $2M Account

## Overview

The Liquidity Screener analyzes stocks to ensure they have adequate liquidity for a $2M trading account with position sizes ranging from $200K to $800K. Getting "stuck" in an illiquid position can be catastrophic - this tool prevents that.

## Position Sizing Context

Based on your 5LC (5-Level Conviction) strategy:
- **Account Size**: $2,000,000
- **Position Sizes**: 10-40% of account ($200K-$800K)
- **Market Health Multiplier**: 0.5x-2.0x (weak to strong markets)
- **Actual Range**: $100K-$1.6M per position

**The Core Problem**: If your $400K position represents 5%+ of a stock's daily dollar volume, you can't exit efficiently without severe slippage (potentially 2-5%+ losses just from market impact).

## The Golden Rule

```
Your Position Size should be ≤ 1-2% of Average Daily Dollar Volume (DDV)
```

**Why?**
- **Entry**: Can accumulate position without driving price up
- **Exit**: Can liquidate in 1-3 days without major market impact
- **Emergency Exit**: Can exit in 1 day if needed (with acceptable slippage)

## Screening Methodology

### 5 Key Liquidity Metrics (Weighted Scoring 0-100)

#### 1. Daily Dollar Volume (35% Weight) - Most Important
```
DDV = Average Volume × Stock Price
```

**Scoring**:
- **100 pts**: DDV ≥ $100M (Excellent - can take max positions)
- **75 pts**: DDV = $40-100M (Good - can take full positions)
- **50 pts**: DDV = $20-40M (Adequate - reduce position 25-50%)
- **25 pts**: DDV = $10-20M (Marginal - small positions only)
- **0 pts**: DDV < $10M (Poor - avoid)

**For Your Account**:
- **$800K position** needs: $80M+ DDV (1% rule) or $160M+ DDV (0.5% rule)
- **$400K position** needs: $40M+ DDV (1% rule) or $80M+ DDV (0.5% rule)
- **$200K position** needs: $20M+ DDV (1% rule) or $40M+ DDV (0.5% rule)

#### 2. Bid-Ask Spread (25% Weight) - Transaction Cost
```
Spread % = ((Ask - Bid) / Ask) × 100%
```

**Scoring** (lower = better):
- **100 pts**: Spread < 0.05% (Excellent - minimal cost)
- **90 pts**: Spread 0.05-0.10% (Very good)
- **70 pts**: Spread 0.10-0.25% (Good)
- **40 pts**: Spread 0.25-0.50% (Acceptable)
- **0 pts**: Spread > 1.00% (Avoid - too expensive)

**Impact**: 1% spread on $400K position = $4,000 immediate cost

#### 3. Turnover Ratio (20% Weight) - Trading Activity
```
Turnover % = (Daily Volume / Shares Outstanding) × 100%
```

**Scoring**:
- **100 pts**: Turnover > 3% (Excellent - very active)
- **80 pts**: Turnover 2-3% (Good)
- **60 pts**: Turnover 1-2% (Adequate)
- **40 pts**: Turnover 0.5-1% (Marginal)
- **0 pts**: Turnover < 0.25% (Poor - illiquid)

**Interpretation**: Higher turnover = more liquidity = easier to trade

#### 4. Float Size (15% Weight) - Available Shares
```
Float = Shares Outstanding - Restricted Shares - Insider Holdings
```

**Scoring**:
- **100 pts**: Float > 100M shares (Excellent - institutional grade)
- **80 pts**: Float 50-100M shares (Good)
- **60 pts**: Float 25-50M shares (Adequate)
- **40 pts**: Float 10-25M shares (Marginal)
- **0 pts**: Float < 5M shares (Avoid - too volatile)

**Note**: William O'Neil prefers LOW float (<20M) for explosive moves, but larger accounts need higher float for liquidity.

#### 5. Market Cap (10% Weight) - Company Size
```
Market Cap = Share Price × Shares Outstanding
```

**Scoring**:
- **100 pts**: Market Cap > $10B (Mega-cap)
- **90 pts**: Market Cap $5-10B (Large-cap)
- **80 pts**: Market Cap $1-5B (Mid-cap) ← **Sweet spot**
- **60 pts**: Market Cap $500M-$1B (Small-cap)
- **0 pts**: Market Cap < $100M (Avoid - too risky)

**Sweet Spot**: $1-10B provides both growth potential AND adequate liquidity

### Hard Filters (Automatic Rejection)

Stocks are automatically rejected if they fail any of these:
```python
Daily Dollar Volume < $20M        # Can't trade $400K+ positions
Average Volume < 500,000 shares   # Insufficient volume
Market Cap < $500M                # Too small, too risky
Stock Price < $10                 # Penny stock territory
Bid-Ask Spread > 0.50%            # Too expensive to trade
Float < 25M shares                # Insufficient liquidity
Not on NYSE/NASDAQ                # OTC = illiquid
```

## Liquidity Tiers

### TIER 1 - EXCELLENT ✅
- **Liquidity Score**: 90-100
- **DDV**: $100M+
- **Max Position**: $800K (full size)
- **Exit Time**: Can exit in < 1 day
- **Examples**: AAPL, MSFT, NVDA, large-cap leaders

### TIER 2 - GOOD ✅
- **Liquidity Score**: 70-89
- **DDV**: $50-100M
- **Max Position**: $600K-$800K
- **Exit Time**: Can exit in 1-2 days
- **Examples**: Mid-to-large caps, active stocks

### TIER 3 - ADEQUATE ⚠️
- **Liquidity Score**: 50-69
- **DDV**: $20-50M
- **Max Position**: $300K-$400K (reduce 25-50%)
- **Exit Time**: Plan for 2-3 day exit
- **Examples**: Smaller mid-caps, less active stocks

### TIER 4 - MARGINAL ⚠️
- **Liquidity Score**: 30-49
- **DDV**: $10-20M
- **Max Position**: $100K-$200K maximum
- **Exit Time**: Plan for 3-5 day exit
- **Warning**: Special situations only, high risk

### TIER 5 - POOR ❌
- **Liquidity Score**: 0-29
- **DDV**: < $10M
- **Max Position**: AVOID or < $100K only
- **Exit Time**: 5-10+ days (getting stuck)
- **Action**: Do not trade

## Exit Strategy Planning

### Days to Liquidate Calculation
```
Days to Liquidate = Your Position Size / Daily Dollar Volume
```

**Targets**:
- **< 0.5 days**: Excellent (can exit in half a day)
- **0.5-1 days**: Good (can exit in 1 day)
- **1-2 days**: Adequate (can exit in 2 days)
- **2-5 days**: Marginal (requires 3-5 days)
- **> 5 days**: Poor (AVOID - getting stuck)

### Emergency Exit (1-Day Liquidation)

**Requirements**:
- Position ≤ 1% of DDV (conservative)
- Position ≤ 2% of DDV (moderate, expect 0.5-1% slippage)
- Position ≤ 3% of DDV (aggressive, expect 1-2% slippage)

**Execution Strategy**:
1. Split into 5-10 limit orders throughout the day
2. Trade during peak volume hours (10 AM - 3 PM ET)
3. Use VWAP algorithm to minimize impact
4. Accept 0.5-1.5% slippage in emergency

### Normal Exit (3-5 Days)

**When to Use**:
- Non-emergency situations
- Larger positions (2-3% of ADV)
- Optimizing exit price

**Execution Strategy**:
- Day 1: Sell 15-20% (test market reaction)
- Day 2-3: Sell 30-40% each day (main distribution)
- Day 4-5: Sell remaining 10-30% (cleanup)

## Slippage Expectations

| Position as % of ADV | Expected Slippage | Example |
|----------------------|-------------------|---------|
| < 0.1% | 0.05-0.10% | $80K in $80M DDV ✅ |
| 0.1-0.5% | 0.10-0.25% | $400K in $80M DDV ✅ |
| 0.5-1% | 0.25-0.40% | $400K in $40M DDV ⚠️ |
| 1-2% | 0.40-0.75% | $400K in $20M DDV ⚠️ |
| 2-5% | 0.75-2% | $400K in $10M DDV ❌ |
| > 5% | 2%+ | $400K in $8M DDV ❌ AVOID |

**Cost Example**:
- $400K position with 1% slippage = $4,000 cost
- $800K position with 1.5% slippage = $12,000 cost

## Usage

### Prerequisites
1. Download stock symbols first:
   ```bash
   cd scans
   python download_the_csv.py
   ```
   This creates a `downloads_YYYY-MM-DD` folder with symbol lists.

### Running the Screener
```bash
cd scans
python "liquidity screener/liquidity_screener.py"
```

The screener will:
1. Automatically find the most recent downloads folder
2. Load all symbols (ASX300, IVV, IJH, IJR)
3. Fetch real-time data from Yahoo Finance
4. Calculate liquidity metrics and scores
5. Save results to CSV files

### Output Files

The screener generates 3 CSV files in the **download folder** (e.g., `downloads_2025-12-27/`):

#### 1. `liquidity_screen_YYYYMMDD_HHMMSS_FULL.csv`
- **All stocks** that passed hard filters
- Sorted by liquidity score (highest to lowest)
- Use for comprehensive analysis

**Columns**:
- `symbol`: Stock ticker
- `source`: Data source (IVV, IJH, IJR, ASX300)
- `price`: Current stock price
- `avg_volume`: 3-month average daily volume (shares)
- `ddv`: Daily Dollar Volume (volume × price)
- `spread_pct`: Bid-ask spread percentage
- `turnover_pct`: Daily volume as % of shares outstanding
- `float_shares`: Available float
- `market_cap`: Total market capitalization
- `liquidity_score`: Overall score (0-100)
- `liquidity_tier`: Tier classification (1-5)
- `max_position_rec`: Recommended maximum position size
- `position_200k_pct_adv`: $200K as % of daily volume
- `position_400k_pct_adv`: $400K as % of daily volume
- `position_800k_pct_adv`: $800K as % of daily volume
- `days_to_liquidate_400k`: Days needed to exit $400K position
- `ddv_score`: DDV component score (0-100)
- `spread_score`: Spread component score (0-100)
- `turnover_score`: Turnover component score (0-100)
- `float_score`: Float component score (0-100)
- `market_cap_score`: Market cap component score (0-100)
- `exchange`: Stock exchange
- `currency`: Trading currency

#### 2. `liquidity_screen_YYYYMMDD_HHMMSS_EXCELLENT.csv`
- **Tier 1 & 2 only** (Excellent and Good liquidity)
- Best candidates for full position sizes
- Safe for $600K-$800K positions

#### 3. `liquidity_screen_YYYYMMDD_HHMMSS_TRADEABLE.csv`
- **Tier 1, 2, & 3** (Excellent, Good, Adequate)
- All stocks suitable for trading
- May need position size adjustments for Tier 3

### Console Output

The screener prints:
- Progress updates every 50 symbols
- Tier distribution statistics
- Liquidity score statistics (mean, median, min, max)
- Daily Dollar Volume statistics
- Top 10 stocks by liquidity score

## Integration with 5LC Strategy

### Recommended Workflow

1. **Run liquidity screener** → Get universe of liquid stocks
2. **Run fundamental screener** → Filter for quality (60%+ fundamental score)
3. **Run technical screener** → Filter for timing (60+ trend strength)
4. **Generate conviction signals** → Score 0-100, convert to levels 1-5
5. **Apply position sizing** → Base size × market health × liquidity adjustment

### Position Size Adjustment Formula

```python
# Base position from conviction level
base_position = {
    1: $200K,   # 10%
    2: $250K,   # 12.5%
    3: $300K,   # 15%
    4: $350K,   # 17.5%
    5: $400K    # 20%
}

# Apply market health multiplier (0.5x-2.0x)
adjusted_position = base_position × market_health_multiplier

# Apply liquidity adjustment
if liquidity_tier == "TIER 1":
    final_position = adjusted_position  # Full size
elif liquidity_tier == "TIER 2":
    final_position = adjusted_position  # Full size
elif liquidity_tier == "TIER 3":
    final_position = adjusted_position × 0.75  # Reduce 25%
elif liquidity_tier == "TIER 4":
    final_position = min(adjusted_position × 0.5, 200_000)  # Max $200K
else:
    final_position = 0  # AVOID
```

### Filtering in 5LC Scanner

Add liquidity filter to your 5LC daily scanner:

```python
# After fundamental and technical screening, before position sizing
liquidity_results = pd.read_csv('downloads_2025-12-27/liquidity_screen_LATEST_TRADEABLE.csv')

# Filter to only trade stocks in Tier 1-3
liquid_symbols = liquidity_results[
    liquidity_results['liquidity_tier'].isin([
        'TIER 1 - EXCELLENT',
        'TIER 2 - GOOD',
        'TIER 3 - ADEQUATE'
    ])
]['symbol'].tolist()

# Apply filter
signals = signals[signals['symbol'].isin(liquid_symbols)]
```

## Red Flags to Avoid

### Critical Warning Signs ❌
- Daily dollar volume < $5M
- Average volume < 50,000 shares
- Market cap < $50M (micro-cap)
- Bid-ask spread > 1%
- Float < 10M shares
- Stock price < $5 (penny stock)
- Not listed on NYSE/NASDAQ (OTC markets)

### Additional Warning Signs ⚠️
- Inconsistent volume (10K some days, 500K others)
- Volume concentrated in few large prints
- Insider ownership > 70% (limited float)
- Single institution owns > 30%
- No institutional ownership at all
- Declining volume trend over 6+ months
- Recent regulatory halts or issues

## Comparison: O'Neil vs Institutional Standards

### William O'Neil (CAN SLIM)
```
Focus: Emerging growth stocks with explosive potential
Volume: 400K+ shares/day
Float: < 20M shares (LOW float for big moves)
Market Cap: Not primary concern
Philosophy: Small float = explosive moves
Best For: Smaller accounts, aggressive growth traders
```

### Institutional / Your $2M Account
```
Focus: Growth stocks with adequate liquidity
DDV: $20M+ ($40M+ preferred)
Float: 25-50M+ shares (adequate liquidity)
Market Cap: $500M+ ($1B+ preferred)
Philosophy: Adequate liquidity = can exit when needed
Best For: Larger accounts that need to exit efficiently
```

**Key Difference**: O'Neil targets low-float stocks for explosive potential (works for smaller accounts), while larger accounts need higher float for liquidity. You're in the middle - need both growth potential AND the ability to get out.

## Performance Benchmarks

### Expected Pass Rates
- **Total universe**: ~1,800 stocks (ASX300 + S&P 500 + Mid-Cap + Small-Cap)
- **Hard filter pass**: ~60-70% (1,100-1,300 stocks)
- **Tier 1 (Excellent)**: ~10-15% of total (180-270 stocks)
- **Tier 2 (Good)**: ~15-20% of total (270-360 stocks)
- **Tier 3 (Adequate)**: ~20-25% of total (360-450 stocks)
- **Tier 1-3 (Tradeable)**: ~45-60% of total (800-1,100 stocks)

### Typical Results
- Large caps (S&P 500): Mostly Tier 1-2 (excellent liquidity)
- Mid caps (S&P 400): Mostly Tier 2-3 (good to adequate)
- Small caps (S&P 600): Mostly Tier 3-4 (adequate to marginal)
- ASX300: Mix of Tier 2-4 (smaller market, less liquidity)

## Technical Details

### Data Source
- **Yahoo Finance API** via `yfinance` library
- Real-time pricing, volume, and fundamentals
- 3-month historical data for volume averages
- Bid/ask spreads from current quotes

### Rate Limiting
- 0.1 second delay between API calls
- Prevents overwhelming Yahoo Finance servers
- Total runtime: ~20-30 minutes for 1,800 stocks

### Error Handling
- Graceful handling of delisted stocks
- Missing data fields handled safely
- Progress tracking and logging
- Partial results saved even if some symbols fail

## Maintenance

### Update Frequency
- **Daily**: Before market open (use latest symbols)
- **Weekly**: Full re-screen to catch liquidity changes
- **Monthly**: Review and adjust thresholds if needed

### Updating Symbol Lists
```bash
cd scans
python download_the_csv.py  # Downloads latest holdings
```

This creates a new `downloads_YYYY-MM-DD` folder. The liquidity screener automatically uses the most recent one.

## Troubleshooting

### "No download folder found"
**Solution**: Run `download_the_csv.py` first to get symbol lists

### "No symbols loaded"
**Solution**: Check that downloads folder contains `*_symbols.csv` files

### Slow execution
**Normal**: Processing 1,800 stocks takes 20-30 minutes due to API rate limiting

### Missing data for some stocks
**Normal**: Some stocks may be delisted or have incomplete data. These are automatically skipped.

## References

### Research Sources
- Market impact models (institutional trading)
- Liquidity measurement methodologies
- Professional trader volume requirements
- Academic studies on transaction costs
- Slippage estimation models

### Key Insights
1. **Position should be ≤ 1-2% of ADV** (industry standard)
2. **Minimum $20M DDV for $400K positions** (conservative)
3. **Spread < 0.5% to avoid high costs** (institutional threshold)
4. **Can exit in 1-3 days for adequate liquidity** (risk management)
5. **Tier 3+ or avoid entirely** (safety first)

## Support

For questions or issues:
1. Check this README first
2. Review console output for error messages
3. Verify download folder contains symbol files
4. Check internet connection (Yahoo Finance API requires connectivity)

---

**Remember**: Liquidity is NOT negotiable. Getting stuck in an illiquid position can cost you 5-10%+ just trying to exit. Better to miss a trade than to get trapped in one you can't exit efficiently.
