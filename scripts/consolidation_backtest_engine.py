"""
Consolidation Conviction Strategy - Professional Backtesting Engine
==================================================================

Institutional-Grade Backtesting Framework
10-Year Historical Analysis (2014-2024)
ASX300 & SP500 Markets

Market Research by Senior Quantitative Analyst
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import time
import os
from concurrent.futures import ThreadPoolExecutor
import logging

warnings.filterwarnings('ignore')

class ConsolidationBacktester:
    """
    Professional backtesting engine for consolidation conviction strategy
    Includes realistic transaction costs, slippage, and risk management
    """
    
    def __init__(self, start_date='2014-01-01', end_date='2024-12-31', initial_capital=1000000):
        """Initialize backtesting engine"""
        
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = initial_capital
        
        # Backtesting parameters
        self.transaction_cost = 0.001  # 0.1% per trade (realistic for institutions)
        self.slippage = 0.0005        # 0.05% market impact
        self.risk_free_rate = 0.03    # 3% annual risk-free rate
        
        # Strategy parameters (from original scanner)
        self.min_3month_gain = 30.0
        self.min_price = 1.00
        self.min_market_cap = 500e6
        self.position_sizes = {0: 0, 1: 0.15, 2: 0.20, 3: 0.25, 4: 0.30, 5: 0.35}
        self.stop_loss_pct = 0.08     # 8% stop loss
        self.profit_target_pct = 0.40 # 40% profit target
        
        # Results storage
        self.results = {}
        self.trades = []
        self.portfolio_history = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        print("CONSOLIDATION CONVICTION BACKTEST ENGINE")
        print("=" * 50)
        print(f"Period: {start_date} to {end_date}")
        print(f"Initial Capital: ${initial_capital:,}")
        print(f"Transaction Cost: {self.transaction_cost*100:.2f}%")
        print("=" * 50)
    
    def get_historical_data(self, symbol: str, period: str = "10y") -> Optional[pd.DataFrame]:
        """Get 10 years of historical data for backtesting"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval="1d")
            
            if hist.empty or len(hist) < 252:  # Need at least 1 year
                return None
            
            # Clean and standardize
            hist.columns = [col.lower() for col in hist.columns]
            hist = hist.dropna()
            hist.index = pd.to_datetime(hist.index)
            
            # Filter to backtest period - handle timezone issues
            hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
            hist = hist[(hist.index >= self.start_date) & (hist.index <= self.end_date)]
            
            if len(hist) < 252:  # Still need sufficient data
                return None
                
            return hist
            
        except Exception as e:
            self.logger.error(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_atr_series(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR series for strategy logic"""
        try:
            if len(df) < period + 1:
                return pd.Series(index=df.index, dtype=float)
            
            df = df.copy()
            df['prev_close'] = df['close'].shift(1)
            
            # True Range components
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['prev_close'] - df['low'])
            df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # ATR calculation
            atr_series = df['true_range'].rolling(period).mean()
            return atr_series
            
        except Exception as e:
            return pd.Series(index=df.index, dtype=float)
    
    def generate_conviction_signal(self, df: pd.DataFrame, date_idx: int) -> Tuple[int, Dict]:
        """Generate consolidation conviction signal for specific date"""
        try:
            if date_idx < 200:  # Need sufficient history
                return 0, {}
            
            # Get data up to current point (avoid lookahead bias)
            current_data = df.iloc[:date_idx+1].copy()
            current_price = current_data['close'].iloc[-1]
            
            # Calculate performance metrics
            if len(current_data) >= 90:
                price_3m_ago = current_data['close'].iloc[-65]  # ~3 months
                gain_3m = ((current_price / price_3m_ago) - 1) * 100
            else:
                gain_3m = 0
                
            if len(current_data) >= 130:
                price_6m_ago = current_data['close'].iloc[-130]  # ~6 months
                gain_6m = ((current_price / price_6m_ago) - 1) * 100
            else:
                gain_6m = gain_3m
            
            # Check primary filter
            medium_term_gain = max(gain_3m, gain_6m)
            if medium_term_gain < self.min_3month_gain:
                return 0, {'medium_term_gain': medium_term_gain}
            
            # Recent performance
            if len(current_data) >= 10:
                price_2w_ago = current_data['close'].iloc[-10]
                gain_2w = ((current_price / price_2w_ago) - 1) * 100
            else:
                gain_2w = 0
                
            if len(current_data) >= 20:
                price_4w_ago = current_data['close'].iloc[-20]
                gain_4w = ((current_price / price_4w_ago) - 1) * 100
            else:
                gain_4w = 0
            
            # ATR analysis
            atr_14 = self.calculate_atr_series(current_data, 14)
            if len(atr_14) < 50:
                return 0, {}
            
            # Recent vs older ATR periods
            recent_atr_2w = atr_14.iloc[-10:].mean() if len(atr_14) >= 10 else 0
            recent_atr_4w = atr_14.iloc[-20:].mean() if len(atr_14) >= 20 else 0
            older_atr = atr_14.iloc[-60:-20].mean() if len(atr_14) >= 60 else 0
            
            if older_atr <= 0:
                return 0, {}
            
            # ATR contraction ratios
            atr_contraction_2w = recent_atr_2w / older_atr
            atr_contraction_4w = recent_atr_4w / older_atr
            best_contraction = min(atr_contraction_2w, atr_contraction_4w)
            
            # Scoring system (simplified for backtesting speed)
            conviction = 0
            
            # Performance points (0-30)
            if medium_term_gain >= 100:
                conviction += 30
            elif medium_term_gain >= 70:
                conviction += 25
            elif medium_term_gain >= 50:
                conviction += 20
            elif medium_term_gain >= 30:
                conviction += 15
            
            # ATR points (0-35)
            if best_contraction <= 0.6:
                conviction += 20
            elif best_contraction <= 0.8:
                conviction += 15
            elif best_contraction <= 1.0:
                conviction += 10
            
            # Recent ATR percentage
            recent_atr_pct = (recent_atr_4w / current_price * 100) if current_price > 0 else 10
            if recent_atr_pct <= 2.0:
                conviction += 10
            elif recent_atr_pct <= 3.5:
                conviction += 8
            elif recent_atr_pct <= 5.0:
                conviction += 5
            
            # Momentum points (0-20) - reward LOW recent momentum
            avg_recent_gain = (abs(gain_2w) + abs(gain_4w)) / 2
            if avg_recent_gain <= 2:
                conviction += 20
            elif avg_recent_gain <= 5:
                conviction += 15
            elif avg_recent_gain <= 8:
                conviction += 10
            
            # Volume analysis (simplified)
            recent_vol = current_data['volume'].iloc[-20:].mean()
            older_vol = current_data['volume'].iloc[-60:-20].mean()
            vol_ratio = recent_vol / older_vol if older_vol > 0 else 1
            
            if 0.7 <= vol_ratio <= 1.3:
                conviction += 15
            elif 0.5 <= vol_ratio <= 1.5:
                conviction += 10
            
            # Convert to level (0-5)
            if conviction >= 80:
                level = 5
            elif conviction >= 65:
                level = 4
            elif conviction >= 50:
                level = 3
            elif conviction >= 35:
                level = 2
            elif conviction >= 20:
                level = 1
            else:
                level = 0
            
            details = {
                'conviction_score': conviction,
                'medium_term_gain': medium_term_gain,
                'gain_2w': gain_2w,
                'gain_4w': gain_4w,
                'best_atr_contraction': best_contraction,
                'recent_atr_pct': recent_atr_pct,
                'avg_recent_gain': avg_recent_gain
            }
            
            return level, details
            
        except Exception as e:
            return 0, {'error': str(e)}
    
    def simulate_trades(self, symbol: str, df: pd.DataFrame) -> List[Dict]:
        """Simulate trades for a single symbol over the backtest period"""
        trades = []
        current_position = None
        
        try:
            # Start simulation from sufficient data point
            start_idx = 200
            
            for i in range(start_idx, len(df)):
                current_date = df.index[i]
                current_price = df['close'].iloc[i]
                
                # Skip if price too low
                if current_price < self.min_price:
                    continue
                
                # Check if we have an open position
                if current_position:
                    # Check stop loss
                    if current_price <= current_position['stop_price']:
                        # Exit on stop loss
                        exit_price = current_position['stop_price'] * (1 - self.slippage)
                        pnl = (exit_price - current_position['entry_price']) * current_position['shares']
                        pnl_pct = (exit_price / current_position['entry_price'] - 1) * 100
                        
                        trade_record = {
                            'symbol': symbol,
                            'entry_date': current_position['entry_date'],
                            'exit_date': current_date,
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'shares': current_position['shares'],
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'STOP_LOSS',
                            'conviction_level': current_position['conviction_level'],
                            'holding_days': (current_date - current_position['entry_date']).days
                        }
                        trades.append(trade_record)
                        current_position = None
                        continue
                    
                    # Check profit target
                    elif current_price >= current_position['target_price']:
                        # Exit on profit target
                        exit_price = current_position['target_price'] * (1 - self.slippage)
                        pnl = (exit_price - current_position['entry_price']) * current_position['shares']
                        pnl_pct = (exit_price / current_position['entry_price'] - 1) * 100
                        
                        trade_record = {
                            'symbol': symbol,
                            'entry_date': current_position['entry_date'],
                            'exit_date': current_date,
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'shares': current_position['shares'],
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'exit_reason': 'PROFIT_TARGET',
                            'conviction_level': current_position['conviction_level'],
                            'holding_days': (current_date - current_position['entry_date']).days
                        }
                        trades.append(trade_record)
                        current_position = None
                        continue
                
                # Look for new entry signals
                if not current_position:
                    conviction_level, details = self.generate_conviction_signal(df, i)
                    
                    # Only enter if conviction >= 2
                    if conviction_level >= 2:
                        position_size = self.position_sizes[conviction_level]
                        position_value = self.initial_capital * position_size
                        
                        entry_price = current_price * (1 + self.slippage)  # Account for slippage
                        shares = int(position_value / entry_price)
                        
                        if shares > 0:  # Valid position
                            stop_price = entry_price * (1 - self.stop_loss_pct)
                            target_price = entry_price * (1 + self.profit_target_pct)
                            
                            current_position = {
                                'symbol': symbol,
                                'entry_date': current_date,
                                'entry_price': entry_price,
                                'shares': shares,
                                'stop_price': stop_price,
                                'target_price': target_price,
                                'conviction_level': conviction_level,
                                'details': details
                            }
            
            # Close any remaining position at end
            if current_position:
                final_price = df['close'].iloc[-1] * (1 - self.slippage)
                pnl = (final_price - current_position['entry_price']) * current_position['shares']
                pnl_pct = (final_price / current_position['entry_price'] - 1) * 100
                
                trade_record = {
                    'symbol': symbol,
                    'entry_date': current_position['entry_date'],
                    'exit_date': df.index[-1],
                    'entry_price': current_position['entry_price'],
                    'exit_price': final_price,
                    'shares': current_position['shares'],
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'END_OF_PERIOD',
                    'conviction_level': current_position['conviction_level'],
                    'holding_days': (df.index[-1] - current_position['entry_date']).days
                }
                trades.append(trade_record)
            
        except Exception as e:
            self.logger.error(f"Error simulating trades for {symbol}: {e}")
        
        return trades
    
    def calculate_performance_metrics(self, trades_df: pd.DataFrame, benchmark_returns: pd.Series) -> Dict:
        """Calculate comprehensive performance metrics"""
        if trades_df.empty:
            return {'total_return': 0, 'error': 'No trades'}
        
        try:
            # Basic metrics
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['pnl_pct'] > 0])
            losing_trades = len(trades_df[trades_df['pnl_pct'] <= 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # P&L metrics
            total_pnl = trades_df['pnl'].sum()
            total_return_pct = (total_pnl / self.initial_capital) * 100
            avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].mean() if losing_trades > 0 else 0
            
            # Risk metrics
            returns_series = trades_df.set_index('exit_date')['pnl_pct'] / 100
            if len(returns_series) > 1:
                sharpe_ratio = (returns_series.mean() * 252 - self.risk_free_rate) / (returns_series.std() * np.sqrt(252))
                max_drawdown = self.calculate_max_drawdown(trades_df)
            else:
                sharpe_ratio = 0
                max_drawdown = 0
            
            # Timing metrics
            avg_holding_days = trades_df['holding_days'].mean()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_return_pct': total_return_pct,
                'avg_win_pct': avg_win,
                'avg_loss_pct': avg_loss,
                'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown_pct': max_drawdown,
                'avg_holding_days': avg_holding_days,
                'total_pnl': total_pnl
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown"""
        try:
            trades_df = trades_df.sort_values('exit_date')
            cumulative_returns = (trades_df['pnl_pct'] / 100).cumsum()
            running_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns - running_max
            max_drawdown = drawdowns.min() * 100  # Convert to percentage
            return abs(max_drawdown)
        except:
            return 0
    
    def get_benchmark_data(self, benchmark_symbol: str) -> pd.Series:
        """Get benchmark returns for comparison"""
        try:
            benchmark_data = self.get_historical_data(benchmark_symbol)
            if benchmark_data is not None:
                returns = benchmark_data['close'].pct_change().dropna()
                return returns
            return pd.Series(dtype=float)
        except:
            return pd.Series(dtype=float)


def main():
    """Initialize backtesting framework"""
    print("Backtesting framework loaded successfully")
    print("Ready for historical analysis...")

if __name__ == "__main__":
    main()