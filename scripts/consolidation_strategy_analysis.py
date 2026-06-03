"""
Consolidation Conviction Strategy - Professional Market Research Analysis
========================================================================

Market Research Analysis by Senior Analyst
20+ Years Quantitative Research Experience

STRATEGY METHODOLOGY ANALYSIS
============================

The Consolidation Conviction Scanner implements a sophisticated post-move consolidation 
strategy that targets stocks exhibiting specific technical and fundamental characteristics.

CORE STRATEGY COMPONENTS:
========================

1. POST-MOVE IDENTIFICATION
---------------------------
- Primary Filter: 30%+ gains over 3-6 month period
- Philosophy: Catch stocks AFTER major moves, during digestion phase
- Logic: Stocks that have moved significantly often consolidate before next leg

2. CONSOLIDATION DETECTION
--------------------------
- Key Metric: ATR (Average True Range) Analysis
- ATR Contraction: Recent ATR must be ≤80% of longer-term ATR
- Time Frames: 2-week, 4-week, 6-week consolidation analysis
- Range Analysis: Tight recent trading ranges preferred

3. MOMENTUM DAMPENING REQUIREMENT
---------------------------------
- Recent 2-4 week performance should be LOW (consolidation, not continuation)
- Rewards minimal recent movement (≤5% preferred)
- Inverts traditional momentum strategies

4. SCORING METHODOLOGY (0-100 points)
------------------------------------
- Performance Points (0-30): Rewards strong 3-6M gains
- ATR Points (0-35): Primary factor - rewards ATR contraction
- Momentum Points (0-20): Rewards LOW recent momentum
- Volume Points (0-15): Normal/decreasing volume preferred

5. POSITION SIZING & RISK MANAGEMENT
------------------------------------
- Conviction Levels 0-5 mapped to 0%, 15%, 20%, 25%, 30%, 35% positions
- 8% stop losses (tighter than typical growth strategies)
- 40% profit targets
- Only Level 2+ generate BUY signals

THEORETICAL STRENGTHS:
=====================
1. Counter-cyclical timing - enters after euphoria subsides
2. Technical rigor - ATR analysis provides objective consolidation measure
3. Risk management - tight stops and graduated position sizing
4. Multi-timeframe analysis - captures different consolidation patterns
5. Volume confirmation - avoids low-interest names

THEORETICAL WEAKNESSES:
======================
1. False Breakout Risk - consolidations may continue indefinitely
2. Market Regime Dependency - may underperform in trending markets
3. Data Staleness - Yahoo Finance fundamental data lag
4. Limited Universe - hardcoded stock lists vs dynamic screening
5. Transaction Cost Impact - frequent small positions
6. Survivorship Bias - static lists don't account for delistings

MARKET CONTEXT CONSIDERATIONS:
=============================
- Strategy assumes mean reversion after momentum exhaustion
- May struggle in persistent trending environments
- Sector rotation could impact performance significantly
- Interest rate environment affects growth stock consolidation patterns

RESEARCH HYPOTHESIS:
===================
H1: Post-move consolidation patterns predict future breakouts
H2: ATR contraction is a reliable consolidation indicator
H3: Strategy generates alpha vs buy-and-hold benchmarks
H4: Risk-adjusted returns justify implementation costs

"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("CONSOLIDATION CONVICTION STRATEGY - METHODOLOGY ANALYSIS")
print("=" * 60)
print("Analysis completed. Strategy components identified and documented.")
print("\nKey Findings:")
print("• Post-move consolidation thesis with ATR-based detection")
print("• Multi-factor scoring system (0-100 points)")
print("• Risk management through graduated position sizing")
print("• Potential weaknesses in trending markets and data quality")
print("=" * 60)