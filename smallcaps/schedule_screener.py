"""
ASX Small Cap Screener — Scheduler
====================================

Runs the cashflow screener on a configurable schedule.

Usage:
    python schedule_screener.py              # Run once immediately
    python schedule_screener.py --schedule   # Run on schedule (see config.py)
    python schedule_screener.py --interval 3 # Override: run every 3 days

Schedule behaviour:
    Waits until SCREEN_RUN_TIME (default 16:30 AEST) each day.
    Only triggers a run every SCREEN_INTERVAL_DAYS days (default: 7 = weekly).
    State (last run date) is persisted in last_run.txt so restarts are safe.
"""

import argparse
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import config
from asx_smallcap_screener import ASXSmallCapScreener

log = logging.getLogger(__name__)

STATE_FILE = config.SMALLCAPS_DIR / 'last_run.txt'


def _load_last_run() -> Optional[date]:
    """Read last run date from state file."""
    if STATE_FILE.exists():
        try:
            text = STATE_FILE.read_text().strip()
            return date.fromisoformat(text)
        except Exception:
            pass
    return None


def _save_last_run(run_date: date) -> None:
    STATE_FILE.write_text(run_date.isoformat())


def run_once() -> None:
    """Execute one full screen run and save results."""
    log.info(f"=== Screen run starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    screener = ASXSmallCapScreener()
    symbols = screener.load_universe()

    if not symbols:
        log.error("No symbols loaded — aborting run.")
        return

    results_df = screener.run_screen(symbols)

    if results_df.empty:
        log.warning("No stocks passed the cashflow screen.")
    else:
        results_dir = config.SMALLCAPS_DIR / f'results_{datetime.now().strftime("%Y-%m")}'
        screener.save_results(results_df, results_dir)

    _save_last_run(date.today())
    log.info(f"=== Screen run complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")


def run_scheduled(interval_days: int) -> None:
    """
    Loop forever, triggering a run at SCREEN_RUN_TIME every interval_days days.

    interval_days: how many calendar days between runs (e.g. 7 = weekly)
    """
    run_time_str = config.SCREEN_RUN_TIME        # e.g. '16:30'
    run_hour, run_minute = map(int, run_time_str.split(':'))

    log.info(f"Scheduler started — run every {interval_days} day(s) at {run_time_str}")

    last_run = _load_last_run()
    if last_run:
        log.info(f"Last run was: {last_run}")
    else:
        log.info("No previous run recorded.")

    while True:
        now = datetime.now()
        today = now.date()

        # Check if a run is due
        due = (last_run is None) or (today - last_run >= timedelta(days=interval_days))

        if due:
            # Wait until run time today (if it's already past, run immediately)
            run_dt = now.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            if now >= run_dt:
                run_once()
                last_run = date.today()
            else:
                wait_secs = (run_dt - now).total_seconds()
                log.info(f"Waiting {wait_secs/60:.0f} min until {run_time_str}...")
                time.sleep(min(wait_secs, 60))   # check every minute
                continue
        else:
            next_run = last_run + timedelta(days=interval_days)
            secs_until_midnight = (
                datetime.combine(today + timedelta(days=1), datetime.min.time()) - now
            ).total_seconds()
            log.info(f"Next run due: {next_run} — sleeping until tomorrow...")
            time.sleep(min(secs_until_midnight, 3600))   # check every hour


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description='ASX Small Cap Cashflow Screener')
    parser.add_argument(
        '--schedule',
        action='store_true',
        help=f'Run on schedule (every SCREEN_INTERVAL_DAYS days at SCREEN_RUN_TIME in config.py)',
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=config.SCREEN_INTERVAL_DAYS,
        help=f'Days between runs when using --schedule (default: {config.SCREEN_INTERVAL_DAYS})',
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled(interval_days=args.interval)
    else:
        run_once()


if __name__ == '__main__':
    main()
