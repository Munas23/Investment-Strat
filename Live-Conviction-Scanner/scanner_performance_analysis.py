"""
Daily Conviction Scanner Performance Analysis
============================================

Analyzes how the conviction scanner's August 21st picks performed
2-5 days later to evaluate the daily change component in the model.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ScannerPerformanceAnalysis:
    """Analyze scanner performance to adjust daily change model"""
    
    def __init__(self):
        self.scan_date = "2024-08-21"  # Fixed year - August 21, 2024 (the actual scan date)
        self.follow_up_days = [2, 3, 4, 5]  # Days after scan to check performance
        
    def load_scanner_results(self):
        """Load the August 21st scanner results"""
        try:
            # Load the TRADE_READY CSV with conviction picks
            df = pd.read_csv('daily_conviction_scan_20250821_164624_TRADE_READY.csv')
            
            # Clean up duplicate entries (keep first occurrence of each symbol)
            df = df.drop_duplicates(subset=['symbol'], keep='first')
            
            print(f"Loaded {len(df)} unique conviction picks from {self.scan_date}")
            return df
            
        except Exception as e:
            print(f"Error loading scanner results: {e}")
            return pd.DataFrame()
    
    def get_stock_performance(self, symbol, scan_date, days_ahead_list):
        """Get stock performance for specified days after scan"""
        try:
            # Get stock data
            ticker = yf.Ticker(symbol)
            
            # Get data from scan date to 15 days later for better coverage
            start_date = datetime.strptime(scan_date, "%Y-%m-%d")
            end_date = start_date + timedelta(days=15)
            
            print(f"  Fetching data from {start_date.date()} to {end_date.date()}")
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if len(hist) < max(days_ahead_list) + 1:
                return None
            
            # Calculate performance from scan date close to future date close
            scan_close = hist['Close'].iloc[0]  # Day of scan
            
            results = {}
            for day in days_ahead_list:
                if day < len(hist):
                    future_close = hist['Close'].iloc[day]
                    performance = (future_close / scan_close - 1) * 100
                    results[f'day_{day}_return'] = performance
                else:
                    results[f'day_{day}_return'] = None
            
            return results
            
        except Exception as e:
            print(f"Error getting performance for {symbol}: {e}")
            # Try to get basic info to debug
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                print(f"  Symbol exists: {info.get('symbol', 'Unknown')}")
            except:
                print(f"  Symbol {symbol} not found or invalid")
            return None
    
    def analyze_daily_change_correlation(self):
        """Analyze correlation between daily change and future performance"""
        
        print("=" * 80)
        print("DAILY CONVICTION SCANNER PERFORMANCE ANALYSIS")
        print("=" * 80)
        print(f"Scan Date: {self.scan_date}")
        print("Analyzing performance 2-5 days after scanner picks")
        print("=" * 80)
        
        # Load scanner results
        scanner_df = self.load_scanner_results()
        if scanner_df.empty:
            return
        
        # Analyze performance for each stock
        results = []
        
        print("\\nAnalyzing individual stock performance...")
        
        for _, row in scanner_df.head(25).iterrows():  # Analyze top 25 picks
            symbol = row['symbol']
            conviction_level = row['conviction_level']
            daily_change = row['daily_change_pct']
            volume_surge = row['volume_surge']
            
            print(f"\\nAnalyzing {symbol}:")
            print(f"  Scanner Data: Conv {conviction_level}, Daily Change: {daily_change:.1f}%, Vol: {volume_surge:.1f}x")
            
            # Get future performance
            performance = self.get_stock_performance(symbol, self.scan_date, self.follow_up_days)
            
            if performance:
                result = {
                    'symbol': symbol,
                    'conviction_level': conviction_level,
                    'daily_change_pct': daily_change,
                    'volume_surge': volume_surge,
                    **performance
                }
                results.append(result)
                
                # Show performance
                for day in self.follow_up_days:
                    ret = performance.get(f'day_{day}_return')
                    if ret is not None:
                        status = "+" if ret > 0 else "-"
                        print(f"    Day {day}: {status} {ret:+5.1f}%")
            else:
                print(f"    X Could not get performance data")
        
        if not results:
            print("No performance data available")
            return
        
        # Convert to DataFrame for analysis
        results_df = pd.DataFrame(results)
        
        # Analyze correlation patterns
        print(f"\\n" + "=" * 80)
        print("CORRELATION ANALYSIS: Daily Change vs Future Performance")
        print("=" * 80)
        
        # Group by daily change ranges
        self.analyze_daily_change_buckets(results_df)
        
        # Analyze by conviction level
        self.analyze_conviction_performance(results_df)
        
        # Suggest model adjustments
        self.suggest_model_adjustments(results_df)
        
        return results_df
    
    def analyze_daily_change_buckets(self, df):
        """Analyze performance by daily change buckets"""
        
        print("\\nPERFORMANCE BY DAILY CHANGE RANGES:")
        print("-" * 50)
        
        # Create buckets for daily change
        buckets = [
            (-10, 0, "Negative/Flat"),
            (0, 2, "Small Move (0-2%)"),
            (2, 5, "Medium Move (2-5%)"),
            (5, 10, "Large Move (5-10%)"),
            (10, 50, "Huge Move (>10%)")
        ]
        
        for min_change, max_change, label in buckets:
            bucket_df = df[(df['daily_change_pct'] >= min_change) & (df['daily_change_pct'] < max_change)]
            
            if len(bucket_df) > 0:
                print(f"\\n{label} ({len(bucket_df)} stocks):")
                
                for day in self.follow_up_days:
                    col = f'day_{day}_return'
                    if col in bucket_df.columns:
                        avg_return = bucket_df[col].mean()
                        win_rate = (bucket_df[col] > 0).mean() * 100
                        print(f"  Day {day}: Avg {avg_return:+5.1f}%, Win Rate {win_rate:.0f}%")
                
                # Show examples
                print("  Examples:")
                for _, row in bucket_df.head(3).iterrows():
                    day2_return = row.get('day_2_return', None)
                    if day2_return is not None:
                        print(f"    {row['symbol']}: {row['daily_change_pct']:.1f}% -> Day 2: {day2_return:+5.1f}%")
                    else:
                        print(f"    {row['symbol']}: {row['daily_change_pct']:.1f}% -> Day 2: N/A")
    
    def analyze_conviction_performance(self, df):
        """Analyze performance by conviction level"""
        
        print(f"\\n" + "=" * 50)
        print("PERFORMANCE BY CONVICTION LEVEL:")
        print("-" * 50)
        
        for conv_level in sorted(df['conviction_level'].unique(), reverse=True):
            conv_df = df[df['conviction_level'] == conv_level]
            
            print(f"\\nConviction Level {conv_level} ({len(conv_df)} stocks):")
            
            for day in self.follow_up_days:
                col = f'day_{day}_return'
                if col in conv_df.columns:
                    avg_return = conv_df[col].mean()
                    win_rate = (conv_df[col] > 0).mean() * 100
                    print(f"  Day {day}: Avg {avg_return:+5.1f}%, Win Rate {win_rate:.0f}%")
            
            # Show daily change distribution
            avg_daily_change = conv_df['daily_change_pct'].mean()
            print(f"  Avg Daily Change: {avg_daily_change:.1f}%")
    
    def suggest_model_adjustments(self, df):
        """Suggest adjustments to the daily change component"""
        
        print(f"\\n" + "=" * 80)
        print("MODEL ADJUSTMENT RECOMMENDATIONS")
        print("=" * 80)
        
        # Analyze which daily change ranges performed best
        best_performers = []
        
        # Look at day 2 performance (most relevant for next-day trading)
        if 'day_2_return' in df.columns:
            
            # Find optimal daily change range
            for min_change in range(0, 10, 1):
                max_change = min_change + 2
                subset = df[(df['daily_change_pct'] >= min_change) & (df['daily_change_pct'] < max_change)]
                
                if len(subset) >= 2:  # Need at least 2 stocks for meaningful analysis
                    avg_return = subset['day_2_return'].mean()
                    win_rate = (subset['day_2_return'] > 0).mean() * 100
                    
                    best_performers.append({
                        'range': f"{min_change}-{max_change}%",
                        'count': len(subset),
                        'avg_return': avg_return,
                        'win_rate': win_rate,
                        'score': avg_return * (win_rate / 100)  # Combined score
                    })
        
        if best_performers:
            # Sort by combined score
            best_performers.sort(key=lambda x: x['score'], reverse=True)
            
            print("\\nBEST PERFORMING DAILY CHANGE RANGES (by 2-day return):")
            print("-" * 60)
            for i, perf in enumerate(best_performers[:5]):
                print(f"{i+1}. {perf['range']}: {perf['avg_return']:+5.1f}% avg, {perf['win_rate']:.0f}% win rate ({perf['count']} stocks)")
            
            # Recommendations
            best_range = best_performers[0]
            print(f"\\nRECOMMENDATIONS:")
            print(f"1. OPTIMAL DAILY CHANGE RANGE: {best_range['range']}")
            print(f"   - Best risk/reward with {best_range['avg_return']:+.1f}% average return")
            print(f"   - {best_range['win_rate']:.0f}% win rate")
            
            # Check current model scoring
            print(f"\\n2. CURRENT MODEL ANALYSIS:")
            
            # Analyze current momentum points allocation
            high_daily_change = df[df['daily_change_pct'] > 5]
            low_daily_change = df[df['daily_change_pct'] <= 2]
            
            if len(high_daily_change) > 0 and len(low_daily_change) > 0:
                high_avg = high_daily_change['day_2_return'].mean() if 'day_2_return' in high_daily_change.columns else 0
                low_avg = low_daily_change['day_2_return'].mean() if 'day_2_return' in low_daily_change.columns else 0
                
                print(f"   - High daily change (>5%): {high_avg:+.1f}% avg return")
                print(f"   - Low daily change (<=2%): {low_avg:+.1f}% avg return")
                
                if low_avg > high_avg:
                    print(f"   WARNING: Lower daily changes performing better!")
                    print(f"   SUGGESTION: Reduce momentum points for high daily changes")
                    print(f"   SUGGESTION: Favor controlled moves over explosive moves")
        
        # Volume analysis
        print(f"\\n3. VOLUME CORRELATION:")
        if 'day_2_return' in df.columns:
            high_vol = df[df['volume_surge'] > 3]
            med_vol = df[(df['volume_surge'] >= 1.5) & (df['volume_surge'] <= 3)]
            
            if len(high_vol) > 0 and len(med_vol) > 0:
                high_vol_avg = high_vol['day_2_return'].mean()
                med_vol_avg = med_vol['day_2_return'].mean()
                
                print(f"   - High volume (>3x): {high_vol_avg:+.1f}% avg return")
                print(f"   - Medium volume (1.5-3x): {med_vol_avg:+.1f}% avg return")
                
                if med_vol_avg > high_vol_avg:
                    print(f"   SUGGESTION: Favor building volume over volume spikes")
        
        print(f"\\n4. PROPOSED MODEL ADJUSTMENTS:")
        print(f"   - Reduce daily momentum points for moves >5%")
        print(f"   - Increase points for controlled moves 1-3%")
        print(f"   - Favor building volume over explosive volume")
        print(f"   - Consider adding 'controlled momentum' factor")
        
        print("=" * 80)

def main():
    """Run the scanner performance analysis"""
    
    analyzer = ScannerPerformanceAnalysis()
    
    print("DAILY CONVICTION SCANNER PERFORMANCE ANALYSIS")
    print("Evaluating August 21st picks to optimize daily change model")
    print()
    
    # Run the analysis
    results = analyzer.analyze_daily_change_correlation()
    
    if results is not None:
        print(f"\\nAnalysis complete. Examined {len(results)} stocks.")
        print("Use recommendations above to adjust the daily change scoring model.")
    else:
        print("Analysis failed - check data availability.")

if __name__ == "__main__":
    main()