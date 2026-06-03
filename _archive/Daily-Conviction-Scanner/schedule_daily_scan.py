"""
Automated Daily Scanner Scheduler
================================

Runs the daily conviction scanner automatically at specified times.
Perfect for hands-off daily analysis.
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime
import os

class DailyScanScheduler:
    """Automated scheduler for daily conviction scanning"""
    
    def __init__(self):
        """Initialize the scheduler"""
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.scanner_script = "daily_conviction_scanner.py"
        self.scan_both_markets = True  # Set to True to scan both US and ASX
        
        print("=" * 60)
        print("DAILY CONVICTION SCANNER SCHEDULER")
        print("=" * 60)
        print("Automated daily market scanning")
        print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def run_daily_scan(self, market_choice: str = "3"):
        """
        Execute the daily scanner
        
        Parameters:
        - market_choice: "1" (US), "2" (ASX), "3" (Both)
        """
        try:
            self.logger.info(f"Starting daily scan - Market choice: {market_choice}")
            
            # Check if scanner script exists
            if not os.path.exists(self.scanner_script):
                self.logger.error(f"Scanner script not found: {self.scanner_script}")
                return False
            
            # Prepare command
            cmd = ["python", self.scanner_script]
            
            # Run scanner with automated input
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Send market choice automatically
            stdout, stderr = process.communicate(input=market_choice + "\n", timeout=3600)  # 1 hour timeout
            
            if process.returncode == 0:
                self.logger.info("Daily scan completed successfully")
                self.logger.info(f"Scanner output: {stdout[-500:]}")  # Last 500 chars
                return True
            else:
                self.logger.error(f"Scanner failed with return code: {process.returncode}")
                self.logger.error(f"Error output: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Scanner timed out after 1 hour")
            process.kill()
            return False
        except Exception as e:
            self.logger.error(f"Error running daily scan: {e}")
            return False
    
    def us_market_scan(self):
        """Scan US market after market close (5:30 PM EST)"""
        self.logger.info("Executing scheduled US market scan")
        success = self.run_daily_scan("1")
        if success:
            self.logger.info("US market scan completed successfully")
        else:
            self.logger.error("US market scan failed")
    
    def asx_market_scan(self):
        """Scan ASX market after market close (5:30 PM AEST)"""
        self.logger.info("Executing scheduled ASX market scan")
        success = self.run_daily_scan("2")
        if success:
            self.logger.info("ASX market scan completed successfully")
        else:
            self.logger.error("ASX market scan failed")
    
    def both_markets_scan(self):
        """Scan both markets (recommended)"""
        self.logger.info("Executing scheduled both markets scan")
        success = self.run_daily_scan("3")
        if success:
            self.logger.info("Both markets scan completed successfully")
        else:
            self.logger.error("Both markets scan failed")
    
    def setup_schedule(self):
        """Setup the scanning schedule"""
        
        # Option 1: Scan both markets once per day (recommended)
        if self.scan_both_markets:
            # Run at 6:00 PM EST (after both US and ASX close)
            schedule.every().monday.at("18:00").do(self.both_markets_scan)
            schedule.every().tuesday.at("18:00").do(self.both_markets_scan)
            schedule.every().wednesday.at("18:00").do(self.both_markets_scan)
            schedule.every().thursday.at("18:00").do(self.both_markets_scan)
            schedule.every().friday.at("18:00").do(self.both_markets_scan)
            
            self.logger.info("Scheduled: Both markets scan at 6:00 PM EST, Monday-Friday")
        
        else:
            # Option 2: Separate schedules for each market
            # US market: Monday-Friday at 5:30 PM EST
            schedule.every().monday.at("17:30").do(self.us_market_scan)
            schedule.every().tuesday.at("17:30").do(self.us_market_scan)
            schedule.every().wednesday.at("17:30").do(self.us_market_scan)
            schedule.every().thursday.at("17:30").do(self.us_market_scan)
            schedule.every().friday.at("17:30").do(self.us_market_scan)
            
            # ASX market: Monday-Friday at 6:00 PM AEST (adjust for your timezone)
            schedule.every().monday.at("18:00").do(self.asx_market_scan)
            schedule.every().tuesday.at("18:00").do(self.asx_market_scan)
            schedule.every().wednesday.at("18:00").do(self.asx_market_scan)
            schedule.every().thursday.at("18:00").do(self.asx_market_scan)
            schedule.every().friday.at("18:00").do(self.asx_market_scan)
            
            self.logger.info("Scheduled: US scan at 5:30 PM EST, ASX scan at 6:00 PM AEST, Monday-Friday")
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        self.setup_schedule()
        
        print(f"\nScheduler running... Next scan times:")
        for job in schedule.jobs:
            print(f"  {job}")
        
        print(f"\nPress Ctrl+C to stop the scheduler")
        print("=" * 60)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
            print("\nScheduler stopped")
    
    def run_test_scan(self):
        """Run a test scan immediately"""
        print("Running test scan...")
        success = self.run_daily_scan("3")  # Both markets
        if success:
            print("✓ Test scan completed successfully")
        else:
            print("✗ Test scan failed")
        return success


def main():
    """Main scheduler function"""
    scheduler = DailyScanScheduler()
    
    print("\nDaily Scanner Scheduler Options:")
    print("1. Run scheduler (automated daily scans)")
    print("2. Run test scan now")
    print("3. Exit")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            scheduler.run_scheduler()
        elif choice == "2":
            scheduler.run_test_scan()
        elif choice == "3":
            print("Exiting...")
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()