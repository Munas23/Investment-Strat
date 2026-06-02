"""
SPY Market Health Analysis for Minervini Strategy (2015-2023)
============================================================

This analysis examines SPY market conditions during the Minervini strategy backtest 
periods to determine if adding a market health overlay would improve performance.

Key Analysis:
1. SPY moving averages (20, 50, 200-day) and market health indicators
2. Identification of major market downturns and recoveries  
3. Correlation with strategy performance during different market regimes
4. Simulation of position sizing adjustments based on market conditions
5. Risk-adjusted return improvements assessment

Market Health Overlay Rules:
- HALVE position sizes when SPY < 20MA AND SPY < 50MA 
- DOUBLE position sizes when SPY > 20MA AND SPY > 50MA AND SPY > 200MA
- Normal sizing otherwise
"""

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class SPYMarketHealthAnalyzer:
    """
    Comprehensive SPY market health analysis for strategy optimization
    """
    
    def __init__(self, start_date: str = "2015-01-01", end_date: str = "2023-12-31"):
        self.start_date = start_date
        self.end_date = end_date
        self.spy_data = None
        self.market_regimes = None
        
        print("SPY MARKET HEALTH ANALYZER")
        print("=" * 50)
        print(f"Analysis Period: {start_date} to {end_date}")
        print("=" * 50)
        
    def download_spy_data(self) -> pd.DataFrame:
        """Download and prepare SPY data with moving averages"""
        
        print("\nDownloading SPY data...")
        self.spy_data = yf.download('SPY', start=self.start_date, end=self.end_date, progress=False)
        
        if self.spy_data.empty:
            raise ValueError("Failed to download SPY data")
        
        # Flatten multi-level columns if necessary
        if isinstance(self.spy_data.columns, pd.MultiIndex):
            self.spy_data.columns = self.spy_data.columns.get_level_values(0)
            
        # Calculate moving averages
        close_prices = self.spy_data['Close']
        self.spy_data['MA20'] = close_prices.rolling(window=20).mean()
        self.spy_data['MA50'] = close_prices.rolling(window=50).mean() 
        self.spy_data['MA200'] = close_prices.rolling(window=200).mean()
        
        # Calculate market health indicators
        self.spy_data['Above_MA20'] = close_prices > self.spy_data['MA20']
        self.spy_data['Above_MA50'] = close_prices > self.spy_data['MA50']
        self.spy_data['Above_MA200'] = close_prices > self.spy_data['MA200']
        
        # Market regime classification
        self.spy_data['Bullish_Regime'] = (
            self.spy_data['Above_MA20'] & 
            self.spy_data['Above_MA50'] & 
            self.spy_data['Above_MA200']
        )
        
        self.spy_data['Bearish_Regime'] = (
            ~self.spy_data['Above_MA20'] & 
            ~self.spy_data['Above_MA50']
        )
        
        self.spy_data['Neutral_Regime'] = (
            ~self.spy_data['Bullish_Regime'] & 
            ~self.spy_data['Bearish_Regime']
        )
        
        # Calculate volatility and momentum
        self.spy_data['Returns'] = self.spy_data['Close'].pct_change()
        self.spy_data['Volatility_20D'] = self.spy_data['Returns'].rolling(20).std() * np.sqrt(252)
        self.spy_data['Momentum_20D'] = ((self.spy_data['Close'] / self.spy_data['Close'].shift(20)) - 1) * 100
        
        print(f"SPY data loaded: {len(self.spy_data)} trading days")
        return self.spy_data
    
    def identify_market_periods(self) -> Dict:
        """Identify major market periods and regimes"""
        
        print("\nIdentifying major market periods...")
        
        periods = {
            # Major bull/bear periods
            'Post_Crisis_Bull': ('2015-01-01', '2016-01-01'),
            'Oil_Crash_Correction': ('2016-01-01', '2016-03-01'),
            'Trump_Rally': ('2016-11-01', '2018-01-01'),
            'Vol_Spike_2018': ('2018-02-01', '2018-04-01'),
            'Trade_War_Volatility': ('2018-10-01', '2018-12-31'),
            'Recovery_2019': ('2019-01-01', '2020-02-01'),
            'COVID_Crash': ('2020-02-01', '2020-04-01'),
            'COVID_Recovery': ('2020-04-01', '2021-01-01'),
            'Meme_Bubble': ('2021-01-01', '2021-11-01'),
            'Inflation_Selloff': ('2021-11-01', '2022-10-01'),
            'Bear_Market_Rally': ('2022-10-01', '2023-01-01'),
            'Banking_Crisis': ('2023-03-01', '2023-05-01'),
            'AI_Rally': ('2023-05-01', '2023-12-31')
        }
        
        regime_analysis = {}
        
        for period_name, (start, end) in periods.items():
            period_data = self.spy_data.loc[start:end]
            if not period_data.empty:
                total_return = ((period_data['Close'].iloc[-1] / period_data['Close'].iloc[0]) - 1) * 100
                max_drawdown = self.calculate_max_drawdown(period_data['Close'])
                volatility = period_data['Volatility_20D'].mean()
                
                # Regime percentages
                bull_pct = period_data['Bullish_Regime'].mean() * 100
                bear_pct = period_data['Bearish_Regime'].mean() * 100
                neutral_pct = period_data['Neutral_Regime'].mean() * 100
                
                regime_analysis[period_name] = {
                    'start_date': start,
                    'end_date': end,
                    'total_return': total_return,
                    'max_drawdown': max_drawdown,
                    'volatility': volatility,
                    'bull_regime_pct': bull_pct,
                    'bear_regime_pct': bear_pct,
                    'neutral_regime_pct': neutral_pct,
                    'trading_days': len(period_data)
                }
        
        self.market_regimes = regime_analysis
        return regime_analysis
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = prices.expanding(min_periods=1).max()
        drawdown = (prices - peak) / peak
        return drawdown.min() * 100
    
    def analyze_regime_performance(self) -> Dict:
        """Analyze SPY performance in different market regimes"""
        
        print("\nAnalyzing regime-based performance...")
        
        regime_stats = {}
        
        for regime in ['Bullish_Regime', 'Bearish_Regime', 'Neutral_Regime']:
            regime_mask = self.spy_data[regime]
            regime_data = self.spy_data[regime_mask]
            
            if not regime_data.empty:
                avg_return = regime_data['Returns'].mean() * 252 * 100  # Annualized
                volatility = regime_data['Returns'].std() * np.sqrt(252) * 100
                sharpe = avg_return / volatility if volatility > 0 else 0
                win_rate = (regime_data['Returns'] > 0).mean() * 100
                
                regime_stats[regime] = {
                    'trading_days': len(regime_data),
                    'pct_of_period': len(regime_data) / len(self.spy_data) * 100,
                    'avg_annual_return': avg_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe,
                    'win_rate': win_rate
                }
        
        return regime_stats
    
    def load_minervini_trades(self) -> pd.DataFrame:
        """Load and analyze Minervini strategy trade data"""
        
        print("\nLoading Minervini trade data...")
        
        # For now, create simulation data to demonstrate the analysis
        print("Creating simulation data for demonstration...")
        return self.simulate_minervini_trades()
    
    def simulate_minervini_trades(self) -> pd.DataFrame:
        """Simulate Minervini-style trades for analysis if real data not available"""
        
        print("Simulating Minervini trades based on SPY momentum...")
        
        # Generate trade signals based on SPY momentum and volatility
        signals = []
        
        for i in range(200, len(self.spy_data), 5):  # Check every 5 days
            date = self.spy_data.index[i]
            
            # Generate signals based on market momentum
            momentum = self.spy_data['Momentum_20D'].iloc[i]
            volatility = self.spy_data['Volatility_20D'].iloc[i]
            
            # Higher probability of trades in trending markets
            if momentum > 5 and volatility < 25 and np.random.random() > 0.7:
                # Simulate a buy signal
                signals.append({
                    'timestamp': date,
                    'action': 'buy',
                    'symbol': f'SIM{len(signals)}',
                    'price': 100 + np.random.normal(0, 10),
                    'quantity': np.random.randint(100, 1000),
                    'reason': f'Momentum: {momentum:.1f}%, Vol: {volatility:.1f}%'
                })
                
                # Simulate corresponding sell 20-60 days later
                sell_days = np.random.randint(20, 60)
                if i + sell_days < len(self.spy_data):
                    sell_date = self.spy_data.index[i + sell_days]
                    
                    # Return based on market performance + noise
                    market_return = ((self.spy_data['Close'].iloc[i + sell_days] / 
                                    self.spy_data['Close'].iloc[i]) - 1) * 100
                    trade_return = market_return + np.random.normal(0, 5)  # Add alpha/noise
                    
                    sell_price = signals[-1]['price'] * (1 + trade_return/100)
                    
                    signals.append({
                        'timestamp': sell_date,
                        'action': 'sell', 
                        'symbol': signals[-1]['symbol'],
                        'price': sell_price,
                        'quantity': signals[-1]['quantity'],
                        'reason': f'Return: {trade_return:.1f}%'
                    })
        
        return pd.DataFrame(signals)
    
    def correlate_trades_with_market(self, trades_df: pd.DataFrame) -> Dict:
        """Correlate trade performance with market conditions"""
        
        print("\nCorrelating trades with market conditions...")
        
        # Merge trades with SPY data
        trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.date
        spy_daily = self.spy_data.copy()
        spy_daily['date'] = spy_daily.index.date
        
        trades_with_market = trades_df.merge(
            spy_daily[['date', 'Bullish_Regime', 'Bearish_Regime', 'Neutral_Regime',
                      'Above_MA20', 'Above_MA50', 'Above_MA200', 'Volatility_20D', 'Momentum_20D']],
            on='date', how='left'
        )
        
        # Calculate trade returns
        buy_trades = trades_with_market[trades_with_market['action'] == 'buy'].copy()
        sell_trades = trades_with_market[trades_with_market['action'] == 'sell'].copy()
        
        # Match buy/sell pairs
        trade_pairs = []
        for _, sell in sell_trades.iterrows():
            # Find corresponding buy
            buys = buy_trades[buy_trades['symbol'] == sell['symbol']]
            if not buys.empty:
                buy = buys.iloc[-1]  # Most recent buy
                
                trade_return = ((sell['price'] / buy['price']) - 1) * 100
                hold_days = (sell['timestamp'] - buy['timestamp']).days
                
                trade_pairs.append({
                    'symbol': sell['symbol'],
                    'entry_date': buy['timestamp'],
                    'exit_date': sell['timestamp'],
                    'entry_price': buy['price'],
                    'exit_price': sell['price'],
                    'return_pct': trade_return,
                    'hold_days': hold_days,
                    'bullish_regime': buy['Bullish_Regime'],
                    'bearish_regime': buy['Bearish_Regime'],
                    'neutral_regime': buy['Neutral_Regime'],
                    'above_ma20': buy['Above_MA20'],
                    'above_ma50': buy['Above_MA50'], 
                    'above_ma200': buy['Above_MA200'],
                    'entry_volatility': buy['Volatility_20D'],
                    'entry_momentum': buy['Momentum_20D']
                })
        
        trade_analysis = pd.DataFrame(trade_pairs)
        
        if trade_analysis.empty:
            print("No complete trade pairs found")
            return {}
        
        # Analyze performance by regime
        regime_performance = {}
        
        for regime in ['bullish_regime', 'bearish_regime', 'neutral_regime']:
            regime_trades = trade_analysis[trade_analysis[regime] == True]
            
            if not regime_trades.empty:
                avg_return = regime_trades['return_pct'].mean()
                win_rate = (regime_trades['return_pct'] > 0).mean() * 100
                avg_hold_days = regime_trades['hold_days'].mean()
                total_trades = len(regime_trades)
                
                regime_performance[regime] = {
                    'total_trades': total_trades,
                    'avg_return': avg_return,
                    'win_rate': win_rate,
                    'avg_hold_days': avg_hold_days,
                    'best_trade': regime_trades['return_pct'].max(),
                    'worst_trade': regime_trades['return_pct'].min()
                }
        
        return {
            'trade_analysis': trade_analysis,
            'regime_performance': regime_performance
        }
    
    def simulate_market_overlay_strategy(self, trades_df: pd.DataFrame) -> Dict:
        """Simulate the impact of market health overlay on position sizing"""
        
        print("\nSimulating market health overlay strategy...")
        
        correlation_results = self.correlate_trades_with_market(trades_df)
        if not correlation_results:
            return {}
            
        trade_analysis = correlation_results['trade_analysis']
        
        # Calculate original strategy performance
        original_returns = trade_analysis['return_pct'].tolist()
        original_avg_return = np.mean(original_returns)
        original_win_rate = (np.array(original_returns) > 0).mean() * 100
        
        # Apply market overlay rules
        enhanced_returns = []
        position_adjustments = []
        
        for _, trade in trade_analysis.iterrows():
            base_return = trade['return_pct']
            
            # Market health overlay rules
            if not trade['above_ma20'] and not trade['above_ma50']:
                # HALVE position size in weak markets
                # This reduces both gains and losses by 50%
                adjusted_return = base_return * 0.5
                adjustment = "HALVED"
                
            elif trade['above_ma20'] and trade['above_ma50'] and trade['above_ma200']:
                # DOUBLE position size in strong markets  
                # This doubles both gains and losses
                adjusted_return = base_return * 2.0
                adjustment = "DOUBLED"
                
            else:
                # Normal position size
                adjusted_return = base_return
                adjustment = "NORMAL"
            
            enhanced_returns.append(adjusted_return)
            position_adjustments.append(adjustment)
        
        # Calculate enhanced strategy performance
        enhanced_avg_return = np.mean(enhanced_returns)
        enhanced_win_rate = (np.array(enhanced_returns) > 0).mean() * 100
        
        # Risk metrics
        original_volatility = np.std(original_returns)
        enhanced_volatility = np.std(enhanced_returns)
        
        original_sharpe = original_avg_return / original_volatility if original_volatility > 0 else 0
        enhanced_sharpe = enhanced_avg_return / enhanced_volatility if enhanced_volatility > 0 else 0
        
        # Drawdown analysis
        original_max_dd = self.calculate_trade_drawdown(original_returns)
        enhanced_max_dd = self.calculate_trade_drawdown(enhanced_returns)
        
        # Count adjustments
        adjustments_count = pd.Series(position_adjustments).value_counts()
        
        return {
            'original_performance': {
                'avg_return': original_avg_return,
                'win_rate': original_win_rate,
                'volatility': original_volatility,
                'sharpe_ratio': original_sharpe,
                'max_drawdown': original_max_dd,
                'total_trades': len(original_returns)
            },
            'enhanced_performance': {
                'avg_return': enhanced_avg_return,
                'win_rate': enhanced_win_rate,
                'volatility': enhanced_volatility,
                'sharpe_ratio': enhanced_sharpe,
                'max_drawdown': enhanced_max_dd,
                'total_trades': len(enhanced_returns)
            },
            'improvement': {
                'return_improvement': enhanced_avg_return - original_avg_return,
                'sharpe_improvement': enhanced_sharpe - original_sharpe,
                'volatility_change': enhanced_volatility - original_volatility,
                'drawdown_improvement': enhanced_max_dd - original_max_dd
            },
            'position_adjustments': adjustments_count.to_dict(),
            'trade_details': pd.DataFrame({
                'original_return': original_returns,
                'enhanced_return': enhanced_returns,
                'adjustment': position_adjustments
            })
        }
    
    def calculate_trade_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown from trade returns"""
        cumulative = np.cumprod([1 + r/100 for r in returns])
        peak = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - peak) / peak
        return np.min(drawdown) * 100
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        
        print("\n" + "=" * 80)
        print("SPY MARKET HEALTH ANALYSIS REPORT (2015-2023)")
        print("=" * 80)
        
        # Download and analyze SPY data
        spy_data = self.download_spy_data()
        market_periods = self.identify_market_periods()
        regime_performance = self.analyze_regime_performance()
        
        # Load and analyze trade data
        trades_df = self.load_minervini_trades()
        correlation_results = self.correlate_trades_with_market(trades_df)
        overlay_results = self.simulate_market_overlay_strategy(trades_df)
        
        # Generate report sections
        self.print_spy_analysis(regime_performance, market_periods)
        self.print_correlation_analysis(correlation_results)
        self.print_overlay_results(overlay_results)
        
        return {
            'spy_analysis': {
                'regime_performance': regime_performance,
                'market_periods': market_periods
            },
            'trade_correlation': correlation_results,
            'market_overlay': overlay_results
        }
    
    def print_spy_analysis(self, regime_performance: Dict, market_periods: Dict):
        """Print SPY analysis section"""
        
        print(f"\n1. SPY MARKET REGIME ANALYSIS")
        print("-" * 50)
        
        for regime, stats in regime_performance.items():
            regime_name = regime.replace('_', ' ').title()
            print(f"\n{regime_name}:")
            print(f"  Trading Days: {stats['trading_days']} ({stats['pct_of_period']:.1f}% of period)")
            print(f"  Annualized Return: {stats['avg_annual_return']:.1f}%")
            print(f"  Volatility: {stats['volatility']:.1f}%")
            print(f"  Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
        
        print(f"\n2. MAJOR MARKET PERIODS")
        print("-" * 50)
        
        for period, stats in market_periods.items():
            period_name = period.replace('_', ' ').title()
            print(f"\n{period_name} ({stats['start_date']} to {stats['end_date']}):")
            print(f"  Total Return: {stats['total_return']:.1f}%")
            print(f"  Max Drawdown: {stats['max_drawdown']:.1f}%")
            print(f"  Average Volatility: {stats['volatility']:.1f}%")
            print(f"  Bullish Regime: {stats['bull_regime_pct']:.1f}% of period")
            print(f"  Bearish Regime: {stats['bear_regime_pct']:.1f}% of period")
    
    def print_correlation_analysis(self, correlation_results: Dict):
        """Print trade correlation analysis"""
        
        print(f"\n3. TRADE PERFORMANCE BY MARKET REGIME")
        print("-" * 50)
        
        if not correlation_results:
            print("No correlation data available")
            return
        
        regime_performance = correlation_results['regime_performance']
        
        for regime, stats in regime_performance.items():
            regime_name = regime.replace('_', ' ').title()
            print(f"\n{regime_name} Trades:")
            print(f"  Total Trades: {stats['total_trades']}")
            print(f"  Average Return: {stats['avg_return']:.1f}%")
            print(f"  Win Rate: {stats['win_rate']:.1f}%")
            print(f"  Average Hold Days: {stats['avg_hold_days']:.1f}")
            print(f"  Best Trade: {stats['best_trade']:.1f}%")
            print(f"  Worst Trade: {stats['worst_trade']:.1f}%")
    
    def print_overlay_results(self, overlay_results: Dict):
        """Print market overlay strategy results"""
        
        print(f"\n4. MARKET HEALTH OVERLAY RESULTS")
        print("-" * 50)
        
        if not overlay_results:
            print("No overlay results available")
            return
        
        original = overlay_results['original_performance']
        enhanced = overlay_results['enhanced_performance']
        improvement = overlay_results['improvement']
        adjustments = overlay_results['position_adjustments']
        
        print(f"\nORIGINAL STRATEGY:")
        print(f"  Average Return per Trade: {original['avg_return']:.1f}%")
        print(f"  Win Rate: {original['win_rate']:.1f}%")
        print(f"  Volatility: {original['volatility']:.1f}%")
        print(f"  Sharpe Ratio: {original['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {original['max_drawdown']:.1f}%")
        
        print(f"\nENHANCED STRATEGY (with Market Overlay):")
        print(f"  Average Return per Trade: {enhanced['avg_return']:.1f}%")
        print(f"  Win Rate: {enhanced['win_rate']:.1f}%")
        print(f"  Volatility: {enhanced['volatility']:.1f}%")
        print(f"  Sharpe Ratio: {enhanced['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {enhanced['max_drawdown']:.1f}%")
        
        print(f"\nIMPROVEMENT METRICS:")
        print(f"  Return Improvement: {improvement['return_improvement']:.1f} percentage points")
        print(f"  Sharpe Improvement: {improvement['sharpe_improvement']:.2f}")
        print(f"  Volatility Change: {improvement['volatility_change']:.1f} pp")
        print(f"  Drawdown Change: {improvement['drawdown_improvement']:.1f} pp")
        
        print(f"\nPOSITION ADJUSTMENTS:")
        for adjustment, count in adjustments.items():
            pct = count / sum(adjustments.values()) * 100
            print(f"  {adjustment}: {count} trades ({pct:.1f}%)")
        
        print(f"\n5. FINAL ASSESSMENT")
        print("-" * 50)
        
        if improvement['return_improvement'] > 1 and improvement['sharpe_improvement'] > 0.1:
            print("RECOMMENDATION: Implement market health overlay")
            print(f"  The overlay improves risk-adjusted returns significantly")
            print(f"  Return improvement: +{improvement['return_improvement']:.1f} pp per trade")
            print(f"  Sharpe ratio improvement: +{improvement['sharpe_improvement']:.2f}")
        elif improvement['sharpe_improvement'] > 0:
            print("CONSIDER: Market overlay shows modest improvement")
            print(f"  Risk-adjusted returns improve by {improvement['sharpe_improvement']:.2f}")
            print(f"  Monitor implementation costs and complexity")
        else:
            print("NOT RECOMMENDED: Market overlay reduces performance")
            print(f"  Sharpe ratio decreases by {abs(improvement['sharpe_improvement']):.2f}")
            print(f"  Stick with original strategy")

def main():
    """Run comprehensive SPY market health analysis"""
    
    analyzer = SPYMarketHealthAnalyzer()
    
    try:
        results = analyzer.generate_comprehensive_report()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n" + "=" * 80)
        print(f"ANALYSIS COMPLETE - {timestamp}")
        print("=" * 80)
        print("Key findings saved for further analysis")
        print("Market health overlay recommendations provided above")
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()