"""
Quick Strategy Test - Tests a few strategies first to verify everything works
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from technical_indicators import StrategyConditions
import warnings

warnings.filterwarnings('ignore')

def quick_test():
    """Quick test of strategy framework"""
    print("QUICK STRATEGY TEST")
    print("=" * 30)
    print("Testing framework with 5 strategies on AAPL")
    print()
    
    # Get AAPL data for testing
    print("Fetching AAPL data...")
    ticker = yf.Ticker("AAPL")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)  # 2 years
    data = ticker.history(start=start_date, end=end_date)
    
    if data.empty:
        print("Error: No data retrieved")
        return
    
    # Standardize column names
    data.columns = [col.lower() for col in data.columns]
    print(f"Got {len(data)} days of data")
    
    # Create strategy conditions
    print("\nCalculating technical indicators...")
    conditions = StrategyConditions(data)
    
    # Test 5 strategies
    strategies_to_test = [
        ("Golden Cross", "golden_cross"),
        ("Fast MA Cross", "fast_ma_cross"),
        ("Strong Momentum", "strong_momentum"),
        ("Volume Breakout", "volume_breakout"),
        ("RSI Recovery", "rsi_recovery")
    ]
    
    print("\nTesting strategies:")
    for name, method in strategies_to_test:
        try:
            if hasattr(conditions, method):
                signals = getattr(conditions, method)()
                signal_count = signals.sum() if not signals.empty else 0
                print(f"  {name}: {signal_count} buy signals")
                
                # Show last few signals
                if signal_count > 0:
                    last_signals = signals[signals == True].tail(3)
                    if not last_signals.empty:
                        print(f"    Recent signals: {list(last_signals.index.strftime('%Y-%m-%d'))}")
            else:
                print(f"  {name}: Method not found")
        except Exception as e:
            print(f"  {name}: Error - {str(e)[:50]}...")
    
    # Test one strategy in detail
    print(f"\nDetailed test of Golden Cross strategy:")
    try:
        signals = conditions.golden_cross()
        
        # Show data quality
        print(f"  Total data points: {len(data)}")
        print(f"  Valid signals: {len(signals.dropna())}")
        print(f"  Buy signals: {signals.sum()}")
        
        # Show moving averages
        sma_50_latest = conditions.data['sma_50'].iloc[-1]
        sma_200_latest = conditions.data['sma_200'].iloc[-1] 
        current_price = data['close'].iloc[-1]
        
        print(f"  Current price: ${current_price:.2f}")
        print(f"  50-day MA: ${sma_50_latest:.2f}")
        print(f"  200-day MA: ${sma_200_latest:.2f}")
        print(f"  Golden cross active: {sma_50_latest > sma_200_latest}")
        
    except Exception as e:
        print(f"  Detailed test error: {e}")
    
    print("\nQuick test completed!")
    print("\nIf this looks good, run the full test with:")
    print("python strategy_tester.py")

def test_asx_stock():
    """Test with ASX stock to verify international support"""
    print(f"\n{'='*30}")
    print("TESTING ASX STOCK (CBA.AX)")
    print("="*30)
    
    try:
        ticker = yf.Ticker("CBA.AX")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 year
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            print("No ASX data available")
            return
            
        data.columns = [col.lower() for col in data.columns]
        print(f"Got {len(data)} days of CBA.AX data")
        
        conditions = StrategyConditions(data)
        
        # Test a few strategies
        test_strategies = [
            ("Fast MA Cross", "fast_ma_cross"),
            ("Moderate Momentum", "moderate_momentum")
        ]
        
        for name, method in test_strategies:
            try:
                signals = getattr(conditions, method)()
                signal_count = signals.sum()
                print(f"  {name}: {signal_count} signals")
            except Exception as e:
                print(f"  {name}: Error - {str(e)[:30]}...")
        
        current_price = data['close'].iloc[-1]
        print(f"  Current CBA.AX price: {current_price:.2f} AUD")
        
    except Exception as e:
        print(f"ASX test error: {e}")

def show_strategy_list():
    """Show all 20 strategies that will be tested"""
    print(f"\n{'='*50}")
    print("ALL 20 STRATEGIES TO BE TESTED")
    print("="*50)
    
    strategies = [
        "1. Golden Cross (50MA > 200MA)",
        "2. Fast MA Cross (10MA > 20MA)",  
        "3. Triple MA Alignment (10 > 20 > 50)",
        "4. EMA Cross (EMA12 > EMA26)",
        "5. Strong Momentum (Up 40% in 60 days)",
        "6. Moderate Momentum (Up 10% in 20 days)",
        "7. Momentum + MA Confirmation",
        "8. Acceleration Pattern",
        "9. Volume Breakout (New high + 2x volume)",
        "10. Volatility Breakout",
        "11. Range Breakout (60-day range break)",
        "12. Gap Up Follow Through", 
        "13. RSI Recovery (Oversold to overbought)",
        "14. MACD Bullish Cross",
        "15. Bollinger Band Squeeze",
        "16. Stochastic Oversold Recovery",
        "17. Pullback Entry (Trend continuation)",
        "18. Cup and Handle Pattern",
        "19. Higher Highs/Higher Lows Trend",
        "20. Support/Resistance Breakout"
    ]
    
    for strategy in strategies:
        print(f"  {strategy}")
    
    print(f"\nEach strategy will be tested on:")
    print("  - US stocks (AAPL, MSFT, GOOGL, etc.)")
    print("  - ASX stocks (CBA.AX, BHP.AX, etc.)")  
    print("  - UK stocks (SHEL.L, AZN.L, etc.)")
    print("  - German stocks (SAP.DE, SIE.DE)")
    print("  - Over 5 years of historical data")
    
    print(f"\nTotal tests: 20 strategies × 8+ stocks = 160+ individual tests")

if __name__ == "__main__":
    quick_test()
    test_asx_stock()
    show_strategy_list()
    
    print(f"\n{'='*50}")
    print("READY FOR FULL TESTING!")
    print("="*50)
    print("Run: python strategy_tester.py")
    print("This will test all 20 strategies over 5 years")
    print("Expected runtime: 5-10 minutes")