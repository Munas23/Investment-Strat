import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def clean_and_save_csv(file_path, symbol, folder_path):
    # Read the CSV file and set the index column
    data = pd.read_csv(file_path, index_col=0)
    
    # Rename the index to 'Date'
    data.index.name = 'Date'
    
    # Ensure numeric types for calculations
    required_columns = ['Open', 'High', 'Low', 'Close']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        print(f"Missing columns in {symbol}: {missing_columns}")
        return  # Skip this file if required columns are missing

    data[required_columns] = data[required_columns].apply(pd.to_numeric, errors='coerce')
    data.dropna(subset=required_columns, inplace=True)
    
    # Clean up the Date column
    data.index = pd.to_datetime(data.index).strftime('%Y-%m-%d')
    
    # Save the cleaned data to CSV
    clean_file_path = os.path.join(folder_path, f'{symbol}.csv')
    data.to_csv(clean_file_path)
    
    # Delete the raw data file
    os.remove(file_path)

def snapshot():
    end_date = "2024-04-30"  # Replace with your end date
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    start_date_obj = end_date_obj - timedelta(days=110)
    start_date = start_date_obj.strftime("%Y-%m-%d")
                                         
    folder_name = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
    folder_path = os.path.join('datasets/daily', folder_name)
    
    # Create the directory if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    
    with open('datasets/symbols.csv') as f:
        companies = f.read().splitlines()
        for company in companies:
            symbol = company.split(",")[0]
            raw_data_file = os.path.join('datasets', f'{symbol}.csv')
            
            # Download and save raw data
            data = yf.download(symbol, start=start_date, end=end_date)
            data.to_csv(raw_data_file)
            
            # Clean, save the data, and delete the raw data file
            clean_and_save_csv(raw_data_file, symbol, folder_path)

    return {
        "code": "success"
    }

snapshot()
