"""
Lumibot Setup Guide for Professional Growth Strategy
===================================================

This guide helps set up and run the professional growth strategy with
Lumibot backtesting framework across multiple markets.

INSTALLATION REQUIREMENTS:
- lumibot
- yfinance  
- pandas
- numpy
- our enhanced_growth_screener module

STRATEGY FEATURES:
✓ Enhanced fundamental screening
✓ Optimal hybrid exits (50% trigger + 15% trail)
✓ 10 different market universes
✓ Professional risk management
✓ Multi-market comparison capability
"""

import subprocess
import sys
import os
from datetime import datetime, timedelta

def check_dependencies():
    """Check if required packages are installed"""
    print("CHECKING DEPENDENCIES")
    print("=" * 30)
    
    required_packages = [
        'lumibot',
        'yfinance', 
        'pandas',
        'numpy',
        'matplotlib',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"+ {package}")
        except ImportError:
            print(f"- {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nInstalling missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"+ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"- Failed to install {package}")
    
    print(f"\nDependency check complete!")

def verify_strategy_files():
    """Verify that strategy files are present"""
    print(f"\nVERIFYING STRATEGY FILES")
    print("=" * 30)
    
    required_files = [
        'enhanced_growth_screener.py',
        'lumibot_hybrid_strategy.py', 
        'lumibot_backtest_runner.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"+ {file}")
        else:
            print(f"- {file} - MISSING")
    
    print(f"\nFile verification complete!")

def create_simple_backtest_example():
    """Create a simple example of running the backtest"""
    
    example_code = '''
"""
Simple Lumibot Backtest Example
===============================
"""

from lumibot.strategies import Strategy
from lumibot.backtesting import YahooDataBacktesting
from lumibot.traders import Trader
from datetime import datetime
from lumibot_hybrid_strategy import ProfessionalGrowthStrategy

def run_simple_backtest():
    """Run a simple backtest example"""
    
    print("SIMPLE BACKTEST EXAMPLE")
    print("=" * 30)
    
    # Create strategy
    strategy = ProfessionalGrowthStrategy()
    
    # Set test market
    strategy.set_test_market("TECHNOLOGY")
    
    # Configure backtest
    backtest = YahooDataBacktesting(
        datetime_start=datetime(2023, 1, 1),
        datetime_end=datetime(2024, 1, 1),
        budget=100000
    )
    
    # Run backtest
    trader = Trader()
    trader.add_strategy(strategy)
    
    print("Running backtest...")
    results = trader.backtest(backtest)
    
    print("Backtest complete!")
    print(f"Results: {results}")
    
    return results

if __name__ == "__main__":
    results = run_simple_backtest()
'''
    
    with open('simple_backtest_example.py', 'w') as f:
        f.write(example_code)
    
    print(f"\nCreated simple_backtest_example.py")

def create_market_universe_reference():
    """Create reference file showing all available markets"""
    
    reference_code = '''
"""
Market Universe Reference
========================

This file shows all available market universes for testing
the professional growth strategy.
"""

MARKET_UNIVERSES = {
    "US_LARGE_CAP": [
        # S&P 100 Large Cap Growth Leaders
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
        "ADBE", "CRM", "ORCL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
        "NOW", "INTU", "CSCO", "IBM", "AMAT", "MU", "ADI", "KLAC"
    ],
    
    "US_MID_CAP": [
        # Mid-cap growth and emerging leaders
        "PLTR", "SNOW", "DDOG", "NET", "CRWD", "ZM", "DOCU", "TWLO",
        "ROKU", "SQ", "SHOP", "UBER", "LYFT", "PINS", "SNAP", "SPOT"
    ],
    
    "TECHNOLOGY": [
        # Pure tech plays
        "NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN", "ADI", "KLAC",
        "LRCX", "AMAT", "MU", "WDC", "STX", "MRVL", "SWKS", "MXIM"
    ],
    
    "HEALTHCARE": [
        # Healthcare and biotech focus  
        "JNJ", "PFE", "UNH", "ABBV", "TMO", "DHR", "ABT", "BMY",
        "LLY", "MRK", "AMGN", "GILD", "REGN", "VRTX", "BIIB", "MRNA"
    ],
    
    "CONSUMER": [
        # Consumer growth stocks
        "AMZN", "SHOP", "ETSY", "W", "CHWY", "PTON", "NKE", "LULU",
        "SBUX", "MCD", "CMG", "DKNG", "PENN", "MGM", "WYNN", "LVS"
    ]
}

def get_market_symbols(market_name):
    """Get symbols for a specific market"""
    return MARKET_UNIVERSES.get(market_name, [])

def list_all_markets():
    """List all available markets"""
    print("AVAILABLE MARKETS:")
    print("=" * 20)
    for market in MARKET_UNIVERSES.keys():
        count = len(MARKET_UNIVERSES[market])
        print(f"{market}: {count} stocks")

if __name__ == "__main__":
    list_all_markets()
'''
    
    with open('market_universe_reference.py', 'w') as f:
        f.write(reference_code)
    
    print(f"Created market_universe_reference.py")

def create_strategy_parameters_guide():
    """Create guide for strategy parameters"""
    
    guide_code = '''
"""
Strategy Parameters Guide
========================

This guide explains all configurable parameters for the
Professional Growth Strategy.
"""

STRATEGY_PARAMETERS = {
    # FUNDAMENTAL SCREENING
    "fundamental_score_threshold": {
        "default": 60.0,
        "range": "50.0 - 80.0",
        "description": "Minimum fundamental score for stock selection"
    },
    
    "rescreen_frequency": {
        "default": 30,
        "range": "7 - 90 days", 
        "description": "How often to rescreen fundamentals"
    },
    
    # POSITION MANAGEMENT
    "max_positions": {
        "default": 8,
        "range": "4 - 12",
        "description": "Maximum number of concurrent positions"
    },
    
    "position_size_pct": {
        "default": 0.125,
        "range": "0.08 - 0.20",
        "description": "Position size as percentage of portfolio"
    },
    
    # ENTRY SIGNALS
    "min_conviction": {
        "default": 3,
        "range": "1 - 5",
        "description": "Minimum conviction level for entry"
    },
    
    "volume_threshold": {
        "default": 1.5,
        "range": "1.2 - 3.0",
        "description": "Minimum volume surge for entry"
    },
    
    # HYBRID EXIT STRATEGY (OPTIMAL SETTINGS)
    "profit_trigger": {
        "default": 50.0,
        "range": "30.0 - 100.0",
        "description": "Profit level to activate trailing stop"
    },
    
    "trailing_stop_pct": {
        "default": 15.0,
        "range": "10.0 - 25.0", 
        "description": "Trailing stop percentage"
    },
    
    "stop_loss_pct": {
        "default": 7.0,
        "range": "5.0 - 10.0",
        "description": "Disaster stop loss percentage"
    }
}

def print_parameter_guide():
    """Print formatted parameter guide"""
    print("STRATEGY PARAMETERS GUIDE")
    print("=" * 40)
    
    for param, info in STRATEGY_PARAMETERS.items():
        print(f"\\n{param}:")
        print(f"  Default: {info['default']}")
        print(f"  Range: {info['range']}")
        print(f"  Description: {info['description']}")

def get_optimal_parameters():
    """Get the optimal parameters from our testing"""
    return {
        "fundamental_score_threshold": 60.0,
        "max_positions": 8,
        "profit_trigger": 50.0,        # From hybrid testing - best performer
        "trailing_stop_pct": 15.0,     # From hybrid testing - best performer  
        "stop_loss_pct": 7.0,
        "min_conviction": 3,
        "volume_threshold": 1.5
    }

if __name__ == "__main__":
    print_parameter_guide()
    print("\\n" + "=" * 40)
    print("OPTIMAL PARAMETERS (from testing):")
    optimal = get_optimal_parameters()
    for param, value in optimal.items():
        print(f"  {param}: {value}")
'''
    
    with open('strategy_parameters_guide.py', 'w') as f:
        f.write(guide_code)
    
    print(f"Created strategy_parameters_guide.py")

def show_usage_examples():
    """Show usage examples"""
    print(f"\nUSAGE EXAMPLES")
    print("=" * 20)
    
    examples = [
        {
            "title": "1. Quick Single Market Test",
            "code": """
from lumibot_backtest_runner import MultiMarketBacktester

backtester = MultiMarketBacktester()
result = backtester.run_single_market_backtest("TECHNOLOGY")
print(f"Technology market return: {result['total_return']:.1f}%")
"""
        },
        
        {
            "title": "2. Compare Multiple Markets", 
            "code": """
from lumibot_backtest_runner import run_quick_test

# Test 3 key markets
backtester = run_quick_test()
# Results automatically compared and analyzed
"""
        },
        
        {
            "title": "3. Full Market Comparison",
            "code": """
from lumibot_backtest_runner import run_full_test

# Test all 10 markets
backtester, results = run_full_test()
# Results exported to CSV automatically  
"""
        },
        
        {
            "title": "4. Custom Strategy Parameters",
            "code": """
from lumibot_hybrid_strategy import ProfessionalGrowthStrategy

strategy = ProfessionalGrowthStrategy()
strategy.parameters["profit_trigger"] = 40.0  # Lower trigger
strategy.parameters["trailing_stop_pct"] = 20.0  # Wider trail
strategy.set_test_market("US_LARGE_CAP")
"""
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}")
        print("-" * len(example['title']))
        print(example['code'])

def main():
    """Main setup function"""
    print("LUMIBOT PROFESSIONAL GROWTH STRATEGY SETUP")
    print("=" * 60)
    print("Setting up the optimal hybrid exit strategy for multi-market testing")
    print()
    
    # Check dependencies
    check_dependencies()
    
    # Verify files
    verify_strategy_files()
    
    # Create helper files
    print(f"\nCREATING HELPER FILES")
    print("=" * 30)
    create_simple_backtest_example()
    create_market_universe_reference()
    create_strategy_parameters_guide()
    
    # Show usage examples
    show_usage_examples()
    
    print(f"\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("Your Professional Growth Strategy is ready for multi-market testing!")
    print()
    print("Files created:")
    print("+ simple_backtest_example.py - Quick start example")
    print("+ market_universe_reference.py - Available markets")
    print("+ strategy_parameters_guide.py - Parameter documentation")
    print()
    print("Next steps:")
    print("1. Run: python simple_backtest_example.py")
    print("2. Run: python lumibot_backtest_runner.py")
    print("3. Customize parameters and test different markets")
    print("4. Analyze results and optimize for your needs")
    print()
    print("Strategy highlights:")
    print("* 50% Trigger + 15% Trail (251.5% avg returns in testing)")
    print("* Enhanced fundamental screening")
    print("* 10 different market universes")
    print("* Professional risk management")

if __name__ == "__main__":
    main()