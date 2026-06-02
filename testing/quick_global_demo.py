"""
Quick Global Trading Demo with verified working tickers
"""
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from multi_market_risk_manager import MultiMarketRiskManager
from market_config import MAJOR_MARKETS

warnings.filterwarnings('ignore')

class QuickGlobalDemo:
    """Quick demo of global trading with verified tickers"""
    
    def __init__(self):
        self.risk_manager = MultiMarketRiskManager(
            account_balance_usd=200000,
            default_risk_percent=2,
            max_position_size=0.08,
            max_positions_per_market=3,
            max_total_positions=12
        )
        
        # Use verified working tickers from diagnostic
        self.verified_tickers = {
            'US_SP500': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
            'AU_ASX300': ['CBA.AX', 'BHP.AX', 'WBC.AX', 'ANZ.AX', 'CSL.AX'],
            'UK_FTSE100': ['SHEL.L', 'AZN.L', 'ULVR.L'],
            'DE_DAX': ['SAP.DE', 'SIE.DE'],
            'JP_NIKKEI': ['7203.T', '6758.T']
        }
        
        self.trades_log = []
        
    def get_price_data(self, ticker, days=30):
        """Get recent price data for analysis"""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=f"{days}d")
            
            if data.empty:
                return None
                
            return data
        except:
            return None
    
    def check_simple_trend(self, data):
        """Simple trend analysis"""
        if len(data) < 20:
            return False, "Insufficient data"
        
        # Calculate simple moving averages
        data['MA10'] = data['Close'].rolling(10).mean()
        data['MA20'] = data['Close'].rolling(20).mean()
        
        # Check trend
        latest_ma10 = data['MA10'].iloc[-1]
        latest_ma20 = data['MA20'].iloc[-1]
        current_price = data['Close'].iloc[-1]
        
        # Simple bullish conditions
        if (current_price > latest_ma10 and 
            latest_ma10 > latest_ma20 and
            not pd.isna(latest_ma10)):
            return True, "Bullish trend detected"
        
        return False, "No clear trend"
    
    def run_demo(self):
        """Run the demo trading simulation"""
        print("QUICK GLOBAL TRADING DEMO")
        print("=" * 40)
        print("Testing live trading logic with verified tickers...")
        print()
        
        total_analyzed = 0
        total_signals = 0
        
        # Analyze each market
        for market_code, tickers in self.verified_tickers.items():
            market_config = MAJOR_MARKETS[market_code]
            print(f"\n{market_config.name} ({market_config.currency}):")
            
            market_positions = 0
            
            for ticker in tickers:
                total_analyzed += 1
                
                # Get price data
                data = self.get_price_data(ticker, 30)
                if data is None:
                    print(f"  {ticker}: No data")
                    continue
                
                current_price = data['Close'].iloc[-1]
                
                # Check if we already have this position
                if ticker in self.risk_manager.active_positions:
                    print(f"  {ticker}: Already holding")
                    continue
                
                # Simple trend analysis
                has_signal, reason = self.check_simple_trend(data)
                
                if has_signal and market_positions < self.risk_manager.max_positions_per_market:
                    try:
                        # Calculate trade using risk manager
                        trade_data = self.risk_manager.calculate_trade(
                            ticker=ticker,
                            current_price=current_price,
                            market_code=market_code,
                            stop_loss_percent=8
                        )
                        
                        # "Execute" trade
                        self.risk_manager.add_position(trade_data)
                        market_positions += 1
                        total_signals += 1
                        
                        # Log details
                        currency = market_config.currency
                        shares = trade_data['shares']
                        value_local = trade_data['trade_value']
                        value_usd = trade_data['trade_value_usd']
                        stop_loss = trade_data['stop_loss']
                        
                        print(f"  BUY {ticker}: {shares} shares at {current_price:.2f} {currency}")
                        print(f"       Value: {value_local:.2f} {currency} (${value_usd:.2f} USD)")
                        print(f"       Stop Loss: {stop_loss:.2f} {currency}")
                        
                        self.trades_log.append({
                            'ticker': ticker,
                            'market': market_config.name,
                            'currency': currency,
                            'shares': shares,
                            'price': current_price,
                            'value_usd': value_usd,
                            'stop_loss': stop_loss
                        })
                        
                    except ValueError as e:
                        print(f"  {ticker}: {str(e)[:50]}...")
                        
                else:
                    print(f"  {ticker}: {current_price:.2f} {market_config.currency} - {reason}")
        
        self.print_summary(total_analyzed, total_signals)
    
    def print_summary(self, total_analyzed, total_signals):
        """Print comprehensive summary"""
        print("\n" + "=" * 50)
        print("GLOBAL TRADING DEMO RESULTS")
        print("=" * 50)
        
        print(f"Stocks Analyzed: {total_analyzed}")
        print(f"Buy Signals: {total_signals}")
        
        if not self.trades_log:
            print("No trades executed")
            return
        
        # Portfolio summary
        exposure = self.risk_manager.get_portfolio_exposure()
        print(f"\nPortfolio Summary:")
        print(f"  Total Exposure: {exposure['exposure_percent']:.1f}%")
        print(f"  Active Positions: {exposure['active_positions']}")
        print(f"  Available Capital: ${exposure['available_capital_usd']:,.0f}")
        
        # Market breakdown
        print(f"\nMarket Breakdown:")
        for market, data in exposure['market_breakdown'].items():
            market_name = MAJOR_MARKETS[market].name
            print(f"  {market_name}: {data['percentage']:.1f}% ({data['positions']} positions)")
        
        # Currency exposure
        currency_risk = self.risk_manager.get_currency_risk_summary()
        print(f"\nCurrency Exposure:")
        print(f"  Foreign Currency Risk: {currency_risk['foreign_exposure_percentage']:.1f}%")
        print(f"  Number of Currencies: {currency_risk['number_of_currencies']}")
        
        # ASX specific trades
        asx_trades = [t for t in self.trades_log if t['ticker'].endswith('.AX')]
        if asx_trades:
            print(f"\nASX 300 Trades ({len(asx_trades)}):")
            for trade in asx_trades:
                print(f"  {trade['ticker']}: {trade['shares']} shares at {trade['price']:.2f} AUD")
                print(f"    Value: ${trade['value_usd']:.0f} USD, Stop: {trade['stop_loss']:.2f} AUD")
        
        # Top trades by value
        if len(self.trades_log) > 1:
            sorted_trades = sorted(self.trades_log, key=lambda x: x['value_usd'], reverse=True)
            print(f"\nLargest Positions:")
            for trade in sorted_trades[:3]:
                print(f"  {trade['ticker']} ({trade['market']}): ${trade['value_usd']:.0f}")


def main():
    """Main demo function"""
    print("Starting Quick Global Trading Demo...")
    print("This demo uses live data from verified working tickers")
    print()
    
    try:
        demo = QuickGlobalDemo()
        demo.run_demo()
        
        print("\nDemo completed successfully!")
        print("\nNEXT STEPS:")
        print("1. This demo shows the system working with live data")
        print("2. For full backtesting, use: python global_flag_strategy.py")
        print("3. For offline testing, use: python offline_strategy.py")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()