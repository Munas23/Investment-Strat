"""
Test script for the enhanced risk management system
"""
import unittest
from risk_manager import RiskManager
import sys

class TestRiskManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager(
            account_balance=10000,
            default_risk_percent=2,
            max_position_size=0.10,
            max_positions=5
        )
    
    def test_valid_trade_calculation(self):
        """Test valid trade calculation"""
        trade = self.risk_manager.calculate_trade("AAPL", 150.0, risk_percent=2, stop_loss_percent=5)
        
        self.assertEqual(trade["ticker"], "AAPL")
        self.assertEqual(trade["current_price"], 150.0)
        self.assertGreater(trade["shares"], 0)
        self.assertLess(trade["trade_value"], 10000)  # Should be less than account balance
        self.assertEqual(trade["stop_loss"], 150.0 * 0.95)  # 5% stop loss
    
    def test_input_validation(self):
        """Test input validation"""
        # Test invalid ticker
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("", 150.0)
        
        # Test negative price
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("AAPL", -150.0)
        
        # Test invalid risk percent
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("AAPL", 150.0, risk_percent=60)
        
        # Test invalid stop loss percent
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("AAPL", 150.0, stop_loss_percent=60)
    
    def test_position_limits(self):
        """Test position limits"""
        # Add max positions
        for i in range(5):
            trade = self.risk_manager.calculate_trade(f"STOCK{i}", 100.0)
            self.risk_manager.add_position(trade)
        
        # Try to add one more - should fail
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("STOCK6", 100.0)
    
    def test_duplicate_position(self):
        """Test duplicate position handling"""
        trade = self.risk_manager.calculate_trade("AAPL", 150.0)
        self.risk_manager.add_position(trade)
        
        # Try to add same ticker again - should fail
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("AAPL", 160.0)
    
    def test_position_size_limit(self):
        """Test position size limit"""
        # Try to buy a very expensive stock that exceeds position limit
        with self.assertRaises(ValueError):
            self.risk_manager.calculate_trade("EXPENSIVE", 5000.0, risk_percent=10)
        
        # Try a stock that fits within position limit
        trade = self.risk_manager.calculate_trade("AFFORDABLE", 500.0, risk_percent=10)
        expected_max_value = self.risk_manager.account_balance * self.risk_manager.max_position_size
        self.assertLessEqual(trade["trade_value"], expected_max_value)
    
    def test_stop_loss_check(self):
        """Test stop loss checking"""
        trade = self.risk_manager.calculate_trade("AAPL", 100.0, stop_loss_percent=10)
        self.risk_manager.add_position(trade)
        
        # Price above stop loss - should not trigger
        self.assertFalse(self.risk_manager.check_stop_loss("AAPL", 95.0))
        
        # Price at stop loss - should trigger
        self.assertTrue(self.risk_manager.check_stop_loss("AAPL", 90.0))
        
        # Price below stop loss - should trigger
        self.assertTrue(self.risk_manager.check_stop_loss("AAPL", 85.0))
    
    def test_portfolio_exposure(self):
        """Test portfolio exposure calculation"""
        # Add some positions
        trade1 = self.risk_manager.calculate_trade("AAPL", 100.0)
        trade2 = self.risk_manager.calculate_trade("MSFT", 200.0)
        
        self.risk_manager.add_position(trade1)
        self.risk_manager.add_position(trade2)
        
        exposure = self.risk_manager.get_portfolio_exposure()
        
        self.assertEqual(exposure['active_positions'], 2)
        self.assertGreater(exposure['total_value'], 0)
        self.assertGreater(exposure['exposure_percent'], 0)
        self.assertLess(exposure['available_capital'], 10000)


def run_manual_tests():
    """Run manual tests to demonstrate functionality"""
    print("=== MANUAL TESTING OF RISK MANAGER ===\n")
    
    rm = RiskManager(account_balance=50000, default_risk_percent=2)
    
    print("1. Testing valid trade calculation:")
    try:
        trade = rm.calculate_trade("AAPL", 150.0, stop_loss_percent=8)
        print(f"   [OK] Trade calculated: {trade['shares']} shares of {trade['ticker']}")
        print(f"   [OK] Trade value: ${trade['trade_value']:.2f}")
        print(f"   [OK] Stop loss: ${trade['stop_loss']:.2f}")
        rm.add_position(trade)
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
    
    print("\n2. Testing position limits:")
    try:
        # Add 9 more positions (total 10, which is the limit)
        for i in range(9):
            trade = rm.calculate_trade(f"STOCK{i}", 100.0)
            rm.add_position(trade)
            print(f"   [OK] Added position {i+1}: {trade['ticker']}")
        
        # Try to add 11th position - should fail
        trade = rm.calculate_trade("STOCK10", 100.0)
        print("   [ERROR] Should have failed - position limit exceeded")
    except ValueError as e:
        print(f"   [OK] Correctly rejected: {e}")
    
    print("\n3. Testing portfolio exposure:")
    exposure = rm.get_portfolio_exposure()
    print(f"   [OK] Total positions: {exposure['active_positions']}")
    print(f"   [OK] Portfolio exposure: {exposure['exposure_percent']:.1f}%")
    print(f"   [OK] Available capital: ${exposure['available_capital']:,.2f}")
    
    print("\n4. Testing stop loss:")
    stop_triggered = rm.check_stop_loss("AAPL", 138.0)  # 8% below 150
    print(f"   [OK] Stop loss triggered: {stop_triggered}")
    
    print("\n5. Testing input validation:")
    try:
        rm.calculate_trade("", 150.0)  # Empty ticker
        print("   [ERROR] Should have failed - empty ticker")
    except ValueError:
        print("   [OK] Correctly rejected empty ticker")
    
    try:
        rm.calculate_trade("AAPL", -150.0)  # Negative price
        print("   [ERROR] Should have failed - negative price")
    except ValueError:
        print("   [OK] Correctly rejected negative price")
    
    print("\n=== MANUAL TESTING COMPLETED ===")


if __name__ == "__main__":
    print("Running unit tests...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50)
    
    # Run manual tests
    run_manual_tests()