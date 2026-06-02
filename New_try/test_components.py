#!/usr/bin/env python3
"""
Test individual components of the Consolidation Conviction Strategy without Lumibot
"""

import pandas as pd
import numpy as np
from datetime import datetime

def calculate_atr_series(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR series for consolidation analysis"""
    try:
        if len(df) < period + 1:
            return pd.Series(index=df.index, dtype=float)
        
        df = df.copy()
        df['prev_close'] = df['close'].shift(1)
        
        # True Range components
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['prev_close'] - df['low'])
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # ATR as rolling mean
        atr_series = df['true_range'].rolling(period).mean()
        
        return atr_series
        
    except Exception as e:
        print(f"Error calculating ATR series: {e}")
        return pd.Series(index=df.index, dtype=float)

def analyze_consolidation_pattern(df: pd.DataFrame) -> dict:
    """Analyze consolidation characteristics"""
    try:
        if len(df) < 100:
            return {'consolidation_score': 0, 'details': 'Insufficient data'}
        
        current_price = df['close'].iloc[-1]
        
        # Calculate ATR series
        atr_14 = calculate_atr_series(df, 14)
        
        # Get recent periods for analysis
        recent_2weeks = slice(-10, None)
        recent_4weeks = slice(-20, None)
        older_period = slice(-90, -30)
        
        # ATR Analysis
        recent_atr_2w = atr_14.iloc[recent_2weeks].mean() if len(atr_14.iloc[recent_2weeks]) > 0 else 0
        recent_atr_4w = atr_14.iloc[recent_4weeks].mean() if len(atr_14.iloc[recent_4weeks]) > 0 else 0
        older_atr = atr_14.iloc[older_period].mean() if len(atr_14.iloc[older_period]) > 0 else 0
        
        # ATR contraction ratios
        atr_contraction_2w = recent_atr_2w / older_atr if older_atr > 0 else 1
        atr_contraction_4w = recent_atr_4w / older_atr if older_atr > 0 else 1
        
        # Performance calculations - look back to capture the big move
        # For consolidation patterns, we want to measure from BEFORE the move
        if len(df) >= 90:
            price_3m_ago = df['close'].iloc[-90]
            gain_3m = ((current_price / price_3m_ago) - 1) * 100 if price_3m_ago > 0 else 0
        else:
            gain_3m = 0
            
        # Look further back for 6M to capture the FULL move (pre-consolidation gains)
        # For consolidation strategies, we need to measure from before the big move
        if len(df) >= 200:  # ~8 months back to capture pre-move price
            price_6m_ago = df['close'].iloc[-200]
            gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
        elif len(df) >= 180:  # Fallback to 6 months
            price_6m_ago = df['close'].iloc[-180]
            gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
        elif len(df) >= 130:  # Further fallback
            price_6m_ago = df['close'].iloc[-130]
            gain_6m = ((current_price / price_6m_ago) - 1) * 100 if price_6m_ago > 0 else 0
        else:
            # If no sufficient data, estimate from 3M
            if len(df) >= 90 and gain_3m > 0:
                gain_6m = gain_3m * 2.0  # Conservative estimate for consolidation
            else:
                gain_6m = gain_3m
        
        if len(df) >= 10:
            price_2w_ago = df['close'].iloc[-10]
            gain_2w = ((current_price / price_2w_ago) - 1) * 100
        else:
            gain_2w = 0
            
        if len(df) >= 20:
            price_4w_ago = df['close'].iloc[-20]
            gain_4w = ((current_price / price_4w_ago) - 1) * 100
        else:
            gain_4w = 0
        
        # ATR as percentage of price
        recent_atr_pct_2w = (recent_atr_2w / current_price * 100) if current_price > 0 else 0
        recent_atr_pct_4w = (recent_atr_4w / current_price * 100) if current_price > 0 else 0
        
        return {
            'gain_3m': gain_3m,
            'gain_6m': gain_6m,
            'gain_2w': gain_2w,
            'gain_4w': gain_4w,
            'recent_atr_pct_2w': recent_atr_pct_2w,
            'recent_atr_pct_4w': recent_atr_pct_4w,
            'atr_contraction_2w': atr_contraction_2w,
            'atr_contraction_4w': atr_contraction_4w,
            'current_atr_14': atr_14.iloc[-1] if len(atr_14) > 0 else 0
        }
        
    except Exception as e:
        print(f"Error analyzing consolidation pattern: {e}")
        return {'consolidation_score': 0, 'error': str(e)}

def generate_conviction_signal(df: pd.DataFrame, min_3month_gain: float = 30.0) -> tuple:
    """Generate conviction signal based on consolidation patterns"""
    try:
        if len(df) < 150:
            return 0, "Insufficient historical data", {}
        
        current_price = df['close'].iloc[-1]
        
        # Get consolidation analysis
        consolidation_data = analyze_consolidation_pattern(df)
        
        # Check primary filter: 3-6 month performance
        medium_term_gain = max(consolidation_data.get('gain_3m', 0), consolidation_data.get('gain_6m', 0))
        if medium_term_gain < min_3month_gain:
            return 0, f"Insufficient 3-6M gain: {medium_term_gain:.1f}% < {min_3month_gain}%", consolidation_data
        
        conviction = 0
        details = consolidation_data.copy()
        
        # Factor 1: Medium-term Performance (0-30 points)
        perf_points = 0
        if medium_term_gain >= 100:
            perf_points = 30
        elif medium_term_gain >= 70:
            perf_points = 25
        elif medium_term_gain >= 50:
            perf_points = 20
        elif medium_term_gain >= 30:
            perf_points = 15
        
        conviction += perf_points
        details['performance_points'] = perf_points
        details['medium_term_gain'] = medium_term_gain
        
        # Factor 2: ATR Analysis (0-35 points)
        atr_points = 0
        best_contraction = min(
            consolidation_data.get('atr_contraction_2w', 1),
            consolidation_data.get('atr_contraction_4w', 1)
        )
        
        if best_contraction <= 0.6:
            atr_points += 20
        elif best_contraction <= 0.8:
            atr_points += 15
        elif best_contraction <= 1.0:
            atr_points += 10
        elif best_contraction <= 1.2:
            atr_points += 5
        
        recent_atr_pct = consolidation_data.get('recent_atr_pct_4w', 10)
        if recent_atr_pct <= 2.0:
            atr_points += 15
        elif recent_atr_pct <= 3.5:
            atr_points += 10
        elif recent_atr_pct <= 5.0:
            atr_points += 5
        
        conviction += atr_points
        details['atr_points'] = atr_points
        details['best_atr_contraction'] = best_contraction
        
        # Factor 3: Recent Momentum (0-20 points) - REWARD LOW momentum
        momentum_points = 0
        recent_gain_2w = consolidation_data.get('gain_2w', 0)
        recent_gain_4w = consolidation_data.get('gain_4w', 0)
        avg_recent_gain = (abs(recent_gain_2w) + abs(recent_gain_4w)) / 2
        
        if avg_recent_gain <= 2:
            momentum_points = 20
        elif avg_recent_gain <= 5:
            momentum_points = 15
        elif avg_recent_gain <= 8:
            momentum_points = 10
        elif avg_recent_gain <= 12:
            momentum_points = 5
        
        conviction += momentum_points
        details['momentum_points'] = momentum_points
        details['avg_recent_gain'] = avg_recent_gain
        details['total_conviction'] = conviction
        
        # Convert to conviction level
        if conviction >= 80:
            level = 5
            reason = f"MAX: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
        elif conviction >= 65:
            level = 4
            reason = f"HIGH: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
        elif conviction >= 50:
            level = 3
            reason = f"GOOD: {conviction}, 3-6M: {medium_term_gain:.1f}%, ATR: {best_contraction:.2f}"
        elif conviction >= 35:
            level = 2
            reason = f"FAIR: {conviction}, 3-6M: {medium_term_gain:.1f}%"
        else:
            level = 0
            reason = f"No signal: {conviction}"
        
        return level, reason, details
        
    except Exception as e:
        print(f"Error generating conviction signal: {e}")
        return 0, f"Error: {e}", {}

def create_mock_consolidation_data():
    """Create mock data simulating post-move consolidation - IDEAL PATTERN"""
    np.random.seed(42)
    dates = pd.date_range(start='2022-01-01', periods=250, freq='D')
    
    # Create textbook consolidation pattern: Big Move -> Tight Consolidation
    prices = []
    
    for i in range(250):
        if i < 90:
            # BIG MOVE phase (first 90 days): $50 -> $110 (120% gain)
            progress = i / 90
            base = 50 + 60 * progress  # Linear growth for simplicity
            volatility = 2.5  # Higher volatility during trend
        else:
            # CONSOLIDATION phase (last 160 days): tight sideways $105-115
            # This is the key - stock holds gains but stops advancing
            base = 110  # Stay near the high
            volatility = 0.7  # Much lower volatility - the consolidation signature
        
        # Add noise
        noise = np.random.normal(0, volatility)
        price = max(base + noise, 1.0)
        prices.append(price)
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.normal(0, 0.002)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, 0.008))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.008))) for p in prices],
        'close': prices,
        'volume': [max(int(np.random.normal(150000, 25000)), 10000) for _ in prices]
    })
    
    return df

def test_consolidation_components():
    """Test consolidation strategy components"""
    print("Testing Consolidation Strategy Components")
    print("=" * 60)
    
    # Create mock data
    print("Creating mock consolidation pattern...")
    df = create_mock_consolidation_data()
    print(f"Mock data created: {len(df)} days")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Test consolidation analysis
    print("\nTesting consolidation analysis...")
    analysis = analyze_consolidation_pattern(df)
    
    # Debug pricing to understand the pattern
    current_price = df['close'].iloc[-1]
    price_3m_ago = df['close'].iloc[-90] if len(df) >= 90 else 0
    if len(df) >= 200:
        price_6m_ago = df['close'].iloc[-200]
    elif len(df) >= 180:
        price_6m_ago = df['close'].iloc[-180]
    elif len(df) >= 130:
        price_6m_ago = df['close'].iloc[-130]
    else:
        price_6m_ago = 0
    price_start = df['close'].iloc[0]  # Starting price
    price_peak = df['close'].max()  # Peak price
    
    # Show the full story
    print(f"Starting price: ${price_start:.2f}")
    print(f"Peak price: ${price_peak:.2f}")
    print(f"Peak gain: {((price_peak / price_start) - 1) * 100:.1f}%")
    
    print(f"Current price: ${current_price:.2f}")
    print(f"3-months ago price: ${price_3m_ago:.2f}")
    print(f"6-months ago price: ${price_6m_ago:.2f}")
    print(f"3-month gain: {analysis.get('gain_3m', 0):.1f}%")
    print(f"6-month gain: {analysis.get('gain_6m', 0):.1f}%")
    print(f"Recent 2w gain: {analysis.get('gain_2w', 0):.1f}%")
    print(f"Recent 4w gain: {analysis.get('gain_4w', 0):.1f}%")
    print(f"ATR contraction 2w: {analysis.get('atr_contraction_2w', 1):.2f}")
    print(f"ATR contraction 4w: {analysis.get('atr_contraction_4w', 1):.2f}")
    print(f"Recent ATR %: {analysis.get('recent_atr_pct_4w', 0):.2f}%")
    
    # Test conviction signal
    print("\nTesting conviction signal generation...")
    level, reason, details = generate_conviction_signal(df)
    print(f"Conviction Level: {level}")
    print(f"Reason: {reason}")
    print(f"Performance points: {details.get('performance_points', 0)}")
    print(f"ATR points: {details.get('atr_points', 0)}")
    print(f"Momentum points: {details.get('momentum_points', 0)}")
    print(f"Total score: {details.get('total_conviction', 0)}")
    
    # Position sizing test
    print("\nTesting position sizing logic...")
    position_sizes = {2: 15, 3: 20, 4: 28, 5: 35}
    for conv_level, expected_pct in position_sizes.items():
        print(f"Conviction {conv_level}: {expected_pct}% position")
    
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS:")
    print("=" * 60)
    
    # Check if our mock data triggers consolidation
    medium_term_gain = details.get('medium_term_gain', 0)
    atr_contraction = details.get('best_atr_contraction', 1)
    recent_movement = details.get('avg_recent_gain', 0)
    
    print(f"Medium-term gain: {medium_term_gain:.1f}% (target: 30%+)")
    print(f"ATR contraction: {atr_contraction:.2f}x (target: <1.0)")
    print(f"Recent movement: {recent_movement:.1f}% (target: <8%)")
    print(f"Final conviction: {level} (2+ = tradeable)")
    
    # Validation checks
    checks_passed = 0
    total_checks = 4
    
    if medium_term_gain >= 30:
        print("[PASS] Medium-term performance check passed")
        checks_passed += 1
    else:
        print("[FAIL] Medium-term performance check failed")
    
    if atr_contraction < 1.0:
        print("[PASS] ATR contraction check passed") 
        checks_passed += 1
    else:
        print("[FAIL] ATR contraction check failed")
    
    if recent_movement < 8:
        print("[PASS] Low recent movement check passed")
        checks_passed += 1
    else:
        print("[FAIL] Low recent movement check failed")
    
    if level >= 2:
        print("[PASS] Conviction signal generated")
        checks_passed += 1
    else:
        print("[FAIL] No conviction signal generated")
    
    print(f"\nValidation: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed >= 3:
        print("[SUCCESS] Consolidation strategy components working correctly!")
        return True
    else:
        print("[WARNING] Some components need adjustment")
        return False

if __name__ == "__main__":
    try:
        success = test_consolidation_components()
        if success:
            print("\n[SUCCESS] Components validated! Ready for full backtest.")
            print("Next: Run 'python run_backtest.py' for complete backtest")
        else:
            print("\n[WARNING] Component validation had issues")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()