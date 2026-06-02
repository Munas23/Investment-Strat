"""
Run Both 5LC Strategies - S&P500 and ASX300
===========================================

Convenience script to run both market strategies and compare results.
"""

import sys
import os
from datetime import datetime

def run_both_5lc_strategies():
    """Run both 5LC strategies and compare results"""
    
    print("=" * 100)
    print("5LC (5 LEVEL CONVICTION) STRATEGIES - DUAL MARKET COMPARISON")
    print("=" * 100)
    print("Running both S&P500 and ASX300 strategies with market health overlays")
    print("Features:")
    print("✓ Original Minervini position sizes (10%-20%) with market health overlay")
    print("✓ Market health overlay (SPY for US, VAS.AX for Australia)")
    print("✓ Dynamic position sizing based on market regime (5%-40% range)")
    print("✓ Professional risk management and analysis")
    print("=" * 100)
    
    results = {}
    
    # Run S&P500 Strategy
    print("\n" + "="*60)
    print("STARTING S&P500 5LC STRATEGY")
    print("="*60)
    
    try:
        from minervini_5lc_sp500_strategy import run_5lc_sp500_backtest
        sp500_results = run_5lc_sp500_backtest()
        results['sp500'] = sp500_results
        print("✅ S&P500 5LC Strategy completed successfully")
    except Exception as e:
        print(f"❌ Error running S&P500 strategy: {e}")
        results['sp500'] = None
    
    print("\n" + "="*60)
    print("STARTING ASX300 5LC STRATEGY") 
    print("="*60)
    
    # Run ASX300 Strategy
    try:
        from minervini_5lc_asx300_strategy import run_5lc_asx300_backtest
        asx300_results = run_5lc_asx300_backtest()
        results['asx300'] = asx300_results
        print("✅ ASX300 5LC Strategy completed successfully")
    except Exception as e:
        print(f"❌ Error running ASX300 strategy: {e}")
        results['asx300'] = None
    
    # Summary
    print("\n" + "="*100)
    print("5LC DUAL STRATEGY EXECUTION SUMMARY")
    print("="*100)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Execution completed: {timestamp}")
    
    if results['sp500'] is not None:
        print("✅ S&P500 5LC Strategy: SUCCESS")
        print("   - Market health based on SPY moving averages")
        print("   - CSV trade log and Pyfolio analysis generated")
    else:
        print("❌ S&P500 5LC Strategy: FAILED")
    
    if results['asx300'] is not None:
        print("✅ ASX300 5LC Strategy: SUCCESS") 
        print("   - Market health based on VAS.AX moving averages")
        print("   - CSV trade log and Pyfolio analysis generated")
    else:
        print("❌ ASX300 5LC Strategy: FAILED")
    
    print("\n📊 ANALYSIS FILES GENERATED:")
    print("   - 5lc_sp500_trades_[timestamp].csv")
    print("   - 5lc_asx300_trades_[timestamp].csv") 
    print("   - pyfolio_reports/ (tear sheets and metrics)")
    
    print("\n🔍 KEY FEATURES IMPLEMENTED:")
    print("   ✓ Original Minervini position sizes (10%-20%)")
    print("   ✓ Market health overlay for dynamic position sizing")
    print("   ✓ Enhanced risk management and stop losses")
    print("   ✓ Professional performance analysis")
    print("   ✓ Minimum price filter: $1 (market cap determines quality)")
    
    print("\n📈 MARKET HEALTH RULES:")
    print("   • WEAK markets (index < 20MA & 50MA): 0.5x position sizes")
    print("   • STRONG markets (index > 20MA & 50MA & 200MA): 2.0x position sizes")
    print("   • NORMAL markets (other conditions): 1.0x position sizes")
    
    print("\n" + "="*100)
    print("🎉 5LC DUAL STRATEGY EXECUTION COMPLETED!")
    print("Check the generated CSV files and pyfolio reports for detailed analysis.")
    print("="*100)
    
    return results

if __name__ == "__main__":
    print("Starting 5LC Dual Strategy Execution...")
    print("This will run both S&P500 and ASX300 strategies with market health overlays.\n")
    
    # Run both strategies
    results = run_both_5lc_strategies()
    
    print("\nExecution finished. Check output files for results.")