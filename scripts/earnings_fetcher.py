"""
Earnings Calendar Fetcher
========================

Fetches earnings calendar data for next week from multiple sources
and exports to CSV format.
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

def get_yahoo_earnings_calendar():
    """
    Fetch earnings calendar from Yahoo Finance for next week
    """
    try:
        # Calculate next week dates
        today = datetime.now()
        start_date = today + timedelta(days=2)  # Monday
        end_date = start_date + timedelta(days=4)  # Friday
        
        print(f"Fetching earnings for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # List of major companies to check
        major_tickers = [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX', 'ADBE', 'CRM',
            'ORCL', 'AVGO', 'AMD', 'QCOM', 'TXN', 'INTC', 'AMAT', 'ADI', 'CSCO', 'PANW',
            
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'LLY', 'MDT', 'BMY', 'AMGN',
            
            # Financials
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'SPGI',
            
            # Consumer
            'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TJX', 'LOW', 'TGT', 'COST', 'PG',
            
            # Industrials
            'UPS', 'HON', 'BA', 'UNP', 'RTX', 'LMT', 'CAT', 'DE', 'MMM', 'GE',
            
            # ASX Major Companies
            'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'BHP.AX', 'RIO.AX', 'CSL.AX', 'WOW.AX'
        ]
        
        earnings_data = []
        
        for ticker in major_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get earnings date if available
                earnings_date = info.get('earningsDate')
                if earnings_date:
                    # Check if earnings date is next week
                    if isinstance(earnings_date, list) and len(earnings_date) > 0:
                        earnings_dt = earnings_date[0]
                        if start_date.date() <= earnings_dt.date() <= end_date.date():
                            earnings_data.append({
                                'Date': earnings_dt.strftime('%Y-%m-%d'),
                                'Ticker': ticker,
                                'Company_Name': info.get('longName', ticker),
                                'Market': 'ASX' if ticker.endswith('.AX') else 'US',
                                'Market_Cap': info.get('marketCap', 0),
                                'Sector': info.get('sector', ''),
                                'Industry': info.get('industry', ''),
                                'Expected_EPS': info.get('forwardEps', ''),
                                'Previous_EPS': info.get('trailingEps', ''),
                                'PE_Ratio': info.get('trailingPE', ''),
                                'Revenue_TTM': info.get('totalRevenue', ''),
                                'Currency': info.get('currency', 'USD')
                            })
                            print(f"Found: {ticker} - {earnings_dt.strftime('%Y-%m-%d')}")
                
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue
        
        return earnings_data
        
    except Exception as e:
        print(f"Error in get_yahoo_earnings_calendar: {e}")
        return []

def get_known_earnings():
    """
    Return known earnings from research
    """
    return [
        {
            'Date': '2025-08-25',
            'Ticker': 'PANW',
            'Company_Name': 'Palo Alto Networks Inc',
            'Market': 'US',
            'Time': 'After Close',
            'Market_Cap': 0,
            'Sector': 'Technology',
            'Industry': 'Cybersecurity',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-26',
            'Ticker': 'MDT',
            'Company_Name': 'Medtronic PLC',
            'Market': 'US',
            'Time': 'Before Open',
            'Market_Cap': 0,
            'Sector': 'Healthcare',
            'Industry': 'Medical Devices',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-26',
            'Ticker': 'HD',
            'Company_Name': 'The Home Depot Inc',
            'Market': 'US',
            'Time': 'Before Open',
            'Market_Cap': 0,
            'Sector': 'Consumer Discretionary',
            'Industry': 'Home Improvement Retail',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-27',
            'Ticker': 'NVDA',
            'Company_Name': 'NVIDIA Corporation',
            'Market': 'US',
            'Time': 'After Close',
            'Market_Cap': 0,
            'Sector': 'Technology',
            'Industry': 'Semiconductors - AI/GPU',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-27',
            'Ticker': 'RY',
            'Company_Name': 'Royal Bank of Canada',
            'Market': 'US',
            'Time': 'Before Open',
            'Market_Cap': 0,
            'Sector': 'Financial Services',
            'Industry': 'Banks',
            'Expected_EPS': '2.31',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '16034900000',
            'Currency': 'CAD'
        },
        {
            'Date': '2025-08-27',
            'Ticker': 'TJX',
            'Company_Name': 'TJX Companies Inc',
            'Market': 'US',
            'Time': 'Before Open',
            'Market_Cap': 0,
            'Sector': 'Consumer Discretionary',
            'Industry': 'Discount Retail',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-27',
            'Ticker': 'LOW',
            'Company_Name': 'Lowe\'s Companies Inc',
            'Market': 'US',
            'Time': 'Before Open',
            'Market_Cap': 0,
            'Sector': 'Consumer Discretionary',
            'Industry': 'Home Improvement Retail',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-28',
            'Ticker': 'WMT',
            'Company_Name': 'Walmart Inc',
            'Market': 'US',
            'Time': 'Before Open',
            'Market_Cap': 0,
            'Sector': 'Consumer Staples',
            'Industry': 'Discount Stores',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        },
        {
            'Date': '2025-08-28',
            'Ticker': 'INTU',
            'Company_Name': 'Intuit Inc',
            'Market': 'US',
            'Time': 'After Close',
            'Market_Cap': 0,
            'Sector': 'Technology',
            'Industry': 'Software - Application',
            'Expected_EPS': '',
            'Previous_EPS': '',
            'PE_Ratio': '',
            'Revenue_TTM': '',
            'Currency': 'USD'
        }
    ]

def main():
    """
    Main function to fetch and export earnings calendar
    """
    print("Fetching earnings calendar for next week...")
    
    # Get earnings data from multiple sources
    yahoo_earnings = get_yahoo_earnings_calendar()
    known_earnings = get_known_earnings()
    
    # Combine all earnings data
    all_earnings = yahoo_earnings + known_earnings
    
    # Remove duplicates based on ticker
    seen_tickers = set()
    unique_earnings = []
    for earning in all_earnings:
        if earning['Ticker'] not in seen_tickers:
            unique_earnings.append(earning)
            seen_tickers.add(earning['Ticker'])
    
    # Create DataFrame
    if unique_earnings:
        df = pd.DataFrame(unique_earnings)
        
        # Sort by date and ticker
        df = df.sort_values(['Date', 'Ticker'])
        
        # Format numbers
        for col in ['Market_Cap', 'Revenue_TTM']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Export to CSV
        filename = f"earnings_calendar_next_week_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\nEarnings calendar exported to: {filename}")
        print(f"Total companies found: {len(df)}")
        print("\nSummary by date:")
        print(df.groupby('Date').size().to_string())
        
        print(f"\nFirst 10 companies:")
        print(df[['Date', 'Ticker', 'Company_Name', 'Market']].head(10).to_string(index=False))
        
        return filename
    else:
        print("No earnings data found")
        return None

if __name__ == "__main__":
    main()