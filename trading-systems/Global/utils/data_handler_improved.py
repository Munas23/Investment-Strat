"""
Improved Data Handler with Better Error Handling
Fixes "no data skipping" issues with robust retry logic and individual symbol handling
"""

import pandas as pd
import numpy as np
import yfinance as yf
import time
import warnings
from typing import Dict, List, Tuple, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

class RobustDataHandler:
    """Handles data downloading with robust error handling and retry logic"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = self._setup_logging()
        self.failed_symbols = set()
        self.successful_downloads = {}
        
    def _setup_logging(self):
        """Setup logging"""
        logger = logging.getLogger("robust_data_handler")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def download_single_symbol_robust(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Download data for a single symbol with robust error handling"""
        for attempt in range(self.max_retries):
            try:
                # Clean symbol (remove problematic characters)
                clean_symbol = symbol.replace('/', '-').replace(' ', '')
                
                # Download with yfinance (more reliable than vectorbt for individual symbols)
                ticker = yf.Ticker(clean_symbol)
                data = ticker.history(start=start_date, end=end_date, auto_adjust=True, progress=False)
                
                if data.empty:
                    raise ValueError(f"No data returned for {symbol}")
                
                # Validate data quality
                if len(data) < 50:  # Need minimum data points
                    raise ValueError(f"Insufficient data for {symbol}: only {len(data)} days")
                
                # Check for reasonable price values
                if (data['Close'] <= 0).any():
                    raise ValueError(f"Invalid price data for {symbol}")
                
                # Check for excessive missing values
                missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns))
                if missing_pct > 0.2:  # More than 20% missing
                    raise ValueError(f"Too much missing data for {symbol}: {missing_pct:.1%}")
                
                # Standardize column names
                data.columns = [col.lower() for col in data.columns]
                
                # Add derived columns
                data['returns'] = data['close'].pct_change()
                data['avg_volume'] = data['volume'].rolling(20).mean()
                
                self.logger.debug(f"✓ Successfully downloaded {symbol}: {len(data)} days")
                return data
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {symbol}: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    self.failed_symbols.add(symbol)
                    self.logger.error(f"✗ Failed to download {symbol} after {self.max_retries} attempts")
        
        return None
    
    def download_symbols_parallel(self, symbols: List[str], start_date: str, end_date: str, 
                                max_workers: int = 5) -> Dict[str, pd.DataFrame]:
        """Download multiple symbols in parallel with error handling"""
        self.logger.info(f"Downloading {len(symbols)} symbols from {start_date} to {end_date}")
        
        successful_data = {}
        
        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_symbol = {
                executor.submit(self.download_single_symbol_robust, symbol, start_date, end_date): symbol
                for symbol in symbols
            }
            
            # Process completed downloads
            completed = 0
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed += 1
                
                try:
                    data = future.result(timeout=60)  # 60 second timeout per symbol
                    if data is not None:
                        successful_data[symbol] = data
                        self.successful_downloads[symbol] = len(data)
                    
                except Exception as e:
                    self.logger.error(f"Exception processing {symbol}: {e}")
                    self.failed_symbols.add(symbol)
                
                # Progress update
                if completed % 10 == 0:
                    success_rate = len(successful_data) / completed * 100
                    self.logger.info(f"Progress: {completed}/{len(symbols)} ({success_rate:.1f}% success rate)")
        
        success_count = len(successful_data)
        failure_count = len(self.failed_symbols)
        success_rate = success_count / len(symbols) * 100
        
        self.logger.info(f"Download completed: {success_count} successful, {failure_count} failed ({success_rate:.1f}% success rate)")
        
        return successful_data
    
    def download_with_chunking(self, symbols: List[str], start_date: str, end_date: str,
                             chunk_size: int = 50) -> Dict[str, pd.DataFrame]:
        """Download symbols in chunks to avoid overwhelming the API"""
        all_data = {}
        total_chunks = (len(symbols) + chunk_size - 1) // chunk_size
        
        for i, chunk_start in enumerate(range(0, len(symbols), chunk_size)):
            chunk_end = min(chunk_start + chunk_size, len(symbols))
            chunk_symbols = symbols[chunk_start:chunk_end]
            
            self.logger.info(f"Processing chunk {i + 1}/{total_chunks}: symbols {chunk_start + 1}-{chunk_end}")
            
            # Download chunk
            chunk_data = self.download_symbols_parallel(
                chunk_symbols, start_date, end_date, max_workers=3  # Lower concurrency per chunk
            )
            
            all_data.update(chunk_data)
            
            # Brief pause between chunks
            if i < total_chunks - 1:
                time.sleep(2)
        
        return all_data
    
    def get_sp500_symbols_robust(self) -> List[str]:
        """Get S&P 500 symbols with fallback options"""
        try:
            # Primary method: Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            df = tables[0]
            symbols = df['Symbol'].tolist()
            
            # Clean symbols
            clean_symbols = []
            for symbol in symbols:
                clean_symbol = symbol.replace('.', '-')
                # Filter out problematic symbols
                if not symbol.startswith('$') and len(symbol) <= 6 and symbol.isalpha():
                    clean_symbols.append(clean_symbol)
            
            self.logger.info(f"Fetched {len(clean_symbols)} S&P 500 symbols from Wikipedia")
            return clean_symbols
            
        except Exception as e:
            self.logger.error(f"Error fetching S&P 500 symbols: {e}")
            
            # Fallback: Curated list of reliable symbols
            fallback_symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT',
                'JPM', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'ADBE', 'CRM', 'NFLX',
                'CMCSA', 'PFE', 'VZ', 'KO', 'PEP', 'ABT', 'TMO', 'COST', 'ABBV', 'ACN',
                'MRK', 'DHR', 'LIN', 'NKE', 'TXN', 'AVGO', 'NEE', 'BMY', 'QCOM', 'HON',
                'UPS', 'LOW', 'LMT', 'ORCL', 'IBM', 'CVX', 'CAT', 'AMD', 'SBUX', 'MMM'
            ]
            
            self.logger.info(f"Using fallback list of {len(fallback_symbols)} symbols")
            return fallback_symbols
    
    def validate_and_clean_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Validate and clean downloaded data"""
        clean_data = {}
        removed_symbols = []
        
        for symbol, data in data_dict.items():
            try:
                # Check for minimum data requirements
                if len(data) < 50:
                    removed_symbols.append((symbol, f"Insufficient data: {len(data)} days"))
                    continue
                
                # Check for price validity
                if (data['close'] <= 0).any():
                    removed_symbols.append((symbol, "Invalid price data"))
                    continue
                
                # Check for excessive volatility (potential data errors)
                daily_returns = data['close'].pct_change().dropna()
                if (abs(daily_returns) > 0.5).any():  # 50% daily moves
                    extreme_moves = (abs(daily_returns) > 0.5).sum()
                    self.logger.warning(f"Extreme volatility in {symbol}: {extreme_moves} days with >50% moves")
                
                # Forward fill missing values (up to 5 consecutive days)
                data_cleaned = data.fillna(method='ffill', limit=5)
                
                # Drop if still too much missing data
                missing_pct = data_cleaned.isnull().sum().sum() / (len(data_cleaned) * len(data_cleaned.columns))
                if missing_pct > 0.1:
                    removed_symbols.append((symbol, f"Too much missing data: {missing_pct:.1%}"))
                    continue
                
                clean_data[symbol] = data_cleaned
                
            except Exception as e:
                removed_symbols.append((symbol, f"Validation error: {e}"))
        
        if removed_symbols:
            self.logger.info(f"Removed {len(removed_symbols)} symbols during validation:")
            for symbol, reason in removed_symbols[:10]:  # Show first 10
                self.logger.info(f"  {symbol}: {reason}")
        
        self.logger.info(f"Data validation completed: {len(clean_data)} symbols passed")
        return clean_data
    
    def get_download_summary(self) -> Dict:
        """Get summary of download results"""
        return {
            'successful_downloads': len(self.successful_downloads),
            'failed_downloads': len(self.failed_symbols),
            'success_rate': len(self.successful_downloads) / (len(self.successful_downloads) + len(self.failed_symbols)) * 100 if (len(self.successful_downloads) + len(self.failed_symbols)) > 0 else 0,
            'failed_symbols': list(self.failed_symbols),
            'avg_data_points': np.mean(list(self.successful_downloads.values())) if self.successful_downloads else 0
        }

# Example usage and testing
if __name__ == "__main__":
    # Test the robust data handler
    handler = RobustDataHandler()
    
    # Test with a small set of symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'INVALID_SYMBOL', 'TSLA']
    start_date = '2022-01-01'
    end_date = '2023-12-31'
    
    print("Testing robust data download...")
    data = handler.download_symbols_parallel(test_symbols, start_date, end_date)
    
    print(f"\nDownload Results:")
    print(f"Successful: {len(data)}")
    print(f"Failed: {len(handler.failed_symbols)}")
    
    # Validate data
    clean_data = handler.validate_and_clean_data(data)
    print(f"Clean data: {len(clean_data)}")
    
    # Summary
    summary = handler.get_download_summary()
    print(f"\nSummary: {summary}")