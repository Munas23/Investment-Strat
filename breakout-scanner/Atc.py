import pandas as pd
import os
import yfinance as yf
from datetime import datetime, timedelta

def calculate_atr(data, period=14):
    # Ensure numeric types for calculations
    data[['Open', 'High', 'Low', 'Close']] = data[['Open', 'High', 'Low', 'Close']].apply(pd.to_numeric, errors='coerce')
    data.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)
    
    data['High-Low'] = data['High'] - data['Low']
    data['High-Close'] = (data['High'] - data['Close'].shift()).abs()
    data['Low-Close'] = (data['Low'] - data['Close'].shift()).abs()
    data['True Range'] = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
    data['ATR'] = data['True Range'].rolling(window=period).mean()
    data['ATR_Percentage'] = (data['ATR'] / data['Close']) * 100
    return data

def calculate_percentage_return(data, days):
    data[f'Return_{days}'] = ((data['Close'] - data['Close'].shift(days)) / data['Close'].shift(days)) * 100
    return data

def check_atr_below_threshold(file_path, threshold=2):
    data = pd.read_csv(file_path)
    data = calculate_atr(data)
    
    # Check if ATR is calculated
    if data['ATR'].empty:
        print(f"No ATR values for {file_path}. Skipping.")
        return None, False
    
    latest_atr_percentage = data['ATR_Percentage'].iloc[-1]
    return latest_atr_percentage, latest_atr_percentage < threshold

def process_folder(folder_path, threshold=2):
    results = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            latest_atr_percentage, is_below_threshold = check_atr_below_threshold(file_path, threshold)
            
            data = pd.read_csv(file_path)
            data = calculate_percentage_return(data, 21)
            data = calculate_percentage_return(data, 35)
            data = calculate_percentage_return(data, 70)
            
            return_21 = data['Return_21'].iloc[-1] if 'Return_21' in data.columns and len(data) >= 21 else None
            return_35 = data['Return_35'].iloc[-1] if 'Return_35' in data.columns and len(data) >= 35 else None
            return_70 = data['Return_70'].iloc[-1] if 'Return_70' in data.columns and len(data) >= 70 else None
            
            results.append((filename, latest_atr_percentage, return_21, return_35, return_70, is_below_threshold))
    
    return results

def save_passing_files(results, output_file, threshold):
    passing_files = [(filename, atr_percentage, return_21, return_35, return_70) for filename, atr_percentage, return_21, return_35, return_70, is_below_threshold in results if is_below_threshold]
    df = pd.DataFrame(passing_files, columns=['Filename', 'ATR_Percentage', 'Return_21_Days', 'Return_35_Days', 'Return_70_Days'])
    df['Threshold'] = threshold
    df.to_csv(output_file, index=False)

def snapshot():
    end_date = "2024-03-03"  # Replace with your end date
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    start_date_obj = end_date_obj - timedelta(days=90)
    start_date = start_date_obj.strftime("%Y-%m-%d")
    
    folder_name = end_date_obj.strftime("%Y%m%d")
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

# Example usage:
folder_path = 'datasets/daily/20240430'  # Replace with your folder path
results = process_folder(folder_path)

output_file = 'datasets/daily/passing_files.csv'  # Replace with your output file path
threshold = 2  # Your ATR threshold
save_passing_files(results, output_file, threshold)

for filename, atr_percentage, return_21, return_35, return_70, is_below_threshold in results:
    print(f"File: {filename} - ATR_Percentage: {atr_percentage} - Return 21 Days: {return_21} - Return 35 Days: {return_35} - Return 70 Days: {return_70} - ATR below threshold: {is_below_threshold}")
