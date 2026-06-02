# 5-LEVEL CONVICTION DAILY SCANNER

**Professional-grade momentum scanner implementing the proven 5LC strategy with quality-first fundamental screening and technical breakout detection.**

## 🚀 Quick Start

1. **Test the scanner first:**
   ```bash
   python test_scanner.py
   ```

2. **Run daily scans:**
   ```bash
   python 5lc_daily_scanner.py
   ```

3. **Review results in generated CSV files**

---

## 📁 Files Overview

### Core Scanner
- **`5lc_daily_scanner.py`** - Main scanner with full S&P 500 + ASX300 coverage
- **`test_scanner.py`** - Validation script to test functionality
- **`fundamental_screening_guide.md`** - Detailed explanation of screening methodology

### Documentation
- **`README.md`** - This overview file

---

## 🎯 Strategy Overview

The 5-Level Conviction (5LC) strategy is a **quality-first momentum system** that combines:

1. **Fundamental Quality Screening** (60% minimum score required)
2. **Technical Breakout Timing** (trend strength + volume confirmation)
3. **Conviction-Based Position Sizing** (20% to 40% positions)
4. **Professional Risk Management** (7% stops, 50% targets)

### Conviction Levels
- **Level 1 (20% position)**: 25-39 conviction points - Minimal signal
- **Level 2 (25% position)**: 40-54 conviction points - Low conviction
- **Level 3 (30% position)**: 55-69 conviction points - Standard conviction
- **Level 4 (35% position)**: 70-84 conviction points - High conviction
- **Level 5 (40% position)**: 85+ conviction points - Maximum conviction

---

## 🔍 Fundamental Screening (150 Points Total)

Our **quality-first approach** screens stocks across 6 categories:

### 1. Market Cap & Price (15 points)
- **US**: $300M-$50B market cap, $15+ price
- **AUS**: $500M-$50B market cap, $5+ price

### 2. Volume (5 points)
- **US**: 500K+ daily volume
- **AUS**: 100K+ daily volume

### 3. Profitability (35 points)
- **ROE**: 15%+ required (up to 20 points)
- **Profit Margin**: 10%+ required (up to 15 points)

### 4. Growth (50 points) - **MOST CRITICAL**
- **Revenue Growth**: 15%+ quarterly required (up to 25 points)
- **Earnings Growth**: 18%+ quarterly required (up to 25 points)

### 5. Financial Strength (25 points)
- **Current Ratio**: 1.5+ required (up to 15 points)
- **Debt/Equity**: 0.3 maximum (up to 10 points)

### 6. Institutional Ownership (20 points)
- **Sweet Spot**: 40-80% institutional ownership
- **Optimal**: 50-70% for maximum points

**Minimum Score**: 90+ points (60%) required to proceed to technical analysis

---

## ⚡ Technical Analysis & Conviction Scoring

Only stocks passing fundamental screening advance to technical analysis:

### Trend Strength Requirements (60+ points required)
- **Moving Average Alignment** (40 pts): Price > SMA20 > SMA50 > SMA200
- **Price Position vs MAs** (20 pts): Distance above key moving averages
- **Momentum Quality** (20 pts): Multi-timeframe momentum alignment
- **Proximity to Highs** (20 pts): Position relative to recent highs

### Conviction Scoring (25-100 points)
- **Breakout Power** (0-25 pts): 1%+ above 20-day high, 2%+ above 50-day high
- **Volume Confirmation** (0-30 pts): 1.2x to 2x+ volume surge
- **Momentum Alignment** (0-25 pts): 5-day, 20-day, 50-day momentum
- **Trend Quality Bonus** (0-20 pts): Extra points for strong trends

---

## 🌍 Market Coverage

### S&P 500 (US Market)
- **Complete coverage**: 500+ symbols automatically loaded from Wikipedia
- **Symbol handling**: Automatic conversion for Yahoo Finance compatibility
- **Fallback list**: 50+ major symbols if Wikipedia fails

### ASX300 (Australian Market)
- **Comprehensive coverage**: 200+ major ASX symbols across all sectors
- **Sector diversity**: Banks, miners, healthcare, tech, retail, REITs
- **Growth focus**: Includes emerging growth names and established leaders

---

## 📊 Output Files

### Main Results
- **`5lc_daily_scan_YYYYMMDD_HHMMSS.csv`** - Complete scan results

### Filtered Results
- **`5lc_daily_scan_YYYYMMDD_HHMMSS_TRADE_READY.csv`** - Level 2+ conviction only
- **`5lc_daily_scan_YYYYMMDD_HHMMSS_HIGH_CONVICTION.csv`** - Level 4+ conviction only

### Log File
- **`5lc_daily_scanner.log`** - Detailed scanning logs with debug information

---

## 🛡️ Risk Management

### Position Sizing
- **Dynamic sizing**: Based on conviction level (20% to 40%)
- **Maximum positions**: Recommended 6 positions maximum
- **Portfolio heat**: Monitor total exposure across all positions

### Stop Losses & Targets
- **Stop Loss**: 7% maximum loss (tight control)
- **Profit Target**: 50% gain target (hunt for large moves)
- **Trailing Stop**: 12% trail after 20% gain
- **Time Exit**: 6-month maximum hold period

---

## 🚀 Usage Instructions

### 1. Initial Setup
```bash
# Install required packages
pip install yfinance pandas numpy matplotlib

# Test the scanner
cd updated_scan
python test_scanner.py
```

### 2. Daily Scanning
```bash
# Run the scanner
python 5lc_daily_scanner.py

# Choose market:
# 1 = US Market (S&P 500)
# 2 = Australian Market (ASX300)
# 3 = Both Markets
```

### 3. Review Results
- Check console output for immediate summary
- Review CSV files for detailed analysis
- Focus on Level 2+ stocks for trading
- Pay special attention to Level 4+ high conviction alerts

---

## 📈 Expected Performance

Based on historical backtesting across 834 trades:

### Conviction Level Performance
- **Level 1**: 23.5% achieve 50%+ gains
- **Level 2**: 26.1% achieve 50%+ gains
- **Level 3**: 24.3% achieve 50%+ gains (optimal risk/reward)
- **Level 4**: 18.8% achieve 50%+ gains (smaller sample)
- **Level 5**: Extremely rare (professional standards)

### Market Performance
- **ASX300**: 656% total return in backtests
- **US Markets**: 97% average return across strategies
- **Overall**: Quality-first approach generates consistent alpha

---

## 🔧 Technical Details

### Data Sources
- **Yahoo Finance API**: Real-time fundamental and technical data
- **Wikipedia S&P 500**: Automatic symbol list updates
- **Manual ASX300**: Curated comprehensive symbol list

### Performance Optimizations
- **Rate limiting**: 0.1-second delays between API calls
- **Error handling**: Graceful handling of data issues
- **Progress tracking**: Real-time scan progress updates
- **Logging**: Comprehensive debug and info logging

### System Requirements
- **Python 3.7+**
- **Internet connection** for data retrieval
- **~2-3 hours** for full dual-market scan
- **Sufficient disk space** for CSV exports

---

## ⚠️ Important Notes

### Market Hours
- **Best results**: Run during market hours or shortly after close
- **Data freshness**: Yahoo Finance data may lag by 15-20 minutes
- **Weekend runs**: Limited data updates over weekends

### Rate Limiting
- **Built-in delays**: Scanner includes appropriate delays
- **Respectful usage**: Don't modify timing without consideration
- **API stability**: Yahoo Finance free tier has usage limits

### Quality Assurance
- **Always test first**: Run `test_scanner.py` before full scans
- **Validate results**: Review high-conviction picks manually
- **Paper trade**: Test strategy with small positions initially

---

## 🎯 Trading Workflow

### Daily Routine
1. **Morning**: Run scanner after market open
2. **Review**: Focus on Level 2+ conviction stocks
3. **Research**: Manually verify high-conviction picks
4. **Execute**: Enter positions with appropriate sizing
5. **Monitor**: Track stops, targets, and trailing stops

### Position Management
1. **Entry**: Buy on conviction signal confirmation
2. **Stop**: Set 7% stop loss immediately
3. **Target**: Scale out at 50% gains or trail stops
4. **Review**: Weekly review of all positions

---

## 📞 Support & Development

### Customization
- **Thresholds**: Modify fundamental/technical thresholds in code
- **Markets**: Add new markets by updating symbol lists
- **Scoring**: Adjust conviction scoring weights as needed

### Troubleshooting
- **Data issues**: Check internet connection and Yahoo Finance status
- **Symbol errors**: Review symbol formatting (especially .AX suffix)
- **Performance**: Reduce symbol lists for faster testing

---

## 🏆 Success Metrics

### Quality Indicators
- **Fundamental pass rate**: ~10-20% of all stocks
- **Technical pass rate**: ~5-10% of fundamental qualifiers
- **Final conviction rate**: ~2-5% of all stocks scanned

### Performance Tracking
- **Win rate**: Track percentage of profitable trades
- **Average gains**: Monitor average return per conviction level
- **Large gains**: Count 50%+ winners (target: 20%+ of trades)

---

## 📚 Additional Resources

### Strategy Education
- **5LC Methodology**: Study original backtesting reports
- **Minervini Principles**: Mark Minervini's momentum trading concepts
- **Risk Management**: Professional position sizing techniques

### Market Research
- **Sector Analysis**: Understand sector rotation and timing
- **Earnings Seasons**: Align scans with earnings calendars
- **Market Conditions**: Adapt strategy to market regime

---

**Remember: This is a quality-first momentum system. Patience for high-quality setups generates superior risk-adjusted returns. Quality first, timing second, conviction third.**