"""
Test Scanner with US Stocks (No Interactive Input)
"""
import sys
sys.path.append('Live-Conviction-Scanner')

from ib_live_scanner import LiveConvictionScanner
import time

def test_scanner():
    scanner = LiveConvictionScanner(client_id=5)  # Different client ID
    
    try:
        # Connect
        print("Connecting to Interactive Brokers...")
        connected = scanner.connect()
        
        if not connected:
            print("Failed to connect to Interactive Brokers")
            return
        
        print("Connected successfully!")
        
        # Test with a few US symbols
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        print(f"\nTesting scanner with {len(test_symbols)} US symbols...")
        
        for symbol in test_symbols:
            print(f"\n--- Scanning {symbol} ---")
            result = scanner.scan_symbol(symbol, "SMART")
            
            if result:
                print(f"Symbol: {result['symbol']}")
                print(f"Price: ${result['price']:.2f}")
                print(f"Volume: {result['volume']:,}")
                print(f"Conviction Level: {result['conviction_level']}")
                print(f"Position Size: {result['position_size_pct']}%")
                print(f"Reason: {result['conviction_reason']}")
                
                if result['conviction_level'] >= 2:
                    print("*** TRADE CANDIDATE ***")
            else:
                print(f"No result for {symbol}")
            
            time.sleep(1)  # Pause between requests
        
        # Print summary
        scanner.print_summary()
        
        # Export results
        filename = scanner.export_results()
        if filename:
            print(f"\nResults exported to: {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scanner.disconnect()
        print("Disconnected from IB")

if __name__ == "__main__":
    test_scanner()