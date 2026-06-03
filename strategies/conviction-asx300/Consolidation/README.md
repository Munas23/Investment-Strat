# Consolidation Conviction Strategy Backtest

## Overview

This folder contains a backtesting implementation of your **Consolidation Conviction Scanner** using the Lumibot framework, based on the 5LC backtesting approach.

## Strategy Focus

The strategy targets stocks **AFTER** their big moves, during consolidation periods:

- **Post-Move Targeting**: Looks for stocks that have had strong 3-6 month performance (30%+ gains)
- **Consolidation Detection**: Identifies stocks currently consolidating with low or shrinking ATR
- **Reduced Recent Momentum**: Focuses on stocks with minimal recent movement (indicating consolidation)
- **Professional Risk Management**: Optimized for consolidation patterns with tighter stops

## Key Features

### Consolidation Criteria
- **3-6 Month Performance**: Minimum 30% gain requirement
- **ATR Analysis**: Shrinking/low ATR relative to stock's own history
- **Recent Movement**: Rewards LOW recent momentum (2-12% recent gains)
- **Volume Patterns**: Normal or decreasing volume during consolidation

### Position Sizing by Conviction Level
- **Level 2 (Fair)**: 15% position
- **Level 3 (Good)**: 20% position  
- **Level 4 (High)**: 28% position
- **Level 5 (Max)**: 35% position

### Risk Management (Optimized for Consolidation)
- **Stop Loss**: 8% (tighter than momentum strategies)
- **Profit Target**: 40% (realistic for post-move stocks)
- **Trailing Stop**: Activates at 15% gain with 10% trail
- **Max Hold**: 6 months (shorter than momentum strategies)

## Files

- `consolidation_conviction_strategy.py` - Main backtesting strategy
- `requirements.txt` - Required Python packages
- `README.md` - This documentation

## Usage

1. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Backtest**:
   ```python
   python consolidation_conviction_strategy.py
   ```

3. **Review Results**:
   - CSV trade log: `consolidation_conviction_trades_YYYYMMDD_HHMMSS.csv`
   - Pyfolio analysis: `pyfolio_reports/` folder
   - Console output with performance metrics

## Strategy Logic

### Screening Process
1. **Universe**: ~150 liquid US stocks across sectors
2. **Basic Filters**: Price > $5, Volume > 100K, sufficient history
3. **Performance Filter**: 30%+ gains over 3-6 months
4. **Consolidation Analysis**: ATR contraction and low recent movement
5. **Conviction Scoring**: 0-100 points across 4 factors

### Conviction Factors
1. **Medium-term Performance** (30 points): Rewards 30%+ 3-6M gains
2. **ATR Consolidation** (35 points): Rewards contracting volatility
3. **Recent Momentum** (20 points): Rewards LOW recent movement  
4. **Volume Patterns** (15 points): Rewards normal consolidation volume

### Entry Criteria
- Conviction Level 2+ required for entry
- Maximum 8 positions simultaneously
- Position sizing based on conviction level
- Fresh data validation before each entry

### Exit Criteria
1. **Stop Loss**: 8% loss
2. **Profit Target**: 40% gain
3. **Trailing Stop**: After 15% gain, trail by 10%
4. **Time Exit**: 6 months maximum hold

## Backtesting Parameters

- **Period**: 2020-2024 (5 years)
- **Initial Capital**: $100,000
- **Benchmark**: SPY (S&P 500 ETF)
- **Commission**: Included in Lumibot framework
- **Screening Frequency**: Every 2 weeks

## Expected Characteristics

This strategy is designed for:
- **Lower Frequency**: Fewer trades than momentum strategies
- **Higher Win Rate**: Post-move consolidations have higher success rates
- **Moderate Returns**: Targeting 40% gains with 8% risk per trade
- **Risk Management**: Emphasis on capital preservation during consolidation

## Differences from Traditional Momentum Strategies

1. **Timing**: AFTER the move vs DURING the move
2. **ATR Focus**: Contracting volatility vs expanding volatility  
3. **Recent Performance**: LOW recent gains vs HIGH recent gains
4. **Hold Period**: Shorter (6M) vs longer (12M)
5. **Stops**: Tighter (8%) due to consolidation nature

## Analysis Output

The backtest generates:
- **Trade Log**: Detailed CSV with entry/exit reasons
- **Pyfolio Reports**: Professional risk/return analysis
- **Performance Metrics**: Returns, Sharpe, drawdown vs S&P 500
- **Debug Statistics**: Screening and signal generation stats

## Next Steps

After running the backtest:
1. Review trade log for pattern validation
2. Analyze Pyfolio reports for risk characteristics
3. Compare results to your live scanner performance
4. Consider parameter optimization based on results
5. Validate against different market periods

---

**Note**: This is a research tool. Past performance does not guarantee future results. Use proper risk management in live trading.