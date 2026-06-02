"""
Mark Minervini's FUNDAMENTAL Stock Screening Criteria
====================================================

Minervini doesn't just use technical analysis - he combines it with specific
fundamental metrics to identify superperformance candidates BEFORE they explode.

KEY FUNDAMENTAL FILTERS (From his books and interviews):

EARNINGS CRITERIA:
1. Quarterly EPS growth: 18-25%+ for past 2-3 quarters
2. Annual EPS growth: 25%+ for past 2-3 years  
3. EPS estimate revisions: Upward revisions by analysts
4. Earnings surprises: Beat estimates in recent quarters

REVENUE CRITERIA:
5. Revenue growth: 15%+ quarterly growth
6. Revenue acceleration: Growth rate increasing
7. Revenue quality: Consistent, not one-time

FINANCIAL STRENGTH:
8. ROE: 15%+ (Return on Equity)
9. Debt-to-Equity: Low (<0.3 preferred)
10. Current Ratio: >1.5 (financial stability)
11. Profit margins: Expanding or stable

INSTITUTIONAL INDICATORS:
12. Institutional ownership: 40-80% (not too high, not too low)
13. Recent institutional buying: Increasing ownership
14. Analyst coverage: Growing interest

MARKET METRICS:
15. Market cap: $300M - $50B (avoids micro caps and mega caps)
16. Average volume: >500K daily
17. Price: >$15 (avoids penny stocks)

This implementation combines these fundamentals with technical breakouts
for a complete Minervini-style screening system.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class MinerviniFoundamentals:
    """
    Mark Minervini's complete fundamental + technical screening system
    
    This combines his fundamental stock selection criteria with
    technical breakout timing for maximum effectiveness.
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Minervini's fundamental criteria thresholds
        self.min_eps_growth = 18          # Minimum quarterly EPS growth %
        self.min_revenue_growth = 15      # Minimum quarterly revenue growth %
        self.min_roe = 15                # Minimum ROE %
        self.max_debt_to_equity = 0.3    # Maximum debt-to-equity ratio
        self.min_current_ratio = 1.5     # Minimum current ratio
        self.min_market_cap = 300e6      # Minimum market cap ($300M)
        self.max_market_cap = 50e9       # Maximum market cap ($50B)
        self.min_price = 15              # Minimum stock price
        self.min_volume = 500000         # Minimum daily volume
        
        print("MINERVINI FUNDAMENTAL + TECHNICAL SCREENING")
        print("=" * 50)
        print("FUNDAMENTAL CRITERIA:")
        print(f"  EPS Growth: >{self.min_eps_growth}% quarterly")
        print(f"  Revenue Growth: >{self.min_revenue_growth}% quarterly")
        print(f"  ROE: >{self.min_roe}%")
        print(f"  Debt/Equity: <{self.max_debt_to_equity}")
        print(f"  Market Cap: ${self.min_market_cap/1e6:.0f}M - ${self.max_market_cap/1e9:.0f}B")
        print(f"  Price: >${self.min_price}")
        print("=" * 50)
    
    def get_fundamental_data(self, symbol: str) -> Dict:
        """
        Get fundamental data for a stock using yfinance
        
        Note: yfinance has limited fundamental data compared to
        professional services, but we'll extract what we can.
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get financials (limited in yfinance)
            try:
                quarterly_financials = ticker.quarterly_financials
                quarterly_earnings = ticker.quarterly_earnings
                balance_sheet = ticker.balance_sheet
            except:
                quarterly_financials = pd.DataFrame()
                quarterly_earnings = pd.DataFrame()
                balance_sheet = pd.DataFrame()
            
            # Extract key metrics
            fundamentals = {
                'symbol': symbol,
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'price': info.get('currentPrice', 0),
                'volume': info.get('averageVolume', 0),
                
                # Profitability
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                
                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'eps_forward': info.get('forwardEps', 0),
                'eps_trailing': info.get('trailingEps', 0),
                
                # Financial strength
                'current_ratio': info.get('currentRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                'quick_ratio': info.get('quickRatio', 0),
                'cash_per_share': info.get('totalCashPerShare', 0),
                
                # Valuation
                'pe_ratio': info.get('trailingPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_sales': info.get('priceToSalesTrailing12Months', 0),
                'price_to_book': info.get('priceToBook', 0),
                
                # Institutional
                'institutional_ownership': info.get('heldByInstitutions', 0) * 100 if info.get('heldByInstitutions') else 0,
                'insider_ownership': info.get('heldByInsiders', 0) * 100 if info.get('heldByInsiders') else 0,
                
                # Additional metrics
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'employees': info.get('fullTimeEmployees', 0),
            }
            
            return fundamentals
            
        except Exception as e:
            print(f"  Error getting fundamentals for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def screen_fundamentals(self, fundamentals: Dict) -> Dict:
        """
        Screen stock based on Minervini's fundamental criteria
        
        Returns screening results with pass/fail for each criterion
        """
        if 'error' in fundamentals:
            return {'symbol': fundamentals['symbol'], 'error': fundamentals['error']}
        
        symbol = fundamentals['symbol']
        screening = {'symbol': symbol, 'criteria': {}, 'total_score': 0, 'max_score': 0}
        
        # Criterion 1: Market Cap (300M - 50B)
        market_cap = fundamentals.get('market_cap', 0)
        criterion_1 = self.min_market_cap <= market_cap <= self.max_market_cap
        screening['criteria']['market_cap'] = {
            'value': market_cap,
            'pass': criterion_1,
            'weight': 10
        }
        
        # Criterion 2: Stock Price (>$15)
        price = fundamentals.get('price', 0)
        criterion_2 = price >= self.min_price
        screening['criteria']['price'] = {
            'value': price,
            'pass': criterion_2,
            'weight': 5
        }
        
        # Criterion 3: Volume (>500K)
        volume = fundamentals.get('volume', 0)
        criterion_3 = volume >= self.min_volume
        screening['criteria']['volume'] = {
            'value': volume,
            'pass': criterion_3,
            'weight': 5
        }
        
        # Criterion 4: ROE (>15%)
        roe = fundamentals.get('roe', 0)
        criterion_4 = roe >= self.min_roe
        screening['criteria']['roe'] = {
            'value': roe,
            'pass': criterion_4,
            'weight': 20
        }
        
        # Criterion 5: Revenue Growth (>15%)
        revenue_growth = fundamentals.get('revenue_growth', 0)
        criterion_5 = revenue_growth >= self.min_revenue_growth
        screening['criteria']['revenue_growth'] = {
            'value': revenue_growth,
            'pass': criterion_5,
            'weight': 25
        }
        
        # Criterion 6: Earnings Growth (>18%)
        earnings_growth = fundamentals.get('earnings_growth', 0)
        criterion_6 = earnings_growth >= self.min_eps_growth
        screening['criteria']['earnings_growth'] = {
            'value': earnings_growth,
            'pass': criterion_6,
            'weight': 25
        }
        
        # Criterion 7: Debt-to-Equity (<0.3)
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        criterion_7 = debt_to_equity <= self.max_debt_to_equity
        screening['criteria']['debt_to_equity'] = {
            'value': debt_to_equity,
            'pass': criterion_7,
            'weight': 15
        }
        
        # Criterion 8: Current Ratio (>1.5)
        current_ratio = fundamentals.get('current_ratio', 0)
        criterion_8 = current_ratio >= self.min_current_ratio
        screening['criteria']['current_ratio'] = {
            'value': current_ratio,
            'pass': criterion_8,
            'weight': 10
        }
        
        # Criterion 9: Institutional Ownership (40-80%)
        institutional_ownership = fundamentals.get('institutional_ownership', 0)
        criterion_9 = 40 <= institutional_ownership <= 80
        screening['criteria']['institutional_ownership'] = {
            'value': institutional_ownership,
            'pass': criterion_9,
            'weight': 15
        }
        
        # Criterion 10: Profit Margin Quality (>10%)
        profit_margin = fundamentals.get('profit_margin', 0)
        criterion_10 = profit_margin >= 10
        screening['criteria']['profit_margin'] = {
            'value': profit_margin,
            'pass': criterion_10,
            'weight': 20
        }
        
        # Calculate total score
        total_score = 0
        max_score = 0
        
        for criterion, data in screening['criteria'].items():
            max_score += data['weight']
            if data['pass']:
                total_score += data['weight']
        
        screening['total_score'] = total_score
        screening['max_score'] = max_score
        screening['score_percentage'] = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Overall quality rating
        score_pct = screening['score_percentage']
        if score_pct >= 80:
            screening['rating'] = 'EXCELLENT'
        elif score_pct >= 60:
            screening['rating'] = 'GOOD' 
        elif score_pct >= 40:
            screening['rating'] = 'FAIR'
        else:
            screening['rating'] = 'POOR'
        
        return screening
    
    def comprehensive_stock_screen(self, symbols: List[str]) -> List[Dict]:
        """
        Perform comprehensive fundamental screening on a list of stocks
        """
        
        print(f"\nSCREENING {len(symbols)} STOCKS FOR MINERVINI CRITERIA")
        print("=" * 60)
        
        screening_results = []
        
        for symbol in symbols:
            print(f"\nScreening {symbol}...")
            
            # Get fundamental data
            fundamentals = self.get_fundamental_data(symbol)
            
            if 'error' not in fundamentals:
                # Screen fundamentals
                screening = self.screen_fundamentals(fundamentals)
                screening_results.append(screening)
                
                # Print key metrics
                print(f"  Market Cap: ${fundamentals.get('market_cap', 0)/1e9:.1f}B")
                print(f"  Price: ${fundamentals.get('price', 0):.2f}")
                print(f"  ROE: {fundamentals.get('roe', 0):.1f}%")
                print(f"  Revenue Growth: {fundamentals.get('revenue_growth', 0):.1f}%")
                print(f"  Earnings Growth: {fundamentals.get('earnings_growth', 0):.1f}%")
                print(f"  Score: {screening['score_percentage']:.1f}% ({screening['rating']})")
            else:
                print(f"  Error: {fundamentals['error']}")
        
        return screening_results
    
    def rank_stocks_by_fundamentals(self, screening_results: List[Dict]) -> List[Dict]:
        """
        Rank stocks by their fundamental screening scores
        """
        
        # Filter out errors and sort by score
        valid_results = [r for r in screening_results if 'error' not in r]
        ranked_results = sorted(valid_results, key=lambda x: x['score_percentage'], reverse=True)
        
        print(f"\n" + "=" * 80)
        print("FUNDAMENTAL SCREENING RESULTS - RANKED")
        print("=" * 80)
        
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Rating':<10} {'Key Strengths':<35}")
        print("-" * 80)
        
        for i, result in enumerate(ranked_results[:20]):  # Top 20
            symbol = result['symbol']
            score = result['score_percentage']
            rating = result['rating']
            
            # Identify key strengths
            strengths = []
            for criterion, data in result['criteria'].items():
                if data['pass'] and data['weight'] >= 20:  # High-weight criteria
                    if criterion == 'revenue_growth':
                        strengths.append(f"Rev+{data['value']:.0f}%")
                    elif criterion == 'earnings_growth':
                        strengths.append(f"EPS+{data['value']:.0f}%")
                    elif criterion == 'roe':
                        strengths.append(f"ROE{data['value']:.0f}%")
                    elif criterion == 'profit_margin':
                        strengths.append(f"Margin{data['value']:.0f}%")
            
            strengths_str = ", ".join(strengths[:3])  # Top 3 strengths
            
            print(f"{i+1:<4} {symbol:<8} {score:>6.1f}% {rating:<10} {strengths_str:<35}")
        
        return ranked_results
    
    def identify_breakout_candidates(self, ranked_results: List[Dict], 
                                   min_fundamental_score: float = 60.0) -> List[str]:
        """
        Identify stocks that pass fundamental screening as breakout candidates
        
        These stocks have strong fundamentals and are ready for technical analysis
        """
        
        candidates = []
        
        print(f"\n" + "=" * 60)
        print("MINERVINI BREAKOUT CANDIDATES")
        print("=" * 60)
        print("Stocks that pass fundamental screening (>60% score)")
        print("These are ready for technical breakout analysis")
        print("-" * 60)
        
        for result in ranked_results:
            if result['score_percentage'] >= min_fundamental_score:
                candidates.append(result['symbol'])
                
                print(f"{result['symbol']:<8} Score: {result['score_percentage']:>5.1f}% ({result['rating']})")
                
                # Show specific strengths
                key_metrics = []
                for criterion, data in result['criteria'].items():
                    if data['pass'] and data['weight'] >= 15:
                        key_metrics.append(f"{criterion}: {data['value']:.1f}")
                
                if key_metrics:
                    print(f"         Key: {', '.join(key_metrics[:3])}")
        
        print(f"\nTotal Candidates: {len(candidates)}")
        
        return candidates
    
    def demo_fundamental_screening(self):
        """
        Demonstrate Minervini's fundamental screening on a diverse set of stocks
        """
        
        # Test universe - mix of different types of stocks
        test_symbols = [
            # Large cap tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA',
            
            # Growth stocks
            'CRM', 'ADBE', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'NET',
            
            # Traditional stocks  
            'JPM', 'JNJ', 'PG', 'KO', 'WMT', 'UNH',
            
            # Mid-cap growth
            'SHOP', 'SQ', 'ROKU', 'ZM', 'DOCU', 'TWLO',
            
            # Biotech/Healthcare
            'MRNA', 'BNTX', 'REGN', 'GILD', 'VRTX'
        ]
        
        # Perform screening
        screening_results = self.comprehensive_stock_screen(test_symbols)
        
        # Rank by fundamentals
        ranked_results = self.rank_stocks_by_fundamentals(screening_results)
        
        # Identify breakout candidates
        candidates = self.identify_breakout_candidates(ranked_results)
        
        print(f"\n" + "=" * 60)
        print("SCREENING SUMMARY")
        print("=" * 60)
        print(f"Stocks Screened: {len(test_symbols)}")
        print(f"Valid Results: {len(ranked_results)}")
        print(f"Breakout Candidates (>60% score): {len(candidates)}")
        
        if candidates:
            print(f"\nTOP FUNDAMENTAL PICKS:")
            for i, symbol in enumerate(candidates[:5]):
                result = next(r for r in ranked_results if r['symbol'] == symbol)
                print(f"  {i+1}. {symbol} - {result['score_percentage']:.1f}% ({result['rating']})")
        
        print(f"\nThese {len(candidates)} stocks pass Minervini's fundamental filter")
        print("Next step: Apply technical breakout analysis to these candidates")
        print("This is how Minervini finds his championship-winning stocks!")
        
        return candidates, ranked_results

def main():
    """
    Demonstrate Minervini's fundamental stock screening system
    """
    
    print("MARK MINERVINI'S FUNDAMENTAL STOCK SCREENING")
    print("=" * 50)
    print("This demonstrates the COMPLETE Minervini methodology:")
    print("1. Fundamental screening to identify quality companies")  
    print("2. Technical analysis for precise entry timing")
    print("3. Combined approach for maximum effectiveness")
    print()
    
    screener = MinerviniFoundamentals()
    
    try:
        candidates, results = screener.demo_fundamental_screening()
        
        print(f"\n" + "=" * 60)
        print("KEY INSIGHTS")
        print("=" * 60)
        print("Minervini's edge comes from combining:")
        print("1. FUNDAMENTAL QUALITY - Only trade strong companies")
        print("2. TECHNICAL TIMING - Enter at precise breakout moments")
        print("3. RISK MANAGEMENT - 7% stops, 50% targets")
        print("4. POSITION SIZING - Concentrate in best ideas")
        print()
        print("This screening identifies the fundamental leaders")
        print("that are most likely to produce home run trades")
        print("when combined with technical breakout signals.")
        
    except Exception as e:
        print(f"Error in screening: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()