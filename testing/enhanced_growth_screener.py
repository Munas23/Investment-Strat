"""
Enhanced Fundamental Growth Screener
===================================

This screener builds on Minervini's fundamental approach but adds enhanced
growth metrics, sales growth analysis, and additional quality factors to
identify the best growth stocks for trading strategies.

KEY ENHANCEMENTS:
1. Multi-timeframe sales growth analysis (quarterly, yearly, 3-year)
2. Sales growth acceleration detection
3. Profitability quality metrics (gross margins, operating margins)
4. Balance sheet strength indicators
5. Market position metrics
6. Growth sustainability indicators

This screener can be integrated with any trading strategy to improve
stock selection and overall performance.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class EnhancedGrowthScreener:
    """
    Enhanced fundamental growth screener with comprehensive metrics
    """
    
    def __init__(self):
        # Enhanced growth criteria thresholds
        self.min_revenue_growth_1y = 15      # 15%+ annual revenue growth
        self.min_revenue_growth_3y = 12      # 12%+ 3-year average growth
        self.min_quarterly_growth = 10       # 10%+ recent quarterly growth
        self.min_earnings_growth = 15        # 15%+ earnings growth
        self.min_roe = 15                    # 15%+ ROE
        self.min_gross_margin = 40           # 40%+ gross margins
        self.min_operating_margin = 10       # 10%+ operating margins
        self.max_debt_to_equity = 0.5        # <50% debt-to-equity
        self.min_current_ratio = 1.2         # >1.2 current ratio
        self.min_market_cap = 100e6          # $100M minimum market cap
        self.max_market_cap = 500e9          # $500B maximum market cap
        self.min_price = 5                   # $5 minimum price
        self.min_volume = 100000             # 100K minimum volume
        
        print("ENHANCED FUNDAMENTAL GROWTH SCREENER")
        print("=" * 50)
        print("GROWTH CRITERIA:")
        print(f"  Revenue Growth (1Y): >{self.min_revenue_growth_1y}%")
        print(f"  Revenue Growth (3Y): >{self.min_revenue_growth_3y}%") 
        print(f"  Quarterly Growth: >{self.min_quarterly_growth}%")
        print(f"  Earnings Growth: >{self.min_earnings_growth}%")
        print("QUALITY CRITERIA:")
        print(f"  ROE: >{self.min_roe}%")
        print(f"  Gross Margin: >{self.min_gross_margin}%")
        print(f"  Operating Margin: >{self.min_operating_margin}%")
        print("FINANCIAL STRENGTH:")
        print(f"  Debt/Equity: <{self.max_debt_to_equity}")
        print(f"  Current Ratio: >{self.min_current_ratio}")
        print("=" * 50)
    
    def get_enhanced_fundamental_data(self, symbol: str) -> Dict:
        """
        Get comprehensive fundamental data with enhanced growth metrics
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get financial statements
            try:
                financials = ticker.financials
                quarterly_financials = ticker.quarterly_financials
                balance_sheet = ticker.balance_sheet
                cashflow = ticker.cashflow
            except:
                financials = pd.DataFrame()
                quarterly_financials = pd.DataFrame()
                balance_sheet = pd.DataFrame()
                cashflow = pd.DataFrame()
            
            # Extract enhanced fundamental metrics
            fundamentals = {
                'symbol': symbol,
                
                # Basic info
                'market_cap': info.get('marketCap', 0),
                'price': info.get('currentPrice', 0),
                'volume': info.get('averageVolume', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                
                # Enhanced growth metrics
                'revenue_growth_1y': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'revenue_per_share': info.get('revenuePerShare', 0),
                'book_value_per_share': info.get('bookValue', 0),
                
                # Profitability quality
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'gross_margins': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                'operating_margins': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0,
                'profit_margins': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                
                # Financial strength
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0,
                'total_cash': info.get('totalCash', 0),
                'total_debt': info.get('totalDebt', 0),
                'free_cashflow': info.get('freeCashflow', 0),
                
                # Valuation metrics
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_sales': info.get('priceToSalesTrailing12Months', 0),
                'price_to_book': info.get('priceToBook', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'ev_to_revenue': info.get('enterpriseToRevenue', 0),
                'ev_to_ebitda': info.get('enterpriseToEbitda', 0),
                
                # Market metrics
                'beta': info.get('beta', 0),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'float_shares': info.get('floatShares', 0),
                'institutional_ownership': info.get('heldByInstitutions', 0) * 100 if info.get('heldByInstitutions') else 0,
                'insider_ownership': info.get('heldByInsiders', 0) * 100 if info.get('heldByInsiders') else 0,
                
                # Additional growth indicators
                'revenue_quarterly_growth': info.get('revenueQuarterlyGrowth', 0) * 100 if info.get('revenueQuarterlyGrowth') else 0,
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0,
                'eps_forward': info.get('forwardEps', 0),
                'eps_trailing': info.get('trailingEps', 0),
            }
            
            # Calculate additional metrics from financial statements
            fundamentals.update(self._calculate_additional_metrics(
                financials, quarterly_financials, balance_sheet, cashflow, info
            ))
            
            return fundamentals
            
        except Exception as e:
            print(f"  Error getting fundamentals for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _calculate_additional_metrics(self, financials: pd.DataFrame, 
                                    quarterly_financials: pd.DataFrame,
                                    balance_sheet: pd.DataFrame,
                                    cashflow: pd.DataFrame,
                                    info: Dict) -> Dict:
        """
        Calculate additional growth and quality metrics from financial statements
        """
        additional_metrics = {
            'revenue_growth_3y_avg': 0,
            'sales_acceleration': 0,
            'margin_improvement': 0,
            'working_capital_ratio': 0,
            'asset_turnover': 0,
            'inventory_turnover': 0,
            'receivables_turnover': 0,
            'cash_conversion_cycle': 0,
            'revenue_predictability': 0
        }
        
        try:
            # Calculate 3-year average revenue growth
            if not financials.empty and 'Total Revenue' in financials.index:
                revenues = financials.loc['Total Revenue'].dropna()
                if len(revenues) >= 3:
                    revenue_growth_rates = []
                    for i in range(len(revenues) - 1):
                        if revenues.iloc[i+1] != 0:
                            growth = (revenues.iloc[i] / revenues.iloc[i+1] - 1) * 100
                            revenue_growth_rates.append(growth)
                    
                    if revenue_growth_rates:
                        additional_metrics['revenue_growth_3y_avg'] = np.mean(revenue_growth_rates)
                        
                        # Calculate sales acceleration (recent growth vs historical)
                        if len(revenue_growth_rates) >= 2:
                            recent_growth = np.mean(revenue_growth_rates[:2])  # Last 2 years
                            older_growth = np.mean(revenue_growth_rates[2:])   # Earlier years
                            additional_metrics['sales_acceleration'] = recent_growth - older_growth
            
            # Calculate margin improvement
            if not financials.empty and 'Gross Profit' in financials.index and 'Total Revenue' in financials.index:
                gross_profits = financials.loc['Gross Profit'].dropna()
                revenues = financials.loc['Total Revenue'].dropna()
                
                if len(gross_profits) >= 2 and len(revenues) >= 2:
                    current_margin = (gross_profits.iloc[0] / revenues.iloc[0]) * 100
                    prev_margin = (gross_profits.iloc[1] / revenues.iloc[1]) * 100
                    additional_metrics['margin_improvement'] = current_margin - prev_margin
            
            # Calculate working capital metrics
            if not balance_sheet.empty:
                try:
                    current_assets = balance_sheet.loc['Current Assets'].iloc[0] if 'Current Assets' in balance_sheet.index else 0
                    current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in balance_sheet.index else 0
                    total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else 0
                    
                    if total_assets > 0:
                        working_capital = current_assets - current_liabilities
                        additional_metrics['working_capital_ratio'] = (working_capital / total_assets) * 100
                except:
                    pass
            
            # Calculate revenue predictability (lower CV = more predictable)
            if not quarterly_financials.empty and 'Total Revenue' in quarterly_financials.index:
                quarterly_revenues = quarterly_financials.loc['Total Revenue'].dropna()
                if len(quarterly_revenues) >= 8:  # Need at least 2 years of quarterly data
                    revenue_growth_rates = []
                    for i in range(len(quarterly_revenues) - 4):  # YoY growth rates
                        if quarterly_revenues.iloc[i+4] != 0:
                            yoy_growth = (quarterly_revenues.iloc[i] / quarterly_revenues.iloc[i+4] - 1) * 100
                            revenue_growth_rates.append(yoy_growth)
                    
                    if revenue_growth_rates and len(revenue_growth_rates) >= 4:
                        # Lower coefficient of variation = more predictable
                        mean_growth = np.mean(revenue_growth_rates)
                        if mean_growth != 0:
                            cv = np.std(revenue_growth_rates) / abs(mean_growth)
                            additional_metrics['revenue_predictability'] = max(0, 100 - cv * 100)
                        
        except Exception as e:
            print(f"    Error calculating additional metrics: {e}")
        
        return additional_metrics
    
    def screen_enhanced_fundamentals(self, fundamentals: Dict) -> Dict:
        """
        Screen stock based on enhanced growth and quality criteria
        """
        if 'error' in fundamentals:
            return {'symbol': fundamentals['symbol'], 'error': fundamentals['error']}
        
        symbol = fundamentals['symbol']
        screening = {'symbol': symbol, 'criteria': {}, 'total_score': 0, 'max_score': 0}
        
        # GROWTH CRITERIA (40% of total weight)
        
        # Criterion 1: Revenue Growth (1 Year) - Weight 15
        revenue_growth_1y = fundamentals.get('revenue_growth_1y', 0)
        pass_1 = revenue_growth_1y >= self.min_revenue_growth_1y
        screening['criteria']['revenue_growth_1y'] = {
            'value': revenue_growth_1y,
            'pass': pass_1,
            'weight': 15
        }
        
        # Criterion 2: Revenue Growth (3 Year Average) - Weight 15  
        revenue_growth_3y = fundamentals.get('revenue_growth_3y_avg', 0)
        pass_2 = revenue_growth_3y >= self.min_revenue_growth_3y
        screening['criteria']['revenue_growth_3y_avg'] = {
            'value': revenue_growth_3y,
            'pass': pass_2,
            'weight': 15
        }
        
        # Criterion 3: Quarterly Revenue Growth - Weight 10
        quarterly_growth = fundamentals.get('revenue_quarterly_growth', 0)
        pass_3 = quarterly_growth >= self.min_quarterly_growth
        screening['criteria']['quarterly_growth'] = {
            'value': quarterly_growth,
            'pass': pass_3,
            'weight': 10
        }
        
        # Criterion 4: Earnings Growth - Weight 15
        earnings_growth = fundamentals.get('earnings_growth', 0)
        pass_4 = earnings_growth >= self.min_earnings_growth
        screening['criteria']['earnings_growth'] = {
            'value': earnings_growth,
            'pass': pass_4,
            'weight': 15
        }
        
        # Criterion 5: Sales Acceleration - Weight 10
        sales_acceleration = fundamentals.get('sales_acceleration', 0)
        pass_5 = sales_acceleration > 0  # Growth is accelerating
        screening['criteria']['sales_acceleration'] = {
            'value': sales_acceleration,
            'pass': pass_5,
            'weight': 10
        }
        
        # PROFITABILITY QUALITY CRITERIA (30% of total weight)
        
        # Criterion 6: ROE - Weight 15
        roe = fundamentals.get('roe', 0)
        pass_6 = roe >= self.min_roe
        screening['criteria']['roe'] = {
            'value': roe,
            'pass': pass_6,
            'weight': 15
        }
        
        # Criterion 7: Gross Margins - Weight 10
        gross_margins = fundamentals.get('gross_margins', 0)
        pass_7 = gross_margins >= self.min_gross_margin
        screening['criteria']['gross_margins'] = {
            'value': gross_margins,
            'pass': pass_7,
            'weight': 10
        }
        
        # Criterion 8: Operating Margins - Weight 10
        operating_margins = fundamentals.get('operating_margins', 0)
        pass_8 = operating_margins >= self.min_operating_margin
        screening['criteria']['operating_margins'] = {
            'value': operating_margins,
            'pass': pass_8,
            'weight': 10
        }
        
        # Criterion 9: Margin Improvement - Weight 5
        margin_improvement = fundamentals.get('margin_improvement', 0)
        pass_9 = margin_improvement >= 0  # Margins improving or stable
        screening['criteria']['margin_improvement'] = {
            'value': margin_improvement,
            'pass': pass_9,
            'weight': 5
        }
        
        # FINANCIAL STRENGTH CRITERIA (20% of total weight)
        
        # Criterion 10: Debt-to-Equity - Weight 10
        debt_to_equity = fundamentals.get('debt_to_equity', 0)
        pass_10 = debt_to_equity <= self.max_debt_to_equity
        screening['criteria']['debt_to_equity'] = {
            'value': debt_to_equity,
            'pass': pass_10,
            'weight': 10
        }
        
        # Criterion 11: Current Ratio - Weight 5
        current_ratio = fundamentals.get('current_ratio', 0)
        pass_11 = current_ratio >= self.min_current_ratio
        screening['criteria']['current_ratio'] = {
            'value': current_ratio,
            'pass': pass_11,
            'weight': 5
        }
        
        # Criterion 12: Free Cash Flow Positive - Weight 5
        free_cashflow = fundamentals.get('free_cashflow', 0)
        pass_12 = free_cashflow > 0
        screening['criteria']['free_cashflow_positive'] = {
            'value': free_cashflow,
            'pass': pass_12,
            'weight': 5
        }
        
        # MARKET CRITERIA (10% of total weight)
        
        # Criterion 13: Market Cap Range - Weight 5
        market_cap = fundamentals.get('market_cap', 0)
        pass_13 = self.min_market_cap <= market_cap <= self.max_market_cap
        screening['criteria']['market_cap'] = {
            'value': market_cap,
            'pass': pass_13,
            'weight': 5
        }
        
        # Criterion 14: Price and Volume - Weight 5
        price = fundamentals.get('price', 0)
        volume = fundamentals.get('volume', 0)
        pass_14 = price >= self.min_price and volume >= self.min_volume
        screening['criteria']['price_volume'] = {
            'value': f"${price:.2f}, {volume:,}",
            'pass': pass_14,
            'weight': 5
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
        
        # Enhanced quality rating
        score_pct = screening['score_percentage']
        if score_pct >= 85:
            screening['rating'] = 'EXCEPTIONAL'
        elif score_pct >= 70:
            screening['rating'] = 'EXCELLENT'
        elif score_pct >= 55:
            screening['rating'] = 'GOOD'
        elif score_pct >= 40:
            screening['rating'] = 'FAIR'
        else:
            screening['rating'] = 'POOR'
        
        return screening
    
    def screen_stock_universe(self, symbols: List[str]) -> List[Dict]:
        """
        Screen a universe of stocks with enhanced fundamental criteria
        """
        print(f"\nSCREENING {len(symbols)} STOCKS WITH ENHANCED GROWTH CRITERIA")
        print("=" * 70)
        
        screening_results = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] Screening {symbol}...")
            
            # Get enhanced fundamental data
            fundamentals = self.get_enhanced_fundamental_data(symbol)
            
            if 'error' not in fundamentals:
                # Screen fundamentals
                screening = self.screen_enhanced_fundamentals(fundamentals)
                screening_results.append(screening)
                
                # Print key metrics
                print(f"  Market Cap: ${fundamentals.get('market_cap', 0)/1e9:.1f}B")
                print(f"  Revenue Growth (1Y): {fundamentals.get('revenue_growth_1y', 0):.1f}%")
                print(f"  Revenue Growth (3Y): {fundamentals.get('revenue_growth_3y_avg', 0):.1f}%")
                print(f"  ROE: {fundamentals.get('roe', 0):.1f}%")
                print(f"  Gross Margin: {fundamentals.get('gross_margins', 0):.1f}%")
                print(f"  Score: {screening['score_percentage']:.1f}% ({screening['rating']})")
            else:
                print(f"  Error: {fundamentals['error']}")
        
        return screening_results
    
    def rank_growth_stocks(self, screening_results: List[Dict]) -> List[Dict]:
        """
        Rank stocks by enhanced growth screening scores
        """
        valid_results = [r for r in screening_results if 'error' not in r]
        ranked_results = sorted(valid_results, key=lambda x: x['score_percentage'], reverse=True)
        
        print(f"\n" + "=" * 90)
        print("ENHANCED GROWTH SCREENING RESULTS - RANKED")
        print("=" * 90)
        
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<8} {'Rating':<12} {'Rev1Y':<8} {'Rev3Y':<8} {'ROE':<6} {'Gross':<6}")
        print("-" * 90)
        
        for i, result in enumerate(ranked_results[:25]):  # Top 25
            symbol = result['symbol']
            score = result['score_percentage']
            rating = result['rating']
            
            # Extract key metrics
            rev_1y = result['criteria'].get('revenue_growth_1y', {}).get('value', 0)
            rev_3y = result['criteria'].get('revenue_growth_3y_avg', {}).get('value', 0)
            roe = result['criteria'].get('roe', {}).get('value', 0)
            gross = result['criteria'].get('gross_margins', {}).get('value', 0)
            
            print(f"{i+1:<4} {symbol:<8} {score:>6.1f}% {rating:<12} {rev_1y:>6.1f}% {rev_3y:>6.1f}% {roe:>4.1f}% {gross:>4.1f}%")
        
        return ranked_results
    
    def get_growth_leaders(self, ranked_results: List[Dict], 
                          min_score: float = 60.0) -> List[str]:
        """
        Get list of stocks that pass enhanced growth screening
        """
        leaders = []
        
        print(f"\n" + "=" * 70)
        print("ENHANCED GROWTH LEADERS")
        print("=" * 70)
        print(f"Stocks scoring >{min_score}% on enhanced growth criteria")
        print("-" * 70)
        
        for result in ranked_results:
            if result['score_percentage'] >= min_score:
                leaders.append(result['symbol'])
                
                print(f"{result['symbol']:<8} Score: {result['score_percentage']:>5.1f}% ({result['rating']})")
                
                # Show growth metrics
                rev_1y = result['criteria'].get('revenue_growth_1y', {}).get('value', 0)
                rev_3y = result['criteria'].get('revenue_growth_3y_avg', {}).get('value', 0)
                earnings = result['criteria'].get('earnings_growth', {}).get('value', 0)
                
                print(f"         Growth: Rev1Y={rev_1y:.1f}%, Rev3Y={rev_3y:.1f}%, EPS={earnings:.1f}%")
        
        print(f"\nTotal Growth Leaders: {len(leaders)}")
        return leaders
    
    def demo_enhanced_screening(self):
        """
        Demonstrate enhanced growth screening on a diverse stock universe
        """
        # Comprehensive test universe
        test_symbols = [
            # Large cap tech growth
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'ADBE',
            
            # High growth SaaS
            'CRM', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'NET', 'DDOG', 'ZS',
            
            # Emerging growth
            'SHOP', 'SQ', 'ROKU', 'ZM', 'DOCU', 'TWLO', 'OKTA', 'MDB',
            
            # Biotech growth
            'MRNA', 'BNTX', 'REGN', 'VRTX', 'GILD', 'BIIB',
            
            # Consumer growth
            'NFLX', 'DIS', 'NKE', 'SBUX', 'HD', 'LOW',
            
            # Fintech
            'V', 'MA', 'PYPL', 'ADYB', 'COIN',
            
            # Traditional value (for comparison)
            'JPM', 'JNJ', 'PG', 'KO', 'WMT', 'UNH'
        ]
        
        # Perform enhanced screening
        screening_results = self.screen_stock_universe(test_symbols)
        
        # Rank by scores
        ranked_results = self.rank_growth_stocks(screening_results)
        
        # Get growth leaders
        growth_leaders = self.get_growth_leaders(ranked_results, min_score=60.0)
        
        print(f"\n" + "=" * 70)
        print("ENHANCED SCREENING SUMMARY")
        print("=" * 70)
        print(f"Total Stocks Screened: {len(test_symbols)}")
        print(f"Valid Results: {len(ranked_results)}")
        print(f"Growth Leaders (>60% score): {len(growth_leaders)}")
        
        if growth_leaders:
            print(f"\nTOP ENHANCED GROWTH PICKS:")
            for i, symbol in enumerate(growth_leaders[:10]):
                result = next(r for r in ranked_results if r['symbol'] == symbol)
                print(f"  {i+1:2d}. {symbol} - {result['score_percentage']:.1f}% ({result['rating']})")
        
        print(f"\nThese {len(growth_leaders)} stocks pass enhanced growth screening")
        print("Ready for integration with any trading strategy!")
        
        return growth_leaders, ranked_results

def main():
    """
    Demonstrate enhanced fundamental growth screening
    """
    print("ENHANCED FUNDAMENTAL GROWTH SCREENER")
    print("=" * 50)
    print("This screener identifies the highest quality growth stocks")
    print("for integration with any trading strategy.")
    print()
    
    screener = EnhancedGrowthScreener()
    
    try:
        growth_leaders, results = screener.demo_enhanced_screening()
        
        print(f"\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("1. Integrate these growth leaders with trading strategies")
        print("2. Compare performance vs random stock selection")
        print("3. Test different score thresholds (50%, 60%, 70%)")
        print("4. Combine with technical analysis for optimal timing")
        print()
        print("The enhanced screener provides a solid foundation")
        print("for improving any trading strategy's performance!")
        
    except Exception as e:
        print(f"Error in screening: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()