"""
Live Trading Configuration

Edit this file to change system, risk, and IB settings.
All other live_*.py files import from here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Interactive Brokers connection
# ---------------------------------------------------------------------------
IB_HOST      = '127.0.0.1'
IB_PORT      = 7497        # 7497 = TWS paper  |  7496 = TWS live  |  4002 = IB Gateway paper
IB_CLIENT_ID = 10          # Must be unique per connected script

# ---------------------------------------------------------------------------
# Trading system
# ---------------------------------------------------------------------------
SYSTEM_ID       = 2        # 1=Minervini 2=Turtle 3=Qullamaggie 4=Hybrid 5=HighConv
MIN_CONVICTION  = 3        # Minimum signal conviction to enter
MAX_POSITIONS   = 12       # Hard cap on simultaneous open positions
MAX_ENTRIES_PER_DAY = 3    # Avoid piling in all at once
BASE_RISK_PCT   = 1.5      # % of account risked per trade at conviction 3
MAX_POS_SIZE_PCT = 8.3     # Max single position as % of account (100/MAX_POSITIONS)

# Per-conviction sizing (System 2 Turtle)
CONVICTION_MULTIPLIERS = {5: 1.5, 4: 1.25, 3: 1.0}
ATR_MULTIPLIERS        = {5: 1.5, 4: 2.0,  3: 2.5}   # stop distance = mult × ATR
CHANDELIER_ATR_MULT    = 3.0                           # trailing stop = peak - N×ATR

# Bear market filter: skip new entries when SPY < 200MA
SKIP_ENTRIES_IN_BEAR = True

# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
# Time (HH:MM) in your LOCAL timezone to run the daily scan
# Run after market close so EOD prices are available from yfinance (~30 min lag)
DAILY_RUN_TIME = '16:30'

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LIVE_DIR        = Path(__file__).parent
SCANS_DIR       = LIVE_DIR.parent
STATE_FILE      = LIVE_DIR / 'state.json'
LOG_FILE        = LIVE_DIR / 'live_trader.log'
CACHE_DIR       = SCANS_DIR / 'backtesting' / 'cache'

IVV_FILE = SCANS_DIR / 'downloads_2026-01-01' / 'IVV_symbols.csv'
IJR_FILE = SCANS_DIR / 'downloads_2026-01-01' / 'IJR_symbols.csv'
