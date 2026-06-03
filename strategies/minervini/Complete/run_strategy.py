"""
Quick Start Script for Minervini Complete Championship Strategy
==============================================================

Run this script to execute the complete Minervini strategy with Lumibot backtesting.
"""

import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['lumibot', 'yfinance', 'pandas', 'numpy']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\nInstalling missing packages...")
        for package in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("Dependencies installed!")
    
    return len(missing) == 0

def main():
    """Main execution"""
    print("MARK MINERVINI'S COMPLETE CHAMPIONSHIP STRATEGY")
    print("=" * 60)
    print("Checking dependencies...")
    
    if not check_dependencies():
        print("Error installing dependencies. Please install manually:")
        print("pip install lumibot yfinance pandas numpy")
        return
    
    print("\nStarting strategy...")
    print("This will:")
    print("1. Screen the S&P 500 for fundamental leaders")
    print("2. Apply technical breakout timing")
    print("3. Execute championship risk management")
    print("4. Generate detailed results")
    print()
    
    try:
        # Import and run the strategy
        from minervini_lumibot_strategy import run_minervini_complete_backtest
        
        results = run_minervini_complete_backtest()
        
        if results:
            print("\n🎉 STRATEGY COMPLETED SUCCESSFULLY!")
            print("\nKey Features Demonstrated:")
            print("✓ Fundamental screening (>60% quality score)")
            print("✓ Conviction-based entries (1-5 levels)")
            print("✓ Championship position sizing (20-40%)")
            print("✓ Professional risk management (7% stops, 50% targets)")
            print("✓ Complete S&P 500 universe testing")
            print("\nResults exported to CSV file for detailed analysis.")
        else:
            print("❌ Strategy failed - check error messages above")
            
    except Exception as e:
        print(f"Error running strategy: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all files are in the same folder")
        print("2. Check internet connection for data download")
        print("3. Ensure Python has sufficient permissions")

if __name__ == "__main__":
    main()