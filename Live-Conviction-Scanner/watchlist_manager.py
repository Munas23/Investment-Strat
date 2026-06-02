"""
Watchlist Manager for Live Conviction Scanner
============================================

Manages custom watchlists and provides real-time monitoring
of specific stocks based on conviction levels and alerts.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import time

class WatchlistManager:
    """
    Manages custom watchlists for live scanning and monitoring
    """
    
    def __init__(self, watchlist_file: str = "watchlists.json"):
        self.watchlist_file = watchlist_file
        self.watchlists = self.load_watchlists()
        self.alerts = []
        self.monitoring = False
        
        print("=== WATCHLIST MANAGER ===")
        print(f"Loaded {len(self.watchlists)} watchlists")
        for name, symbols in self.watchlists.items():
            print(f"  {name}: {len(symbols)} symbols")
        print("=" * 30)
    
    def load_watchlists(self) -> Dict[str, List[str]]:
        """Load watchlists from JSON file"""
        try:
            if os.path.exists(self.watchlist_file):
                with open(self.watchlist_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default watchlists
                return self.create_default_watchlists()
        except Exception as e:
            print(f"Error loading watchlists: {e}")
            return self.create_default_watchlists()
    
    def save_watchlists(self):
        """Save watchlists to JSON file"""
        try:
            with open(self.watchlist_file, 'w') as f:
                json.dump(self.watchlists, f, indent=2)
            print(f"✓ Watchlists saved to {self.watchlist_file}")
        except Exception as e:
            print(f"Error saving watchlists: {e}")
    
    def create_default_watchlists(self) -> Dict[str, List[str]]:
        """Create default watchlists"""
        default_lists = {
            "US_Tech": [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
                'ADBE', 'CRM', 'ORCL', 'AMD', 'QCOM', 'AVGO', 'TXN', 'INTC'
            ],
            "US_Blue_Chip": [
                'JNJ', 'JPM', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'DIS', 'WMT',
                'KO', 'MCD', 'VZ', 'PFE', 'CVX', 'XOM', 'T', 'IBM', 'GE', 'MMM'
            ],
            "ASX_Big_4_Banks": [
                'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX'
            ],
            "ASX_Mining": [
                'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'STO.AX', 'WDS.AX', 
                'OZL.AX', 'IGO.AX', 'EVN.AX', 'NST.AX'
            ],
            "ASX_Healthcare": [
                'CSL.AX', 'COH.AX', 'RMD.AX', 'PME.AX', 'SHL.AX', 'NAN.AX', 
                'RHC.AX', 'FPH.AX', 'API.AX'
            ],
            "ASX_Tech": [
                'APT.AX', 'XRO.AX', 'WTC.AX', 'TNE.AX', 'CPU.AX', 'KGN.AX',
                'NXT.AX', 'CAR.AX', 'NEA.AX', 'ZIP.AX'
            ],
            "High_Conviction_Candidates": [
                # This will be populated by the scanner
            ]
        }
        
        # Save default lists
        self.watchlists = default_lists
        self.save_watchlists()
        return default_lists
    
    def create_watchlist(self, name: str, symbols: List[str]):
        """Create a new watchlist"""
        self.watchlists[name] = symbols
        self.save_watchlists()
        print(f"✓ Created watchlist '{name}' with {len(symbols)} symbols")
    
    def add_to_watchlist(self, name: str, symbols: List[str]):
        """Add symbols to existing watchlist"""
        if name not in self.watchlists:
            self.watchlists[name] = []
        
        new_symbols = []
        for symbol in symbols:
            if symbol not in self.watchlists[name]:
                self.watchlists[name].append(symbol)
                new_symbols.append(symbol)
        
        if new_symbols:
            self.save_watchlists()
            print(f"✓ Added {len(new_symbols)} symbols to '{name}': {new_symbols}")
        else:
            print(f"All symbols already in '{name}' watchlist")
    
    def remove_from_watchlist(self, name: str, symbols: List[str]):
        """Remove symbols from watchlist"""
        if name not in self.watchlists:
            print(f"Watchlist '{name}' not found")
            return
        
        removed = []
        for symbol in symbols:
            if symbol in self.watchlists[name]:
                self.watchlists[name].remove(symbol)
                removed.append(symbol)
        
        if removed:
            self.save_watchlists()
            print(f"✓ Removed {len(removed)} symbols from '{name}': {removed}")
        else:
            print(f"No symbols found to remove from '{name}'")
    
    def get_watchlist(self, name: str) -> List[str]:
        """Get symbols from a watchlist"""
        return self.watchlists.get(name, [])
    
    def list_watchlists(self):
        """List all watchlists"""
        print("\nAVAILABLE WATCHLISTS:")
        print("-" * 50)
        for name, symbols in self.watchlists.items():
            print(f"{name:<25} {len(symbols):>3} symbols")
        print("-" * 50)
    
    def show_watchlist(self, name: str):
        """Show contents of a watchlist"""
        if name not in self.watchlists:
            print(f"Watchlist '{name}' not found")
            return
        
        symbols = self.watchlists[name]
        print(f"\nWATCHLIST: {name} ({len(symbols)} symbols)")
        print("-" * 40)
        
        # Display in columns
        cols = 4
        for i in range(0, len(symbols), cols):
            row = symbols[i:i+cols]
            print("  ".join(f"{sym:<10}" for sym in row))
        print("-" * 40)
    
    def search_symbol(self, search_term: str) -> Dict[str, List[str]]:
        """Search for a symbol across all watchlists"""
        search_term = search_term.upper()
        found_in = {}
        
        for name, symbols in self.watchlists.items():
            matching = [s for s in symbols if search_term in s.upper()]
            if matching:
                found_in[name] = matching
        
        return found_in
    
    def add_high_conviction_symbol(self, symbol: str, conviction_level: int, reason: str):
        """Add symbol to high conviction watchlist with metadata"""
        # Add to high conviction list
        self.add_to_watchlist("High_Conviction_Candidates", [symbol])
        
        # Create alert
        alert = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'conviction_level': conviction_level,
            'reason': reason,
            'alert_type': 'high_conviction'
        }
        self.alerts.append(alert)
        
        print(f"🎯 Added {symbol} to High Conviction list (Level {conviction_level})")
    
    def create_sector_watchlists(self):
        """Create sector-based watchlists"""
        sector_lists = {
            "US_Healthcare": [
                'JNJ', 'UNH', 'PFE', 'ABT', 'TMO', 'MRK', 'ABBV', 'BMY', 
                'AMGN', 'MDT', 'LLY', 'GILD', 'CVS', 'CI', 'HUM'
            ],
            "US_Financial": [
                'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'BLK', 'SCHW',
                'USB', 'PNC', 'TFC', 'COF', 'AIG', 'MET'
            ],
            "US_Energy": [
                'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 
                'KMI', 'OKE', 'WMB', 'FANG', 'DVN', 'HAL'
            ],
            "ASX_Retail": [
                'WOW.AX', 'COL.AX', 'WES.AX', 'JBH.AX', 'HVN.AX', 'SUL.AX',
                'LOV.AX', 'PMV.AX', 'MYR.AX', 'BBN.AX'
            ],
            "ASX_REIT": [
                'SCG.AX', 'GMG.AX', 'VCX.AX', 'DXS.AX', 'CHC.AX', 'SCP.AX',
                'MGR.AX', 'BWP.AX', 'URF.AX', 'NSR.AX'
            ]
        }
        
        for name, symbols in sector_lists.items():
            self.create_watchlist(name, symbols)
        
        print(f"✓ Created {len(sector_lists)} sector watchlists")
    
    def export_watchlist(self, name: str, filename: str = None):
        """Export watchlist to CSV"""
        if name not in self.watchlists:
            print(f"Watchlist '{name}' not found")
            return
        
        symbols = self.watchlists[name]
        df = pd.DataFrame({'symbol': symbols})
        
        if not filename:
            filename = f"watchlist_{name}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        df.to_csv(filename, index=False)
        print(f"✓ Exported watchlist '{name}' to {filename}")
    
    def import_watchlist(self, name: str, filename: str):
        """Import watchlist from CSV"""
        try:
            df = pd.read_csv(filename)
            
            # Try different column names
            symbol_col = None
            for col in ['symbol', 'Symbol', 'SYMBOL', 'ticker', 'Ticker']:
                if col in df.columns:
                    symbol_col = col
                    break
            
            if not symbol_col:
                print(f"Error: No symbol column found in {filename}")
                return
            
            symbols = df[symbol_col].dropna().tolist()
            symbols = [str(s).strip().upper() for s in symbols]  # Clean symbols
            
            self.create_watchlist(name, symbols)
            print(f"✓ Imported {len(symbols)} symbols to watchlist '{name}'")
            
        except Exception as e:
            print(f"Error importing watchlist: {e}")
    
    def get_alerts(self, hours_back: int = 24) -> List[Dict]:
        """Get recent alerts"""
        cutoff = datetime.now() - timedelta(hours=hours_back)
        return [alert for alert in self.alerts if alert['timestamp'] > cutoff]
    
    def print_alerts(self, hours_back: int = 24):
        """Print recent alerts"""
        alerts = self.get_alerts(hours_back)
        
        if not alerts:
            print(f"No alerts in the last {hours_back} hours")
            return
        
        print(f"\nRECENT ALERTS (Last {hours_back} hours):")
        print("-" * 60)
        
        for alert in sorted(alerts, key=lambda x: x['timestamp'], reverse=True):
            timestamp = alert['timestamp'].strftime("%H:%M:%S")
            print(f"{timestamp} | {alert['symbol']:<8} | Level {alert['conviction_level']} | {alert['reason']}")
        
        print("-" * 60)


def main():
    """Interactive watchlist management"""
    manager = WatchlistManager()
    
    while True:
        print("\nWATCHLIST MANAGER")
        print("1. List watchlists")
        print("2. Show watchlist")
        print("3. Create watchlist")
        print("4. Add symbols to watchlist")
        print("5. Remove symbols from watchlist")
        print("6. Search symbol")
        print("7. Create sector watchlists")
        print("8. Export watchlist")
        print("9. Import watchlist")
        print("10. Show alerts")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            manager.list_watchlists()
        
        elif choice == '2':
            name = input("Watchlist name: ").strip()
            manager.show_watchlist(name)
        
        elif choice == '3':
            name = input("New watchlist name: ").strip()
            symbols_input = input("Symbols (comma separated): ").strip()
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
            if symbols:
                manager.create_watchlist(name, symbols)
        
        elif choice == '4':
            name = input("Watchlist name: ").strip()
            symbols_input = input("Symbols to add (comma separated): ").strip()
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
            if symbols:
                manager.add_to_watchlist(name, symbols)
        
        elif choice == '5':
            name = input("Watchlist name: ").strip()
            symbols_input = input("Symbols to remove (comma separated): ").strip()
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
            if symbols:
                manager.remove_from_watchlist(name, symbols)
        
        elif choice == '6':
            search_term = input("Search for symbol: ").strip()
            results = manager.search_symbol(search_term)
            if results:
                print(f"\nFound '{search_term}' in:")
                for watchlist, symbols in results.items():
                    print(f"  {watchlist}: {symbols}")
            else:
                print(f"'{search_term}' not found in any watchlist")
        
        elif choice == '7':
            manager.create_sector_watchlists()
        
        elif choice == '8':
            name = input("Watchlist name to export: ").strip()
            filename = input("Filename (optional): ").strip() or None
            manager.export_watchlist(name, filename)
        
        elif choice == '9':
            name = input("New watchlist name: ").strip()
            filename = input("CSV filename: ").strip()
            manager.import_watchlist(name, filename)
        
        elif choice == '10':
            hours = input("Hours back (default 24): ").strip()
            hours_back = int(hours) if hours.isdigit() else 24
            manager.print_alerts(hours_back)
        
        elif choice == '0':
            break
        
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()