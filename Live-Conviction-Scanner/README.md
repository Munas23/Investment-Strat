# Live Conviction Scanner - Interactive Brokers Integration

Real-time market scanning using Interactive Brokers API to identify stocks meeting our proven 5-Level Conviction criteria in today's markets.

## 🎯 Features

- **Real-time conviction analysis** using our proven 5-level system
- **US and ASX market scanning** with your paid IB market data
- **Live alerts** for high-conviction setups (Level 3+ signals)
- **Custom watchlist management** for focused monitoring
- **Export capabilities** for detailed analysis
- **Rate limiting** to respect IB API limits

## 📋 Prerequisites

### 1. Interactive Brokers Account
- Active IB account with API access enabled
- **Paid market data subscriptions** (you mentioned you have this)
- TWS (Trader Workstation) or IB Gateway installed

### 2. Required Market Data Subscriptions
- **US Securities Snapshot and Futures Value Bundle** - for US stocks
- **Australian Securities Exchange (ASX)** - for ASX stocks  
- **NASDAQ Basic** - for NASDAQ stocks
- **NYSE Market Data** - for NYSE stocks

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Interactive Brokers
1. **Open TWS or IB Gateway** and log in
2. **Enable API access**: File → Global Configuration → API → Settings
3. **Check "Enable ActiveX and Socket Clients"**
4. **Set Socket Port** to `7497` (IB Gateway) or `7496` (TWS)
5. **Add "127.0.0.1"** to trusted IP addresses
6. **Restart TWS/IB Gateway**

### 3. Run Live Scanner
```bash
python ib_live_scanner.py
```

### 4. Manage Watchlists
```bash
python watchlist_manager.py
```

## 🔍 How It Works

### Our 5-Level Conviction System Applied Live

The scanner applies our proven conviction methodology to live market data:

#### **Level 1 (20% position)**: Minimal Conviction
- Basic trend strength (60+ score)
- Light volume confirmation
- Minimal momentum alignment

#### **Level 2 (25% position)**: Low Conviction  
- Stronger trend strength
- Some volume surge (1.2x average)
- Better momentum alignment

#### **Level 3 (30% position)**: Standard Conviction
- Good trend strength (70+ score)
- Decent volume surge (1.5x average)
- Multiple momentum factors aligned

#### **Level 4 (35% position)**: High Conviction
- Strong trend strength (80+ score)
- Significant volume surge (1.8x average)
- Strong momentum across timeframes

#### **Level 5 (40% position)**: Maximum Conviction
- Exceptional trend strength (90+ score)
- Massive volume surge (2x+ average)
- Perfect momentum alignment

### Real-Time Scoring Algorithm

```python
# Factor 1: Breakout Power (0-25 points)
if price > high_20 * 1.01:  # 1% above 20-day high
    conviction += 15
    if price > high_50 * 1.02:  # 2% above 50-day high
        conviction += 10

# Factor 2: Volume Confirmation (0-30 points)
if volume_surge > 2.0:      # 2x average volume
    conviction += 30
elif volume_surge > 1.5:    # 1.5x volume
    conviction += 20

# Factor 3: Momentum Alignment (0-25 points)
if momentum_5d > 1: conviction += 5
if momentum_20d > 5: conviction += 10
if momentum_50d > 10: conviction += 10

# Factor 4: Trend Quality Bonus (0-20 points)
trend_bonus = min(20, (trend_strength - 60) / 2)
conviction += trend_bonus
```

## 📊 Scanner Features

### **Market Coverage**
- **US Market**: S&P 500 major stocks
- **ASX Market**: ASX300 major stocks  
- **Real-time data**: Using your paid IB subscriptions

### **Filtering Criteria**
- Minimum price: $5 (adjustable)
- Minimum volume: 100K daily (adjustable)
- Maximum market cap: $100B (adjustable)
- Trend strength: >60 required

### **Output Features**
- **Live alerts** for Level 3+ conviction
- **Detailed scoring** breakdown for analysis
- **CSV export** with full conviction details
- **Real-time logging** of all activity

## 🎛️ Watchlist Management

### Pre-built Watchlists
- **US_Tech**: Apple, Microsoft, Google, Amazon, etc.
- **US_Blue_Chip**: J&J, JPM, Visa, P&G, etc.
- **ASX_Big_4_Banks**: CBA, ANZ, WBC, NAB
- **ASX_Mining**: BHP, RIO, FMG, NCM, etc.
- **ASX_Healthcare**: CSL, COH, RMD, etc.

### Custom Watchlists
- Create sector-specific lists
- Import from CSV files
- Export for external analysis
- Real-time monitoring capabilities

## 🚨 Live Alerts

### High Conviction Alerts (Level 3+)
```
🎯 HIGH CONVICTION: AAPL - Level 4 - HIGH conviction: 78, trend: 85, vol: 1.8x
📊 Conviction: MSFT - Level 3 - STANDARD conviction: 65, trend: 75, vol: 1.4x
```

### Alert Types
- **Level 3+**: Immediate console alerts
- **Level 4+**: Highlighted in results
- **Level 5**: Maximum conviction (rare!)

## 📈 Example Usage

### 1. Scan US Market
```bash
python ib_live_scanner.py
# Select option 1: US Market
# Wait for scan completion
# Review high conviction alerts
```

### 2. Scan ASX Market
```bash
python ib_live_scanner.py
# Select option 2: ASX Market  
# Monitor for ASX opportunities
# Export results for analysis
```

### 3. Custom Watchlist Scan
```python
from ib_live_scanner import LiveConvictionScanner

scanner = LiveConvictionScanner()
await scanner.connect()

# Scan custom list
custom_symbols = ['AAPL', 'TSLA', 'CBA.AX', 'BHP.AX']
results = scanner.scan_market(custom_symbols)

# Process results
for result in results:
    if result['conviction_level'] >= 3:
        print(f"High conviction: {result['symbol']} - Level {result['conviction_level']}")
```

## 📝 Output Files

### CSV Export Columns
- `timestamp`: Scan time
- `symbol`: Stock symbol
- `exchange`: Exchange (SMART, ASX, etc.)
- `price`: Current price
- `volume`: Current volume
- `conviction_level`: 0-5 conviction level
- `position_size_pct`: Recommended position size
- `trend_strength`: Technical trend score
- `breakout_power`: Breakout strength points
- `volume_surge`: Volume vs average
- `momentum_points`: Momentum alignment score
- `conviction_reason`: Detailed explanation

### Log Files
- `live_scanner.log`: Detailed scan activity
- Real-time progress tracking
- Error logging and debugging

## ⚠️ Important Notes

### **Market Hours**
- **US Markets**: 9:30 AM - 4:00 PM EST
- **ASX Markets**: 10:00 AM - 4:00 PM AEST
- Scanner works during market hours with live data
- After-hours: Limited data availability

### **Rate Limiting**
- Scanner includes delays between requests
- Respects IB API rate limits
- Large scans may take several minutes

### **Data Quality**
- Requires paid market data subscriptions
- Real-time data during market hours
- 15-20 minute delays for non-paying subscribers

### **API Stability**
- Keep TWS/IB Gateway running during scans
- Monitor connection status
- Automatic reconnection attempts

## 🔧 Configuration

### Scanner Settings (ib_live_scanner.py)
```python
# Modify these in the scanner initialization
self.fundamental_threshold = 60.0    # Minimum fundamental score
self.min_price = 5.0                # Minimum stock price  
self.min_volume = 100000            # Minimum daily volume
self.max_market_cap = 100e9         # Maximum market cap
```

### Connection Settings
```python
# Default IB connection
host = '127.0.0.1'       # localhost
port = 7497              # IB Gateway (use 7496 for TWS)
client_id = 1            # Unique client identifier
```

## 🎯 Best Practices

### **For Live Scanning**
1. **Start with small watchlists** to test setup
2. **Monitor during active market hours** for best data
3. **Focus on Level 3+ alerts** for actionable signals
4. **Export results** for detailed analysis
5. **Use paper trading** before live implementation

### **For Risk Management**
1. **Never risk more than conviction level suggests**
2. **Always use stop losses** (7% recommended)
3. **Consider market conditions** and volatility
4. **Diversify across conviction levels**
5. **Monitor position sizes** carefully

## 🆘 Troubleshooting

### **Connection Issues**
- Verify TWS/IB Gateway is running
- Check API is enabled in settings
- Confirm correct port number
- Ensure unique client ID

### **No Market Data**
- Verify paid subscriptions are active
- Check data feed status in TWS
- Confirm symbol format (add .AX for ASX)

### **Scanner Errors**
- Check log files for details
- Verify symbol lists are valid
- Monitor API rate limits
- Restart TWS if needed

## 📞 Support

- **Interactive Brokers API**: https://interactivebrokers.github.io/tws-api/
- **ib_insync Library**: https://ib-insync.readthedocs.io/
- **IB Customer Support**: Through Account Management portal

---

**Ready to scan today's markets for high-conviction opportunities using your proven 5-level system!** 🚀