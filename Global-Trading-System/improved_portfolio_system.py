"""
Improved Portfolio Trading System
Enhanced risk management and better entry/exit conditions
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import time
warnings.filterwarnings('ignore')

class ImprovedRiskManager:
    """Enhanced risk management with better position sizing"""
    
    def __init__(self, risk_percent=1.5, max_position_percent=8, max_portfolio_risk=15):
        self.risk_percent = risk_percent  # 1.5% risk per trade (more conservative)
        self.max_position_percent = max_position_percent  # Max 8% per position
        self.max_portfolio_risk = max_portfolio_risk  # Max 15% total portfolio risk
    
    def calculate_position_size(self, symbol, current_price, atr, account_balance):
        """
        Calculate position size using ATR-based risk management
        """
        # Use ATR for dynamic stop loss (2x ATR or minimum 4%)
        atr_percent = (atr / current_price) * 100
        stop_loss_percent = max(atr_percent * 2, 4.0)  # Minimum 4% stop
        stop_loss_percent = min(stop_loss_percent, 8.0)  # Maximum 8% stop
        
        # Calculate capital to risk
        capital_to_risk = account_balance * (self.risk_percent / 100)
        
        # Calculate stop loss price
        stop_loss_price = current_price * (1 - stop_loss_percent / 100)
        risk_per_share = current_price - stop_loss_price
        
        if risk_per_share <= 0:
            return None
        
        # Calculate shares based on risk
        shares_by_risk = int(capital_to_risk / risk_per_share)
        
        # Limit by maximum position size
        max_position_value = account_balance * (self.max_position_percent / 100)
        shares_by_position = int(max_position_value / current_price)
        
        # Take the smaller limit
        shares = min(shares_by_risk, shares_by_position)
        
        if shares <= 0:
            return None
        
        trade_value = shares * current_price
        
        return {
            "symbol": symbol,
            "shares": shares,
            "current_price": current_price,
            "trade_value": trade_value,
            "stop_loss_price": stop_loss_price,
            "stop_loss_percent": stop_loss_percent,
            "risk_amount": shares * risk_per_share,
            "position_percent": (trade_value / account_balance) * 100,
            "atr": atr
        }

class ImprovedPortfolio:
    """Enhanced portfolio with better risk controls"""
    
    def __init__(self, initial_balance=100000):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {}
        self.trade_history = []
        self.portfolio_history = []
        self.risk_manager = ImprovedRiskManager()
        self.max_positions = 8  # Reduced for better concentration
        self.daily_loss_limit = 0.02  # 2% daily loss limit
        self.daily_start_value = initial_balance
        
    def get_portfolio_value(self, current_prices=None):
        """Calculate current portfolio value"""
        total_value = self.cash
        
        if current_prices:
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    total_value += position['shares'] * current_prices[symbol]
        
        return total_value
    
    def check_daily_loss_limit(self, current_prices):
        """Check if daily loss limit is exceeded"""
        current_value = self.get_portfolio_value(current_prices)
        daily_loss = (self.daily_start_value - current_value) / self.daily_start_value
        
        return daily_loss > self.daily_loss_limit
    
    def enter_position(self, symbol, current_price, atr, signal_info=None):
        """Enter position with improved risk management"""
        if symbol in self.positions:
            return False, "Already have position"
        
        if len(self.positions) >= self.max_positions:
            return False, "Maximum positions reached"
        
        current_portfolio_value = self.get_portfolio_value()
        
        # Calculate position using ATR-based risk
        position_calc = self.risk_manager.calculate_position_size(
            symbol, current_price, atr, current_portfolio_value
        )
        
        if not position_calc:
            return False, "Risk calculation failed"
        
        # Check if we have enough cash
        if position_calc['trade_value'] > self.cash:
            return False, "Insufficient cash"
        
        # Execute trade
        self.cash -= position_calc['trade_value']
        
        self.positions[symbol] = {
            'shares': position_calc['shares'],
            'entry_price': current_price,
            'entry_date': datetime.now(),
            'stop_loss': position_calc['stop_loss_price'],
            'entry_value': position_calc['trade_value'],
            'atr_at_entry': atr,
            'highest_price': current_price,  # For trailing stops
            'signal_info': signal_info or {}
        }
        
        # Log trade
        self.trade_history.append({
            'action': 'buy',
            'symbol': symbol,
            'date': datetime.now(),
            'price': current_price,
            'shares': position_calc['shares'],
            'value': position_calc['trade_value'],
            'stop_loss': position_calc['stop_loss_price'],
            'stop_loss_percent': position_calc['stop_loss_percent'],
            'risk_amount': position_calc['risk_amount'],
            'position_percent': position_calc['position_percent'],
            'portfolio_value': current_portfolio_value,
            'signal_info': signal_info
        })
        
        print(f"ENTER {symbol}: {position_calc['shares']} shares @ ${current_price:.2f}")
        print(f"  Value: ${position_calc['trade_value']:,.0f} ({position_calc['position_percent']:.1f}%)")
        print(f"  Stop: ${position_calc['stop_loss_price']:.2f} ({position_calc['stop_loss_percent']:.1f}%)")
        print(f"  Risk: ${position_calc['risk_amount']:.0f}")
        
        return True, "Position entered"
    
    def exit_position(self, symbol, current_price, reason="Manual exit"):
        """Exit position"""
        if symbol not in self.positions:
            return False, "No position to exit"
        
        position = self.positions[symbol]
        proceeds = position['shares'] * current_price
        self.cash += proceeds
        
        # Calculate P&L
        pnl = proceeds - position['entry_value']
        pnl_percent = (current_price / position['entry_price'] - 1) * 100
        
        # Log trade
        self.trade_history.append({
            'action': 'sell',
            'symbol': symbol,
            'date': datetime.now(),
            'price': current_price,
            'shares': position['shares'],
            'value': proceeds,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'hold_days': (datetime.now() - position['entry_date']).days,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value({symbol: current_price})
        })
        
        print(f"EXIT {symbol}: ${pnl:,.0f} ({pnl_percent:.1f}%) - {reason}")
        
        del self.positions[symbol]
        return True, "Position exited"
    
    def update_stops_and_trails(self, current_prices):
        """Update stops and trailing stops"""
        positions_to_exit = []
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                
                # Update highest price for trailing
                if current_price > position['highest_price']:
                    position['highest_price'] = current_price
                
                # Calculate current gain
                current_gain = (current_price / position['entry_price'] - 1) * 100
                
                # Start trailing after 20% gain
                if current_gain > 20:
                    # Trail by 15% from highest price
                    trail_stop = position['highest_price'] * 0.85
                    if trail_stop > position['stop_loss']:
                        old_stop = position['stop_loss']
                        position['stop_loss'] = trail_stop
                        print(f"TRAIL {symbol}: Stop ${old_stop:.2f} -> ${trail_stop:.2f}")
                
                # Check if stop hit
                if current_price <= position['stop_loss']:
                    positions_to_exit.append((symbol, current_price, "Stop loss"))
        
        # Execute exits
        for symbol, price, reason in positions_to_exit:
            self.exit_position(symbol, price, reason)
    
    def get_performance_summary(self):
        """Get performance summary"""
        if not self.trade_history:
            return {"error": "No trades"}
        
        trades_df = pd.DataFrame(self.trade_history)
        buy_trades = trades_df[trades_df['action'] == 'buy']
        sell_trades = trades_df[trades_df['action'] == 'sell']
        
        current_value = self.get_portfolio_value()
        total_return = (current_value / self.initial_balance - 1) * 100
        
        summary = {
            'initial_balance': self.initial_balance,
            'current_value': current_value,
            'total_return_percent': total_return,
            'total_trades': len(buy_trades),
            'completed_trades': len(sell_trades),
            'active_positions': len(self.positions)
        }
        
        if len(sell_trades) > 0:
            summary.update({
                'win_rate_percent': (sell_trades['pnl_percent'] > 0).mean() * 100,
                'average_return_percent': sell_trades['pnl_percent'].mean(),
                'best_trade_percent': sell_trades['pnl_percent'].max(),
                'worst_trade_percent': sell_trades['pnl_percent'].min(),
                'total_realized_pnl': sell_trades['pnl'].sum()
            })
        
        return summary

def download_and_calculate_atr(symbol, start_date, end_date):
    """Download data and calculate ATR"""
    try:
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None
        
        # Fix columns
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        
        # Calculate ATR
        data['High_Low'] = data['High'] - data['Low']
        data['High_Close'] = abs(data['High'] - data['Close'].shift(1))
        data['Low_Close'] = abs(data['Low'] - data['Close'].shift(1))
        data['TR'] = data[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
        data['ATR'] = data['TR'].rolling(14).mean()
        
        return data
        
    except Exception as e:
        return None

def get_quality_stocks():
    """Get a list of quality stocks for trading"""
    # Focus on liquid, established stocks with good volatility
    quality_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
        'AMD', 'ADBE', 'CRM', 'PYPL', 'SHOP', 'SQ', 'ROKU', 'ZOOM',
        'JPM', 'BAC', 'GS', 'MS', 'V', 'MA', 'UNH', 'JNJ',
        'HD', 'LOW', 'TGT', 'WMT', 'COST', 'NKE', 'SBUX', 'MCD'
    ]
    return quality_stocks

def calculate_improved_signals(stock_data):
    """Calculate improved trading signals"""
    print(f"Calculating improved signals for {len(stock_data)} stocks...")
    
    results = {}
    
    for symbol, data in stock_data.items():
        try:
            # Basic indicators
            data['MA_10'] = data['Close'].rolling(10).mean()
            data['MA_20'] = data['Close'].rolling(20).mean()
            data['MA_50'] = data['Close'].rolling(50).mean()
            data['MA_200'] = data['Close'].rolling(200).mean()
            
            # Momentum indicators
            data['ROC_10'] = (data['Close'] / data['Close'].shift(10) - 1) * 100
            data['ROC_20'] = (data['Close'] / data['Close'].shift(20) - 1) * 100
            
            # Volume analysis
            data['Volume_MA'] = data['Volume'].rolling(20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_MA']
            
            # Volatility
            data['BB_Upper'] = data['MA_20'] + (data['Close'].rolling(20).std() * 2)
            data['BB_Lower'] = data['MA_20'] - (data['Close'].rolling(20).std() * 2)
            data['BB_Position'] = (data['Close'] - data['BB_Lower']) / (data['BB_Upper'] - data['BB_Lower'])
            
            # Trend strength
            data['ADX'] = abs(data['MA_10'] - data['MA_20']) / data['Close'] * 100
            
            # Entry conditions (more selective)
            conditions = {
                'trending_up': data['Close'] > data['MA_200'],  # Long-term uptrend
                'strong_momentum': data['ROC_20'] > 15,  # Strong 20-day momentum
                'recent_strength': data['ROC_10'] > 5,   # Recent strength
                'ma_aligned': (data['MA_10'] > data['MA_20']) & (data['MA_20'] > data['MA_50']),
                'above_ma20': data['Close'] > data['MA_20'],
                'volume_surge': data['Volume_Ratio'] > 1.3,
                'not_overbought': data['BB_Position'] < 0.8,  # Not too extended
                'strong_trend': data['ADX'] > 1.0  # Trending market
            }
            
            # Combined entry signal (more conservative)
            data['Entry_Signal'] = (
                conditions['trending_up'] &
                conditions['strong_momentum'] &
                conditions['recent_strength'] &
                conditions['ma_aligned'] &
                conditions['above_ma20'] &
                conditions['volume_surge'] &
                conditions['not_overbought'] &
                conditions['strong_trend']
            )
            
            # Exit signals
            data['Exit_Signal'] = (
                (data['Close'] < data['MA_10']) |  # Below fast MA
                (data['ROC_10'] < -5)  # Recent weakness
            )
            
            signals = data['Entry_Signal'].sum()
            print(f"  {symbol}: {signals} signals")
            
            results[symbol] = data
            
        except Exception as e:
            print(f"  Error processing {symbol}: {e}")
            continue
    
    return results

def run_improved_backtest(processed_data, portfolio):
    """Run improved backtest"""
    print(f"\nRunning improved backtest...")
    
    # Get trading dates
    all_dates = None
    for symbol, data in processed_data.items():
        if all_dates is None:
            all_dates = data.index
        else:
            all_dates = all_dates.intersection(data.index)
    
    all_dates = sorted(all_dates)
    print(f"Trading period: {len(all_dates)} days")
    
    for i, date in enumerate(all_dates):
        # Update daily start value
        if i == 0 or date.day != all_dates[i-1].day:
            current_prices = {symbol: data.loc[date, 'Close'] 
                            for symbol, data in processed_data.items() 
                            if date in data.index}
            portfolio.daily_start_value = portfolio.get_portfolio_value(current_prices)
        
        # Get current prices and ATR
        current_prices = {}
        current_atrs = {}
        
        for symbol, data in processed_data.items():
            if date in data.index:
                current_prices[symbol] = data.loc[date, 'Close']
                current_atrs[symbol] = data.loc[date, 'ATR']
        
        # Check daily loss limit
        if portfolio.check_daily_loss_limit(current_prices):
            print(f"Daily loss limit exceeded on {date}")
            continue
        
        # Update stops and trails
        portfolio.update_stops_and_trails(current_prices)
        
        # Check exits
        for symbol in list(portfolio.positions.keys()):
            if symbol in processed_data and date in processed_data[symbol].index:
                if processed_data[symbol].loc[date, 'Exit_Signal']:
                    portfolio.exit_position(symbol, current_prices[symbol], "Exit signal")
        
        # Check entries (only if market conditions are good)
        if len(portfolio.positions) < portfolio.max_positions:
            entry_candidates = []
            
            for symbol, data in processed_data.items():
                if symbol not in portfolio.positions and date in data.index:
                    if (data.loc[date, 'Entry_Signal'] and 
                        not pd.isna(current_atrs.get(symbol)) and
                        current_atrs[symbol] > 0):
                        
                        # Score the entry
                        score = (
                            data.loc[date, 'ROC_20'] +  # Momentum
                            data.loc[date, 'Volume_Ratio'] +  # Volume
                            (data.loc[date, 'ADX'] * 10)  # Trend strength
                        )
                        
                        entry_candidates.append((symbol, score))
            
            # Sort by score and enter best opportunities
            entry_candidates.sort(key=lambda x: x[1], reverse=True)
            
            for symbol, score in entry_candidates[:2]:  # Max 2 entries per day
                if len(portfolio.positions) >= portfolio.max_positions:
                    break
                
                signal_info = {
                    'score': score,
                    'momentum': processed_data[symbol].loc[date, 'ROC_20'],
                    'volume_ratio': processed_data[symbol].loc[date, 'Volume_Ratio']
                }
                
                success, message = portfolio.enter_position(
                    symbol, 
                    current_prices[symbol], 
                    current_atrs[symbol],
                    signal_info
                )
        
        # Progress update
        if (i + 1) % 100 == 0:
            pv = portfolio.get_portfolio_value(current_prices)
            print(f"  Day {i+1}/{len(all_dates)}: ${pv:,.0f}, Positions: {len(portfolio.positions)}")

def main():
    """Main improved portfolio system"""
    print("IMPROVED PORTFOLIO TRADING SYSTEM")
    print("Enhanced Risk Management & Signal Quality")
    print("=" * 50)
    
    # Initialize improved portfolio
    portfolio = ImprovedPortfolio(initial_balance=100000)
    
    # Get quality stocks
    symbols = get_quality_stocks()
    print(f"Using {len(symbols)} quality stocks")
    
    # Download data with ATR
    print("Downloading data and calculating ATR...")
    stock_data = {}
    
    for i, symbol in enumerate(symbols):
        print(f"  {i+1}/{len(symbols)}: {symbol}")
        data = download_and_calculate_atr(symbol, '2022-01-01', '2023-12-31')
        
        if data is not None and len(data) > 200:
            stock_data[symbol] = data
            print(f"    SUCCESS: {len(data)} days")
        else:
            print(f"    FAILED")
        
        time.sleep(0.1)
    
    print(f"Downloaded {len(stock_data)} stocks")
    
    if not stock_data:
        print("No data downloaded!")
        return
    
    # Calculate improved signals
    processed_data = calculate_improved_signals(stock_data)
    
    if not processed_data:
        print("No signals calculated!")
        return
    
    # Run backtest
    run_improved_backtest(processed_data, portfolio)
    
    # Results
    summary = portfolio.get_performance_summary()
    
    print(f"\n" + "=" * 50)
    print("IMPROVED PORTFOLIO RESULTS")
    print("=" * 50)
    
    for key, value in summary.items():
        if isinstance(value, float):
            if 'percent' in key:
                print(f"{key.replace('_', ' ').title()}: {value:.2f}%")
            else:
                print(f"{key.replace('_', ' ').title()}: ${value:,.2f}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if portfolio.trade_history:
        trades_df = pd.DataFrame(portfolio.trade_history)
        filename = f"improved_portfolio_trades_{timestamp}.csv"
        trades_df.to_csv(filename, index=False)
        print(f"\nResults saved: {filename}")

if __name__ == "__main__":
    main()