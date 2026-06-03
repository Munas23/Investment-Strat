import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from lumibot.entities import Asset
import logging

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)

class TurtleTradingStrategy(Strategy):
    """
    Turtle Trading Strategy using Lumibot
    
    This strategy implements the classic Turtle Trading system:
    1. Entry: Buy when price breaks above 20-day high
    2. Exit: Sell when price breaks below 10-day low
    3. Position sizing: 5% per position, max 20 positions
    4. Momentum filter: Only trade stocks up 20%+ in last 6 months
    """
    
    def initialize(self):
        """Initialize strategy parameters"""
        # Set the minimum sleep time between iterations
        self.sleeptime = "1D"  # Check once per day
        
        # Turtle Trading Parameters
        self.entry_days = 20      # Buy on 20-day high breakout
        self.exit_days = 10       # Sell on 10-day low breakdown
        
        # Position Management
        self.max_positions = 20           # Maximum number of positions
        self.position_size = 0.05         # 5% position size
        
        # Momentum Filter
        self.momentum_period = 126        # ~6 months in trading days
        self.momentum_threshold = 0.20    # Minimum 20% gain required
        
        # Get S&P 500 tickers
        self.tickers = self.get_sp500_tickers()
        
        # Performance tracking
        self.trades_log = []
        self.entry_prices = {}  # Track entry prices for each position
        
        self.log_message("Turtle Trading Strategy initialized successfully")
        self.log_message(f"Tracking {len(self.tickers)} S&P 500 stocks")
        
    def get_sp500_tickers(self):
        """Get complete S&P 500 tickers list"""
        # Complete S&P 500 list as of the strategy date
        tickers = [
            'MSFT', 'NVDA', 'AAPL', 'AMZN', 'GOOG', 'GOOGL', 'META', 'AVGO', 'BRK-B', 'TSLA',
            'WMT', 'JPM', 'V', 'LLY', 'MA', 'NFLX', 'ORCL', 'COST', 'XOM', 'PG',
            'JNJ', 'HD', 'BAC', 'ABBV', 'KO', 'PLTR', 'PM', 'TMUS', 'UNH', 'GE',
            'CRM', 'CSCO', 'WFC', 'CVX', 'IBM', 'ABT', 'LIN', 'MCD', 'INTU', 'NOW',
            'AXP', 'MS', 'DIS', 'T', 'ISRG', 'ACN', 'MRK', 'AMD', 'RTX', 'VZ',
            'BKNG', 'GS', 'UBER', 'PEP', 'ADBE', 'TXN', 'BX', 'CAT', 'PGR', 'QCOM',
            'SCHW', 'SPGI', 'BA', 'AMGN', 'BLK', 'TMO', 'BSX', 'NEE', 'HON', 'SYK',
            'C', 'TJX', 'DE', 'DHR', 'GILD', 'AMAT', 'UNP', 'PANW', 'PFE', 'ADP',
            'GEV', 'ETN', 'CMCSA', 'LOW', 'ANET', 'MU', 'CB', 'CRWD', 'VRTX', 'MMC',
            'APH', 'LMT', 'MDT', 'LRCX', 'ADI', 'COP', 'KKR', 'KLAC', 'PLD', 'ICE',
            'SBUX', 'WELL', 'MO', 'AMT', 'CME', 'BMY', 'SO', 'TT', 'WM', 'CEG',
            'NKE', 'DASH', 'HCA', 'FI', 'CTAS', 'DUK', 'EQIX', 'SHW', 'MCK', 'ELV',
            'MCO', 'INTC', 'ABNB', 'PH', 'MDLZ', 'AJG', 'CI', 'UPS', 'TDG', 'CDNS',
            'CVS', 'FTNT', 'AON', 'RSG', 'ORLY', 'MMM', 'DELL', 'APO', 'COF', 'ZTS',
            'ECL', 'SNPS', 'RCL', 'GD', 'WMB', 'CL', 'MAR', 'ITW', 'PYPL', 'HWM',
            'CMG', 'PNC', 'NOC', 'MSI', 'USB', 'EMR', 'JCI', 'WDAY', 'BK', 'COIN',
            'ADSK', 'KMI', 'APD', 'EOG', 'AZO', 'TRV', 'MNST', 'AXON', 'ROP', 'CHTR',
            'SPG', 'DLR', 'CARR', 'CSX', 'HLT', 'FCX', 'VST', 'NEM', 'PAYX', 'NSC',
            'AFL', 'COR', 'ALL', 'AEP', 'MET', 'PWR', 'PSA', 'TFC', 'FDX', 'GWW',
            'NXPI', 'REGN', 'OKE', 'O', 'AIG', 'SRE', 'BDX', 'AMP', 'MPC', 'NDAQ',
            'PCAR', 'CTVA', 'TEL', 'CPRT', 'D', 'ROST', 'PSX', 'SLB', 'URI', 'LHX',
            'GM', 'EW', 'CMI', 'VRSK', 'KDP', 'KMB', 'TGT', 'KR', 'MSCI', 'GLW',
            'FICO', 'CCI', 'EXC', 'FIS', 'TTWO', 'IDXX', 'HES', 'OXY', 'KVUE', 'AME',
            'FANG', 'F', 'YUM', 'VLO', 'PEG', 'GRMN', 'CTSH', 'XEL', 'OTIS', 'CBRE',
            'BKR', 'EA', 'PRU', 'DHI', 'CAH', 'RMD', 'HIG', 'ED', 'ROK', 'TRGP',
            'EBAY', 'SYY', 'ACGL', 'ETR', 'WAB', 'MCHP', 'VMC', 'PCG', 'DXCM', 'ODFL',
            'EQT', 'WEC', 'IR', 'LYV', 'EFX', 'DAL', 'VICI', 'MLM', 'EXR', 'CSGP',
            'MPWR', 'A', 'TKO', 'GEHC', 'HSY', 'IT', 'CCL', 'LULU', 'BRO', 'KHC',
            'XYL', 'WTW', 'NRG', 'STZ', 'IRM', 'GIS', 'ANSS', 'RJF', 'MTB', 'VTR',
            'AVB', 'BR', 'LEN', 'DD', 'K', 'LVS', 'WRB', 'STT', 'NUE', 'ROL',
            'EXE', 'KEYS', 'HUM', 'DTE', 'UAL', 'CNC', 'AWK', 'TSCO', 'STX', 'EQR',
            'VRSN', 'IQV', 'FITB', 'GDDY', 'AEE', 'TPL', 'PPG', 'DRI', 'PPL', 'IP',
            'DG', 'VLTO', 'TYL', 'FTV', 'SMCI', 'EL', 'MTD', 'DOV', 'FOXA', 'CHD',
            'WBD', 'SBAC', 'ATO', 'ES', 'CNP', 'STE', 'CPAY', 'HPE', 'HPQ', 'HBAN',
            'CINF', 'CDW', 'FE', 'TDY', 'FOX', 'CBOE', 'ADM', 'SW', 'SYF', 'EXPE',
            'PODD', 'NTAP', 'LH', 'NVR', 'HUBB', 'NTRS', 'ON', 'CMS', 'ULTA', 'WAT',
            'AMCR', 'TROW', 'DVN', 'EIX', 'PTC', 'INVH', 'DOW', 'PHM', 'MKC', 'STLD',
            'RF', 'DLTR', 'TSN', 'IFF', 'LII', 'CTRA', 'BIIB', 'DGX', 'ERIE', 'WSM',
            'WY', 'WDC', 'LUV', 'LDOS', 'JBL', 'GPN', 'L', 'ESS', 'NI', 'ZBH',
            'GEN', 'LYB', 'MAA', 'CFG', 'KEY', 'FSLR', 'HAL', 'PKG', 'GPC', 'PFG',
            'TRMB', 'FFIV', 'HRL', 'SNA', 'RL', 'NWS', 'FDS', 'TPR', 'PNR', 'DECK',
            'WST', 'MOH', 'DPZ', 'CLX', 'NWSA', 'LNT', 'BAX', 'BBY', 'EXPD', 'J',
            'ZBRA', 'EVRG', 'CF', 'BALL', 'PAYC', 'EG', 'UDR', 'APTV', 'COO', 'HOLX',
            'KIM', 'AVY', 'OMC', 'JBHT', 'IEX', 'TER', 'TXT', 'MAS', 'INCY', 'BF-B',
            'JKHY', 'REG', 'BXP', 'ALGN', 'SOLV', 'CPT', 'BLDR', 'DOC', 'UHS', 'ARE',
            'NDSN', 'JNPR', 'ALLE', 'SJM', 'BEN', 'CHRW', 'AKAM', 'POOL', 'HST', 'MOS',
            'RVTY', 'SWKS', 'CAG', 'PNW', 'MRNA', 'TAP', 'DVA', 'AIZ', 'CPB', 'SWK',
            'VTRS', 'EPAM', 'LKQ', 'GL', 'BG', 'KMX', 'WBA', 'DAY', 'HAS', 'AOS',
            'EMN', 'HII', 'NCLH', 'MGM', 'WYNN', 'HSIC', 'IPG', 'FRT', 'MKTX', 'PARA',
            'LW', 'MTCH', 'AES', 'TECH', 'GNRC', 'CRL', 'ALB', 'APA', 'IVZ', 'MHK',
            'ENPH', 'CZR'
        ]
        
        # Clean tickers - remove any that might cause issues
        clean_tickers = []
        for ticker in tickers:
            if not ticker.startswith('$') and len(ticker) <= 5:
                clean_tickers.append(ticker)
        
        return clean_tickers[:100]  # Limit to first 100 for faster backtesting
    
    def get_symbol_data(self, symbol, days_back=150):
        """Get historical data for a symbol"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            
            if bars is not None and hasattr(bars, 'df') and len(bars.df) > 0:
                return bars.df
            return None
        except Exception as e:
            self.log_message(f"Error getting data for {symbol}: {e}")
            return None
    
    def check_momentum_filter(self, df, current_idx):
        """Check if stock passes 6-month momentum filter (up 20%+)"""
        if current_idx < self.momentum_period:
            return False, 0
        
        try:
            current_price = float(df['close'].iloc[current_idx])
            price_6m_ago = float(df['close'].iloc[current_idx - self.momentum_period])
            
            if price_6m_ago <= 0:
                return False, 0
            
            six_month_return = (current_price / price_6m_ago) - 1
            
            return six_month_return >= self.momentum_threshold, six_month_return
        except:
            return False, 0
    
    def check_entry_signal(self, df):
        """Check if price breaks above 20-day high"""
        if len(df) < self.entry_days + 1:
            return False
        
        try:
            # Get current high
            current_high = float(df['high'].iloc[-1])
            
            # Get 20-day high (excluding today)
            twenty_day_high = float(df['high'].iloc[-(self.entry_days+1):-1].max())
            
            # Entry signal: current high breaks above 20-day high
            return current_high > twenty_day_high
        except:
            return False
    
    def check_exit_signal(self, df):
        """Check if price breaks below 10-day low"""
        if len(df) < self.exit_days + 1:
            return False
        
        try:
            # Get current low
            current_low = float(df['low'].iloc[-1])
            
            # Get 10-day low (excluding today)
            ten_day_low = float(df['low'].iloc[-(self.exit_days+1):-1].min())
            
            # Exit signal: current low breaks below 10-day low
            return current_low < ten_day_low
        except:
            return False
    
    def calculate_position_size(self, price):
        """Calculate position size based on portfolio value"""
        try:
            portfolio_value = self.get_portfolio_value()
            position_value = portfolio_value * self.position_size
            shares = int(position_value / price)
            return max(shares, 0)
        except:
            return 0
    
    def on_trading_iteration(self):
        """Main trading logic executed daily"""
        try:
            # Get current date
            current_date = self.get_datetime()
            
            # Get current positions
            positions = self.get_positions()
            current_positions = len(positions)
            
            self.log_message(f"Date: {current_date.date()}, Positions: {current_positions}/{self.max_positions}")
            
            # First, check exit conditions for existing positions
            self.check_exits()
            
            # Then, look for new entries if we have room
            if current_positions < self.max_positions:
                self.scan_for_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def check_exits(self):
        """Check exit conditions for all positions"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                
                # Get recent data
                df = self.get_symbol_data(symbol, days_back=30)
                if df is None or len(df) < self.exit_days + 1:
                    continue
                
                # Check exit signal
                if self.check_exit_signal(df):
                    current_price = float(df['close'].iloc[-1])
                    
                    # Calculate P&L
                    entry_price = self.entry_prices.get(symbol, current_price)
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    
                    self.log_message(f"EXIT {symbol}: Price ${current_price:.2f}, P&L: {pnl_pct:.2f}%")
                    
                    # Create sell order
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    # Log the trade
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"10-day low exit, P&L: {pnl_pct:.2f}%")
                    
                    # Remove from entry prices
                    if symbol in self.entry_prices:
                        del self.entry_prices[symbol]
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {symbol}: {e}")
    
    def scan_for_entries(self):
        """Scan for new entry opportunities"""
        # Get current positions to avoid duplicates
        current_symbols = set()
        for pos in self.get_positions():
            current_symbols.add(pos.asset.symbol)
        
        # Track how many new positions we can add
        positions_to_add = self.max_positions - len(current_symbols)
        entries_found = 0
        
        # Collect all candidates first
        candidates = []
        
        for symbol in self.tickers:
            if symbol in current_symbols:
                continue
            
            try:
                # Get historical data
                df = self.get_symbol_data(symbol, days_back=150)
                if df is None or len(df) < self.momentum_period:
                    continue
                
                # Check momentum filter
                passes_momentum, six_month_return = self.check_momentum_filter(df, len(df) - 1)
                if not passes_momentum:
                    continue
                
                # Check entry signal
                if self.check_entry_signal(df):
                    current_price = float(df['close'].iloc[-1])
                    
                    # Calculate 20-day momentum for ranking
                    if len(df) >= 20:
                        momentum_20d = (current_price / float(df['close'].iloc[-20])) - 1
                    else:
                        momentum_20d = 0
                    
                    candidates.append({
                        'symbol': symbol,
                        'price': current_price,
                        'momentum_20d': momentum_20d,
                        'momentum_6m': six_month_return
                    })
                    
            except Exception as e:
                continue
        
        # Sort candidates by 20-day momentum (short-term strength)
        candidates.sort(key=lambda x: x['momentum_20d'], reverse=True)
        
        # Enter positions for top candidates
        for candidate in candidates[:positions_to_add]:
            try:
                symbol = candidate['symbol']
                price = candidate['price']
                quantity = self.calculate_position_size(price)
                
                if quantity > 0:
                    # Create and submit buy order
                    asset = Asset(symbol=symbol, asset_type="stock")
                    order = self.create_order(asset, quantity, "buy")
                    self.submit_order(order)
                    
                    # Store entry price
                    self.entry_prices[symbol] = price
                    
                    self.log_message(f"ENTRY {symbol}: {quantity} shares @ ${price:.2f}, "
                                   f"6M: {candidate['momentum_6m']:.1%}, 20D: {candidate['momentum_20d']:.1%}")
                    
                    # Log the trade
                    self.log_trade(symbol, "buy", price, quantity, 
                                 f"20-day breakout, 6M momentum: {candidate['momentum_6m']:.1%}")
                    
                    entries_found += 1
                    
            except Exception as e:
                self.log_message(f"Error entering position for {symbol}: {e}")
        
        if entries_found == 0 and len(candidates) == 0:
            self.log_message("No entry signals found")
        elif entries_found == 0 and len(candidates) > 0:
            self.log_message(f"Found {len(candidates)} candidates but couldn't enter positions")
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trade details"""
        trade_data = {
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason
        }
        self.trades_log.append(trade_data)
    
    def on_strategy_end(self):
        """Called when strategy ends"""
        self.log_message("\n=== TURTLE TRADING STRATEGY ENDED ===")
        self.export_trades_to_csv()
        self.print_performance_summary()
    
    def export_trades_to_csv(self):
        """Export all trades to CSV"""
        if not self.trades_log:
            self.log_message("No trades to export")
            return
        
        try:
            df = pd.DataFrame(self.trades_log)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"turtle_lumibot_trades_{timestamp}.csv"
            df.to_csv(filename, index=False)
            self.log_message(f"Exported {len(df)} trades to {filename}")
        except Exception as e:
            self.log_message(f"Error exporting trades: {e}")
    
    def print_performance_summary(self):
        """Print a summary of strategy performance"""
        try:
            positions = self.get_positions()
            portfolio_value = self.get_portfolio_value()
            cash = self.get_cash()
            
            self.log_message("\n=== TURTLE TRADING PERFORMANCE SUMMARY ===")
            self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
            self.log_message(f"Cash: ${cash:,.2f}")
            self.log_message(f"Active Positions: {len(positions)}")
            self.log_message(f"Total Trades: {len(self.trades_log)}")
            
            if self.trades_log:
                trades_df = pd.DataFrame(self.trades_log)
                buy_trades = trades_df[trades_df['action'] == 'buy']
                sell_trades = trades_df[trades_df['action'] == 'sell']
                
                self.log_message(f"\nTrade Statistics:")
                self.log_message(f"Buy Orders: {len(buy_trades)}")
                self.log_message(f"Sell Orders: {len(sell_trades)}")
                
                if len(buy_trades) > 0:
                    total_invested = buy_trades['value'].sum()
                    self.log_message(f"Total Invested: ${total_invested:,.2f}")
                
                if len(sell_trades) > 0:
                    total_sold = sell_trades['value'].sum()
                    self.log_message(f"Total Sold: ${total_sold:,.2f}")
                
                # Calculate win rate from closed trades
                closed_trades = []
                for sell in sell_trades.itertuples():
                    # Find corresponding buy
                    symbol_buys = buy_trades[buy_trades['symbol'] == sell.symbol]
                    if len(symbol_buys) > 0:
                        buy_price = symbol_buys.iloc[0]['price']
                        pnl = (sell.price - buy_price) / buy_price
                        closed_trades.append(pnl)
                
                if closed_trades:
                    win_rate = sum(1 for pnl in closed_trades if pnl > 0) / len(closed_trades) * 100
                    avg_win = np.mean([pnl for pnl in closed_trades if pnl > 0]) * 100 if any(pnl > 0 for pnl in closed_trades) else 0
                    avg_loss = np.mean([pnl for pnl in closed_trades if pnl < 0]) * 100 if any(pnl < 0 for pnl in closed_trades) else 0
                    
                    self.log_message(f"\nClosed Trade Statistics:")
                    self.log_message(f"Win Rate: {win_rate:.1f}%")
                    self.log_message(f"Average Win: {avg_win:.1f}%")
                    self.log_message(f"Average Loss: {avg_loss:.1f}%")
            
        except Exception as e:
            self.log_message(f"Error printing performance summary: {e}")


def run_backtest():
    """Run the Turtle Trading backtest"""
    try:
        # Strategy parameters - matching original backtest period
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2024, 12, 31)
        
        print("\n=== TURTLE TRADING STRATEGY BACKTEST ===")
        print(f"Period: {backtesting_start.strftime('%Y-%m-%d')} to {backtesting_end.strftime('%Y-%m-%d')}")
        print("Initial Capital: $100,000")
        print("Position Size: 5% per position")
        print("Max Positions: 20")
        print("Entry: 20-day high breakout")
        print("Exit: 10-day low breakdown")
        print("Filter: 6-month momentum > 20%")
        print("\nStarting backtest...")
        print("This may take several minutes...\n")
        
        # Custom backtest class with minimal fees
        class MinimalFeeBacktesting(YahooDataBacktesting):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Minimal trading fees to match original backtest
                self.trading_fee = 0.001  # 0.1% commission
        
        # Run the backtest
        results = TurtleTradingStrategy.backtest(
            MinimalFeeBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={
                "cash_at_risk": 0.05,  # Match position sizing
            },
            initial_cash=100000,  # $100k starting capital
            benchmark_asset="SPY"
        )
        
        return results
        
    except Exception as e:
        print(f"Error in backtest setup: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    try:
        print("Running S&P 500 Turtle Trading Strategy Backtest with Lumibot...")
        results = run_backtest()
        
        if results is not None:
            print("\n=== BACKTEST COMPLETED ===")
            print("Check the generated CSV file for detailed trade records")
            
            # Try to print additional stats if available
            try:
                print("\nTrying to extract performance metrics...")
                
                # Print any available statistics
                if hasattr(results, '__dict__'):
                    print("Available result attributes:")
                    for attr in dir(results):
                        if not attr.startswith('_'):
                            print(f"  - {attr}")
                
            except Exception as e:
                print(f"Could not extract detailed metrics: {e}")
        else:
            print("Backtest failed to complete")
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        import traceback
        traceback.print_exc()