# Backtest Systems Plan

**Goal**: Build and backtest multiple risk management systems to determine optimal approach for $2M account.

---

## Systems to Test

### System 1: Conservative Growth (Minervini-Style)
**Philosophy**: Tight stops, high win rate, moderate position sizes

```python
system_1_conservative = {
    'name': 'Conservative Growth (Minervini)',

    # Position Sizing
    'position_sizing_method': 'Fixed Percentage Risk',
    'base_risk_percent': 1.0,  # Conservative 1%
    'conviction_multipliers': {
        5: 1.25,  # 1.25% for Level 5
        4: 1.0,   # 1.0% for Level 4
        3: 0.75,  # 0.75% for Level 3
    },
    'market_multipliers': None,  # Don't use market multipliers
    'max_risk_per_trade': 1.5,  # Cap at 1.5%

    # Stop Loss
    'stop_loss_method': 'Percentage-Based',
    'stop_loss_by_conviction': {
        5: 3,   # 3% for VCP/tight patterns
        4: 5,   # 5% standard
        3: 7,   # 7% wider
    },

    # Portfolio Limits
    'max_total_risk': 10,  # 10% max total risk
    'max_positions': 10,
    'max_position_size_pct': 15,  # 15% max per stock

    # Exits
    'exit_method': 'Scaled',
    'profit_targets': {
        1: {'pct': 10, 'sell': 33},   # +10% sell 33%
        2: {'pct': 20, 'sell': 33},   # +20% sell 33%
    },
    'trailing_stop': '10_day_MA',

    # Entry Requirements
    'min_conviction': 4,  # Only Level 4-5
    'min_fundamental_score': 75,  # Only EXCELLENT fundamentals
    'liquidity_tiers': [1, 2],  # Only Tier 1-2

    # Expected Outcomes
    'expected_win_rate': 45,
    'expected_avg_win': 25,
    'expected_avg_loss': 4,
}
```

**Pros**: Low risk, high win rate, suitable for risk-averse
**Cons**: May miss opportunities, smaller gains

---

### System 2: Moderate Aggressive (Turtle-Style)
**Philosophy**: ATR-based stops, volatility-adjusted, pyramiding

```python
system_2_turtle = {
    'name': 'Moderate Aggressive (Turtle)',

    # Position Sizing
    'position_sizing_method': 'ATR-Based',
    'base_risk_percent': 1.5,
    'conviction_multipliers': {
        5: 1.5,   # 2.25% for Level 5
        4: 1.25,  # 1.875% for Level 4
        3: 1.0,   # 1.5% for Level 3
    },
    'market_multipliers': {
        'bull': 1.5,
        'uptrend': 1.25,
        'neutral': 1.0,
        'downtrend': 0.5,
    },
    'max_risk_per_trade': 3.0,  # Cap at 3%

    # Stop Loss
    'stop_loss_method': 'ATR-Based',
    'atr_multipliers': {
        5: 1.5,  # 1.5 ATR
        4: 2.0,  # 2 ATR (classic Turtle)
        3: 2.5,  # 2.5 ATR
    },
    'max_stop_percent': {
        5: 5,
        4: 7,
        3: 8,
    },

    # Portfolio Limits
    'max_total_risk': 20,  # 20% max total risk
    'max_positions': 12,
    'max_position_size_pct': 25,

    # Exits
    'exit_method': 'Scaled',
    'profit_targets': {
        1: {'atr_multiple': 2, 'sell': 33},  # 2 ATR sell 33%
        2: {'atr_multiple': 4, 'sell': 33},  # 4 ATR sell 33%
    },
    'trailing_stop': 'Chandelier_3ATR',

    # Pyramiding
    'pyramiding_enabled': True,
    'pyramid_method': 'Turtle',
    'pyramid_add_at': 0.5,  # 0.5 ATR
    'max_units': 4,

    # Entry Requirements
    'min_conviction': 3,  # Level 3+
    'min_fundamental_score': 60,  # QUALITY
    'liquidity_tiers': [1, 2, 3],

    # Expected Outcomes
    'expected_win_rate': 35,
    'expected_avg_win': 35,
    'expected_avg_loss': 6,
}
```

**Pros**: Balanced, proven method, handles volatility
**Cons**: Wider stops, lower win rate

---

### System 3: Aggressive Momentum (Qullamaggie-Style)
**Philosophy**: Large positions, tight stops, let winners run

```python
system_3_qullamaggie = {
    'name': 'Aggressive Momentum (Qullamaggie)',

    # Position Sizing
    'position_sizing_method': 'Conviction-Based',
    'base_position_pct': {
        5: 20,  # 20% position for Level 5
        4: 15,  # 15% position for Level 4
        3: 10,  # 10% position for Level 3
    },
    'market_multipliers': {
        'bull': 1.25,      # Increase 25%
        'uptrend': 1.0,
        'neutral': 0.75,
        'downtrend': 0.5,
    },
    'max_position_size_pct': 25,

    # Stop Loss
    'stop_loss_method': 'Pattern-Based',
    'stop_rules': {
        'breakout': 'Low of day (max 1 ATR)',
        'pullback': 'Below MA with buffer',
    },
    'max_stop_percent': 8,

    # Portfolio Limits
    'max_total_risk': 25,  # Aggressive 25%
    'max_positions': 15,
    'max_position_size_pct': 25,

    # Exits
    'exit_method': 'Time + Trail',
    'profit_targets': {
        'day_3_to_5': {'sell': 50},  # Sell half after 3-5 days
    },
    'trailing_stop_fast': '10_day_MA',
    'trailing_stop_slow': '20_day_MA',

    # Pyramiding
    'pyramiding_enabled': False,  # Enter full size

    # Entry Requirements
    'min_conviction': 3,
    'min_fundamental_score': 50,  # Lower bar
    'liquidity_tiers': [1, 2, 3],
    'prefer_breakouts': True,  # Focus on breakouts
    'prefer_high_volume': True,  # 2x+ volume

    # Expected Outcomes
    'expected_win_rate': 25,
    'expected_avg_win': 50,  # Large wins
    'expected_avg_loss': 5,
}
```

**Pros**: Large gains on winners, concentrated positions
**Cons**: Low win rate, high drawdowns, requires discipline

---

### System 4: Hybrid Balanced
**Philosophy**: Best of all methods, adaptable

```python
system_4_hybrid = {
    'name': 'Hybrid Balanced',

    # Position Sizing
    'position_sizing_method': 'Hybrid',
    'base_risk_percent': 1.5,
    'conviction_multipliers': {
        5: 1.5,
        4: 1.25,
        3: 1.0,
    },
    'market_multipliers': {
        'bull': 1.5,
        'uptrend': 1.25,
        'neutral': 1.0,
        'downtrend': 0.5,
    },
    'use_atr_for_stops': True,
    'max_risk_per_trade': 3.0,
    'max_position_size_pct': 20,

    # Stop Loss
    'stop_loss_method': 'ATR with Percent Cap',
    'atr_multipliers': {
        5: 1.5,
        4: 2.0,
        3: 2.5,
    },
    'max_stop_percent': {
        5: 5,
        4: 7,
        3: 8,
    },

    # Portfolio Limits
    'max_total_risk': 18,  # Between conservative and aggressive
    'max_positions': 12,
    'max_position_size_pct': 20,

    # Exits
    'exit_method': 'Adaptive',
    'profit_targets': {
        1: {'atr_multiple': 2, 'sell': 33},
        2: {'atr_multiple': 4, 'sell': 33},
    },
    'trailing_stop': 'Best of MA or Chandelier',

    # Pyramiding
    'pyramiding_enabled': True,
    'pyramid_method': 'Selective',  # Only Level 5
    'pyramid_add_at': 0.5,  # 0.5 ATR
    'max_units': 3,

    # Entry Requirements
    'min_conviction': 3,
    'min_fundamental_score': 60,
    'liquidity_tiers': [1, 2, 3],

    # Expected Outcomes
    'expected_win_rate': 38,
    'expected_avg_win': 32,
    'expected_avg_loss': 6,
}
```

**Pros**: Balanced risk/reward, adaptable
**Cons**: More complex to execute

---

### System 5: High Conviction Only
**Philosophy**: Only trade Level 5 setups, very selective

```python
system_5_selective = {
    'name': 'High Conviction Only',

    # Position Sizing
    'position_sizing_method': 'Large Positions',
    'base_risk_percent': 2.5,  # Larger since selective
    'max_risk_per_trade': 3.0,
    'typical_position_size_pct': 20,  # Concentrated

    # Stop Loss
    'stop_loss_method': 'Tight Percentage',
    'stop_loss_percent': 4,  # 4% tight stop

    # Portfolio Limits
    'max_total_risk': 15,  # Lower total (5-6 positions max)
    'max_positions': 6,
    'max_position_size_pct': 25,

    # Exits
    'exit_method': 'Let Winners Run',
    'profit_targets': {
        1: {'pct': 15, 'sell': 25},  # Small profit taking
    },
    'trailing_stop': '20_day_MA',  # Wider trail

    # Entry Requirements
    'min_conviction': 5,  # ONLY Level 5
    'min_fundamental_score': 75,  # EXCELLENT only
    'liquidity_tiers': [1, 2],
    'min_rs_rating': 90,  # Top 10%
    'require_breakout': True,

    # Expected Outcomes
    'expected_win_rate': 50,  # Higher due to selectivity
    'expected_avg_win': 40,
    'expected_avg_loss': 4,
    'trades_per_month': 2,  # Very selective
}
```

**Pros**: Highest quality setups, high win rate
**Cons**: Few opportunities, may miss rallies

---

## Backtest Parameters

### Universe
- Use stocks that passed:
  1. Liquidity Screen (Tier 1-3)
  2. Fundamental Screen (60%+)
  3. Technical Screen (Level 3+)

### Timeframe
- **Primary**: 2020-2024 (5 years, includes bull and bear)
- **Bull Market Test**: 2023-2024
- **Bear Market Test**: 2022
- **Full Cycle**: 2020-2024

### Starting Capital
- $2,000,000

### Transaction Costs
- Commission: $0 (assume zero commission broker)
- Slippage: 0.1% (realistic)
- Market impact: Built into liquidity screen

### Metrics to Track

**Performance Metrics:**
1. Total Return (%)
2. CAGR (%)
3. Sharpe Ratio
4. Sortino Ratio
5. Max Drawdown (%)
6. Recovery Time (days)
7. Win Rate (%)
8. Avg Win (%)
9. Avg Loss (%)
10. Profit Factor

**Risk Metrics:**
11. Max Portfolio Risk Hit (%)
12. Avg Portfolio Risk (%)
13. Largest Single Loss (%)
14. Consecutive Losses (max)
15. Volatility (annual %)

**Trade Metrics:**
16. Total Trades
17. Avg Trade Duration (days)
18. Best Trade (%)
19. Worst Trade (%)
20. R-Multiples Distribution

**System Health:**
21. Trades per Month
22. Avg Position Size (%)
23. Max Positions Held
24. Conviction Level Distribution
25. Sector Exposure

---

## Backtest Approach

### Phase 1: Individual System Testing (Historical)

Test each system independently on historical data:

```python
for system in [system_1, system_2, system_3, system_4, system_5]:
    results = backtest(
        system=system,
        start_date='2020-01-01',
        end_date='2024-12-31',
        initial_capital=2_000_000,
        universe='liquid_fundamental_technical',
    )

    print_report(results)
    save_results(system.name, results)
```

**Output for Each System:**
- Equity curve
- Drawdown curve
- Trade log
- Performance metrics
- Monthly/annual returns

---

### Phase 2: Forward Testing (Walk-Forward)

Simulate how system would perform if run daily:

```python
# Walk-Forward Test
for month in range('2020-01', '2024-12'):
    # Run screeners as of month start
    liquid_stocks = run_liquidity_screen(month)
    fundamental_stocks = run_fundamental_screen(liquid_stocks, month)

    # Run technical screen daily
    for day in month:
        technical_signals = run_technical_screen(fundamental_stocks, day)

        # Apply system rules
        trades = apply_system_rules(system, technical_signals)

        # Execute trades
        execute_trades(trades)

        # Update positions (stops, targets, trails)
        manage_positions(system)

    # End of month review
    calculate_metrics(month)
```

**This simulates real trading:**
- Screeners run on schedule (weekly/monthly)
- Technical signals daily
- Positions managed daily
- Realistic fills and slippage

---

### Phase 3: Monte Carlo Simulation

Test system robustness:

```python
# Run 1,000 simulations
for i in range(1000):
    # Randomize:
    # - Entry timing (±1 day)
    # - Fill prices (±0.2%)
    # - Stop execution (slippage)
    # - Market conditions

    results = backtest_with_randomization(system)
    all_results.append(results)

# Analyze distribution
percentile_5 = results.percentile(5)   # Worst 5%
percentile_50 = results.percentile(50) # Median
percentile_95 = results.percentile(95) # Best 5%

print(f"Expected Range: {percentile_5} to {percentile_95}")
```

**Answers:**
- What's the worst realistic outcome?
- How robust is the system?
- Will it survive bad luck?

---

### Phase 4: Market Condition Analysis

Test each system under different conditions:

```python
market_conditions = {
    'strong_bull': '2023-01 to 2023-12',  # S&P +24%
    'choppy': '2022-01 to 2022-12',       # S&P -18%
    'recovery': '2020-04 to 2020-12',     # Post-COVID
    'steady': '2021-01 to 2021-12',       # S&P +27%
}

for condition, period in market_conditions.items():
    for system in systems:
        results = backtest(system, period)
        print(f"{system.name} in {condition}: {results.return_pct}%")
```

**Goal:** Identify which system works best in which market

---

## Backtest Implementation Plan

### Step 1: Build Backtest Engine

Create `backtest_engine.py`:

```python
class BacktestEngine:
    def __init__(self, system_config, start_date, end_date, capital):
        self.system = system_config
        self.start_date = start_date
        self.end_date = end_date
        self.capital = capital
        self.positions = []
        self.cash = capital
        self.equity_curve = []

    def run(self):
        # Load historical data
        # Run screeners
        # Generate signals
        # Execute trades
        # Manage positions
        # Calculate metrics
        pass

    def calculate_position_size(self, signal):
        # Implement system's position sizing logic
        pass

    def calculate_stop(self, entry, atr, conviction):
        # Implement system's stop logic
        pass

    def check_exits(self, position, current_price, current_date):
        # Check profit targets, stops, trailing stops
        pass

    def generate_report(self):
        # Create comprehensive report
        pass
```

### Step 2: Historical Data Preparation

Need historical data for:
- Daily OHLCV for all stocks (2020-2024)
- Fundamental data (quarterly)
- Sector/industry classifications
- Stock splits/dividends

**Data Sources:**
- yfinance (free, good for initial testing)
- Alpha Vantage (free tier)
- Polygon.io (paid, better quality)

### Step 3: Recreate Historical Screens

Simulate what screeners would have shown:

```python
def historical_liquidity_screen(date):
    """What stocks were liquid as of this date?"""
    # Calculate DDV, turnover, etc. using data up to date
    pass

def historical_fundamental_screen(date):
    """What stocks had strong fundamentals as of this date?"""
    # Use quarterly data available at that time
    # No lookahead bias
    pass

def historical_technical_screen(date):
    """What were technical signals as of this date?"""
    # Calculate conviction based on data available then
    pass
```

**Critical:** No lookahead bias! Only use data available at that time.

### Step 4: Run Backtests

```bash
# Run all systems
python backtest_all_systems.py

# Run specific system
python backtest_engine.py --system turtle --start 2020-01-01 --end 2024-12-31

# Run comparison
python compare_systems.py
```

### Step 5: Generate Reports

Create reports for each system:

1. **Executive Summary**
   - Return, drawdown, Sharpe ratio
   - Win rate, profit factor
   - Recommendation

2. **Detailed Metrics**
   - All 25 metrics
   - Charts and graphs

3. **Trade Log**
   - Every trade with entry/exit
   - P&L per trade
   - Conviction levels

4. **Equity Curve**
   - Daily equity
   - Underwater equity
   - Compared to buy-and-hold

5. **System Analysis**
   - What worked
   - What didn't
   - Suggested improvements

---

## Expected Timeline

### Week 1: Setup
- Build backtest engine framework
- Download historical data
- Test data quality

### Week 2: System 1 & 2
- Backtest Conservative Growth
- Backtest Turtle-Style
- Generate reports

### Week 3: System 3, 4, 5
- Backtest Qullamaggie-Style
- Backtest Hybrid
- Backtest High Conviction Only

### Week 4: Analysis & Optimization
- Compare all systems
- Run Monte Carlo
- Market condition analysis
- Final recommendation

---

## Success Criteria

A system passes if:

1. **Return**: >15% CAGR
2. **Drawdown**: <25% max
3. **Sharpe Ratio**: >1.0
4. **Win Rate**: >30%
5. **Profit Factor**: >1.5
6. **Robustness**: Performs in Monte Carlo 5th percentile
7. **Consistency**: Positive in 70%+ of months
8. **Recovery**: Max drawdown recovered within 6 months

**Ideal System:**
- 20%+ CAGR
- <20% drawdown
- Sharpe >1.5
- 40%+ win rate
- Profit factor >2.0

---

## After Backtest: Implementation

Once we identify the best system(s):

1. **Build Risk Calculator**
   - Integrates with screeners
   - Calculates position sizes
   - Sets stops and targets
   - Manages portfolio risk

2. **Build Trade Manager**
   - Tracks open positions
   - Monitors stops/targets
   - Sends alerts
   - Generates daily reports

3. **Paper Trading**
   - Run system live with paper account
   - Track real-time vs backtest
   - Validate execution

4. **Live Trading (Small)**
   - Start with 10% of capital
   - Verify system works live
   - Scale up gradually

---

## Questions for You

Before building the backtest engine:

1. **Data**: Do you have access to historical data or should I use yfinance (free)?

2. **Timeframe**: 2020-2024 okay? Or go back further?

3. **Priority**: Which system interests you most? Test that first?

4. **Simplification**: Start with simple backtest (just buy/sell, no pyramiding) then add complexity?

5. **Quick Test**: Want me to build a simple backtest for ONE system first to validate approach?

6. **Tools**: Python with pandas/numpy okay? Or want specific backtesting library (backtrader, vectorbt)?

**My Recommendation**:
- Start with System 2 (Turtle-Style) - proven method, clear rules
- Use yfinance for free data
- Build simple backtest first (2023-2024, 2 years)
- If promising, expand to full engine

Ready to build when you are!
