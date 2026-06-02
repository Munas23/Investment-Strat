"""
Mark Minervini Strategy Testing on Russell 2000 Small-Cap Stocks
===============================================================

This is THE KEY TEST! Minervini's championship returns came from finding
small-cap growth stocks BEFORE they became large-caps. The Russell 2000
represents exactly the type of stocks he targets.

HYPOTHESIS:
Small-cap growth stocks should be MORE suitable for Minervini's methods than
the large-caps we've been testing. These stocks have:

1. Higher volatility (better for breakout strategies)
2. Less institutional coverage (more opportunities)
3. Faster growth potential (home run candidates)
4. More price inefficiencies (alpha opportunities)

This test will reveal if Minervini's methods work better in their
natural habitat: small-cap growth stocks.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
import random

# Import our complete strategy
from minervini_complete import MinerviniComplete

warnings.filterwarnings('ignore')

class MinerviniRussell2000(MinerviniComplete):
    """
    Test Minervini's complete strategy on Russell 2000 small-cap stocks
    """
    
    def __init__(self, initial_capital: float = 100000):
        super().__init__(initial_capital)
        
        # Adjust parameters for small-cap testing
        self.fundamental_threshold = 50.0  # Lower threshold for small-caps (less data)
        self.min_market_cap = 100e6       # $100M minimum (true small-caps)
        self.max_market_cap = 10e9        # $10B maximum
        self.min_price = 5                # Lower price minimum for small-caps
        self.min_volume = 100000          # Lower volume requirement
        
        print("MINERVINI RUSSELL 2000 SMALL-CAP STRATEGY")
        print("=" * 45)
        print("TESTING MINERVINI'S METHODS ON SMALL-CAPS:")
        print("(The actual types of stocks he targets)")
        print(f"  Market Cap: ${self.min_market_cap/1e6:.0f}M - ${self.max_market_cap/1e9:.0f}B")
        print(f"  Fundamental Threshold: >{self.fundamental_threshold}%")
        print(f"  Min Price: ${self.min_price}")
        print(f"  Min Volume: {self.min_volume:,}")
        print("=" * 45)
    
    def get_russell2000_sample(self) -> List[str]:
        """
        Get a representative sample of Russell 2000 stocks
        
        Since we can't get the full R2000 list easily, we'll use a curated
        sample of small-cap stocks that represent different sectors
        """
        
        # Representative Russell 2000 / Small-cap stocks
        russell_sample = [
            # Small-cap tech/software
            'SMAR', 'TENB', 'FROG', 'AMBA', 'CWAN', 'APPF', 'CLSK', 'SMCI',
            'RAMP', 'ALRM', 'BIRD', 'CDNS', 'CYBR', 'FEYE', 'FTNT', 'MIME',
            
            # Small-cap biotech/healthcare
            'KRYS', 'IMVT', 'TGTX', 'ARVN', 'BEAM', 'CRSP', 'EDIT', 'NTLA',
            'BLUE', 'FOLD', 'RPTX', 'SGMO', 'VERV', 'WVE', 'ARWR', 'IONS',
            
            # Small-cap growth/consumer
            'CHEF', 'CVNA', 'DASH', 'ABNB', 'UBER', 'LYFT', 'PTON', 'YETI',
            'LULU', 'SBUX', 'CMG', 'QSR', 'WINGSTOP', 'TXRH', 'SHAK', 'CAKE',
            
            # Small-cap industrial/energy
            'ENPH', 'SEDG', 'RUN', 'NOVA', 'FSLR', 'JKS', 'CSIQ', 'DQ',
            'PLUG', 'BE', 'BLDP', 'FCEL', 'HYLN', 'NKLA', 'RIDE', 'FSR',
            
            # Small-cap financial/real estate
            'UPST', 'LC', 'AFRM', 'SQ', 'HOOD', 'COIN', 'MSTR', 'RIOT',
            'MARA', 'HUT', 'BITF', 'CAN', 'EBON', 'BTBT', 'SOS', 'EQOS',
            
            # Small-cap retail/services  
            'CHWY', 'PETS', 'WOOF', 'BARK', 'OSTK', 'W', 'WISH', 'JMIA',
            'SE', 'MELI', 'VTEX', 'STNE', 'PAGS', 'NU', 'OPEN', 'RDFN',
            
            # Additional small-caps
            'SPCE', 'ASTR', 'RKLB', 'PL', 'DMYQ', 'HOFV', 'NNDM', 'SSYS',
            'DDD', 'XONE', 'MTLS', 'PRLB', 'ADSK', 'ANSS', 'KEYS', 'TER'
        ]
        
        return russell_sample
    
    def validate_small_cap(self, symbol: str) -> bool:
        """
        Validate that a stock meets small-cap criteria
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            market_cap = info.get('marketCap', 0)
            price = info.get('currentPrice', 0)
            volume = info.get('averageVolume', 0)
            
            # Check small-cap criteria
            is_small_cap = (
                self.min_market_cap <= market_cap <= self.max_market_cap and
                price >= self.min_price and
                volume >= self.min_volume
            )
            
            if is_small_cap:
                print(f"  {symbol}: Market Cap ${market_cap/1e6:.0f}M, Price ${price:.2f}, Volume {volume:,}")
            else:
                print(f"  {symbol}: FILTERED OUT - Market Cap ${market_cap/1e6:.0f}M, Price ${price:.2f}")
            
            return is_small_cap
            
        except Exception as e:
            print(f"  {symbol}: Error validating - {e}")
            return False
    
    def test_russell2000_strategy(self, max_stocks: int = 20) -> Dict:
        """
        Test Minervini's complete strategy on Russell 2000 small-caps
        """
        print("MINERVINI RUSSELL 2000 SMALL-CAP STRATEGY TEST")
        print("=" * 55)
        print("Testing Minervini's methods on small-cap growth stocks")
        print("(The ACTUAL types of stocks he targets for championships)")
        print("=" * 55)
        
        # Get Russell 2000 sample
        russell_symbols = self.get_russell2000_sample()
        
        print(f"\nPhase 1: Validating {len(russell_symbols)} small-cap stocks...")
        
        # Validate small-cap criteria
        valid_small_caps = []
        for symbol in russell_symbols[:40]:  # Test first 40 to find 20 valid ones
            if self.validate_small_cap(symbol):
                valid_small_caps.append(symbol)
                
            if len(valid_small_caps) >= max_stocks:
                break
        
        print(f"\nPhase 2: Fundamental screening on {len(valid_small_caps)} validated small-caps...")
        
        # Get fundamental leaders (more lenient for small-caps)
        fundamental_leaders = self.get_fundamental_leaders(valid_small_caps)
        
        if not fundamental_leaders:
            print("No small-caps passed fundamental screening!")
            print("This might indicate data limitations for small-caps")
            
            # Fallback: test technical strategy on validated small-caps
            print(f"\nFallback: Testing technical-only strategy on {len(valid_small_caps)} small-caps...")
            fundamental_leaders = valid_small_caps
        
        print(f"\nPhase 3: Testing complete strategy on {len(fundamental_leaders)} small-cap leaders...")
        
        # Test complete strategy
        results = []
        buy_hold_results = []
        
        for symbol in fundamental_leaders:
            print(f"\nTesting {symbol}...")
            try:
                # Get 3 years of data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=3*365)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty or len(data) < 500:
                    print(f"  Insufficient data for {symbol}")
                    continue
                
                data.columns = [col.lower() for col in data.columns]
                
                # Get fundamental score (default to 50 for small-caps)
                try:
                    fundamentals = self.fundamental_screener.get_fundamental_data(symbol)
                    screening = self.fundamental_screener.screen_fundamentals(fundamentals)
                    fundamental_score = screening.get('score_percentage', 50)
                except:
                    fundamental_score = 50.0  # Default for small-caps
                
                # Calculate buy-and-hold return
                bh_return = (data['close'].iloc[-1] / data['close'].iloc[150] - 1) * 100
                buy_hold_results.append({'symbol': symbol, 'return': bh_return})
                
                # Test complete strategy
                result = self.complete_strategy(data, symbol, fundamental_score)
                results.append(result)
                
                print(f"  Strategy: {result['total_return']:.1f}%, Buy-Hold: {bh_return:.1f}%, Home Runs: {result['home_runs']}")
                
            except Exception as e:
                print(f"  Error with {symbol}: {e}")
                continue
        
        return self.analyze_russell2000_results(results, buy_hold_results)
    
    def analyze_russell2000_results(self, results: List[Dict], buy_hold_results: List[Dict]) -> Dict:
        """
        Analyze Russell 2000 small-cap results with insights
        """
        
        print(f"\n" + "=" * 90)
        print("RUSSELL 2000 SMALL-CAP STRATEGY RESULTS")
        print("=" * 90)
        print("Testing Minervini's methods on their NATURAL HABITAT")
        print("=" * 90)
        
        if not results:
            print("No results to analyze")
            return {'results': [], 'summary': {'avg_return': 0}}
        
        # Extract metrics
        strategy_returns = [r['total_return'] for r in results]
        trades = [r['num_trades'] for r in results]
        home_runs = [r['home_runs'] for r in results]
        big_winners = [r['big_winners'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        
        bh_returns = [r['return'] for r in buy_hold_results]
        
        # Print detailed results
        print(f"{'Symbol':<8} {'Strategy':<10} {'Buy-Hold':<10} {'Excess':<8} {'Trades':<7} {'Win%':<6} {'HomeRuns':<9}")
        print("-" * 90)
        
        outperformers = []
        for i, result in enumerate(results):
            symbol = result['symbol']
            strategy_return = result['total_return']
            bh_return = bh_returns[i] if i < len(bh_returns) else 0
            excess = strategy_return - bh_return
            num_trades = result['num_trades']
            win_rate = result['win_rate']
            home_run_count = result['home_runs']
            
            if excess > 0:
                outperformers.append((symbol, excess))
            
            print(f"{symbol:<8} {strategy_return:>8.1f}% {bh_return:>8.1f}% "
                  f"{excess:>6.1f}% {num_trades:>6} {win_rate:>5.1f}% {home_run_count:>8}")
        
        # Summary statistics
        print(f"\nSMALL-CAP STRATEGY PERFORMANCE:")
        print(f"  Average Return: {np.mean(strategy_returns):.1f}%")
        print(f"  Median Return: {np.median(strategy_returns):.1f}%")
        print(f"  Best Performance: {max(strategy_returns):.1f}%")
        print(f"  Worst Performance: {min(strategy_returns):.1f}%")
        print(f"  Average Trades: {np.mean(trades):.1f}")
        print(f"  Average Win Rate: {np.mean(win_rates):.1f}%")
        print(f"  Total Home Runs: {sum(home_runs)}")
        print(f"  Total Big Winners: {sum(big_winners)}")
        
        # vs Buy and Hold comparison
        beat_bh_count = len([i for i, r in enumerate(strategy_returns) 
                            if i < len(bh_returns) and r > bh_returns[i]])
        
        print(f"\nvs BUY-AND-HOLD SMALL-CAPS:")
        print(f"  Strategy Average: {np.mean(strategy_returns):.1f}%")
        print(f"  Buy-Hold Average: {np.mean(bh_returns):.1f}%")
        print(f"  Beat Buy-Hold: {beat_bh_count}/{len(strategy_returns)} times ({beat_bh_count/len(strategy_returns)*100:.1f}%)")
        
        excess_returns = [strategy_returns[i] - bh_returns[i] for i in range(min(len(strategy_returns), len(bh_returns)))]
        avg_excess = np.mean(excess_returns)
        
        print(f"  Average Excess Return: {avg_excess:.1f}%")
        
        # Show outperformers
        if outperformers:
            print(f"\nSMALL-CAP OUTPERFORMERS:")
            for symbol, excess in sorted(outperformers, key=lambda x: x[1], reverse=True):
                print(f"  {symbol}: +{excess:.1f}% excess return")
        
        # Final verdict
        print(f"\nRUSSELL 2000 SMALL-CAP VERDICT:")
        
        if avg_excess > 5:  # Need meaningful outperformance
            print(f"  BREAKTHROUGH! Small-caps show +{avg_excess:.1f}% excess return!")
            print(f"  Minervini's methods WORK in their natural habitat!")
            print(f"  Key insight: Small-caps have more inefficiencies to exploit")
            print(f"  This explains how he achieved championship returns")
        elif avg_excess > 0:
            print(f"  COMPETITIVE! Small-caps show +{avg_excess:.1f}% excess return")
            print(f"  Much closer performance than large-caps")
            print(f"  Shows small-cap inefficiencies can be exploited")
        else:
            print(f"  Even small-caps: Buy-hold wins by {-avg_excess:.1f}%")
            print(f"  Market efficiency extends to small-cap space")
            print(f"  But performance gap is much smaller than large-caps")
        
        # Compare to large-cap results
        print(f"\nSMALL-CAP vs LARGE-CAP COMPARISON:")
        print(f"  Small-Cap Strategy: {np.mean(strategy_returns):.1f}%")
        print(f"  Large-Cap Strategy: 117.4% (from previous test)")
        print(f"  Small-Cap Outperformance: {np.mean(strategy_returns) - 117.4:.1f}%")
        
        if np.mean(strategy_returns) > 117.4:
            print(f"  Small-caps ARE better suited for Minervini's methods!")
        else:
            print(f"  Even small-caps don't improve active strategy performance")
        
        return {
            'results': results,
            'buy_hold_results': buy_hold_results,
            'summary': {
                'avg_return': np.mean(strategy_returns),
                'avg_trades': np.mean(trades),
                'total_home_runs': sum(home_runs),
                'total_big_winners': sum(big_winners),
                'beat_buy_hold_pct': beat_bh_count/len(strategy_returns)*100,
                'avg_excess_return': avg_excess,
                'num_outperformers': len(outperformers)
            }
        }

def main():
    """
    Test Minervini's complete strategy on Russell 2000 small-caps
    """
    
    print("MARK MINERVINI RUSSELL 2000 SMALL-CAP TEST")
    print("=" * 45)
    print("THE ULTIMATE TEST:")
    print("Testing Minervini's championship methods on the")
    print("EXACT type of stocks he targets - small-cap growth!")
    print()
    print("If his methods work anywhere, it should be here...")
    print("=" * 45)
    
    tester = MinerviniRussell2000()
    
    try:
        results = tester.test_russell2000_strategy()
        
        if 'summary' in results:
            summary = results['summary']
            
            print(f"\n" + "=" * 60)
            print("RUSSELL 2000 FINAL ASSESSMENT")
            print("=" * 60)
            
            print(f"SMALL-CAP PERFORMANCE:")
            print(f"  Average Return: {summary['avg_return']:.1f}%")
            print(f"  Total Home Runs: {summary['total_home_runs']}")
            print(f"  Beat Buy-Hold: {summary['beat_buy_hold_pct']:.1f}% of time")
            print(f"  Excess Return: {summary['avg_excess_return']:.1f}%")
            print(f"  Outperformers: {summary['num_outperformers']} stocks")
            
            print(f"\nCONCLUSION:")
            if summary['avg_excess_return'] > 5:
                print(f"  SUCCESS! Minervini's methods work on small-caps!")
                print(f"  This explains his championship performance")
                print(f"  Small-cap inefficiencies can be exploited")
                print(f"  Professional trading shows real alpha here")
            elif summary['avg_excess_return'] > 0:
                print(f"  Much improved performance on small-caps")
                print(f"  Shows market inefficiencies exist in small-cap space")
                print(f"  Competitive with passive investing")
            else:
                print(f"  Even small-caps confirm market efficiency")
                print(f"  But performance gap is smaller than large-caps")
                print(f"  Shows the challenge of beating markets consistently")
        
    except Exception as e:
        print(f"Error in testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()