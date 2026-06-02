"""
Offline/Cached Global Strategy for when data download issues occur
"""
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from multi_market_risk_manager import MultiMarketRiskManager
from market_config import MAJOR_MARKETS

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

class OfflineGlobalStrategy:
    """
    Simplified global strategy that works with cached/synthetic data
    when live data download fails
    """
    
    def __init__(self):
        self.risk_manager = MultiMarketRiskManager(
            account_balance_usd=100000,
            default_risk_percent=2,
            max_position_size=0.08,
            max_positions_per_market=3,
            max_total_positions=15
        )
        
        # Cached/sample data for testing
        self.sample_stocks = self.create_sample_data()
        self.trades_log = []
        
    def create_sample_data(self):
        """Create sample stock data for testing when downloads fail"""
        
        sample_stocks = {
            # US Stocks
            'AAPL': {'price': 175.50, 'market': 'US_SP500', 'currency': 'USD'},
            'MSFT': {'price': 338.20, 'market': 'US_SP500', 'currency': 'USD'},
            'GOOGL': {'price': 125.40, 'market': 'US_NASDAQ', 'currency': 'USD'},
            
            # ASX 300 Stocks (Key requirement)
            'CBA.AX': {'price': 95.50, 'market': 'AU_ASX300', 'currency': 'AUD'},
            'BHP.AX': {'price': 42.30, 'market': 'AU_ASX300', 'currency': 'AUD'},
            'CSL.AX': {'price': 285.20, 'market': 'AU_ASX300', 'currency': 'AUD'},
            'WBC.AX': {'price': 22.15, 'market': 'AU_ASX300', 'currency': 'AUD'},
            'ANZ.AX': {'price': 25.80, 'market': 'AU_ASX300', 'currency': 'AUD'},
            
            # UK Stocks
            'SHEL.L': {'price': 25.50, 'market': 'UK_FTSE100', 'currency': 'GBP'},
            'AZN.L': {'price': 110.25, 'market': 'UK_FTSE100', 'currency': 'GBP'},
            
            # German Stocks
            'SAP.DE': {'price': 120.40, 'market': 'DE_DAX', 'currency': 'EUR'},
            'SIE.DE': {'price': 155.80, 'market': 'DE_DAX', 'currency': 'EUR'},
            
            # Japanese Stocks
            '7203.T': {'price': 2450.0, 'market': 'JP_NIKKEI', 'currency': 'JPY'},
            '6758.T': {'price': 8920.0, 'market': 'JP_NIKKEI', 'currency': 'JPY'}
        }
        
        return sample_stocks
    
    def generate_sample_price_data(self, base_price, days=60):
        """Generate synthetic price data for testing"""
        np.random.seed(42)  # For reproducible results
        
        # Generate random walk with slight upward bias
        returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
        prices = [base_price]
        
        for ret in returns:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))  # Ensure positive prices
        
        # Create DataFrame
        dates = pd.date_range(end=datetime.now(), periods=len(prices), freq='D')
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': [int(np.random.normal(1000000, 200000)) for _ in prices]
        }, index=dates)
        
        # Ensure high >= close >= low
        df['high'] = df[['high', 'close']].max(axis=1)
        df['low'] = df[['low', 'close']].min(axis=1)
        
        return df
    
    def check_flag_pattern_offline(self, df, min_gain=0.25):
        """Simplified flag pattern check using synthetic data"""
        if len(df) < 30:
            return False, 0
        
        # Look for trend over last 30 days
        recent_data = df.tail(30)
        high_max = recent_data['high'].max()
        low_min = recent_data['low'].min()
        
        if low_min <= 0:
            return False, 0
        
        trend_gain = (high_max / low_min) - 1
        return trend_gain > min_gain, trend_gain
    
    def calculate_moving_averages_offline(self, df):
        """Calculate moving averages for synthetic data"""
        if len(df) < 50:
            return None, None, None
        
        ma_fast = df['close'].rolling(window=10).mean()
        ma_medium = df['close'].rolling(window=20).mean()
        ma_slow = df['close'].rolling(window=50).mean()
        
        return ma_fast, ma_medium, ma_slow
    
    def check_ma_alignment_offline(self, ma_fast, ma_medium, ma_slow):
        """Check MA alignment for synthetic data"""
        if ma_fast is None or len(ma_fast) == 0:
            return False
        
        try:
            latest_fast = ma_fast.iloc[-1]
            latest_medium = ma_medium.iloc[-1]
            latest_slow = ma_slow.iloc[-1]
            
            if pd.isna(latest_fast) or pd.isna(latest_medium) or pd.isna(latest_slow):
                return False
            
            return (latest_fast > latest_medium * 0.98 and 
                   latest_medium > latest_slow * 0.98)
        except:
            return False
    
    def run_offline_simulation(self):
        """Run offline simulation using sample data"""
        print("🔄 Running Offline Global Trading Simulation")
        print("=" * 50)
        
        # Simulate trading across multiple days
        for day in range(10):  # Simulate 10 trading days
            print(f"\n📅 Day {day + 1}")
            
            # Check each sample stock
            for ticker, stock_info in self.sample_stocks.items():
                try:
                    # Generate sample price data
                    df = self.generate_sample_price_data(stock_info['price'])
                    current_price = df['close'].iloc[-1]
                    
                    # Skip if we already have this position
                    if ticker in self.risk_manager.active_positions:
                        continue
                    
                    # Check entry conditions
                    has_flag, trend_gain = self.check_flag_pattern_offline(df)
                    if not has_flag:
                        continue
                    
                    ma_fast, ma_medium, ma_slow = self.calculate_moving_averages_offline(df)
                    if not self.check_ma_alignment_offline(ma_fast, ma_medium, ma_slow):
                        continue
                    
                    # Try to place trade
                    try:
                        trade_data = self.risk_manager.calculate_trade(
                            ticker=ticker,
                            current_price=current_price,
                            market_code=stock_info['market'],
                            stop_loss_percent=8
                        )
                        
                        # Simulate trade execution
                        self.risk_manager.add_position(trade_data)
                        
                        market_name = MAJOR_MARKETS[stock_info['market']].name
                        currency = stock_info['currency']
                        
                        print(f"   ✅ BUY {ticker} ({market_name}): {trade_data['shares']} shares at {current_price:.2f} {currency}")
                        print(f"      Value: {trade_data['trade_value']:.2f} {currency} (${trade_data['trade_value_usd']:.2f} USD)")
                        
                        # Log trade
                        self.trades_log.append({
                            'day': day + 1,
                            'ticker': ticker,
                            'action': 'BUY',
                            'price': current_price,
                            'shares': trade_data['shares'],
                            'market': market_name,
                            'currency': currency
                        })
                        
                    except Exception as e:
                        print(f"   ❌ {ticker}: {str(e)[:60]}...")
                        
                except Exception as e:
                    continue
            
            # Show portfolio status
            exposure = self.risk_manager.get_portfolio_exposure()
            print(f"   💼 Portfolio Exposure: {exposure['exposure_percent']:.1f}%")
            print(f"   📊 Active Positions: {exposure['active_positions']}")
            
            # Stop if we reach position limits
            if exposure['active_positions'] >= self.risk_manager.max_total_positions:
                print("   🛑 Maximum positions reached")
                break
    
    def print_results(self):
        """Print simulation results"""
        print("\n" + "=" * 50)
        print("📊 OFFLINE SIMULATION RESULTS")
        print("=" * 50)
        
        if not self.trades_log:
            print("❌ No trades executed")
            return
        
        # Trade summary
        trades_df = pd.DataFrame(self.trades_log)
        print(f"✅ Total Trades: {len(trades_df)}")
        
        # Market breakdown
        print("\n🌍 TRADES BY MARKET:")
        market_counts = trades_df['market'].value_counts()
        for market, count in market_counts.items():
            print(f"   {market}: {count} trades")
        
        # ASX specific
        asx_trades = trades_df[trades_df['ticker'].str.contains('.AX')]
        if not asx_trades.empty:
            print(f"\n🇦🇺 ASX 300 TRADES: {len(asx_trades)}")
            for _, trade in asx_trades.iterrows():
                print(f"   {trade['ticker']}: {trade['shares']} shares at {trade['price']:.2f} {trade['currency']}")
        
        # Portfolio summary
        exposure = self.risk_manager.get_portfolio_exposure()
        print(f"\n💼 FINAL PORTFOLIO:")
        print(f"   Total Exposure: {exposure['exposure_percent']:.1f}%")
        print(f"   Active Positions: {exposure['active_positions']}")
        
        print("\n🌍 MARKET EXPOSURE:")
        for market, data in exposure['market_breakdown'].items():
            market_name = MAJOR_MARKETS[market].name
            print(f"   {market_name}: {data['percentage']:.1f}% ({data['positions']} positions)")
        
        # Currency exposure
        currency_risk = self.risk_manager.get_currency_risk_summary()
        print(f"\n💱 CURRENCY EXPOSURE:")
        print(f"   Foreign Currency: {currency_risk['foreign_exposure_percentage']:.1f}%")
        print(f"   Number of Currencies: {currency_risk['number_of_currencies']}")


def main():
    """Main function for offline simulation"""
    print("🌍 OFFLINE GLOBAL TRADING STRATEGY")
    print("This simulation uses sample/synthetic data when live data is unavailable")
    print("=" * 70)
    
    try:
        strategy = OfflineGlobalStrategy()
        strategy.run_offline_simulation()
        strategy.print_results()
        
        print("\n✅ Offline simulation completed successfully!")
        print("\n📋 NEXT STEPS:")
        print("1. Check internet connection for live data")
        print("2. Try: python simple_global_test.py")
        print("3. If data works, try: python global_flag_strategy.py")
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()