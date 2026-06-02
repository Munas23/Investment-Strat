"""
Market Data Handler for Global Multi-Market Trading System
Handles data fetching and management for ASX300, S&P500, Russell2000, FTSE, DAX
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class MarketDataHandler:
    """Handles market data fetching and management for multiple global markets"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_market_config(config_path)
        self.logger = self._setup_logging()
        self.symbol_lists = {}
        self.market_data = {}
        
    def _load_market_config(self, config_path: str) -> Dict:
        """Load market configuration"""
        if config_path:
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("market_data")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols from Wikipedia"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            df = tables[0]
            symbols = df['Symbol'].tolist()
            
            # Clean symbols
            clean_symbols = []
            for symbol in symbols:
                clean_symbol = symbol.replace('.', '-')
                clean_symbols.append(clean_symbol)
            
            self.logger.info(f"Fetched {len(clean_symbols)} S&P 500 symbols")
            return clean_symbols
            
        except Exception as e:
            self.logger.error(f"Error fetching S&P 500 symbols: {e}")
            # Fallback list
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JNJ', 'V', 'WMT']
    
    def get_asx300_symbols(self) -> List[str]:
        """Get ASX 300 symbols (using a curated list as ASX doesn't have a free API)"""
        # Major ASX 300 companies with .AX suffix
        asx300_symbols = [
            'CBA.AX', 'BHP.AX', 'CSL.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'WES.AX', 'MQG.AX',
            'TCL.AX', 'RIO.AX', 'WOW.AX', 'TLS.AX', 'GMG.AX', 'COL.AX', 'IAG.AX', 'STO.AX',
            'QBE.AX', 'WDS.AX', 'FMG.AX', 'JHX.AX', 'ALL.AX', 'ASX.AX', 'REA.AX', 'CPU.AX',
            'XRO.AX', 'CAR.AX', 'WTC.AX', 'NCM.AX', 'APT.AX', 'CWN.AX', 'S32.AX', 'AMP.AX',
            'ILU.AX', 'CCL.AX', 'JBH.AX', 'MIN.AX', 'ORA.AX', 'ORG.AX', 'EVN.AX', 'RHC.AX',
            'COH.AX', 'PME.AX', 'TPM.AX', 'SGP.AX', 'AGL.AX', 'AWC.AX', 'BEN.AX', 'SYD.AX',
            'BOQ.AX', 'BXB.AX', 'CHC.AX', 'DMP.AX', 'EDV.AX', 'GPT.AX', 'LLC.AX', 'MGR.AX'
        ]
        
        self.logger.info(f"Using {len(asx300_symbols)} ASX 300 symbols")
        return asx300_symbols
    
    def get_russell2000_symbols(self) -> List[str]:
        """Get Russell 2000 symbols (using ETF holdings as proxy)"""
        # Since Russell 2000 list is proprietary, we'll use a subset of common small caps
        russell2000_symbols = [
            'GDRX', 'PTON', 'MGNI', 'AFRM', 'OPEN', 'HOOD', 'SOFI', 'UPST', 'LCID', 'RIVN',
            'PLTR', 'COIN', 'ABNB', 'SNOW', 'NET', 'DDOG', 'CRWD', 'ZM', 'DOCU', 'OKTA',
            'TWLO', 'ROKU', 'FSLY', 'ESTC', 'PINS', 'SNAP', 'SPOT', 'SQ', 'SHOP', 'UBER',
            'LYFT', 'DASH', 'ETSY', 'CHWY', 'CHEGG', 'LMND', 'ROOT', 'WISH', 'CLOV', 'SPCE',
            'NKLA', 'QS', 'HYLN', 'RIDE', 'GOEV', 'CANOO', 'WKHS', 'BLNK', 'CHPT', 'VLDR'
        ]
        
        self.logger.info(f"Using {len(russell2000_symbols)} Russell 2000 proxy symbols")
        return russell2000_symbols
    
    def get_ftse_symbols(self) -> List[str]:
        """Get FTSE 100 symbols"""
        ftse_symbols = [
            'SHEL.L', 'AZN.L', 'ULVR.L', 'HSBA.L', 'BP.L', 'VODL.L', 'GLEN.L', 'RIO.L',
            'BARC.L', 'LLOY.L', 'NWG.L', 'BT-A.L', 'TSCO.L', 'AVST.L', 'RDSB.L', 'MNG.L',
            'CRH.L', 'LSEG.L', 'FLTR.L', 'ANTO.L', 'STAN.L', 'EXPN.L', 'RR.L', 'AAL.L',
            'REL.L', 'SGE.L', 'HL.L', 'IHG.L', 'WTB.L', 'SMDS.L', 'DGE.L', 'INF.L',
            'ITRK.L', 'IAG.L', 'KGF.L', 'FERG.L', 'PHNX.L', 'PSON.L', 'JMAT.L', 'CRDA.L',
            'SSE.L', 'NG.L', 'SBRY.L', 'BRBY.L', 'CCH.L', 'MRO.L', 'SMIN.L', 'NXT.L',
            'ADM.L', 'BDEV.L', 'BNZL.L', 'EMG.L', 'HLMA.L', 'ICP.L', 'LAND.L', 'LGEN.L'
        ]
        
        self.logger.info(f"Using {len(ftse_symbols)} FTSE 100 symbols")
        return ftse_symbols
    
    def get_dax_symbols(self) -> List[str]:
        """Get DAX symbols"""
        dax_symbols = [
            'SAP.DE', 'SIE.DE', 'ALV.DE', 'DTE.DE', 'VOW3.DE', 'MUV2.DE', 'BAS.DE', 'BMW.DE',
            'ADS.DE', 'EOAN.DE', 'IFX.DE', 'DB1.DE', 'DBK.DE', 'CON.DE', 'HEN3.DE', 'FRE.DE',
            'DAI.DE', 'LIN.DE', 'BEI.DE', 'VNA.DE', 'MRK.DE', 'RWE.DE', 'FME.DE', 'SHL.DE',
            '1COV.DE', 'MTX.DE', 'ZAL.DE', 'BNR.DE', 'QIA.DE', 'AXX.DE', 'HEI.DE', 'PUM.DE',
            'WDI.DE', 'AIR.DE', 'SRT3.DE', 'HOT.DE', 'ENR.DE', 'EVK.DE', 'TEG.DE', 'LEG.DE'
        ]
        
        self.logger.info(f"Using {len(dax_symbols)} DAX symbols")
        return dax_symbols
    
    def get_market_symbols(self, market: str) -> List[str]:
        """Get symbols for a specific market"""
        market = market.upper()
        
        if market in self.symbol_lists:
            return self.symbol_lists[market]
        
        if market == 'SP500':
            symbols = self.get_sp500_symbols()
        elif market == 'ASX300':
            symbols = self.get_asx300_symbols()
        elif market == 'RUSSELL2000':
            symbols = self.get_russell2000_symbols()
        elif market == 'FTSE':
            symbols = self.get_ftse_symbols()
        elif market == 'DAX':
            symbols = self.get_dax_symbols()
        else:
            raise ValueError(f"Unknown market: {market}")
        
        self.symbol_lists[market] = symbols
        return symbols
    
    def download_single_symbol(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Download data for a single symbol"""
        try:
            data = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if data.empty or len(data) < 50:  # Need minimum data
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            # Add basic indicators
            data['returns'] = data['close'].pct_change()
            data['ma_20'] = data['close'].rolling(20).mean()
            data['ma_50'] = data['close'].rolling(50).mean()
            data['volatility'] = data['returns'].rolling(20).std() * np.sqrt(252)
            
            return data
            
        except Exception as e:
            self.logger.warning(f"Failed to download {symbol}: {e}")
            return None
    
    def download_market_data(self, market: str, start_date: str, end_date: str, 
                           max_symbols: int = None, max_workers: int = 10) -> Dict[str, pd.DataFrame]:
        """Download data for all symbols in a market"""
        symbols = self.get_market_symbols(market)
        
        if max_symbols:
            symbols = symbols[:max_symbols]
        
        self.logger.info(f"Downloading data for {len(symbols)} {market} symbols...")
        
        market_data = {}
        failed_symbols = []
        
        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_symbol = {
                executor.submit(self.download_single_symbol, symbol, start_date, end_date): symbol
                for symbol in symbols
            }
            
            # Process completed downloads
            for i, future in enumerate(as_completed(future_to_symbol)):
                symbol = future_to_symbol[future]
                
                try:
                    data = future.result()
                    if data is not None:
                        market_data[symbol] = data
                    else:
                        failed_symbols.append(symbol)
                        
                except Exception as e:
                    self.logger.warning(f"Exception downloading {symbol}: {e}")
                    failed_symbols.append(symbol)
                
                # Progress update
                if (i + 1) % 20 == 0:
                    self.logger.info(f"Downloaded {i + 1}/{len(symbols)} symbols...")
        
        success_count = len(market_data)
        failure_count = len(failed_symbols)
        
        self.logger.info(f"Download complete: {success_count} successful, {failure_count} failed")
        
        if failed_symbols:
            self.logger.info(f"Failed symbols: {failed_symbols[:10]}...")  # Show first 10
        
        self.market_data[market] = market_data
        return market_data
    
    def get_benchmark_data(self, market: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Get benchmark data for a market"""
        if market not in self.config.get('markets', {}):
            self.logger.error(f"Unknown market: {market}")
            return None
        
        benchmark_symbol = self.config['markets'][market]['benchmark']
        
        try:
            data = yf.download(benchmark_symbol, start=start_date, end=end_date, 
                             progress=False, auto_adjust=True)
            
            if not data.empty:
                data.columns = [col.lower() for col in data.columns]
                self.logger.info(f"Downloaded benchmark data for {market} ({benchmark_symbol})")
                return data
            else:
                self.logger.error(f"No benchmark data for {market}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading benchmark for {market}: {e}")
            return None
    
    def save_market_data(self, market: str, output_dir: str):
        """Save market data to CSV files"""
        if market not in self.market_data:
            self.logger.error(f"No data available for {market}")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d")
        
        for symbol, data in self.market_data[market].items():
            # Clean symbol for filename
            clean_symbol = symbol.replace('.', '_').replace('-', '_')
            filename = f"{output_dir}/{market}_{clean_symbol}_{timestamp}.csv"
            data.to_csv(filename)
        
        self.logger.info(f"Saved {len(self.market_data[market])} {market} files to {output_dir}")
    
    def get_market_info(self, market: str) -> Dict:
        """Get market information"""
        if market in self.config.get('markets', {}):
            return self.config['markets'][market]
        return {}
    
    def validate_data_quality(self, data: pd.DataFrame, symbol: str) -> bool:
        """Validate data quality for a symbol"""
        if data.empty:
            return False
        
        # Check for minimum data points
        if len(data) < 50:
            return False
        
        # Check for excessive missing values
        missing_pct = data['close'].isna().sum() / len(data)
        if missing_pct > 0.1:  # More than 10% missing
            return False
        
        # Check for price anomalies (e.g., zero prices)
        if (data['close'] <= 0).any():
            return False
        
        # Check for extreme volatility (potential data errors)
        daily_returns = data['close'].pct_change().dropna()
        if (abs(daily_returns) > 0.5).any():  # 50% daily moves
            self.logger.warning(f"Extreme volatility detected in {symbol}")
        
        return True