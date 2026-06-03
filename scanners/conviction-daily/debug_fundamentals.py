"""Debug script to check fundamental data and scoring"""
import sys
import os
import importlib.util

# Import the scanner
spec = importlib.util.spec_from_file_location("five_lc_scanner", "5lc_daily_scanner.py")
five_lc_scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(five_lc_scanner)
FiveLevelConvictionScanner = five_lc_scanner.FiveLevelConvictionScanner

def debug_stock(symbol):
    """Debug a single stock's fundamental data"""
    print(f"\n=== DEBUGGING {symbol} ===")

    scanner = FiveLevelConvictionScanner()

    try:
        # Get raw fundamental data
        fundamentals = scanner.get_fundamental_data(symbol)

        print("Raw fundamental data:")
        for key, value in fundamentals.items():
            if key != 'symbol':
                print(f"  {key}: {value}")

        # Calculate fundamental score
        if 'error' not in fundamentals:
            fund_score, breakdown = scanner.calculate_fundamental_score(symbol, fundamentals)
            print(f"\nFundamental Score: {fund_score:.1f}/150 (need 90+ to pass)")
            print("Score breakdown:")
            for key, value in breakdown.items():
                print(f"  {key}: {value}")
        else:
            print(f"ERROR getting fundamentals: {fundamentals.get('error', 'Unknown')}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Test a few representative stocks
    test_symbols = ['AAPL', 'CBA.AX', 'KO']

    for symbol in test_symbols:
        debug_stock(symbol)
        print("\n" + "="*50)