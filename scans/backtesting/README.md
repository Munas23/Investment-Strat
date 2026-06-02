# Comprehensive Backtesting System

Complete backtesting framework for testing all 5 trading systems from BACKTEST_SYSTEMS_PLAN.md with integrated position sizing.

## Structure

```
backtesting/
├── backtest_engine.py          # Core backtesting engine
├── strategies/                  # Individual trading systems
│   ├── system_1_conservative.py    # Minervini-style
│   ├── system_2_turtle.py          # Turtle ATR-based
│   ├── system_3_qullamaggie.py     # Aggressive momentum
│   ├── system_4_hybrid.py          # Balanced approach
│   └── system_5_selective.py       # High conviction only
├── utils/                       # Helper functions
│   ├── data_handler.py             # Historical data management
│   └── performance_analyzer.py     # Metrics and reporting
├── results/                     # Backtest outputs
│   ├── *_trades.csv               # Trade logs
│   ├── *_equity.csv               # Equity curves
│   └── *_metrics.json             # Performance metrics
├── data/                        # Cached historical data
└── run_all_backtests.py        # Master runner script
```

## Systems to Test

### System 1: Conservative Growth (Minervini)
- Base risk: 1.0%
- Tight stops (3-5%)
- Min conviction: Level 4
- Max 10 positions

### System 2: Turtle ATR-Based
- Base risk: 1.5%
- ATR stops (2x multiplier)
- Pyramiding enabled
- Max 12 positions

### System 3: Qullamaggie Aggressive
- Base risk: 2.0%
- Pattern-based stops
- Large positions (20-25%)
- Max 15 positions

### System 4: Hybrid Balanced
- Base risk: 1.5%
- ATR with caps
- Adaptive exits
- Max 12 positions

### System 5: High Conviction Only
- Base risk: 2.5%
- Level 5 only
- Max 6 positions
- Let winners run

## Quick Start

```bash
cd scans/backtesting

# Run single system
python strategies/system_1_conservative.py

# Run all systems
python run_all_backtests.py

# Compare results
python compare_systems.py
```

## Configuration

Edit system parameters in each strategy file or use config.json:

```json
{
  "account_size": 2000000,
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "transaction_cost_pct": 0.1,
  "slippage_pct": 0.05,
  "risk_free_rate": 3.0
}
```

## Output Files

Each backtest generates:

1. **trades.csv** - Complete trade log
2. **equity.csv** - Daily equity curve
3. **metrics.json** - Performance statistics

## Performance Metrics

- Total Return %
- CAGR
- Sharpe Ratio
- Sortino Ratio
- Max Drawdown
- Win Rate
- Profit Factor
- Avg R-Multiple
- Expectancy

## Integration

Uses your existing:
- Position sizing calculator
- Risk management framework
- Screening results (for universe)

## Next Steps

1. Run backtests on 2020-2024 data
2. Analyze results
3. Compare systems
4. Choose best system
5. Paper trade for validation
