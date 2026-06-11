# IB Paper Trading — Setup & Go-Live Guide

*One-time setup to go from dry-run to a live paper account.*

---

## 1. Prerequisites

- [ ] Interactive Brokers account with **paper trading** enabled
- [ ] TWS (Trader Workstation) downloaded and installed
      → Download at: ibkr.com/en/trading/tws
- [ ] Python dependencies installed (from repo root):
      ```
      pip install ib_insync schedule
      ```

---

## 2. TWS configuration (one-time)

1. **Open TWS and log in to your paper account**
   - At the login screen, tick **"Paper Trading"** before clicking Log In
   - Your paper account username is the same as your live username

2. **Enable the API**
   - Go to: `Edit → Global Configuration → API → Settings`
   - Tick **"Enable ActiveX and Socket Clients"**
   - Set **Socket port** to `7497` (TWS paper default)
   - Tick **"Allow connections from localhost only"** (security)
   - Under "Trusted IP Addresses" add `127.0.0.1` if prompted
   - Click **Apply** then **OK**

3. **Restart TWS** after changing API settings (required for changes to take effect)

---

## 3. Config check (`config.py`)

Open `scans/live_multi/config.py` and confirm:

```python
IB_PORT      = 7497          # TWS paper — correct
IB_CLIENT_ID = 20            # fine as-is; change only if another script uses id 20
ALLOW_LIVE_PORT = False      # leave False — safety rail against live account
```

If you use **IB Gateway** instead of TWS, change the port to `4002`.

---

## 4. First live paper run

With TWS open and logged into the paper account:

```
cd Investment-Strat-clean/scans/live_multi
python multi_trader.py
```

This will:
1. Connect to TWS on port 7497
2. Read your paper account's net liquidation value
3. Download prices for ~775 symbols (cached after first run — takes ~2 min)
4. Run the quarterly fundamental screen if due
5. Scan both systems for entry signals
6. Place Market-On-Open BUY orders for any signals, each with a GTC stop

---

## 5. Verify in TWS after running

In TWS, go to **Activity Monitor → Orders**:

- You should see BUY orders tagged `LM_QULL` (Qullamaggie) and/or `LM_HYBRID` (Hybrid)
- Each entry BUY is a **Market-On-Open** order — it fills at the next day's open
- Each entry should have a corresponding **GTC Stop** order at the calculated stop price

If the market was NEUTRAL or BEAR when you ran, Qullamaggie may produce no orders —
that is correct behaviour. Hybrid will typically find 1–3 signals.

To check open positions and state at any time:
```
python multi_trader.py --status
```

---

## 6. Daily schedule

Run once per day after the US market close. EOD prices are available from
Yahoo Finance ~30 minutes after the 4pm ET close.

**Option A — Manual (recommended to start)**

Each weekday after 4:30pm ET, run:
```
python multi_trader.py
```

**Option B — Auto-scheduler (stays running in background)**

```
python multi_trader.py --schedule
```

Fires automatically every weekday at 16:30 local time. Keep the terminal open
(or run it in a background process / Windows service).

**Option C — Windows Task Scheduler**

Create a task that runs daily at 16:30 (Mon–Fri):
- Program: `python`
- Arguments: `multi_trader.py`
- Start in: `C:\...\Investment-Strat-clean\scans\live_multi`

---

## 7. What happens each daily run

```
1. Connect to IB → read NetLiquidation
2. Download EOD prices for russell1000 + sp500 universe (cached to disk)
3. Check market health (SPY vs 50/200MA)
4. Run quarterly fundamental screen if 88+ days since last run
5. For each system (QULL, HYBRID):
   a. Reconcile: check if pending entry orders filled; check if stop orders hit
   b. Trail stops: update GTC stop orders upward for open positions
   c. Scan: find new entry signals
   d. Place: MOO entry + GTC stop for each new signal
   e. Save state to state/state_QULL.json / state_HYBRID.json
6. Print combined daily report to terminal + multi_trader.log
```

---

## 8. Order tags in TWS

Every order is stamped with a system tag in the IB `orderRef` field:

| Tag | System |
|-----|--------|
| `LM_QULL` | Qullamaggie (system 3) |
| `LM_HYBRID` | Hybrid Balanced (system 4) |

You can filter TWS's order blotter by these tags to see each system's activity
independently, even if both systems hold the same stock.

---

## 9. State files

Each system persists its positions and order IDs to:
```
scans/live_multi/state/state_QULL.json
scans/live_multi/state/state_HYBRID.json
```

These are updated atomically after every run. If you need to inspect or
manually correct a position, edit the JSON directly and re-run with `--status`
to verify.

Do **not** delete the state files while positions are open — the script uses
them to track which IB order IDs belong to each system.

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Cannot connect to IB TWS/Gateway` | TWS not running or API not enabled | Start TWS, check API settings (step 2) |
| `Refusing to connect: IB_PORT not a paper port` | Port is a live port | Check `config.py` — use 7497 or 4002 |
| `No universe symbols found` | Universe CSV path wrong | Check `config.DATA_DIR` points to `backtesting/data/` |
| Orders appear but don't fill | MOO orders fill at next day's open | Normal — check TWS the following morning |
| `ib_insync not installed` | Missing dependency | `pip install ib_insync` |
| Two scripts connected with same client ID | Client ID conflict | Change `IB_CLIENT_ID` in config.py |
