# Investment-Strat-clean

A momentum / breakout equity trading system rooted in Minervini's SEPA
methodology, with backtesting, scanning, risk management, and a live
Interactive Brokers runner. This repository is the **canonical** copy of the
project; the loose files in the parent `GitHub/` folder are an older workspace
kept only for history.

> **Status:** Active clean-up toward go-live. See `PROJECT_PLAN.md` for the full
> roadmap. The goal is one trusted backtest harness, an objective strategy
> bake-off, and the winning strategy running on IB **paper** trading before any
> real capital is committed.

---

## What this system does

The system screens equities (US and ASX universes) for high-conviction
momentum and breakout setups using a blend of Minervini fundamentals and
technical criteria, sizes positions with explicit risk rules, backtests
candidate strategies, and can place and manage orders through Interactive
Brokers.

A core idea throughout is a **market-health overlay**: position sizing is cut
in weak markets and increased in confirmed bull markets, since the strategies
perform far better in strong-bull regimes than in bear regimes.

---

## Strategy families

- **5LC (5 Level Conviction)** — the most developed strategy and the current
  front-runner. Minervini fundamentals + technicals with a SPY market-health
  overlay. Has both S&P 500 and ASX300 versions.
  → `strategies/minervini/5LC/`, `strategies/minervini/ASX300/`
- **Conviction scanners** — Standard and Consolidation/VCP variants for ASX300,
  plus international (Germany, Hong Kong, UK).
  → `strategies/conviction-asx300/`, `strategies/international/`
- **Earlier experiments** — Qullamaggie, Turtle, multi-stock breakout, and
  SPY-200MA trend systems. Candidates for the bake-off, then archival.
- **Small caps** — `strategies/smallcaps/`

The objective bake-off that picks the single winner is described in
`PROJECT_PLAN.md`, section 5.

---

## Repository layout

| Path | What's in it |
|------|--------------|
| `strategies/` | Strategy logic, organised by family (Minervini/5LC, conviction, international, smallcaps). |
| `scans/live/` | The Interactive Brokers live/paper trading runner — connects to TWS, syncs positions, manages chandelier trailing stops, places orders, persists state. |
| `scans/` | Scanners, fundamentals/technical/liquidity screeners, and risk docs (`RISK_MANAGEMENT_FRAMEWORK.md`). |
| `backtesting/` | Backtester, data (`data/*_symbols.csv` universes), and configs (`config/*_config.json`). Basis for the planned unified harness. |
| `breakout-scanner/` | Breakout scanning experiments. |
| `scanners/` | Daily conviction scanner. |
| `strategies/`, `testing/` | Active strategies and ~50 experimental variants (the latter to be archived). |
| `results/`, `reports/`, `logs/` | Run outputs and logs (regenerable; largely git-ignored). |
| `_archive/` | Older systems and superseded code kept for reference. |
| `PROJECT_PLAN.md` | The clean-up and go-live plan. Start here. |

---

## Setup

This project targets Python 3. From the repository root:

```bash
# 1. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

`TA-Lib` depends on a C library that must be installed before the Python
package — see the note at the top of `requirements.txt`.

Live trading additionally requires Interactive Brokers **TWS** or **IB Gateway**
running locally with API access enabled. Always point it at a **paper** account
first.

---

## A note on the numbers

Backtest figures in this repo are **not yet verified**. Several historical runs
allowed cash to go negative (i.e. silent leverage), so results must be treated
as unconfirmed until they come out of the corrected, cash-constrained harness
described in `PROJECT_PLAN.md`. Paper trading is the gate before any real money,
and then only at small size.

This repository is engineering and research. Nothing here is financial advice
or a recommendation to trade any strategy.
