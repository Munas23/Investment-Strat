import pandas as pd
import numpy as np
import re

# Read and combine all files
files = [
    'C:/Users/User/Documents/GitHub/minervini_asx300_trades_20250817_222701.csv',
    'C:/Users/User/Documents/GitHub/minervini_complete_trades_20250817_121915.csv',
    'C:/Users/User/Documents/GitHub/minervini_complete_trades_20250817_135244.csv', 
    'C:/Users/User/Documents/GitHub/minervini_enhanced_trades_20250817_150630.csv',
    'C:/Users/User/Documents/GitHub/minervini_enhanced_trades_20250817_181722.csv'
]

print('=== MINERVINI 5-LEVEL CONVICTION SYSTEM ANALYSIS ===')
print('Analyzing performance by conviction level across 5 strategy runs...\n')

all_trades = []
strategy_summaries = {}

for file in files:
    try:
        df = pd.read_csv(file)
        
        # Strategy type
        if 'asx300' in file:
            strategy_type = 'ASX300'
            market = 'Australia'
        elif 'enhanced' in file:
            strategy_type = 'Enhanced'
            market = 'US'
        else:
            strategy_type = 'Standard'
            market = 'US'
        
        df['strategy'] = strategy_type
        df['market'] = market
        
        # Extract conviction levels from buy trades
        df['conviction_level'] = 0
        for idx, row in df.iterrows():
            if row['action'] == 'buy' and 'Conviction' in str(row['reason']):
                match = re.search(r'Conviction (\d)', str(row['reason']))
                if match:
                    df.at[idx, 'conviction_level'] = int(match.group(1))
        
        all_trades.append(df)
        
        # Strategy summary
        initial_value = 100000
        final_value = df['portfolio_value'].iloc[-1] if len(df) > 0 else initial_value
        total_return = (final_value - initial_value) / initial_value * 100
        
        strategy_summaries[f"{strategy_type}_{market}"] = {
            'trades': len(df),
            'final_value': final_value,
            'total_return': total_return
        }
        
    except Exception as e:
        print(f'Error processing {file}: {e}')

# Combine all trades
combined_df = pd.concat(all_trades, ignore_index=True)

# Analyze buy trades by conviction level
buy_trades = combined_df[combined_df['action'] == 'buy'].copy()
conviction_buys = buy_trades[buy_trades['conviction_level'] > 0].copy()

print(f'OVERALL STRATEGY PERFORMANCE:')
print('-' * 50)
for strategy, data in strategy_summaries.items():
    print(f'{strategy:<20}: {data["total_return"]:>7.1f}% return (${data["final_value"]:,.0f})')

print(f'\nCONVICTION LEVEL DISTRIBUTION:')
print('-' * 50)
print(f'Total buy trades: {len(buy_trades)}')
print(f'Trades with conviction levels: {len(conviction_buys)}\n')

# Conviction level breakdown
conviction_stats = {}
for level in range(1, 6):
    level_trades = conviction_buys[conviction_buys['conviction_level'] == level]
    if len(level_trades) > 0:
        conviction_stats[level] = {
            'count': len(level_trades),
            'avg_position': level_trades['value'].mean(),
            'total_invested': level_trades['value'].sum(),
            'percentage': len(level_trades) / len(conviction_buys) * 100
        }

print('Level | Count | Avg Position | Total Invested | % of Trades | Expected %')
print('-' * 75)
expected_position = {1: 20, 2: 25, 3: 30, 4: 35, 5: 40}

for level in range(1, 6):
    if level in conviction_stats:
        stats = conviction_stats[level]
        print(f'{level:5d} | {stats["count"]:5d} | ${stats["avg_position"]:11,.0f} | ${stats["total_invested"]:12,.0f} | {stats["percentage"]:9.1f}% | {expected_position[level]:8d}%')
    else:
        print(f'{level:5d} |     0 |           $0 |            $0 |      0.0% | {expected_position[level]:8d}%')

# Now let's analyze the PERFORMANCE by conviction level
print(f'\nCONVICTION LEVEL PERFORMANCE ANALYSIS:')
print('=' * 60)

# For this we need to match buy/sell pairs
def calculate_trade_performance():
    results_by_conviction = {}
    
    for level in range(1, 6):
        level_buys = conviction_buys[conviction_buys['conviction_level'] == level]
        results_by_conviction[level] = {
            'trades': len(level_buys),
            'wins': 0,
            'losses': 0,
            'home_runs': 0,
            'total_return': 0,
            'avg_return': 0,
            'win_rate': 0
        }
        
        if len(level_buys) == 0:
            continue
            
        returns = []
        
        for _, buy_trade in level_buys.iterrows():
            symbol = buy_trade['symbol']
            buy_date = buy_trade['timestamp']
            buy_price = buy_trade['price']
            
            # Find corresponding sell trade
            strategy_trades = combined_df[combined_df['strategy'] == buy_trade['strategy']]
            potential_sells = strategy_trades[
                (strategy_trades['symbol'] == symbol) & 
                (strategy_trades['action'] == 'sell') &
                (strategy_trades['timestamp'] > buy_date)
            ]
            
            if len(potential_sells) > 0:
                sell_trade = potential_sells.iloc[0]
                sell_price = sell_trade['price']
                
                # Calculate return
                trade_return = (sell_price - buy_price) / buy_price * 100
                returns.append(trade_return)
                
                if trade_return > 0:
                    results_by_conviction[level]['wins'] += 1
                    if trade_return >= 50:
                        results_by_conviction[level]['home_runs'] += 1
                else:
                    results_by_conviction[level]['losses'] += 1
        
        if len(returns) > 0:
            results_by_conviction[level]['avg_return'] = np.mean(returns)
            results_by_conviction[level]['win_rate'] = results_by_conviction[level]['wins'] / len(returns) * 100
    
    return results_by_conviction

performance_results = calculate_trade_performance()

print('Level | Trades | Win Rate | Avg Return | Home Runs | Wins | Losses')
print('-' * 70)

for level in range(1, 6):
    if level in performance_results and performance_results[level]['trades'] > 0:
        data = performance_results[level]
        print(f'{level:5d} | {data["trades"]:6d} | {data["win_rate"]:7.1f}% | {data["avg_return"]:9.1f}% | {data["home_runs"]:8d} | {data["wins"]:4d} | {data["losses"]:6d}')
    else:
        print(f'{level:5d} |      0 |    0.0% |      0.0% |        0 |    0 |      0')

print(f'\nKEY INSIGHTS:')
print('=' * 40)
print('1. CONVICTION DISTRIBUTION:')
for level in range(1, 6):
    if level in conviction_stats:
        print(f'   Level {level}: {conviction_stats[level]["count"]} trades ({conviction_stats[level]["percentage"]:.1f}%)')

print('\n2. PERFORMANCE BY CONVICTION:')
total_home_runs = sum(performance_results[level]['home_runs'] for level in performance_results if performance_results[level]['trades'] > 0)
print(f'   Total Home Runs (50%+ gains): {total_home_runs}')

best_level = max(performance_results.keys(), key=lambda x: performance_results[x]['avg_return'] if performance_results[x]['trades'] > 0 else -999)
worst_level = min(performance_results.keys(), key=lambda x: performance_results[x]['avg_return'] if performance_results[x]['trades'] > 0 else 999)

if performance_results[best_level]['trades'] > 0:
    print(f'   Best performing level: {best_level} ({performance_results[best_level]["avg_return"]:.1f}% avg return)')
if performance_results[worst_level]['trades'] > 0:
    print(f'   Worst performing level: {worst_level} ({performance_results[worst_level]["avg_return"]:.1f}% avg return)')

print('\n3. STRATEGY COMPARISON:')
asx_performance = [k for k in strategy_summaries.keys() if 'Australia' in k]
us_performance = [k for k in strategy_summaries.keys() if 'US' in k]

if asx_performance:
    asx_return = strategy_summaries[asx_performance[0]]['total_return']
    print(f'   ASX300 Strategy: {asx_return:.1f}% total return')

if us_performance:
    us_returns = [strategy_summaries[k]['total_return'] for k in us_performance]
    avg_us_return = np.mean(us_returns)
    print(f'   US Strategies (avg): {avg_us_return:.1f}% total return')