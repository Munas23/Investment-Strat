"""
Simple IB Connection Test
"""
try:
    from ib_insync import IB
    print("✓ ib_insync library available")
    
    ib = IB()
    print("✓ IB object created")
    
    # Try to connect
    print("Attempting connection...")
    ib.connect('127.0.0.1', 7497, clientId=1)  # Gateway port
    
    if ib.isConnected():
        print("✅ Connected to IB Gateway successfully!")
        
        # Test basic functionality
        positions = ib.positions()
        print(f"✓ Found {len(positions)} positions in account")
        
        # Test market data request
        from ib_insync import Stock
        contract = Stock('AAPL', 'SMART', 'USD')
        ib.qualifyContracts(contract)
        print("✓ Contract qualification successful")
        
    else:
        print("❌ Not connected")
    
    ib.disconnect()
    print("✓ Disconnected cleanly")
    
except ImportError:
    print("❌ ib_insync not installed. Run: pip install ib_insync")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure TWS or IB Gateway is running")
    print("2. Enable API in TWS: Configure → API → Enable ActiveX and Socket Clients")
    print("3. Check port: 7497 (Gateway) or 7496 (TWS)")
    print("4. Make sure no other app is using the same client ID")