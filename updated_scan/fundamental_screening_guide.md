# 5-LEVEL CONVICTION FUNDAMENTAL SCREENING GUIDE

## Overview

The 5LC strategy uses a **quality-first approach** with comprehensive fundamental screening as the foundation. Only stocks that pass our rigorous 60% minimum quality threshold are eligible for technical analysis and conviction scoring.

This screening eliminates poor-quality companies before we waste time on technical analysis, ensuring we only trade fundamentally sound businesses during their technical breakouts.

---

## FUNDAMENTAL SCORING SYSTEM (150 Total Points)

### **Target Score: 90+ points (60% minimum) for trade consideration**

The scoring system evaluates 6 critical categories that identify high-quality growth companies suitable for momentum trading:

---

## 1. MARKET CAP & PRICE FILTER (15 Points)

**Purpose**: Ensure adequate company size and share price for institutional participation

### Market Cap Scoring (10 points)
- **USD Markets (S&P 500)**: $300M - $50B range
- **AUD Markets (ASX300)**: $500M - $50B range

**Rationale**:
- Minimum caps ensure liquidity and institutional coverage
- Maximum caps avoid mega-caps with limited upside potential
- Sweet spot for growth momentum plays

### Price Filter (5 points)
- **USD Markets**: $15+ minimum share price
- **AUD Markets**: $5+ minimum share price

**Rationale**:
- Eliminates penny stocks and poor-quality companies
- Ensures institutional tradability
- Higher prices indicate market respect

---

## 2. VOLUME FILTER (5 Points)

**Purpose**: Ensure adequate liquidity for position entry/exit

### Daily Volume Requirements
- **USD Markets**: 500,000+ average daily volume
- **AUD Markets**: 100,000+ average daily volume

**Rationale**:
- Prevents liquidity issues during volatility
- Ensures tight bid-ask spreads
- Allows for larger position sizes
- Different thresholds account for market size differences

---

## 3. PROFITABILITY METRICS (35 Points)

**Purpose**: Identify companies with excellent operational performance

### Return on Equity - ROE (20 points)
- **Excellent (20 pts)**: 25%+ ROE
- **Good (15 pts)**: 20-24.9% ROE
- **Pass (10 pts)**: 15-19.9% ROE
- **Fail (0 pts)**: <15% ROE

**Why ROE Matters**:
- Measures management effectiveness with shareholder capital
- High ROE indicates competitive advantages
- Strong ROE often correlates with stock outperformance
- 15% minimum eliminates mediocre businesses

### Profit Margin (15 points)
- **Excellent (15 pts)**: 20%+ margin
- **Good (12 pts)**: 15-19.9% margin
- **Pass (8 pts)**: 10-14.9% margin
- **Fail (0 pts)**: <10% margin

**Why Profit Margin Matters**:
- Indicates pricing power and cost control
- High margins suggest competitive moats
- Provides cushion during economic stress
- 10% minimum ensures quality operations

---

## 4. GROWTH METRICS (50 Points) - **MOST CRITICAL**

**Purpose**: Identify companies with accelerating business momentum

### Quarterly Revenue Growth (25 points)
- **Excellent (25 pts)**: 30%+ quarterly growth
- **Good (20 pts)**: 20-29.9% quarterly growth
- **Pass (15 pts)**: 15-19.9% quarterly growth
- **Fail (0 pts)**: <15% quarterly growth

### Quarterly Earnings Growth (25 points)
- **Excellent (25 pts)**: 40%+ quarterly growth
- **Good (20 pts)**: 25-39.9% quarterly growth
- **Pass (15 pts)**: 18-24.9% quarterly growth
- **Fail (0 pts)**: <18% quarterly growth

**Why Growth is Critical for 5LC**:
- **Quarterly focus**: Recent performance matters more than annual
- **High thresholds**: We want accelerating, not declining growth
- **Earnings leverage**: Earnings should grow faster than revenue
- **Momentum correlation**: Strong fundamentals drive technical momentum
- **Institution attraction**: Growth stocks attract momentum capital

**Growth Scoring Philosophy**:
```
50 points / 150 total = 33% of fundamental score
This heavy weighting reflects that growth drives momentum
We're not value investors - we want growth acceleration
```

---

## 5. FINANCIAL STRENGTH (25 Points)

**Purpose**: Ensure balance sheet quality for sustainable growth

### Current Ratio (15 points)
- **Excellent (15 pts)**: 2.0+ current ratio
- **Good (12 pts)**: 1.8-1.99 current ratio
- **Pass (8 pts)**: 1.5-1.79 current ratio
- **Fail (0 pts)**: <1.5 current ratio

**Why Current Ratio Matters**:
- Measures short-term liquidity safety
- 1.5+ ensures ability to pay bills
- Higher ratios provide recession cushion
- Prevents bankruptcy risk in portfolios

### Debt-to-Equity (10 points)
- **Excellent (10 pts)**: 0.1 or less (10% debt)
- **Good (8 pts)**: 0.11-0.20 (11-20% debt)
- **Pass (5 pts)**: 0.21-0.30 (21-30% debt)
- **Fail (0 pts)**: >0.30 (30%+ debt)

**Why Low Debt Matters**:
- Reduces financial risk during downturns
- Preserves growth capital flexibility
- Prevents interest rate sensitivity
- 30% maximum keeps leverage reasonable

---

## 6. INSTITUTIONAL OWNERSHIP (20 Points)

**Purpose**: Ensure professional money management validation

### Institutional Ownership Percentage
- **Optimal (20 pts)**: 50-70% institutional ownership
- **Good (15 pts)**: 40-49% or 71-80% institutional
- **Fail (0 pts)**: <40% or >80% institutional

**Why Institutional Ownership Matters**:

**Minimum 40% Required**:
- Professional validation of business quality
- Provides buying support during volatility
- Indicates analyst coverage and research
- Suggests adequate liquidity for institutions

**Sweet Spot 50-70%**:
- Balanced between validation and room for growth
- Not over-owned by momentum funds
- Still attracting new institutional buyers
- Optimal for momentum continuation

**Maximum 80% Limit**:
- Prevents over-ownership situations
- Avoids "crowded trade" risks
- Maintains retail participation potential
- Reduces liquidation pressure risk

---

## MARKET-SPECIFIC ADAPTATIONS

### US Markets (S&P 500)
- Higher volume requirements (500K vs 100K)
- Higher price minimums ($15 vs $5)
- USD-denominated thresholds
- More competitive fundamental requirements

### Australian Markets (ASX300)
- Lower volume thresholds (smaller market)
- AUD-denominated calculations
- Adjusted market cap minimums
- Accounts for market size differences

---

## FUNDAMENTAL SCREENING PROCESS

### Step 1: Basic Filters
```python
# Must pass ALL basic filters to continue
✓ Market cap in acceptable range
✓ Share price above minimums
✓ Average volume above thresholds
```

### Step 2: Quality Scoring
```python
# Calculate weighted score across 6 categories
profitability_score = roe_points + margin_points          # 35 pts max
growth_score = revenue_growth + earnings_growth           # 50 pts max
strength_score = current_ratio + debt_equity              # 25 pts max
institutional_score = ownership_percentage                # 20 pts max
size_score = market_cap + price_filter                   # 15 pts max
liquidity_score = volume_filter                          # 5 pts max

total_score = sum(all_categories)                         # 150 pts max
percentage_score = (total_score / 150) * 100
```

### Step 3: Pass/Fail Decision
```python
if percentage_score >= 60%:  # 90+ points
    proceed_to_technical_analysis()
else:
    reject_symbol("Failed fundamental screen")
```

---

## SCORING EXAMPLES

### Example 1: High-Quality Growth Stock
```
NVDA-type Profile:
Market Cap: $1.2T (10 pts) + Price: $750 (5 pts) = 15/15
Volume: 50M daily (5 pts) = 5/5
ROE: 35% (20 pts) + Profit Margin: 25% (15 pts) = 35/35
Revenue Growth: 35% (25 pts) + Earnings Growth: 55% (25 pts) = 50/50
Current Ratio: 2.1 (15 pts) + Debt/Equity: 0.15 (8 pts) = 23/25
Institutional: 65% (20 pts) = 20/20

Total: 148/150 = 99% - EXCELLENT QUALITY
```

### Example 2: Marginal Quality Stock
```
Borderline Profile:
Market Cap: $800M (10 pts) + Price: $25 (5 pts) = 15/15
Volume: 600K daily (5 pts) = 5/5
ROE: 16% (10 pts) + Profit Margin: 12% (8 pts) = 18/35
Revenue Growth: 18% (15 pts) + Earnings Growth: 20% (15 pts) = 30/50
Current Ratio: 1.6 (8 pts) + Debt/Equity: 0.25 (5 pts) = 13/25
Institutional: 45% (15 pts) = 15/20

Total: 96/150 = 64% - BARELY PASSES (90+ points needed)
```

### Example 3: Poor Quality Stock
```
Failed Profile:
Market Cap: $200M (0 pts) + Price: $8 (0 pts) = 0/15
Volume: 50K daily (0 pts) = 0/5
ROE: 8% (0 pts) + Profit Margin: 5% (0 pts) = 0/35
Revenue Growth: 5% (0 pts) + Earnings Growth: 2% (0 pts) = 0/50
Current Ratio: 1.2 (0 pts) + Debt/Equity: 0.6 (0 pts) = 0/25
Institutional: 25% (0 pts) = 0/20

Total: 0/150 = 0% - COMPLETE FAILURE
```

---

## WHY FUNDAMENTAL SCREENING FIRST?

### 1. **Eliminates 80%+ of Stocks**
- Most stocks fail our quality standards
- Saves computational time on technical analysis
- Focuses effort on worthy candidates

### 2. **Quality Drives Performance**
- Fundamental quality correlates with stock performance
- Poor fundamentals rarely sustain technical momentum
- Quality companies recover faster from setbacks

### 3. **Risk Management**
- Screens out potential bankruptcies
- Ensures balance sheet safety
- Reduces portfolio blow-up risk

### 4. **Professional Standards**
- Institutional-grade screening criteria
- Eliminates "story stocks" without substance
- Focuses on profitable, growing businesses

### 5. **Momentum Sustainability**
- Strong fundamentals support sustained breakouts
- Growth acceleration attracts institutional buyers
- Quality companies maintain momentum longer

---

## INTEGRATION WITH TECHNICAL ANALYSIS

The fundamental screen is **Step 1** of our complete methodology:

```
1. Fundamental Screen (>60% score) ← QUALITY FILTER
2. Technical Analysis (>60 trend strength) ← TIMING FILTER
3. Conviction Scoring (25-100 points) ← SIZING FILTER
4. Risk Management (stops, targets, trails) ← PROTECTION FILTER
```

**Only stocks passing fundamental screening advance to technical analysis.**

This ensures we never waste time analyzing technically attractive setups in fundamentally poor companies.

---

## CONCLUSION

The 5LC fundamental screening system identifies **high-quality growth companies** suitable for momentum trading. By requiring 60%+ scores across profitability, growth, financial strength, and institutional validation, we create a universe of stocks with:

- **Sustainable competitive advantages** (high ROE, margins)
- **Accelerating business momentum** (strong growth rates)
- **Financial safety** (strong balance sheets)
- **Professional validation** (institutional ownership)
- **Adequate liquidity** (volume, market cap, price)

This quality-first approach provides the foundation for successful momentum trading, ensuring we only apply our technical timing and conviction systems to fundamentally sound businesses capable of sustained outperformance.

**Remember: We can't time our way out of a fundamentally poor business. Quality first, timing second.**