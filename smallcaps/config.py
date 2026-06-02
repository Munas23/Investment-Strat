"""
ASX Small Cap Screener — Configuration
=======================================

Edit this file to adjust universe, filters, and scheduling.
All other smallcap files import from here.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------

# S&P/ASX 50 constituents — excluded from this strategy.
# These are the 50 largest ASX companies by market cap (approximate, early 2026).
# Update this list periodically as the index composition changes.
ASX50_CODES = {
    'CBA', 'BHP', 'CSL', 'NAB', 'ANZ', 'WBC', 'WES', 'GMG', 'RIO', 'FMG',
    'MQG', 'WOW', 'TLS', 'RMD', 'BXB', 'COL', 'ALL', 'REA', 'WDS', 'IAG',
    'QBE', 'COH', 'AMC', 'SEK', 'TCL', 'SUN', 'CPU', 'JHX', 'APA', 'MPL',
    'TWE', 'SGP', 'GPT', 'DXS', 'NST', 'SCG', 'LLC', 'XRO', 'MIN', 'NXT',
    'ALX', 'AZJ', 'WTC', 'BSL', 'CWY', 'CHC', 'MGR', 'CAR', 'SOL', 'WHC',
}

# ---------------------------------------------------------------------------
# Account & position sizing
# ---------------------------------------------------------------------------
ACCOUNT_SIZE = 500_000       # Default account size (AUD)
MAX_POSITIONS = 10           # Max simultaneous open positions
BASE_RISK_PCT = 1.5          # % of account risked per trade
MAX_POS_SIZE_PCT = 10.0      # Max single position as % of account

# ---------------------------------------------------------------------------
# Universe filters (hard filters — stocks that fail are dropped immediately)
# ---------------------------------------------------------------------------
MIN_MARKET_CAP_AUD = 50_000_000        # $50M minimum market cap
MAX_MARKET_CAP_AUD = 3_000_000_000     # $3B maximum (true small/mid cap)
MIN_AVG_VOLUME     = 50_000            # 50K shares/day minimum average volume
MIN_DDV_AUD        = 500_000           # $500K daily dollar volume minimum

# ---------------------------------------------------------------------------
# Cashflow filters (primary strategy criterion)
# ---------------------------------------------------------------------------
REQUIRE_POSITIVE_OPERATING_CF = True   # Must have positive operating cashflow
REQUIRE_POSITIVE_FREE_CF      = False  # Free cashflow positive is preferred but not required

# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------
MIN_SCORE_QUALITY = 60   # Minimum score to appear in QUALITY output file
MIN_SCORE_TOP     = 70   # Minimum score to appear in TOP output file

# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
# Run time in your local timezone (AEST = UTC+10 or +11 daylight)
# ASX closes at 4:00pm AEST — run after 4:30pm to ensure EOD prices are available
SCREEN_RUN_TIME = '16:30'

# How often to run (days between runs).
# Set to 1 for daily, 7 for weekly, etc.
SCREEN_INTERVAL_DAYS = 30    # Monthly (cashflow data is quarterly)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SMALLCAPS_DIR = Path(__file__).parent
SCANS_DIR     = SMALLCAPS_DIR.parent / 'scans'
LOG_FILE      = SMALLCAPS_DIR / 'screener.log'

# Where to look for ASX symbol CSV files.
# The screener checks these paths in order; uses first one found.
SYMBOL_CSV_SEARCH_PATHS = [
    SMALLCAPS_DIR / 'asx_symbols.csv',                    # Drop a CSV here (preferred)
    SCANS_DIR / 'downloads_2026-01-01' / 'ASX300_symbols.csv',  # Reuse scans data
]
