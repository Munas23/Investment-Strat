"""Test institutional ownership data availability"""
import yfinance as yf

def test_institutional_data(symbol):
    """Test what institutional data is available"""
    print(f"\n=== TESTING {symbol} ===")

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Look for all keys related to institutional/insider ownership
        ownership_keys = []
        for key, value in info.items():
            if any(word in key.lower() for word in ['held', 'insider', 'institution', 'ownership', 'shares']):
                ownership_keys.append((key, value))

        if ownership_keys:
            print("Found ownership-related data:")
            for key, value in ownership_keys:
                print(f"  {key}: {value}")
        else:
            print("No ownership data found")

        # Test specific keys
        specific_keys = [
            'heldByInstitutions', 'heldByInsiders', 'institutionalHolders',
            'sharesHeld', 'sharesOutstanding', 'floatShares', 'impliedSharesOutstanding'
        ]

        print("\nSpecific key tests:")
        for key in specific_keys:
            value = info.get(key, 'NOT_FOUND')
            print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    symbols = ['AAPL', 'MSFT', 'CBA.AX']

    for symbol in symbols:
        test_institutional_data(symbol)
        print("-" * 50)