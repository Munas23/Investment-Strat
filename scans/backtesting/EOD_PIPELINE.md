# Phase 4 — EOD Data Pipeline (design)

Goal: a dependable daily store of end-of-day OHLCV for every configured
universe, so the daily scanner and (later) paper trading run off a local
store instead of hitting Yahoo live each morning.

## What it does
`eod_pipeline.py` downloads the gap between the last stored bar and today for
each symbol and merges it into a per-symbol parquet. It is idempotent
(re-running the same day is a no-op via the manifest's `last_date` check) and
resumable (the manifest is checkpointed after every symbol, so an interrupted
run picks up where it stopped).

## Store layout
```
backtesting/eod_store/
  prices/<SYMBOL>.parquet   # full OHLCV history, tz-naive, lowercase columns
  manifest.json             # {symbols: {SYM: last_date}, last_run: iso8601}
```
Parquet (not pickle) so the store is portable and inspectable. The existing
screener cache (`cache/prices/*.pkl`) stays as-is; this store is the forward
feed, and a later step can point the screener/scanner at it.

## Run cadence
US universes settle after the 16:00 ET close; schedule ~22:30 UTC on weekdays:
```
30 22 * * 1-5  cd .../scans/backtesting && python eod_pipeline.py --all
```
ASX closes earlier (AEST); if AU latency matters, run a second `--universes
asx300` job after the Sydney close.

## First run
```
python eod_pipeline.py --all --full      # seeds full history (DEFAULT_HISTORY_START=2018-01-01)
```
Subsequent runs use `--all` (incremental).

## Open items before wiring to live
1. **Adjusted vs raw:** pulls `auto_adjust=True` (split/div adjusted) to match
   the backtests. If paper trading needs raw closes for order sizing, store both.
2. **Corporate actions / delistings:** a delisted symbol returns `no-data`; the
   manifest records the stale `last_date`. Add a staleness report so dead tickers
   are pruned at the quarterly universe rebuild (`backtesting/data/build_universes.py`).
3. **Survivorship:** the universe CSVs are current constituents. For point-in-time
   correctness the rebuild step should snapshot membership per quarter (already a
   known Phase 2 caveat).
4. **Scanner integration:** repoint `5lc_daily_scanner.py` (and any Qullamaggie/
   Hybrid scanner) to read `eod_store/prices/` instead of fetching live.
