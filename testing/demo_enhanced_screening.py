"""
Demo Enhanced Fundamental Growth Screening
=========================================

This is a simple demonstration of the enhanced fundamental growth screener
that can be run to show how it identifies quality growth stocks for trading.

DEMO FEATURES:
1. Screen a sample set of stocks
2. Show detailed scoring breakdown
3. Identify growth leaders
4. Compare with traditional metrics
5. Export results for analysis

This demo can be run standalone to see the screener in action.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

from enhanced_growth_screener import EnhancedGrowthScreener

warnings.filterwarnings('ignore')

def demo_enhanced_screening():
    """
    Demonstrate enhanced fundamental growth screening
    """
    print("ENHANCED FUNDAMENTAL GROWTH SCREENING DEMO")
    print("=" * 60)
    print("This demo shows how the enhanced screener identifies")
    print("high-quality growth stocks for trading strategies")
    print("=" * 60)
    
    # Initialize screener
    screener = EnhancedGrowthScreener()
    
    # Demo stock universe - mix of different types
    demo_stocks = [
        # High growth tech leaders
        'NVDA', 'AMD', 'TSLA', 'GOOGL', 'META', 'AMZN', 'NFLX',
        
        # SaaS/Cloud growth
        'CRM', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'NET', 'DDOG',
        
        # Traditional tech
        'AAPL', 'MSFT', 'ADBE', 'ORCL', 'IBM',
        
        # Emerging growth
        'SHOP', 'SQ', 'ROKU', 'ZM', 'DOCU', 'TWLO',
        
        # Healthcare/Biotech
        'JNJ', 'PFE', 'MRNA', 'BNTX', 'REGN', 'VRTX',
        
        # Traditional value
        'JPM', 'KO', 'PG', 'WMT', 'UNH'
    ]
    
    print(f"\nDEMO UNIVERSE: {len(demo_stocks)} stocks")
    print("Mix of growth, tech, healthcare, and value stocks")
    
    # Screen the universe
    print(f"\nStarting enhanced fundamental screening...")
    screening_results = screener.screen_stock_universe(demo_stocks)
    
    # Rank results
    ranked_results = screener.rank_growth_stocks(screening_results)
    
    # Get growth leaders at different thresholds
    thresholds = [50, 60, 70, 80]
    threshold_analysis = {}
    
    print(f"\nTHRESHOLD ANALYSIS:")
    print("=" * 50)
    
    for threshold in thresholds:
        leaders = screener.get_growth_leaders(ranked_results, threshold)
        threshold_analysis[threshold] = leaders
        
        print(f"\n{threshold}% Threshold: {len(leaders)} stocks qualify")
        if leaders:
            print(f"Leaders: {', '.join(leaders[:10])}")
            if len(leaders) > 10:
                print(f"... and {len(leaders)-10} more")
    
    # Detailed analysis of top performers
    print(f"\nDETAILED ANALYSIS - TOP 10 STOCKS")
    print("=" * 80)
    
    if ranked_results:
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<6} {'Rev1Y':<7} {'Rev3Y':<7} {'ROE':<6} {'Gross':<6} {'Debt/Eq':<7}")
        print("-" * 80)
        
        for i, result in enumerate(ranked_results[:10]):
            rank = i + 1
            symbol = result['symbol']
            score = result['score_percentage']
            
            # Extract key metrics
            rev_1y = result['criteria'].get('revenue_growth_1y', {}).get('value', 0)
            rev_3y = result['criteria'].get('revenue_growth_3y_avg', {}).get('value', 0)
            roe = result['criteria'].get('roe', {}).get('value', 0)
            gross = result['criteria'].get('gross_margins', {}).get('value', 0)
            debt_eq = result['criteria'].get('debt_to_equity', {}).get('value', 0)
            
            print(f"{rank:<4} {symbol:<8} {score:>5.1f}% {rev_1y:>6.1f}% {rev_3y:>6.1f}% "
                  f"{roe:>5.1f}% {gross:>5.1f}% {debt_eq:>6.2f}")
    
    # Show screening breakdown for top stock
    if ranked_results:
        top_stock = ranked_results[0]
        print(f"\nDETAILED BREAKDOWN - {top_stock['symbol']} (Top Rated)")
        print("=" * 60)
        
        print(f"Overall Score: {top_stock['score_percentage']:.1f}% ({top_stock['rating']})")
        print(f"\nCriteria Breakdown:")
        
        categories = {
            'GROWTH': ['revenue_growth_1y', 'revenue_growth_3y_avg', 'quarterly_growth', 
                      'earnings_growth', 'sales_acceleration'],
            'PROFITABILITY': ['roe', 'gross_margins', 'operating_margins', 'margin_improvement'],
            'FINANCIAL STRENGTH': ['debt_to_equity', 'current_ratio', 'free_cashflow_positive'],
            'MARKET': ['market_cap', 'price_volume']
        }
        
        for category, criteria in categories.items():
            print(f"\n{category}:")
            category_score = 0
            category_max = 0
            
            for criterion in criteria:
                if criterion in top_stock['criteria']:
                    data = top_stock['criteria'][criterion]
                    status = "✅" if data['pass'] else "❌"
                    print(f"  {status} {criterion.replace('_', ' ').title()}: {data['value']} "
                          f"(Weight: {data['weight']})")
                    category_max += data['weight']
                    if data['pass']:
                        category_score += data['weight']
            
            if category_max > 0:
                category_pct = (category_score / category_max) * 100
                print(f"  Category Score: {category_score}/{category_max} ({category_pct:.1f}%)")
    
    # Summary insights
    print(f"\nSCREENING INSIGHTS:")
    print("=" * 40)
    
    total_stocks = len(demo_stocks)
    valid_results = len(ranked_results)
    
    if threshold_analysis:
        leaders_60 = len(threshold_analysis.get(60, []))
        leaders_70 = len(threshold_analysis.get(70, []))
        
        print(f"• {valid_results}/{total_stocks} stocks had sufficient data for screening")
        print(f"• {leaders_60} stocks ({leaders_60/total_stocks*100:.1f}%) score >60% (good quality)")
        print(f"• {leaders_70} stocks ({leaders_70/total_stocks*100:.1f}%) score >70% (excellent quality)")
        
        if ranked_results:
            top_score = ranked_results[0]['score_percentage']
            avg_score = np.mean([r['score_percentage'] for r in ranked_results])
            print(f"• Top score: {top_score:.1f}% | Average score: {avg_score:.1f}%")
    
    # Growth vs Value comparison
    growth_stocks = ['NVDA', 'TSLA', 'SNOW', 'PLTR', 'SHOP', 'ROKU']
    value_stocks = ['JPM', 'KO', 'PG', 'WMT', 'UNH']
    
    growth_scores = []
    value_scores = []
    
    for result in ranked_results:
        if result['symbol'] in growth_stocks:
            growth_scores.append(result['score_percentage'])
        elif result['symbol'] in value_stocks:
            value_scores.append(result['score_percentage'])
    
    if growth_scores and value_scores:
        avg_growth_score = np.mean(growth_scores)
        avg_value_score = np.mean(value_scores)
        
        print(f"\nGROWTH vs VALUE COMPARISON:")
        print(f"• Average Growth Stock Score: {avg_growth_score:.1f}%")
        print(f"• Average Value Stock Score: {avg_value_score:.1f}%")
        print(f"• Growth Premium: {avg_growth_score - avg_value_score:.1f} points")
    
    # Final recommendation
    print(f"\nRECOMMENDATION:")
    print("=" * 30)
    
    if threshold_analysis.get(60, []):
        recommended_stocks = threshold_analysis[60][:5]
        print("Top recommended stocks for growth strategies:")
        for i, stock in enumerate(recommended_stocks, 1):
            score = next(r['score_percentage'] for r in ranked_results if r['symbol'] == stock)
            print(f"  {i}. {stock} - {score:.1f}%")
        
        print(f"\nThese {len(threshold_analysis[60])} stocks pass enhanced growth screening")
        print("and are ready for technical analysis and strategy application!")
    else:
        print("No stocks in this demo universe meet the 60% threshold.")
        print("Consider expanding the universe or lowering the threshold.")
    
    return {
        'screening_results': ranked_results,
        'threshold_analysis': threshold_analysis,
        'demo_stocks': demo_stocks
    }

def export_demo_results(results: dict):
    """
    Export demo results to CSV for further analysis
    """
    if 'screening_results' not in results:
        return
    
    # Create summary DataFrame
    summary_data = []
    for result in results['screening_results']:
        row = {
            'Symbol': result['symbol'],
            'Score': result['score_percentage'],
            'Rating': result['rating']
        }
        
        # Add key metrics
        for criterion, data in result['criteria'].items():
            row[criterion.replace('_', ' ').title()] = data['value']
            row[f"{criterion}_pass"] = data['pass']
        
        summary_data.append(row)
    
    df = pd.DataFrame(summary_data)
    
    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enhanced_screening_demo_{timestamp}.csv"
    df.to_csv(filename, index=False)
    
    print(f"\nResults exported to: {filename}")
    print(f"Contains detailed screening data for {len(df)} stocks")

def main():
    """
    Run enhanced screening demo
    """
    print("Starting Enhanced Fundamental Growth Screening Demo...")
    print()
    
    try:
        # Run demo
        results = demo_enhanced_screening()
        
        # Export results
        export_demo_results(results)
        
        print(f"\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("The enhanced fundamental growth screener has identified")
        print("the highest quality growth stocks from the demo universe.")
        print()
        print("Next steps:")
        print("1. Apply these stocks to your trading strategies")
        print("2. Test different score thresholds")
        print("3. Expand the screening universe")
        print("4. Combine with technical analysis for optimal timing")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()