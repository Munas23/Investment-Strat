"""
Debug Market Data Function
"""
import sys
sys.path.append('Live-Conviction-Scanner')

from ib_live_scanner import LiveConvictionScanner
import pandas as pd

def debug_market_data():
    scanner = LiveConvictionScanner(client_id=6)
    
    try:
        # Connect
        connected = scanner.connect()
        if not connected:
            print("Failed to connect")
            return
        
        print("Connected! Testing market data retrieval...")
        
        # Test get_market_data directly
        symbol = 'AAPL'
        print(f"\nTesting market data for {symbol}...")
        
        market_data = scanner.get_market_data(symbol, "SMART")
        
        if market_data:
            print("SUCCESS - Market data received:")
            print(f"  Symbol: {market_data['symbol']}")
            print(f"  Price: {market_data['price']}")
            print(f"  Volume: {market_data['volume']}")
            print(f"  Bid: {market_data['bid']}")
            print(f"  Ask: {market_data['ask']}")
            print(f"  Exchange: {market_data['exchange']}")
            print(f"  Historical data rows: {len(market_data['historical_data'])}")
            
            # Test basic filters
            print(f"\nFilter tests:")
            print(f"  Min price ${scanner.min_price} - Pass: {market_data['price'] >= scanner.min_price}")
            
            # Test average volume
            df = market_data['historical_data']
            if len(df) >= 20:
                avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                print(f"  Current tick volume: {market_data['volume']:,}")
                print(f"  Average daily volume: {avg_volume:,.0f}")
                print(f"  Min volume {scanner.min_volume:,} - Pass: {avg_volume >= scanner.min_volume}")
            else:
                print(f"  Min volume {scanner.min_volume:,} - Pass: {market_data['volume'] >= scanner.min_volume}")
            
            # Test trend calculation
            if len(market_data['historical_data']) >= 150:
                trend_strength = scanner.calculate_trend_strength(market_data['historical_data'])
                print(f"  Trend strength: {trend_strength:.1f}/100")
                
                # Test conviction signal
                conviction_level, reason, details = scanner.generate_conviction_signal(market_data)
                print(f"  Conviction level: {conviction_level}")
                print(f"  Reason: {reason}")
                print(f"  Details: {details}")
            else:
                print(f"  Insufficient historical data: {len(market_data['historical_data'])} rows")
        else:
            print("FAILED - No market data received")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scanner.disconnect()

if __name__ == "__main__":
    debug_market_data()