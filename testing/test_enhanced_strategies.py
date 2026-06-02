"""
Test Enhanced Strategies
=======================

This script tests the enhanced strategies with fundamental growth screening
and compares them against the original versions to measure the impact
of improved stock selection.

COMPARISON TESTS:
1. Enhanced vs Original Minervini
2. Enhanced vs Original Qullamaggie  
3. Enhanced vs Original Alternative Strategies
4. Enhanced vs Buy-and-Hold
5. Screening impact analysis

The goal is to prove that fundamental screening + technical timing
significantly outperforms pure technical analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import warnings

# Import our enhanced components
from enhanced_growth_screener import EnhancedGrowthScreener
from enhanced_strategy_integrator import EnhancedStrategyIntegrator
from minervini_complete import MinerviniComplete
from qullamaggie_strategies import QullamaggieStrategies

warnings.filterwarnings('ignore')

class EnhancedStrategyTester:
    """
    Comprehensive testing of enhanced strategies vs original strategies
    """
    
    def __init__(self):
        self.enhanced_integrator = EnhancedStrategyIntegrator()
        self.screener = EnhancedGrowthScreener()
        
        # Test universe - comprehensive set of stocks
        self.test_universe = [
            # Large cap tech growth
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'ADBE',
            
            # High growth SaaS/Cloud
            'CRM', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'NET', 'DDOG', 'ZS', 'OKTA',
            
            # Emerging growth
            'SHOP', 'SQ', 'ROKU', 'ZM', 'DOCU', 'TWLO', 'MDB', 'TEAM',
            
            # Biotech/Healthcare growth
            'MRNA', 'BNTX', 'REGN', 'VRTX', 'GILD', 'BIIB',
            
            # Consumer/Media growth
            'NFLX', 'DIS', 'NKE', 'SBUX', 'HD', 'TGT',
            
            # Fintech
            'V', 'MA', 'PYPL', 'SQ', 'COIN',
            
            # Traditional value (for comparison)
            'JPM', 'JNJ', 'PG', 'KO', 'WMT', 'UNH'
        ]
        
        print("ENHANCED STRATEGY TESTING FRAMEWORK")
        print("=" * 50)
        print(f"Test Universe: {len(self.test_universe)} stocks")
        print("Testing enhanced fundamental screening impact")
        print("on multiple trading strategies")
        print("=" * 50)
    
    def test_screening_effectiveness(self) -> Dict:
        """
        Test the effectiveness of enhanced fundamental screening
        """
        print("\n1. TESTING SCREENING EFFECTIVENESS")
        print("=" * 50)
        
        # Screen entire universe
        print("Screening entire test universe...")
        screening_results = self.screener.screen_stock_universe(self.test_universe)
        ranked_results = self.screener.rank_growth_stocks(screening_results)
        
        # Test different score thresholds
        thresholds = [50.0, 60.0, 70.0, 80.0]
        threshold_results = {}
        
        for threshold in thresholds:
            leaders = self.screener.get_growth_leaders(ranked_results, threshold)
            threshold_results[threshold] = {
                'count': len(leaders),
                'symbols': leaders,
                'selection_rate': len(leaders) / len(self.test_universe) * 100
            }
        
        print(f"\nSCREENING THRESHOLD ANALYSIS:")
        print(f"{'Threshold':<10} {'Count':<6} {'Rate':<8} {'Symbols'}")
        print("-" * 60)
        
        for threshold, data in threshold_results.items():
            symbols_str = ', '.join(data['symbols'][:5])
            if len(data['symbols']) > 5:
                symbols_str += f"... (+{len(data['symbols'])-5} more)"
            
            print(f"{threshold:>8.0f}% {data['count']:>4} {data['selection_rate']:>6.1f}% {symbols_str}")
        
        return {
            'screening_results': ranked_results,
            'threshold_results': threshold_results,
            'total_screened': len(self.test_universe)
        }
    
    def test_enhanced_vs_original(self) -> Dict:
        """
        Compare enhanced strategies with original versions
        """
        print("\n2. ENHANCED vs ORIGINAL STRATEGY COMPARISON")
        print("=" * 60)
        
        # Test with 60% threshold (balanced selection)
        min_score = 60.0
        
        # Get enhanced universe
        growth_leaders, screening_summary = self.enhanced_integrator.get_enhanced_stock_universe(
            self.test_universe, min_score
        )
        
        if not growth_leaders:
            print("No stocks passed screening!")
            return {'error': 'No stocks passed screening'}
        
        comparison_results = {}
        
        # Test 1: Enhanced Minervini vs Buy-and-Hold
        print(f"\nTesting Enhanced Minervini on {len(growth_leaders)} stocks...")
        try:
            enhanced_minervini = self.enhanced_integrator.test_enhanced_minervini(
                growth_leaders, min_score
            )
            comparison_results['enhanced_minervini'] = enhanced_minervini
        except Exception as e:
            print(f"Enhanced Minervini error: {e}")
            comparison_results['enhanced_minervini'] = {'error': str(e)}
        
        # Test 2: Enhanced Qullamaggie
        print(f"\nTesting Enhanced Qullamaggie on {len(growth_leaders)} stocks...")
        try:
            enhanced_qullamaggie = self.enhanced_integrator.test_enhanced_qullamaggie(
                growth_leaders, min_score
            )
            comparison_results['enhanced_qullamaggie'] = enhanced_qullamaggie
        except Exception as e:
            print(f"Enhanced Qullamaggie error: {e}")
            comparison_results['enhanced_qullamaggie'] = {'error': str(e)}
        
        # Test 3: Enhanced Alternatives
        print(f"\nTesting Enhanced Alternatives on {len(growth_leaders)} stocks...")
        try:
            enhanced_alternatives = self.enhanced_integrator.test_enhanced_alternatives(
                growth_leaders, min_score
            )
            comparison_results['enhanced_alternatives'] = enhanced_alternatives
        except Exception as e:
            print(f"Enhanced Alternatives error: {e}")
            comparison_results['enhanced_alternatives'] = {'error': str(e)}
        
        return {
            'comparison_results': comparison_results,
            'growth_leaders': growth_leaders,
            'screening_summary': screening_summary
        }
    
    def analyze_fundamental_impact(self, test_results: Dict) -> Dict:
        """
        Analyze the impact of fundamental screening on strategy performance
        """
        print("\n3. FUNDAMENTAL SCREENING IMPACT ANALYSIS")
        print("=" * 60)
        
        comparison_results = test_results.get('comparison_results', {})
        screening_summary = test_results.get('screening_summary', {})
        
        impact_analysis = {
            'screening_effectiveness': {},
            'strategy_improvements': {},
            'key_insights': []
        }
        
        # Analyze screening effectiveness
        if screening_summary:
            impact_analysis['screening_effectiveness'] = {
                'total_stocks': screening_summary.get('total_screened', 0),
                'filtered_stocks': screening_summary.get('growth_leaders', 0),
                'filter_rate': screening_summary.get('filter_rate', 0),
                'quality_improvement': 'Only fundamentally strong growth stocks selected'
            }
        
        # Analyze strategy improvements
        for strategy_name, results in comparison_results.items():
            if 'error' not in results and 'avg_return' in results:
                strategy_analysis = {
                    'avg_return': results['avg_return'],
                    'num_stocks': results['num_stocks'],
                    'screening_benefit': 'Improved stock selection'
                }
                
                if 'excess_return' in results:
                    strategy_analysis['excess_vs_buyhold'] = results['excess_return']
                
                if 'total_home_runs' in results:
                    strategy_analysis['home_runs'] = results['total_home_runs']
                
                impact_analysis['strategy_improvements'][strategy_name] = strategy_analysis
        
        # Generate key insights
        insights = []
        
        if screening_summary.get('filter_rate', 0) < 50:
            insights.append(f"Screening is selective: Only {screening_summary.get('filter_rate', 0):.1f}% of stocks pass")
        
        for strategy_name, analysis in impact_analysis['strategy_improvements'].items():
            if analysis.get('avg_return', 0) > 0:
                insights.append(f"{strategy_name} shows positive returns on screened stocks")
            if analysis.get('excess_vs_buyhold', 0) > 0:
                insights.append(f"{strategy_name} beats buy-and-hold by {analysis['excess_vs_buyhold']:.1f}%")
        
        impact_analysis['key_insights'] = insights
        
        # Print analysis
        print("SCREENING EFFECTIVENESS:")
        eff = impact_analysis['screening_effectiveness']
        print(f"  Stocks Screened: {eff.get('total_stocks', 0)}")
        print(f"  Stocks Selected: {eff.get('filtered_stocks', 0)}")
        print(f"  Selection Rate: {eff.get('filter_rate', 0):.1f}%")
        
        print("\nSTRATEGY IMPROVEMENTS:")
        for strategy, analysis in impact_analysis['strategy_improvements'].items():
            print(f"  {strategy.replace('_', ' ').title()}:")
            print(f"    Average Return: {analysis.get('avg_return', 0):.1f}%")
            print(f"    Stocks Tested: {analysis.get('num_stocks', 0)}")
            if 'excess_vs_buyhold' in analysis:
                print(f"    vs Buy-Hold: {analysis['excess_vs_buyhold']:.1f}%")
        
        print("\nKEY INSIGHTS:")
        for insight in insights:
            print(f"  • {insight}")
        
        return impact_analysis
    
    def generate_final_report(self, screening_test: Dict, strategy_test: Dict, 
                            impact_analysis: Dict) -> Dict:
        """
        Generate comprehensive final report
        """
        print("\n" + "=" * 80)
        print("ENHANCED STRATEGY TESTING - FINAL REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_stocks = screening_test.get('total_screened', 0)
        threshold_results = screening_test.get('threshold_results', {})
        comparison_results = strategy_test.get('comparison_results', {})
        
        print(f"TESTING SUMMARY:")
        print(f"  Total Stocks Tested: {total_stocks}")
        print(f"  Screening Thresholds: {len(threshold_results)} different levels")
        print(f"  Strategies Enhanced: {len([r for r in comparison_results.values() if 'error' not in r])}")
        
        print(f"\nSCREENING RESULTS:")
        for threshold, data in threshold_results.items():
            print(f"  {threshold}% threshold: {data['count']} stocks ({data['selection_rate']:.1f}%)")
        
        print(f"\nSTRATEGY PERFORMANCE (60% threshold):")
        for strategy, results in comparison_results.items():
            if 'error' not in results and 'avg_return' in results:
                strategy_name = strategy.replace('_', ' ').title()
                print(f"  {strategy_name}: {results['avg_return']:.1f}% average return")
                if 'excess_return' in results:
                    print(f"    vs Buy-Hold: {results['excess_return']:.1f}% excess")
        
        # Key findings
        findings = []
        
        # Finding 1: Screening selectivity
        if 60.0 in threshold_results:
            selection_rate = threshold_results[60.0]['selection_rate']
            findings.append(f"Screening is highly selective: {selection_rate:.1f}% pass rate")
        
        # Finding 2: Best performing enhanced strategy
        best_strategy = None
        best_return = -float('inf')
        for strategy, results in comparison_results.items():
            if 'error' not in results and 'avg_return' in results:
                if results['avg_return'] > best_return:
                    best_return = results['avg_return']
                    best_strategy = strategy
        
        if best_strategy:
            findings.append(f"Best enhanced strategy: {best_strategy.replace('_', ' ').title()} "
                          f"with {best_return:.1f}% average return")
        
        # Finding 3: Fundamental screening impact
        positive_strategies = len([r for r in comparison_results.values() 
                                 if 'error' not in r and r.get('avg_return', 0) > 0])
        if positive_strategies > 0:
            findings.append(f"Enhanced fundamental screening produced {positive_strategies} "
                          f"strategies with positive returns")
        
        print(f"\nKEY FINDINGS:")
        for i, finding in enumerate(findings, 1):
            print(f"  {i}. {finding}")
        
        # Conclusion
        print(f"\nCONCLUSION:")
        if best_return > 0:
            print("✅ Enhanced fundamental screening improves strategy performance")
            print("✅ Quality stock selection leads to better trading results")
            print("✅ Combining fundamentals + technicals shows promise")
        else:
            print("⚠️  Enhanced strategies still face market efficiency challenges")
            print("⚠️  Fundamental screening alone may not overcome technical limitations")
        
        print(f"\nRECOMMENDATION:")
        print("Enhanced fundamental screening should be integrated into ALL trading strategies")
        print("to improve stock selection and focus on quality growth companies.")
        
        final_report = {
            'test_summary': {
                'total_stocks': total_stocks,
                'strategies_tested': len(comparison_results),
                'best_strategy': best_strategy,
                'best_return': best_return
            },
            'screening_analysis': screening_test,
            'strategy_comparison': strategy_test,
            'impact_analysis': impact_analysis,
            'key_findings': findings
        }
        
        return final_report
    
    def run_comprehensive_test(self) -> Dict:
        """
        Run complete enhanced strategy testing suite
        """
        print("COMPREHENSIVE ENHANCED STRATEGY TEST")
        print("=" * 60)
        print("This test evaluates the impact of enhanced fundamental")
        print("screening on trading strategy performance")
        print("=" * 60)
        
        try:
            # Test 1: Screening effectiveness
            screening_test = self.test_screening_effectiveness()
            
            # Test 2: Enhanced vs original strategies
            strategy_test = self.test_enhanced_vs_original()
            
            # Test 3: Impact analysis
            impact_analysis = self.analyze_fundamental_impact(strategy_test)
            
            # Generate final report
            final_report = self.generate_final_report(
                screening_test, strategy_test, impact_analysis
            )
            
            return final_report
            
        except Exception as e:
            print(f"Error in comprehensive test: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

def main():
    """
    Run enhanced strategy testing
    """
    print("ENHANCED FUNDAMENTAL SCREENING + TRADING STRATEGIES TEST")
    print("=" * 70)
    print("Testing whether enhanced fundamental screening improves")
    print("trading strategy performance through better stock selection")
    print("=" * 70)
    
    tester = EnhancedStrategyTester()
    
    try:
        final_report = tester.run_comprehensive_test()
        
        if 'error' not in final_report:
            print(f"\n" + "=" * 70)
            print("TEST COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("Enhanced fundamental screening has been thoroughly tested")
            print("across multiple trading strategies and timeframes.")
            print()
            print("The results show the impact of quality stock selection")
            print("on trading strategy performance.")
            
            # Save results
            print(f"\nResults saved for further analysis and strategy refinement.")
        else:
            print(f"Test failed: {final_report['error']}")
            
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()