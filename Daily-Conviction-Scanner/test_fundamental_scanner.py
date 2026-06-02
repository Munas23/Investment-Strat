"""
Test the fundamental analysis integration
"""
from daily_conviction_scanner import DailyConvictionScanner
import pandas as pd

def test_fundamental_analysis():
    """Test a single stock to see all the fundamental data"""
    
    scanner = DailyConvictionScanner()
    
    # Test one stock to see all fundamental data
    symbol = 'AAPL'
    print(f"Testing comprehensive analysis for {symbol}...")
    print("=" * 60)
    
    result = scanner.scan_symbol(symbol)
    
    if result:
        print("TRADING INFORMATION:")
        print(f"  Symbol: {result['symbol']}")
        print(f"  Price: ${result['price']:.2f}")
        print(f"  Conviction Level: {result['conviction_level']}")
        print(f"  Action: {result['ib_action']}")
        print(f"  Position Size: {result['position_size_pct']}%")
        print(f"  Stop Loss: ${result['stop_loss_price']:.2f}")
        print(f"  Profit Target: ${result['profit_target_price']:.2f}")
        print()
        
        print("FUNDAMENTAL ANALYSIS:")
        print(f"  Fundamental Score: {result.get('fundamental_score', 'N/A')}/100")
        print(f"  Fundamental Grade: {result.get('fundamental_grade', 'N/A')}")
        print(f"  Market Cap: ${result.get('market_cap', 0):,}")
        print(f"  PE Ratio: {result.get('pe_ratio', 0):.1f}")
        print(f"  PEG Ratio: {result.get('peg_ratio', 0):.2f}")
        print()
        
        print("PROFITABILITY:")
        print(f"  ROE: {result.get('roe', 0):.1f}%")
        print(f"  ROA: {result.get('roa', 0):.1f}%")
        print(f"  Profit Margin: {result.get('profit_margin', 0):.1f}%")
        print(f"  Gross Margin: {result.get('gross_margin', 0):.1f}%")
        print()
        
        print("GROWTH:")
        print(f"  Revenue Growth: {result.get('revenue_growth', 0):.1f}%")
        print(f"  Earnings Growth: {result.get('earnings_growth', 0):.1f}%")
        print(f"  Quarterly Earnings Growth: {result.get('earnings_quarterly_growth', 0):.1f}%")
        print()
        
        print("FINANCIAL STRENGTH:")
        print(f"  Current Ratio: {result.get('current_ratio', 0):.2f}")
        print(f"  Debt-to-Equity: {result.get('debt_to_equity', 0):.3f}")
        print(f"  Free Cash Flow: ${result.get('free_cashflow', 0):,}")
        print()
        
        print("TECHNICAL ANALYSIS:")
        print(f"  Trend Strength: {result.get('trend_strength', 0):.0f}/100")
        print(f"  Breakout Power: {result.get('breakout_power', 0)}")
        print(f"  Volume Surge: {result.get('volume_surge', 0):.1f}x")
        print(f"  Momentum Points: {result.get('momentum_points', 0)}")
        print()
        
        # Show fundamental breakdown
        breakdown = result.get('fundamental_breakdown', {})
        if breakdown:
            print("FUNDAMENTAL SCORING BREAKDOWN:")
            for key, value in breakdown.items():
                if key not in ['total_score', 'grade']:
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print("=" * 60)
        print("SUCCESS: Comprehensive fundamental analysis working!")
        
        # Create a mini CSV to see the format
        scanner.scan_results = [result]  # Set the result for export
        df = pd.DataFrame([{
            'symbol': result['symbol'],
            'conviction_level': result['conviction_level'],
            'price': result['price'],
            'fundamental_score': result.get('fundamental_score', 0),
            'fundamental_grade': result.get('fundamental_grade', 'N/A'),
            'roe': result.get('roe', 0),
            'earnings_growth': result.get('earnings_growth', 0),
            'revenue_growth': result.get('revenue_growth', 0),
            'debt_to_equity': result.get('debt_to_equity', 0),
            'profit_margin': result.get('profit_margin', 0),
            'pe_ratio': result.get('pe_ratio', 0),
            'trend_strength': result.get('trend_strength', 0)
        }])
        
        print("\nSAMPLE CSV FORMAT:")
        print(df.to_string(index=False))
        
        return True
    else:
        print("Failed to get data")
        return False

if __name__ == "__main__":
    test_fundamental_analysis()