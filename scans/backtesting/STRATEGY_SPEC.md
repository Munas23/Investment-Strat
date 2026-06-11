# Strategy Specification — Locked Parameters

*Owner: Ash. Generated 5 June 2026, after the Phase 2 bake-off (120 runs, zero failures).*
*This file is the single source of truth for the parameters that advance to paper trading.*
*Any change here must be re-validated by re-running the bake-off.*

---

## Advancement decisions

| Universe     | Strategy (system) | Exit       | Stops          | Max positions | Position cap |
|--------------|-------------------|------------|----------------|---------------|--------------|
| russell1000  | Qullamaggie (3)   | time_trail | ATR-based      | 15            | 6.7%         |
| nasdaq100    | Qullamaggie (3)   | time_trail | ATR-based      | 15            | 6.7%         |
| sp500        | Hybrid (4)        | adaptive   | ATR + cap      | 12            | 8.3%         |
| asx300       | **HOLD**          | —          | —              | —             | —            |

ASX is held pending the Phase 3a recalibration (market-aware screening profile
+ loosened VCP gate, both now in code) being re-run on real data. Do not paper
trade AU until the recalibrated bake-off shows a viable cohort.

Position cap = `min(100 / max_positions, 15)` %, so every slot can be filled
simultaneously without breaching 100% exposure.

---

## Qullamaggie (system 3) — russell1000, nasdaq100

Locked config (from `run_backtest.SYSTEMS[3]`, with the bake-off engine fixes applied):

```
base_risk              : 2.0 %
min_conviction         : 3
max_positions          : 15
max_total_risk         : 25 %
conviction_multipliers : {5: 1.5, 4: 1.25, 3: 1.0}
exit_method            : time_trail
stop_method            : ATR-based   (see note)
```

Entry signal (`technical_scanner._score_system3`): 20-day Donchian breakout,
price within 10% of the 52-week high, an explosive up day (>= 3%) on >= 1.5x
average volume. Conviction 5 needs >= 3x volume and >= 8% day; conviction 4
needs >= 2x volume and >= 5% day; else conviction 3.

**Note on stops:** `SYSTEMS[3]` declares `stop_method: 'pattern'`. The
advancement decision uses ATR-based stops, which the bake-off engine applied
once the exit methods were wired. Before paper trading, confirm `stop_method`
is set to `'atr'` (with `atr_multipliers {5: 1.5, 4: 2.0, 3: 2.5}`) so the
production config matches the backtest that produced the advancement numbers.

Bake-off performance (full period, risk-adjusted composite winner):
russell1000 — CAGR 15.5%, Calmar 2.10, Sharpe 1.37, max DD -7.4%, win rate 53–56%.
nasdaq100 — CAGR 7.9%, Calmar 1.64, Sharpe 0.89, max DD -4.8%.
Strongest all-weather US system; best bear-2022 alpha on every universe.

---

## Hybrid Balanced (system 4) — sp500

Locked config (from `run_backtest.SYSTEMS[4]`):

```
base_risk              : 1.5 %
min_conviction         : 3
max_positions          : 12
max_total_risk         : 18 %
conviction_multipliers : {5: 1.5, 4: 1.25, 3: 1.0}
exit_method            : adaptive   (scaled in bull, let_run in bear)
stop_method            : atr_with_cap
atr_multipliers        : {5: 1.5, 4: 2.0, 3: 2.5}
```

Entry signal (`technical_scanner._score_system4`): price above the 50-day MA,
within 20% of the 52-week high, and a 20-day Donchian breakout. Conviction 5 on
full Stage-2 alignment + RS > 10; conviction 4 if above the 200-day MA; else 3.

Bake-off performance (full period winner, sp500): CAGR 14.5%, Calmar 1.69,
Sharpe 1.06, max DD -8.6%. Most consistent cross-period profile; the adaptive
exit contributes.

---

## Eliminated / parked

- **High Conviction Only (5):** biggest drawdowns (-14% to -24%) with no return
  premium. Eliminated.
- **VCP (6):** signal-starved in the bake-off. Gate loosened in Phase 3a
  (proximity 10%→15%, ATR contraction 0.85→0.92). Re-evaluate after the next run
  before any advancement.
- **5LC (8) vs Conviction (7):** no universal winner from the fundamental gate
  (5LC edges nasdaq100, Conviction edges sp500). Kept as research candidates.

---

## Live-scanner alignment (action required before paper trading)

The production daily scanner is `scanners/conviction-daily/5lc_daily_scanner.py`,
which implements the **5LC** logic — *not* the advancement winners (Qullamaggie,
Hybrid). Two divergences must be resolved so live entries match the backtest:

1. **Strategy mismatch.** The advancement winners are systems 3 and 4. Either
   (a) point the production scanner at the Qullamaggie/Hybrid entry rules in
   `technical_scanner._score_system3` / `_score_system4`, or (b) keep 5LC as a
   separate fundamental-gated track and stand up Qullamaggie/Hybrid scanners for
   the US universes. **This is Ash's call** and is the gate for Phase 5.
2. **Fundamental gate.** The scanner uses a 55% fundamental-score gate
   (`fundamental_thresholds.min_score = 55.0`); the harness uses the integer
   `min_fundamental` per system. Whichever strategy goes live, the two gates must
   express the same filter, or live and backtested universes will diverge.
