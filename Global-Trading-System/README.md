# Global Multi-Market Trading System

A comprehensive backtesting system that supports trading strategies across multiple global markets:

- **ASX300** (Australia)
- **S&P500** (USA)
- **Russell2000** (USA Small Cap)
- **FTSE 100** (UK)
- **DAX** (Germany)

## Features

### 🌍 Multi-Market Support
- Simultaneous backtesting across 5 major global markets
- Market-specific configurations (timezones, currencies, trading hours)
- Automated symbol list management for each market

### 📈 Strategy Framework
- Extensible base strategy class for easy custom strategy development
- Built-in risk management and position sizing
- Advanced performance analytics and reporting

### 🔧 Built-in Strategies
1. **Global Momentum Strategy**
   - Identifies stocks with strong price momentum
   - Multi-factor scoring system (price, volume, RSI, moving averages)
   - Adaptive position sizing based on signal confidence

2. **Global Breakout Strategy**
   - Detects breakout patterns from consolidation
   - Volume confirmation and ATR-based stops
   - Pattern recognition for tight consolidations

### 📊 Performance Analysis
- Comprehensive performance metrics (Sharpe ratio, drawdown, win rate)
- Benchmark comparison for each market
- Automated chart generation and reporting
- Export to CSV and JSON formats

## Quick Start

### 1. Installation

```bash
git clone <repository-url>
cd Global-Trading-System
pip install -r requirements.txt
```

### 2. Run Sample Backtest

```bash
python run_backtest.py
```

Select option 1 for a quick demonstration with 2 markets and 20 stocks each.

### 3. Configuration

Edit configuration files in the `config/` directory:
- `markets.json`: Market-specific settings
- `strategy_config.json`: Strategy parameters and risk management

## Project Structure

```
Global-Trading-System/
├── config/                 # Configuration files
│   ├── markets.json       # Market definitions
│   └── strategy_config.json # Strategy parameters
├── strategies/            # Strategy implementations
│   ├── momentum_strategy.py
│   └── breakout_strategy.py
├── utils/                 # Core utilities
│   ├── base_strategy.py   # Base strategy framework
│   └── market_data.py     # Data handling
├── data/                  # Downloaded market data (created automatically)
├── results/              # Backtest results (created automatically)
├── logs/                 # Log files (created automatically)
├── global_backtester.py  # Main backtesting engine
├── run_backtest.py       # Execution script
└── requirements.txt      # Dependencies
```

## Usage Examples

### Basic Usage

```python
from global_backtester import GlobalBacktester
from strategies.momentum_strategy import GlobalMomentumStrategy

# Initialize backtester
backtester = GlobalBacktester()

# Create strategy
strategy = GlobalMomentumStrategy(name="My_Momentum", config_path="config/strategy_config.json")

# Run backtest
results = backtester.run_multi_market_backtest(
    strategies=[strategy],
    markets=['SP500', 'ASX300'],
    start_date='2022-01-01',
    end_date='2024-01-01',
    max_symbols_per_market=50
)
```

### Creating Custom Strategies

```python
from utils.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def initialize(self):
        # Set strategy parameters
        self.my_parameter = 20
        
    def generate_signals(self, symbol: str, data: pd.DataFrame):
        # Your signal logic here
        return {'action': 'buy', 'confidence': 0.8, 'reason': 'Custom signal'}
```

## Market Coverage

| Market | Symbols | Benchmark | Currency | Timezone |
|--------|---------|-----------|----------|----------|
| S&P500 | ~500 | SPY | USD | America/New_York |
| ASX300 | ~50 major | VAS.AX | AUD | Australia/Sydney |
| Russell2000 | ~50 proxy | IWM | USD | America/New_York |
| FTSE 100 | ~55 major | ^FTSE | GBP | Europe/London |
| DAX | ~40 major | ^GDAXI | EUR | Europe/Berlin |

## Risk Management Features

- **Position Sizing**: Risk-based allocation (default 2% risk per trade)
- **Stop Losses**: ATR-based or percentage-based stops
- **Portfolio Limits**: Maximum positions and sector exposure
- **Drawdown Controls**: Maximum portfolio risk limits

## Performance Metrics

The system calculates comprehensive performance statistics:

- Total and annualized returns
- Sharpe ratio and volatility
- Maximum drawdown
- Win rate and average win/loss
- Benchmark comparison and excess returns
- Trade-level analysis

## Output Files

Results are automatically saved to the `results/` directory:

- `*_trades_*.csv`: Detailed trade logs
- `*_portfolio_*.csv`: Portfolio value over time
- `*_stats_*.json`: Performance statistics
- `backtest_summary_*.csv`: Summary across all strategies/markets
- `performance_chart_*.png`: Visualization charts

## Configuration

### Market Configuration (`config/markets.json`)

```json
{
    "markets": {
        "SP500": {
            "name": "S&P 500",
            "currency": "USD",
            "timezone": "America/New_York",
            "benchmark": "SPY",
            "symbol_suffix": ""
        }
    }
}
```

### Strategy Configuration (`config/strategy_config.json`)

```json
{
    "default_parameters": {
        "initial_capital": 100000,
        "commission": 0.001,
        "max_positions": 20,
        "risk_per_trade": 0.02
    }
}
```

## Requirements

- Python 3.8+
- pandas >= 1.5.0
- numpy >= 1.21.0
- yfinance >= 0.2.0
- talib-binary >= 0.4.0
- matplotlib >= 3.5.0
- seaborn >= 0.11.0

## Limitations

- Data source: Yahoo Finance (free but may have limitations)
- Historical data only (not for live trading)
- Symbol lists are curated subsets, not complete market indices
- No corporate actions or dividend adjustments in basic version

## Future Enhancements

- [ ] Live trading integration
- [ ] More sophisticated risk models
- [ ] Machine learning strategy templates
- [ ] Alternative data sources
- [ ] Portfolio optimization
- [ ] Sector rotation strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your strategy or enhancement
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and research purposes. Please ensure compliance with data provider terms of service and local regulations before using for commercial purposes.

## Disclaimer

This software is for educational and research purposes only. Past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor before making investment decisions.