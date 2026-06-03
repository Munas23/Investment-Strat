"""
Live Market Scanner - Interactive Brokers Integration
===================================================

Real-time market scanning using Interactive Brokers API to identify stocks
meeting our 5-Level Conviction criteria in today's markets.

Features:
- Real-time fundamental and technical screening
- 5-level conviction scoring
- US and ASX market support
- Live alerts for high-conviction setups
- Export capabilities for analysis

Requirements:
- Interactive Brokers TWS or IB Gateway running
- Paid market data subscription
- ib_insync library for API connection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import asyncio
from typing import Dict, List, Optional, Tuple
import logging

# Interactive Brokers API
try:
    from ib_insync import IB, Stock, util
    IB_AVAILABLE = True
    print("Interactive Brokers API available")
except ImportError:
    IB_AVAILABLE = False
    print("WARNING: ib_insync not installed. Install with: pip install ib_insync")

# Our conviction scoring system
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class LiveConvictionScanner:
    """
    Live market scanner using Interactive Brokers for real-time conviction analysis
    """
    
    def __init__(self, host='127.0.0.1', port=7496, client_id=1):
        """
        Initialize IB connection
        
        Parameters:
        - host: IB Gateway/TWS host (default: localhost)
        - port: IB Gateway port (7497) or TWS port (7496)
        - client_id: Unique client identifier
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        
        # Scanner settings
        self.fundamental_threshold = 60.0
        self.min_price = 5.0  # Minimum stock price
        self.min_volume = 100000  # Minimum daily volume
        self.max_market_cap = 100e9  # $100B max market cap
        
        # Live scanning results
        self.scan_results = []
        self.conviction_alerts = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('live_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        print("=== LIVE CONVICTION SCANNER ===")
        print("Real-time market scanning with Interactive Brokers")
        print(f"Connection: {host}:{port} (Client ID: {client_id})")
        print("=" * 50)
    
    def connect(self):
        """Connect to Interactive Brokers"""
        try:
            if not IB_AVAILABLE:
                raise Exception("ib_insync not available - install with: pip install ib_insync")
            
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            self.logger.info(f"Connected to Interactive Brokers at {self.host}:{self.port}")
            
            # Test connection
            positions = self.ib.positions()
            self.logger.info(f"Connection verified - Found {len(positions)} positions")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to IB: {e}")
            self.logger.error("Make sure TWS or IB Gateway is running and accepting API connections")
            return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            self.logger.info("Disconnected from Interactive Brokers")
    
    def get_market_data(self, symbol: str, exchange: str = "SMART") -> Optional[Dict]:
        """
        Get real-time market data for a symbol
        
        Parameters:
        - symbol: Stock symbol (e.g., 'AAPL', 'CBA')
        - exchange: Exchange (SMART, NYSE, NASDAQ, ASX)
        """
        try:
            if not self.connected:
                self.logger.warning("Not connected to IB")
                return None
            
            # Create contract
            if '.AX' in symbol:
                # Australian stock
                symbol_clean = symbol.replace('.AX', '')
                contract = Stock(symbol_clean, 'ASX', 'AUD')
                exchange = 'ASX'
            else:
                # US stock
                contract = Stock(symbol, exchange, 'USD')
            
            # Get contract details
            self.ib.qualifyContracts(contract)
            
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(1)  # Wait for data
            
            # Get historical data for technical analysis
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr='200 D',
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            if not bars:
                self.logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = util.df(bars)
            if df.empty:
                return None
            
            # Current market data
            current_data = {
                'symbol': symbol,
                'exchange': exchange,
                'price': ticker.last if ticker.last and ticker.last > 0 else ticker.close,
                'volume': ticker.volume if ticker.volume else 0,
                'bid': ticker.bid if ticker.bid else 0,
                'ask': ticker.ask if ticker.ask else 0,
                'last_update': datetime.now(),
                'historical_data': df
            }
            
            # Cancel market data to avoid overload
            self.ib.cancelMktData(contract)
            
            return current_data
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength score (0-100)"""
        try:
            if len(df) < 150:
                return 0
            
            current = df.iloc[-1]
            
            # Calculate moving averages
            df['ma_21'] = df['close'].rolling(21).mean()
            df['ma_50'] = df['close'].rolling(50).mean()
            df['ma_150'] = df['close'].rolling(150).mean()
            
            ma_21 = df['ma_21'].iloc[-1]
            ma_50 = df['ma_50'].iloc[-1]
            ma_150 = df['ma_150'].iloc[-1]
            
            # Calculate momentum
            momentum_20d = ((current['close'] / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
            momentum_50d = ((current['close'] / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
            
            # Calculate highs
            high_50 = df['high'].rolling(50).max().iloc[-1]
            
            score = 0
            
            # Price above moving averages (40 points)
            if not pd.isna(ma_21) and current['close'] > ma_21:
                score += 10
            if not pd.isna(ma_50) and current['close'] > ma_50:
                score += 15
            if not pd.isna(ma_150) and current['close'] > ma_150:
                score += 15
            
            # Moving average alignment (20 points)
            if not pd.isna(ma_21) and not pd.isna(ma_50) and ma_21 > ma_50:
                score += 10
            if not pd.isna(ma_50) and not pd.isna(ma_150) and ma_50 > ma_150:
                score += 10
            
            # Momentum (20 points)
            if momentum_20d > 5:
                score += 10
            if momentum_50d > 10:
                score += 10
            
            # Near highs (20 points)
            if not pd.isna(high_50):
                distance_from_high = (current['close'] / high_50 - 1) * 100
                if distance_from_high > -10:  # Within 10% of 50-day high
                    score += 20
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 0
    
    def generate_conviction_signal(self, market_data: Dict) -> Tuple[int, str, Dict]:
        """
        Generate real-time conviction signal (0-5)
        
        Returns:
        - conviction_level: 0-5 
        - reason: Explanation
        - details: Scoring breakdown
        """
        try:
            df = market_data['historical_data']
            current_price = market_data['price']
            current_volume = market_data['volume']
            
            if len(df) < 150:
                return 0, "Insufficient historical data", {}
            
            # Base requirement: Strong trend (score >60)
            trend_strength = self.calculate_trend_strength(df)
            if trend_strength < 60:
                return 0, f"Weak trend: {trend_strength:.0f}", {'trend_strength': trend_strength}
            
            conviction = 0
            details = {'trend_strength': trend_strength}
            
            # Factor 1: Breakout power (0-25 points)
            high_20 = df['high'].rolling(20).max().iloc[-1]
            high_50 = df['high'].rolling(50).max().iloc[-1]
            
            breakout_points = 0
            if current_price > high_20 * 1.01:  # 1% above 20-day high
                breakout_points += 15
                if current_price > high_50 * 1.02:  # 2% above 50-day high
                    breakout_points += 10
            
            conviction += breakout_points
            details['breakout_power'] = breakout_points
            details['high_20'] = high_20
            details['high_50'] = high_50
            
            # Factor 2: Volume confirmation (0-30 points)
            volume_avg = df['volume'].rolling(20).mean().iloc[-1]
            volume_surge = current_volume / volume_avg if volume_avg > 0 and current_volume > 0 else 0
            
            volume_points = 0
            if volume_surge > 2.0:  # 2x volume
                volume_points = 30
            elif volume_surge > 1.5:  # 1.5x volume
                volume_points = 20
            elif volume_surge > 1.2:  # 1.2x volume
                volume_points = 10
            
            conviction += volume_points
            details['volume_surge'] = volume_surge
            details['volume_points'] = volume_points
            
            # Factor 3: Momentum alignment (0-25 points)
            momentum_5d = ((current_price / df['close'].iloc[-6]) - 1) * 100 if len(df) >= 6 else 0
            momentum_20d = ((current_price / df['close'].iloc[-21]) - 1) * 100 if len(df) >= 21 else 0
            momentum_50d = ((current_price / df['close'].iloc[-51]) - 1) * 100 if len(df) >= 51 else 0
            
            momentum_points = 0
            if momentum_5d > 1:
                momentum_points += 5
            if momentum_20d > 5:
                momentum_points += 10
            if momentum_50d > 10:
                momentum_points += 10
            
            conviction += momentum_points
            details['momentum_5d'] = momentum_5d
            details['momentum_20d'] = momentum_20d
            details['momentum_50d'] = momentum_50d
            details['momentum_points'] = momentum_points
            
            # Factor 4: Trend quality bonus (0-20 points)
            trend_bonus = min(20, int((trend_strength - 60) / 2))
            conviction += trend_bonus
            details['trend_bonus'] = trend_bonus
            details['total_conviction'] = conviction
            
            # Convert to conviction level (0-100 -> 0-5)
            if conviction >= 85:
                level = 5
                reason = f"MAX conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            elif conviction >= 70:
                level = 4
                reason = f"HIGH conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            elif conviction >= 55:
                level = 3
                reason = f"STANDARD conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            elif conviction >= 40:
                level = 2
                reason = f"LOW conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            elif conviction >= 25:
                level = 1
                reason = f"MINIMAL conviction: {conviction}, trend: {trend_strength:.0f}, vol: {volume_surge:.1f}x"
            else:
                level = 0
                reason = f"No conviction: {conviction}, trend: {trend_strength:.0f}"
            
            return level, reason, details
            
        except Exception as e:
            self.logger.error(f"Error generating conviction signal: {e}")
            return 0, f"Error: {e}", {}
    
    def scan_symbol(self, symbol: str, exchange: str = "SMART") -> Optional[Dict]:
        """
        Scan a single symbol for conviction signals
        """
        try:
            self.logger.info(f"Scanning {symbol}...")
            
            # Get market data
            market_data = self.get_market_data(symbol, exchange)
            if not market_data:
                return None
            
            # Basic filters
            price = market_data['price']
            volume = market_data['volume']
            
            if price < self.min_price:
                self.logger.debug(f"{symbol}: Price too low (${price:.2f})")
                return None
            
            # Check average volume from historical data instead of current tick volume
            df = market_data['historical_data']
            if len(df) >= 20:
                avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                if avg_volume < self.min_volume:
                    self.logger.debug(f"{symbol}: Average volume too low ({avg_volume:,.0f})")
                    return None
            
            # Generate conviction signal
            conviction_level, reason, details = self.generate_conviction_signal(market_data)
            
            # Create result
            result = {
                'symbol': symbol,
                'exchange': exchange,
                'timestamp': datetime.now(),
                'price': price,
                'volume': volume,
                'conviction_level': conviction_level,
                'conviction_reason': reason,
                'conviction_details': details,
                'position_size_pct': {
                    1: 20, 2: 25, 3: 30, 4: 35, 5: 40
                }.get(conviction_level, 0)
            }
            
            # Log significant findings
            if conviction_level >= 3:
                self.logger.info(f"HIGH CONVICTION: {symbol} - Level {conviction_level} - {reason}")
                self.conviction_alerts.append(result)
            elif conviction_level >= 1:
                self.logger.info(f"Conviction: {symbol} - Level {conviction_level}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            return None
    
    def scan_market(self, symbols: List[str], exchange: str = "SMART") -> List[Dict]:
        """
        Scan multiple symbols for conviction signals
        """
        results = []
        total_symbols = len(symbols)
        
        self.logger.info(f"Starting market scan of {total_symbols} symbols...")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                self.logger.info(f"Progress: {i}/{total_symbols} - Scanning {symbol}")
                
                result = self.scan_symbol(symbol, exchange)
                if result:
                    results.append(result)
                    self.scan_results.append(result)
                
                # Rate limiting - don't overwhelm the API
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                self.logger.info("Scan interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in market scan for {symbol}: {e}")
                continue
        
        self.logger.info(f"Market scan complete - {len(results)} symbols processed")
        return results
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbol list"""
        try:
            # Major S&P 500 stocks for live scanning
            sp500_sample = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'BAC',
                'ABBV', 'PFE', 'AVGO', 'KO', 'LLY', 'WMT', 'MRK', 'PEP', 'TMO',
                'COST', 'DIS', 'ABT', 'ADBE', 'CRM', 'ACN', 'MCD', 'VZ', 'NFLX',
                'WFC', 'NEE', 'NKE', 'BMY', 'QCOM', 'T', 'UPS', 'LOW', 'TXN',
                'LIN', 'ORCL', 'HON', 'PM', 'COP', 'IBM', 'RTX', 'AMD', 'SBUX'
            ]
            return sp500_sample
        except Exception as e:
            self.logger.error(f"Error getting S&P 500 symbols: {e}")
            return []
    
    def get_asx300_symbols(self) -> List[str]:
        """Get ASX300 symbol list"""
        try:
            # Major ASX300 stocks for live scanning
            asx300_sample = [
                'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX',  # Big 4 banks
                'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX',  # Mining
                'CSL.AX', 'COH.AX', 'RMD.AX', 'PME.AX',  # Healthcare
                'WOW.AX', 'COL.AX', 'WES.AX', 'JBH.AX',  # Retail
                'TLS.AX', 'REA.AX', 'WTC.AX', 'TNE.AX',  # Tech/Telecom
                'QBE.AX', 'IAG.AX', 'SUN.AX', 'QAN.AX',  # Industrials
                'SCG.AX', 'GMG.AX', 'TCL.AX', 'ALL.AX'   # REITs/Others
            ]
            return asx300_sample
        except Exception as e:
            self.logger.error(f"Error getting ASX300 symbols: {e}")
            return []
    
    def export_results(self, filename: str = None) -> str:
        """Export scan results to CSV"""
        try:
            if not self.scan_results:
                self.logger.warning("No scan results to export")
                return ""
            
            # Create DataFrame
            export_data = []
            for result in self.scan_results:
                row = {
                    'timestamp': result['timestamp'],
                    'symbol': result['symbol'],
                    'exchange': result['exchange'],
                    'price': result['price'],
                    'volume': result['volume'],
                    'conviction_level': result['conviction_level'],
                    'position_size_pct': result['position_size_pct'],
                    'conviction_reason': result['conviction_reason']
                }
                
                # Add conviction details
                details = result.get('conviction_details', {})
                row.update({
                    'trend_strength': details.get('trend_strength', 0),
                    'breakout_power': details.get('breakout_power', 0),
                    'volume_surge': details.get('volume_surge', 0),
                    'momentum_points': details.get('momentum_points', 0),
                    'total_conviction': details.get('total_conviction', 0)
                })
                
                export_data.append(row)
            
            df = pd.DataFrame(export_data)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"live_conviction_scan_{timestamp}.csv"
            
            # Export
            df.to_csv(filename, index=False)
            self.logger.info(f"Exported {len(df)} results to {filename}")
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting results: {e}")
            return ""
    
    def print_summary(self):
        """Print scan summary"""
        if not self.scan_results:
            print("No scan results available")
            return
        
        # Summary statistics
        total_scanned = len(self.scan_results)
        conviction_counts = {}
        for result in self.scan_results:
            level = result['conviction_level']
            conviction_counts[level] = conviction_counts.get(level, 0) + 1
        
        print("\n" + "=" * 60)
        print("LIVE CONVICTION SCAN SUMMARY")
        print("=" * 60)
        print(f"Total symbols scanned: {total_scanned}")
        print(f"Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("CONVICTION LEVEL DISTRIBUTION:")
        for level in range(6):
            count = conviction_counts.get(level, 0)
            pct = count / total_scanned * 100 if total_scanned > 0 else 0
            position_pct = {0: 0, 1: 20, 2: 25, 3: 30, 4: 35, 5: 40}.get(level, 0)
            print(f"  Level {level} ({position_pct:2d}% position): {count:3d} stocks ({pct:5.1f}%)")
        
        # High conviction alerts
        high_conviction = [r for r in self.scan_results if r['conviction_level'] >= 3]
        if high_conviction:
            print(f"\nHIGH CONVICTION ALERTS ({len(high_conviction)} stocks):")
            print("-" * 60)
            for result in sorted(high_conviction, key=lambda x: x['conviction_level'], reverse=True):
                print(f"  {result['symbol']:<8} Level {result['conviction_level']} - ${result['price']:>8.2f} - {result['conviction_reason']}")
        
        print("=" * 60)


def main():
    """Main scanning function"""
    scanner = LiveConvictionScanner()
    
    try:
        # Connect to Interactive Brokers
        print("Connecting to Interactive Brokers...")
        connected = scanner.connect()
        
        if not connected:
            print("Failed to connect to Interactive Brokers")
            print("Make sure TWS or IB Gateway is running with API enabled")
            return
        
        # Choose market to scan
        print("\nSelect market to scan:")
        print("1. US Market (S&P 500 sample)")
        print("2. ASX Market (ASX300 sample)")
        print("3. Both markets")
        
        choice = input("Enter choice (1-3): ").strip()
        
        symbols_to_scan = []
        if choice in ['1', '3']:
            symbols_to_scan.extend(scanner.get_sp500_symbols())
            print(f"Added {len(scanner.get_sp500_symbols())} US symbols")
        
        if choice in ['2', '3']:
            symbols_to_scan.extend(scanner.get_asx300_symbols())
            print(f"Added {len(scanner.get_asx300_symbols())} ASX symbols")
        
        if not symbols_to_scan:
            print("No symbols to scan")
            return
        
        print(f"\nStarting live scan of {len(symbols_to_scan)} symbols...")
        print("This may take several minutes depending on your data subscription...")
        
        # Perform scan
        results = scanner.scan_market(symbols_to_scan)
        
        # Print summary
        scanner.print_summary()
        
        # Export results
        filename = scanner.export_results()
        if filename:
            print(f"\nResults exported to: {filename}")
        
        # Show top conviction picks
        top_picks = [r for r in results if r['conviction_level'] >= 2]
        top_picks.sort(key=lambda x: x['conviction_level'], reverse=True)
        
        if top_picks:
            print(f"\nTOP CONVICTION PICKS ({len(top_picks)} stocks):")
            print("-" * 80)
            print(f"{'Symbol':<8} {'Level':<6} {'Price':<10} {'Volume':<12} {'Reason':<40}")
            print("-" * 80)
            for pick in top_picks[:10]:  # Top 10
                print(f"{pick['symbol']:<8} {pick['conviction_level']:<6} ${pick['price']:<9.2f} {pick['volume']:<12,} {pick['conviction_reason'][:40]}")
    
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error in main scan: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always disconnect
        scanner.disconnect()
        print("Disconnected from Interactive Brokers")


if __name__ == "__main__":
    if not IB_AVAILABLE:
        print("Interactive Brokers API not available")
        print("Install with: pip install ib_insync")
        exit(1)
    
    print("LIVE MARKET SCANNER")
    print("Real-time conviction analysis using Interactive Brokers")
    print("Make sure TWS or IB Gateway is running with API enabled")
    print()
    
    # Run main function
    main()