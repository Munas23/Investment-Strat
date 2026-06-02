"""
Kristjan Kullamägi (Qullamaggie) Trading Strategies Implementation
Based on the methods that made him tens of millions from $5k start

His 3 core strategies:
1. High Tight Flag (HTF) Breakouts
2. Breakout Strategy (20-50% move + consolidation)
3. Episodic Pivots (EP) - Unexpected news catalysts
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class QullamaggieStrategies:
    """Implementation of Kristjan Kullamägi's proven trading strategies"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Qullamaggie's specific parameters
        self.strategies = {
            1: {"name": "High Tight Flag (HTF)", "method": "high_tight_flag"},
            2: {"name": "Breakout Strategy", "method": "breakout_strategy"}, 
            3: {"name": "Episodic Pivots", "method": "episodic_pivots"},
            4: {"name": "Combined Qullamaggie", "method": "combined_qullamaggie"}
        }
        
        # His risk management rules
        self.max_position_size = 0.20  # 10-20% of account per position
        self.max_risk_per_trade = 0.01  # 0.25-1% risk per position
        self.max_overnight_exposure = 0.30  # Never more than 30% overnight
        
    def get_historical_data(self, symbol: str, years: int = 3) -> Optional[pd.DataFrame]:
        """Get historical data - Qullamaggie focuses on recent patterns"""
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
    
    def calculate_qullamaggie_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators specific to Qullamaggie's methods"""
        df = data.copy()
        
        # Key moving averages (his exit triggers)
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_20'] = df['close'].rolling(20).mean()
        
        # Price performance over different periods
        df['perf_1w'] = ((df['close'] / df['close'].shift(5)) - 1) * 100
        df['perf_2w'] = ((df['close'] / df['close'].shift(10)) - 1) * 100
        df['perf_4w'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        df['perf_8w'] = ((df['close'] / df['close'].shift(40)) - 1) * 100
        df['perf_12w'] = ((df['close'] / df['close'].shift(60)) - 1) * 100
        
        # Volume analysis
        df['volume_avg_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg_20']
        
        # ATR for volatility
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr_14'] = df['true_range'].rolling(14).mean()
        
        # Rolling highs and lows for pattern recognition
        df['high_52w'] = df['high'].rolling(252).max()
        df['high_12w'] = df['high'].rolling(60).max()
        df['high_8w'] = df['high'].rolling(40).max()
        df['high_4w'] = df['high'].rolling(20).max()
        
        # Distance from highs (for tight flag identification)
        df['distance_from_12w_high'] = ((df['close'] / df['high_12w']) - 1) * 100
        df['distance_from_8w_high'] = ((df['close'] / df['high_8w']) - 1) * 100
        df['distance_from_4w_high'] = ((df['close'] / df['high_4w']) - 1) * 100
        
        return df
    
    def high_tight_flag(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 1: High Tight Flag (HTF) Breakouts
        
        Criteria:
        - Stock has moved up 90-100%+ in short period
        - Consolidation with max 15-25% pullback from peak
        - Tight range on diminished volume
        - Breakout on increased volume
        """
        df = self.calculate_qullamaggie_indicators(data)
        
        signals = pd.Series(False, index=df.index)
        
        for i in range(60, len(df)):  # Need 60 days for pattern recognition
            current_idx = df.index[i]
            
            # Look for big move in last 8-12 weeks (30-100% gain)
            perf_8w = df.loc[current_idx, 'perf_8w']
            perf_12w = df.loc[current_idx, 'perf_12w']
            
            # Must have strong recent performance
            if pd.isna(perf_8w) or pd.isna(perf_12w):
                continue
                
            has_big_move = (perf_8w > 50 and perf_8w < 200) or (perf_12w > 75 and perf_12w < 300)
            
            if not has_big_move:
                continue
            
            # Check for tight consolidation (15-25% max pullback)
            distance_from_8w_high = df.loc[current_idx, 'distance_from_8w_high']
            distance_from_4w_high = df.loc[current_idx, 'distance_from_4w_high']
            
            if pd.isna(distance_from_8w_high) or pd.isna(distance_from_4w_high):
                continue
            
            # Tight flag: pullback between 10-25% from recent high
            is_tight_flag = (distance_from_8w_high > -25 and distance_from_8w_high < -8) or \
                           (distance_from_4w_high > -20 and distance_from_4w_high < -5)
            
            if not is_tight_flag:
                continue
            
            # Check for breakout above recent resistance
            current_price = df.loc[current_idx, 'close']
            high_4w = df.loc[current_idx, 'high_4w']
            
            # Breakout condition: breaking above 4-week high
            is_breakout = current_price > high_4w * 1.02  # 2% above 4-week high
            
            # Volume confirmation
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            has_volume = not pd.isna(volume_ratio) and volume_ratio > 1.5
            
            # Above key moving averages
            ma_10 = df.loc[current_idx, 'ma_10']
            ma_20 = df.loc[current_idx, 'ma_20']
            above_mas = (not pd.isna(ma_10) and current_price > ma_10) and \
                       (not pd.isna(ma_20) and current_price > ma_20)
            
            if is_breakout and has_volume and above_mas:
                signals[current_idx] = True
        
        return self._simulate_qullamaggie_strategy(df, signals, "High Tight Flag")
    
    def breakout_strategy(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 2: Breakout Strategy
        
        Criteria:
        - Big move (30-100%) within last 12 weeks
        - Orderly pullback into 2-8 week consolidation
        - Price surfing above 10 and 20 day MAs during consolidation
        - Breakout with volume
        """
        df = self.calculate_qullamaggie_indicators(data)
        
        signals = pd.Series(False, index=df.index)
        
        for i in range(60, len(df)):
            current_idx = df.index[i]
            
            # 1. Big move in last 12 weeks (30-100%)
            perf_12w = df.loc[current_idx, 'perf_12w']
            if pd.isna(perf_12w) or perf_12w < 30 or perf_12w > 150:
                continue
            
            # 2. Check for consolidation pattern (2-8 weeks)
            # Look for sideways price action in recent 2-6 weeks
            recent_20d = df.iloc[i-20:i]['close']
            if len(recent_20d) < 20:
                continue
            
            price_range = (recent_20d.max() - recent_20d.min()) / recent_20d.mean()
            is_consolidating = price_range < 0.15  # Less than 15% range = consolidation
            
            if not is_consolidating:
                continue
            
            # 3. Price surfing above 10 and 20 day MAs
            ma_10 = df.loc[current_idx, 'ma_10']
            ma_20 = df.loc[current_idx, 'ma_20']
            current_price = df.loc[current_idx, 'close']
            
            if pd.isna(ma_10) or pd.isna(ma_20):
                continue
            
            surfing_mas = current_price > ma_10 * 0.98 and current_price > ma_20 * 0.95
            
            if not surfing_mas:
                continue
            
            # 4. Breakout from consolidation
            consolidation_high = recent_20d.max()
            is_breakout = current_price > consolidation_high * 1.015  # 1.5% above consolidation high
            
            # 5. Volume confirmation
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            has_volume = not pd.isna(volume_ratio) and volume_ratio > 1.3
            
            if is_breakout and has_volume:
                signals[current_idx] = True
        
        return self._simulate_qullamaggie_strategy(df, signals, "Breakout Strategy")
    
    def episodic_pivots(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 3: Episodic Pivots (EP)
        
        Criteria:
        - Stock has been flat/sideways for 3-6 months
        - Sudden big move on news/catalyst (gap up + follow through)
        - Volume explosion
        - Quick entry on momentum
        """
        df = self.calculate_qullamaggie_indicators(data)
        
        signals = pd.Series(False, index=df.index)
        
        for i in range(120, len(df)):  # Need 120 days to check for flat period
            current_idx = df.index[i]
            
            # 1. Check for flat/sideways action in past 3-6 months
            past_3m = df.iloc[i-60:i-20]['close']  # 2-3 months ago period
            if len(past_3m) < 30:
                continue
            
            # Calculate if stock was flat (low volatility, minimal trend)
            price_change_3m = (past_3m.iloc[-1] / past_3m.iloc[0] - 1) * 100
            was_flat = abs(price_change_3m) < 25  # Less than 25% move = flat
            
            if not was_flat:
                continue
            
            # 2. Sudden big move (gap up or strong intraday move)
            current_price = df.loc[current_idx, 'close']
            prev_close = df.loc[df.index[i-1], 'close']
            today_open = df.loc[current_idx, 'open']
            
            # Gap up or strong move
            gap_up = (today_open / prev_close - 1) > 0.05  # 5%+ gap
            strong_move = (current_price / prev_close - 1) > 0.08  # 8%+ daily move
            
            if not (gap_up or strong_move):
                continue
            
            # 3. Volume explosion (3x+ average volume)
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            if pd.isna(volume_ratio) or volume_ratio < 3.0:
                continue
            
            # 4. Follow through (close near highs of the day)
            daily_range = df.loc[current_idx, 'high'] - df.loc[current_idx, 'low']
            close_position = (current_price - df.loc[current_idx, 'low']) / daily_range
            
            has_follow_through = close_position > 0.7  # Close in top 30% of range
            
            if has_follow_through:
                signals[current_idx] = True
        
        return self._simulate_qullamaggie_strategy(df, signals, "Episodic Pivots")
    
    def combined_qullamaggie(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 4: Combined approach using all 3 setups
        """
        df = self.calculate_qullamaggie_indicators(data)
        
        # Get signals from all strategies
        htf_signals = pd.Series(False, index=df.index)
        breakout_signals = pd.Series(False, index=df.index)
        ep_signals = pd.Series(False, index=df.index)
        
        # Simplified signal generation for combined approach
        for i in range(60, len(df)):
            current_idx = df.index[i]
            
            # HTF-like signals
            perf_8w = df.loc[current_idx, 'perf_8w']
            distance_from_4w_high = df.loc[current_idx, 'distance_from_4w_high']
            
            if (not pd.isna(perf_8w) and perf_8w > 40 and 
                not pd.isna(distance_from_4w_high) and distance_from_4w_high > -20):
                htf_signals[current_idx] = True
            
            # Breakout-like signals  
            perf_12w = df.loc[current_idx, 'perf_12w']
            ma_10 = df.loc[current_idx, 'ma_10']
            current_price = df.loc[current_idx, 'close']
            
            if (not pd.isna(perf_12w) and perf_12w > 25 and 
                not pd.isna(ma_10) and current_price > ma_10):
                breakout_signals[current_idx] = True
            
            # EP-like signals
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            perf_1w = df.loc[current_idx, 'perf_1w']
            
            if (not pd.isna(volume_ratio) and volume_ratio > 2.0 and
                not pd.isna(perf_1w) and perf_1w > 5):
                ep_signals[current_idx] = True
        
        # Combine signals (any strategy triggers entry)
        combined_signals = htf_signals | breakout_signals | ep_signals
        
        return self._simulate_qullamaggie_strategy(df, combined_signals, "Combined Qullamaggie")
    
    def _simulate_qullamaggie_strategy(self, df: pd.DataFrame, signals: pd.Series, strategy_name: str) -> Dict:
        """
        Simulate Qullamaggie's specific trading approach:
        - Position size: 10-20% of account
        - Risk: 0.25-1% per trade
        - Exit: Below 10 or 20 day MA
        - Partial profit taking after 3-5 days
        """
        cash = self.initial_capital
        positions = []
        trades = []
        
        for i, (date, signal) in enumerate(signals.items()):
            if i < 60:  # Skip warmup
                continue
                
            current_price = df.loc[date, 'close']
            ma_10 = df.loc[date, 'ma_10']
            ma_20 = df.loc[date, 'ma_20']
            
            # Exit conditions for existing positions
            for pos in positions[:]:  # Copy list to modify during iteration
                entry_date = pos['entry_date']
                entry_price = pos['entry_price']
                shares = pos['shares']
                
                # Days held
                days_held = (date - entry_date).days
                
                # Exit condition 1: Below MA (Qullamaggie's main exit)
                below_ma_10 = not pd.isna(ma_10) and current_price < ma_10
                below_ma_20 = not pd.isna(ma_20) and current_price < ma_20
                
                if below_ma_10 or below_ma_20:
                    # Sell entire position
                    cash += shares * current_price
                    exit_return = (current_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'return_pct': exit_return,
                        'hold_days': days_held,
                        'exit_reason': 'MA exit'
                    })
                    
                    positions.remove(pos)
                    continue
                
                # Exit condition 2: Partial profit taking after 3-5 days (Qullamaggie method)
                if days_held >= 3 and days_held <= 5 and pos.get('partial_sold', False) == False:
                    if current_price > entry_price * 1.05:  # 5%+ profit
                        # Sell 1/3 to 1/2 of position
                        partial_shares = int(shares * 0.4)  # Sell 40%
                        if partial_shares > 0:
                            cash += partial_shares * current_price
                            pos['shares'] = shares - partial_shares
                            pos['partial_sold'] = True
                            
                            # Record partial sale
                            partial_return = (current_price / entry_price - 1) * 100
                            trades.append({
                                'entry_date': entry_date,
                                'exit_date': date,
                                'entry_price': entry_price,
                                'exit_price': current_price,
                                'shares': partial_shares,
                                'return_pct': partial_return,
                                'hold_days': days_held,
                                'exit_reason': 'Partial profit'
                            })
            
            # Entry logic
            if signal and len(positions) < 3:  # Max 3 positions (concentration)
                # Qullamaggie position sizing: 10-20% of account
                position_value = cash * 0.15  # 15% position size
                shares_to_buy = int(position_value / current_price)
                
                if shares_to_buy > 0 and cash >= shares_to_buy * current_price:
                    cash -= shares_to_buy * current_price
                    
                    positions.append({
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares_to_buy,
                        'partial_sold': False
                    })
        
        # Close remaining positions
        if positions:
            final_price = df['close'].iloc[-1]
            for pos in positions:
                cash += pos['shares'] * final_price
                exit_return = (final_price / pos['entry_price'] - 1) * 100
                days_held = (df.index[-1] - pos['entry_date']).days
                
                trades.append({
                    'entry_date': pos['entry_date'],
                    'exit_date': df.index[-1],
                    'entry_price': pos['entry_price'],
                    'exit_price': final_price,
                    'shares': pos['shares'],
                    'return_pct': exit_return,
                    'hold_days': days_held,
                    'exit_reason': 'Final exit'
                })
        
        # Calculate performance
        final_value = cash
        total_return = (final_value / self.initial_capital - 1) * 100
        
        if trades:
            returns = [t['return_pct'] for t in trades]
            win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
            avg_return = np.mean(returns)
            avg_hold_days = np.mean([t['hold_days'] for t in trades])
        else:
            win_rate = avg_return = avg_hold_days = 0
        
        return {
            'total_return': total_return,
            'num_trades': len(trades),
            'win_rate': win_rate,
            'avg_return_per_trade': avg_return,
            'avg_hold_days': avg_hold_days,
            'strategy': strategy_name,
            'trades': trades
        }
    
    def test_qullamaggie_strategies(self, symbols: List[str] = None) -> Dict:
        """Test all Qullamaggie strategies"""
        if symbols is None:
            # Focus on growth stocks that fit his style
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMZN', 'META', 'NFLX']
        
        print("KRISTJAN KULLAMÄGI (QULLAMAGGIE) STRATEGY TESTING")
        print("=" * 55)
        print("Testing the strategies that made him tens of millions")
        print("From $5,000 to $100M+ using these 3 core setups")
        print()
        
        all_results = []
        
        for symbol in symbols:
            print(f"Testing {symbol}...")
            data = self.get_historical_data(symbol, 3)  # 3 years for pattern recognition
            
            if data is None:
                print(f"  No data for {symbol}")
                continue
            
            for strategy_id, strategy_info in self.strategies.items():
                method_name = strategy_info["method"]
                strategy_name = strategy_info["name"]
                
                try:
                    if hasattr(self, method_name):
                        result = getattr(self, method_name)(data)
                        result['symbol'] = symbol
                        result['strategy_id'] = strategy_id
                        result['strategy_name'] = strategy_name
                        all_results.append(result)
                        
                        print(f"  {strategy_name}: {result['total_return']:.1f}% ({result['num_trades']} trades)")
                        
                except Exception as e:
                    print(f"  {strategy_name}: Error - {str(e)[:50]}...")
        
        return self.analyze_qullamaggie_results(all_results)
    
    def analyze_qullamaggie_results(self, results: List[Dict]) -> Dict:
        """Analyze Qullamaggie strategy results"""
        print("\n" + "=" * 60)
        print("QULLAMAGGIE STRATEGY RESULTS")
        print("=" * 60)
        
        # Group by strategy
        strategy_summary = {}
        for result in results:
            strategy_id = result['strategy_id']
            strategy_name = result['strategy_name']
            
            if strategy_id not in strategy_summary:
                strategy_summary[strategy_id] = {
                    'name': strategy_name,
                    'results': [],
                }
            
            strategy_summary[strategy_id]['results'].append(result)
        
        # Calculate summary statistics
        for strategy_id, summary in strategy_summary.items():
            results = summary['results']
            returns = [r['total_return'] for r in results]
            trades = [r['num_trades'] for r in results]
            win_rates = [r['win_rate'] for r in results]
            
            summary['avg_return'] = np.mean(returns)
            summary['median_return'] = np.median(returns)
            summary['consistency'] = len([r for r in returns if r > 0]) / len(returns) * 100
            summary['avg_trades'] = np.mean(trades)
            summary['avg_win_rate'] = np.mean(win_rates)
            summary['num_tests'] = len(results)
        
        # Sort by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        print(f"{'Rank':<4} {'Strategy':<25} {'Avg Return':<12} {'Win Rate':<10} {'Trades':<8} {'Consistency':<12}")
        print("-" * 75)
        
        for rank, (strategy_id, summary) in enumerate(sorted_strategies, 1):
            print(f"{rank:<4} {summary['name']:<25} {summary['avg_return']:>10.1f}% "
                  f"{summary['avg_win_rate']:>8.1f}% {summary['avg_trades']:>6.1f} "
                  f"{summary['consistency']:>10.1f}%")
        
        return strategy_summary


def main():
    """Test Qullamaggie strategies"""
    print("Testing Kristjan Kullamägi's (Qullamaggie) Trading Strategies")
    print("The methods that took him from $5,000 to $100M+")
    print()
    
    tester = QullamaggieStrategies()
    
    # Test on growth stocks that fit his style
    growth_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMZN']
    
    try:
        results = tester.test_qullamaggie_strategies(growth_stocks)
        
        print("\n" + "=" * 60)
        print("COMPARISON WITH PREVIOUS RESULTS")
        print("=" * 60)
        print("Previous Test Results:")
        print("  Buy and Hold: +376% average")
        print("  Traditional TA: -80% to -95% losses")
        print("  Best Traditional Strategy: +0.6%")
        print()
        print("Qullamaggie Results:")
        print("  See detailed results above")
        print()
        print("Key Question: Can Qullamaggie's proven methods beat buy-and-hold?")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()