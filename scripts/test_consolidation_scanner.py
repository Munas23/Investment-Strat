"""
Test script for the Consolidation Conviction Scanner
===================================================

Quick test to demonstrate the scanner functionality
"""

from consolidation_conviction_scanner import ConsolidationConvictionScanner

def test_scanner():
    """Test the consolidation scanner with sample data"""
    
    print("Testing Consolidation Conviction Scanner")
    print("="*50)
    
    # Initialize scanner
    scanner = ConsolidationConvictionScanner()
    
    # Test with a few well-known symbols
    test_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA',
        'META', 'AMZN', 'NFLX', 'AMD', 'CRM'
    ]
    
    print(f"\nTesting {len(test_symbols)} symbols for consolidation patterns...")
    print("Looking for stocks with 30%+ gains in 3-6 months but low recent ATR")
    print("-" * 80)
    
    results = []
    for symbol in test_symbols:
        try:
            result = scanner.scan_symbol(symbol)
            if result:
                results.append(result)
                
                level = result['conviction_level']
                price = result['price']
                gain_3_6m = result['medium_term_gain']
                atr_contraction = result['best_atr_contraction']
                recent_2w = result['gain_2w_pct']
                
                action = "BUY" if level >= 2 else "WATCH"
                
                print(f"{symbol:<6} | Level {level} | ${price:>8.2f} | "
                      f"3-6M: {gain_3_6m:>6.1f}% | ATR: {atr_contraction:>5.2f} | "
                      f"2W: {recent_2w:>5.1f}% | {action}")
            else:
                print(f"{symbol:<6} | Filtered out (likely insufficient 3-6M gain or other criteria)")
        
        except Exception as e:
            print(f"{symbol:<6} | ERROR: {e}")
    
    print("-" * 80)
    
    # Summary
    consolidation_candidates = [r for r in results if r['conviction_level'] >= 2]
    high_conviction = [r for r in results if r['conviction_level'] >= 3]
    
    print(f"\nRESULTS SUMMARY:")
    print(f"Total tested: {len(test_symbols)}")
    print(f"Valid results: {len(results)}")
    print(f"Trade candidates (Level 2+): {len(consolidation_candidates)}")
    print(f"High conviction (Level 3+): {len(high_conviction)}")
    
    if high_conviction:
        print(f"\nHIGH CONVICTION CONSOLIDATION PATTERNS:")
        for result in sorted(high_conviction, key=lambda x: x['conviction_level'], reverse=True):
            print(f"  {result['symbol']}: Level {result['conviction_level']} - "
                  f"3-6M gain: {result['medium_term_gain']:.1f}% - "
                  f"ATR contraction: {result['best_atr_contraction']:.2f}")
    
    print("\nKEY INSIGHTS:")
    print("• This scanner focuses on stocks AFTER big moves, during consolidation")
    print("• Requires 30%+ gains over 3-6 months (strong medium-term performance)")  
    print("• Rewards low/contracting ATR (indicates consolidation, not breakout)")
    print("• Lower weight on recent momentum (we want consolidation, not continuation)")
    print("• Perfect for catching the next leg up after a consolidation phase")

if __name__ == "__main__":
    test_scanner()