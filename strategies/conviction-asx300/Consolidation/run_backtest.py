#!/usr/bin/env python3
"""
Simple runner for the Consolidation Conviction Strategy backtest
"""

from consolidation_conviction_backtest import run_consolidation_conviction_backtest
import sys
from datetime import datetime

def main():
    """Main runner function"""
    print("=" * 60)
    print("CONSOLIDATION CONVICTION STRATEGY BACKTEST RUNNER")
    print("=" * 60)
    print(f"Starting backtest at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run the backtest
        results = run_consolidation_conviction_backtest()
        
        if results:
            print("\n" + "=" * 60)
            print("BACKTEST COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("Check the following files:")
            print("- consolidation_conviction_trades_*.csv - Trade log")
            print("- pyfolio_reports/ - Performance analysis")
            print("- Console output above - Summary statistics")
            print("=" * 60)
            return 0
        else:
            print("\nBacktest failed - check error messages above")
            return 1
            
    except KeyboardInterrupt:
        print("\nBacktest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)