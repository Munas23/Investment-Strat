# Signal Generation — How Conviction Levels Work

*Covers systems 3 (Qullamaggie) and 4 (Hybrid Balanced), the Phase-2 bake-off
advancement winners running in `live_multi`.*

---

## Market health (shared gate for both systems)

Market health is read from SPY moving averages every day before scanning:

| Health | Condition | Effect |
|--------|-----------|--------|
| Bull | SPY > 200MA, 50MA > 200MA | Full entries |
| Uptrend | SPY > 50MA | Full entries |
| Neutral | SPY between 50MA and 200MA | Full entries (fewer breakouts naturally) |
| Choppy | SPY < 50MA but > 200MA | Full entries (caution warranted) |
| Bear | SPY < 200MA | **No new entries** — stops trail only |

---

## System 3 — Qullamaggie Aggressive

### Entry gate (all required before any signal fires)

1. Today's close is a new **20-day high** (Donchian breakout)
2. Price is **within 10% of the 52-week high**
3. **Day return ≥ 3%** AND **volume ≥ 1.5× the 20-day average** — both required

### Conviction levels

| Level | Additional requirement | Typical frequency |
|-------|------------------------|-------------------|
| 3 | Passes all base gates above | A few times per week in bull |
| 4 | Volume ≥ 2× average AND day return ≥ 5% | Once or twice per week |
| 5 | Volume ≥ 3× average AND day return ≥ 8% | A few times per month |

### Why Qullamaggie is quiet in neutral markets

This system hunts "episodic pivot" days — a single explosive breakout session
where a stock jumps 5–8%+ on 2–3× normal volume. These genuinely don't happen
every day. In the bake-off it averaged roughly 2 entries per week across the
entire russell1000 universe. Zero signals on a given neutral-market day is normal.
Signals cluster in bull runs and around earnings catalysts.

---

## System 4 — Hybrid Balanced

### Entry gate (all required before any signal fires)

1. Price is **above the 50-day MA**
2. Price is **within 20% of the 52-week high**
3. Today's close is a new **20-day high** (Donchian breakout)

### Conviction levels

| Level | Additional requirement | Meaning |
|-------|------------------------|---------|
| 3 | Passes all base gates, but price **below** the 200MA | Early-stage recovery; smaller position |
| 4 | Price **above** the 200MA (but not full Stage 2) | Established uptrend, MA order not perfect |
| 5 | **Stage 2 alignment** (close > 50MA > 150MA > 200MA) AND **RS rank > 10** | Full Minervini template — biggest position |

Stage 2 alignment means all four moving averages are stacked in the correct order
(price on top, then 50MA, then 150MA, then 200MA at the bottom — all rising).
RS rank > 10 means the stock's 3-month return is at least 10 percentage points
above SPY over the same period.

### Why you see mostly conviction-5 signals

Stocks that break to 20-day highs while above their 50MA and near their 52-week
high tend to already be in strong uptrends — which means they often have Stage 2
alignment and positive RS. So the base gate is self-selecting for the best
technical setups, which naturally score conviction 5.

Conviction 3 and 4 signals appear more often when:
- The market broadens out and more stocks break out, including some in early
  uptrend stages
- The fundamental universe is larger (it contracted to 41 stocks in Jan 2026 as
  earnings season hit; it was 129 in mid-2025)
- You're coming out of a correction and stocks are repairing their MAs at
  different rates

---

## Position sizing by conviction

Both systems use the same formula:

```
dollar_risk  = account_value × base_risk% × conviction_multiplier
stop_distance = entry_price − stop_price
shares        = dollar_risk / stop_distance
position_value capped at: account_value / max_positions
```

| System | Base risk | Conv 5 mult | Conv 4 mult | Conv 3 mult | Max positions |
|--------|-----------|-------------|-------------|-------------|---------------|
| Qullamaggie | 2.0% | 1.5× | 1.25× | 1.0× | 15 |
| Hybrid | 1.5% | 1.5× | 1.25× | 1.0× | 12 |

Example (Hybrid, $100k account, conviction 5):
- Dollar risk = $100,000 × 1.5% × 1.5 = $2,250
- If stop is 5% away on a $100 stock → stop distance = $5 → shares = 450
- Position value = 450 × $100 = $45,000 (but capped at $100k / 12 = $8.3k per slot)

The position cap kicks in when stop distance is tight relative to account size —
protecting against over-concentration in any single name.

---

## Stop methods

**Qullamaggie — ATR-based:**
Stop placed at `entry − (ATR_multiplier × ATR)`. Multiplier is 1.5× for
conviction 5, 2.0× for conviction 4, 2.5× for conviction 3 (tighter stops on
your best setups, more room on marginal ones). Trails as a chandelier: tightens
from `peak − 3×ATR` to `peak − 2×ATR` after 30 holding days.

**Hybrid — ATR with cap:**
Same ATR formula, but capped so the stop can never be wider than:
- Conviction 5: max 5% below entry
- Conviction 4: max 7% below entry
- Conviction 3: max 8% below entry

On a highly volatile stock where 1.5×ATR would put the stop 8% away, the cap
overrides it and uses 5% instead — giving a tighter stop and therefore a larger
position for the same dollar risk.

---

## What a normal week looks like

| Market | Qullamaggie signals/week | Hybrid signals/week |
|--------|--------------------------|---------------------|
| Bear | 0 (entries blocked) | 0 (entries blocked) |
| Neutral | 0–2 | 1–4 |
| Uptrend / Bull | 2–6 | 3–8 |

Signals are not evenly spread — they cluster around market breakouts, strong
earnings weeks, and sector rotations. Long quiet periods followed by bursts of
activity is normal behaviour for both systems.
