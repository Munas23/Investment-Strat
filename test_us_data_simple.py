"""
Simple Synchronous US Market Data Test
"""
from ib_insync import IB, Stock
import time

def test_us_data():
    ib = IB()
    
    try:
        # Connect synchronously
        ib.connect('127.0.0.1', 7496, clientId=3)
        print("Connected to IB")
        
        # Test a simple US symbol
        print("\nTesting AAPL...")
        
        # Create contract
        contract = Stock('AAPL', 'SMART', 'USD')
        ib.qualifyContracts(contract)
        print(f"Contract qualified: {contract}")
        
        # Request real-time data
        ticker = ib.reqMktData(contract, '', False, False)
        ib.sleep(3)  # Wait for data
        
        print(f"Market data for AAPL:")
        print(f"  Last price: {ticker.last}")
        print(f"  Bid: {ticker.bid}")
        print(f"  Ask: {ticker.ask}")
        print(f"  Volume: {ticker.volume}")
        print(f"  Market data type: {ticker.marketDataType}")
        
        # Test historical data
        print("\nTesting historical data...")
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='5 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        
        print(f"Historical bars received: {len(bars)}")
        if bars:
            latest = bars[-1]
            print(f"Latest bar: {latest.date} - Close: ${latest.close:.2f}, Volume: {latest.volume}")
        else:
            print("No historical data received")
        
        # Cancel market data
        ib.cancelMktData(contract)
        
        # Check what data subscriptions we have
        print(f"\nAccount details:")
        account = ib.managedAccounts()[0] if ib.managedAccounts() else "None"
        print(f"  Managed account: {account}")
        
        # Test if we get delayed vs real-time data
        print(f"\nMarket data type info:")
        print(f"  Ticker market data type: {ticker.marketDataType}")
        if ticker.marketDataType == 1:
            print("  Real-time data")
        elif ticker.marketDataType == 2:
            print("  Frozen data")
        elif ticker.marketDataType == 3:
            print("  Delayed data")
        elif ticker.marketDataType == 4:
            print("  Delayed frozen data")
        else:
            print(f"  Unknown data type: {ticker.marketDataType}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if ib.isConnected():
            ib.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    test_us_data()