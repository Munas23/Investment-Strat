import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# US stocks from the scanner file yesterday 4:46pm
us_stocks = [
    'TJX', 'ADI', 'ADM', 'WBA', 'MO', 'HCA', 'PODD', 'ALL', 'CBOE', 'LOW', 
    'TOL', 'TXN', 'ABBV', 'EL', 'O', 'REGN', 'FSLR', 'JNJ', 'RMD', 'ZBH', 
    'VTRS', 'AFL', 'WRB', 'HD', 'GM', 'AZO', 'ROST', 'LEN', 'WMT', 'VZ', 'NEM'
]

# Get yesterday's and today's data
yesterday = datetime(2025, 8, 20)
today = datetime(2025, 8, 21)

print("US Stock Performance from August 20 close to August 21 morning:")
print("=" * 70)

results = []

for symbol in us_stocks:
    try:
        # Get 3 days of data to ensure we have both dates
        stock = yf.Ticker(symbol)
        hist = stock.history(start='2025-08-19', end='2025-08-22')
        
        if len(hist) >= 2:
            # Get close prices
            yesterday_close = hist.iloc[-2]['Close']  # Aug 20 close
            today_open = hist.iloc[-1]['Open']        # Aug 21 open
            today_current = hist.iloc[-1]['Close']    # Aug 21 close
            
            # Calculate overnight performance (close to open)
            overnight_change = ((today_open - yesterday_close) / yesterday_close) * 100
            
            # Calculate day performance (open to current)
            day_change = ((today_current - today_open) / today_open) * 100
            
            # Total change from yesterday close to today close
            total_change = ((today_current - yesterday_close) / yesterday_close) * 100
            
            results.append({
                'Symbol': symbol,
                'Yesterday Close': yesterday_close,
                'Today Open': today_open,
                'Today Close': today_current,
                'Overnight %': overnight_change,
                'Day %': day_change,
                'Total %': total_change
            })
            
            print(f"{symbol:6} | Overnight: {overnight_change:+6.2f}% | Day: {day_change:+6.2f}% | Total: {total_change:+6.2f}%")
        
    except Exception as e:
        print(f"{symbol:6} | Error: {str(e)}")

# Calculate summary statistics
if results:
    df = pd.DataFrame(results)
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"Average Overnight Performance: {df['Overnight %'].mean():+.2f}%")
    print(f"Average Day Performance: {df['Day %'].mean():+.2f}%")
    print(f"Average Total Performance: {df['Total %'].mean():+.2f}%")
    print(f"Best Overnight Performer: {df.loc[df['Overnight %'].idxmax(), 'Symbol']} ({df['Overnight %'].max():+.2f}%)")
    print(f"Worst Overnight Performer: {df.loc[df['Overnight %'].idxmin(), 'Symbol']} ({df['Overnight %'].min():+.2f}%)")
    print(f"Stocks Up Overnight: {len(df[df['Overnight %'] > 0])}/{len(df)}")