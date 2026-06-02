import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

def create_date_folder():
    """Create a folder with today's date in the same directory as this script"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent

    # Create the downloads folder in the script's directory
    today = datetime.now().strftime('%Y-%m-%d')
    folder_path = script_dir / f'downloads_{today}'
    folder_path.mkdir(exist_ok=True)
    return folder_path

def download_asx300_symbols(folder_path):
    """Download ASX300 symbols from FNArena"""
    print("Downloading ASX300 symbols...")
    url = 'https://fnarena.com/index/ASX300/'

    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table with ASX300 symbols
        # Symbols are in the second column (index 1), not the first column
        symbols = []
        table = soup.find('table')

        if table:
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cols = row.find_all('td')
                if cols and len(cols) > 1:
                    symbol = cols[1].text.strip()  # Column 2 contains the symbols
                    if symbol and len(symbol) <= 3:  # Only add 3-character symbols
                        symbols.append(symbol)

        # Save to CSV
        if symbols:
            df = pd.DataFrame({'Symbol': symbols})
            output_file = folder_path / 'ASX300_symbols.csv'
            df.to_csv(output_file, index=False)
            print(f"Saved ASX300 symbols to {output_file}")
        else:
            print("No symbols found on ASX300 page")

    except Exception as e:
        print(f"Error downloading ASX300 symbols: {e}")

def download_blackrock_excel(etf_code, download_url, folder_path):
    """Download Excel file from BlackRock and extract ticker symbols"""
    print(f"Downloading {etf_code} holdings...")

    try:
        # Download the Excel file directly
        response = requests.get(download_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        # Save the file
        output_file = folder_path / f'{etf_code}_holdings.xlsx'
        with open(output_file, 'wb') as f:
            f.write(response.content)

        print(f"Saved {etf_code} holdings to {output_file}")

        # Parse the XML-based Excel file to extract data
        try:
            # Read the XML file and strip BOM characters
            with open(output_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # Parse XML
            soup = BeautifulSoup(content, features="xml")

            # Find all rows in the worksheet
            rows = soup.find_all('Row')

            # Extract all data into a list
            all_data = []
            headers = []

            for row in rows:
                cells = row.find_all('Cell')
                row_data = []

                # Handle sparse cells (cells with Index attribute indicating position)
                cell_index = 0
                for cell in cells:
                    # Check if cell has an Index attribute (sparse data)
                    if cell.has_attr('Index'):
                        target_index = int(cell['Index']) - 1
                        # Fill gaps with empty strings
                        while cell_index < target_index:
                            row_data.append('')
                            cell_index += 1

                    data = cell.find('Data')
                    if data:
                        row_data.append(data.text.strip())
                    else:
                        row_data.append('')
                    cell_index += 1

                # Only add non-empty rows
                if row_data and any(row_data):
                    # Look for the header row by checking if it contains "Ticker"
                    if not headers and 'Ticker' in row_data:
                        headers = row_data
                    elif headers:
                        all_data.append(row_data)

            # Create DataFrame
            if headers and all_data:
                # Make sure all rows have the same number of columns as headers
                max_cols = len(headers)
                for row in all_data:
                    while len(row) < max_cols:
                        row.append('')

                df = pd.DataFrame(all_data, columns=headers)

                # Save full CSV
                full_csv_file = folder_path / f'{etf_code}_holdings.csv'
                df.to_csv(full_csv_file, index=False)
                print(f"Converted to CSV: {full_csv_file}")

                # Extract just the ticker symbols (first column named 'Ticker')
                if 'Ticker' in df.columns:
                    tickers = df['Ticker'].dropna().unique()  # Remove duplicates and NaN values

                    # Filter out invalid tickers:
                    # - Empty strings
                    # - Dates (contains '-' or '/')
                    # - Non-alphanumeric characters except '.' and '-'
                    # - Anything longer than 10 characters (most tickers are 1-5 chars)
                    # - Common currency codes and metadata
                    currency_codes = {'USD', 'AUD', 'EUR', 'GBP', 'JPY', 'CAD', 'CHF', 'CNY', 'HKD', 'NZD'}
                    valid_tickers = []
                    for t in tickers:
                        t = t.strip()
                        # Skip if empty, contains date separators, or too long
                        if not t or '/' in t or len(t) > 10:
                            continue
                        # Skip currency codes
                        if t.upper() in currency_codes:
                            continue
                        # Skip if it looks like a date (e.g., "31-Oct-2020", "Ex-Date")
                        if '-' in t and any(month in t for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec', 'Date']):
                            continue
                        # Only include if it's mostly alphanumeric (allow . and -)
                        if t.replace('.', '').replace('-', '').isalnum():
                            valid_tickers.append(t)

                    ticker_df = pd.DataFrame({'Symbol': valid_tickers})
                    ticker_file = folder_path / f'{etf_code}_symbols.csv'
                    ticker_df.to_csv(ticker_file, index=False)
                    print(f"Extracted {len(valid_tickers)} symbols to {ticker_file}")
                else:
                    print(f"Warning: 'Ticker' column not found in {etf_code} data")
            else:
                print(f"No data found in {etf_code} file")

        except Exception as e:
            print(f"Could not process {etf_code} Excel file: {e}")

    except Exception as e:
        print(f"Error downloading {etf_code}: {e}")

def main():
    """Main function to download all files"""
    print("Starting download process...")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")

    # Create folder with today's date
    folder_path = create_date_folder()
    print(f"Created folder: {folder_path}\n")

    # Download ASX300 symbols
    download_asx300_symbols(folder_path)
    print()

    # Download BlackRock ETF holdings - direct Excel download links
    blackrock_etfs = [
        ('IJR', 'https://www.blackrock.com/au/products/273426/fund/1535604546388.ajax?fileType=xls&fileName=iShares-SP-Small-Cap-ETF_fund&dataType=fund'),
        ('IVV', 'https://www.blackrock.com/au/products/275304/fund/1535604546388.ajax?fileType=xls&fileName=iShares-SP-500-ETF_fund&dataType=fund'),
        ('IJH', 'https://www.blackrock.com/au/products/273425/fund/1535604546388.ajax?fileType=xls&fileName=iShares-SP-Mid-Cap-ETF_fund&dataType=fund')
    ]

    for etf_code, download_url in blackrock_etfs:
        download_blackrock_excel(etf_code, download_url, folder_path)
        print()

    print("Download process completed!")
    print(f"All files saved to: {folder_path}")

if __name__ == '__main__':
    main()
