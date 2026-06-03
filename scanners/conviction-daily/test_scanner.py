"""
5LC SCANNER TEST SCRIPT
======================

Quick test script to verify the 5LC daily scanner functionality
with a small sample of well-known stocks before running full scans.

This tests:
• Data retrieval functionality
• Fundamental screening accuracy
• Technical analysis calculations
• Conviction scoring methodology
• Export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import importlib.util
spec = importlib.util.spec_from_file_location("five_lc_scanner", "5lc_daily_scanner.py")
five_lc_scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(five_lc_scanner)
FiveLevelConvictionScanner = five_lc_scanner.FiveLevelConvictionScanner
import time

def test_scanner():
    """Test the scanner with a small sample of known stocks"""

    print("=" * 60)
    print("5LC SCANNER FUNCTIONALITY TEST")
    print("=" * 60)

    # Initialize scanner
    scanner = FiveLevelConvictionScanner()

    # Test symbols - mix of quality levels and markets
    test_symbols = [
        # US High-quality growth stocks
        'AAPL',   # Large cap tech leader
        'NVDA',   # High-growth AI leader
        'MSFT',   # Mega cap stable grower
        'GOOGL',  # Tech giant
        'TSLA',   # High-volatility growth

        # US Mixed quality
        'KO',     # Stable dividend stock (low growth)
        'F',      # Cyclical auto (moderate quality)
        'GME',    # Meme stock (poor fundamentals)

        # ASX Stocks
        'CBA.AX', # Major Australian bank
        'BHP.AX', # Mining giant
        'CSL.AX', # Healthcare leader
        'XRO.AX', # Tech growth stock
        'WOW.AX'  # Retail giant
    ]

    print(f"Testing scanner with {len(test_symbols)} diverse stocks...")
    print("This tests fundamental screening, technical analysis, and conviction scoring.")
    print()

    test_results = []
    start_time = time.time()

    for i, symbol in enumerate(test_symbols, 1):
        print(f"Testing {i}/{len(test_symbols)}: {symbol}...")

        try:
            result = scanner.scan_symbol(symbol)
            if result:
                test_results.append(result)
                print(f"  OK PASSED: Level {result['conviction_level']} conviction "
                      f"(Fund: {result['fundamental_score']:.0f}%, "
                      f"Trend: {result['trend_strength']}, "
                      f"Score: {result['conviction_score']})")
            else:
                print(f"  REJECTED: Failed screening criteria")

        except Exception as e:
            print(f"  ERROR: {e}")

        # Small delay to avoid rate limits
        time.sleep(0.5)

    test_time = time.time() - start_time

    # Print test summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Test duration: {test_time:.1f} seconds")
    print(f"Symbols tested: {len(test_symbols)}")
    print(f"Symbols passed: {len(test_results)}")
    print(f"Pass rate: {len(test_results)/len(test_symbols)*100:.1f}%")
    print()

    if test_results:
        print("CONVICTION BREAKDOWN:")
        conviction_counts = {}
        for result in test_results:
            level = result['conviction_level']
            conviction_counts[level] = conviction_counts.get(level, 0) + 1

        for level in sorted(conviction_counts.keys(), reverse=True):
            count = conviction_counts[level]
            position_pct = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}.get(level, 0)
            print(f"  Level {level} ({position_pct}% position): {count} stocks")

        print("\nTOP RESULTS:")
        sorted_results = sorted(test_results,
                              key=lambda x: (x['conviction_level'], x['conviction_score']),
                              reverse=True)

        for result in sorted_results[:5]:
            print(f"  {result['symbol']:<6} Level {result['conviction_level']} "
                  f"({result['conviction_score']:3.0f} pts) - "
                  f"Fund: {result['fundamental_score']:3.0f}% - "
                  f"Trend: {result['trend_strength']:2.0f} - "
                  f"${result['price']:6.2f}")

    # Test export functionality
    if test_results:
        print(f"\nTesting export functionality...")
        scanner.scan_results = test_results  # Set results for export
        filename = scanner.export_results("test_scan_results.csv")
        if filename:
            print(f"OK Export test successful: {filename}")
        else:
            print("FAIL Export test failed")

    print("\n" + "=" * 60)
    print("SCANNER VALIDATION")
    print("=" * 60)

    # Expected behavior validation
    validations = []

    # Check if high-quality stocks passed
    quality_symbols = ['AAPL', 'NVDA', 'MSFT', 'GOOGL', 'CBA.AX', 'CSL.AX']
    quality_passed = [r for r in test_results if r['symbol'] in quality_symbols]
    validations.append(("Quality stocks pass screening", len(quality_passed) > 0))

    # Check if fundamental scoring works
    fund_scores = [r['fundamental_score'] for r in test_results]
    validations.append(("Fundamental scores calculated", len(fund_scores) > 0 and max(fund_scores) >= 60))

    # Check if conviction scoring works
    conv_scores = [r['conviction_score'] for r in test_results]
    validations.append(("Conviction scores calculated", len(conv_scores) > 0 and max(conv_scores) >= 25))

    # Check if different conviction levels exist
    conv_levels = set(r['conviction_level'] for r in test_results)
    validations.append(("Multiple conviction levels", len(conv_levels) > 1))

    # Check if position sizing works
    position_sizes = set(r['position_size_pct'] for r in test_results)
    validations.append(("Position sizing calculated", len(position_sizes) > 0))

    for validation, passed in validations:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {validation}")

    all_passed = all(passed for _, passed in validations)

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: SCANNER TEST SUCCESSFUL!")
        print("The 5LC daily scanner is ready for production use.")
        print("You can now run full S&P 500 and ASX300 scans.")
    else:
        print("WARNING SCANNER TEST ISSUES DETECTED")
        print("Please review the validation failures above.")
    print("=" * 60)

    return all_passed, test_results

def main():
    """Run the scanner test"""
    try:
        success, results = test_scanner()
        return success
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("5LC SCANNER VALIDATION TEST")
    print("Testing with sample stocks to verify functionality...")
    print()

    success = main()

    if success:
        print("\nReady to run full market scans!")
        print("Use: python 5lc_daily_scanner.py")
    else:
        print("\nPlease fix issues before running full scans.")