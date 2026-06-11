"""
Multi-System Live/Paper Trading — Global Configuration

Runs the bake-off's Phase-2 advancement winners concurrently against ONE
Interactive Brokers paper account:

    Qullamaggie (id 3)  ·  Hybrid Balanced (id 4)

Both size off the FULL account equity (per the chosen capital model),
keep their own state files, and tag every order with a per-system `orderRef`
so fills are attributed correctly even when both systems hold the same symbol.

Edit the connection block to match your TWS / IB Gateway, then run:

    python multi_trader.py --dry-run     # logic only, no IB, no orders
    python multi_trader.py               # one live pass now (paper account)
    python multi_trader.py --schedule    # run every weekday at DAILY_RUN_TIME
    python multi_trader.py --status       # print all systems' positions
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Interactive Brokers connection
# ---------------------------------------------------------------------------
# Ports:  7497 = TWS paper | 7496 = TWS live | 4002 = IB Gateway paper | 4001 = IBG live
IB_HOST      = '127.0.0.1'
IB_PORT      = 7497          # TWS paper by default — KEEP THIS A PAPER PORT
IB_CLIENT_ID = 20            # Unique per connected script (live_multi uses one connection)

# Safety rail: refuse to run against a non-paper port unless explicitly allowed.
ALLOW_LIVE_PORT = False      # set True only when you genuinely want real-money ports

# ---------------------------------------------------------------------------
# Which systems to run (bake-off Phase-2 advancement winners)
# ---------------------------------------------------------------------------
# IDs map to definitions in systems.py
ACTIVE_SYSTEM_IDS = [3, 4]    # Qullamaggie, Hybrid Balanced

# Capital model: each system sizes as if it owned the whole account.
# Combined exposure across systems can therefore exceed 100% — this is a
# signal-comparison paper run, not a single blended portfolio.
CAPITAL_MODEL = 'full_equity'    # 'full_equity' | 'split_equity'
# If you ever switch to 'split_equity', each system is sized off
# account_value / len(ACTIVE_SYSTEM_IDS).

# ---------------------------------------------------------------------------
# Shared trading rules
# ---------------------------------------------------------------------------
SKIP_ENTRIES_IN_BEAR = True   # No new entries when SPY < 200-day MA
MAX_ENTRIES_PER_DAY  = 3      # Per system, per day
CHANDELIER_ATR_MULT  = 3.0    # Trailing stop for ATR-stop systems = peak - N x ATR

# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
# Local-time HH:MM to run the daily scan. Run after the close so EOD prices
# are available from yfinance (~30 min lag).
DAILY_RUN_TIME = '16:30'

# ---------------------------------------------------------------------------
# Price data
# ---------------------------------------------------------------------------
PRICE_LOOKBACK_DAYS = 400     # Enough for 200-day MA + ATR history

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LIVE_DIR   = Path(__file__).parent
SCANS_DIR  = LIVE_DIR.parent
STATE_DIR  = LIVE_DIR / 'state'           # one JSON per system lives here
LOG_FILE   = LIVE_DIR / 'multi_trader.log'
CACHE_DIR  = SCANS_DIR / 'backtesting' / 'cache'

# Universe symbol files — bake-off winner universes.
# Qullamaggie was validated on russell1000; Hybrid on sp500.
# Running both over the combined russell1000+sp500 set (they overlap heavily).
DATA_DIR         = LIVE_DIR.parent.parent / 'backtesting' / 'data'
RUSSELL1000_FILE = DATA_DIR / 'russell1000_symbols.csv'
SP500_FILE       = DATA_DIR / 'sp500_symbols.csv'

STATE_DIR.mkdir(exist_ok=True)
