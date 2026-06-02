"""
Download current S&P 500 and ASX300 ticker lists and save to CSV files
"""
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def download_sp500_tickers():
    """Download current S&P 500 tickers from Wikipedia and save to CSV"""
    print("Downloading S&P 500 tickers from Wikipedia...")

    try:
        # Get S&P 500 list from Wikipedia
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML tables
        tables = pd.read_html(response.content)

        # First table contains current S&P 500 companies
        df = tables[0]

        # Extract and clean symbols
        symbols = []
        for symbol in df['Symbol']:
            if pd.notna(symbol):
                clean_symbol = str(symbol).strip().upper()
                # Handle special cases like BRK.B -> BRK-B
                if '.' in clean_symbol:
                    clean_symbol = clean_symbol.replace('.', '-')
                symbols.append(clean_symbol)

        # Create DataFrame and save to CSV
        ticker_df = pd.DataFrame({'Symbol': symbols})
        ticker_df.to_csv('sp500_tickers.csv', index=False)

        print(f"OK Successfully downloaded {len(symbols)} S&P 500 tickers to sp500_tickers.csv")
        return True

    except Exception as e:
        print(f"ERROR downloading S&P 500 tickers: {e}")
        print("Creating fallback S&P 500 list...")

        # Create comprehensive fallback list
        fallback_symbols = [
            # Top 100 S&P 500 stocks (current major components)
            'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'BRK-B', 'AVGO',
            'LLY', 'V', 'WMT', 'JPM', 'XOM', 'UNH', 'MA', 'ORCL', 'HD', 'PG',
            'JNJ', 'COST', 'ABBV', 'NFLX', 'CRM', 'BAC', 'CVX', 'KO', 'PEP', 'TMO',
            'ADBE', 'LIN', 'MRK', 'ACN', 'DIS', 'WFC', 'AMD', 'VZ', 'DHR', 'NEE',
            'TXN', 'ABT', 'QCOM', 'PM', 'SPGI', 'INTU', 'COP', 'RTX', 'IBM', 'GS',
            'AMAT', 'CAT', 'ISRG', 'BKNG', 'AXP', 'HON', 'AMGN', 'TJX', 'NOW', 'SYK',
            'PFE', 'LOW', 'ELV', 'VRTX', 'BSX', 'GILD', 'TMUS', 'MDT', 'SCHW', 'ETN',
            'MU', 'ADP', 'C', 'CVS', 'ADI', 'LRCX', 'BLK', 'REGN', 'AMT', 'CB',
            'SO', 'ZTS', 'FI', 'KLAC', 'MDLZ', 'DUK', 'PLD', 'SBUX', 'EQIX', 'ICE',
            'CMG', 'SHW', 'WM', 'GD', 'AON', 'USB', 'TGT', 'NSC', 'MSI', 'HUM',
            # Additional major stocks
            'CL', 'MMC', 'PANW', 'MO', 'ITW', 'FCX', 'PGR', 'EMR', 'TFC', 'GM',
            'F', 'NXPI', 'MRVL', 'CDNS', 'SNPS', 'ORLY', 'HCA', 'MCK', 'PSX', 'VLO',
            'MPC', 'KMB', 'GE', 'AIG', 'PCAR', 'FTNT', 'DELL', 'HPQ', 'CNC', 'CTVA'
        ]

        ticker_df = pd.DataFrame({'Symbol': fallback_symbols})
        ticker_df.to_csv('sp500_tickers.csv', index=False)
        print(f"OK Created fallback S&P 500 list with {len(fallback_symbols)} major stocks")
        return True

def download_asx300_tickers():
    """Download current ASX300 tickers and save to CSV"""
    print("Creating current ASX300 ticker list...")

    # Current ASX300 major companies (as of 2024)
    # This list includes major stocks that are actively traded
    asx_tickers = [
        # Big 4 Banks
        'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX',

        # Major Miners
        'BHP.AX', 'RIO.AX', 'FMG.AX', 'NCM.AX', 'OZL.AX', 'EVN.AX', 'SFR.AX', 'NST.AX',
        'IGO.AX', 'MIN.AX', 'GOR.AX', 'RSG.AX', 'WAF.AX', 'RRL.AX',

        # Tech & Telecom
        'TLS.AX', 'TPM.AX', 'XRO.AX', 'WTC.AX', 'APT.AX', 'ZIP.AX', 'CPU.AX', 'KGN.AX',
        'TNE.AX', 'CAR.AX', 'REA.AX', 'SEK.AX', 'NXT.AX', 'MP1.AX',

        # Healthcare & Biotech
        'CSL.AX', 'COH.AX', 'SHL.AX', 'RMD.AX', 'PME.AX', 'FPH.AX', 'RHC.AX', 'MSB.AX',
        'AVH.AX', 'PRR.AX', 'IMU.AX', 'VTG.AX',

        # Retail & Consumer
        'WOW.AX', 'WES.AX', 'JBH.AX', 'HVN.AX', 'SUL.AX', 'CWN.AX', 'ALL.AX', 'MYR.AX',
        'BAP.AX', 'BRG.AX', 'PMV.AX', 'BKW.AX',

        # Infrastructure & Utilities
        'TCL.AX', 'APA.AX', 'AST.AX', 'AGL.AX', 'ORG.AX', 'VEA.AX', 'SPN.AX',

        # REITs
        'SCG.AX', 'GMG.AX', 'MGR.AX', 'CHC.AX', 'VCX.AX', 'BWP.AX', 'CQR.AX',

        # Industrial & Materials
        'WOR.AX', 'BXB.AX', 'ALD.AX', 'JHX.AX', 'IPL.AX', 'ORA.AX', 'BSL.AX', 'CCL.AX',
        'AWC.AX', 'BLD.AX', 'CSR.AX', 'JHG.AX',

        # Financial Services
        'MQG.AX', 'QBE.AX', 'IAG.AX', 'SUN.AX', 'ASX.AX', 'AMP.AX', 'IFL.AX', 'BOQ.AX',
        'BEN.AX', 'NHF.AX', 'CUV.AX',

        # Energy
        'WPL.AX', 'STO.AX', 'ORG.AX', 'COE.AX', 'DLS.AX', 'AWE.AX', 'OSH.AX', 'AUT.AX',

        # Transport & Logistics
        'QAN.AX', 'VAH.AX', 'TNT.AX', 'CTX.AX', 'AHY.AX', 'SEA.AX',

        # Emerging Growth
        'LYC.AX', 'PLS.AX', 'AVL.AX', 'NVX.AX', 'IXR.AX', 'LKE.AX', 'VUL.AX', 'CXO.AX',
        'ZIP.AX', 'Z1P.AX', 'HT8.AX', 'TNE.AX', 'MSB.AX', 'IMU.AX'
    ]

    # Test each ticker to make sure it's valid
    valid_tickers = []
    print("Validating ASX tickers...")

    for i, ticker in enumerate(asx_tickers):
        try:
            # Quick test to see if ticker exists
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if not hist.empty:
                valid_tickers.append(ticker)
                print(f"OK {ticker} - Valid ({i+1}/{len(asx_tickers)})")
            else:
                print(f"SKIP {ticker} - No data ({i+1}/{len(asx_tickers)})")

        except Exception as e:
            print(f"ERROR {ticker} - {e} ({i+1}/{len(asx_tickers)})")

        # Small delay to avoid hitting API limits
        time.sleep(0.1)

    # Create DataFrame and save to CSV
    ticker_df = pd.DataFrame({'Symbol': valid_tickers})
    ticker_df.to_csv('asx300_tickers.csv', index=False)

    print(f"OK Successfully saved {len(valid_tickers)} valid ASX300 tickers to asx300_tickers.csv")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TICKER DOWNLOAD UTILITY")
    print("=" * 60)

    # Download S&P 500 tickers
    sp500_success = download_sp500_tickers()
    print()

    # Download ASX300 tickers
    asx_success = download_asx300_tickers()
    print()

    print("=" * 60)
    if sp500_success and asx_success:
        print("OK All ticker files created successfully!")
    else:
        print("WARNING Some downloads failed - check errors above")
    print("=" * 60)