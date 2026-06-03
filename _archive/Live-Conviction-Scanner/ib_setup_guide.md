# Interactive Brokers Setup Guide

## Prerequisites

1. **Interactive Brokers Account** with API access enabled
2. **Paid Market Data Subscription** (required for real-time scanning)
3. **TWS (Trader Workstation) or IB Gateway** installed and running

## Step 1: Enable API Access in TWS/IB Gateway

### In TWS (Trader Workstation):
1. Open TWS and log in
2. Go to **File → Global Configuration → API → Settings**
3. Check **"Enable ActiveX and Socket Clients"**
4. Set **Socket Port** to `7496` (for TWS) or `7497` (for IB Gateway)
5. Check **"Read-Only API"** if you only want to scan (recommended for safety)
6. Add **"127.0.0.1"** to trusted IP addresses
7. Click **OK** and restart TWS

### In IB Gateway:
1. Open IB Gateway and log in
2. Go to **Configure → Settings → API**
3. Check **"Enable ActiveX and Socket Clients"**
4. Set **Socket Port** to `7497`
5. Check **"Read-Only API"** for scanning only
6. Add **"127.0.0.1"** to trusted IP addresses
7. Click **OK**

## Step 2: Market Data Subscriptions

### Required Subscriptions (in Account Management):
1. **US Securities Snapshot and Futures Value Bundle** - for US stocks
2. **Australian Securities Exchange (ASX)** - for ASX stocks  
3. **NASDAQ Basic** - for NASDAQ stocks
4. **NYSE Market Data** - for NYSE stocks

### To Check/Add Subscriptions:
1. Log into **Account Management** (accountmanagement.interactivebrokers.com)
2. Go to **Settings → User Settings → Market Data Subscriptions**
3. Subscribe to required data feeds
4. **Note**: Most subscriptions have monthly fees (~$1-10 per feed)

## Step 3: Install Required Libraries

```bash
pip install -r requirements.txt
```

Key library: `ib_insync` - Python wrapper for IB API

## Step 4: Test Connection

### Basic Connection Test:
```python
from ib_insync import IB

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Use 7496 for TWS
print("Connected:", ib.isConnected())
ib.disconnect()
```

### If Connection Fails:
1. **Check TWS/IB Gateway is running**
2. **Verify API is enabled** in settings
3. **Check port number** (7496 for TWS, 7497 for IB Gateway)
4. **Ensure client ID is unique** (each connection needs different ID)
5. **Check firewall** isn't blocking the connection

## Step 5: Run Live Scanner

```bash
python ib_live_scanner.py
```

### Scanner Features:
- **Real-time conviction analysis** using your proven 5-level system
- **US and ASX market scanning** 
- **Live alerts** for high-conviction setups
- **Export to CSV** for further analysis
- **Rate limiting** to respect API limits

### Scanner Options:
1. **US Market Only** - Scans S&P 500 sample
2. **ASX Market Only** - Scans ASX300 sample  
3. **Both Markets** - Comprehensive scan

## Troubleshooting

### Common Issues:

1. **"Connection refused"**
   - TWS/IB Gateway not running
   - API not enabled
   - Wrong port number

2. **"No market data"**
   - Missing market data subscriptions
   - Check account permissions
   - Verify data feed status in TWS

3. **"Rate limiting"**
   - Too many requests too fast
   - Scanner includes delays to prevent this
   - Consider reducing symbol list

4. **"Permission denied"**
   - API not enabled for your account
   - Check account settings in TWS

### Data Feeds Status:
Check in TWS: **Help → About Trader Workstation → Market Data Farms**
- Green = Connected and receiving data
- Red = Issues with data feed

## Security Notes

1. **Use Read-Only API** when possible
2. **Never share API credentials**
3. **Monitor for unusual activity**
4. **Consider paper trading account** for testing

## Performance Tips

1. **Use IB Gateway** instead of full TWS (lighter weight)
2. **Limit concurrent requests** (scanner includes rate limiting)
3. **Subscribe only to needed data feeds** (saves money)
4. **Run during market hours** for best data quality

## Support

- **IB API Documentation**: https://interactivebrokers.github.io/tws-api/
- **ib_insync Documentation**: https://ib-insync.readthedocs.io/
- **IB Support**: Submit ticket through Account Management