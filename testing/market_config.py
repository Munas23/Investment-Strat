"""
Configuration for major global markets including ASX 300
"""
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
import yfinance as yf

@dataclass
class MarketConfig:
    name: str
    country: str
    currency: str
    timezone: str
    suffix: str  # Yahoo Finance suffix for tickers
    trading_hours: Dict[str, str]  # Local trading hours
    min_price: float  # Minimum stock price filter
    market_cap_min: float  # Minimum market cap (in USD)

# Define the 10 major markets
MAJOR_MARKETS = {
    'US_SP500': MarketConfig(
        name="S&P 500",
        country="USA",
        currency="USD",
        timezone="America/New_York",
        suffix="",
        trading_hours={"open": "09:30", "close": "16:00"},
        min_price=5.0,
        market_cap_min=1e9  # $1B
    ),
    
    'US_NASDAQ': MarketConfig(
        name="NASDAQ 100",
        country="USA", 
        currency="USD",
        timezone="America/New_York",
        suffix="",
        trading_hours={"open": "09:30", "close": "16:00"},
        min_price=10.0,
        market_cap_min=5e9  # $5B
    ),
    
    'AU_ASX300': MarketConfig(
        name="ASX 300",
        country="Australia",
        currency="AUD",
        timezone="Australia/Sydney",
        suffix=".AX",
        trading_hours={"open": "10:00", "close": "16:00"},
        min_price=1.0,
        market_cap_min=5e8  # $500M USD
    ),
    
    'UK_FTSE100': MarketConfig(
        name="FTSE 100",
        country="United Kingdom",
        currency="GBP",
        timezone="Europe/London",
        suffix=".L",
        trading_hours={"open": "08:00", "close": "16:30"},
        min_price=1.0,
        market_cap_min=1e9  # $1B USD
    ),
    
    'DE_DAX': MarketConfig(
        name="DAX 40",
        country="Germany",
        currency="EUR",
        timezone="Europe/Berlin",
        suffix=".DE",
        trading_hours={"open": "09:00", "close": "17:30"},
        min_price=5.0,
        market_cap_min=1e9  # $1B USD
    ),
    
    'JP_NIKKEI': MarketConfig(
        name="Nikkei 225",
        country="Japan",
        currency="JPY",
        timezone="Asia/Tokyo",
        suffix=".T",
        trading_hours={"open": "09:00", "close": "15:00"},
        min_price=100.0,  # JPY
        market_cap_min=5e8  # $500M USD
    ),
    
    'CA_TSX': MarketConfig(
        name="TSX 60",
        country="Canada",
        currency="CAD",
        timezone="America/Toronto",
        suffix=".TO",
        trading_hours={"open": "09:30", "close": "16:00"},
        min_price=5.0,
        market_cap_min=1e9  # $1B USD
    ),
    
    'FR_CAC40': MarketConfig(
        name="CAC 40",
        country="France",
        currency="EUR",
        timezone="Europe/Paris",
        suffix=".PA",
        trading_hours={"open": "09:00", "close": "17:30"},
        min_price=5.0,
        market_cap_min=1e9  # $1B USD
    ),
    
    'HK_HSI': MarketConfig(
        name="Hang Seng Index",
        country="Hong Kong",
        currency="HKD",
        timezone="Asia/Hong_Kong",
        suffix=".HK",
        trading_hours={"open": "09:30", "close": "16:00"},
        min_price=1.0,
        market_cap_min=5e8  # $500M USD
    ),
    
    'CH_SMI': MarketConfig(
        name="Swiss Market Index",
        country="Switzerland",
        currency="CHF",
        timezone="Europe/Zurich",
        suffix=".SW",
        trading_hours={"open": "09:00", "close": "17:30"},
        min_price=1.0,
        market_cap_min=1e9  # $1B USD
    )
}

class MultiMarketDataFetcher:
    """Fetch stock lists and data from multiple major markets"""
    
    def __init__(self):
        self.markets = MAJOR_MARKETS
        
    def get_sp500_tickers(self) -> List[str]:
        """Get S&P 500 tickers"""
        try:
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url, header=0)[0]
            tickers = table['Symbol'].tolist()
            return [ticker.replace('.', '-') for ticker in tickers if len(ticker) <= 5][:100]  # Limit for testing
        except:
            return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'V', 'PG']
    
    def get_nasdaq100_tickers(self) -> List[str]:
        """Get NASDAQ 100 tickers"""
        try:
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            # Find the table with company listings
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    ticker_col = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    tickers = table[ticker_col].tolist()
                    return [str(ticker) for ticker in tickers if pd.notna(ticker)][:50]  # Limit for testing
        except:
            pass
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'NFLX']
    
    def get_asx300_tickers(self) -> List[str]:
        """Get ASX 300 tickers"""
        # Common ASX 300 stocks with .AX suffix
        asx_tickers = [
            'CBA.AX', 'BHP.AX', 'CSL.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'WES.AX', 'MQG.AX', 
            'TLS.AX', 'WOW.AX', 'RIO.AX', 'TCL.AX', 'STO.AX', 'QBE.AX', 'WDS.AX', 'COL.AX',
            'JHX.AX', 'XRO.AX', 'REA.AX', 'PME.AX', 'CAR.AX', 'LLC.AX', 'WTC.AX', 'CPU.AX',
            'APT.AX', 'ALL.AX', 'IAG.AX', 'SUN.AX', 'ASX.AX', 'GMG.AX', 'JBH.AX', 'COH.AX',
            'WPL.AX', 'QAN.AX', 'S32.AX', 'ALD.AX', 'SEK.AX', 'AMP.AX', 'ORG.AX', 'TAH.AX'
        ]
        return asx_tickers
    
    def get_ftse100_tickers(self) -> List[str]:
        """Get FTSE 100 tickers"""
        ftse_tickers = [
            'SHEL.L', 'AZN.L', 'ULVR.L', 'LSEG.L', 'BP.L', 'HSBA.L', 'VOD.L', 'GLEN.L',
            'GSK.L', 'DGE.L', 'LLOY.L', 'BARC.L', 'RIO.L', 'NG.L', 'BT-A.L', 'TSCO.L',
            'ADM.L', 'CRH.L', 'AAL.L', 'NWG.L', 'FLTR.L', 'SAGE.L', 'JD.L', 'HIK.L',
            'EXPN.L', 'OCDO.L', 'IMB.L', 'FRES.L', 'BNZL.L', 'SMT.L'
        ]
        return ftse_tickers
    
    def get_dax_tickers(self) -> List[str]:
        """Get DAX 40 tickers"""
        dax_tickers = [
            'SAP.DE', 'ASME.DE', 'SIE.DE', 'DTE.DE', 'ALV.DE', 'MUV2.DE', 'BAS.DE', 
            'BMW.DE', 'VOW3.DE', 'ADS.DE', 'DB1.DE', 'DBK.DE', 'CON.DE', 'ENR.DE',
            'BEI.DE', 'HEN3.DE', 'FRE.DE', 'IFX.DE', 'MRK.DE', 'RWE.DE'
        ]
        return dax_tickers
    
    def get_nikkei_tickers(self) -> List[str]:
        """Get Nikkei 225 tickers"""
        nikkei_tickers = [
            '7203.T', '6758.T', '6861.T', '8306.T', '9984.T', '9433.T', '6098.T', '4063.T',
            '8031.T', '6367.T', '9432.T', '4452.T', '4578.T', '6902.T', '7974.T', '9434.T',
            '8035.T', '6954.T', '4543.T', '6501.T', '8802.T', '9062.T', '8058.T', '4911.T',
            '6178.T', '4704.T', '7267.T', '2914.T', '4204.T', '9983.T'
        ]
        return nikkei_tickers
    
    def get_tsx_tickers(self) -> List[str]:
        """Get TSX 60 tickers"""
        tsx_tickers = [
            'RY.TO', 'TD.TO', 'BNS.TO', 'BMO.TO', 'CNR.TO', 'CP.TO', 'CVE.TO', 'ENB.TO',
            'TRP.TO', 'CNQ.TO', 'MFC.TO', 'SLF.TO', 'IAG.TO', 'FFH.TO', 'QSR.TO', 'ATD.TO',
            'WCN.TO', 'DOL.TO', 'CTC-A.TO', 'MG.TO', 'BTO.TO', 'K.TO', 'ABX.TO', 'FM.TO',
            'NTR.TO', 'CCO.TO', 'WFG.TO', 'WPM.TO', 'AEM.TO', 'TIH.TO'
        ]
        return tsx_tickers
    
    def get_cac40_tickers(self) -> List[str]:
        """Get CAC 40 tickers"""
        cac_tickers = [
            'MC.PA', 'ASML.PA', 'OR.PA', 'SAN.PA', 'TTE.PA', 'BNP.PA', 'SAF.PA', 'SU.PA',
            'LR.PA', 'CAP.PA', 'ACA.PA', 'KER.PA', 'AIR.PA', 'DG.PA', 'BN.PA', 'CS.PA',
            'ML.PA', 'ORA.PA', 'EL.PA', 'URW.PA', 'RNO.PA', 'GLE.PA', 'VIE.PA', 'TEP.PA',
            'DSY.PA', 'STM.PA', 'WLN.PA', 'VIV.PA', 'EN.PA', 'PUB.PA'
        ]
        return cac_tickers
    
    def get_hsi_tickers(self) -> List[str]:
        """Get Hang Seng Index tickers"""
        hsi_tickers = [
            '0700.HK', '9988.HK', '0005.HK', '0939.HK', '1299.HK', '0941.HK', '9618.HK',
            '0003.HK', '2318.HK', '1398.HK', '0016.HK', '1109.HK', '0017.HK', '0011.HK',
            '2269.HK', '0388.HK', '1113.HK', '2020.HK', '0002.HK', '1093.HK', '0883.HK',
            '0960.HK', '1810.HK', '0027.HK', '0688.HK', '1038.HK', '1972.HK', '2382.HK',
            '0175.HK', '0268.HK'
        ]
        return hsi_tickers
    
    def get_smi_tickers(self) -> List[str]:
        """Get Swiss Market Index tickers"""
        smi_tickers = [
            'NESN.SW', 'ROG.SW', 'NOVN.SW', 'ASME.SW', 'CFR.SW', 'UHR.SW', 'ABBN.SW',
            'SIKA.SW', 'GIVN.SW', 'ALC.SW', 'LONN.SW', 'SCMN.SW', 'SLHN.SW', 'HOLN.SW',
            'PGHN.SW', 'LHN.SW', 'ZURN.SW', 'CSGN.SW', 'UBS.SW', 'GEBN.SW'
        ]
        return smi_tickers
    
    def get_market_tickers(self, market_code: str, limit: int = 50) -> List[str]:
        """Get tickers for a specific market"""
        method_map = {
            'US_SP500': self.get_sp500_tickers,
            'US_NASDAQ': self.get_nasdaq100_tickers,
            'AU_ASX300': self.get_asx300_tickers,
            'UK_FTSE100': self.get_ftse100_tickers,
            'DE_DAX': self.get_dax_tickers,
            'JP_NIKKEI': self.get_nikkei_tickers,
            'CA_TSX': self.get_tsx_tickers,
            'FR_CAC40': self.get_cac40_tickers,
            'HK_HSI': self.get_hsi_tickers,
            'CH_SMI': self.get_smi_tickers
        }
        
        if market_code not in method_map:
            raise ValueError(f"Unknown market code: {market_code}")
        
        tickers = method_map[market_code]()
        return tickers[:limit]
    
    def get_all_market_tickers(self, limit_per_market: int = 20) -> Dict[str, List[str]]:
        """Get tickers from all markets"""
        all_tickers = {}
        for market_code in self.markets.keys():
            try:
                tickers = self.get_market_tickers(market_code, limit_per_market)
                all_tickers[market_code] = tickers
                print(f"✓ {market_code}: {len(tickers)} tickers")
            except Exception as e:
                print(f"✗ {market_code}: Error - {e}")
                all_tickers[market_code] = []
        
        return all_tickers
    
    def validate_tickers(self, tickers: List[str], sample_size: int = 5) -> List[str]:
        """Validate that tickers have data available"""
        if not tickers:
            return []
        
        # Test a sample of tickers
        sample_tickers = tickers[:sample_size]
        valid_tickers = []
        
        for ticker in sample_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if not hist.empty and len(hist) > 0:
                    valid_tickers.append(ticker)
            except:
                continue
        
        # If most of the sample works, assume the rest will too
        if len(valid_tickers) >= sample_size * 0.6:  # 60% success rate
            return tickers
        else:
            return valid_tickers


# Currency conversion rates (approximate - in production, use live rates)
CURRENCY_RATES = {
    'USD': 1.0,      # Base currency
    'EUR': 0.85,     # 1 USD = 0.85 EUR
    'GBP': 0.75,     # 1 USD = 0.75 GBP
    'JPY': 110.0,    # 1 USD = 110 JPY
    'CAD': 1.25,     # 1 USD = 1.25 CAD
    'AUD': 1.35,     # 1 USD = 1.35 AUD
    'CHF': 0.92,     # 1 USD = 0.92 CHF
    'HKD': 7.8,      # 1 USD = 7.8 HKD
}

def convert_to_usd(amount: float, currency: str) -> float:
    """Convert amount from given currency to USD"""
    if currency == 'USD':
        return amount
    if currency not in CURRENCY_RATES:
        raise ValueError(f"Unknown currency: {currency}")
    return amount / CURRENCY_RATES[currency]

def convert_from_usd(amount: float, currency: str) -> float:
    """Convert amount from USD to given currency"""
    if currency == 'USD':
        return amount
    if currency not in CURRENCY_RATES:
        raise ValueError(f"Unknown currency: {currency}")
    return amount * CURRENCY_RATES[currency]