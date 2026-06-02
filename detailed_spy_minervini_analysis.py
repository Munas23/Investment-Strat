"""
DETAILED SPY MARKET HEALTH ANALYSIS FOR MINERVINI STRATEGY
=========================================================

This script provides a comprehensive analysis of how SPY market conditions
correlate with Minervini strategy performance during 2015-2023, using the
actual trade data from the strategy backtests.

Key Analysis Areas:
1. SPY regime classification and performance metrics
2. Major market downturns and recovery periods identification
3. Strategy performance correlation with market conditions
4. Position sizing overlay simulation and performance impact
5. Risk-adjusted return improvements assessment
"""

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
import re
warnings.filterwarnings('ignore')

class DetailedSPYMinerviniAnalyzer:
    """
    Advanced analyzer for SPY market conditions and Minervini strategy correlation
    """
    
    def __init__(self):
        self.spy_data = None
        self.trade_data = None
        
        print("DETAILED SPY-MINERVINI STRATEGY ANALYZER")
        print("=" * 60)
        
    def download_spy_data(self, start_date: str = "2015-01-01", end_date: str = "2023-12-31") -> pd.DataFrame:
        """Download SPY data and calculate market health indicators"""
        
        print(f"\nDownloading SPY data ({start_date} to {end_date})...")
        
        spy = yf.download('SPY', start=start_date, end=end_date, progress=False)
        
        # Handle multi-level columns
        if isinstance(spy.columns, pd.MultiIndex):
            spy.columns = spy.columns.get_level_values(0)
        
        # Calculate moving averages and indicators
        spy['MA20'] = spy['Close'].rolling(20).mean()
        spy['MA50'] = spy['Close'].rolling(50).mean()
        spy['MA200'] = spy['Close'].rolling(200).mean()
        
        # Market health conditions
        spy['Above_MA20'] = spy['Close'] > spy['MA20']
        spy['Above_MA50'] = spy['Close'] > spy['MA50'] 
        spy['Above_MA200'] = spy['Close'] > spy['MA200']
        
        # Market regimes
        spy['Strong_Bull'] = spy['Above_MA20'] & spy['Above_MA50'] & spy['Above_MA200']
        spy['Weak_Bear'] = ~spy['Above_MA20'] & ~spy['Above_MA50']
        spy['Neutral'] = ~spy['Strong_Bull'] & ~spy['Weak_Bear']
        
        # Volatility and momentum
        spy['Returns'] = spy['Close'].pct_change()
        spy['Volatility_20D'] = spy['Returns'].rolling(20).std() * np.sqrt(252) * 100
        spy['Momentum_20D'] = ((spy['Close'] / spy['Close'].shift(20)) - 1) * 100
        
        self.spy_data = spy
        print(f"SPY data loaded: {len(spy)} trading days")
        return spy
    
    def load_actual_trade_data(self) -> pd.DataFrame:
        """Load the actual Minervini trade data"""
        
        print("\nLoading actual Minervini trade data...")
        
        # Load the most recent enhanced trades file
        import glob
        trade_files = glob.glob("C:/Users/User/Documents/GitHub/minervini_enhanced_trades_*.csv")
        
        if not trade_files:
            raise FileNotFoundError("No Minervini trade files found")
        
        latest_file = max(trade_files, key=lambda x: x.split('_')[-1].split('.')[0])
        print(f"Loading from: {latest_file}")
        
        trades = pd.read_csv(latest_file)
        
        # Parse timestamps more carefully
        def parse_timestamp(ts_str):
            try:
                # Handle timezone-aware timestamps
                if '+' in str(ts_str) or '-' in str(ts_str)[-6:]:
                    return pd.to_datetime(ts_str, utc=True).tz_localize(None)
                else:
                    return pd.to_datetime(ts_str)
            except:
                return pd.NaT
        
        trades['timestamp'] = trades['timestamp'].apply(parse_timestamp)
        trades = trades.dropna(subset=['timestamp'])
        trades['date'] = trades['timestamp'].dt.date
        
        print(f"Loaded {len(trades)} trade records")
        
        self.trade_data = trades
        return trades
    
    def parse_trade_pairs(self) -> pd.DataFrame:
        """Parse buy/sell pairs from trade data"""
        
        print("\nParsing trade pairs...")
        
        buys = self.trade_data[self.trade_data['action'] == 'buy'].copy()
        sells = self.trade_data[self.trade_data['action'] == 'sell'].copy()
        
        trade_pairs = []
        
        # Group by symbol and match buy/sell pairs
        for symbol in buys['symbol'].unique():
            symbol_buys = buys[buys['symbol'] == symbol].sort_values('timestamp')
            symbol_sells = sells[sells['symbol'] == symbol].sort_values('timestamp')
            
            # Simple pairing: match sells to most recent buy
            for _, sell in symbol_sells.iterrows():
                # Find the most recent buy before this sell
                prior_buys = symbol_buys[symbol_buys['timestamp'] < sell['timestamp']]
                if not prior_buys.empty:
                    buy = prior_buys.iloc[-1]
                    
                    # Calculate trade metrics
                    return_pct = ((sell['price'] / buy['price']) - 1) * 100
                    hold_days = (sell['timestamp'] - buy['timestamp']).days
                    
                    # Extract conviction level from reason if available
                    conviction = self.extract_conviction(buy.get('reason', ''))
                    
                    trade_pairs.append({
                        'symbol': symbol,
                        'entry_date': buy['timestamp'],
                        'exit_date': sell['timestamp'], 
                        'entry_price': buy['price'],
                        'exit_price': sell['price'],
                        'return_pct': return_pct,
                        'hold_days': hold_days,
                        'conviction': conviction,
                        'exit_reason': sell.get('reason', 'Unknown')
                    })
        
        trade_pairs_df = pd.DataFrame(trade_pairs)
        print(f"Parsed {len(trade_pairs_df)} complete trade pairs")
        
        return trade_pairs_df
    
    def extract_conviction(self, reason_str: str) -> int:
        """Extract conviction level from trade reason string"""
        
        if pd.isna(reason_str):
            return 1
            
        # Look for conviction patterns
        conviction_patterns = {
            'Conviction 5': 5,
            'Conviction 4': 4, 
            'Conviction 3': 3,
            'Conviction 2': 2,
            'Conviction 1': 1,
            'MAXIMUM': 5,
            'HIGH': 4,
            'STANDARD': 3,
            'LOW': 2,
            'MINIMAL': 1
        }
        
        reason_upper = str(reason_str).upper()
        for pattern, level in conviction_patterns.items():
            if pattern.upper() in reason_upper:
                return level
        
        return 1  # Default to minimal conviction
    
    def merge_with_spy_data(self, trade_pairs: pd.DataFrame) -> pd.DataFrame:
        """Merge trade data with SPY market conditions"""
        
        print("\nMerging trades with SPY market data...")
        
        # Prepare SPY data for merging
        spy_daily = self.spy_data.copy()
        spy_daily['date'] = spy_daily.index.date
        
        # Merge on entry date
        merged = trade_pairs.merge(
            spy_daily[['date', 'Strong_Bull', 'Weak_Bear', 'Neutral', 
                      'Above_MA20', 'Above_MA50', 'Above_MA200',
                      'Volatility_20D', 'Momentum_20D', 'Close']],
            left_on=trade_pairs['entry_date'].dt.date,
            right_on='date',
            how='left',
            suffixes=('', '_spy')
        )
        
        # Rename SPY columns for clarity
        merged.rename(columns={
            'Close': 'spy_price_entry',
            'Strong_Bull': 'entry_strong_bull',
            'Weak_Bear': 'entry_weak_bear', 
            'Neutral': 'entry_neutral',
            'Above_MA20': 'entry_above_ma20',
            'Above_MA50': 'entry_above_ma50',
            'Above_MA200': 'entry_above_ma200',
            'Volatility_20D': 'entry_volatility',
            'Momentum_20D': 'entry_momentum'
        }, inplace=True)
        
        merged.drop('date', axis=1, inplace=True)
        
        print(f"Successfully merged {len(merged)} trades with SPY data")
        return merged
    
    def analyze_performance_by_regime(self, merged_trades: pd.DataFrame) -> Dict:
        """Analyze strategy performance by market regime"""
        
        print("\nAnalyzing performance by market regime...")
        
        regimes = {
            'Strong Bull Market': merged_trades['entry_strong_bull'],
            'Weak Bear Market': merged_trades['entry_weak_bear'],
            'Neutral Market': merged_trades['entry_neutral']
        }
        
        regime_analysis = {}
        
        for regime_name, regime_mask in regimes.items():
            regime_trades = merged_trades[regime_mask == True]
            
            if not regime_trades.empty:
                returns = regime_trades['return_pct']
                
                regime_analysis[regime_name] = {
                    'total_trades': len(regime_trades),
                    'avg_return': returns.mean(),
                    'median_return': returns.median(),
                    'win_rate': (returns > 0).mean() * 100,
                    'avg_winner': returns[returns > 0].mean() if (returns > 0).any() else 0,
                    'avg_loser': returns[returns < 0].mean() if (returns < 0).any() else 0,
                    'best_trade': returns.max(),
                    'worst_trade': returns.min(),
                    'volatility': returns.std(),
                    'avg_hold_days': regime_trades['hold_days'].mean(),
                    'home_runs': (returns >= 50).sum(),
                    'big_losers': (returns <= -20).sum()
                }
        
        return regime_analysis
    
    def identify_major_periods(self) -> Dict:
        """Identify major market periods and their characteristics"""
        
        periods = {
            'Oil Crash 2016': ('2016-01-01', '2016-03-31'),
            'Trump Rally': ('2016-11-01', '2018-01-31'), 
            '2018 Volatility': ('2018-02-01', '2018-12-31'),
            '2019 Recovery': ('2019-01-01', '2020-02-01'),
            'COVID Crash': ('2020-02-01', '2020-04-30'),
            'COVID Recovery': ('2020-05-01', '2021-12-31'),
            'Inflation Bear': ('2022-01-01', '2022-10-31'),
            '2023 Recovery': ('2023-01-01', '2023-12-31')
        }
        
        period_analysis = {}
        
        for period_name, (start, end) in periods.items():
            period_spy = self.spy_data.loc[start:end]
            
            if not period_spy.empty:
                period_return = ((period_spy['Close'].iloc[-1] / period_spy['Close'].iloc[0]) - 1) * 100
                max_dd = self.calculate_max_drawdown(period_spy['Close'])
                avg_vol = period_spy['Volatility_20D'].mean()
                
                # Market regime percentages
                bull_pct = period_spy['Strong_Bull'].mean() * 100
                bear_pct = period_spy['Weak_Bear'].mean() * 100
                
                period_analysis[period_name] = {
                    'spy_return': period_return,
                    'max_drawdown': max_dd,
                    'avg_volatility': avg_vol,
                    'bull_regime_pct': bull_pct,
                    'bear_regime_pct': bear_pct,
                    'trading_days': len(period_spy)
                }
        
        return period_analysis
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak * 100
        return drawdown.min()
    
    def simulate_market_overlay(self, merged_trades: pd.DataFrame) -> Dict:
        """Simulate market health position sizing overlay"""
        
        print("\nSimulating market health overlay...")
        
        # Original strategy returns
        original_returns = merged_trades['return_pct'].tolist()
        
        # Apply market overlay rules
        enhanced_returns = []
        adjustments = []
        
        for _, trade in merged_trades.iterrows():
            base_return = trade['return_pct']
            
            # Market overlay rules:
            # HALVE size when SPY below both 20MA and 50MA
            if not trade['entry_above_ma20'] and not trade['entry_above_ma50']:
                adjusted_return = base_return * 0.5
                adjustment = "HALVED"
            
            # DOUBLE size when SPY above all MAs (strong bull)
            elif trade['entry_strong_bull']:
                adjusted_return = base_return * 2.0  
                adjustment = "DOUBLED"
            
            # Normal size otherwise
            else:
                adjusted_return = base_return
                adjustment = "NORMAL"
            
            enhanced_returns.append(adjusted_return)
            adjustments.append(adjustment)
        
        # Calculate performance metrics
        def calc_metrics(returns_list):
            returns_arr = np.array(returns_list)
            return {
                'avg_return': np.mean(returns_arr),
                'median_return': np.median(returns_arr),
                'volatility': np.std(returns_arr),
                'win_rate': (returns_arr > 0).mean() * 100,
                'sharpe_ratio': np.mean(returns_arr) / np.std(returns_arr) if np.std(returns_arr) > 0 else 0,
                'max_drawdown': self.calculate_trade_drawdown(returns_list),
                'total_return': np.sum(returns_arr)
            }
        
        original_metrics = calc_metrics(original_returns)
        enhanced_metrics = calc_metrics(enhanced_returns)
        
        # Count adjustments
        from collections import Counter
        adjustment_counts = Counter(adjustments)
        
        return {
            'original': original_metrics,
            'enhanced': enhanced_metrics,
            'adjustments': dict(adjustment_counts),
            'improvement': {
                'avg_return': enhanced_metrics['avg_return'] - original_metrics['avg_return'],
                'volatility': enhanced_metrics['volatility'] - original_metrics['volatility'], 
                'sharpe_ratio': enhanced_metrics['sharpe_ratio'] - original_metrics['sharpe_ratio'],
                'total_return': enhanced_metrics['total_return'] - original_metrics['total_return']
            }
        }
    
    def calculate_trade_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown from trade sequence"""
        cumulative = np.cumprod([1 + r/100 for r in returns])
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak * 100
        return np.min(drawdown)
    
    def generate_detailed_report(self):
        """Generate comprehensive analysis report"""
        
        print("\n" + "=" * 80)
        print("DETAILED SPY MARKET HEALTH ANALYSIS FOR MINERVINI STRATEGY")
        print("=" * 80)
        
        # Load and process data
        spy_data = self.download_spy_data()
        trade_data = self.load_actual_trade_data()
        trade_pairs = self.parse_trade_pairs()
        merged_trades = self.merge_with_spy_data(trade_pairs)
        
        # Perform analysis
        regime_performance = self.analyze_performance_by_regime(merged_trades)
        period_analysis = self.identify_major_periods()
        overlay_results = self.simulate_market_overlay(merged_trades)
        
        # Generate report sections
        self.print_regime_analysis(regime_performance)
        self.print_period_analysis(period_analysis)
        self.print_overlay_analysis(overlay_results)
        self.print_detailed_recommendations(overlay_results, regime_performance)
        
        return {
            'regime_performance': regime_performance,
            'period_analysis': period_analysis,
            'overlay_results': overlay_results,
            'trade_data': merged_trades
        }
    
    def print_regime_analysis(self, regime_performance: Dict):
        """Print market regime analysis results"""
        
        print(f"\n1. STRATEGY PERFORMANCE BY MARKET REGIME")
        print("=" * 60)
        
        for regime, stats in regime_performance.items():
            print(f"\n{regime.upper()}:")
            print(f"  Total Trades: {stats['total_trades']}")
            print(f"  Average Return: {stats['avg_return']:.1f}%")
            print(f"  Median Return: {stats['median_return']:.1f}%") 
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            print(f"  Average Winner: {stats['avg_winner']:.1f}%")
            print(f"  Average Loser: {stats['avg_loser']:.1f}%")
            print(f"  Best Trade: {stats['best_trade']:.1f}%")
            print(f"  Worst Trade: {stats['worst_trade']:.1f}%")
            print(f"  Return Volatility: {stats['volatility']:.1f}%")
            print(f"  Average Hold Days: {stats['avg_hold_days']:.0f}")
            print(f"  Home Runs (>50%): {stats['home_runs']}")
            print(f"  Big Losers (<-20%): {stats['big_losers']}")
    
    def print_period_analysis(self, period_analysis: Dict):
        """Print major period analysis results"""
        
        print(f"\n2. MAJOR MARKET PERIODS ANALYSIS")
        print("=" * 60)
        
        for period, stats in period_analysis.items():
            print(f"\n{period.upper()}:")
            print(f"  SPY Return: {stats['spy_return']:.1f}%")
            print(f"  Max Drawdown: {stats['max_drawdown']:.1f}%")
            print(f"  Average Volatility: {stats['avg_volatility']:.1f}%")
            print(f"  Bull Regime Days: {stats['bull_regime_pct']:.1f}%")
            print(f"  Bear Regime Days: {stats['bear_regime_pct']:.1f}%")
            print(f"  Trading Days: {stats['trading_days']}")
    
    def print_overlay_analysis(self, overlay_results: Dict):
        """Print market overlay analysis results"""
        
        print(f"\n3. MARKET HEALTH OVERLAY RESULTS")
        print("=" * 60)
        
        orig = overlay_results['original']
        enhanced = overlay_results['enhanced']
        improvement = overlay_results['improvement']
        adjustments = overlay_results['adjustments']
        
        print(f"\nORIGINAL STRATEGY PERFORMANCE:")
        print(f"  Average Return per Trade: {orig['avg_return']:.1f}%")
        print(f"  Total Return: {orig['total_return']:.1f}%")
        print(f"  Win Rate: {orig['win_rate']:.1f}%")
        print(f"  Volatility: {orig['volatility']:.1f}%")
        print(f"  Sharpe Ratio: {orig['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {orig['max_drawdown']:.1f}%")
        
        print(f"\nENHANCED STRATEGY (Market Overlay):")
        print(f"  Average Return per Trade: {enhanced['avg_return']:.1f}%")
        print(f"  Total Return: {enhanced['total_return']:.1f}%")
        print(f"  Win Rate: {enhanced['win_rate']:.1f}%")
        print(f"  Volatility: {enhanced['volatility']:.1f}%")
        print(f"  Sharpe Ratio: {enhanced['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {enhanced['max_drawdown']:.1f}%")
        
        print(f"\nIMPROVEMENT METRICS:")
        print(f"  Average Return Improvement: {improvement['avg_return']:.1f} pp")
        print(f"  Total Return Improvement: {improvement['total_return']:.1f} pp")
        print(f"  Volatility Change: {improvement['volatility']:.1f} pp")
        print(f"  Sharpe Ratio Improvement: {improvement['sharpe_ratio']:.2f}")
        
        print(f"\nPOSITION ADJUSTMENTS BREAKDOWN:")
        total_trades = sum(adjustments.values())
        for adj_type, count in adjustments.items():
            pct = count / total_trades * 100
            print(f"  {adj_type}: {count} trades ({pct:.1f}%)")
    
    def print_detailed_recommendations(self, overlay_results: Dict, regime_performance: Dict):
        """Print detailed recommendations"""
        
        print(f"\n4. DETAILED RECOMMENDATIONS")
        print("=" * 60)
        
        improvement = overlay_results['improvement']
        
        print(f"\nMARKET HEALTH OVERLAY ASSESSMENT:")
        
        if improvement['avg_return'] > 2 and improvement['sharpe_ratio'] > 0.1:
            print("STRONG RECOMMENDATION: Implement market health overlay")
            print(f"  • Significant improvement in average returns (+{improvement['avg_return']:.1f} pp)")
            print(f"  • Meaningful Sharpe ratio enhancement (+{improvement['sharpe_ratio']:.2f})")
            print(f"  • Total return boost: +{improvement['total_return']:.1f} percentage points")
            
        elif improvement['sharpe_ratio'] > 0 and improvement['avg_return'] > 0:
            print("MODERATE RECOMMENDATION: Consider implementing overlay")
            print(f"  • Modest improvements in risk-adjusted returns")
            print(f"  • Average return improvement: +{improvement['avg_return']:.1f} pp")
            print(f"  • Sharpe ratio improvement: +{improvement['sharpe_ratio']:.2f}")
            print(f"  • Monitor implementation complexity vs benefits")
            
        else:
            print("NOT RECOMMENDED: Market overlay reduces performance")
            print(f"  • Negative impact on risk-adjusted returns")
            print(f"  • Average return change: {improvement['avg_return']:.1f} pp")
            print(f"  • Sharpe ratio change: {improvement['sharpe_ratio']:.2f}")
            print(f"  • Stick with original strategy")
        
        print(f"\nKEY INSIGHTS FROM REGIME ANALYSIS:")
        
        # Find best performing regime
        best_regime = max(regime_performance.keys(), 
                         key=lambda x: regime_performance[x]['avg_return'])
        worst_regime = min(regime_performance.keys(),
                          key=lambda x: regime_performance[x]['avg_return'])
        
        print(f"  • Best performing regime: {best_regime}")
        print(f"    Average return: {regime_performance[best_regime]['avg_return']:.1f}%")
        print(f"    Win rate: {regime_performance[best_regime]['win_rate']:.1f}%")
        
        print(f"  • Worst performing regime: {worst_regime}")
        print(f"    Average return: {regime_performance[worst_regime]['avg_return']:.1f}%")
        print(f"    Win rate: {regime_performance[worst_regime]['win_rate']:.1f}%")
        
        print(f"\nIMPLEMENTATION GUIDELINES:")
        print(f"  • Monitor SPY vs 20MA, 50MA, and 200MA daily")
        print(f"  • Adjust position sizes based on market regime:")
        print(f"    - HALVE sizes when SPY < 20MA AND SPY < 50MA")
        print(f"    - DOUBLE sizes when SPY > 20MA AND > 50MA AND > 200MA")
        print(f"    - Normal sizes otherwise")
        print(f"  • Review and adjust rules quarterly based on market evolution")

def main():
    """Run detailed SPY-Minervini analysis"""
    
    analyzer = DetailedSPYMinerviniAnalyzer()
    
    try:
        results = analyzer.generate_detailed_report()
        
        print(f"\n" + "=" * 80)
        print(f"ANALYSIS COMPLETE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("Comprehensive SPY market health analysis completed.")
        print("Use results to optimize Minervini strategy performance.")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()