#working example of a Turtle Trading strategy applied to the S&P 500
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def run_sp500_turtle_portfolio():
    """
    Simplified S&P 500 Turtle Trading Portfolio
    """
    print("S&P 500 TURTLE TRADING PORTFOLIO")
    print("="*60)
    
    # Parameters
    initial_capital = 100000
    max_positions = 20
    position_size = 0.05  # 5% per position
    entry_days = 20
    exit_days = 10
    start_date = '2015-01-01'
    end_date = '2024-12-31'
    
    print(f"Initial Capital: ${initial_capital:,}")
    print(f"Max Positions: {max_positions}")
    print(f"Position Size: {position_size*100}%")
    print(f"Period: {start_date} to {end_date}")
    
    # Get complete S&P 500 symbols
    print("\nUsing complete S&P 500 (503 stocks)...")
    symbols = [
        'MSFT', 'NVDA', 'AAPL', 'AMZN', 'GOOG', 'GOOGL', 'META', 'AVGO', 'BRK.B', 'TSLA',
        'WMT', 'JPM', 'V', 'LLY', 'MA', 'NFLX', 'ORCL', 'COST', 'XOM', 'PG',
        'JNJ', 'HD', 'BAC', 'ABBV', 'KO', 'PLTR', 'PM', 'TMUS', 'UNH', 'GE',
        'CRM', 'CSCO', 'WFC', 'CVX', 'IBM', 'ABT', 'LIN', 'MCD', 'INTU', 'NOW',
        'AXP', 'MS', 'DIS', 'T', 'ISRG', 'ACN', 'MRK', 'AMD', 'RTX', 'VZ',
        'BKNG', 'GS', 'UBER', 'PEP', 'ADBE', 'TXN', 'BX', 'CAT', 'PGR', 'QCOM',
        'SCHW', 'SPGI', 'BA', 'AMGN', 'BLK', 'TMO', 'BSX', 'NEE', 'HON', 'SYK',
        'C', 'TJX', 'DE', 'DHR', 'GILD', 'AMAT', 'UNP', 'PANW', 'PFE', 'ADP',
        'GEV', 'ETN', 'CMCSA', 'LOW', 'ANET', 'MU', 'CB', 'CRWD', 'VRTX', 'MMC',
        'APH', 'LMT', 'MDT', 'LRCX', 'ADI', 'COP', 'KKR', 'KLAC', 'PLD', 'ICE',
        'SBUX', 'WELL', 'MO', 'AMT', 'CME', 'BMY', 'SO', 'TT', 'WM', 'CEG',
        'NKE', 'DASH', 'HCA', 'FI', 'CTAS', 'DUK', 'EQIX', 'SHW', 'MCK', 'ELV',
        'MCO', 'INTC', 'ABNB', 'PH', 'MDLZ', 'AJG', 'CI', 'UPS', 'TDG', 'CDNS',
        'CVS', 'FTNT', 'AON', 'RSG', 'ORLY', 'MMM', 'DELL', 'APO', 'COF', 'ZTS',
        'ECL', 'SNPS', 'RCL', 'GD', 'WMB', 'CL', 'MAR', 'ITW', 'PYPL', 'HWM',
        'CMG', 'PNC', 'NOC', 'MSI', 'USB', 'EMR', 'JCI', 'WDAY', 'BK', 'COIN',
        'ADSK', 'KMI', 'APD', 'EOG', 'AZO', 'TRV', 'MNST', 'AXON', 'ROP', 'CHTR',
        'SPG', 'DLR', 'CARR', 'CSX', 'HLT', 'FCX', 'VST', 'NEM', 'PAYX', 'NSC',
        'AFL', 'COR', 'ALL', 'AEP', 'MET', 'PWR', 'PSA', 'TFC', 'FDX', 'GWW',
        'NXPI', 'REGN', 'OKE', 'O', 'AIG', 'SRE', 'BDX', 'AMP', 'MPC', 'NDAQ',
        'PCAR', 'CTVA', 'TEL', 'CPRT', 'D', 'ROST', 'PSX', 'SLB', 'URI', 'LHX',
        'GM', 'EW', 'CMI', 'VRSK', 'KDP', 'KMB', 'TGT', 'KR', 'MSCI', 'GLW',
        'FICO', 'CCI', 'EXC', 'FIS', 'TTWO', 'IDXX', 'HES', 'OXY', 'KVUE', 'AME',
        'FANG', 'F', 'YUM', 'VLO', 'PEG', 'GRMN', 'CTSH', 'XEL', 'OTIS', 'CBRE',
        'BKR', 'EA', 'PRU', 'DHI', 'CAH', 'RMD', 'HIG', 'ED', 'ROK', 'TRGP',
        'EBAY', 'SYY', 'ACGL', 'ETR', 'WAB', 'MCHP', 'VMC', 'PCG', 'DXCM', 'ODFL',
        'EQT', 'WEC', 'IR', 'LYV', 'EFX', 'DAL', 'VICI', 'MLM', 'EXR', 'CSGP',
        'MPWR', 'A', 'TKO', 'GEHC', 'HSY', 'IT', 'CCL', 'LULU', 'BRO', 'KHC',
        'XYL', 'WTW', 'NRG', 'STZ', 'IRM', 'GIS', 'ANSS', 'RJF', 'MTB', 'VTR',
        'AVB', 'BR', 'LEN', 'DD', 'K', 'LVS', 'WRB', 'STT', 'NUE', 'ROL',
        'EXE', 'KEYS', 'HUM', 'DTE', 'UAL', 'CNC', 'AWK', 'TSCO', 'STX', 'EQR',
        'VRSN', 'IQV', 'FITB', 'GDDY', 'AEE', 'TPL', 'PPG', 'DRI', 'PPL', 'IP',
        'DG', 'VLTO', 'TYL', 'FTV', 'SMCI', 'EL', 'MTD', 'DOV', 'FOXA', 'CHD',
        'WBD', 'SBAC', 'ATO', 'ES', 'CNP', 'STE', 'CPAY', 'HPE', 'HPQ', 'HBAN',
        'CINF', 'CDW', 'FE', 'TDY', 'FOX', 'CBOE', 'ADM', 'SW', 'SYF', 'EXPE',
        'PODD', 'NTAP', 'LH', 'NVR', 'HUBB', 'NTRS', 'ON', 'CMS', 'ULTA', 'WAT',
        'AMCR', 'TROW', 'DVN', 'EIX', 'PTC', 'INVH', 'DOW', 'PHM', 'MKC', 'STLD',
        'RF', 'DLTR', 'TSN', 'IFF', 'LII', 'CTRA', 'BIIB', 'DGX', 'ERIE', 'WSM',
        'WY', 'WDC', 'LUV', 'LDOS', 'JBL', 'GPN', 'L', 'ESS', 'NI', 'ZBH',
        'GEN', 'LYB', 'MAA', 'CFG', 'KEY', 'FSLR', 'HAL', 'PKG', 'GPC', 'PFG',
        'TRMB', 'FFIV', 'HRL', 'SNA', 'RL', 'NWS', 'FDS', 'TPR', 'PNR', 'DECK',
        'WST', 'MOH', 'DPZ', 'CLX', 'NWSA', 'LNT', 'BAX', 'BBY', 'EXPD', 'J',
        'ZBRA', 'EVRG', 'CF', 'BALL', 'PAYC', 'EG', 'UDR', 'APTV', 'COO', 'HOLX',
        'KIM', 'AVY', 'OMC', 'JBHT', 'IEX', 'TER', 'TXT', 'MAS', 'INCY', 'BF.B',
        'JKHY', 'REG', 'BXP', 'ALGN', 'SOLV', 'CPT', 'BLDR', 'DOC', 'UHS', 'ARE',
        'NDSN', 'JNPR', 'ALLE', 'SJM', 'BEN', 'CHRW', 'AKAM', 'POOL', 'HST', 'MOS',
        'RVTY', 'SWKS', 'CAG', 'PNW', 'MRNA', 'TAP', 'DVA', 'AIZ', 'CPB', 'SWK',
        'VTRS', 'EPAM', 'LKQ', 'GL', 'BG', 'KMX', 'WBA', 'DAY', 'HAS', 'AOS',
        'EMN', 'HII', 'NCLH', 'MGM', 'WYNN', 'HSIC', 'IPG', 'FRT', 'MKTX', 'PARA',
        'LW', 'MTCH', 'AES', 'TECH', 'GNRC', 'CRL', 'ALB', 'APA', 'IVZ', 'MHK',
        'ENPH', 'CZR'
    ]
    
    # Download data
    print("\nDownloading stock data...")
    stock_data = {}
    failed = []
    
    for symbol in symbols:
        try:
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if len(data) > entry_days:
                stock_data[symbol] = data
        except:
            failed.append(symbol)
    
    print(f"Successfully downloaded {len(stock_data)} stocks")
    
    # Download SPY
    print("Downloading SPY benchmark...")
    spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False)
    
    # Initialize portfolio
    cash = initial_capital
    positions = {}  # {symbol: {'shares': x, 'entry_price': y, 'entry_date': z}}
    portfolio_value = []
    dates = []
    all_trades = []
    
    # Get trading dates from SPY
    trading_dates = spy_data.index[entry_days:]
    
    print(f"\nRunning backtest over {len(trading_dates)} trading days...")
    
    # Process each trading day
    for i, date in enumerate(trading_dates):
        # Check exits first
        positions_to_close = []
        
        for symbol, pos in positions.items():
            if symbol in stock_data and date in stock_data[symbol].index:
                # Calculate exit signal
                data = stock_data[symbol]
                idx = data.index.get_loc(date)
                
                if idx >= exit_days:
                    # Get the minimum low over the exit period
                    low_n = data['Low'].iloc[idx-exit_days:idx].min()
                    current_low = data['Low'].iloc[idx]
                    
                    # Convert to scalar values for comparison
                    if float(current_low) < float(low_n):
                        positions_to_close.append(symbol)
        
        # Execute exits
        for symbol in positions_to_close:
            pos = positions[symbol]
            exit_price = float(stock_data[symbol].loc[date, 'Close'])
            proceeds = pos['shares'] * exit_price * 0.999  # 0.1% commission
            cash += proceeds
            
            # Record trade
            pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
            all_trades.append({
                'symbol': symbol,
                'entry_date': pos['entry_date'],
                'exit_date': date,
                'pnl_pct': pnl
            })
            
            del positions[symbol]
        
        # Check for new entries
        if len(positions) < max_positions:
            candidates = []
            
            for symbol in stock_data:
                if symbol not in positions and date in stock_data[symbol].index:
                    data = stock_data[symbol]
                    idx = data.index.get_loc(date)
                    
                    if idx >= entry_days:
                        # Get the maximum high over the entry period
                        high_n = data['High'].iloc[idx-entry_days:idx].max()
                        current_high = data['High'].iloc[idx]
                        
                        # Convert to scalar values for comparison
                        if float(current_high) > float(high_n):
                            # Calculate momentum for ranking
                            if idx >= 20:
                                momentum = (float(data['Close'].iloc[idx]) / float(data['Close'].iloc[idx-20])) - 1
                                candidates.append((symbol, float(data['Close'].iloc[idx]), momentum))
            
            # Sort by momentum and enter best ones
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            for symbol, price, momentum in candidates[:max_positions - len(positions)]:
                # Calculate position value based on total portfolio
                current_portfolio_value = cash
                for s, pos in positions.items():
                    if s in stock_data and date in stock_data[s].index:
                        current_portfolio_value += pos['shares'] * float(stock_data[s].loc[date, 'Close'])
                
                position_value = current_portfolio_value * position_size
                shares = int(position_value / price)
                
                if shares > 0:
                    cost = shares * price * 1.001  # 0.1% commission
                    
                    if cost <= cash:
                        cash -= cost
                        positions[symbol] = {
                            'shares': shares,
                            'entry_price': price,
                            'entry_date': date
                        }
        
        # Calculate portfolio value
        total_value = cash
        for symbol, pos in positions.items():
            if symbol in stock_data and date in stock_data[symbol].index:
                total_value += pos['shares'] * float(stock_data[symbol].loc[date, 'Close'])
        
        portfolio_value.append(total_value)
        dates.append(date)
        
        # Progress update
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} / {len(trading_dates)} days...")
    
    # Close remaining positions
    final_date = dates[-1]
    for symbol, pos in positions.items():
        if symbol in stock_data and final_date in stock_data[symbol].index:
            exit_price = float(stock_data[symbol].loc[final_date, 'Close'])
            pnl = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
            all_trades.append({
                'symbol': symbol,
                'entry_date': pos['entry_date'],
                'exit_date': final_date,
                'pnl_pct': pnl
            })
    
    print("Backtest complete!")
    
    # Calculate results
    portfolio_series = pd.Series(portfolio_value, index=dates)
    spy_series = spy_data['Close'].loc[dates]
    
    # Calculate returns
    total_return = (portfolio_series.iloc[-1] - initial_capital) / initial_capital * 100
    spy_return = (float(spy_series.iloc[-1]) - float(spy_series.iloc[0])) / float(spy_series.iloc[0]) * 100
    
    # Trade statistics
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        win_rate = (trades_df['pnl_pct'] > 0).mean() * 100
        avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean() if any(trades_df['pnl_pct'] > 0) else 0
        avg_loss = trades_df[trades_df['pnl_pct'] < 0]['pnl_pct'].mean() if any(trades_df['pnl_pct'] < 0) else 0
        num_trades = len(trades_df)
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        num_trades = 0
    
    # Display results
    print("\n" + "="*60)
    print("PORTFOLIO RESULTS")
    print("="*60)
    print(f"\nTurtle Portfolio:")
    print(f"  Total Return: {total_return:.2f}%")
    print(f"  Final Value: ${portfolio_series.iloc[-1]:,.2f}")
    print(f"  Total Trades: {num_trades}")
    print(f"  Win Rate: {win_rate:.2f}%")
    print(f"  Avg Win: {avg_win:.2f}%")
    print(f"  Avg Loss: {avg_loss:.2f}%")
    
    print(f"\nSPY Benchmark:")
    print(f"  Total Return: {spy_return:.2f}%")
    print(f"  Final Value: ${float(spy_series.iloc[0]) * (1 + spy_return/100):,.2f}")
    
    print(f"\nOutperformance: {total_return - spy_return:.2f}%")
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    
    # Normalize both to start at 100
    portfolio_norm = portfolio_series / portfolio_series.iloc[0] * 100
    spy_norm = spy_series / spy_series.iloc[0] * 100
    
    # Plot performance
    ax1.plot(portfolio_norm.index, portfolio_norm.values, label='Turtle Portfolio', linewidth=2, color='green')
    ax1.plot(spy_norm.index, spy_norm.values, label='SPY Benchmark', linewidth=2, color='blue')
    ax1.set_title('Turtle Trading Portfolio vs SPY Benchmark', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Value (Start = 100)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    
    # Normalize both to start at 100
    portfolio_norm = portfolio_series / portfolio_series.iloc[0] * 100
    spy_norm = spy_series / spy_series.iloc[0] * 100
    
    # Plot performance
    ax1.plot(portfolio_norm.index, portfolio_norm.values, label='Turtle Portfolio', linewidth=2, color='green')
    ax1.plot(spy_norm.index, spy_norm.values, label='SPY Benchmark', linewidth=2, color='blue')
    ax1.set_title('Turtle Trading Portfolio vs SPY Benchmark', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Value (Start = 100)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
    
    # Normalize both to start at 100
    portfolio_norm = portfolio_series / portfolio_series.iloc[0] * 100
    spy_norm = spy_series / spy_series.iloc[0] * 100
    
    # Plot performance
    ax1.plot(portfolio_norm.index, portfolio_norm.values, label='Turtle Portfolio', linewidth=2, color='green')
    ax1.plot(spy_norm.index, spy_norm.values, label='SPY Benchmark', linewidth=2, color='blue')
    ax1.set_title('Turtle Trading Portfolio vs SPY Benchmark', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Value (Start = 100)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot relative performance - simple line plot
    relative = portfolio_norm - spy_norm
    
    # Plot the relative performance line
    ax2.plot(relative.index, relative.values, color='purple', linewidth=2, label='Relative Performance')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)
    
    # Color the background based on performance
    ax2.axhspan(0, relative.values.max(), alpha=0.1, color='green', label='Outperformance Zone')
    ax2.axhspan(relative.values.min(), 0, alpha=0.1, color='red', label='Underperformance Zone')
    
    ax2.set_ylabel('Relative Performance (%)')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('turtle_sp500_results.png', dpi=300, bbox_inches='tight')
    print("\nChart saved as 'turtle_sp500_results.png'")
    # Remove plt.show() to prevent multiple graphs
    
    # Save trades
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df.to_csv('turtle_sp500_trades.csv', index=False)
        print("Trades saved to 'turtle_sp500_trades.csv'")
        
        # Show top trades
        print("\nTop 10 Trades:")
        top_trades = trades_df.nlargest(10, 'pnl_pct')[['symbol', 'pnl_pct']]
        for _, trade in top_trades.iterrows():
            print(f"  {trade['symbol']}: {trade['pnl_pct']:.1f}%")
    
    return portfolio_series, spy_series, all_trades

if __name__ == "__main__":
    print("Starting S&P 500 Turtle Trading Portfolio Backtest...")
    print("Using top 100 S&P 500 stocks")
    print()
    
    portfolio, spy, trades = run_sp500_turtle_portfolio()
    
    print("\n✓ Backtest complete!")
    print("✓ Chart saved as 'turtle_sp500_results.png'")
    if trades:
        print("✓ Trades saved as 'turtle_sp500_trades.csv'")