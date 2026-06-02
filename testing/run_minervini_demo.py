"""
Quick Demo Runner for Minervini Strategies
=========================================

Run this file to see Mark Minervini's strategies applied to current market data.
This will analyze several stocks using his proven methodology.
"""

from minervini_explained import demonstrate_minervini_strategies

if __name__ == "__main__":
    print("🚀 Running Mark Minervini Strategy Demonstration...")
    print("This will analyze current market data using proven champion methods\n")
    
    try:
        demonstrate_minervini_strategies()
        
        print("\n" + "="*60)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*60)
        print("You've just seen how a 2-time US Investing Champion")
        print("analyzes stocks using systematic, proven criteria.")
        print()
        print("Key Takeaways:")
        print("• Trend Template filters for institutional-quality stocks")
        print("• SEPA provides precise entry timing")  
        print("• Risk management limits losses to 7-8%")
        print("• Position sizing controls total portfolio risk")
        print("• Even champion methods still underperformed buy-and-hold")
        
    except Exception as e:
        print(f"❌ Error running demonstration: {e}")
        print("Make sure you have internet connection for live data")