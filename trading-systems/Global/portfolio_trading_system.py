"""
Portfolio Trading System with Risk Management
Integrates place_trade.py risk management approach with our working system
Starting balance: $100,000
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import time
warnings.filterwarnings('ignore')

class RiskManager:
    """Risk management class based on place_trade.py"""
    
    def __init__(self, risk_percent=2, default_stop_loss_percent=5, max_position_percent=10):
        self.risk_percent = risk_percent  # 2% risk per trade
        self.default_stop_loss_percent = default_stop_loss_percent  # 5% default stop loss
        self.max_position_percent = max_position_percent  # Max 10% per position
    
    def calculate_trade(self, symbol, current_price, account_balance, stop_loss_percent=None):
        """
        Calculate trade size based on risk management - from place_trade.py
        """
        if stop_loss_percent is None:
            stop_loss_percent = self.default_stop_loss_percent
        
        # Calculate capital to risk
        capital_to_risk = account_balance * (self.risk_percent / 100)
        
        # Calculate stop loss price
        stop_loss = current_price * (1 - stop_loss_percent / 100)
        
        # Risk per share
        risk_per_share = current_price - stop_loss
        
        if risk_per_share <= 0:
            return None  # Invalid risk calculation
        
        # Number of shares to buy (rounded down to nearest whole share)
        shares_by_risk = int(capital_to_risk / risk_per_share)
        
        # Limit by maximum position size
        max_position_value = account_balance * (self.max_position_percent / 100)
        shares_by_position_limit = int(max_position_value / current_price)
        
        # Take the smaller of the two limits
        shares = min(shares_by_risk, shares_by_position_limit)
        
        if shares <= 0:
            return None
        
        # Total trade value
        trade_value = shares * current_price
        
        return {
            "symbol": symbol,
            "shares": shares,
            "current_price": current_price,
            "trade_value": trade_value,
            "stop_loss": stop_loss,
            "stop_loss_percent": stop_loss_percent,
            "risk_amount": shares * risk_per_share,
            "position_percent": (trade_value / account_balance) * 100
        }

class Portfolio:
    """Portfolio management class"""
    
    def __init__(self, initial_balance=100000):
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.positions = {}  # {symbol: position_info}
        self.trade_history = []
        self.portfolio_history = []
        self.risk_manager = RiskManager()
    
    def get_portfolio_value(self, current_prices=None):
        """Calculate current portfolio value"""
        total_value = self.cash
        
        if current_prices:
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    total_value += position['shares'] * current_prices[symbol]
        
        return total_value
    
    def get_position_value(self, symbol, current_price):
        """Get current value of a position"""
        if symbol in self.positions:
            return self.positions[symbol]['shares'] * current_price
        return 0
    
    def can_add_position(self, symbol, proposed_trade_value):
        """Check if we can add a new position"""
        current_portfolio_value = self.get_portfolio_value()
        max_positions = 10  # Maximum number of positions
        
        # Check if we already have too many positions
        if len(self.positions) >= max_positions:
            return False, "Maximum positions reached"
        
        # Check if we have enough cash
        if proposed_trade_value > self.cash:
            return False, "Insufficient cash"
        
        # Check if position size is reasonable
        position_percent = (proposed_trade_value / current_portfolio_value) * 100
        if position_percent > self.risk_manager.max_position_percent:
            return False, f"Position too large: {position_percent:.1f}%"
        
        return True, "OK"
    
    def enter_position(self, symbol, current_price, signal_info=None):
        """Enter a new position using risk management"""
        if symbol in self.positions:
            return False, "Already have position"
        
        current_portfolio_value = self.get_portfolio_value()
        
        # Calculate trade using risk management
        trade_calc = self.risk_manager.calculate_trade(
            symbol=symbol,
            current_price=current_price,
            account_balance=current_portfolio_value
        )
        
        if not trade_calc:
            return False, "Risk calculation failed"
        
        # Check if we can add this position
        can_add, reason = self.can_add_position(symbol, trade_calc['trade_value'])
        if not can_add:
            return False, reason
        
        # Execute the trade
        self.cash -= trade_calc['trade_value']
        
        self.positions[symbol] = {
            'shares': trade_calc['shares'],
            'entry_price': current_price,
            'entry_date': datetime.now(),
            'stop_loss': trade_calc['stop_loss'],
            'entry_value': trade_calc['trade_value'],
            'signal_info': signal_info or {}
        }
        
        # Record trade
        self.trade_history.append({
            'action': 'buy',
            'symbol': symbol,
            'date': datetime.now(),
            'price': current_price,
            'shares': trade_calc['shares'],
            'value': trade_calc['trade_value'],
            'stop_loss': trade_calc['stop_loss'],
            'portfolio_value': current_portfolio_value,
            'cash_after': self.cash,
            'signal_info': signal_info
        })
        
        print(f"ENTER {symbol}: {trade_calc['shares']} shares @ ${current_price:.2f}")
        print(f"  Trade value: ${trade_calc['trade_value']:,.0f}")
        print(f"  Stop loss: ${trade_calc['stop_loss']:.2f}")
        print(f"  Risk amount: ${trade_calc['risk_amount']:.0f}")
        print(f"  Position %: {trade_calc['position_percent']:.1f}%")
        
        return True, "Position entered"
    
    def exit_position(self, symbol, current_price, reason="Manual exit"):
        """Exit a position"""
        if symbol not in self.positions:
            return False, "No position to exit"
        
        position = self.positions[symbol]
        proceeds = position['shares'] * current_price
        self.cash += proceeds
        
        # Calculate P&L
        pnl = proceeds - position['entry_value']
        pnl_percent = (current_price / position['entry_price'] - 1) * 100
        
        # Record trade
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
        
        print(f"EXIT {symbol}: {position['shares']} shares @ ${current_price:.2f}")
        print(f"  P&L: ${pnl:,.0f} ({pnl_percent:.1f}%)")
        print(f"  Reason: {reason}")
        
        del self.positions[symbol]
        return True, "Position exited"
    
    def check_stop_losses(self, current_prices):
        """Check stop losses for all positions"""
        positions_to_exit = []
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                if current_price <= position['stop_loss']:
                    positions_to_exit.append((symbol, current_price, "Stop loss"))
        
        for symbol, price, reason in positions_to_exit:
            self.exit_position(symbol, price, reason)
    
    def update_trailing_stops(self, current_prices, trail_percent=10):
        """Update trailing stops for profitable positions"""
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                current_gain = (current_price / position['entry_price'] - 1) * 100
                
                # Start trailing after 15% gain
                if current_gain > 15:
                    new_stop = current_price * (1 - trail_percent / 100)
                    if new_stop > position['stop_loss']:
                        old_stop = position['stop_loss']
                        position['stop_loss'] = new_stop
                        print(f"TRAIL {symbol}: Stop moved from ${old_stop:.2f} to ${new_stop:.2f}")
    
    def record_portfolio_snapshot(self, current_prices, date):
        """Record portfolio value for tracking"""
        portfolio_value = self.get_portfolio_value(current_prices)
        
        position_values = {}
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position_values[symbol] = {
                    'shares': position['shares'],
                    'price': current_prices[symbol],
                    'value': position['shares'] * current_prices[symbol],
                    'pnl_percent': (current_prices[symbol] / position['entry_price'] - 1) * 100
                }
        
        self.portfolio_history.append({
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'positions_count': len(self.positions),
            'position_values': position_values,
            'total_return_percent': (portfolio_value / self.initial_balance - 1) * 100
        })
    
    def get_performance_summary(self):
        """Get portfolio performance summary"""
        if not self.trade_history:
            return {"error": "No trades executed"}
        
        trades_df = pd.DataFrame(self.trade_history)
        buy_trades = trades_df[trades_df['action'] == 'buy']
        sell_trades = trades_df[trades_df['action'] == 'sell']
        
        current_value = self.get_portfolio_value()
        total_return = (current_value / self.initial_balance - 1) * 100
        
        summary = {
            'initial_balance': self.initial_balance,
            'current_value': current_value,
            'cash': self.cash,
            'total_return_percent': total_return,
            'total_trades': len(buy_trades),
            'active_positions': len(self.positions),
            'total_invested': buy_trades['value'].sum() if len(buy_trades) > 0 else 0,
            'total_proceeds': sell_trades['value'].sum() if len(sell_trades) > 0 else 0
        }
        
        if len(sell_trades) > 0:
            summary.update({
                'completed_trades': len(sell_trades),
                'win_rate_percent': (sell_trades['pnl_percent'] > 0).mean() * 100,
                'average_return_percent': sell_trades['pnl_percent'].mean(),
                'best_trade_percent': sell_trades['pnl_percent'].max(),
                'worst_trade_percent': sell_trades['pnl_percent'].min(),
                'total_realized_pnl': sell_trades['pnl'].sum()
            })
        
        return summary

def get_sp500_symbols():
    """Get S&P 500 symbols"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url, header=0)[0]
        tickers = table['Symbol'].tolist()
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        print(f"Fetched {len(tickers)} S&P 500 tickers")
        return tickers
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT']

def download_and_fix_columns(symbol, start_date, end_date):
    """Download single symbol and fix columns"""
    try:
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None
        
        # Fix multi-level columns
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        
        return data
        
    except Exception as e:
        return None

def download_stocks_for_portfolio(symbols, start_date, end_date, max_stocks=20):
    """Download stocks for portfolio system"""
    print(f"Downloading {min(len(symbols), max_stocks)} stocks for portfolio system...")
    
    stock_data = {}
    test_symbols = symbols[:max_stocks]
    
    for i, symbol in enumerate(test_symbols):
        print(f"  {i+1}/{len(test_symbols)}: {symbol}")
        
        data = download_and_fix_columns(symbol, start_date, end_date)
        
        if data is not None and len(data) > 50:
            stock_data[symbol] = data
            print(f"    SUCCESS: {len(data)} days")
        else:
            print(f"    FAILED")
        
        time.sleep(0.1)
    
    print(f"Downloaded {len(stock_data)} stocks successfully")
    return stock_data

def calculate_signals_for_portfolio(stock_data):
    """Calculate trading signals for portfolio system"""
    print(f"Calculating signals for {len(stock_data)} stocks...")
    
    results = {}
    
    for symbol, data in stock_data.items():
        try:
            # Calculate indicators
            data['MA_10'] = data['Close'].rolling(10).mean()
            data['MA_20'] = data['Close'].rolling(20).mean()
            data['MA_50'] = data['Close'].rolling(50).mean()
            
            # Momentum
            data['Momentum_20'] = data['Close'] / data['Close'].shift(20) - 1
            data['Momentum_10'] = data['Close'] / data['Close'].shift(10) - 1
            
            # Volume
            data['Volume_MA_20'] = data['Volume'].rolling(20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_MA_20']
            
            # ATR for volatility-based stops
            data['High_Low'] = data['High'] - data['Low']
            data['High_Close'] = abs(data['High'] - data['Close'].shift(1))
            data['Low_Close'] = abs(data['Low'] - data['Close'].shift(1))
            data['TR'] = data[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
            data['ATR'] = data['TR'].rolling(14).mean()
            
            # Entry conditions (more conservative for portfolio)
            data['Strong_Momentum'] = data['Momentum_20'] > 0.10  # 10% momentum
            data['Recent_Strength'] = data['Momentum_10'] > 0.03  # 3% recent momentum
            data['Above_MA20'] = data['Close'] > data['MA_20']
            data['MA_Aligned'] = data['MA_20'] > data['MA_50']
            data['Volume_Surge'] = data['Volume_Ratio'] > 1.5
            data['High_20'] = data['High'].rolling(20).max()
            data['Near_Highs'] = data['Close'] > (data['High_20'] * 0.90)
            
            # Combined entry signal
            data['Entry_Signal'] = (
                data['Strong_Momentum'] &
                data['Recent_Strength'] &
                data['Above_MA20'] &
                data['MA_Aligned'] &
                data['Volume_Surge'] &
                data['Near_Highs']
            )
            
            # Exit signals
            data['Exit_Signal'] = data['Close'] < data['MA_20']
            
            # Calculate dynamic stop loss based on ATR
            data['ATR_Stop_Percent'] = np.clip((data['ATR'] / data['Close']) * 2, 0.03, 0.10)
            
            signals = data['Entry_Signal'].sum()
            print(f"  {symbol}: {signals} signals")
            
            results[symbol] = data
            
        except Exception as e:
            print(f"  Error processing {symbol}: {e}")
            continue
    
    return results

def run_portfolio_backtest(processed_data, portfolio):
    """Run backtest with portfolio risk management"""
    print(f"\nRunning portfolio backtest...")
    
    # Get trading dates
    all_dates = None
    for symbol, data in processed_data.items():
        if all_dates is None:
            all_dates = data.index
        else:
            all_dates = all_dates.intersection(data.index)
    
    all_dates = sorted(all_dates)
    print(f"Trading period: {len(all_dates)} days ({all_dates[0]} to {all_dates[-1]})")
    
    # Backtest loop
    for i, date in enumerate(all_dates):
        current_prices = {}
        
        # Get current prices
        for symbol, data in processed_data.items():
            if date in data.index:
                current_prices[symbol] = data.loc[date, 'Close']
        
        # Check stop losses first
        portfolio.check_stop_losses(current_prices)
        
        # Update trailing stops
        portfolio.update_trailing_stops(current_prices)
        
        # Check exits
        for symbol in list(portfolio.positions.keys()):
            if symbol in processed_data and date in processed_data[symbol].index:
                if processed_data[symbol].loc[date, 'Exit_Signal']:
                    portfolio.exit_position(symbol, current_prices[symbol], "Exit signal")
        
        # Check entries
        for symbol, data in processed_data.items():
            if symbol not in portfolio.positions and date in data.index:
                if data.loc[date, 'Entry_Signal']:
                    # Get dynamic stop loss percentage
                    atr_stop_pct = data.loc[date, 'ATR_Stop_Percent'] * 100
                    
                    signal_info = {
                        'momentum_20': data.loc[date, 'Momentum_20'],
                        'volume_ratio': data.loc[date, 'Volume_Ratio'],
                        'atr_stop_pct': atr_stop_pct
                    }
                    
                    # Use dynamic stop loss from ATR
                    portfolio.risk_manager.default_stop_loss_percent = atr_stop_pct
                    
                    success, message = portfolio.enter_position(
                        symbol, 
                        current_prices[symbol], 
                        signal_info
                    )
                    
                    if not success and "Maximum positions" not in message:
                        print(f"  Could not enter {symbol}: {message}")
        
        # Record portfolio snapshot
        portfolio.record_portfolio_snapshot(current_prices, date)
        
        # Progress update
        if (i + 1) % 100 == 0:
            pv = portfolio.get_portfolio_value(current_prices)
            print(f"  Day {i+1}/{len(all_dates)}: Portfolio ${pv:,.0f}, Positions: {len(portfolio.positions)}")

def main():
    """Main portfolio trading system"""
    print("PORTFOLIO TRADING SYSTEM WITH RISK MANAGEMENT")
    print("Starting Balance: $100,000")
    print("Risk Management: 2% risk per trade, 10% max position size")
    print("=" * 60)
    
    # Initialize portfolio
    portfolio = Portfolio(initial_balance=100000)
    
    # Get symbols and download data
    symbols = get_sp500_symbols()
    stock_data = download_stocks_for_portfolio(symbols, '2022-01-01', '2023-12-31', max_stocks=25)
    
    if not stock_data:
        print("No data downloaded!")
        return
    
    # Calculate signals
    processed_data = calculate_signals_for_portfolio(stock_data)
    
    if not processed_data:
        print("No signals calculated!")
        return
    
    # Run backtest
    run_portfolio_backtest(processed_data, portfolio)
    
    # Get performance summary
    summary = portfolio.get_performance_summary()
    
    print(f"\n" + "=" * 60)
    print("PORTFOLIO PERFORMANCE SUMMARY")
    print("=" * 60)
    
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
    
    # Save trade history
    if portfolio.trade_history:
        trades_df = pd.DataFrame(portfolio.trade_history)
        trades_file = f"portfolio_trades_{timestamp}.csv"
        trades_df.to_csv(trades_file, index=False)
        print(f"\nTrade history saved: {trades_file}")
    
    # Save portfolio history
    if portfolio.portfolio_history:
        portfolio_df = pd.DataFrame(portfolio.portfolio_history)
        portfolio_file = f"portfolio_performance_{timestamp}.csv"
        portfolio_df.to_csv(portfolio_file, index=False)
        print(f"Portfolio performance saved: {portfolio_file}")
    
    print(f"\nPortfolio system completed successfully!")

if __name__ == "__main__":
    main()