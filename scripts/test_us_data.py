"""
Test US Market Data Access
"""
import asyncio
from ib_insync import IB, Stock

async def test_us_data():
    ib = IB()
    
    try:
        # Connect
        await ib.connectAsync('127.0.0.1', 7496, clientId=2)
        print("Connected to IB")
        
        # Test different US symbols
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'SPY']
        
        for symbol in test_symbols:
            print(f"\nTesting {symbol}...")
            
            try:
                # Create contract
                contract = Stock(symbol, 'SMART', 'USD')
                ib.qualifyContracts(contract)
                print(f"  Contract qualified: {contract}")
                
                # Request market data
                ticker = ib.reqMktData(contract, '', False, False)
                await ib.sleep(2)  # Wait for data
                
                print(f"  Last price: {ticker.last}")
                print(f"  Bid: {ticker.bid}")
                print(f"  Ask: {ticker.ask}")
                print(f"  Volume: {ticker.volume}")
                
                # Test historical data
                bars = ib.reqHistoricalData(
                    contract,
                    endDateTime='',
                    durationStr='5 D',
                    barSizeSetting='1 day',
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1
                )
                
                print(f"  Historical bars: {len(bars)} days")
                if bars:
                    print(f"  Latest close: ${bars[-1].close:.2f}")
                
                # Cancel market data
                ib.cancelMktData(contract)
                
            except Exception as e:
                print(f"  ERROR with {symbol}: {e}")
        
        # Check account/permissions
        print(f"\nAccount info:")
        account = ib.managedAccounts()[0] if ib.managedAccounts() else "None"
        print(f"  Account: {account}")
        
        positions = ib.positions()
        print(f"  Positions: {len(positions)}")
        
    except Exception as e:
        print(f"Connection error: {e}")
    
    finally:
        ib.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(test_us_data())