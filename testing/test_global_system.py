"""
Test script for the global multi-market trading system
"""
import unittest
from multi_market_risk_manager import MultiMarketRiskManager
from market_config import MultiMarketDataFetcher, MAJOR_MARKETS, convert_to_usd, convert_from_usd
import sys

class TestGlobalSystem(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = MultiMarketRiskManager(
            account_balance_usd=100000,
            default_risk_percent=2,
            max_position_size=0.08,
            max_positions_per_market=3,
            max_total_positions=15
        )
        self.market_fetcher = MultiMarketDataFetcher()
    
    def test_currency_conversion(self):
        """Test currency conversion functions"""
        # Test USD (base currency)
        self.assertEqual(convert_to_usd(100, 'USD'), 100.0)
        self.assertEqual(convert_from_usd(100, 'USD'), 100.0)
        
        # Test EUR conversion
        eur_amount = convert_from_usd(100, 'EUR')
        usd_amount = convert_to_usd(eur_amount, 'EUR')
        self.assertAlmostEqual(usd_amount, 100.0, places=2)
    
    def test_market_detection(self):
        """Test market detection from ticker symbols"""
        # US stocks (no suffix)
        self.assertEqual(self.risk_manager.get_market_from_ticker('AAPL'), 'US_SP500')
        
        # Australian stocks (.AX suffix)
        self.assertEqual(self.risk_manager.get_market_from_ticker('CBA.AX'), 'AU_ASX300')
        
        # UK stocks (.L suffix)
        self.assertEqual(self.risk_manager.get_market_from_ticker('SHEL.L'), 'UK_FTSE100')
        
        # German stocks (.DE suffix)
        self.assertEqual(self.risk_manager.get_market_from_ticker('SAP.DE'), 'DE_DAX')
    
    def test_multi_market_position_limits(self):
        """Test position limits across markets"""
        # Add max positions to US market
        for i in range(3):
            trade = self.risk_manager.calculate_trade(f"STOCK{i}", 100.0, "US_SP500")
            self.risk_manager.add_position(trade)
        
        # Try to add one more to US - should fail
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("STOCK4", 100.0, "US_SP500")
        
        # Should still be able to add to other markets
        trade_au = self.risk_manager.calculate_trade("CBA.AX", 80.0, "AU_ASX300")
        self.risk_manager.add_position(trade_au)
        self.assertEqual(len(self.risk_manager.active_positions), 4)
    
    def test_asx300_specific_trades(self):
        """Test ASX 300 specific trading functionality"""
        # Test typical ASX stock
        trade = self.risk_manager.calculate_trade("CBA.AX", 95.50, "AU_ASX300")
        
        self.assertEqual(trade["ticker"], "CBA.AX")
        self.assertEqual(trade["market_code"], "AU_ASX300")
        self.assertEqual(trade["currency"], "AUD")
        self.assertGreater(trade["shares"], 0)
        self.assertGreater(trade["trade_value_usd"], 0)  # Should have USD equivalent
        
        # Test stop loss calculation
        expected_stop = 95.50 * 0.92  # 8% stop loss
        self.assertAlmostEqual(trade["stop_loss"], expected_stop, places=2)
    
    def test_currency_exposure_tracking(self):
        """Test currency exposure tracking"""
        # Add positions in different currencies
        trade_usd = self.risk_manager.calculate_trade("AAPL", 150.0, "US_SP500")
        trade_aud = self.risk_manager.calculate_trade("CBA.AX", 95.0, "AU_ASX300")
        trade_gbp = self.risk_manager.calculate_trade("SHEL.L", 25.0, "UK_FTSE100")
        
        self.risk_manager.add_position(trade_usd)
        self.risk_manager.add_position(trade_aud)
        self.risk_manager.add_position(trade_gbp)
        
        # Check currency exposure
        currency_risk = self.risk_manager.get_currency_risk_summary()
        
        self.assertIn('AUD', currency_risk['currency_breakdown'])
        self.assertIn('GBP', currency_risk['currency_breakdown'])
        self.assertGreaterEqual(currency_risk['number_of_currencies'], 2)  # USD positions also tracked
        self.assertGreater(currency_risk['foreign_exposure_percentage'], 0)
    
    def test_portfolio_exposure_breakdown(self):
        """Test portfolio exposure breakdown by market"""
        # Add positions to multiple markets
        trade_us = self.risk_manager.calculate_trade("AAPL", 150.0, "US_SP500")
        trade_au = self.risk_manager.calculate_trade("CBA.AX", 95.0, "AU_ASX300")
        trade_uk = self.risk_manager.calculate_trade("SHEL.L", 25.0, "UK_FTSE100")
        
        self.risk_manager.add_position(trade_us)
        self.risk_manager.add_position(trade_au)
        self.risk_manager.add_position(trade_uk)
        
        exposure = self.risk_manager.get_portfolio_exposure()
        
        # Should have breakdown for each market
        self.assertIn('US_SP500', exposure['market_breakdown'])
        self.assertIn('AU_ASX300', exposure['market_breakdown'])
        self.assertIn('UK_FTSE100', exposure['market_breakdown'])
        
        # Check position counts
        self.assertEqual(exposure['market_breakdown']['US_SP500']['positions'], 1)
        self.assertEqual(exposure['market_breakdown']['AU_ASX300']['positions'], 1)
        self.assertEqual(exposure['market_breakdown']['UK_FTSE100']['positions'], 1)
    
    def test_market_ticker_fetching(self):
        """Test fetching tickers from different markets"""
        # Test ASX 300 tickers
        asx_tickers = self.market_fetcher.get_asx300_tickers()
        self.assertGreater(len(asx_tickers), 10)
        self.assertTrue(all(ticker.endswith('.AX') for ticker in asx_tickers))
        
        # Test US tickers
        sp500_tickers = self.market_fetcher.get_sp500_tickers()
        self.assertGreater(len(sp500_tickers), 10)
        
        # Test UK tickers
        ftse_tickers = self.market_fetcher.get_ftse100_tickers()
        self.assertGreater(len(ftse_tickers), 10)
        self.assertTrue(all(ticker.endswith('.L') for ticker in ftse_tickers))


def run_manual_global_tests():
    """Run manual tests to demonstrate global functionality"""
    print("=== MANUAL TESTING OF GLOBAL SYSTEM ===\n")
    
    # Test multi-market risk manager
    rm = MultiMarketRiskManager(account_balance_usd=200000, default_risk_percent=2)
    mf = MultiMarketDataFetcher()
    
    print("1. Testing multi-market ticker fetching:")
    try:
        # Test specific markets including ASX 300
        markets_to_test = ['US_SP500', 'AU_ASX300', 'UK_FTSE100', 'DE_DAX']
        
        for market in markets_to_test:
            tickers = mf.get_market_tickers(market, 5)
            market_name = MAJOR_MARKETS[market].name
            print(f"   [OK] {market_name}: {len(tickers)} tickers")
            print(f"        Sample: {tickers[:3]}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    print("\n2. Testing ASX 300 trade calculation:")
    try:
        # Test ASX stock (Commonwealth Bank)
        trade = rm.calculate_trade("CBA.AX", 95.50, "AU_ASX300", stop_loss_percent=8)
        print(f"   [OK] ASX Trade: {trade['shares']} shares of {trade['ticker']}")
        print(f"   [OK] Value: {trade['trade_value']:.2f} {trade['currency']}")
        print(f"   [OK] USD Equivalent: ${trade['trade_value_usd']:.2f}")
        print(f"   [OK] Stop Loss: {trade['stop_loss']:.2f} {trade['currency']}")
        rm.add_position(trade)
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    print("\n3. Testing multi-currency portfolio:")
    try:
        # Add positions in different currencies
        trades = [
            ("AAPL", 150.0, "US_SP500"),     # USD
            ("SHEL.L", 25.0, "UK_FTSE100"),  # GBP
            ("SAP.DE", 120.0, "DE_DAX"),     # EUR
            ("7203.T", 2500.0, "JP_NIKKEI")  # JPY
        ]
        
        for ticker, price, market in trades:
            try:
                trade = rm.calculate_trade(ticker, price, market)
                rm.add_position(trade)
                currency = MAJOR_MARKETS[market].currency
                print(f"   [OK] Added {ticker}: {trade['shares']} shares in {currency}")
            except Exception as e:
                print(f"   [ERROR] Failed to add {ticker}: {e}")
        
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    print("\n4. Testing portfolio exposure breakdown:")
    try:
        exposure = rm.get_portfolio_exposure()
        print(f"   [OK] Total Exposure: {exposure['exposure_percent']:.1f}%")
        print(f"   [OK] Active Positions: {exposure['active_positions']}")
        
        print("   [OK] Market Breakdown:")
        for market, data in exposure['market_breakdown'].items():
            market_name = MAJOR_MARKETS[market].name
            print(f"        {market_name}: {data['percentage']:.1f}% ({data['positions']} pos)")
        
        currency_risk = rm.get_currency_risk_summary()
        print(f"   [OK] Currency Risk: {currency_risk['foreign_exposure_percentage']:.1f}% in {currency_risk['number_of_currencies']} currencies")
        
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    print("\n5. Testing market-specific limits:")
    try:
        # Try to exceed per-market limits
        positions_in_us = len([p for p in rm.active_positions.values() if p['market_code'] == 'US_SP500'])
        print(f"   [OK] Current US positions: {positions_in_us}/{rm.max_positions_per_market}")
        
        # Try to add more than limit
        for i in range(rm.max_positions_per_market - positions_in_us + 1):
            try:
                trade = rm.calculate_trade(f"TEST{i}", 50.0, "US_SP500")
                rm.add_position(trade)
                print(f"   [OK] Added TEST{i}")
            except ValueError as e:
                print(f"   [OK] Correctly rejected TEST{i}: Market limit reached")
                break
                
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    print("\n=== GLOBAL TESTING COMPLETED ===")
    print(f"Final portfolio exposure: {rm.get_portfolio_exposure()['exposure_percent']:.1f}%")
    print(f"Total positions across all markets: {len(rm.active_positions)}")


if __name__ == "__main__":
    print("Running global system unit tests...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*60)
    
    # Run manual tests
    run_manual_global_tests()