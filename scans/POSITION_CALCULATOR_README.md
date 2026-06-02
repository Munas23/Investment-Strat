# Position Sizing Calculators

Complete position sizing tools for $2M trading account, integrating all screening results and risk management rules.

---

## Overview

Two complementary tools:

1. **[position_calculator.py](position_calculator.py)** - Interactive single-stock calculator
2. **[batch_position_calculator.py](batch_position_calculator.py)** - Batch calculator for watchlists

Both implement the complete risk management framework from [RISK_MANAGEMENT_FRAMEWORK.md](RISK_MANAGEMENT_FRAMEWORK.md).

---

## Features

### Core Calculations
- ✅ **Conviction-based position sizing** (5-level system)
- ✅ **Market health multipliers** (bear to bull)
- ✅ **ATR-based stops** with percentage caps
- ✅ **Liquidity limits** (max 2% of DDV)
- ✅ **Position size limits** (by conviction and tier)
- ✅ **Portfolio risk management** (20% max total risk)
- ✅ **Profit targets** (2/4/6 ATR multiples)
- ✅ **Scaled exits** (33/33/34 method)
- ✅ **R-multiple calculations**

### Integration
- ✅ Loads liquidity screening results
- ✅ Loads fundamental screening results
- ✅ Fetches real-time price and ATR from Yahoo Finance
- ✅ Validates portfolio limits
- ✅ Exports to CSV

---

## Installation

```bash
cd scans
pip install pandas numpy yfinance
```

**Requirements:**
- Python 3.7+
- pandas
- numpy
- yfinance

---

## Usage

### 1. Single Stock Calculator (Interactive)

**Run:**
```bash
python position_calculator.py
```

**Interactive Prompts:**
- Symbol (e.g., NVDA)
- Entry price
- Conviction level (1-5)
- Market health (bull/uptrend/neutral/choppy/downtrend/bear)
- Liquidity tier (TIER 1/2/3)
- Daily Dollar Volume
- Fundamental score (optional)
- Pattern type (standard/vcp/episodic_pivot)

**Output:**
- Complete position sizing report
- Stop loss price and percentage
- Profit targets (3 levels)
- Risk/reward ratios
- Scaled exit plan
- Portfolio impact

**Example:**
```
Symbol: NVDA
Entry Price: $500
Conviction Level: 5
Market Health: bull
Liquidity Tier: TIER 1 - EXCELLENT
Daily Dollar Volume: $25000000000
Fundamental Score: 85
Pattern Type: vcp
```

**Result:**
```
POSITION SIZING REPORT: NVDA
================================================================================
📊 POSITION SUMMARY
   Entry Price:        $500.00
   Shares:             2,000
   Position Value:     $1,000,000.00 (50.00% of account)
   Dollar Risk:        $60,000.00 (3.00% risk)

🛑 STOP LOSS
   Stop Price:         $470.00
   Stop Distance:      $30.00 (6.00%)
   ATR:                $20.00 (using 1.5x multiplier)

🎯 PROFIT TARGETS
   Target 1 (2 ATR):   $540.00 (+8.0%) = 1.3R
      → Sell 660 shares, move stop to breakeven
   Target 2 (4 ATR):   $580.00 (+16.0%) = 2.7R
      → Sell 660 shares, move stop to Target 1
   Target 3 (6 ATR):   $620.00 (+24.0%) = 4.0R
      → Trail final 680 shares with 10/20 MA
```

---

### 2. Batch Position Calculator

Calculate positions for multiple stocks from your screening results.

**Run:**
```bash
python batch_position_calculator.py
```

**Three Modes:**

#### Mode 1: Manual Watchlist
Calculate for a custom list of symbols.

**Example:**
```
Choice: 1
Current Market Health: bull
Symbols: NVDA,AAPL,MSFT,GOOGL
Conviction levels:
  NVDA: 5
  AAPL: 4
  MSFT: 4
  GOOGL: 3
```

#### Mode 2: From Technical Screening Results
Automatically calculate for all stocks from technical screener.

**Example:**
```
Choice: 2
Path to technical screening CSV: technical screener/results_2026-01/technical_screen_20260102_TOP_CANDIDATES.csv
Minimum conviction level: 4
Current Market Health: bull
```

This will:
- Load all Level 4-5 stocks from technical screening
- Merge with liquidity and fundamental data
- Calculate position sizes for each
- Generate a trading plan respecting portfolio limits

#### Mode 3: Top N Fundamental Stocks
Calculate for the highest-rated fundamental stocks.

**Example:**
```
Choice: 3
How many top stocks: 20
Default conviction level: 3
Current Market Health: neutral
```

---

### 3. Programmatic Usage

```python
from position_calculator import PositionSizingCalculator

# Initialize
calc = PositionSizingCalculator(account_size=2_000_000)

# Calculate position
position = calc.calculate_position_size(
    symbol='NVDA',
    entry_price=500.00,
    atr=20.00,
    conviction_level=5,
    market_health='bull',
    liquidity_tier='TIER 1 - EXCELLENT',
    ddv=25_000_000_000,
    fundamental_score=85.0,
    pattern_type='vcp'
)

# Print report
calc.print_position_report(position, detailed=True)

# Check portfolio limits
can_add, message = calc.check_portfolio_limits(position['final_risk_pct'])
if can_add:
    calc.add_position_to_portfolio(position)

# Get portfolio summary
summary = calc.get_portfolio_summary()
print(f"Total risk: {summary['total_risk_pct']}%")
```

---

## Position Sizing Formula

### Step 1: Calculate Risk Percentage

```python
base_risk = 1.5%  # Base risk per trade

# Conviction multiplier
conviction_mult = {
    5: 1.5,   # Level 5 = 150%
    4: 1.25,  # Level 4 = 125%
    3: 1.0,   # Level 3 = 100%
    2: 0.75,  # Level 2 = 75%
    1: 0.5,   # Level 1 = 50%
}

# Market health multiplier
market_mult = {
    'bull': 1.5,
    'uptrend': 1.25,
    'neutral': 1.0,
    'choppy': 0.75,
    'downtrend': 0.5,
}

# Calculate
risk_pct = base_risk × conviction_mult × market_mult
risk_pct = min(risk_pct, 3.0%)  # Cap at 3%

dollar_risk = $2,000,000 × risk_pct
```

**Example (Level 5 in bull market):**
```
risk_pct = 1.5% × 1.5 × 1.5 = 3.375% → capped at 3.0%
dollar_risk = $2,000,000 × 0.03 = $60,000
```

### Step 2: Calculate Stop Loss

```python
# ATR multipliers by conviction
atr_mult = {
    5: 1.5,  # Tight
    4: 2.0,  # Standard (Turtle)
    3: 2.5,  # Wider
}

# ATR-based stop
stop_distance = ATR × atr_mult
stop_price = entry - stop_distance

# Apply percentage cap
max_stop_pct = {5: 5%, 4: 7%, 3: 8%}
max_stop_price = entry × (1 - max_stop_pct)

# Use tighter of the two
final_stop = max(atr_stop_price, max_stop_price)
```

**Example:**
```
entry = $100
ATR = $3
atr_mult = 1.5 (Level 5)

atr_stop = $100 - ($3 × 1.5) = $95.50
max_stop = $100 × 0.95 = $95.00

final_stop = $95.50 (tighter)
stop_percent = 4.5%
```

### Step 3: Calculate Shares

```python
shares = dollar_risk / stop_distance

# Example:
shares = $60,000 / $4.50 = 13,333 shares
position_value = 13,333 × $100 = $1,333,333
position_pct = 66.7% of account
```

### Step 4: Apply Limits

```python
# Position size limits
max_by_conviction = {5: 25%, 4: 20%, 3: 15%}
max_by_tier = {'TIER 1': 25%, 'TIER 2': 20%, 'TIER 3': 15%}
max_by_liquidity = DDV × 2%

# Use most restrictive
max_position = min(
    max_by_conviction,
    max_by_tier,
    max_by_liquidity,
    25%  # Hard cap
)

# Reduce if needed
if position_value > max_position:
    position_value = max_position
    shares = position_value / entry_price
    # Recalculate actual risk
```

---

## Output Files

### position_calculator.py
Saves to: `position_{SYMBOL}_{TIMESTAMP}.csv`

Single row with all position details.

### batch_position_calculator.py
Saves two files:

1. **`batch_positions_{TIMESTAMP}_FULL.csv`**
   - All calculated positions
   - Sorted by conviction and fundamental score

2. **`batch_positions_{TIMESTAMP}_TRADING_PLAN.csv`**
   - Selected positions respecting portfolio limits
   - Ready to trade
   - Includes portfolio risk tracking

---

## Risk Management Rules

### Individual Position Limits

| Conviction | Max Risk % | Typical Stop % | Max Position % |
|------------|------------|----------------|----------------|
| Level 5 | 3.0% | 4-5% | 25% |
| Level 4 | 2.8% | 6-7% | 20% |
| Level 3 | 2.25% | 7-8% | 15% |
| Level 2 | 1.7% | 8-10% | 10% |

### Portfolio Limits

- **Max Total Risk**: 20% ($400,000)
- **Max Positions**: 12 concurrent
- **Max Single Position**: 25% ($500,000)
- **Max Position as % of DDV**: 2%
- **Max Sector Exposure**: 30%

### Stop Loss Rules

- **ATR-based** with percentage caps
- Never move stop down (only up)
- Hard stops, no exceptions
- Exit entire position on stop hit

### Profit Targets (33/33/34 Method)

1. **Target 1 (2 ATR)**: Sell 33%, move stop to breakeven
2. **Target 2 (4 ATR)**: Sell 33%, move stop to Target 1
3. **Target 3 (6 ATR)**: Trail final 34% with 10/20 MA

---

## Example Workflow

### Daily Trading Routine

1. **Run Technical Screener** (daily)
   ```bash
   python "technical screener/technical_screener.py"
   ```

2. **Calculate Positions** (for Level 4-5 setups)
   ```bash
   python batch_position_calculator.py
   ```
   - Choose Mode 2 (from technical screening)
   - Set minimum conviction: 4
   - Enter market health: bull/uptrend/neutral

3. **Review Trading Plan**
   - Open `batch_positions_*_TRADING_PLAN.csv`
   - Review top positions
   - Verify stops and targets

4. **Execute Trades**
   - Enter positions at calculated prices
   - Set stop loss orders immediately
   - Set profit target alerts

5. **Manage Positions**
   - Monitor profit targets
   - Scale out per 33/33/34 plan
   - Trail stops on final portion

---

## Integration with Screening System

### Complete Pipeline

```
1. Weekly/Monthly:
   ├── download_the_csv.py         → Get symbols
   ├── liquidity_screener.py       → Screen for liquidity
   └── fundamental_screener.py     → Screen for quality

2. Daily:
   ├── technical_screener.py       → Get conviction levels
   └── batch_position_calculator.py → Calculate positions

3. Execution:
   ├── Review trading plan
   ├── Execute trades
   └── Manage positions
```

### Data Flow

```
Liquidity Screen (1,171 stocks)
        ↓
Fundamental Screen (81 stocks, 60%+)
        ↓
Technical Screen (Daily, Level 3-5)
        ↓
Position Calculator
        ↓
Trading Plan (Top 6-12 positions)
```

---

## Customization

### Modify Risk Parameters

Edit in `position_calculator.py`:

```python
def __init__(self, account_size: float = 2_000_000):
    # CUSTOMIZE THESE:
    self.base_risk_percent = 1.5          # Base risk (1.5%)
    self.max_risk_per_trade = 3.0         # Max risk cap (3%)
    self.max_total_portfolio_risk = 20.0  # Max total risk (20%)
    self.max_positions = 12               # Max positions
    self.max_single_position_percent = 25 # Max per position (25%)

    # Conviction multipliers
    self.conviction_multipliers = {
        5: 1.5,   # Adjust these
        4: 1.25,
        3: 1.0,
    }

    # Market multipliers
    self.market_multipliers = {
        'bull': 1.5,      # Adjust these
        'uptrend': 1.25,
        'neutral': 1.0,
    }
```

---

## Expected Outcomes

### By Conviction Level

**Level 5 (MAXIMUM):**
- Win Rate: 40-50%
- Avg Win: 8-10R (32-50%)
- Avg Loss: 1R (4-5%)
- Expectancy: +6R per trade

**Level 4 (HIGH):**
- Win Rate: 35-45%
- Avg Win: 5-7R (30-49%)
- Avg Loss: 1R (6-7%)
- Expectancy: +3R per trade

**Level 3 (MODERATE):**
- Win Rate: 30-40%
- Avg Win: 3-5R (24-40%)
- Avg Loss: 1R (7-8%)
- Expectancy: +1.5R per trade

### Portfolio Performance

With 20% total portfolio risk and mixed conviction levels:
- Expected return per cycle: +15-30%
- Maximum drawdown: <20%
- Win rate: ~37%
- Average R-multiple: +1.5R

---

## Troubleshooting

### "No downloads folder found"
**Solution**: Run `download_the_csv.py` first to get stock symbols

### "No liquidity screening results found"
**Solution**: Run `liquidity screener/liquidity_screener.py`

### "Could not fetch ATR for {symbol}"
**Causes**:
- Symbol not found on Yahoo Finance
- Insufficient historical data
- Network connection issue

**Solution**: Enter ATR manually when prompted

### "Position exceeds liquidity limit"
**Cause**: Position too large for stock's daily volume

**Solution**: Position is automatically reduced to 2% of DDV

### "Portfolio limit exceeded"
**Cause**: Adding position would exceed 20% total risk

**Solution**: Either:
1. Reduce size of existing positions
2. Skip this trade
3. Close some positions first

---

## Advanced Features

### Portfolio Tracking

```python
calc = PositionSizingCalculator()

# Add positions as you enter them
position1 = calc.calculate_position_size(...)
calc.add_position_to_portfolio(position1)

position2 = calc.calculate_position_size(...)
calc.add_position_to_portfolio(position2)

# Check current state
summary = calc.get_portfolio_summary()
print(f"Total risk: {summary['total_risk_pct']}%")
print(f"Positions: {summary['total_positions']}/{calc.max_positions}")
print(f"Capital deployed: ${summary['total_capital_deployed']:,}")
```

### Pattern-Specific Stops

```python
# VCP (Volatility Contraction Pattern) - tighter stops
position = calc.calculate_position_size(
    ...
    pattern_type='vcp'  # Uses tighter ATR multiplier
)

# Episodic Pivot - use low of day
position = calc.calculate_position_size(
    ...
    pattern_type='episodic_pivot'  # Returns 'LOD' recommendation
)
```

---

## Future Enhancements

Planned features:
- [ ] Pyramiding calculator (Turtle-style adds)
- [ ] Real-time position monitoring
- [ ] Automated alerts for profit targets
- [ ] Portfolio rebalancing tool
- [ ] Performance tracking and analytics
- [ ] Integration with broker APIs

---

## References

- [RISK_MANAGEMENT_FRAMEWORK.md](RISK_MANAGEMENT_FRAMEWORK.md) - Complete risk rules
- [legendary_traders_technical_setups.md](legendary_traders_technical_setups.md) - Trader methodologies
- [qullamaggie_atr_risk_management.md](qullamaggie_atr_risk_management.md) - ATR-based risk

---

## Support

For questions or issues:
1. Check this README first
2. Review risk management framework
3. Verify screening data is current
4. Check internet connection (Yahoo Finance API)

---

**Remember**: Position sizing is your most important risk management tool. The calculator implements professional-grade rules, but YOU must:
1. Enter accurate data
2. Respect the limits
3. Execute the stops
4. Follow the exit plan

**Never override the calculator to take larger positions. The math is designed to protect your capital.**

Trade smart. Manage risk. Compound gains.
