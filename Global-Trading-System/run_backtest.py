"""
Global Multi-Market Backtesting System
Main execution script for testing strategies across ASX300, S&P500, Russell2000, FTSE, DAX
"""

import os
import sys
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add strategies directory to path
sys.path.append('strategies')

# Import our components
from global_backtester import GlobalBacktester
from strategies.momentum_strategy import GlobalMomentumStrategy
from strategies.breakout_strategy import GlobalBreakoutStrategy

def run_sample_backtest():
    """Run a sample backtest to demonstrate the system"""
    print("="*80)
    print("GLOBAL MULTI-MARKET BACKTESTING SYSTEM")
    print("="*80)
    print("Testing strategies across global markets:")
    print("- ASX300 (Australia)")
    print("- S&P500 (USA)")
    print("- Russell2000 (USA Small Cap)")
    print("- FTSE (UK)")
    print("- DAX (Germany)")
    print("="*80)
    
    # Initialize backtester
    backtester = GlobalBacktester()
    
    # Define test parameters
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')  # 2 years
    
    print(f"Backtest Period: {start_date} to {end_date}")
    print(f"Testing with limited symbols for demonstration...")
    
    # Create strategy instances
    strategies = [
        GlobalMomentumStrategy(
            name="Global_Momentum",
            config_path="config/strategy_config.json"
        ),
        GlobalBreakoutStrategy(
            name="Global_Breakout", 
            config_path="config/strategy_config.json"
        )
    ]
    
    # Define markets to test (start with a subset for demonstration)
    test_markets = ['SP500', 'ASX300']  # Start with 2 markets for demo
    
    print(f"Testing {len(strategies)} strategies on {len(test_markets)} markets")
    print("Strategies:")
    for strategy in strategies:
        print(f"  - {strategy.name}")
    print("Markets:")
    for market in test_markets:
        print(f"  - {market}")
    
    # Run backtest
    try:
        results = backtester.run_multi_market_backtest(
            strategies=strategies,
            markets=test_markets,
            start_date=start_date,
            end_date=end_date,
            max_symbols_per_market=20,  # Limit to 20 symbols per market for demo
            download_fresh_data=True
        )
        
        print("\n" + "="*80)
        print("BACKTEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("Results files generated in 'results' directory:")
        print("- Detailed trade logs (CSV)")
        print("- Portfolio performance data (CSV)")
        print("- Performance statistics (JSON)")
        print("- Summary report (CSV)")
        print("- Performance charts (PNG)")
        
        return results
        
    except Exception as e:
        print(f"\nError running backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_full_backtest():
    """Run full backtest across all markets"""
    print("="*80)
    print("RUNNING FULL GLOBAL BACKTEST")
    print("="*80)
    
    # Initialize backtester
    backtester = GlobalBacktester()
    
    # Define parameters for full backtest
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')  # 3 years
    
    # Create all strategies
    strategies = [
        GlobalMomentumStrategy(
            name="Global_Momentum_Full",
            config_path="config/strategy_config.json"
        ),
        GlobalBreakoutStrategy(
            name="Global_Breakout_Full",
            config_path="config/strategy_config.json"
        )
    ]
    
    # All markets
    all_markets = ['SP500', 'ASX300', 'RUSSELL2000', 'FTSE', 'DAX']
    
    print(f"Period: {start_date} to {end_date}")
    print(f"Strategies: {len(strategies)}")
    print(f"Markets: {len(all_markets)}")
    print("This will take longer due to data download and processing...")
    
    # Run full backtest
    results = backtester.run_multi_market_backtest(
        strategies=strategies,
        markets=all_markets,
        start_date=start_date,
        end_date=end_date,
        max_symbols_per_market=100,  # More symbols for full test
        download_fresh_data=True
    )
    
    return results

def check_system_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'matplotlib', 
        'seaborn', 'talib', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main execution function"""
    print("Global Trading System - Multi-Market Backtester")
    print("Supports: ASX300, S&P500, Russell2000, FTSE, DAX")
    print()
    
    # Check requirements
    if not check_system_requirements():
        print("Please install required packages first.")
        return
    
    # Create directories if they don't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Menu
    while True:
        print("\nSelect an option:")
        print("1. Run Sample Backtest (Quick demo - 2 markets, 20 stocks each)")
        print("2. Run Full Backtest (All 5 markets, more stocks)")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            print("\nStarting sample backtest...")
            results = run_sample_backtest()
            
            if results:
                print("\nSample backtest completed! Check the 'results' directory for outputs.")
            else:
                print("\nSample backtest failed. Check error messages above.")
        
        elif choice == '2':
            print("\nStarting full backtest...")
            print("WARNING: This will download a lot of data and take significant time.")
            confirm = input("Continue? (y/n): ").strip().lower()
            
            if confirm == 'y':
                results = run_full_backtest()
                if results:
                    print("\nFull backtest completed! Check the 'results' directory for outputs.")
                else:
                    print("\nFull backtest failed. Check error messages above.")
            else:
                print("Full backtest cancelled.")
        
        elif choice == '3':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()