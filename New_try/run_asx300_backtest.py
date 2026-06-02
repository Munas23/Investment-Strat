#!/usr/bin/env python3
"""
Simple runner for the ASX300 Consolidation Conviction Strategy backtest
"""

from consolidation_conviction_asx300 import run_consolidation_conviction_asx300_backtest
import sys
from datetime import datetime

def main():
    """Main runner function"""
    print("=" * 60)
    print("ASX300 CONSOLIDATION CONVICTION STRATEGY BACKTEST RUNNER")
    print("=" * 60)
    print(f"Starting ASX backtest at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Run the backtest
        results = run_consolidation_conviction_asx300_backtest()
        
        if results:
            print("\n" + "=" * 60)
            print("ASX300 BACKTEST COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("Check the following files:")
            print("- consolidation_conviction_asx300_trades_*.csv - Trade log")
            print("- pyfolio_reports/ - Performance analysis vs VAS.AX")
            print("- Console output above - Summary statistics")
            print("=" * 60)
            return 0
        else:
            print("\nASX300 Backtest failed - check error messages above")
            return 1
            
    except KeyboardInterrupt:
        print("\nASX300 Backtest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error in ASX300 backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)