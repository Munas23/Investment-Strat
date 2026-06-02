import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
import json
import os
import requests
from io import StringIO
import re
import time
warnings.filterwarnings('ignore')

class TickerDownloader:
    """
    Comprehensive ticker list downloader for major stock exchanges
    """
    
    def __init__(self):
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
    
    def download_sp500_tickers(self):
        """Download complete S&P 500 ticker list from Wikipedia"""
        try:
            print("📥 Downloading S&P 500 tickers from Wikipedia...")
            
            # Read S&P 500 companies from Wikipedia
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            
            # The first table contains the companies
            sp500_table = tables[0]
            
            # Extract symbols
            symbols = sp500_table['Symbol'].tolist()
            
            # Clean symbols (remove any dots for Class A/B shares that might cause issues)
            symbols = [symbol.strip() for symbol in symbols if pd.notna(symbol)]
            
            # Save to CSV
            df = pd.DataFrame({'symbol': symbols})
            filepath = os.path.join(self.data_dir, 'sp500_symbols.csv')
            df.to_csv(filepath, index=False)
            
            print(f"✅ Downloaded {len(symbols)} S&P 500 symbols to {filepath}")
            return symbols
            
        except Exception as e:
            print(f"❌ Failed to download S&P 500 tickers: {str(e)}")
            return self._get_fallback_sp500()
    
    def download_nasdaq100_tickers(self):
        """Download NASDAQ 100 ticker list"""
        try:
            print("📥 Downloading NASDAQ 100 tickers from Wikipedia...")
            
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            
            # Find the table with companies (usually the first or second table)
            nasdaq_table = None
            for table in tables:
                if 'Symbol' in table.columns or 'Ticker' in table.columns:
                    nasdaq_table = table
                    break
            
            if nasdaq_table is None:
                print("⚠️  Could not find NASDAQ 100 table, using fallback...")
                return self._get_fallback_nasdaq100()
            
            # Extract symbols
            symbol_col = 'Symbol' if 'Symbol' in nasdaq_table.columns else 'Ticker'
            symbols = nasdaq_table[symbol_col].tolist()
            symbols = [symbol.strip() for symbol in symbols if pd.notna(symbol)]
            
            # Save to CSV
            df = pd.DataFrame({'symbol': symbols})
            filepath = os.path.join(self.data_dir, 'nasdaq100_symbols.csv')
            df.to_csv(filepath, index=False)
            
            print(f"✅ Downloaded {len(symbols)} NASDAQ 100 symbols to {filepath}")
            return symbols
            
        except Exception as e:
            print(f"❌ Failed to download NASDAQ 100 tickers: {str(e)}")
            return self._get_fallback_nasdaq100()
    
    def download_ftse100_tickers(self):
        """Download FTSE 100 ticker list"""
        try:
            print("📥 Downloading FTSE 100 tickers from Wikipedia...")
            
            url = 'https://en.wikipedia.org/wiki/FTSE_100_Index'
            tables = pd.read_html(url)
            
            # Look for the constituents table
            ftse_table = None
            for table in tables:
                if len(table.columns) >= 2 and len(table) > 50:  # Should have 100 companies
                    ftse_table = table
                    break
            
            if ftse_table is None:
                print("⚠️  Could not find FTSE 100 table, using fallback...")
                return self._get_fallback_ftse100()
            
            # Extract symbols - they should have .L suffix
            symbols = []
            for col in ftse_table.columns:
                if 'symbol' in col.lower() or 'ticker' in col.lower():
                    symbols = ftse_table[col].tolist()
                    break
            
            if not symbols:
                # Try to extract from first column or company names
                return self._get_fallback_ftse100()
            
            # Ensure .L suffix
            symbols = [symbol + '.L' if not symbol.endswith('.L') else symbol 
                      for symbol in symbols if pd.notna(symbol)]
            
            # Save to CSV
            df = pd.DataFrame({'symbol': symbols})
            filepath = os.path.join(self.data_dir, 'ftse100_symbols.csv')
            df.to_csv(filepath, index=False)
            
            print(f"✅ Downloaded {len(symbols)} FTSE 100 symbols to {filepath}")
            return symbols
            
        except Exception as e:
            print(f"❌ Failed to download FTSE 100 tickers: {str(e)}")
            return self._get_fallback_ftse100()
    
    def download_asx300_tickers(self):
        """Download ASX 300 ticker list"""
        try:
            print("📥 Downloading ASX 300 tickers...")
            
            # ASX doesn't have a simple Wikipedia table, so we'll use a comprehensive fallback
            # In practice, you'd want to scrape from ASX official site or use a financial API
            return self._get_comprehensive_asx300()
            
        except Exception as e:
            print(f"❌ Failed to download ASX 300 tickers: {str(e)}")
            return self._get_fallback_asx300()
    
    def download_russell1000_tickers(self):
        """Download Russell 1000 ticker list"""
        try:
            print("📥 Downloading Russell 1000 tickers...")
            
            # Russell 1000 is harder to get from free sources, use comprehensive fallback
            return self._get_comprehensive_russell1000()
            
        except Exception as e:
            print(f"❌ Failed to download Russell 1000 tickers: {str(e)}")
            return self._get_fallback_russell1000()
    
    def _get_fallback_sp500(self):
        """Comprehensive S&P 500 fallback list"""
        symbols = [
            'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG', 'GOOGL', 'META', 'TSLA', 'AVGO', 'WMT',
            'JPM', 'V', 'LLY', 'MA', 'NFLX', 'ORCL', 'COST', 'XOM', 'PG', 'JNJ', 'HD', 'BAC',
            'ABBV', 'KO', 'PM', 'TMUS', 'UNH', 'CRM', 'CSCO', 'WFC', 'CVX', 'IBM', 'ABT',
            'LIN', 'MCD', 'INTU', 'NOW', 'AXP', 'MS', 'DIS', 'T', 'ISRG', 'ACN', 'MRK',
            'AMD', 'RTX', 'VZ', 'BKNG', 'GS', 'UBER', 'PEP', 'ADBE', 'TXN', 'BX', 'CAT',
            'PGR', 'QCOM', 'SCHW', 'SPGI', 'BA', 'AMGN', 'BLK', 'TMO', 'BSX', 'NEE', 'HON',
            'SYK', 'C', 'TJX', 'DE', 'DHR', 'GILD', 'AMAT', 'UNP', 'PANW', 'PFE', 'ADP',
            'GEV', 'ETN', 'CMCSA', 'LOW', 'ANET', 'MU', 'CB', 'CRWD', 'VRTX', 'MMC', 'APH',
            'LMT', 'MDT', 'LRCX', 'ADI', 'COP', 'KKR', 'KLAC', 'PLD', 'ICE', 'SBUX', 'WELL',
            'MO', 'AMT', 'CME', 'BMY', 'SO', 'TT', 'WM', 'CEG', 'NKE', 'DASH', 'HCA', 'FI',
            'CTAS', 'DUK', 'EQIX', 'SHW', 'MCK', 'ELV', 'MCO', 'INTC', 'ABNB', 'PH', 'MDLZ',
            'AJG', 'CI', 'UPS', 'TDG', 'CDNS', 'CVS', 'FTNT', 'AON', 'RSG', 'ORLY', 'MMM',
            'DELL', 'APO', 'COF', 'ZTS', 'ECL', 'SNPS', 'RCL', 'GD', 'WMB', 'CL', 'MAR',
            'ITW', 'PYPL', 'HWM', 'CMG', 'PNC', 'NOC', 'MSI', 'USB', 'EMR', 'JCI', 'WDAY',
            'BK', 'COIN', 'ADSK', 'KMI', 'APD', 'EOG', 'AZO', 'TRV', 'MNST', 'AXON', 'ROP',
            'CHTR', 'SPG', 'DLR', 'CARR', 'CSX', 'HLT', 'FCX', 'VST', 'NEM', 'PAYX', 'NSC',
            'AFL', 'COR', 'ALL', 'AEP', 'MET', 'PWR', 'PSA', 'TFC', 'FDX', 'GWW', 'NXPI',
            'REGN', 'OKE', 'O', 'AIG', 'SRE', 'BDX', 'AMP', 'MPC', 'NDAQ', 'PCAR', 'CTVA',
            'TEL', 'CPRT', 'D', 'ROST', 'PSX', 'SLB', 'URI', 'LHX', 'GM', 'EW', 'CMI',
            'VRSK', 'KDP', 'KMB', 'TGT', 'KR', 'MSCI', 'GLW', 'FICO', 'CCI', 'EXC', 'FIS',
            'TTWO', 'IDXX', 'HES', 'OXY', 'KVUE', 'AME', 'FANG', 'F', 'YUM', 'VLO', 'PEG',
            'GRMN', 'CTSH', 'XEL', 'OTIS', 'CBRE', 'BKR', 'EA', 'PRU', 'DHI', 'CAH', 'RMD',
            'HIG', 'ED', 'ROK', 'TRGP', 'EBAY', 'SYY', 'ACGL', 'ETR', 'WAB', 'MCHP', 'VMC',
            'PCG', 'DXCM', 'ODFL', 'EQT', 'WEC', 'IR', 'LYV', 'EFX', 'DAL', 'VICI', 'MLM',
            'EXR', 'CSGP', 'MPWR', 'A', 'TKO', 'GEHC', 'HSY', 'IT', 'CCL', 'LULU', 'BRO',
            'KHC', 'XYL', 'WTW', 'NRG', 'STZ', 'IRM', 'GIS', 'ANSS', 'RJF', 'MTB', 'VTR',
            'AVB', 'BR', 'LEN', 'DD', 'K', 'LVS', 'WRB', 'STT', 'NUE', 'ROL', 'EXE', 'KEYS',
            'HUM', 'DTE', 'UAL', 'CNC', 'AWK', 'TSCO', 'STX', 'EQR', 'VRSN', 'IQV', 'FITB',
            'GDDY', 'AEE', 'TPL', 'PPG', 'DRI', 'PPL', 'IP', 'DG', 'VLTO', 'TYL', 'FTV',
            'SMCI', 'EL', 'MTD', 'DOV', 'FOXA', 'CHD', 'WBD', 'SBAC', 'ATO', 'ES', 'CNP',
            'STE', 'CPAY', 'HPE', 'HPQ', 'HBAN', 'CINF', 'CDW', 'FE', 'TDY', 'FOX', 'CBOE',
            'ADM', 'SW', 'SYF', 'EXPE', 'PODD', 'NTAP', 'LH', 'NVR', 'HUBB', 'NTRS', 'ON',
            'CMS', 'ULTA', 'WAT', 'AMCR', 'TROW', 'DVN', 'EIX', 'PTC', 'INVH', 'DOW', 'PHM',
            'MKC', 'STLD', 'RF', 'DLTR', 'TSN', 'IFF', 'LII', 'CTRA', 'BIIB', 'DGX', 'ERIE',
            'WSM', 'WY', 'WDC', 'LUV', 'LDOS', 'JBL', 'GPN', 'L', 'ESS', 'NI', 'ZBH', 'GEN',
            'LYB', 'MAA', 'CFG', 'KEY', 'FSLR', 'HAL', 'PKG', 'GPC', 'PFG', 'TRMB', 'FFIV',
            'HRL', 'SNA', 'RL', 'NWS', 'FDS', 'TPR', 'PNR', 'DECK', 'WST', 'MOH', 'DPZ',
            'CLX', 'NWSA', 'LNT', 'BAX', 'BBY', 'EXPD', 'J', 'ZBRA', 'EVRG', 'CF', 'BALL',
            'PAYC', 'EG', 'UDR', 'APTV', 'COO', 'HOLX', 'KIM', 'AVY', 'OMC', 'JBHT', 'IEX',
            'TER', 'TXT', 'MAS', 'INCY', 'BF.B', 'JKHY', 'REG', 'BXP', 'ALGN', 'SOLV',
            'CPT', 'BLDR', 'DOC', 'UHS', 'ARE', 'NDSN', 'JNPR', 'ALLE', 'SJM', 'BEN',
            'CHRW', 'AKAM', 'POOL', 'HST', 'MOS', 'RVTY', 'SWKS', 'CAG', 'PNW', 'MRNA',
            'TAP', 'DVA', 'AIZ', 'CPB', 'SWK', 'VTRS', 'EPAM', 'LKQ', 'GL', 'BG', 'KMX',
            'WBA', 'DAY', 'HAS', 'AOS', 'EMN', 'HII', 'NCLH', 'MGM', 'WYNN', 'HSIC', 'IPG',
            'FRT', 'MKTX', 'PARA', 'LW', 'MTCH', 'AES', 'TECH', 'GNRC', 'CRL', 'ALB', 'APA',
            'IVZ', 'MHK', 'ENPH', 'CZR'
        ]
        
        df = pd.DataFrame({'symbol': symbols})
        filepath = os.path.join(self.data_dir, 'sp500_symbols.csv')
        df.to_csv(filepath, index=False)
        print(f"✅ Created fallback S&P 500 list with {len(symbols)} symbols")
        return symbols
    
    def _get_fallback_nasdaq100(self):
        """Comprehensive NASDAQ 100 fallback list"""
        symbols = [
            'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOG', 'GOOGL', 'META', 'TSLA', 'AVGO', 'NFLX',
            'ORCL', 'COST', 'ADBE', 'PEP', 'TMUS', 'CSCO', 'AMD', 'LIN', 'TXN', 'QCOM',
            'INTU', 'ISRG', 'CMCSA', 'AMAT', 'BKNG', 'HON', 'VRTX', 'ADP', 'PANW', 'SBUX',
            'MU', 'ADI', 'GILD', 'LRCX', 'REGN', 'MDLZ', 'KLAC', 'PYPL', 'SNPS', 'CDNS',
            'MAR', 'MRVL', 'ORLY', 'FTNT', 'CSX', 'DASH', 'ASML', 'ABNB', 'CHTR', 'PCAR',
            'WDAY', 'MNST', 'FANG', 'EA', 'IDXX', 'CRWD', 'DXCM', 'CSGP', 'FAST', 'BIIB',
            'ODFL', 'EXC', 'AEP', 'GEHC', 'ON', 'KDP', 'MRNA', 'CCEP', 'KHC', 'LULU',
            'CTAS', 'XEL', 'WBD', 'DLTR', 'MCHP', 'BKR', 'ANSS', 'DDOG', 'CDW', 'ILMN',
            'VRSK', 'WBA', 'ALGN', 'CTSH', 'ZS', 'SIRI', 'NTES', 'TCOM', 'SWKS', 'MTCH',
            'SPLK', 'OKTA', 'DOCU', 'ZM', 'PDD', 'NXPI', 'SGEN', 'FISV', 'ADSK', 'LCID'
        ]
        
        df = pd.DataFrame({'symbol': symbols})
        filepath = os.path.join(self.data_dir, 'nasdaq100_symbols.csv')
        df.to_csv(filepath, index=False)
        print(f"✅ Created fallback NASDAQ 100 list with {len(symbols)} symbols")
        return symbols
    
    def _get_fallback_ftse100(self):
        """Current FTSE 100 fallback list"""
        symbols = [
            'SHEL.L', 'AZN.L', 'LLOY.L', 'ULVR.L', 'HSBA.L', 'BP.L', 'GSK.L', 'BARC.L', 'RIO.L',
            'BT-A.L', 'TSCO.L', 'LSEG.L', 'DGE.L', 'NWG.L', 'GLEN.L', 'ANTO.L', 'IAG.L', 'AAL.L',
            'EXPN.L', 'CRDA.L', 'IMB.L', 'PSON.L', 'RKT.L', 'SMDS.L', 'CPG.L', 'KGF.L', 'PSH.L',
            'SPX.L', 'SMIN.L', 'WEIR.L', 'AUTO.L', 'CCH.L', 'CNA.L', 'CTEC.L', 'EDV.L',
            'ENT.L', 'FCIT.L', 'FRES.L', 'JD.L', 'ADM.L', 'MKS.L', 'MNDI.L', 'NXT.L', 'PRU.L',
            'REL.L', 'RR.L', 'SBRY.L', 'STAN.L', 'VOD.L', 'WTB.L', 'BATS.L', 'BLND.L', 'BNZL.L',
            'DCC.L', 'DPLM.L', 'EZJ.L', 'GAW.L', 'HLN.L', 'HLMA.L', 'HL.L', 'HIK.L', 'HSX.L',
            'HWDN.L', 'IMI.L', 'INF.L', 'IHG.L', 'ICG.L', 'ITRK.L', 'LAND.L', 'LGEN.L', 'LMP.L',
            'MNG.L', 'MRO.L', 'NG.L', 'PSN.L', 'PHNX.L', 'RMV.L', 'RTO.L', 'SGE.L', 'SDR.L',
            'SMT.L', 'SGRO.L', 'SVT.L', 'SN.L', 'SSE.L', 'STJ.L', 'TW.L', 'UTG.L', 'UU.L',
            'WPP.L', 'III.L', 'AV.L', 'BA.L', 'BTRW.L', 'BEZ.L', 'BKG.L', 'CAKE.L', 'CCL.L'
        ]
        
        df = pd.DataFrame({'symbol': symbols})
        filepath = os.path.join(self.data_dir, 'ftse100_symbols.csv')
        df.to_csv(filepath, index=False)
        print(f"✅ Created fallback FTSE 100 list with {len(symbols)} symbols")
        return symbols
    
    def _get_comprehensive_asx300(self):
        """Comprehensive ASX 300 list"""
        symbols = [
            'CBA.AX', 'BHP.AX', 'CSL.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'WES.AX', 'MQG.AX', 
            'TCL.AX', 'TLS.AX', 'WOW.AX', 'FMG.AX', 'RIO.AX', 'COL.AX', 'STO.AX', 'WDS.AX',
            'REA.AX', 'JHX.AX', 'QBE.AX', 'XRO.AX', 'MIN.AX', 'COH.AX', 'ALL.AX', 'IAG.AX',
            'RMD.AX', 'CPU.AX', 'GMG.AX', 'ASX.AX', 'WTC.AX', 'S32.AX', 'SCG.AX', 'CAR.AX',
            'LLC.AX', 'MGR.AX', 'VCX.AX', 'SHL.AX', 'CWN.AX', 'SOL.AX', 'NCM.AX', 'AZJ.AX',
            'EVN.AX', 'PDN.AX', 'PLS.AX', 'LYC.AX', 'ZIP.AX', 'APX.AX', 'NXT.AX', 'WOR.AX',
            'BSL.AX', 'JBH.AX', 'CCP.AX', 'RHC.AX', 'IPL.AX', 'AMP.AX', 'SUN.AX', 'ORI.AX',
            'DXS.AX', 'CGF.AX', 'CHC.AX', 'TPG.AX', 'NEC.AX', 'ILU.AX', 'BOQ.AX', 'BEN.AX',
            'AGL.AX', 'ORG.AX', 'NST.AX', 'FLT.AX', 'IGO.AX', 'EDV.AX', 'WSP.AX', 'SDF.AX',
            'BXB.AX', 'QAN.AX', 'JHG.AX', 'TAH.AX', 'NHF.AX', 'ARG.AX', 'ALD.AX', 'DMP.AX',
            'LOV.AX', 'SGP.AX', 'TWE.AX', 'CMW.AX', 'SPK.AX', 'PNV.AX', 'HSN.AX', 'WHC.AX',
            'BLD.AX', 'URW.AX', 'IEL.AX', 'VEA.AX', 'ING.AX', 'OZL.AX', 'WPL.AX', 'ALX.AX',
            'ABP.AX', 'PWH.AX', 'VUK.AX', 'IPH.AX', 'TGR.AX', 'MLX.AX', 'LTR.AX', 'DRR.AX',
            'PRN.AX', 'BTH.AX', 'AIA.AX', 'TNE.AX', 'VRL.AX', 'PXA.AX', 'CNU.AX', 'AWC.AX',
            'RWC.AX', 'AUB.AX', 'BKW.AX', 'ALU.AX', 'HVN.AX', 'SKI.AX', 'PME.AX', 'SEK.AX',
            'NWL.AX', 'VCX.AX', 'MYR.AX', 'PMV.AX', 'BAP.AX', 'LNK.AX', 'GUD.AX', 'TUA.AX',
            'ANN.AX', 'SMR.AX', 'CDA.AX', 'MTS.AX', 'IFL.AX', 'CTD.AX', 'WAF.AX', 'RRL.AX',
            'CHN.AX', 'WEB.AX', 'CLW.AX', 'FPH.AX', 'PBH.AX', 'RED.AX', 'KGN.AX', 'INA.AX',
            'CIA.AX', 'WHF.AX', 'STO.AX', 'FBU.AX', 'PSI.AX', 'BKL.AX', 'MFG.AX', 'CIP.AX',
            'SIG.AX', 'NAN.AX', 'APA.AX', 'GXY.AX', 'FMG.AX', 'SAR.AX', 'MND.AX', 'APE.AX',
            'HT1.AX', 'CXL.AX', 'RNT.AX', 'BRG.AX', 'SBM.AX', 'PNI.AX', 'EHL.AX', 'ORA.AX',
            'GEM.AX', 'SYD.AX', 'SGR.AX', 'RFG.AX', 'CWY.AX', 'SUL.AX', 'DLX.AX', 'MPL.AX',
            'APT.AX', 'ZIP.AX', 'SZL.AX', 'HUB.AX', 'KMD.AX', 'WLE.AX', 'GWA.AX', 'CQR.AX',
            'SWM.AX', 'TNT.AX', 'NEA.AX', 'DUE.AX', 'CSR.AX', 'CAJ.AX', 'CQE.AX', 'GNC.AX',
            'AAC.AX', 'CLH.AX', 'RCG.AX', 'ALQ.AX', 'BIN.AX', 'PGH.AX', 'GOZ.AX', 'TPM.AX',
            'IDX.AX', 'PRT.AX', 'SRX.AX', 'SXY.AX', 'TGR.AX', 'BUB.AX', 'MMS.AX', 'RFF.AX',
            'BKL.AX', 'S32.AX', 'SFR.AX', 'SXY.AX', 'TNE.AX', 'TGR.AX', 'VUK.AX', 'WAF.AX', 'WOR.AX',
            'WPL.AX', 'WES.AX', 'WOW.AX', 'Z1P.AX', 'ZIM.AX', 'ZNO.AX', 'ZNO.AX', 'Z1P.AX'
        ]