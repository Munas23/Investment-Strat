"""
Consolidation Conviction Strategy - ASX300 Implementation
========================================================

Post-move consolidation pattern detection strategy for ASX300 using the proven 5LC backtesting framework.
Targets Australian stocks AFTER big moves during consolidation periods with:
1. 30%+ 3-6 month performance requirement
2. Low/contracting ATR analysis 
3. Reduced recent momentum weighting
4. Professional risk management optimized for consolidation patterns
5. Market health overlay using VAS.AX (ASX300 ETF)
"""

import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.entities import Asset
import os

# Import enhanced analysis
try:
    import pyfolio as pf
    PYFOLIO_AVAILABLE = True
    print("Pyfolio-reloaded loaded successfully")
except ImportError:
    PYFOLIO_AVAILABLE = False
    print("WARNING: Pyfolio-reloaded not installed. Install with: pip install pyfolio-reloaded")

warnings.filterwarnings('ignore')

class ConsolidationConvictionASX300Strategy(Strategy):
    """
    Consolidation Conviction Strategy for ASX300 based on 5LC framework
    
    Features:
    1. Post-move consolidation pattern detection for Australian stocks
    2. 30%+ 3-6 month performance requirement
    3. ATR contraction analysis for consolidation identification  
    4. Dynamic position sizing (15%-35% based on conviction)
    5. Enhanced risk management optimized for consolidation patterns
    6. Market health overlay using VAS.AX moving averages
    """
    
    def initialize(self):
        """Initialize strategy parameters - based on 5LC ASX300 structure"""
        self.sleeptime = "1D"
        
        # Consolidation-specific parameters for ASX300
        self.max_positions = 8
        self.min_position_size = 0.15  # 15% minimum 
        self.max_position_size = 0.35  # 35% maximum
        self.stop_loss_pct = 0.08  # 8% stop (tighter for consolidation)
        self.profit_target = 0.50  # 40% target (realistic for post-move)
        
        # Consolidation criteria
        self.min_3month_gain = 30.0  # Minimum 30% gain over 3-6 months
        self.min_price = 1.00  # Lower minimum for ASX (many stocks under $5)
        self.min_avg_volume = 50000  # Lower volume requirement for ASX
        
        # Risk management for consolidation patterns
        self.trail_profit_trigger = 0.15  # Earlier trailing (15% vs 20%)
        self.trail_percent = 0.10  # Tighter trailing (10% vs 12%)
        self.max_hold_days = 180  # Shorter holds (6 months vs 12)
        
        # Market health overlay parameters - ASX specific
        self.market_health_symbol = "VAS.AX"  # ASX300 ETF
        self.market_health_data = None
        self.current_market_regime = "NORMAL"  # WEAK, NORMAL, STRONG
        
        # Universe - ASX300 stocks
        self.asx300_symbols = self.get_asx300_symbols()
        
        # Performance tracking for Pyfolio (same as 5LC)
        self.daily_returns = []
        self.portfolio_values = []
        self.benchmark_returns = []
        self.dates = []
        
        # Trading tracking (same structure as 5LC)
        self.consolidation_leaders = []
        self.last_screening_date = None
        self.screening_frequency = 14  # Screen every 2 weeks
        self.trades_log = []
        self.position_tracker = {}
        
        # Debug tracking (same as 5LC)
        self.debug_stats = {
            'screening_attempts': 0,
            'consolidation_patterns_found': 0,
            'technical_signals_checked': 0,
            'conviction_signals_generated': 0,
            'orders_attempted': 0,
            'orders_successful': 0,
            'market_regime_changes': 0
        }
        
        self.log_message("=== CONSOLIDATION CONVICTION ASX300 STRATEGY ===")
        self.log_message(f"Universe: ASX300 ({len(self.asx300_symbols)} stocks)")
        self.log_message(f"Market Health Indicator: {self.market_health_symbol}")
        self.log_message(f"Focus: Post-move consolidation patterns")
        self.log_message(f"Min 3-6M gain: {self.min_3month_gain}%")
        self.log_message(f"Pyfolio Integration: {'Enabled' if PYFOLIO_AVAILABLE else 'Disabled'}")
        self.log_message("=" * 70)
    
    def get_asx300_symbols(self):
        """Get comprehensive ASX300 symbol list"""
        try:
            # Comprehensive ASX300 symbols with .AX suffix for Yahoo Finance
            # Based on actual ASX300 constituents (representative sample)
            asx300_comprehensive = [
                # ASX20 - Top 20 largest companies
                'CBA.AX', 'BHP.AX', 'CSL.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'WOW.AX', 'MQG.AX',
                'RIO.AX', 'WES.AX', 'FMG.AX', 'TCL.AX', 'TLS.AX', 'XRO.AX', 'COH.AX', 'RMD.AX',
                'STO.AX', 'QBE.AX', 'REA.AX', 'JBH.AX',
                
                # ASX21-50 - Large caps
                'NCM.AX', 'WTC.AX', 'ALL.AX', 'QAN.AX', 'IAG.AX', 'MIN.AX', 'AMP.AX', 'AGL.AX',
                'S32.AX', 'ORG.AX', 'ASX.AX', 'CAR.AX', 'APT.AX', 'CPU.AX', 'SCG.AX', 'GMG.AX',
                'OZL.AX', 'TWE.AX', 'EVN.AX', 'IGO.AX', 'WHC.AX', 'SHL.AX', 'COL.AX', 'SOL.AX',
                'WDS.AX', 'A2M.AX', 'PME.AX', 'NST.AX', 'TAH.AX', 'AZJ.AX',
                
                # ASX51-100 - Mid caps
                'BOQ.AX', 'SYD.AX', 'ALD.AX', 'MGR.AX', 'SUN.AX', 'BEN.AX', 'NXT.AX', 'SKI.AX',
                'LLC.AX', 'VCX.AX', 'DUE.AX', 'CHC.AX', 'MPL.AX', 'URW.AX', 'ING.AX', 'BKW.AX',
                'ALU.AX', 'HVN.AX', 'AST.AX', 'APA.AX', 'BWP.AX', 'DXS.AX', 'TNT.AX', 'ALX.AX',
                'CWN.AX', 'GPT.AX', 'FPH.AX', 'BXB.AX', 'SCP.AX', 'DOW.AX', 'RHC.AX', 'SUL.AX',
                'VEA.AX', 'PDN.AX', 'GOR.AX', 'WSA.AX', 'PLS.AX', 'LTR.AX', 'LYC.AX', 'ZIP.AX',
                'SEK.AX', 'TNE.AX', 'MP1.AX', 'KGN.AX', 'NVX.AX', 'IOU.AX', 'AGE.AX', 'LKE.AX',
                
                # ASX101-200 - Smaller mid caps
                'IPL.AX', 'ORE.AX', 'PNV.AX', 'IEL.AX', 'RRL.AX', 'SAR.AX', 'CCL.AX', 'IMU.AX',
                'MSB.AX', 'SDG.AX', 'NEU.AX', 'BRG.AX', 'GUD.AX', 'BAP.AX', 'KMD.AX', 'BAL.AX',
                'PMV.AX', 'CMW.AX', 'CQR.AX', 'NHF.AX', 'PPT.AX', 'SWM.AX', 'VAH.AX', 'PRN.AX',
                'TPM.AX', 'WOR.AX', 'RED.AX', 'ANN.AX', 'NEC.AX', 'BSL.AX', 'PBH.AX', 'BLD.AX',
                'COE.AX', 'ELD.AX', 'GNC.AX', 'SDF.AX', 'CDA.AX', 'WEB.AX', 'NUF.AX', 'CTX.AX',
                'PWH.AX', 'AUB.AX', 'IFL.AX', 'CLW.AX', 'MTS.AX', 'RWC.AX', 'TNG.AX', 'BRN.AX',
                'HLS.AX', 'MYR.AX', 'PXA.AX', 'CCP.AX', 'ABP.AX', 'BPT.AX', 'NWL.AX', 'BKL.AX',
                
                # ASX201-300 - Small caps and growth stocks  
                'MFF.AX', 'AFI.AX', 'ANN.AX', 'ARG.AX', 'CNU.AX', 'DRO.AX', 'EHL.AX', 'GMA.AX',
                'HUB.AX', 'ILU.AX', 'JMS.AX', 'KAR.AX', 'LNK.AX', 'MYX.AX', 'NAN.AX', 'OML.AX',
                'PTM.AX', 'QUB.AX', 'RFG.AX', 'SGR.AX', 'TPW.AX', 'UOS.AX', 'VTG.AX', 'WHF.AX',
                'XIP.AX', 'YOW.AX', 'Z1P.AX', '88E.AX', 'ACX.AX', 'BUB.AX', 'CRN.AX', 'DCC.AX',
                'EMR.AX', 'FLT.AX', 'GRR.AX', 'HT8.AX', 'IPH.AX', 'JRV.AX', 'KSS.AX', 'LRS.AX',
                'MAD.AX', 'NRZ.AX', 'OBM.AX', 'PCI.AX', 'QAN.AX', 'RCR.AX', 'SFR.AX', 'TGR.AX',
                'UGL.AX', 'VLA.AX', 'WAF.AX', 'XST.AX', 'YAL.AX', 'ZIP.AX', 'AAC.AX', 'BBN.AX',
                'CCV.AX', 'DDH.AX', 'EGG.AX', 'FNP.AX', 'GXY.AX', 'HZR.AX', 'INF.AX', 'JXT.AX',
                
                # Additional sectors and emerging stocks
                'KZR.AX', 'LAM.AX', 'MMS.AX', 'NOV.AX', 'OCA.AX', 'PGH.AX', 'QVE.AX', 'RDM.AX',
                'SBM.AX', 'TKL.AX', 'UNI.AX', 'VML.AX', 'WMI.AX', 'XTE.AX', 'YPB.AX', 'ZLD.AX',
                'AJX.AX', 'BIT.AX', 'CDM.AX', 'DKM.AX', 'EML.AX', 'FGR.AX', 'GWA.AX', 'HPI.AX',
                'IXR.AX', 'JHL.AX', 'KLL.AX', 'LPI.AX', 'MNS.AX', 'NTI.AX', 'OSH.AX', 'PGF.AX',
                'QMS.AX', 'RFF.AX', 'SIQ.AX', 'TRS.AX', 'UMG.AX', 'VEE.AX', 'WTC.AX', 'XRF.AX',
                
                # Technology and Growth
                'ADO.AX', 'BRG.AX', 'CL1.AX', 'DTL.AX', 'EOS.AX', 'FZO.AX', 'GBT.AX', 'HCW.AX',
                'IDX.AX', 'JDO.AX', 'KGN.AX', 'LBY.AX', 'MEI.AX', 'NNW.AX', 'OPY.AX', 'PNI.AX',
                'RCT.AX', 'SRV.AX', 'TLC.AX', 'VHT.AX', 'WGB.AX', 'XPE.AX', 'YBR.AX', 'ZER.AX'
            ]
            
            self.log_message(f"Successfully loaded {len(asx300_comprehensive)} ASX300 symbols")
            return asx300_comprehensive
            
        except Exception as e:
            self.log_message(f"Error loading ASX300 symbols: {e}")
            # Fallback to major ASX stocks
            return [
                'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'BHP.AX', 'RIO.AX',
                'CSL.AX', 'WOW.AX', 'WES.AX', 'TLS.AX', 'MQG.AX', 'TCL.AX',
                'FMG.AX', 'XRO.AX', 'WTC.AX', 'REA.AX', 'COH.AX', 'QAN.AX',
                'ALL.AX', 'QBE.AX', 'STO.AX', 'NCM.AX', 'RMD.AX', 'A2M.AX'
            ]
    
    def get_market_health_regime(self):
        """Determine current ASX market health regime using VAS.AX"""
        try:
            # Get VAS.AX data for market health analysis
            vas_asset = Asset(symbol=self.market_health_symbol, asset_type="stock")
            vas_data = self.get_historical_prices(vas_asset, 250, "day")
            
            if not vas_data or len(vas_data.df) < 200:
                return "NORMAL"
            
            df = vas_data.df
            current_price = df['close'].iloc[-1]
            
            # Calculate moving averages
            ma_20 = df['close'].rolling(20).mean().iloc[-1]
            ma_50 = df['close'].rolling(50).mean().iloc[-1]
            ma_200 = df['close'].rolling(200).mean().iloc[-1]
            
            # Determine regime
            if (current_price < ma_20 and current_price < ma_50):
                regime = "WEAK"  # Bear market - halve positions
            elif (current_price > ma_20 and current_price > ma_50 and current_price > ma_200):
                regime = "STRONG"  # Bull market - double positions
            else:
                regime = "NORMAL"  # Mixed conditions - normal positions
            
            # Track regime changes
            if regime != self.current_market_regime:
                self.debug_stats['market_regime_changes'] += 1
                self.log_message(f"ASX MARKET REGIME CHANGE: {self.current_market_regime} → {regime}")
                self.log_message(f"  VAS.AX: ${current_price:.2f}, 20MA: ${ma_20:.2f}, 50MA: ${ma_50:.2f}, 200MA: ${ma_200:.2f}")
                self.current_market_regime = regime
            
            return regime
            
        except Exception as e:
            self.log_message(f"Error determining ASX market regime: {e}")
            return "NORMAL"
    
    def apply_market_health_multiplier(self, base_position_size):
        """Apply ASX market health multiplier to position size"""
        regime = self.get_market_health_regime()
        
        if regime == "WEAK":
            return base_position_size * 0.5  # Halve positions in weak markets
        elif regime == "STRONG":
            return base_position_size * 1.5  # 1.5x positions in strong markets (less aggressive than US)
        else:
            return base_position_size  # Normal positions
    
    def calculate_atr_series(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR series for consolidation analysis"""
        try:
            if len(df) < period + 1:
                return pd.Series(index=df.index, dtype=float)
            
            df = df.copy()
            df['prev_close'] = df['close'].shift(1)
            
            # True Range components
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['prev_close'] - df['low'])
            df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # ATR as rolling mean
            atr_series = df['true_range'].rolling(period).mean()
            
            return atr_series
            
        except Exception as e:
            self.log_message(f"Error calculating ATR series: {e}")
            return pd.Series(index=df.index, dtype=float)
    
    def analyze_consolidation_pattern(self, df: pd.DataFrame) -> dict:
        """Analyze consolidation characteristics - your scanner logic adapted for ASX"""
        try:
            if len(df) < 100:
                return {'consolidation_score': 0, 'details': 'Insufficient data'}
            
            current_price = df['close'].iloc[-1]
            
            # Calculate ATR series
            atr_14 = self.calculate_atr_series(df, 14)
            
            # Get recent periods for analysis
            recent_2weeks = slice(-10, None)
            recent_4weeks = slice(-20, None)
            older_period = slice(-90, -30)
            
            # ATR Analysis - Key consolidation indicator
            recent_atr_2w = atr_14.iloc[recent_2weeks].mean() if len(atr_14.iloc[recent_2weeks]) > 0 else 0
            recent_atr_4w = atr_14.iloc[recent_4weeks].mean() if len(atr_14.iloc[recent_4weeks]) > 0 else 0
            older_atr = atr_14.iloc[older_period].mean() if len(atr_14.iloc[older_period]) > 0 else 0
            
            # ATR contraction ratios
            atr_contraction_2w = recent_atr_2w / older_atr if older_atr > 0 else 1
            atr_contraction_4w = recent_atr_4w / older_atr if older_atr > 0 else 1
            
            # Performance calculations - look back to capture the big move
            if len(df) >= 90:
                price_3m_ago = df['close'].iloc[-90]
                gain_3m = ((current_price / price_3m_ago) - 1) * 100 if price_3m_ago > 0 else 0
            else:
                gain_3m = 0
                
            # Look further back for 6M to capture pre-consolidation gains
            if len(df) >= 200:  # ~8 months back to capture pre-move price
                price_6m_ago = df['close'].iloc[-200]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
            elif len(df) >= 180:
                price_6m_ago = df['close'].iloc[-180]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
            elif len(df) >= 130:
                price_6m_ago = df['close'].iloc[-130]
                gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
            else:
                gain_6m = gain_3m * 2.0 if gain_3m > 0 else 0
            
            # Recent performance (should be lower for consolidation)
            if len(df) >= 10:
                price_2w_ago = df['close'].iloc[-10]
                gain_2w = ((current_price / price_2w_ago) - 1) * 100 if price_2w_ago > 0 else 0
            else:
                gain_2w = 0
                
            if len(df) >= 20:
                price_4w_ago = df['close'].iloc[-20]
                gain_4w = ((current_price / price_4w_ago) - 1) * 100 if price_4w_ago > 0 else 0
            else:
                gain_4w = 0
            
            # ATR as percentage of price
            recent_atr_pct_2w = (recent_atr_2w / current_price * 100) if current_price > 0 else 0
            recent_atr_pct_4w = (recent_atr_4w / current_price * 100) if current_price > 0 else 0
            
            return {
                'gain_3m': gain_3m,
                'gain_6m': gain_6m,
                'gain_2w': gain_2w,
                'gain_4w': gain_4w,
                'recent_atr_pct_2w': recent_atr_pct_2w,
                'recent_atr_pct_4w': recent_atr_pct_4w,
                'atr_contraction_2w': atr_contraction_2w,
                'atr_contraction_4w': atr_contraction_4w,
                'current_atr_14': atr_14.iloc[-1] if len(atr_14) > 0 else 0
            }
            
        except Exception as e:
            self.log_message(f"Error analyzing consolidation pattern: {e}")
            return {'consolidation_score': 0, 'error': str(e)}
    
    def generate_consolidation_conviction_signal(self, symbol: str, df: pd.DataFrame):
        """Generate consolidation conviction signal - your scanner logic for ASX"""
        try:
            if len(df) < 150:
                return 0, "Insufficient historical data", {}
            
            current_price = df['close'].iloc[-1]
            
            # Get consolidation analysis
            consolidation_data = self.analyze_consolidation_pattern(df)
            
            # Check primary filter: 3-6 month performance
            medium_term_gain = max(consolidation_data.get('gain_3m', 0), consolidation_data.get('gain_6m', 0))
            if medium_term_gain < self.min_3month_gain:
                return 0, f"Insufficient 3-6M gain: {medium_term_gain:.1f}% < {self.min_3month_gain}%", consolidation_data
            
            conviction = 0
            details = consolidation_data.copy()
            
            # Factor 1: Medium-term Performance Strength (0-30 points)
            perf_points = 0
            if medium_term_gain >= 150:  # 150%+ gain (ASX can have bigger moves)
                perf_points = 30
            elif medium_term_gain >= 100:  # 100%+ gain
                perf_points = 25
            elif medium_term_gain >= 70:  # 70%+ gain
                perf_points = 20
            elif medium_term_gain >= 50:  # 50%+ gain
                perf_points = 18
            elif medium_term_gain >= 30:  # 30%+ gain (minimum)
                perf_points = 15
            
            conviction += perf_points
            details['performance_points'] = perf_points
            details['medium_term_gain'] = medium_term_gain
            
            # Factor 2: ATR Consolidation Analysis (0-35 points)
            atr_points = 0
            best_contraction = min(
                consolidation_data.get('atr_contraction_2w', 1),
                consolidation_data.get('atr_contraction_4w', 1)
            )
            
            if best_contraction <= 0.6:  # ATR contracted to 60% or less
                atr_points += 20
            elif best_contraction <= 0.8:  # ATR contracted to 80% or less
                atr_points += 15
            elif best_contraction <= 1.0:  # ATR staying same or lower
                atr_points += 10
            elif best_contraction <= 1.2:  # ATR only slightly higher
                atr_points += 5
            
            # Absolute ATR level (ASX stocks can be more volatile)
            recent_atr_pct = consolidation_data.get('recent_atr_pct_4w', 10)
            if recent_atr_pct <= 3.0:  # Very low volatility for ASX
                atr_points += 15
            elif recent_atr_pct <= 5.0:  # Low-moderate volatility
                atr_points += 10
            elif recent_atr_pct <= 7.0:  # Moderate volatility
                atr_points += 5
            elif recent_atr_pct <= 10.0:  # Higher volatility but acceptable for ASX
                atr_points += 2
            
            conviction += atr_points
            details['atr_points'] = atr_points
            details['best_atr_contraction'] = best_contraction
            
            # Factor 3: Recent Momentum Dampening (0-20 points)
            momentum_points = 0
            recent_gain_2w = consolidation_data.get('gain_2w', 0)
            recent_gain_4w = consolidation_data.get('gain_4w', 0)
            avg_recent_gain = (abs(recent_gain_2w) + abs(recent_gain_4w)) / 2
            
            if avg_recent_gain <= 3:  # Very low recent movement (slightly higher for ASX)
                momentum_points = 20
            elif avg_recent_gain <= 6:  # Low recent movement
                momentum_points = 15
            elif avg_recent_gain <= 10:  # Moderate recent movement
                momentum_points = 10
            elif avg_recent_gain <= 15:  # Some recent movement
                momentum_points = 5
            
            conviction += momentum_points
            details['momentum_points'] = momentum_points
            details['avg_recent_gain'] = avg_recent_gain
            details['total_conviction'] = conviction
            
            # Convert to conviction level (0-100 -> 0-5) - slightly adjusted for ASX
            if conviction >= 75:  # Slightly lower threshold for ASX
                level = 5
                reason = f"ASX MAX: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
            elif conviction >= 60:
                level = 4
                reason = f"ASX HIGH: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
            elif conviction >= 45:
                level = 3
                reason = f"ASX GOOD: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
            elif conviction >= 30:
                level = 2
                reason = f"ASX FAIR: {conviction}, 3-6M: {medium_term_gain:.1f}%"
            else:
                level = 0
                reason = f"No ASX signal: {conviction}"
            
            return level, reason, details
            
        except Exception as e:
            self.log_message(f"Error generating consolidation signal for {symbol}: {e}")
            return 0, f"Error: {e}", {}
    
    def get_symbol_data(self, symbol, days_back=250):
        """Get symbol data - same as 5LC approach"""
        try:
            asset = Asset(symbol=symbol, asset_type="stock")
            bars = self.get_historical_prices(asset, days_back, "day")
            return bars.df if bars and hasattr(bars, 'df') and len(bars.df) > 0 else None
        except Exception as e:
            self.log_message(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_position_size(self, symbol, price, conviction_level):
        """Calculate position size with ASX market health overlay"""
        try:
            portfolio_value = self.get_portfolio_value()
            
            # Position size by conviction level (optimized for consolidation)
            base_position_pct = {
                2: 0.15,   # 15% - fair consolidation
                3: 0.20,   # 20% - good consolidation  
                4: 0.28,   # 28% - high consolidation
                5: 0.35    # 35% - max consolidation
            }.get(conviction_level, 0.15)
            
            # Apply ASX market health multiplier
            adjusted_position_pct = self.apply_market_health_multiplier(base_position_pct)
            
            # Ensure we don't exceed limits
            final_position_pct = min(adjusted_position_pct, self.max_position_size)
            final_position_pct = max(final_position_pct, self.min_position_size)
            
            # Calculate position value
            position_value = portfolio_value * final_position_pct
            shares = int(position_value / price)
            
            # Apply cash constraints
            max_shares_by_cash = int(self.get_cash() / price)
            final_shares = min(shares, max_shares_by_cash)
            
            return max(final_shares, 0)
            
        except Exception as e:
            self.log_message(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def on_trading_iteration(self):
        """Main trading logic - same structure as 5LC"""
        try:
            current_date = self.get_datetime()
            portfolio_value = self.get_portfolio_value()
            
            # Track performance for Pyfolio (same as 5LC)
            self.track_daily_performance(current_date, portfolio_value)
            
            # Update consolidation leaders periodically
            self.update_consolidation_leaders()
            
            # Check exits first (same as 5LC)
            self.check_consolidation_exits()
            
            # Look for new entries if we have room
            positions = self.get_positions()
            if len(positions) < self.max_positions and self.consolidation_leaders:
                self.scan_for_consolidation_entries()
                
        except Exception as e:
            self.log_message(f"Error in trading iteration: {e}")
    
    def track_daily_performance(self, date, portfolio_value):
        """Track daily performance - VAS.AX as benchmark"""
        try:
            # Calculate daily return
            if len(self.portfolio_values) > 0:
                previous_value = self.portfolio_values[-1]
                daily_return = (portfolio_value / previous_value) - 1
            else:
                daily_return = 0.0
            
            self.daily_returns.append(daily_return)
            self.portfolio_values.append(portfolio_value)
            self.dates.append(date)
            
            # Get benchmark return (VAS.AX) - ASX300 ETF
            try:
                vas_asset = Asset(symbol="VAS.AX", asset_type="stock")
                vas_data = self.get_historical_prices(vas_asset, 2, "day")
                
                if vas_data and len(vas_data.df) >= 2:
                    vas_current = vas_data.df['close'].iloc[-1]
                    vas_previous = vas_data.df['close'].iloc[-2]
                    benchmark_return = (vas_current / vas_previous) - 1
                else:
                    benchmark_return = 0.0
            except:
                benchmark_return = 0.0
            
            self.benchmark_returns.append(benchmark_return)
            
        except Exception as e:
            self.log_message(f"Error tracking performance: {e}")
    
    def update_consolidation_leaders(self):
        """Update list of ASX consolidation candidates"""
        current_date = self.get_datetime()
        
        # Check if we need to re-screen (same timing as 5LC)
        if (self.last_screening_date is None or 
            (current_date - self.last_screening_date).days >= self.screening_frequency):
            
            self.log_message(f"Screening ASX300 for consolidation patterns...")
            
            # Sample subset for faster screening - larger now we have full ASX300
            sample_size = min(150, len(self.asx300_symbols))  # Screen more of ASX300
            symbols_to_screen = self.asx300_symbols[:sample_size]
            
            leaders = []
            screening_count = 0
            
            for symbol in symbols_to_screen:
                try:
                    self.debug_stats['screening_attempts'] += 1
                    
                    # Get data
                    df = self.get_symbol_data(symbol, days_back=250)
                    if df is None or len(df) < 150:
                        continue
                    
                    current_price = df['close'].iloc[-1]
                    avg_volume = df['volume'].rolling(20).mean().iloc[-1]
                    
                    # Basic filters (ASX specific)
                    if (current_price >= self.min_price and 
                        avg_volume >= self.min_avg_volume):
                        
                        # Check for consolidation pattern
                        conviction, reason, details = self.generate_consolidation_conviction_signal(symbol, df)
                        
                        if conviction >= 2:  # Only conviction level 2+ 
                            leaders.append({
                                'symbol': symbol,
                                'conviction': conviction,
                                'reason': reason,
                                'details': details
                            })
                            self.debug_stats['consolidation_patterns_found'] += 1
                        
                        screening_count += 1
                        
                        # Progress update (same as 5LC)
                        if screening_count % 10 == 0:
                            self.log_message(f"  Screened {screening_count}/{len(symbols_to_screen)} ASX stocks...")
                    
                except Exception as e:
                    continue
            
            # Update leaders list
            self.consolidation_leaders = [leader['symbol'] for leader in leaders]
            self.last_screening_date = current_date
            
            self.log_message(f"ASX consolidation screening complete:")
            self.log_message(f"  Screened: {screening_count} stocks")
            self.log_message(f"  Consolidation patterns found: {len(self.consolidation_leaders)}")
            self.log_message(f"  ASX Market Regime: {self.current_market_regime}")
            
            # Log top consolidation candidates
            for leader in sorted(leaders, key=lambda x: x['conviction'], reverse=True)[:5]:
                details = leader['details']
                self.log_message(f"    {leader['symbol']}: Conv {leader['conviction']} - "
                               f"{details.get('medium_term_gain', 0):.1f}% 3-6M")
    
    def scan_for_consolidation_entries(self):
        """Scan ASX for entries - same structure as 5LC"""
        entries_made = 0
        max_entries_per_day = 2
        
        # Randomize order to avoid bias (same as 5LC)
        import random
        candidates = self.consolidation_leaders.copy()
        random.shuffle(candidates)
        
        for symbol in candidates[:12]:  # Check top 12 ASX consolidation leaders
            try:
                # Skip if already holding
                if any(pos.asset.symbol == symbol for pos in self.get_positions()):
                    continue
                
                # Get fresh data
                df = self.get_symbol_data(symbol, days_back=250)
                if df is None or len(df) < 150:
                    continue
                
                # Generate conviction signal
                self.debug_stats['technical_signals_checked'] += 1
                conviction, reason, details = self.generate_consolidation_conviction_signal(symbol, df)
                
                if conviction >= 2:  # Minimum consolidation conviction
                    self.debug_stats['conviction_signals_generated'] += 1
                    current_price = df['close'].iloc[-1]
                    shares = self.calculate_position_size(symbol, current_price, conviction)
                    
                    if shares > 0:
                        try:
                            # Create and submit order (same as 5LC)
                            self.debug_stats['orders_attempted'] += 1
                            asset = Asset(symbol=symbol, asset_type="stock")
                            order = self.create_order(asset, shares, "buy")
                            self.submit_order(order)
                            self.debug_stats['orders_successful'] += 1
                            
                            # Track position (same as 5LC structure)
                            stop_price = current_price * (1 - self.stop_loss_pct)
                            self.position_tracker[symbol] = {
                                'entry_price': current_price,
                                'entry_date': self.get_datetime(),
                                'stop_loss': stop_price,
                                'highest_price': current_price,
                                'trailing': False,
                                'conviction': conviction
                            }
                            
                            position_pct = (shares * current_price) / self.get_portfolio_value() * 100
                            
                            self.log_message(f"ASX CONSOLIDATION ENTRY: {symbol} - Conviction {conviction} | {self.current_market_regime}")
                            self.log_message(f"  {shares} shares @ ${current_price:.2f} ({position_pct:.1f}% position)")
                            self.log_message(f"  Stop: ${stop_price:.2f}, 3-6M gain: {details.get('medium_term_gain', 0):.1f}%")
                            
                            self.log_trade(symbol, "buy", current_price, shares, reason)
                            
                            entries_made += 1
                            if entries_made >= max_entries_per_day:
                                break
                                
                        except Exception as e:
                            self.log_message(f"Order error for {symbol}: {e}")
                            
            except Exception as e:
                continue
    
    def check_consolidation_exits(self):
        """Check exits - same structure as 5LC but optimized for consolidation"""
        positions = self.get_positions()
        
        for position in positions:
            try:
                symbol = position.asset.symbol
                current_price = self.get_last_price(position.asset)
                
                if current_price is None:
                    continue
                
                # Get position tracking data (same as 5LC)
                if symbol not in self.position_tracker:
                    # Initialize tracking for existing position
                    self.position_tracker[symbol] = {
                        'entry_price': current_price,
                        'entry_date': self.get_datetime(),
                        'stop_loss': current_price * (1 - self.stop_loss_pct),
                        'highest_price': current_price,
                        'trailing': False
                    }
                
                pos_data = self.position_tracker[symbol]
                entry_price = pos_data['entry_price']
                stop_loss = pos_data['stop_loss']
                highest_price = pos_data['highest_price']
                
                # Update highest price
                if current_price > highest_price:
                    pos_data['highest_price'] = current_price
                    highest_price = current_price
                
                # Calculate current P&L
                pnl_pct = (current_price / entry_price - 1) * 100
                days_held = (self.get_datetime() - pos_data['entry_date']).days
                
                should_exit = False
                exit_reason = ""
                
                # 1. Stop Loss (8% for consolidation)
                if pnl_pct < -self.stop_loss_pct * 100:
                    should_exit = True
                    exit_reason = 'Stop Loss'
                
                # 2. Profit Target (40% for consolidation)
                elif pnl_pct > self.profit_target * 100:
                    should_exit = True
                    exit_reason = 'ASX PROFIT TARGET'
                
                # 3. Trailing Stop (after 15% gain for consolidation)
                elif pnl_pct > self.trail_profit_trigger * 100:
                    if not pos_data['trailing']:
                        pos_data['trailing'] = True
                        self.log_message(f"ASX CONSOLIDATION TRAILING activated for {symbol} at {pnl_pct:.1f}% gain")
                    
                    new_stop = highest_price * (1 - self.trail_percent)
                    if new_stop > pos_data['stop_loss']:
                        pos_data['stop_loss'] = new_stop
                    
                    if current_price <= pos_data['stop_loss']:
                        should_exit = True
                        exit_reason = 'Trailing Stop'
                
                # 4. Time Exit (6 months max for consolidation)
                elif days_held > self.max_hold_days:
                    should_exit = True
                    exit_reason = 'Time Exit'
                
                if should_exit:
                    # Execute exit (same as 5LC)
                    order = self.create_order(position.asset, position.quantity, "sell")
                    self.submit_order(order)
                    
                    self.log_message(f"ASX CONSOLIDATION EXIT: {symbol} @ ${current_price:.2f}")
                    self.log_message(f"  P&L: {pnl_pct:.1f}%, Hold: {days_held} days, Reason: {exit_reason}")
                    
                    # Log trade
                    self.log_trade(symbol, "sell", current_price, position.quantity, 
                                 f"{exit_reason} | P&L: {pnl_pct:.1f}%")
                    
                    # Remove from tracking
                    if symbol in self.position_tracker:
                        del self.position_tracker[symbol]
                    
            except Exception as e:
                self.log_message(f"Error checking exit for {position.asset.symbol}: {e}")
    
    def log_trade(self, symbol, action, price, quantity, reason):
        """Log trades - same as 5LC"""
        self.trades_log.append({
            'timestamp': self.get_datetime(),
            'symbol': symbol,
            'action': action,
            'price': price,
            'quantity': quantity,
            'value': price * quantity,
            'reason': reason,
            'portfolio_value': self.get_portfolio_value(),
            'market_regime': self.current_market_regime,
            'strategy': 'consolidation_conviction_asx300'
        })
    
    def on_strategy_end(self):
        """Enhanced strategy end - same structure as 5LC"""
        self.log_message("=== CONSOLIDATION CONVICTION ASX300 STRATEGY COMPLETED ===")
        
        # Save trades CSV (same as 5LC)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.trades_log:
            trades_df = pd.DataFrame(self.trades_log)
            csv_filename = f"consolidation_conviction_asx300_trades_{timestamp}.csv"
            trades_df.to_csv(csv_filename, index=False)
            self.log_message(f"Trades saved: {csv_filename}")
        
        # Generate Pyfolio Analysis (same as 5LC)
        if PYFOLIO_AVAILABLE and len(self.daily_returns) > 1:
            try:
                self.generate_pyfolio_analysis(timestamp)
            except Exception as e:
                self.log_message(f"Error generating Pyfolio analysis: {e}")
        
        # Performance summary (same structure as 5LC)
        portfolio_value = self.get_portfolio_value()
        total_trades = len(self.trades_log)
        positions = len(self.get_positions())
        
        self.log_message("=" * 80)
        self.log_message("CONSOLIDATION CONVICTION ASX300 STRATEGY PERFORMANCE")
        self.log_message("=" * 80)
        self.log_message(f"Final Portfolio Value: ${portfolio_value:,.2f}")
        self.log_message(f"Active Positions: {positions}")
        self.log_message(f"Total Trades: {total_trades}")
        self.log_message(f"Market Regime Changes: {self.debug_stats['market_regime_changes']}")
        self.log_message(f"Final ASX Market Regime: {self.current_market_regime}")
        
        # Debug statistics (same as 5LC)
        self.log_message(f"\nASX CONSOLIDATION SCREENING STATISTICS:")
        self.log_message(f"  Stocks Screened: {self.debug_stats['screening_attempts']}")
        self.log_message(f"  Consolidation Patterns Found: {self.debug_stats['consolidation_patterns_found']}")
        self.log_message(f"  Technical Signals Checked: {self.debug_stats['technical_signals_checked']}")
        self.log_message(f"  Conviction Signals Generated: {self.debug_stats['conviction_signals_generated']}")
        self.log_message(f"  Orders Attempted: {self.debug_stats['orders_attempted']}")
        self.log_message(f"  Orders Successful: {self.debug_stats['orders_successful']}")
        
        # Calculate return (same as 5LC)
        initial_value = 100000.0
        total_return = (portfolio_value - initial_value) / initial_value * 100
        self.log_message(f"\nPERFORMANCE:")
        self.log_message(f"  Total Return: {total_return:.1f}%")
        
        self.log_message("=" * 80)
        self.log_message("ASX300 Consolidation Conviction strategy completed")
    
    def generate_pyfolio_analysis(self, timestamp):
        """Generate Pyfolio analysis - VAS.AX benchmark"""
        if not PYFOLIO_AVAILABLE:
            return
            
        self.log_message("Generating ASX Pyfolio analysis...")
        
        # Prepare data (same as 5LC)
        returns_series = pd.Series(
            self.daily_returns[1:],
            index=self.dates[1:],
            name='consolidation_conviction_asx300_returns'
        )
        
        benchmark_series = pd.Series(
            self.benchmark_returns[1:],
            index=self.dates[1:],
            name='vas_ax_benchmark_returns'
        )
        
        # Create output directory (same as 5LC)
        output_dir = "pyfolio_reports"
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            # Create returns tear sheet (same as 5LC)
            plt.figure(figsize=(16, 12))
            pf.create_returns_tear_sheet(
                returns_series,
                benchmark_rets=benchmark_series,
                live_start_date=None,
                return_fig=False
            )
            plt.savefig(f"{output_dir}/consolidation_conviction_asx300_returns_tearsheet_{timestamp}.png", 
                       dpi=300, bbox_inches='tight')
            plt.close('all')
            
            self.log_message(f"ASX Consolidation strategy Pyfolio analysis saved")
            
            # Basic metrics (same as 5LC)
            total_return = (returns_series + 1).prod() - 1
            volatility = returns_series.std() * np.sqrt(252)
            sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252)
            
            self.log_message(f"  Total Return: {total_return:.2%}")
            self.log_message(f"  Volatility: {volatility:.2%}")
            self.log_message(f"  Sharpe Ratio: {sharpe:.2f}")
            
        except Exception as e:
            self.log_message(f"Error creating Pyfolio analysis: {e}")


def run_consolidation_conviction_asx300_backtest():
    """Run complete ASX300 Consolidation Conviction strategy backtest - same structure as 5LC"""
    try:
        print("=" * 80)
        print("CONSOLIDATION CONVICTION ASX300 STRATEGY BACKTEST")
        print("=" * 80)
        print("Strategy Focus:")
        print("Post-move consolidation pattern detection for ASX300")
        print("30%+ 3-6 month performance requirement")
        print("ATR contraction analysis for consolidation identification")
        print("Dynamic position sizing (15%-35% based on conviction)")
        print("Enhanced risk management optimized for consolidation")
        print("Tighter stops (8%) and realistic targets (40%)")
        print("Market health overlay using VAS.AX moving averages")
        if PYFOLIO_AVAILABLE:
            print("Comprehensive Pyfolio analysis vs VAS.AX")
        else:
            print("WARNING: Install pyfolio-reloaded for enhanced analysis:")
            print("   pip install pyfolio-reloaded")
        print("=" * 80)
        
        # Backtest parameters (same structure as 5LC)
        backtesting_start = datetime(2015, 1, 1)
        backtesting_end = datetime(2024, 12, 31)
        initial_cash = 100000.0
        
        print(f"Period: {backtesting_start.date()} to {backtesting_end.date()}")
        print(f"Initial Capital: ${initial_cash:,.2f}")
        print(f"Benchmark: VAS.AX (ASX300 ETF)")
        print(f"Universe: ASX300 stocks")
        print("Market Health Multipliers:")
        print("  - WEAK (VAS.AX < 20MA & 50MA): 0.5x positions")
        print("  - STRONG (VAS.AX > 20MA & 50MA & 200MA): 1.5x positions")
        print("  - NORMAL (other conditions): 1.0x positions")
        print("Focus: Post-move consolidation patterns")
        print("Min 3-6M gain: 30%+")
        print("=" * 80)
        
        # Run backtest (exactly same as 5LC)
        results = ConsolidationConvictionASX300Strategy.backtest(
            YahooDataBacktesting,
            backtesting_start,
            backtesting_end,
            parameters={'initial_cash': initial_cash},
            benchmark_asset="VAS.AX"
        )
        
        print("\nCONSOLIDATION CONVICTION ASX300 STRATEGY COMPLETED!")
        print("Trade log exported with ASX consolidation metrics")
        if PYFOLIO_AVAILABLE:
            print("Pyfolio tear sheet generated vs VAS.AX benchmark")
        print("ASX consolidation pattern analysis completed")
        print("Market health analysis with VAS.AX overlay completed")
        
        return results
        
    except Exception as e:
        print(f"Error in ASX300 Consolidation Conviction backtest: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting ASX300 Consolidation Conviction Strategy Backtest...")
    results = run_consolidation_conviction_asx300_backtest()