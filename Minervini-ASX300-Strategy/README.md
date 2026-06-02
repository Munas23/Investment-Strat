# Mark Minervini's Complete Championship Strategy - ASX300 Version

This folder contains a complete implementation of Mark Minervini's championship trading methodology adapted for the **ASX300 market**, combining **fundamental screening** with **technical timing** - the exact approach that made him a 2-time US Investing Champion.

## 🏆 Strategy Overview

Mark Minervini's complete methodology consists of three critical components adapted for Australian markets:

### 1. **Fundamental Screening (Quality Filter - ASX Adapted)**
- Only trade stocks with >60% fundamental score
- High earnings growth (>18% quarterly)
- Strong revenue growth (>15% quarterly) 
- Excellent ROE (>15%)
- Low debt-to-equity (<0.3)
- Proper market cap range ($300M - $50B AUD)
- Minimum price >$5 AUD (avoids penny stocks)
- Adequate liquidity (>100K daily volume)

### 2. **Technical Breakout Timing (Precise Entries)**
- Wait for breakout signals from fundamentally strong ASX stocks
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
- **`minervini_asx300_strategy.py`** - Complete strategy with Lumibot backtesting for ASX300 (RECOMMENDED)
- **`minervini_fundamentals.py`** - Fundamental screening system adapted for ASX markets
- **`requirements.txt`** - Python dependencies (including Lumibot)

## 🚀 Quick Start

### Installation & Run
```bash
pip install -r requirements.txt
python minervini_asx300_strategy.py
```

This will:
1. Screen the **ASX300** for fundamental leaders (>60% score)
2. Apply technical breakout timing with conviction levels (1-5)
3. Execute championship risk management (7% stops, 50% targets)
4. Generate detailed backtest results with trade-by-trade analysis
5. Benchmark against VAS.AX (Vanguard Australian Shares Index ETF)

## 🎯 Key Features

### Championship Parameters (ASX Adapted)
```python
max_positions = 6           # Concentrated portfolio
min_position_size = 0.20    # 20% minimum positions
max_position_size = 0.40    # 40% maximum positions
stop_loss_pct = 0.07        # 7% stops
profit_target = 0.50        # 50% targets
fundamental_threshold = 60.0 # Only quality ASX stocks
benchmark = "VAS.AX"        # ASX300 benchmark
```

### ASX300 Symbol Universe
The strategy screens across major ASX300 stocks including:
- **Banks**: CBA.AX, ANZ.AX, WBC.AX, NAB.AX
- **Mining**: BHP.AX, RIO.AX, FMG.AX, NCM.AX
- **Healthcare**: CSL.AX, COH.AX, RMD.AX
- **Technology**: APT.AX, XRO.AX, WTC.AX
- **Retail**: WOW.AX, COL.AX, JBH.AX
- **REITs**: SCG.AX, TCL.AX, GMG.AX
- **And 70+ other quality ASX300 companies**

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

Based on testing, this ASX300 adaptation typically shows:
- **Home Run Trades**: Multiple 50%+ winners from quality ASX stocks
- **High Win Quality**: Big winners offset small losses
- **Market Competition**: Competitive with VAS.AX buy-and-hold
- **Professional Execution**: Championship-level methodology for ASX

## 🔬 How It Works

### Phase 1: ASX300 Fundamental Screening
```python
# Screen for quality ASX companies
asx300_symbols = get_asx300_symbols()
fundamental_leaders = get_fundamental_leaders(asx300_symbols)
# Only trade ASX stocks with >60% fundamental score
```

### Phase 2: Technical Timing
```python
# Generate conviction-based signals (0-5 levels)
conviction_signals = generate_complete_signals(asx_data)
# Enter only on high-conviction breakouts
```

### Phase 3: Risk Management
```python
# Position size based on conviction + fundamentals
position_size = base_position_pct * conviction_level
# Professional exits: stops, targets, trails
# Benchmark against VAS.AX performance
```

## 🎓 Educational Value

This ASX300 implementation demonstrates:
- **Why fundamentals matter**: Quality ASX stocks produce bigger moves
- **Importance of timing**: Technical breakouts provide precise entries
- **Risk management**: How champions protect capital while hunting home runs
- **Position sizing**: Concentration in best ASX ideas drives performance
- **Complete methodology**: Integration of all Minervini principles for Australian markets

## 🇦🇺 ASX Market Adaptations

### Currency & Pricing
- All prices in Australian Dollars (AUD)
- Minimum price threshold: $5 AUD (vs $15 USD for US markets)
- Market cap range: $300M - $50B AUD

### Liquidity Requirements
- Minimum daily volume: 100,000 shares (vs 500,000 for US)
- Adapted for smaller ASX market size

### Benchmark
- Uses VAS.AX (Vanguard Australian Shares Index ETF) as benchmark
- Represents broader ASX300 performance

### Symbol Format
- All symbols include .AX suffix for Yahoo Finance compatibility
- Examples: CBA.AX, BHP.AX, CSL.AX

## ⚠️ Important Notes

1. **Fundamental First**: Never ignore the fundamental screening
2. **Patience Required**: Wait for high-conviction setups
3. **Risk Management**: 7% stops are non-negotiable
4. **Concentration**: Maximum 6 positions, not 20+
5. **Home Run Mentality**: Hunt for 50%+ winners, not 10% gains
6. **ASX Hours**: Consider ASX trading hours (10:00 AM - 4:00 PM AEST)

## 🏆 Championship Insight

> *"The key to my success isn't just technical analysis - it's finding fundamentally superior companies at the exact moment they're about to make big moves. Quality + Timing + Risk Management = Championships."* - Mark Minervini

This strategy represents the complete methodology that won two US Investing Championships, now adapted for the Australian ASX300 market.

## 🔧 Customization

You can modify key parameters for ASX conditions:
- `fundamental_threshold`: Adjust quality requirements
- `profit_target`: Change home run target  
- `stop_loss_pct`: Modify risk tolerance
- `max_positions`: Adjust concentration level
- `asx300_symbols`: Modify stock universe

## 📈 Next Steps

1. **Run the ASX300 strategy** to understand the methodology
2. **Study the fundamental screening** to see quality requirements for ASX stocks
3. **Analyze the results** to understand home run generation potential
4. **Consider paper trading** before live implementation
5. **Study Minervini's books** for deeper understanding
6. **Monitor ASX market conditions** and sector rotations

## 🇦🇺 ASX-Specific Considerations

- **Sector Concentration**: ASX300 is heavily weighted toward banks and mining
- **Dividend Focus**: Many ASX stocks are dividend-focused vs growth
- **Market Hours**: Strategy runs during ASX trading hours
- **Currency**: All calculations in AUD
- **Liquidity**: Adapted thresholds for smaller market size

---

*This implementation is for educational purposes and demonstrates professional-level trading methodology adapted for Australian markets. Always do your own research and consider consulting with a financial advisor familiar with ASX regulations.*