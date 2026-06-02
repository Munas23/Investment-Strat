"""
Alternative Strategy Tests - Based on shocking results from traditional TA
Testing approaches that might actually work
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class AlternativeStrategies:
    """Test alternative approaches after traditional TA failed spectacularly"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Test these alternative approaches
        self.alternative_strategies = {
            1: {"name": "Buy and Hold", "method": "buy_and_hold"},
            2: {"name": "Mean Reversion (Oversold Quality)", "method": "mean_reversion_quality"},
            3: {"name": "Long-term Trend (200MA + 12mo momentum)", "method": "long_term_trend"},
            4: {"name": "Anti-Momentum (Buy Weakness)", "method": "anti_momentum"},
            5: {"name": "Dollar Cost Averaging", "method": "dollar_cost_averaging"},
            6: {"name": "Volatility Timing (Buy Low Vol)", "method": "volatility_timing"},
            7: {"name": "Minimal Technical (Only Major Levels)", "method": "minimal_technical"},
            8: {"name": "Market Structure (Support/Resistance)", "method": "market_structure"}
        }
        
    def get_historical_data(self, symbol: str, years: int = 5) -> Optional[pd.DataFrame]:
        """Get historical data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365 + 100)
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 252:
                return None
            
            data.columns = [col.lower() for col in data.columns]
            return data
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators for alternative strategies"""
        df = data.copy()
        
        # Long-term moving averages
        df['sma_200'] = df['close'].rolling(200).mean()
        df['sma_50'] = df['close'].rolling(50).mean()
        
        # Price metrics
        df['return_1m'] = df['close'].pct_change(21)  # 1 month return
        df['return_3m'] = df['close'].pct_change(63)  # 3 month return
        df['return_12m'] = df['close'].pct_change(252)  # 12 month return
        
        # Volatility (20-day rolling)
        df['volatility'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
        
        # Distance from highs/lows
        df['distance_from_52w_high'] = (df['close'] / df['close'].rolling(252).max() - 1) * 100
        df['distance_from_52w_low'] = (df['close'] / df['close'].rolling(252).min() - 1) * 100
        
        # Volume analysis
        df['volume_avg'] = df['volume'].rolling(50).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg']
        
        return df
    
    def buy_and_hold(self, data: pd.DataFrame) -> Dict:
        """Strategy 1: Simple buy and hold"""
        start_price = data['close'].iloc[200]  # Skip warmup period
        end_price = data['close'].iloc[-1]
        
        total_return = (end_price / start_price - 1) * 100
        
        return {
            'total_return': total_return,
            'num_trades': 1,
            'win_rate': 100.0 if total_return > 0 else 0.0,
            'max_drawdown': self._calculate_max_drawdown(data['close'].iloc[200:]),
            'strategy': 'Buy and Hold'
        }
    
    def mean_reversion_quality(self, data: pd.DataFrame) -> Dict:
        """Strategy 2: Buy when stock is oversold but fundamentally strong"""
        df = self.calculate_indicators(data)
        
        # Entry: Stock down 20%+ from 52-week high + low volatility
        oversold = df['distance_from_52w_high'] < -20
        low_vol = df['volatility'] < df['volatility'].rolling(100).quantile(0.3)
        
        signals = oversold & low_vol
        
        return self._simulate_strategy(df, signals, "Mean Reversion")
    
    def long_term_trend(self, data: pd.DataFrame) -> Dict:
        """Strategy 3: Long-term trend following (very different from failed short-term)"""
        df = self.calculate_indicators(data)
        
        # Entry: Price above 200MA + positive 12-month momentum
        above_200ma = df['close'] > df['sma_200']
        positive_12m = df['return_12m'] > 0.1  # 10%+ over 12 months
        
        signals = above_200ma & positive_12m
        
        return self._simulate_strategy(df, signals, "Long-term Trend")
    
    def anti_momentum(self, data: pd.DataFrame) -> Dict:
        """Strategy 4: Buy weakness (opposite of failed momentum strategies)"""
        df = self.calculate_indicators(data)
        
        # Entry: Recent weakness + near 52-week lows
        recent_weakness = df['return_1m'] < -0.1  # Down 10% in month
        near_lows = df['distance_from_52w_low'] < 20  # Within 20% of 52w low
        
        signals = recent_weakness & near_lows
        
        return self._simulate_strategy(df, signals, "Anti-Momentum")
    
    def dollar_cost_averaging(self, data: pd.DataFrame) -> Dict:
        """Strategy 5: Regular purchases regardless of price"""
        df = data.iloc[200:].copy()  # Skip warmup
        
        # Buy every 21 days (monthly)
        buy_dates = df.index[::21]
        
        total_invested = 0
        total_shares = 0
        
        monthly_investment = 2000  # $2000 per month
        
        for date in buy_dates:
            if date in df.index:
                price = df.loc[date, 'close']
                shares_bought = monthly_investment / price
                total_shares += shares_bought
                total_invested += monthly_investment
        
        final_value = total_shares * df['close'].iloc[-1]
        total_return = (final_value / total_invested - 1) * 100
        
        return {
            'total_return': total_return,
            'num_trades': len(buy_dates),
            'win_rate': 100.0 if total_return > 0 else 0.0,
            'strategy': 'Dollar Cost Averaging'
        }
    
    def volatility_timing(self, data: pd.DataFrame) -> Dict:
        """Strategy 6: Buy during low volatility periods"""
        df = self.calculate_indicators(data)
        
        # Entry: Volatility in bottom 25% + not in downtrend
        low_vol = df['volatility'] < df['volatility'].rolling(100).quantile(0.25)
        not_downtrend = df['close'] > df['sma_50']
        
        signals = low_vol & not_downtrend
        
        return self._simulate_strategy(df, signals, "Volatility Timing")
    
    def minimal_technical(self, data: pd.DataFrame) -> Dict:
        """Strategy 7: Only major support/resistance levels"""
        df = self.calculate_indicators(data)
        
        # Entry: Bounce from major support (50% retracement level)
        high_52w = df['close'].rolling(252).max()
        low_52w = df['close'].rolling(252).min()
        mid_level = (high_52w + low_52w) / 2
        
        # Buy when price touches middle level from below
        at_support = np.abs(df['close'] - mid_level) / mid_level < 0.02
        coming_from_below = df['close'].shift(5) < mid_level * 0.98
        
        signals = at_support & coming_from_below
        
        return self._simulate_strategy(df, signals, "Minimal Technical")
    
    def market_structure(self, data: pd.DataFrame) -> Dict:
        """Strategy 8: Market structure based on actual support/resistance"""
        df = self.calculate_indicators(data)
        
        # Find actual support levels (local lows that held multiple times)
        local_lows = df['close'][(df['close'].shift(5) > df['close']) & 
                                (df['close'].shift(-5) > df['close'])]
        
        # Entry: Price near established support level
        signals = pd.Series(False, index=df.index)
        
        for idx in df.index[100:]:  # Skip early data
            current_price = df.loc[idx, 'close']
            
            # Check if current price is near any established support level
            for support_date in local_lows.index:
                if support_date < idx:
                    support_level = local_lows[support_date]
                    if abs(current_price - support_level) / support_level < 0.03:  # Within 3%
                        signals[idx] = True
                        break
        
        return self._simulate_strategy(df, signals, "Market Structure")
    
    def _simulate_strategy(self, df: pd.DataFrame, signals: pd.Series, strategy_name: str) -> Dict:
        """Simulate a strategy given buy signals"""
        cash = self.initial_capital
        shares = 0
        trades = []
        
        for i, (date, signal) in enumerate(signals.items()):
            if i < 200:  # Skip warmup period
                continue
                
            current_price = df.loc[date, 'close']
            
            # Exit logic: 15% stop loss OR 25% profit target (less aggressive than 8%)
            if shares > 0:
                if len(trades) > 0:
                    entry_price = trades[-1]['entry_price']
                    
                    # Stop loss (15%) or profit target (25%)
                    if current_price < entry_price * 0.85 or current_price > entry_price * 1.25:
                        # Sell
                        cash = shares * current_price
                        exit_return = (current_price / entry_price - 1) * 100
                        trades[-1]['exit_price'] = current_price
                        trades[-1]['exit_date'] = date
                        trades[-1]['return_pct'] = exit_return
                        shares = 0
                        continue
            
            # Entry logic
            if signal and shares == 0 and not pd.isna(current_price):
                # Use 25% of capital per trade (less aggressive than 100%)
                position_value = cash * 0.25
                shares_to_buy = int(position_value / current_price)
                
                if shares_to_buy > 0:
                    shares = shares_to_buy
                    cost = shares * current_price
                    cash -= cost
                    
                    trades.append({
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares,
                        'cost': cost,
                        'exit_price': None,
                        'exit_date': None,
                        'return_pct': None
                    })
        
        # Close final position
        if shares > 0 and len(trades) > 0 and trades[-1]['exit_price'] is None:
            final_price = df['close'].iloc[-1]
            cash = shares * final_price
            entry_price = trades[-1]['entry_price']
            exit_return = (final_price / entry_price - 1) * 100
            trades[-1]['exit_price'] = final_price
            trades[-1]['exit_date'] = df.index[-1]
            trades[-1]['return_pct'] = exit_return
        
        # Calculate metrics
        final_value = cash
        total_return = (final_value / self.initial_capital - 1) * 100
        
        completed_trades = [t for t in trades if t['return_pct'] is not None]
        
        if completed_trades:
            returns = [t['return_pct'] for t in completed_trades]
            win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
        else:
            win_rate = 0
        
        return {
            'total_return': total_return,
            'num_trades': len(completed_trades),
            'win_rate': win_rate,
            'strategy': strategy_name,
            'trades': completed_trades
        }
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = prices.expanding().max()
        drawdown = (prices / peak - 1) * 100
        return drawdown.min()
    
    def test_alternatives(self, symbols: List[str] = None) -> Dict:
        """Test alternative strategies"""
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
        
        print("ALTERNATIVE STRATEGY TESTING")
        print("=" * 40)
        print("Testing approaches that might actually work")
        print("(After traditional TA failed spectacularly)")
        print()
        
        all_results = []
        
        for symbol in symbols:
            print(f"Testing {symbol}...")
            data = self.get_historical_data(symbol, 5)
            
            if data is None:
                continue
            
            for strategy_id, strategy_info in self.alternative_strategies.items():
                method_name = strategy_info["method"]
                strategy_name = strategy_info["name"]
                
                try:
                    if hasattr(self, method_name):
                        result = getattr(self, method_name)(data)
                        result['symbol'] = symbol
                        result['strategy_id'] = strategy_id
                        result['strategy_name'] = strategy_name
                        all_results.append(result)
                        
                        print(f"  {strategy_name}: {result['total_return']:.1f}%")
                        
                except Exception as e:
                    print(f"  {strategy_name}: Error - {e}")
        
        return self.analyze_alternative_results(all_results)
    
    def analyze_alternative_results(self, results: List[Dict]) -> Dict:
        """Analyze alternative strategy results"""
        print("\n" + "=" * 50)
        print("ALTERNATIVE STRATEGY RESULTS")
        print("=" * 50)
        
        # Group by strategy
        strategy_summary = {}
        for result in results:
            strategy_id = result['strategy_id']
            strategy_name = result['strategy_name']
            
            if strategy_id not in strategy_summary:
                strategy_summary[strategy_id] = {
                    'name': strategy_name,
                    'results': [],
                    'avg_return': 0,
                    'consistency': 0
                }
            
            strategy_summary[strategy_id]['results'].append(result)
        
        # Calculate summary statistics
        for strategy_id, summary in strategy_summary.items():
            results = summary['results']
            returns = [r['total_return'] for r in results]
            
            summary['avg_return'] = np.mean(returns)
            summary['median_return'] = np.median(returns)
            summary['consistency'] = len([r for r in returns if r > 0]) / len(returns) * 100
            summary['num_tests'] = len(results)
        
        # Sort by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        print(f"{'Rank':<4} {'Strategy':<30} {'Avg Return':<12} {'Consistency':<12} {'Tests':<6}")
        print("-" * 70)
        
        for rank, (strategy_id, summary) in enumerate(sorted_strategies, 1):
            print(f"{rank:<4} {summary['name']:<30} {summary['avg_return']:>10.1f}% "
                  f"{summary['consistency']:>10.1f}% {summary['num_tests']:>4}")
        
        return strategy_summary


def main():
    """Test alternative strategies"""
    tester = AlternativeStrategies()
    
    # Test on fewer stocks for speed
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA']
    
    results = tester.test_alternatives(test_symbols)
    
    print("\n" + "=" * 50)
    print("COMPARISON WITH TRADITIONAL TA")
    print("=" * 50)
    print("Traditional TA Results (from comprehensive test):")
    print("  Best Strategy: Pullback Entry (+0.6%)")
    print("  Typical Strategy: -80% to -95% losses")
    print("  Golden Cross: -79.6%")
    print("  Fast MA Cross: -83.3%")
    print()
    print("Alternative Strategy Results:")
    print("  See results above ↑")
    print()
    print("Key Question: Do ANY of these beat buy-and-hold?")


if __name__ == "__main__":
    main()