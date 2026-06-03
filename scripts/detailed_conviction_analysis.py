import pandas as pd
import numpy as np
import re

# Read and analyze each file individually for detailed comparison
files = {
    'ASX300': 'C:/Users/User/Documents/GitHub/minervini_asx300_trades_20250817_222701.csv',
    'Standard_1': 'C:/Users/User/Documents/GitHub/minervini_complete_trades_20250817_121915.csv',
    'Standard_2': 'C:/Users/User/Documents/GitHub/minervini_complete_trades_20250817_135244.csv', 
    'Enhanced_1': 'C:/Users/User/Documents/GitHub/minervini_enhanced_trades_20250817_150630.csv',
    'Enhanced_2': 'C:/Users/User/Documents/GitHub/minervini_enhanced_trades_20250817_181722.csv'
}

print('=== DETAILED MINERVINI CONVICTION SYSTEM ANALYSIS ===')
print('Understanding the 5-level conviction system performance\n')

strategy_details = {}

for strategy_name, file_path in files.items():
    try:
        df = pd.read_csv(file_path)
        
        # Calculate overall strategy performance
        initial_value = 100000
        final_value = df['portfolio_value'].iloc[-1] if len(df) > 0 else initial_value
        total_return = (final_value - initial_value) / initial_value * 100
        
        # Extract buy trades with conviction
        buy_trades = df[df['action'] == 'buy'].copy()
        buy_trades['conviction_level'] = 0
        
        for idx, row in buy_trades.iterrows():
            if 'Conviction' in str(row['reason']):
                match = re.search(r'Conviction (\d)', str(row['reason']))
                if match:
                    buy_trades.at[idx, 'conviction_level'] = int(match.group(1))
        
        conviction_buys = buy_trades[buy_trades['conviction_level'] > 0]
        
        # Analyze conviction distribution
        conviction_dist = {}
        for level in range(1, 6):
            level_trades = conviction_buys[conviction_buys['conviction_level'] == level]
            conviction_dist[level] = len(level_trades)
        
        # Calculate returns for each conviction level
        conviction_performance = {}
        for level in range(1, 6):
            level_buys = conviction_buys[conviction_buys['conviction_level'] == level]
            if len(level_buys) == 0:
                conviction_performance[level] = {'trades': 0, 'avg_return': 0, 'home_runs': 0}
                continue
                
            returns = []
            home_runs = 0
            
            for _, buy_trade in level_buys.iterrows():
                symbol = buy_trade['symbol']
                buy_date = buy_trade['timestamp']
                buy_price = buy_trade['price']
                
                # Find corresponding sell
                potential_sells = df[
                    (df['symbol'] == symbol) & 
                    (df['action'] == 'sell') &
                    (df['timestamp'] > buy_date)
                ]
                
                if len(potential_sells) > 0:
                    sell_trade = potential_sells.iloc[0]
                    sell_price = sell_trade['price']
                    trade_return = (sell_price - buy_price) / buy_price * 100
                    returns.append(trade_return)
                    if trade_return >= 50:
                        home_runs += 1
            
            avg_return = np.mean(returns) if returns else 0
            conviction_performance[level] = {
                'trades': len(returns),
                'avg_return': avg_return,
                'home_runs': home_runs
            }
        
        strategy_details[strategy_name] = {
            'total_return': total_return,
            'final_value': final_value,
            'total_trades': len(buy_trades),
            'conviction_trades': len(conviction_buys),
            'conviction_dist': conviction_dist,
            'conviction_performance': conviction_performance
        }
        
    except Exception as e:
        print(f'Error processing {strategy_name}: {e}')

# Display results
print('STRATEGY PERFORMANCE COMPARISON:')
print('=' * 70)
print(f'{"Strategy":<12} {"Total Return":<12} {"Final Value":<12} {"Total Trades":<12}')
print('-' * 70)

for strategy, data in strategy_details.items():
    print(f'{strategy:<12} {data["total_return"]:>10.1f}% ${data["final_value"]:>10,.0f} {data["total_trades"]:>10d}')

print(f'\nCONVICTION LEVEL USAGE ACROSS STRATEGIES:')
print('=' * 80)
print(f'{"Strategy":<12} {"Level 1":<8} {"Level 2":<8} {"Level 3":<8} {"Level 4":<8} {"Level 5":<8}')
print('-' * 80)

for strategy, data in strategy_details.items():
    dist = data['conviction_dist']
    print(f'{strategy:<12} {dist.get(1,0):>6d} {dist.get(2,0):>8d} {dist.get(3,0):>8d} {dist.get(4,0):>8d} {dist.get(5,0):>8d}')

print(f'\nCONVICTION LEVEL PERFORMANCE BY STRATEGY:')
print('=' * 100)

for strategy, data in strategy_details.items():
    print(f'\n{strategy.upper()} STRATEGY:')
    print(f'Total Return: {data["total_return"]:.1f}%')
    print('Level | Trades | Avg Return | Home Runs | Position Size Expected')
    print('-' * 65)
    
    expected_sizes = {1: '20%', 2: '25%', 3: '30%', 4: '35%', 5: '40%'}
    perf = data['conviction_performance']
    
    for level in range(1, 6):
        if level in perf:
            p = perf[level]
            print(f'{level:5d} | {p["trades"]:6d} | {p["avg_return"]:9.1f}% | {p["home_runs"]:8d} | {expected_sizes[level]:>17}')

# Calculate overall insights
print(f'\nKEY INSIGHTS FROM THE 5-LEVEL CONVICTION SYSTEM:')
print('=' * 60)

# Aggregate all conviction data
all_conviction_data = {}
for level in range(1, 6):
    all_conviction_data[level] = {
        'total_trades': 0,
        'total_returns': [],
        'total_home_runs': 0
    }

for strategy, data in strategy_details.items():
    for level in range(1, 6):
        if level in data['conviction_performance']:
            perf = data['conviction_performance'][level]
            all_conviction_data[level]['total_trades'] += perf['trades']
            if perf['trades'] > 0:
                # Approximate individual returns based on average
                for _ in range(perf['trades']):
                    all_conviction_data[level]['total_returns'].append(perf['avg_return'])
            all_conviction_data[level]['total_home_runs'] += perf['home_runs']

print('1. CONVICTION LEVEL EFFECTIVENESS:')
for level in range(1, 6):
    data = all_conviction_data[level]
    if data['total_trades'] > 0:
        avg_return = np.mean(data['total_returns'])
        home_run_rate = data['total_home_runs'] / data['total_trades'] * 100
        print(f'   Level {level}: {data["total_trades"]} trades, {avg_return:.1f}% avg return, {home_run_rate:.1f}% home run rate')
    else:
        print(f'   Level {level}: No trades')

# Find most successful strategy
best_strategy = max(strategy_details.keys(), key=lambda x: strategy_details[x]['total_return'])
print(f'\n2. BEST PERFORMING STRATEGY:')
print(f'   {best_strategy}: {strategy_details[best_strategy]["total_return"]:.1f}% total return')

# Calculate market comparison
asx_return = strategy_details.get('ASX300', {}).get('total_return', 0)
us_strategies = [k for k in strategy_details.keys() if k != 'ASX300']
us_returns = [strategy_details[k]['total_return'] for k in us_strategies]
avg_us_return = np.mean(us_returns) if us_returns else 0

print(f'\n3. MARKET COMPARISON:')
print(f'   ASX300 Strategy: {asx_return:.1f}% return')
print(f'   US Strategies (avg): {avg_us_return:.1f}% return')
print(f'   ASX300 outperformed US by: {asx_return - avg_us_return:.1f} percentage points')

print(f'\n4. CONVICTION SYSTEM ANALYSIS:')
total_conviction_trades = sum(all_conviction_data[level]['total_trades'] for level in range(1, 6))
level_1_pct = all_conviction_data[1]['total_trades'] / total_conviction_trades * 100
level_2_pct = all_conviction_data[2]['total_trades'] / total_conviction_trades * 100
high_conviction_pct = sum(all_conviction_data[level]['total_trades'] for level in [3,4,5]) / total_conviction_trades * 100

print(f'   Low conviction (Level 1): {level_1_pct:.1f}% of trades')
print(f'   Medium conviction (Level 2): {level_2_pct:.1f}% of trades') 
print(f'   High conviction (Level 3-5): {high_conviction_pct:.1f}% of trades')
print(f'   Strategy is conservative - relies mostly on Level 1-2 setups')

# Level 5 mystery
print(f'\n5. LEVEL 5 CONVICTION MYSTERY:')
level_5_total = all_conviction_data[5]['total_trades']
if level_5_total == 0:
    print('   NO Level 5 (40% position) trades were executed!')
    print('   This suggests either:')
    print('   - Market conditions never met maximum conviction criteria')
    print('   - The scoring system is too conservative')
    print('   - Technical requirements for Level 5 are extremely rare')
    print('   - This is the "home run" level that requires perfect setups')
else:
    print(f'   Level 5 trades executed: {level_5_total}')