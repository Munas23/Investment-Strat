"""
Mark Minervini Trading Strategies Implementation
Based on SEPA (Specific Entry Point Analysis) and Trend Template methodology

Minervini is a 2-time US Investing Champion (1997, 2021) with exceptional returns
His methodology focuses on superperformance stocks with precise entry/exit points
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class MinerviniStrategies:
    """Implementation of Mark Minervini's proven trading strategies"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        
        # Minervini's specific strategies
        self.strategies = {
            1: {"name": "Trend Template", "method": "trend_template"},
            2: {"name": "SEPA Breakout", "method": "sepa_breakout"},
            3: {"name": "SEPA Pullback", "method": "sepa_pullback"},
            4: {"name": "Combined Minervini", "method": "combined_minervini"}
        }
        
        # Minervini's risk management rules
        self.max_risk_per_trade = 0.07  # 7% max loss per trade (his typical stop)
        self.max_position_size = 0.10   # 10% max position size
        self.rs_rating_min = 70         # Minimum RS rating (relative strength)
        
    def get_historical_data_10_year(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get 10+ years of historical data"""
        try:
            end_date = datetime.now()
            start_date = datetime(2014, 1, 1)
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty or len(data) < 2520:
                return None
            
            data.columns = [col.lower() for col in data.columns]
            return data
            
        except Exception as e:
            print(f"  Error getting data for {symbol}: {e}")
            return None
    
    def calculate_minervini_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators specific to Minervini's methods"""
        df = data.copy()
        
        # Key moving averages (Minervini's trend template)
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_150'] = df['close'].rolling(150).mean()
        df['ma_200'] = df['close'].rolling(200).mean()
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_21'] = df['close'].rolling(21).mean()
        
        # 52-week high/low tracking
        df['high_52w'] = df['high'].rolling(252).max()
        df['low_52w'] = df['low'].rolling(252).min()
        
        # Distance from 52-week high and low
        df['distance_from_52w_high'] = ((df['close'] / df['high_52w']) - 1) * 100
        df['distance_from_52w_low'] = ((df['close'] / df['low_52w']) - 1) * 100
        
        # Price performance for relative strength calculation
        df['perf_4w'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        df['perf_13w'] = ((df['close'] / df['close'].shift(65)) - 1) * 100
        df['perf_26w'] = ((df['close'] / df['close'].shift(130)) - 1) * 100
        df['perf_52w'] = ((df['close'] / df['close'].shift(252)) - 1) * 100
        
        # Volume analysis
        df['volume_avg_50'] = df['volume'].rolling(50).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg_50']
        
        # Trend strength (MA slopes)
        df['ma_50_slope'] = ((df['ma_50'] / df['ma_50'].shift(10)) - 1) * 100
        df['ma_150_slope'] = ((df['ma_150'] / df['ma_150'].shift(10)) - 1) * 100
        df['ma_200_slope'] = ((df['ma_200'] / df['ma_200'].shift(10)) - 1) * 100
        
        # Volatility for entry timing
        df['atr_14'] = self._calculate_atr(df, 14)
        
        # Relative strength approximation (simplified)
        # In practice, this would be calculated against S&P 500
        df['rs_rating'] = self._calculate_rs_rating(df)
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(period).mean()
    
    def _calculate_rs_rating(self, df: pd.DataFrame) -> pd.Series:
        """
        Simplified RS Rating calculation
        In practice, this would compare to S&P 500 performance
        Here we use percentile ranking of price performance
        """
        perf_52w = df['perf_52w']
        
        # Create rolling percentile ranking (simplified RS rating)
        rs_rating = pd.Series(index=df.index, dtype=float)
        
        for i in range(252, len(df)):
            current_perf = perf_52w.iloc[i]
            if pd.isna(current_perf):
                rs_rating.iloc[i] = 50
            else:
                # Simple approximation: if stock is up more than market average
                if current_perf > 15:  # Arbitrary threshold for strong performance
                    rs_rating.iloc[i] = 85
                elif current_perf > 5:
                    rs_rating.iloc[i] = 70
                elif current_perf > -5:
                    rs_rating.iloc[i] = 50
                else:
                    rs_rating.iloc[i] = 30
        
        return rs_rating
    
    def trend_template(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 1: Minervini's Trend Template
        
        Criteria:
        1. Price above 150 and 200 MA
        2. Current price above 50 MA
        3. 50 MA > 150 MA > 200 MA
        4. Current price within 25% of 52-week high
        5. Current price > 30% above 52-week low
        6. RS Rating > 70
        """
        df = self.calculate_minervini_indicators(data)
        
        signals = pd.Series(False, index=df.index)
        
        for i in range(252, len(df)):  # Need 252 days for all indicators
            current_idx = df.index[i]
            
            # Get current values
            price = df.loc[current_idx, 'close']
            ma_50 = df.loc[current_idx, 'ma_50']
            ma_150 = df.loc[current_idx, 'ma_150']
            ma_200 = df.loc[current_idx, 'ma_200']
            distance_from_high = df.loc[current_idx, 'distance_from_52w_high']
            distance_from_low = df.loc[current_idx, 'distance_from_52w_low']
            rs_rating = df.loc[current_idx, 'rs_rating']
            
            # Check all conditions
            if (pd.isna(price) or pd.isna(ma_50) or pd.isna(ma_150) or 
                pd.isna(ma_200) or pd.isna(distance_from_high) or 
                pd.isna(distance_from_low) or pd.isna(rs_rating)):
                continue
            
            # Trend Template Conditions
            condition_1 = price > ma_150 and price > ma_200  # Price above 150 and 200 MA
            condition_2 = price > ma_50  # Price above 50 MA
            condition_3 = ma_50 > ma_150 and ma_150 > ma_200  # MA alignment
            condition_4 = distance_from_high > -25  # Within 25% of 52-week high
            condition_5 = distance_from_low > 30  # More than 30% above 52-week low
            condition_6 = rs_rating > self.rs_rating_min  # Strong relative strength
            
            if (condition_1 and condition_2 and condition_3 and 
                condition_4 and condition_5 and condition_6):
                signals[current_idx] = True
        
        return self._simulate_minervini_strategy(df, signals, "Trend Template")
    
    def sepa_breakout(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 2: SEPA Breakout Method
        
        Criteria:
        - Stock passes trend template first
        - Breakout from consolidation/base
        - Volume confirmation
        - Tight stop loss below breakout level
        """
        df = self.calculate_minervini_indicators(data)
        
        signals = pd.Series(False, index=df.index)
        
        for i in range(252, len(df)):
            current_idx = df.index[i]
            
            # First check trend template (simplified)
            price = df.loc[current_idx, 'close']
            ma_50 = df.loc[current_idx, 'ma_50']
            ma_150 = df.loc[current_idx, 'ma_150']
            ma_200 = df.loc[current_idx, 'ma_200']
            
            if (pd.isna(price) or pd.isna(ma_50) or pd.isna(ma_150) or pd.isna(ma_200)):
                continue
            
            # Basic trend template check
            trend_template_ok = (price > ma_150 and price > ma_200 and 
                               price > ma_50 and ma_50 > ma_150)
            
            if not trend_template_ok:
                continue
            
            # Look for breakout pattern
            # Check for consolidation in past 4-8 weeks
            lookback_period = 30  # ~6 weeks
            if i < lookback_period:
                continue
            
            recent_data = df.iloc[i-lookback_period:i]
            high_of_base = recent_data['high'].max()
            
            # Breakout condition: current price breaking above recent high
            is_breakout = price > high_of_base * 1.02  # 2% above base high
            
            # Volume confirmation
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            volume_confirmation = not pd.isna(volume_ratio) and volume_ratio > 1.5
            
            # Distance from 52-week high (not too extended)
            distance_from_high = df.loc[current_idx, 'distance_from_52w_high']
            not_extended = not pd.isna(distance_from_high) and distance_from_high > -15
            
            if is_breakout and volume_confirmation and not_extended:
                signals[current_idx] = True
        
        return self._simulate_minervini_strategy(df, signals, "SEPA Breakout")
    
    def sepa_pullback(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 3: SEPA Pullback Method
        
        Criteria:
        - Stock in strong uptrend (trend template)
        - Pullback to support (10-21 MA)
        - Low volume on pullback
        - Bounce with volume
        """
        df = self.calculate_minervini_indicators(data)
        
        signals = pd.Series(False, index=df.index)
        
        for i in range(252, len(df)):
            current_idx = df.index[i]
            
            # Check trend template first
            price = df.loc[current_idx, 'close']
            ma_10 = df.loc[current_idx, 'ma_10']
            ma_21 = df.loc[current_idx, 'ma_21']
            ma_50 = df.loc[current_idx, 'ma_50']
            ma_150 = df.loc[current_idx, 'ma_150']
            
            if (pd.isna(price) or pd.isna(ma_10) or pd.isna(ma_21) or 
                pd.isna(ma_50) or pd.isna(ma_150)):
                continue
            
            # Strong uptrend required
            strong_uptrend = (price > ma_150 and ma_10 > ma_21 and 
                            ma_21 > ma_50 and ma_50 > ma_150)
            
            if not strong_uptrend:
                continue
            
            # Look for pullback to moving average support
            near_ma_support = (abs(price - ma_21) / ma_21 < 0.03 or  # Within 3% of 21 MA
                             abs(price - ma_10) / ma_10 < 0.02)  # Within 2% of 10 MA
            
            # Check if price is bouncing (today's close > yesterday's close)
            if i > 0:
                prev_price = df.iloc[i-1]['close']
                bouncing = price > prev_price * 1.01  # 1% bounce
            else:
                bouncing = False
            
            # Volume confirmation on bounce
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            volume_confirmation = not pd.isna(volume_ratio) and volume_ratio > 1.2
            
            if near_ma_support and bouncing and volume_confirmation:
                signals[current_idx] = True
        
        return self._simulate_minervini_strategy(df, signals, "SEPA Pullback")
    
    def combined_minervini(self, data: pd.DataFrame) -> Dict:
        """
        Strategy 4: Combined Minervini approach
        Uses all three methods with broader criteria
        """
        df = self.calculate_minervini_indicators(data)
        
        # Get signals from all strategies
        template_signals = pd.Series(False, index=df.index)
        breakout_signals = pd.Series(False, index=df.index)
        pullback_signals = pd.Series(False, index=df.index)
        
        for i in range(252, len(df)):
            current_idx = df.index[i]
            
            # Get current values
            price = df.loc[current_idx, 'close']
            ma_50 = df.loc[current_idx, 'ma_50']
            ma_150 = df.loc[current_idx, 'ma_150']
            ma_200 = df.loc[current_idx, 'ma_200']
            
            if (pd.isna(price) or pd.isna(ma_50) or pd.isna(ma_150) or pd.isna(ma_200)):
                continue
            
            # Basic trend template (simplified)
            basic_trend = (price > ma_150 and price > ma_200 and price > ma_50)
            
            if not basic_trend:
                continue
            
            # Template signal (stricter)
            distance_from_high = df.loc[current_idx, 'distance_from_52w_high']
            rs_rating = df.loc[current_idx, 'rs_rating']
            
            if (not pd.isna(distance_from_high) and distance_from_high > -20 and
                not pd.isna(rs_rating) and rs_rating > 60):
                template_signals[current_idx] = True
            
            # Breakout signal
            volume_ratio = df.loc[current_idx, 'volume_ratio']
            if not pd.isna(volume_ratio) and volume_ratio > 1.3:
                breakout_signals[current_idx] = True
            
            # Pullback signal
            ma_21 = df.loc[current_idx, 'ma_21']
            if not pd.isna(ma_21) and price > ma_21 * 0.98:  # Near 21 MA
                pullback_signals[current_idx] = True
        
        # Combine signals (any method triggers entry)
        combined_signals = template_signals | breakout_signals | pullback_signals
        
        return self._simulate_minervini_strategy(df, combined_signals, "Combined Minervini")
    
    def _simulate_minervini_strategy(self, df: pd.DataFrame, signals: pd.Series, strategy_name: str) -> Dict:
        """
        Simulate Minervini's specific trading approach:
        - Position size: 5-10% of account
        - Stop loss: 7-8% below entry
        - Profit taking: 20-25% gains
        - Trailing stop: Raise to breakeven after 10% gain
        """
        cash = self.initial_capital
        positions = []
        trades = []
        
        for i, (date, signal) in enumerate(signals.items()):
            if i < 252:  # Skip warmup
                continue
                
            current_price = df.loc[date, 'close']
            
            # Exit conditions for existing positions
            for pos in positions[:]:
                entry_price = pos['entry_price']
                shares = pos['shares']
                days_held = (date - pos['entry_date']).days
                
                # Calculate current P&L
                current_pnl = (current_price / entry_price - 1) * 100
                
                # Exit condition 1: Stop loss (7% below entry)
                if current_pnl < -7:
                    cash += shares * current_price
                    
                    trades.append({
                        'entry_date': pos['entry_date'],
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'return_pct': current_pnl,
                        'hold_days': days_held,
                        'exit_reason': 'Stop loss'
                    })
                    
                    positions.remove(pos)
                    continue
                
                # Exit condition 2: Profit target (25% gain)
                elif current_pnl > 25:
                    cash += shares * current_price
                    
                    trades.append({
                        'entry_date': pos['entry_date'],
                        'exit_date': date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'shares': shares,
                        'return_pct': current_pnl,
                        'hold_days': days_held,
                        'exit_reason': 'Profit target'
                    })
                    
                    positions.remove(pos)
                    continue
                
                # Exit condition 3: Trailing stop (below 21 MA after 10% gain)
                elif current_pnl > 10:
                    ma_21 = df.loc[date, 'ma_21']
                    if not pd.isna(ma_21) and current_price < ma_21 * 0.95:  # 5% below 21 MA
                        cash += shares * current_price
                        
                        trades.append({
                            'entry_date': pos['entry_date'],
                            'exit_date': date,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'shares': shares,
                            'return_pct': current_pnl,
                            'hold_days': days_held,
                            'exit_reason': 'Trailing stop'
                        })
                        
                        positions.remove(pos)
                        continue
            
            # Entry logic
            if signal and len(positions) < 8:  # Max 8 positions (concentration)
                # Minervini position sizing: 5-10% of account
                position_value = cash * 0.08  # 8% position size
                shares_to_buy = int(position_value / current_price)
                
                if shares_to_buy > 0 and cash >= shares_to_buy * current_price:
                    cash -= shares_to_buy * current_price
                    
                    positions.append({
                        'entry_date': date,
                        'entry_price': current_price,
                        'shares': shares_to_buy
                    })
        
        # Close remaining positions
        if positions:
            final_price = df['close'].iloc[-1]
            for pos in positions:
                cash += pos['shares'] * final_price
                days_held = (df.index[-1] - pos['entry_date']).days
                exit_return = (final_price / pos['entry_price'] - 1) * 100
                
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
    
    def test_minervini_strategies(self, symbols: List[str] = None) -> Dict:
        """Test all Minervini strategies over 10 years"""
        if symbols is None:
            # Focus on growth stocks that fit Minervini's style
            symbols = [
                # Large Cap Tech
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'NVDA', 'TSLA',
                # Growth stocks
                'CRM', 'ADBE', 'NOW', 'SHOP',
                # Traditional for comparison
                'JPM', 'JNJ', 'PG', 'KO', 'WMT', 'DIS'
            ]
        
        print("MARK MINERVINI STRATEGY TESTING (10-YEAR)")
        print("=" * 50)
        print("Testing SEPA methodology and Trend Template")
        print("2-time US Investing Champion (1997, 2021)")
        print()
        
        all_results = []
        buy_hold_returns = {}
        
        # Get data and calculate buy-hold returns
        print("Loading data and calculating buy-hold returns...")
        valid_symbols = []
        
        for symbol in symbols:
            print(f"  {symbol}: ", end="")
            data = self.get_historical_data_10_year(symbol)
            
            if data is not None:
                # Calculate buy-hold return
                start_price = data['close'].iloc[252]  # After warmup
                end_price = data['close'].iloc[-1]
                bh_return = (end_price / start_price - 1) * 100
                buy_hold_returns[symbol] = bh_return
                valid_symbols.append(symbol)
                print(f"Buy-Hold: {bh_return:.1f}%")
                
                # Test all strategies on this symbol
                for strategy_id, strategy_info in self.strategies.items():
                    method_name = strategy_info["method"]
                    strategy_name = strategy_info["name"]
                    
                    try:
                        if hasattr(self, method_name):
                            result = getattr(self, method_name)(data)
                            result['symbol'] = symbol
                            result['strategy_id'] = strategy_id
                            result['strategy_name'] = strategy_name
                            result['buy_hold_return'] = bh_return
                            result['excess_return'] = result['total_return'] - bh_return
                            all_results.append(result)
                    except Exception as e:
                        print(f"Error in {strategy_name} for {symbol}: {str(e)[:30]}...")
            else:
                print("No data")
        
        return self.analyze_minervini_results(all_results, buy_hold_returns)
    
    def analyze_minervini_results(self, results: List[Dict], buy_hold_returns: Dict) -> Dict:
        """Analyze Minervini strategy results"""
        print(f"\n" + "=" * 70)
        print("MARK MINERVINI STRATEGY RESULTS (10-YEAR)")
        print("=" * 70)
        
        # Group by strategy
        strategy_summary = {}
        for result in results:
            strategy_name = result['strategy_name']
            
            if strategy_name not in strategy_summary:
                strategy_summary[strategy_name] = {'results': []}
            
            strategy_summary[strategy_name]['results'].append(result)
        
        # Calculate summary statistics
        for strategy_name, summary in strategy_summary.items():
            results_list = summary['results']
            
            if not results_list:
                continue
                
            returns = [r['total_return'] for r in results_list]
            excess_returns = [r['excess_return'] for r in results_list]
            trade_counts = [r['num_trades'] for r in results_list]
            win_rates = [r['win_rate'] for r in results_list]
            
            summary.update({
                'avg_return': np.mean(returns),
                'median_return': np.median(returns),
                'avg_excess_return': np.mean(excess_returns),
                'beat_buy_hold_pct': len([er for er in excess_returns if er > 0]) / len(excess_returns) * 100,
                'avg_trades': np.mean(trade_counts),
                'avg_win_rate': np.mean(win_rates),
                'consistency': len([r for r in returns if r > 0]) / len(returns) * 100,
                'num_tests': len(results_list)
            })
        
        # Sort by average return
        sorted_strategies = sorted(strategy_summary.items(), 
                                 key=lambda x: x[1]['avg_return'], reverse=True)
        
        # Print results
        print(f"{'Strategy':<20} {'Avg Return':<12} {'vs B&H':<10} {'Beat B&H':<10} {'Win Rate':<10} {'Trades':<8} {'Consistency':<12}")
        print("-" * 85)
        
        for strategy_name, summary in sorted_strategies:
            print(f"{strategy_name:<20} {summary['avg_return']:>10.1f}% "
                  f"{summary['avg_excess_return']:>8.1f}% "
                  f"{summary['beat_buy_hold_pct']:>8.1f}% "
                  f"{summary['avg_win_rate']:>8.1f}% "
                  f"{summary['avg_trades']:>6.1f} "
                  f"{summary['consistency']:>10.1f}%")
        
        # Compare with buy-hold
        bh_returns = list(buy_hold_returns.values())
        avg_buy_hold = np.mean(bh_returns)
        
        print(f"\n" + "=" * 70)
        print("MINERVINI vs BUY-AND-HOLD COMPARISON")
        print("=" * 70)
        print(f"Buy-and-Hold Average: {avg_buy_hold:.1f}%")
        
        if sorted_strategies:
            best_strategy = sorted_strategies[0]
            best_name = best_strategy[0]
            best_stats = best_strategy[1]
            
            print(f"Best Minervini Strategy: {best_name}")
            print(f"  Average Return: {best_stats['avg_return']:.1f}%")
            print(f"  Excess Return: {best_stats['avg_excess_return']:.1f}%")
            print(f"  Beat Buy-Hold: {best_stats['beat_buy_hold_pct']:.1f}% of time")
            
            if best_stats['avg_return'] > avg_buy_hold:
                print(f"\nWINNER: {best_name} beats Buy-and-Hold!")
            else:
                print(f"\nWINNER: Buy-and-Hold beats all Minervini strategies")
        
        return strategy_summary


def main():
    """Test Minervini strategies"""
    print("Testing Mark Minervini's Trading Strategies")
    print("SEPA (Specific Entry Point Analysis) and Trend Template")
    print("2-time US Investing Champion methodology")
    print()
    
    tester = MinerviniStrategies()
    
    try:
        results = tester.test_minervini_strategies()
        
        print(f"\n" + "=" * 70)
        print("COMPARISON WITH PREVIOUS RESULTS")
        print("=" * 70)
        print("Previous 10-Year Test Results:")
        print("  Buy-and-Hold: +3,102% average")
        print("  Qullamaggie Combined: +18%")
        print("  Traditional TA: Mostly negative")
        print()
        print("Minervini Results:")
        print("  See detailed results above")
        print()
        print("Key Question: Can Minervini's champion methods beat buy-and-hold?")
        
    except Exception as e:
        print(f"Testing error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()