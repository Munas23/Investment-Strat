# Enhanced Flag Pattern Trading Strategy

This folder contains an enhanced version of the trading backtesting system that integrates the risk management logic from `place_trade.py` with the flag pattern strategy from `lumbot_og.py`.

## Files

### Core Components

1. **`risk_manager.py`** - Enhanced risk management system
   - Integrates position sizing logic from `place_trade.py`
   - Adds portfolio-level risk controls
   - Implements proper input validation
   - Tracks active positions and stop losses

2. **`enhanced_flag_strategy.py`** - Improved trading strategy
   - Uses `risk_manager.py` for all position sizing decisions
   - Implements actual stop loss orders (not just MA exits)
   - Enhanced error handling and logging
   - Better integration between risk management and strategy logic

3. **`test_risk_manager.py`** - Comprehensive test suite
   - Unit tests for all risk management functions
   - Manual testing demonstrations
   - Input validation testing

## Key Improvements

### From Original `lumbot_og.py`:
- ✅ **Actual Stop Losses**: Implements real stop loss orders instead of only MA-based exits
- ✅ **Portfolio Risk Management**: Tracks total exposure and position limits
- ✅ **Better Position Sizing**: Uses enhanced logic from `place_trade.py` with proper validation
- ✅ **Input Validation**: Validates all inputs before processing
- ✅ **Error Handling**: Comprehensive error handling throughout

### From Original `place_trade.py`:
- ✅ **Portfolio Integration**: Connects with actual trading strategy
- ✅ **Position Tracking**: Maintains active position database
- ✅ **Risk Limits**: Enforces maximum position sizes and exposure limits
- ✅ **Proper Rounding**: Uses proper rounding instead of truncating shares
- ✅ **Edge Case Handling**: Handles stocks that exceed position limits

## Risk Management Features

### Position Sizing
- Risk-based position sizing (default 2% account risk per trade)
- Maximum position size limits (default 10% of portfolio)
- Validates sufficient capital before placing trades
- Handles expensive stocks that exceed position limits

### Portfolio Controls
- Maximum number of positions (default 10)
- Portfolio exposure tracking
- Available capital calculations
- Prevents duplicate positions

### Stop Loss Management
- Calculates stop loss levels based on percentage
- Tracks stop losses for all active positions
- Automatically triggers exits when stop loss hit
- Validates stop loss calculations

### Input Validation
- Validates ticker symbols (non-empty strings)
- Ensures positive prices and valid percentages
- Checks risk and stop loss percentages within reasonable ranges
- Prevents invalid trade configurations

## Usage

### Running Tests
```bash
cd testing
python test_risk_manager.py
```

### Running Backtest
```bash
cd testing
python enhanced_flag_strategy.py
```

## Configuration

### Risk Manager Parameters
```python
risk_manager = RiskManager(
    account_balance=100000,     # Starting capital
    default_risk_percent=2,     # Risk 2% per trade
    max_position_size=0.10,     # Max 10% per position
    max_positions=10            # Max 10 positions
)
```

### Strategy Parameters
```python
# Flag pattern detection
flagpole_period = 60            # Lookback for trend
flagpole_min_gain = 0.30        # Minimum 30% gain required

# Moving averages
ma_fast = 10                    # Fast MA period
ma_medium = 20                  # Medium MA period
ma_slow = 50                    # Slow MA period

# Risk management
stop_loss_percent = 8           # 8% stop loss
```

## Example Trade Flow

1. **Screen**: Strategy identifies flag pattern candidate
2. **Validate**: Risk manager validates all inputs
3. **Calculate**: Determines position size based on risk limits
4. **Check Limits**: Ensures position fits within portfolio constraints
5. **Execute**: Places trade with calculated position size
6. **Track**: Adds position to active tracking with stop loss
7. **Monitor**: Continuously monitors for stop loss triggers
8. **Exit**: Executes stop loss or MA-based exit as appropriate

## Testing Results

All unit tests pass:
- ✅ Valid trade calculation
- ✅ Input validation 
- ✅ Position limits enforcement
- ✅ Duplicate position prevention
- ✅ Portfolio exposure tracking
- ✅ Stop loss checking
- ✅ Position size limits

Manual testing demonstrates:
- Proper risk-based position sizing
- Position limit enforcement
- Portfolio exposure tracking
- Stop loss trigger detection
- Input validation error handling

## Next Steps

For production use, consider adding:
- Commission/fee modeling
- Slippage calculations
- Correlation analysis between positions
- Maximum drawdown controls
- Performance attribution analysis
- Real-time data integration