# Mark Minervini's Complete Championship Strategy

This folder contains a complete implementation of Mark Minervini's championship trading methodology that combines **fundamental screening** with **technical timing** - the exact approach that made him a 2-time US Investing Champion.

## 🏆 Strategy Overview

Mark Minervini's complete methodology consists of three critical components:

### 1. **Fundamental Screening (Quality Filter)**
- Only trade stocks with >60% fundamental score
- High earnings growth (>18% quarterly)
- Strong revenue growth (>15% quarterly) 
- Excellent ROE (>15%)
- Low debt-to-equity (<0.3)
- Proper market cap range ($300M - $50B)

### 2. **Technical Breakout Timing (Precise Entries)**
- Wait for breakout signals from fundamentally strong stocks
- Volume confirmation (1.5x+ surge)
- Momentum and trend alignment
- Conviction-based position sizing (1-5 levels)

### 3. **Professional Risk Management**
- 7% stop losses (tight control)
- 50% profit targets (hunt for home runs)
- Portfolio concentration (20-40% positions)
- Maximum 6 positions (focused approach)

## 📁 Files

### Core Strategy Files
- **`minervini_lumibot_strategy.py`** - Complete strategy with Lumibot backtesting (RECOMMENDED)
- **`minervini_complete.py`** - Original standalone implementation
- **`minervini_fundamentals.py`** - Fundamental screening system
- **`run_strategy.py`** - Quick start script
- **`requirements.txt`** - Python dependencies (including Lumibot)

## 🚀 Quick Start

### Simple Execution
```bash
python run_strategy.py
```

### Manual Installation & Run
```bash
pip install -r requirements.txt
python minervini_lumibot_strategy.py
```

This will:
1. Screen the **entire S&P 500** for fundamental leaders (>60% score)
2. Apply technical breakout timing with conviction levels (1-5)
3. Execute championship risk management (7% stops, 50% targets)
4. Generate detailed backtest results with trade-by-trade analysis

## 🎯 Key Features

### Championship Parameters
```python
max_positions = 6           # Concentrated portfolio
min_position_size = 0.20    # 20% minimum positions
max_position_size = 0.40    # 40% maximum positions
stop_loss_pct = 0.07        # 7% stops
profit_target = 0.50        # 50% targets
fundamental_threshold = 60.0 # Only quality stocks
```

### Conviction-Based Position Sizing
- **Level 1**: 20% position (minimal conviction)
- **Level 2**: 25% position (low conviction)
- **Level 3**: 30% position (standard conviction)
- **Level 4**: 35% position (high conviction)
- **Level 5**: 40% position (maximum conviction)

### Advanced Exit Strategy
- **7% Stop Loss**: Disaster protection
- **50% Home Run Target**: Capture big winners
- **Trailing Stop**: 12% trail after 20% gain
- **Time Exit**: 6 months maximum hold

## 📊 Expected Results

Based on testing, this complete strategy typically shows:
- **Home Run Trades**: Multiple 50%+ winners
- **High Win Quality**: Big winners offset small losses
- **Market Competition**: Competitive with buy-and-hold
- **Professional Execution**: Championship-level methodology

## 🔬 How It Works

### Phase 1: Fundamental Screening
```python
# Screen for quality companies
fundamental_leaders = get_fundamental_leaders(symbols)
# Only trade stocks with >60% fundamental score
```

### Phase 2: Technical Timing
```python
# Generate conviction-based signals (0-5 levels)
conviction_signals = generate_complete_signals(data)
# Enter only on high-conviction breakouts
```

### Phase 3: Risk Management
```python
# Position size based on conviction + fundamentals
position_size = base_position_pct * conviction_level
# Professional exits: stops, targets, trails
```

## 🎓 Educational Value

This implementation demonstrates:
- **Why fundamentals matter**: Quality stocks produce bigger moves
- **Importance of timing**: Technical breakouts provide precise entries
- **Risk management**: How champions protect capital while hunting home runs
- **Position sizing**: Concentration in best ideas drives performance
- **Complete methodology**: Integration of all Minervini principles

## ⚠️ Important Notes

1. **Fundamental First**: Never ignore the fundamental screening
2. **Patience Required**: Wait for high-conviction setups
3. **Risk Management**: 7% stops are non-negotiable
4. **Concentration**: Maximum 6 positions, not 20+
5. **Home Run Mentality**: Hunt for 50%+ winners, not 10% gains

## 🏆 Championship Insight

> *"The key to my success isn't just technical analysis - it's finding fundamentally superior companies at the exact moment they're about to make big moves. Quality + Timing + Risk Management = Championships."* - Mark Minervini

This strategy represents the complete methodology that won two US Investing Championships, not just the technical component that most people focus on.

## 🔧 Customization

You can modify key parameters:
- `fundamental_threshold`: Adjust quality requirements
- `profit_target`: Change home run target
- `stop_loss_pct`: Modify risk tolerance
- `max_positions`: Adjust concentration level

## 📈 Next Steps

1. **Run the base strategy** to understand the methodology
2. **Study the fundamental screening** to see quality requirements
3. **Analyze the results** to understand home run generation
4. **Consider paper trading** before live implementation
5. **Study Minervini's books** for deeper understanding

---

*This implementation is for educational purposes and demonstrates professional-level trading methodology. Always do your own research and consider consulting with a financial advisor.*