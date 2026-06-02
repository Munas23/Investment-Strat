import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def analyze_turtle_results(csv_file='turtle_results.csv'):
    """Analyze and visualize Turtle Trading results"""
    
    # Read results
    df = pd.read_csv(csv_file)
    
    print("TURTLE TRADING STRATEGY ANALYSIS")
    print("="*60)
    
    # Key findings
    print("\nKEY FINDINGS:")
    print(f"1. Best Performer: {df.iloc[0]['Symbol']} with {df.iloc[0]['Total Return %']:.1f}% return")
    print(f"2. Worst Performer: {df.iloc[-1]['Symbol']} with {df.iloc[-1]['Total Return %']:.1f}% return")
    print(f"3. Average Return: {df['Total Return %'].mean():.1f}%")
    print(f"4. Win Rate Range: {df['Win Rate %'].min():.1f}% to {df['Win Rate %'].max():.1f}%")
    print(f"5. Most Active: {df.loc[df['Number of Trades'].idxmax(), 'Symbol']} with {df['Number of Trades'].max()} trades")
    
    # Performance categories
    excellent = df[df['Total Return %'] > 100]
    good = df[(df['Total Return %'] > 20) & (df['Total Return %'] <= 100)]
    poor = df[df['Total Return %'] <= 20]
    
    print(f"\nPERFORMANCE BREAKDOWN:")
    print(f"Excellent (>100%): {list(excellent['Symbol'].values)}")
    print(f"Good (20-100%): {list(good['Symbol'].values)}")
    print(f"Poor (<20%): {list(poor['Symbol'].values)}")
    
    # Create visualizations
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Returns bar chart
    colors = ['green' if x > 0 else 'red' for x in df['Total Return %']]
    bars = ax1.bar(df['Symbol'], df['Total Return %'], color=colors, alpha=0.7)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.set_title('Turtle Trading Returns by Symbol', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Total Return %')
    ax1.set_xlabel('Symbol')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, df['Total Return %']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 10 if height > 0 else height - 20,
                f'{value:.0f}%', ha='center', va='bottom' if height > 0 else 'top', fontsize=9)
    
    # 2. Win Rate vs Return scatter
    ax2.scatter(df['Win Rate %'], df['Total Return %'], s=100, alpha=0.6, c=df['Sharpe Ratio'], 
                cmap='RdYlGn', edgecolors='black', linewidth=1)
    
    # Add labels for each point
    for _, row in df.iterrows():
        ax2.annotate(row['Symbol'], (row['Win Rate %'], row['Total Return %']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.axvline(x=50, color='black', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Win Rate %')
    ax2.set_ylabel('Total Return %')
    ax2.set_title('Win Rate vs Returns (colored by Sharpe Ratio)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=plt.Normalize(vmin=df['Sharpe Ratio'].min(), 
                                                                   vmax=df['Sharpe Ratio'].max()))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax2)
    cbar.set_label('Sharpe Ratio', rotation=270, labelpad=15)
    
    # 3. Risk-Return profile
    ax3.scatter(df['Avg Loss %'].abs(), df['Avg Win %'], s=df['Number of Trades']*5, 
                alpha=0.6, c=df['Total Return %'], cmap='RdYlGn', edgecolors='black', linewidth=1)
    
    # Add diagonal line (1:1 risk-reward)
    max_val = max(df['Avg Loss %'].abs().max(), df['Avg Win %'].max())
    ax3.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='1:1 Risk/Reward')
    
    # Add labels
    for _, row in df.iterrows():
        ax3.annotate(row['Symbol'], (abs(row['Avg Loss %']), row['Avg Win %']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax3.set_xlabel('Average Loss % (absolute)')
    ax3.set_ylabel('Average Win %')
    ax3.set_title('Risk vs Reward (size = # trades, color = return)', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Trade statistics
    metrics = ['Total Return %', 'Win Rate %', 'Sharpe Ratio', 'Number of Trades']
    positions = np.arange(len(metrics))
    
    # Calculate percentile ranks for each metric
    percentiles = []
    for metric in metrics:
        if metric == 'Number of Trades':
            # For trades, we might want fewer trades with higher returns
            percentiles.append(50)  # Neutral
        else:
            # Find TSLA's percentile rank
            tsla_value = df[df['Symbol'] == 'TSLA'][metric].values[0]
            percentile = (df[metric] < tsla_value).sum() / len(df) * 100
            percentiles.append(percentile)
    
    bars = ax4.barh(positions, percentiles, color='skyblue', alpha=0.7)
    ax4.set_yticks(positions)
    ax4.set_yticklabels(metrics)
    ax4.set_xlabel('Percentile Rank')
    ax4.set_title('TSLA Performance Metrics (Percentile Rank)', fontsize=14, fontweight='bold')
    ax4.set_xlim(0, 100)
    ax4.grid(True, axis='x', alpha=0.3)
    
    # Add value labels
    for bar, value in zip(bars, percentiles):
        ax4.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                f'{value:.0f}%', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('turtle_analysis.png', dpi=300, bbox_inches='tight')
    print("\nAnalysis chart saved as 'turtle_analysis.png'")
    plt.show()
    
    # Additional insights
    print("\nADDITIONAL INSIGHTS:")
    
    # Correlation analysis
    print("\nCorrelations:")
    print(f"Win Rate vs Return: {df['Win Rate %'].corr(df['Total Return %']):.3f}")
    print(f"Sharpe vs Return: {df['Sharpe Ratio'].corr(df['Total Return %']):.3f}")
    print(f"Trades vs Return: {df['Number of Trades'].corr(df['Total Return %']):.3f}")
    
    # Risk-adjusted returns
    df['Return per Trade'] = df['Total Return %'] / df['Number of Trades']
    best_efficiency = df.loc[df['Return per Trade'].idxmax()]
    print(f"\nMost Efficient: {best_efficiency['Symbol']} with {best_efficiency['Return per Trade']:.2f}% per trade")
    
    # Consistency metric (Sharpe * Win Rate)
    df['Consistency'] = df['Sharpe Ratio'] * df['Win Rate %']
    most_consistent = df.loc[df['Consistency'].idxmax()]
    print(f"Most Consistent: {most_consistent['Symbol']} (Sharpe: {most_consistent['Sharpe Ratio']:.2f}, Win Rate: {most_consistent['Win Rate %']:.1f}%)")
    
    return df

def create_strategy_report():
    """Create a comprehensive strategy report"""
    
    print("\n" + "="*60)
    print("TURTLE TRADING STRATEGY REPORT")
    print("="*60)
    
    print("\nSTRATEGY SUMMARY:")
    print("- Entry: Buy when price breaks above 20-day high")
    print("- Exit: Sell when price breaks below 10-day low")
    print("- Position Size: Fixed 10% of capital per trade")
    print("- Commission: 0.1% per trade")
    
    print("\nKEY TAKEAWAYS:")
    print("1. High-volatility growth stocks (TSLA, NVDA) performed best")
    print("2. Win rate is not strongly correlated with returns")
    print("3. Large average wins compensate for lower win rates")
    print("4. The strategy works best in trending markets")
    print("5. Traditional value stocks (V, MA) underperformed")
    
    print("\nRECOMMENDATIONS:")
    print("1. Focus on high-momentum technology stocks")
    print("2. Consider filtering for stocks in strong uptrends")
    print("3. May benefit from volatility-based position sizing")
    print("4. Could add market regime filter (bull/bear)")
    print("5. Test longer entry periods (30-50 days) for less volatile stocks")
    
    print("\nRISK CONSIDERATIONS:")
    print("- High drawdowns possible during consolidation periods")
    print("- Whipsaws in ranging markets reduce profitability")
    print("- Requires discipline to follow signals mechanically")
    print("- Past performance doesn't guarantee future results")

# Run the analysis
if __name__ == "__main__":
    # Analyze results
    df = analyze_turtle_results()
    
    # Create strategy report
    create_strategy_report()
    
    print("\n✓ Analysis complete! Check 'turtle_analysis.png' for visual insights.")