# Quick Start Guide - Position Sizing Calculator

## What You Just Built

A complete position sizing calculator for your $2M trading account that:
- ✅ Integrates with all your screening results
- ✅ Calculates optimal position sizes based on conviction levels
- ✅ Manages portfolio risk (20% max)
- ✅ Sets ATR-based stops with caps
- ✅ Provides profit targets and exit plans
- ✅ Respects liquidity limits

---

## Files Created

1. **[position_calculator.py](position_calculator.py)** - Core calculator (single stocks)
2. **[batch_position_calculator.py](batch_position_calculator.py)** - Batch calculator (watchlists)
3. **[test_position_calculator.py](test_position_calculator.py)** - Test with NVDA
4. **[POSITION_CALCULATOR_README.md](POSITION_CALCULATOR_README.md)** - Full documentation

---

## Quick Test (5 seconds)

```bash
cd scans
python test_position_calculator.py
```

This tests NVDA in 3 scenarios:
- Level 5 in bull market
- Level 4 in uptrend
- Level 3 in neutral market

**Example Output:**
```
NVDA @ $184.77
- Level 5 Bull: 2,164 shares, $400K position (20%), 0.66% risk, stop $178.63
- Level 4 Up:   2,164 shares, $400K position (20%), 1.33% risk, stop $172.49
- Level 3 Neu:  1,623 shares, $300K position (15%), 1.20% risk, stop $169.99
```

---

## Usage Examples

### Example 1: Calculate Position for One Stock

```bash
python position_calculator.py
```

**Prompts:**
```
Symbol: AAPL
Entry Price: $225
Conviction Level: 4
Market Health: bull
Liquidity Tier: TIER 1 - EXCELLENT
Daily Dollar Volume: 50000000000
Fundamental Score: 75
Pattern Type: standard
```

**Result:** Complete position sizing report with stops, targets, and risk/reward.

---

### Example 2: Calculate for Your Watchlist

```bash
python batch_position_calculator.py
```

**Select Mode 1:** Manual watchlist
```
Current Market Health: bull
Symbols: NVDA,AAPL,MSFT,GOOGL,TSLA
Conviction levels:
  NVDA: 5
  AAPL: 4
  MSFT: 4
  GOOGL: 3
  TSLA: 3
```

**Result:** Position sizing for all 5 stocks + trading plan

---

### Example 3: Auto-Calculate from Screening Results

```bash
python batch_position_calculator.py
```

**Select Mode 3:** Top fundamental stocks
```
How many top stocks: 10
Default conviction level: 4
Current Market Health: uptrend
```

**Result:** Automatically fetches top 10 from your fundamental screening, calculates positions, generates trading plan.

---

## Understanding the Output

### Position Report Shows:

**📊 POSITION SUMMARY**
- Entry price (current market price)
- Shares to buy
- Position value (total $)
- Position % of account (10-25%)
- Dollar risk (actual $ at risk)
- Risk % (0.66%-3.0%)

**🛑 STOP LOSS**
- Stop price (exit if hits this)
- Stop distance ($)
- Stop % (typically 4-8%)
- ATR multiplier used

**🎯 PROFIT TARGETS**
- Target 1 (2 ATR): Sell 33%
- Target 2 (4 ATR): Sell 33%
- Target 3 (6 ATR): Trail final 34%
- R-multiples (2R, 4R, 6R)

**⚖️ RISK/REWARD**
- Risk amount (%)
- Reward amount (%)
- Ratio (1:2.0 = risking 1% to make 2%)

---

## Key Numbers for $2M Account

| Parameter | Value |
|-----------|-------|
| Account Size | $2,000,000 |
| Base Risk | 1.5% ($30K) |
| Max Risk/Trade | 3.0% ($60K) |
| Max Total Risk | 20% ($400K) |
| Max Positions | 12 |
| Max Position Size | 25% ($500K) |

### Position Sizing by Conviction (Bull Market)

| Level | Risk % | Typical Stop % | Position Size | Example $ |
|-------|--------|----------------|---------------|-----------|
| 5 | 3.0% | 4-5% | 20-25% | $400K-$500K |
| 4 | 2.8% | 6-7% | 15-20% | $300K-$400K |
| 3 | 2.25% | 7-8% | 10-15% | $200K-$300K |

---

## Daily Workflow (Once Set Up)

### 1. Morning Routine (Before Market Open)

Run technical screener on your quality stocks:
```bash
python "technical screener/technical_screener.py"
```

This generates Level 1-5 conviction scores for all stocks.

### 2. Calculate Positions (5 minutes)

For Level 4-5 setups:
```bash
python batch_position_calculator.py
```
- Mode 2: Load technical screening results
- Min conviction: 4
- Market health: (check market condition)

### 3. Review Trading Plan

Open: `batch_positions_YYYYMMDD_TRADING_PLAN.csv`

Review:
- Top positions by conviction
- Position sizes
- Stops and targets
- Total portfolio risk

### 4. Execute Trades

For each position:
1. Enter at calculated price (or better)
2. **Immediately set stop-loss order** at stop price
3. Set alerts for profit targets
4. Record entry in tracking spreadsheet

### 5. Manage Throughout Day

**At Target 1 (2 ATR / ~10-15% gain):**
- Sell 33% of shares
- Move stop to breakeven
- Let rest run

**At Target 2 (4 ATR / ~20-30% gain):**
- Sell another 33%
- Move stop to Target 1 price
- Trail final portion

**Final 34%:**
- Trail with 10-day or 20-day MA
- Exit when closes below MA

---

## Common Scenarios

### Scenario: Found Perfect Level 5 Setup

**Stock:** DUOL (from your screening)
- Fundamental: 86.7% (A+)
- Liquidity: Tier 2 - Good
- Technical: Level 5 (perfect VCP)
- Market: Bull

**Calculator Says:**
- Buy 2,280 shares @ $175.50
- Position value: $400K (20% of account)
- Risk: 3.0% ($60K)
- Stop: $168.84 (3.8%)
- Target 1: $187.58 (+6.9%) = sell 753 shares
- R:R: 1:1.8

**Action:**
1. Enter limit order: 2,280 shares @ $175.50 (or better)
2. Set stop-loss: $168.84 (immediate!)
3. Set alert: $187.58 (Target 1)
4. Wait and manage

---

### Scenario: Building Full Portfolio

You have 6 Level 4-5 setups. Can you take them all?

**Check with batch calculator:**
```bash
python batch_position_calculator.py
```

Calculator automatically:
- Sorts by conviction (5 → 4 → 3)
- Adds positions until 20% total risk hit
- Generates trading plan with top positions

**Example Output:**
```
Trading Plan: 5 positions selected
Total Risk: 19.8% (under 20% limit)
Capital Deployed: $1.85M (92.5%)

Position 1: DUOL (L5) - $400K, 3.0% risk
Position 2: NVDA (L5) - $400K, 3.0% risk
Position 3: AAPL (L4) - $400K, 2.8% risk
Position 4: MSFT (L4) - $350K, 2.8% risk
Position 5: GOOGL (L4) - $300K, 2.4% risk

Skipped: TSLA (would exceed 20% risk limit)
```

---

## Safety Features Built In

### ✅ Automatic Limits

1. **Position Size Capped**
   - Level 5: Max 25%
   - Level 4: Max 20%
   - Level 3: Max 15%
   - Plus liquidity limits (2% of DDV)

2. **Risk Capped**
   - Individual: 3.0% max
   - Portfolio total: 20% max

3. **Stop Loss Required**
   - ATR-based (respects volatility)
   - Percentage capped (prevents runaway stops)
   - Tighter of the two used

4. **Portfolio Validation**
   - Checks before adding position
   - Warns if limit exceeded
   - Suggests alternatives

---

## What If...?

### Q: Stock gaps down past my stop?

**A:** You'll lose more than calculated risk. This is "slippage risk."

**Mitigation:**
- Only trade liquid stocks (Tier 1-3)
- Use stop-limit orders in volatile stocks
- Monitor overnight gaps
- Reduce size before earnings

### Q: Calculator says position too large for liquidity?

**A:** Position automatically reduced to 2% of DDV.

**Example:**
- Stock DDV: $20M
- Limit: 2% = $400K max
- If calculator wants $500K → reduced to $400K

### Q: Can I override and take bigger positions?

**A:** You CAN, but you SHOULDN'T.

**Why not:**
- Risk management protects you
- Limits are based on math, not emotion
- One big loss can wipe out months of gains
- Professional traders respect their rules

**Better approach:**
- If conviction super high → add after breakout works (pyramiding)
- Don't go bigger upfront

### Q: Portfolio at 20% risk, but found perfect Level 5 setup?

**A:** Options:
1. Close a weaker position (Level 3)
2. Reduce all positions slightly
3. Wait for a stop-out
4. Skip this trade (discipline!)

**Remember:** There's always another trade. Protecting capital > catching every move.

---

## Next Steps

1. ✅ **Test calculator** with your screening data
2. ✅ **Paper trade** for 1-2 weeks to validate
3. ✅ **Start small** (10% of account = $200K)
4. ✅ **Scale up** as you gain confidence
5. ✅ **Track results** (win rate, R-multiples)
6. ✅ **Adjust** parameters based on your results

---

## Pro Tips

1. **Always use the calculator** - Don't wing it
2. **Set stops immediately** - No exceptions
3. **Take profits at targets** - Follow the plan
4. **Review weekly** - What worked? What didn't?
5. **Adjust market health** - Be honest about conditions
6. **Start conservative** - Use neutral market multipliers
7. **Respect the limits** - They exist for a reason

---

## Support Files

- Full docs: [POSITION_CALCULATOR_README.md](POSITION_CALCULATOR_README.md)
- Risk framework: [RISK_MANAGEMENT_FRAMEWORK.md](RISK_MANAGEMENT_FRAMEWORK.md)
- Backtest plan: [BACKTEST_SYSTEMS_PLAN.md](BACKTEST_SYSTEMS_PLAN.md)

---

**You now have a professional-grade position sizing system. Use it wisely. Manage risk first, profits will follow.**

🎯 Good luck trading!
