#!/usr/bin/env python3
"""
Run Daily Conviction Scanner for August 19th, 2024
Non-interactive execution for both markets
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path so we can import the scanner
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daily_conviction_scanner import DailyConvictionScanner

def run_scanner_august19():
    """Run scanner for August 19th, 2024"""
    
    print("=" * 80)
    print("DAILY CONVICTION SCANNER - AUGUST 19TH, 2024")
    print("=" * 80)
    print("Running automated scan for both US and ASX markets")
    print("Target date: August 19th, 2024")
    print()
    
    scanner = DailyConvictionScanner()
    
    try:
        all_results = []
        
        # Scan US market
        print("Scanning US Market (S&P 500)...")
        us_symbols = scanner.get_sp500_symbols()
        print(f"Analyzing {len(us_symbols)} S&P 500 stocks...")
        us_results = scanner.scan_market(us_symbols, "US Market")
        all_results.extend(us_results)
        
        # Scan ASX market  
        print("\nScanning ASX Market (ASX300)...")
        asx_symbols = scanner.get_asx300_symbols()
        print(f"Analyzing {len(asx_symbols)} ASX300 stocks...")
        asx_results = scanner.scan_market(asx_symbols, "ASX Market")
        all_results.extend(asx_results)
        
        # Set results for export
        scanner.all_results = all_results
        
        # Print summary
        scanner.print_summary()
        
        # Export results 
        filename = scanner.export_results()
        
        # Rename file to include August 19th date
        if filename and os.path.exists(filename):
            new_filename = filename.replace(filename.split('_')[-1], "20240819_automated.csv")
            os.rename(filename, new_filename)
            filename = new_filename
        
        if filename:
            print(f"\nResults exported to: {filename}")
            print("CSV file ready for analysis")
        
        # Show summary
        top_picks = [r for r in all_results if r['conviction_level'] >= 2]
        trade_ready = [r for r in all_results if r['conviction_level'] >= 4]
        
        print(f"\nSUMMARY FOR AUGUST 19TH, 2024:")
        print(f"Total candidates: {len(top_picks)}")
        print(f"Trade-ready (Level 4+): {len(trade_ready)}")
        
        if trade_ready:
            print("\nTOP TRADE-READY PICKS:")
            for pick in sorted(trade_ready, key=lambda x: x['conviction_level'], reverse=True)[:10]:
                print(f"  {pick['symbol']}: Level {pick['conviction_level']}, "
                      f"Daily Change: {pick['daily_change_pct']:.1f}%, "
                      f"Volume: {pick['volume_surge']:.1f}x")
        
        return filename
        
    except Exception as e:
        print(f"Error during scan: {e}")
        return None

if __name__ == "__main__":
    result_file = run_scanner_august19()
    if result_file:
        print(f"\nScan completed successfully. Results saved to: {result_file}")
    else:
        print("\nScan failed.")