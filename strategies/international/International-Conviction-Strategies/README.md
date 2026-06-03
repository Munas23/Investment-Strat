# International Conviction Strategies

Global implementation of our proven 5-Level Conviction trading system across UK, German, and Hong Kong markets.

## 🌍 Markets Covered

### 🇬🇧 United Kingdom - `uk_conviction_strategy.py`
- **Universe**: FTSE 100/250 major stocks
- **Currency**: GBP (British Pounds)  
- **Benchmark**: VUKE.L (FTSE 100 ETF)
- **Adaptations**: Lower volume threshold (50K), UK-specific fundamentals

### 🇩🇪 Germany - `germany_conviction_strategy.py`  
- **Universe**: DAX major stocks
- **Currency**: EUR (Euros)
- **Benchmark**: EXS1.DE (EURO STOXX 50 ETF)
- **Adaptations**: Standard thresholds, German market structure

### 🇭🇰 Hong Kong - `hongkong_conviction_strategy.py`
- **Universe**: HSI major stocks  
- **Currency**: HKD (Hong Kong Dollars)
- **Benchmark**: 2800.HK (Tracker Fund)
- **Adaptations**: Higher volume threshold (1M), adjusted fundamentals for volatility

## 🎯 Core Methodology

### 5-Level Conviction System
All markets use the same core conviction framework:

| Level | Position Size | Conviction Criteria |
|-------|---------------|-------------------|
| **1** | 20% | Minimal conviction (20-30 points) |
| **2** | 25% | Low conviction (30-45 points) |
| **3** | 30% | Standard conviction (45-60 points) |
| **4** | 35% | High conviction (60-80 points) |
| **5** | 40% | Maximum conviction (80+ points) |

### Quality-First Screening
- **Fundamental threshold**: >60% quality score
- **ROE requirement**: >12-15% (market adjusted)
- **Revenue growth**: >8-15% (market adjusted)  
- **Debt management**: <40-50% debt-to-equity
- **Market cap filters**: Appropriate for each market

### Professional Risk Management
- **Stop loss**: 7% across all markets
- **Profit target**: 50% across all markets
- **Trailing stop**: 12% after 20% profit
- **Time exit**: 360 days maximum hold

## 🚀 Quick Start

### Run Individual Market
```bash
# UK Market
python uk_conviction_strategy.py

# Germany Market  
python germany_conviction_strategy.py

# Hong Kong Market
python hongkong_conviction_strategy.py
```

### Run Full International Comparison
```bash
python international_comparison.py
```

## 📊 Market-Specific Parameters

### Volume Thresholds
- **UK**: 50,000 daily (smaller market)
- **Germany**: 100,000 daily (standard)
- **Hong Kong**: 1,000,000 daily (liquidity requirement)

### Price Minimums
- **UK**: £2.00 (adjusted for UK market)
- **Germany**: €5.00 (DAX quality requirement)  
- **Hong Kong**: HK$1.00 (market structure)

### Market Cap Ranges
- **UK**: £200M - £100B
- **Germany**: €500M - €150B
- **Hong Kong**: HK$2B - HK$500B

### Fundamental Adjustments
- **UK**: Standard Western market criteria
- **Germany**: Industrial economy focus
- **Hong Kong**: Emerging market adjustments (lower ROE/growth thresholds)

## 🎪 Signal Generation

### Breakout Power (0-25 points)
- Price >1% above 20-day high: +15 points
- Price >2% above 50-day high: +10 points

### Volume Confirmation (0-30 points)
- **UK/Germany**: 2x volume = 30 points
- **Hong Kong**: 2.5x volume = 30 points (higher volatility)

### Momentum Alignment (0-25 points)
- 5-day momentum: +5 points
- 20-day momentum: +10 points  
- 50-day momentum: +10 points

### Trend Quality Bonus (0-20 points)
- Based on trend strength >60
- Bonus: (trend_strength - 60) / 2

## 📈 Expected Outputs

### CSV Files Generated
- `uk_conviction_trades_YYYYMMDD_HHMMSS.csv`
- `germany_conviction_trades_YYYYMMDD_HHMMSS.csv`
- `hongkong_conviction_trades_YYYYMMDD_HHMMSS.csv`
- `international_comparison_summary_YYYYMMDD_HHMMSS.csv`

### CSV Columns
- `timestamp`: Trade execution time
- `symbol`: Stock symbol with country suffix
- `action`: buy/sell
- `price`: Execution price in local currency
- `quantity`: Number of shares
- `value`: Total trade value
- `reason`: Conviction level and technical details
- `portfolio_value`: Portfolio value at time of trade

## 🌟 Key Features

### Currency Diversification
- **GBP exposure**: UK FTSE stocks
- **EUR exposure**: German DAX stocks
- **HKD exposure**: Hong Kong HSI stocks

### Time Zone Coverage  
- **UK**: GMT/BST trading hours
- **Germany**: CET/CEST trading hours
- **Hong Kong**: HKT trading hours

### Regulatory Adaptations
- **UK**: FCA regulations and LSE rules
- **Germany**: BaFin regulations and XETRA rules  
- **Hong Kong**: SFC regulations and HKEX rules

## ⚠️ Important Considerations

### Data Quality
- Market data quality varies by region
- Some emerging markets have limited fundamental data
- Consider data provider reliability for each market

### Currency Risk
- All returns are in local currency
- Consider hedging strategies for multi-currency portfolios
- Monitor exchange rate impacts on performance

### Regulatory Compliance
- Each market has different trading rules
- Tax implications vary by jurisdiction
- Ensure compliance with local investment regulations

### Market Hours
- **UK**: 8:00 AM - 4:30 PM GMT
- **Germany**: 9:00 AM - 5:30 PM CET  
- **Hong Kong**: 9:30 AM - 4:00 PM HKT

## 🔧 Customization

### Adjusting Thresholds
Modify parameters in each strategy file:

```python
# Fundamental thresholds
self.fundamental_threshold = 60.0  # Quality score minimum
self.min_roe = 15                  # ROE requirement  
self.min_revenue_growth = 10       # Revenue growth requirement

# Risk management
self.stop_loss_pct = 0.07         # 7% stop loss
self.profit_target = 0.50         # 50% profit target
self.trail_percent = 0.12         # 12% trailing stop

# Market filters
self.min_price = 5.0              # Minimum stock price
self.min_volume = 100000          # Minimum daily volume
self.min_market_cap = 500e6       # Minimum market cap
```

### Adding New Markets
To add a new market, copy an existing strategy and modify:

1. **Symbol universe**: Update stock list with local suffixes
2. **Currency**: Update currency references  
3. **Thresholds**: Adjust for local market conditions
4. **Benchmark**: Set appropriate market benchmark
5. **Fundamentals**: Adjust criteria for market maturity

## 📞 Support

For questions about specific market implementations:
- UK Market: London Stock Exchange documentation
- German Market: Deutsche Börse documentation  
- Hong Kong Market: Hong Kong Exchanges documentation

---

**🌍 Global systematic trading using our proven 5-Level Conviction methodology!**