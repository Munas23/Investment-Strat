"""
Test Daily Scanner - Quick verification with a few symbols
"""

from daily_conviction_scanner import DailyConvictionScanner
import time

def test_scanner():
    """Test the daily scanner with a small sample"""
    
    scanner = DailyConvictionScanner()
    
    print("Testing Daily Conviction Scanner...")
    print("=" * 50)
    
    # Test symbols from both markets
    test_symbols = {
        'US': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'],
        'ASX': ['CBA.AX', 'BHP.AX', 'CSL.AX', 'WBC.AX', 'ANZ.AX']
    }
    
    all_results = []
    
    for market, symbols in test_symbols.items():
        print(f"\nTesting {market} symbols: {', '.join(symbols)}")
        print("-" * 40)
        
        start_time = time.time()
        
        for symbol in symbols:
            result = scanner.scan_symbol(symbol)
            if result:
                all_results.append(result)
                print(f"{symbol:<8} Level {result['conviction_level']} - "
                      f"${result['price']:>8.2f} - {result['ib_action']} - "
                      f"{result['conviction_reason'][:40]}...")
            else:
                print(f"{symbol:<8} No data or filtered out")
            
            time.sleep(0.2)  # Rate limiting
        
        scan_time = time.time() - start_time
        print(f"Scanned {len(symbols)} {market} symbols in {scan_time:.1f}s")
    
    # Print summary
    print(f"\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if all_results:
        print(f"Total symbols processed: {len(all_results)}")
        
        # Count by conviction level
        conviction_counts = {}
        for result in all_results:
            level = result['conviction_level']
            conviction_counts[level] = conviction_counts.get(level, 0) + 1
        
        print("\nConviction Distribution:")
        for level in range(6):
            count = conviction_counts.get(level, 0)
            if count > 0:
                action = "BUY" if level >= 2 else "WATCH"
                print(f"  Level {level}: {count} stocks ({action})")
        
        # Show trade candidates
        trade_candidates = [r for r in all_results if r['conviction_level'] >= 2]
        if trade_candidates:
            print(f"\nTRADE CANDIDATES ({len(trade_candidates)}):")
            for candidate in trade_candidates:
                print(f"  {candidate['symbol']} - Level {candidate['conviction_level']} - "
                      f"${candidate['price']:.2f} - Stop: ${candidate['stop_loss_price']:.2f}")
        else:
            print("\nNo trade candidates (Level 2+) found in test sample")
        
        # Test export functionality
        print(f"\nTesting CSV export...")
        scanner.scan_results = all_results  # Set results for export
        filename = scanner.export_results("test_scan_results.csv")
        if filename:
            print(f"Export successful: {filename}")
        else:
            print("Export failed")
        
    else:
        print("No results obtained - check internet connection or symbol validity")
    
    print("=" * 60)
    print("TEST COMPLETE")
    
    return len(all_results) > 0

if __name__ == "__main__":
    success = test_scanner()
    if success:
        print("\nDaily scanner is working correctly!")
        print("Ready to run full market scans.")
    else:
        print("\nScanner test failed - check configuration")