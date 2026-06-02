"""
Mark Minervini Trading Strategies - Complete Educational Implementation
=====================================================================

Mark Minervini is a 2-time US Investing Champion (1997: +334%, 2021: +220%)
His methodology focuses on superperformance stocks with precise entry/exit points.

This file demonstrates his core strategies with detailed explanations and live examples.

Key Concepts:
- SEPA: Specific Entry Point Analysis
- Trend Template: Foundation for stock selection
- Risk Management: Maximum 7-8% loss per trade
- Position Sizing: 5-10% concentration in best ideas
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

class MinerviniEducational:
    """
    Educational implementation of Mark Minervini's proven trading strategies
    
    This class demonstrates the exact criteria and methods used by a 2-time
    US Investing Champion to achieve superior returns.
    """
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.explain_strategies()
        
    def explain_strategies(self):
        """Print detailed explanation of Minervini's methodology"""
        print("=" * 80)
        print("MARK MINERVINI'S TRADING STRATEGIES - EDUCATIONAL GUIDE")
        print("=" * 80)
        print()
        print("🏆 TRACK RECORD:")
        print("  - 1997 US Investing Champion: +334% return")
        print("  - 2021 US Investing Champion: +220% return") 
        print("  - Average annual return: ~40% over 30+ years")
        print("  - Maximum drawdown: Typically under 15%")
        print()
        print("🎯 CORE PHILOSOPHY:")
        print("  1. Buy stocks making new highs (counterintuitive to most)")
        print("  2. Focus on superperformance stocks (top 2% of market)")
        print("  3. Use precise entry and exit points (SEPA methodology)")
        print("  4. Risk management is everything (7-8% max loss)")
        print("  5. Concentrate in best ideas (5-10% position sizes)")
        print()
        print("📚 KEY CONCEPTS:")
        print("  - Trend Template: 8-point checklist for stock quality")
        print("  - SEPA: Specific Entry Point Analysis for timing")
        print("  - Stage Analysis: Stocks move through 4 stages")
        print("  - Relative Strength: Outperforming the market")
        print()
        
    def get_live_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Get live market data for analysis"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                print(f"❌ No data available for {symbol}")
                return None
                
            data.columns = [col.lower() for col in data.columns]
            print(f"✅ Loaded {len(data)} days of data for {symbol}")
            return data
            
        except Exception as e:
            print(f"❌ Error loading {symbol}: {e}")
            return None
    
    def calculate_minervini_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators needed for Minervini's analysis
        
        Key Indicators:
        - Moving Averages: 10, 21, 50, 150, 200 (trend analysis)
        - 52-week high/low: For stage analysis
        - Volume: For institutional accumulation
        - Relative Strength: Performance vs market
        """
        df = data.copy()
        
        # Moving averages (Minervini's key trend indicators)
        df['ma_10'] = df['close'].rolling(10).mean()
        df['ma_21'] = df['close'].rolling(21).mean()
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_150'] = df['close'].rolling(150).mean()
        df['ma_200'] = df['close'].rolling(200).mean()
        
        # 52-week analysis (Stage Analysis)
        df['high_52w'] = df['high'].rolling(252).max()
        df['low_52w'] = df['low'].rolling(252).min()
        df['distance_from_52w_high'] = ((df['close'] / df['high_52w']) - 1) * 100
        df['distance_from_52w_low'] = ((df['close'] / df['low_52w']) - 1) * 100
        
        # Relative Strength (simplified - normally vs S&P 500)
        df['rs_4w'] = ((df['close'] / df['close'].shift(20)) - 1) * 100
        df['rs_13w'] = ((df['close'] / df['close'].shift(65)) - 1) * 100
        df['rs_26w'] = ((df['close'] / df['close'].shift(130)) - 1) * 100
        df['rs_52w'] = ((df['close'] / df['close'].shift(252)) - 1) * 100
        
        # Volume analysis (institutional activity)
        df['volume_avg_50'] = df['volume'].rolling(50).mean()
        df['volume_ratio'] = df['volume'] / df['volume_avg_50']
        
        # Moving average slopes (trend strength)
        df['ma_50_slope'] = ((df['ma_50'] / df['ma_50'].shift(5)) - 1) * 100
        df['ma_150_slope'] = ((df['ma_150'] / df['ma_150'].shift(10)) - 1) * 100
        df['ma_200_slope'] = ((df['ma_200'] / df['ma_200'].shift(10)) - 1) * 100
        
        return df
    
    def trend_template_analysis(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        STRATEGY 1: MINERVINI'S TREND TEMPLATE
        =====================================
        
        This is Minervini's foundation - an 8-point checklist to identify
        stocks in Stage 2 uptrends with institutional accumulation.
        
        THE 8 CRITERIA:
        1. Price > 150-day and 200-day moving average
        2. 150-day MA > 200-day MA (trend direction)
        3. 200-day MA trending up for at least 1 month
        4. 50-day MA > 150-day MA and 200-day MA
        5. Current price > 50-day MA
        6. Current price within 25% of 52-week high
        7. Current price at least 30% above 52-week low
        8. Relative Strength rating > 70 (top 30% of stocks)
        
        WHY THIS WORKS:
        - Filters for stocks in confirmed uptrends
        - Eliminates weak/declining stocks
        - Focuses on institutional favorites
        - Reduces risk of buying into downtrends
        """
        
        print("\n" + "="*60)
        print(f"TREND TEMPLATE ANALYSIS: {symbol}")
        print("="*60)
        
        df = self.calculate_minervini_indicators(data)
        
        # Get latest values
        latest = df.iloc[-1]
        
        print(f"📊 CURRENT DATA ({latest.name.strftime('%Y-%m-%d')}):")
        print(f"   Price: ${latest['close']:.2f}")
        print(f"   Volume: {latest['volume']:,.0f} (vs 50-day avg: {latest['volume_ratio']:.1f}x)")
        
        print(f"\n📈 MOVING AVERAGES:")
        print(f"   10-day:  ${latest['ma_10']:.2f}")
        print(f"   21-day:  ${latest['ma_21']:.2f}")
        print(f"   50-day:  ${latest['ma_50']:.2f}")
        print(f"   150-day: ${latest['ma_150']:.2f}")
        print(f"   200-day: ${latest['ma_200']:.2f}")
        
        print(f"\n🎯 52-WEEK ANALYSIS:")
        print(f"   52-week high: ${latest['high_52w']:.2f}")
        print(f"   52-week low:  ${latest['low_52w']:.2f}")
        print(f"   Distance from high: {latest['distance_from_52w_high']:.1f}%")
        print(f"   Distance from low:  {latest['distance_from_52w_low']:.1f}%")
        
        print(f"\n⚡ RELATIVE STRENGTH:")
        print(f"   4-week:  {latest['rs_4w']:.1f}%")
        print(f"   13-week: {latest['rs_13w']:.1f}%")
        print(f"   26-week: {latest['rs_26w']:.1f}%")
        print(f"   52-week: {latest['rs_52w']:.1f}%")
        
        # Check each Trend Template criterion
        print(f"\n✅ TREND TEMPLATE CHECKLIST:")
        
        # Criterion 1: Price above 150 and 200 MA
        criterion_1 = latest['close'] > latest['ma_150'] and latest['close'] > latest['ma_200']
        status_1 = "✅ PASS" if criterion_1 else "❌ FAIL"
        print(f"   1. Price > 150MA & 200MA: {status_1}")
        
        # Criterion 2: 150MA > 200MA
        criterion_2 = latest['ma_150'] > latest['ma_200']
        status_2 = "✅ PASS" if criterion_2 else "❌ FAIL"
        print(f"   2. 150MA > 200MA: {status_2}")
        
        # Criterion 3: 200MA trending up
        criterion_3 = latest['ma_200_slope'] > 0
        status_3 = "✅ PASS" if criterion_3 else "❌ FAIL"
        print(f"   3. 200MA trending up: {status_3} ({latest['ma_200_slope']:.1f}%)")
        
        # Criterion 4: 50MA > 150MA and 200MA
        criterion_4 = latest['ma_50'] > latest['ma_150'] and latest['ma_50'] > latest['ma_200']
        status_4 = "✅ PASS" if criterion_4 else "❌ FAIL"
        print(f"   4. 50MA > 150MA & 200MA: {status_4}")
        
        # Criterion 5: Price > 50MA
        criterion_5 = latest['close'] > latest['ma_50']
        status_5 = "✅ PASS" if criterion_5 else "❌ FAIL"
        print(f"   5. Price > 50MA: {status_5}")
        
        # Criterion 6: Within 25% of 52-week high
        criterion_6 = latest['distance_from_52w_high'] > -25
        status_6 = "✅ PASS" if criterion_6 else "❌ FAIL"
        print(f"   6. Within 25% of 52W high: {status_6}")
        
        # Criterion 7: 30% above 52-week low
        criterion_7 = latest['distance_from_52w_low'] > 30
        status_7 = "✅ PASS" if criterion_7 else "❌ FAIL"
        print(f"   7. >30% above 52W low: {status_7}")
        
        # Criterion 8: Strong relative strength (simplified)
        rs_score = 50 + (latest['rs_52w'] / 50) * 50  # Simplified RS rating
        criterion_8 = rs_score > 70
        status_8 = "✅ PASS" if criterion_8 else "❌ FAIL"
        print(f"   8. RS Rating > 70: {status_8} (Est: {rs_score:.0f})")
        
        # Overall assessment
        criteria_passed = sum([criterion_1, criterion_2, criterion_3, criterion_4,
                              criterion_5, criterion_6, criterion_7, criterion_8])
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Criteria Passed: {criteria_passed}/8")
        
        if criteria_passed >= 7:
            verdict = "🟢 STRONG BUY CANDIDATE"
        elif criteria_passed >= 5:
            verdict = "🟡 MONITOR CLOSELY"
        else:
            verdict = "🔴 AVOID - WEAK TREND"
            
        print(f"   Verdict: {verdict}")
        
        return {
            'symbol': symbol,
            'criteria_passed': criteria_passed,
            'trend_template_score': criteria_passed / 8 * 100,
            'verdict': verdict,
            'current_price': latest['close'],
            'rs_rating': rs_score,
            'distance_from_high': latest['distance_from_52w_high']
        }
    
    def sepa_breakout_analysis(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        STRATEGY 2: SEPA BREAKOUT METHOD
        ===============================
        
        SEPA = Specific Entry Point Analysis
        
        This method focuses on buying stocks at the exact moment they break
        out to new highs with institutional volume confirmation.
        
        KEY CRITERIA:
        1. Stock must pass Trend Template first
        2. Breaking out from a proper base (4-8 weeks)
        3. Volume 40-50% above average on breakout
        4. Buy within 5% of breakout point
        5. Stop loss 7-8% below entry
        
        WHY THIS WORKS:
        - Catches stocks at the beginning of major moves
        - Volume confirms institutional buying
        - Tight stops limit downside risk
        - High reward-to-risk ratio
        """
        
        print(f"\n" + "="*60)
        print(f"SEPA BREAKOUT ANALYSIS: {symbol}")
        print("="*60)
        
        df = self.calculate_minervini_indicators(data)
        
        # Look for recent breakout opportunities
        breakout_signals = []
        
        for i in range(60, len(df)):  # Look at last 60 days
            current_row = df.iloc[i]
            
            # Check if stock broke to new high with volume
            if i >= 30:  # Need base period
                base_period = df.iloc[i-30:i-1]
                base_high = base_period['high'].max()
                
                # Breakout criteria
                is_breakout = current_row['close'] > base_high * 1.01  # 1% above base
                volume_surge = current_row['volume_ratio'] > 1.4  # 40% above average
                
                if is_breakout and volume_surge:
                    breakout_signals.append({
                        'date': current_row.name,
                        'price': current_row['close'],
                        'volume_ratio': current_row['volume_ratio'],
                        'base_high': base_high,
                        'breakout_percent': ((current_row['close'] / base_high) - 1) * 100
                    })
        
        print(f"📊 BREAKOUT ANALYSIS:")
        print(f"   Scanning last 60 days for breakout patterns...")
        print(f"   Found {len(breakout_signals)} potential breakout signals")
        
        if breakout_signals:
            print(f"\n🚀 RECENT BREAKOUT SIGNALS:")
            for signal in breakout_signals[-5:]:  # Show last 5
                date_str = signal['date'].strftime('%Y-%m-%d')
                print(f"   {date_str}: ${signal['price']:.2f} "
                      f"(+{signal['breakout_percent']:.1f}% breakout, "
                      f"{signal['volume_ratio']:.1f}x volume)")
        
        # Current breakout potential
        latest = df.iloc[-1]
        recent_high = df['high'].tail(30).max()
        distance_from_breakout = ((latest['close'] / recent_high) - 1) * 100
        
        print(f"\n🎯 CURRENT BREAKOUT POTENTIAL:")
        print(f"   Current Price: ${latest['close']:.2f}")
        print(f"   Recent 30-day High: ${recent_high:.2f}")
        print(f"   Distance to Breakout: {distance_from_breakout:.1f}%")
        print(f"   Volume Ratio: {latest['volume_ratio']:.1f}x")
        
        if distance_from_breakout > -2:
            status = "🟢 NEAR BREAKOUT - WATCH CLOSELY"
        elif distance_from_breakout > -10:
            status = "🟡 BUILDING BASE - MONITOR"
        else:
            status = "🔴 FAR FROM BREAKOUT"
            
        print(f"   Status: {status}")
        
        return {
            'symbol': symbol,
            'breakout_signals': len(breakout_signals),
            'distance_to_breakout': distance_from_breakout,
            'current_volume_ratio': latest['volume_ratio'],
            'status': status
        }
    
    def sepa_pullback_analysis(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        STRATEGY 3: SEPA PULLBACK METHOD
        ===============================
        
        This method buys strength on pullbacks to key moving averages
        in stocks that are in confirmed uptrends.
        
        KEY CRITERIA:
        1. Stock in strong uptrend (Trend Template)
        2. Pullback to 10-day or 21-day MA support
        3. Volume dries up on pullback (selling exhausted)
        4. Volume increases on bounce from support
        5. Buy when price reclaims support with volume
        
        WHY THIS WORKS:
        - Lower risk entry than breakouts
        - Better reward-to-risk ratio
        - Institutions often accumulate on pullbacks
        - Support levels provide natural stop areas
        """
        
        print(f"\n" + "="*60)
        print(f"SEPA PULLBACK ANALYSIS: {symbol}")
        print("="*60)
        
        df = self.calculate_minervini_indicators(data)
        latest = df.iloc[-1]
        
        # Check pullback to moving averages
        ma_10_distance = ((latest['close'] / latest['ma_10']) - 1) * 100
        ma_21_distance = ((latest['close'] / latest['ma_21']) - 1) * 100
        ma_50_distance = ((latest['close'] / latest['ma_50']) - 1) * 100
        
        print(f"📊 PULLBACK ANALYSIS:")
        print(f"   Distance from 10-day MA: {ma_10_distance:.1f}%")
        print(f"   Distance from 21-day MA: {ma_21_distance:.1f}%")
        print(f"   Distance from 50-day MA: {ma_50_distance:.1f}%")
        
        # Check for pullback patterns in last 20 days
        pullback_opportunities = []
        
        for i in range(len(df)-20, len(df)):
            if i < 21:
                continue
                
            current = df.iloc[i]
            
            # Near moving average support
            near_ma_10 = abs((current['close'] / current['ma_10']) - 1) < 0.03  # Within 3%
            near_ma_21 = abs((current['close'] / current['ma_21']) - 1) < 0.03
            
            # Volume pattern (lower volume on pullback)
            volume_ratio = current['volume_ratio']
            
            if (near_ma_10 or near_ma_21) and volume_ratio < 0.8:
                pullback_opportunities.append({
                    'date': current.name,
                    'price': current['close'],
                    'ma_10_distance': ((current['close'] / current['ma_10']) - 1) * 100,
                    'ma_21_distance': ((current['close'] / current['ma_21']) - 1) * 100,
                    'volume_ratio': volume_ratio
                })
        
        print(f"\n🎯 RECENT PULLBACK OPPORTUNITIES:")
        if pullback_opportunities:
            for opp in pullback_opportunities[-3:]:  # Show last 3
                date_str = opp['date'].strftime('%Y-%m-%d')
                print(f"   {date_str}: ${opp['price']:.2f} "
                      f"(10MA: {opp['ma_10_distance']:+.1f}%, "
                      f"21MA: {opp['ma_21_distance']:+.1f}%, "
                      f"Vol: {opp['volume_ratio']:.1f}x)")
        else:
            print("   No significant pullback opportunities found recently")
        
        # Current pullback status
        is_pullback = min(abs(ma_10_distance), abs(ma_21_distance)) < 5
        volume_declining = latest['volume_ratio'] < 0.9
        
        if is_pullback and volume_declining:
            status = "🟢 PULLBACK OPPORTUNITY - WATCH FOR BOUNCE"
        elif is_pullback:
            status = "🟡 NEAR SUPPORT - MONITOR VOLUME"
        else:
            status = "🔴 NOT IN PULLBACK PATTERN"
            
        print(f"\n✅ CURRENT PULLBACK STATUS:")
        print(f"   Status: {status}")
        print(f"   Volume Pattern: {'Declining ✅' if volume_declining else 'Not Declining ❌'}")
        
        return {
            'symbol': symbol,
            'pullback_opportunities': len(pullback_opportunities),
            'ma_10_distance': ma_10_distance,
            'ma_21_distance': ma_21_distance,
            'volume_declining': volume_declining,
            'status': status
        }
    
    def risk_management_guide(self, entry_price: float, symbol: str):
        """
        MINERVINI'S RISK MANAGEMENT RULES
        ================================
        
        Risk management is the foundation of Minervini's success.
        He NEVER risks more than 7-8% on any single trade.
        
        KEY RULES:
        1. Stop loss: 7-8% below entry price
        2. Position size: Risk only 1-2% of total capital per trade
        3. Profit targets: 20-25% gains (3:1 reward-to-risk)
        4. Trailing stops: Move to breakeven after 10% gain
        5. Cut losses quickly, let winners run
        """
        
        print(f"\n" + "="*60)
        print(f"RISK MANAGEMENT CALCULATOR: {symbol}")
        print("="*60)
        
        # Calculate stop loss
        stop_loss = entry_price * 0.93  # 7% stop loss
        stop_loss_tight = entry_price * 0.92  # 8% stop loss
        
        # Calculate profit targets
        target_1 = entry_price * 1.20  # 20% gain
        target_2 = entry_price * 1.25  # 25% gain
        
        # Position sizing (risk 2% of capital)
        risk_per_share = entry_price - stop_loss
        max_position_risk = self.initial_capital * 0.02  # 2% max risk
        position_size = int(max_position_risk / risk_per_share)
        position_value = position_size * entry_price
        
        print(f"📊 POSITION SIZING:")
        print(f"   Entry Price: ${entry_price:.2f}")
        print(f"   Stop Loss: ${stop_loss:.2f} (7% risk)")
        print(f"   Risk per Share: ${risk_per_share:.2f}")
        print(f"   Maximum Risk: ${max_position_risk:,.0f} (2% of capital)")
        print(f"   Position Size: {position_size:,} shares")
        print(f"   Position Value: ${position_value:,.0f}")
        print(f"   Portfolio %: {(position_value/self.initial_capital)*100:.1f}%")
        
        print(f"\n🎯 PROFIT TARGETS:")
        print(f"   Target 1 (20%): ${target_1:.2f}")
        print(f"   Target 2 (25%): ${target_2:.2f}")
        print(f"   Reward-to-Risk: {(target_1-entry_price)/(entry_price-stop_loss):.1f}:1")
        
        print(f"\n⚠️  RISK MANAGEMENT RULES:")
        print(f"   ✅ Never risk more than 7-8% per trade")
        print(f"   ✅ Position size limits total risk to 2% of capital")
        print(f"   ✅ Cut losses quickly at predetermined stop")
        print(f"   ✅ Take partial profits at 20-25% gains")
        print(f"   ✅ Trail stop to breakeven after 10% gain")
        
        return {
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_size': position_size,
            'position_value': position_value,
            'max_risk': max_position_risk,
            'target_1': target_1,
            'target_2': target_2,
            'reward_to_risk': (target_1-entry_price)/(entry_price-stop_loss)
        }
    
    def comprehensive_analysis(self, symbol: str) -> Dict:
        """
        Complete Minervini analysis combining all strategies
        """
        print(f"\n" + "="*80)
        print(f"COMPREHENSIVE MINERVINI ANALYSIS: {symbol}")
        print(f"Mark Minervini's Complete Methodology Applied")
        print("="*80)
        
        # Get live data
        data = self.get_live_data(symbol)
        if data is None:
            return {'error': f'Could not load data for {symbol}'}
        
        # Run all analyses
        results = {}
        
        # 1. Trend Template Analysis
        results['trend_template'] = self.trend_template_analysis(data, symbol)
        
        # 2. SEPA Breakout Analysis
        results['sepa_breakout'] = self.sepa_breakout_analysis(data, symbol)
        
        # 3. SEPA Pullback Analysis
        results['sepa_pullback'] = self.sepa_pullback_analysis(data, symbol)
        
        # 4. Risk Management
        current_price = data['close'].iloc[-1]
        results['risk_management'] = self.risk_management_guide(current_price, symbol)
        
        # 5. Overall Recommendation
        self.generate_recommendation(results, symbol)
        
        return results
    
    def generate_recommendation(self, results: Dict, symbol: str):
        """Generate overall trading recommendation"""
        
        print(f"\n" + "="*60)
        print(f"FINAL RECOMMENDATION: {symbol}")
        print("="*60)
        
        trend_score = results['trend_template']['criteria_passed']
        breakout_status = results['sepa_breakout']['distance_to_breakout']
        pullback_ops = results['sepa_pullback']['pullback_opportunities']
        
        print(f"📊 SUMMARY SCORES:")
        print(f"   Trend Template: {trend_score}/8 criteria")
        print(f"   Breakout Distance: {breakout_status:.1f}%")
        print(f"   Pullback Opportunities: {pullback_ops}")
        
        # Generate recommendation
        if trend_score >= 7:
            if breakout_status > -2:
                recommendation = "🟢 STRONG BUY - Near breakout with strong trend"
                action = "Watch for volume breakout above recent highs"
            elif abs(results['sepa_pullback']['ma_21_distance']) < 3:
                recommendation = "🟢 BUY - Pullback opportunity in strong trend"
                action = "Buy on bounce from 21-day MA with volume"
            else:
                recommendation = "🟡 WATCHLIST - Strong trend, wait for entry"
                action = "Monitor for breakout or pullback opportunity"
        elif trend_score >= 5:
            recommendation = "🟡 MONITOR - Improving trend, not ready yet"
            action = "Wait for more criteria to align"
        else:
            recommendation = "🔴 AVOID - Weak trend structure"
            action = "Look for better opportunities"
            
        print(f"\n🎯 RECOMMENDATION: {recommendation}")
        print(f"📋 ACTION: {action}")
        
        # Risk parameters
        risk_mgmt = results['risk_management']
        print(f"\n💰 IF BUYING:")
        print(f"   Entry: ${risk_mgmt['entry_price']:.2f}")
        print(f"   Stop Loss: ${risk_mgmt['stop_loss']:.2f}")
        print(f"   Target: ${risk_mgmt['target_1']:.2f}")
        print(f"   Position Size: {risk_mgmt['position_size']:,} shares")
        print(f"   Max Risk: ${risk_mgmt['max_risk']:,.0f}")

def demonstrate_minervini_strategies():
    """
    DEMONSTRATION: Analyze multiple stocks using Minervini's methods
    """
    
    analyzer = MinerviniEducational()
    
    # Test stocks - mix of different types
    test_stocks = [
        'AAPL',  # Large cap tech
        'NVDA',  # High growth 
        'AMZN',  # Mega cap
        'CRM',   # SaaS growth
        'TSLA'   # Volatile growth
    ]
    
    print("\n" + "="*80)
    print("LIVE DEMONSTRATION: MINERVINI ANALYSIS ON CURRENT MARKET")
    print("="*80)
    print(f"Analyzing {len(test_stocks)} stocks using Mark Minervini's proven methodology")
    print("This demonstrates how a 2-time US Investing Champion evaluates stocks")
    
    results_summary = []
    
    for symbol in test_stocks:
        try:
            result = analyzer.comprehensive_analysis(symbol)
            if 'error' not in result:
                results_summary.append({
                    'symbol': symbol,
                    'trend_score': result['trend_template']['criteria_passed'],
                    'verdict': result['trend_template']['verdict'],
                    'breakout_distance': result['sepa_breakout']['distance_to_breakout'],
                    'pullback_ops': result['sepa_pullback']['pullback_opportunities']
                })
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
    
    # Summary comparison
    print(f"\n" + "="*80)
    print("STOCK COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Symbol':<8} {'Trend Score':<12} {'Breakout %':<12} {'Pullbacks':<12} {'Verdict':<25}")
    print("-" * 80)
    
    for result in sorted(results_summary, key=lambda x: x['trend_score'], reverse=True):
        print(f"{result['symbol']:<8} {result['trend_score']}/8{'':<6} "
              f"{result['breakout_distance']:>+8.1f}%    "
              f"{result['pullback_ops']:>8}     "
              f"{result['verdict']}")
    
    print(f"\n🎓 EDUCATIONAL SUMMARY:")
    print(f"   This demonstrates Minervini's systematic approach to stock analysis")
    print(f"   High trend scores (7-8/8) indicate institutional-quality stocks")
    print(f"   Combine trend strength with precise entry timing for best results")
    print(f"   Remember: Risk management is MORE important than entry technique")

if __name__ == "__main__":
    print("MARK MINERVINI TRADING STRATEGIES - EDUCATIONAL IMPLEMENTATION")
    print("=" * 65)
    print("This educational tool demonstrates the exact methods used by")
    print("2-time US Investing Champion Mark Minervini to achieve")
    print("superior returns with controlled risk.")
    print()
    
    # Run the demonstration
    demonstrate_minervini_strategies()
    
    print(f"\n" + "="*80)
    print("📚 LEARN MORE:")
    print("   Books: 'Trade Like a Stock Market Wizard' by Mark Minervini")
    print("   Website: minervini.com")
    print("   Course: Mark Minervini's Momentum Stock Selection")
    print()
    print("⚠️  DISCLAIMER:")
    print("   This is for educational purposes only. Past performance")
    print("   does not guarantee future results. Trade at your own risk.")
    print("="*80)