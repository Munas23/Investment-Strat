"""Test different data sources for financial metrics"""
import yfinance as yf
import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import time

def test_yfinance_advanced(symbol):
    """Test yfinance for more comprehensive data"""
    print(f"\n=== YFINANCE ADVANCED: {symbol} ===")

    try:
        ticker = yf.Ticker(symbol)

        # Try different data endpoints
        info = ticker.info
        financials = ticker.financials
        quarterly_financials = ticker.quarterly_financials
        earnings = ticker.earnings
        quarterly_earnings = ticker.quarterly_earnings

        print("Basic Info Growth Data:")
        growth_keys = [k for k in info.keys() if 'growth' in k.lower() or 'revenue' in k.lower() or 'earnings' in k.lower()]
        for key in growth_keys[:10]:  # Show first 10
            print(f"  {key}: {info.get(key)}")

        print("\nQuarterly Financials Available:", not quarterly_financials.empty)
        if not quarterly_financials.empty:
            print("Quarterly Financials Shape:", quarterly_financials.shape)
            print("Recent Quarters:", list(quarterly_financials.columns)[:4])

        print("\nQuarterly Earnings Available:", not quarterly_earnings.empty)
        if not quarterly_earnings.empty:
            print("Quarterly Earnings:", quarterly_earnings.head())

            # Calculate quarterly growth if we have data
            if len(quarterly_earnings) >= 2:
                recent_revenue = quarterly_earnings['Revenue'].iloc[0] if 'Revenue' in quarterly_earnings.columns else None
                prev_revenue = quarterly_earnings['Revenue'].iloc[1] if 'Revenue' in quarterly_earnings.columns else None

                if recent_revenue and prev_revenue:
                    rev_growth = ((recent_revenue - prev_revenue) / prev_revenue) * 100
                    print(f"Calculated Revenue Growth Q/Q: {rev_growth:.1f}%")

        # Check for institutional ownership
        print(f"\nInstitutional Ownership: {info.get('heldByInsiders', 'N/A')}% (insiders)")
        print(f"Institutions: {info.get('heldByInstitutions', 'N/A')}% (institutions)")

        return True

    except Exception as e:
        print(f"Error with yfinance advanced: {e}")
        return False

def test_yahoo_finance_scraping(symbol):
    """Test scraping Yahoo Finance statistics page"""
    print(f"\n=== YAHOO FINANCE SCRAPING: {symbol} ===")

    try:
        # Clean symbol for URL (remove .AX suffix for Yahoo URL)
        clean_symbol = symbol.replace('.AX', '')
        url = f"https://finance.yahoo.com/quote/{clean_symbol}/key-statistics"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for growth data in tables
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables on statistics page")

            # Look for specific growth metrics
            page_text = soup.get_text().lower()
            if 'quarterly revenue growth' in page_text:
                print("✓ Found quarterly revenue growth data in page")
            if 'quarterly earnings growth' in page_text:
                print("✓ Found quarterly earnings growth data in page")

            return True
        else:
            print(f"Failed to access Yahoo Finance page: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error with Yahoo scraping: {e}")
        return False

def test_financial_modeling_prep():
    """Test Financial Modeling Prep API (free tier)"""
    print(f"\n=== FINANCIAL MODELING PREP API ===")

    try:
        # Free API - limited calls per day
        symbol = "AAPL"  # Test with AAPL
        api_key = "demo"  # Demo key with limited functionality

        url = f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}?period=quarter&limit=4&apikey={api_key}"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully retrieved {len(data)} quarters of data")

            if len(data) >= 2:
                recent = data[0]
                previous = data[1]

                if 'revenue' in recent and 'revenue' in previous:
                    rev_growth = ((recent['revenue'] - previous['revenue']) / previous['revenue']) * 100
                    print(f"Revenue Growth Q/Q: {rev_growth:.1f}%")

            return True
        else:
            print(f"API request failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error with Financial Modeling Prep: {e}")
        return False

def test_alpha_vantage():
    """Test Alpha Vantage API (free tier)"""
    print(f"\n=== ALPHA VANTAGE API ===")

    try:
        # Free API key (demo)
        api_key = "demo"
        symbol = "AAPL"

        url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={api_key}"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'quarterlyEarnings' in data:
                quarterly = data['quarterlyEarnings']
                print(f"✓ Found {len(quarterly)} quarters of earnings data")

                if len(quarterly) >= 2:
                    recent = quarterly[0]
                    previous = quarterly[1]
                    print(f"Recent EPS: {recent.get('reportedEPS')}")
                    print(f"Previous EPS: {previous.get('reportedEPS')}")

                return True
            else:
                print("No quarterly earnings data found")
                return False
        else:
            print(f"API request failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error with Alpha Vantage: {e}")
        return False

if __name__ == "__main__":
    test_symbols = ['AAPL', 'CBA.AX']

    print("TESTING DATA SOURCES FOR ENHANCED FINANCIAL METRICS")
    print("=" * 60)

    for symbol in test_symbols:
        print(f"\nTESTING SYMBOL: {symbol}")
        print("-" * 30)

        # Test yfinance advanced features
        yf_success = test_yfinance_advanced(symbol)

        # Test Yahoo Finance scraping
        yahoo_success = test_yahoo_finance_scraping(symbol)

        print("\n" + "="*60)

        time.sleep(2)  # Be respectful to APIs

    # Test external APIs (once)
    print("\nTESTING EXTERNAL APIs")
    print("-" * 30)

    fmp_success = test_financial_modeling_prep()
    av_success = test_alpha_vantage()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("yfinance: Available but limited quarterly growth data")
    print("Yahoo scraping: Possible but brittle")
    print("Financial Modeling Prep: Professional API with free tier")
    print("Alpha Vantage: Professional API with free tier")