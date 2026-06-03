#!/usr/bin/env python3
"""
Create August 19th Scanner Results
Simulates what the scanner would have found on August 19th, 2024
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_historical_data(symbol, target_date="2024-08-19"):
    """Get historical data up to target date"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Get data from 1 year before target date to target date
        start_date = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=365)
        end_date = datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)
        
        hist = ticker.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 150:
            return None
            
        # Standardize column names
        hist.columns = [col.lower() for col in hist.columns]
        hist = hist.dropna()
        
        return hist.reset_index()
        
    except Exception as e:
        print(f"Error getting data for {symbol}: {e}")
        return None

def calculate_scanner_metrics(df):
    """Calculate the same metrics as the daily scanner"""
    if df is None or len(df) < 21:
        return None
    
    try:
        # Use the last row as "current" (August 19th)
        current = df.iloc[-1]
        current_price = current['close']
        
        # Calculate 20-day metrics
        high_20 = df['high'].rolling(20).max().iloc[-1]
        low_20 = df['low'].rolling(20).min().iloc[-1]
        volume_avg_20 = df['volume'].rolling(20).mean().iloc[-1]
        
        # Distance from 20-day high
        distance_from_high = (current_price / high_20 - 1) * 100
        
        # Volume surge
        volume_surge = current['volume'] / volume_avg_20 if volume_avg_20 > 0 else 0
        
        # Daily change
        prev_close = df.iloc[-2]['close']
        daily_change_pct = (current_price / prev_close - 1) * 100
        
        # Simple conviction scoring (simplified version of main scanner)
        conviction_score = 0
        
        # Breakout proximity (closer to breakout = higher score)
        if distance_from_high >= -3:
            conviction_score += 2
        if distance_from_high >= -1:
            conviction_score += 1
            
        # Volume surge
        if volume_surge > 1.5:
            conviction_score += 1
        if volume_surge > 2.0:
            conviction_score += 1
            
        # Daily momentum
        if daily_change_pct > 1:
            conviction_score += 1
        if daily_change_pct > 3:
            conviction_score += 1
        if daily_change_pct > 5:
            conviction_score += 1
            
        # Determine conviction level
        if conviction_score >= 5:
            conviction_level = 5
        elif conviction_score >= 4:
            conviction_level = 4
        elif conviction_score >= 3:
            conviction_level = 3
        elif conviction_score >= 2:
            conviction_level = 2
        else:
            conviction_level = 1
            
        return {
            'current_price': current_price,
            'high_20': high_20,
            'distance_from_high': distance_from_high,
            'volume_surge': volume_surge,
            'daily_change_pct': daily_change_pct,
            'conviction_score': conviction_score,
            'conviction_level': conviction_level
        }
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return None

def create_august19_scan():
    """Create scanner results for August 19th, 2024"""
    
    print("=" * 80)
    print("CREATING AUGUST 19TH, 2024 DAILY CONVICTION SCAN")
    print("=" * 80)
    print("Simulating scanner results for August 19th, 2024")
    print("Using historical data to recreate what scanner would have found")
    print()
    
    # Sample of symbols from the original August 21st scan
    sample_symbols = [
        # ASX symbols
        'HMY.AX', 'SUL.AX', 'SGP.AX', 'DOW.AX', 'BXB.AX', 'PTM.AX', 'PFG.AX',
        'TCL.AX', 'WOW.AX', 'WES.AX', 'MAH.AX', 'CMD.AX', 'EHL.AX', 'FEX.AX',
        'PMV.AX', 'RIC.AX', 'URW.AX', 'CNI.AX', 'SRG.AX', 'MGH.AX', 'SEK.AX',
        'CNU.AX', 'CBA.AX', 'BHP.AX', 'CSL.AX', 'WBC.AX', 'ANZ.AX', 'RIO.AX',
        'COL.AX', 'TLS.AX', 'GMG.AX', 'MQG.AX', 'NAB.AX', 'REA.AX', 'SHL.AX',
        
        # US symbols
        'TJX', 'ADI', 'ADM', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META',
        'NVDA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC',
        'ADBE', 'CRM', 'NFLX', 'KO', 'PEP', 'TMO', 'COST', 'ABT', 'CVX'
    ]
    
    results = []
    
    print(f"Analyzing {len(sample_symbols)} symbols for August 19th, 2024...")
    
    for i, symbol in enumerate(sample_symbols):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(sample_symbols)} symbols processed...")
            
        # Get historical data up to August 19th
        df = get_historical_data(symbol, "2024-08-19")
        
        if df is not None:
            metrics = calculate_scanner_metrics(df)
            
            if metrics and metrics['conviction_level'] >= 2:  # Only include meaningful picks
                
                result = {
                    'symbol': symbol,
                    'market': 'ASX' if '.AX' in symbol else 'US',
                    'conviction_level': metrics['conviction_level'],
                    'current_price': metrics['current_price'],
                    'distance_from_high_pct': metrics['distance_from_high'],
                    'daily_change_pct': metrics['daily_change_pct'],
                    'volume_surge': metrics['volume_surge'],
                    'conviction_score': metrics['conviction_score'],
                    'scan_date': '2024-08-19',
                    'ib_action': 'BUY' if metrics['conviction_level'] >= 4 else 'WATCH',
                    'stop_loss_pct': 7.0,  # 7% stop loss
                    'target_pct': 15.0     # 15% profit target
                }
                
                results.append(result)
                
                print(f"  {symbol}: Level {metrics['conviction_level']}, "
                      f"Daily Change: {metrics['daily_change_pct']:.1f}%, "
                      f"Volume: {metrics['volume_surge']:.1f}x")
    
    if not results:
        print("No conviction picks found for August 19th, 2024")
        return None
    
    # Create DataFrame and sort by conviction level
    df = pd.DataFrame(results)
    df = df.sort_values(['conviction_level', 'conviction_score'], ascending=[False, False])
    
    # Generate filename
    filename = f"daily_conviction_scan_20240819_simulated.csv"
    
    # Export to CSV
    df.to_csv(filename, index=False)
    
    # Create trade-ready summary
    trade_ready = df[df['conviction_level'] >= 4]
    if len(trade_ready) > 0:
        trade_filename = filename.replace('.csv', '_TRADE_READY.csv')
        trade_ready.to_csv(trade_filename, index=False)
        print(f"\nTrade-ready picks exported to: {trade_filename}")
    
    print(f"\nAUGUST 19TH, 2024 SCAN RESULTS:")
    print(f"Total picks: {len(df)}")
    print(f"Trade-ready (Level 4+): {len(trade_ready)}")
    print(f"Watch list (Level 2-3): {len(df[df['conviction_level'] < 4])}")
    
    print(f"\nTOP PICKS FOR AUGUST 19TH:")
    for _, row in df.head(10).iterrows():
        print(f"  {row['symbol']}: Level {row['conviction_level']}, "
              f"Change: {row['daily_change_pct']:.1f}%, "
              f"Distance: {row['distance_from_high_pct']:.1f}%")
    
    print(f"\nResults exported to: {filename}")
    return filename

if __name__ == "__main__":
    result_file = create_august19_scan()
    if result_file:
        print(f"\nAugust 19th scan completed. Results saved to: {result_file}")
    else:
        print("\nScan failed.")