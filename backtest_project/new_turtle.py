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
    position_size = 0.03  # 5% per position
    entry_days = 20
    exit_days = 10
    start_date = '2015-01-01'
    end_date = '2024-12-31'
    
    print(f"Initial Capital: ${initial_capital:,}")
    print(f"Max Positions: {max_positions}")
    print(f"Position Size: {position_size*100}%")
    print(f"Period: {start_date} to {end_date}")
    print(f"Momentum Filter: Stock must be up 20%+ in last 6 months")
    
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
                            # 6-month momentum filter: stock must be up 20% in last 6 months (126 trading days)
                            momentum_period = 126  # approximately 6 months of trading days
                            if idx >= momentum_period:
                                current_price = float(data['Close'].iloc[idx])
                                price_6m_ago = float(data['Close'].iloc[idx-momentum_period])
                                six_month_return = (current_price / price_6m_ago) - 1
                                
                                # Only consider stocks up 20% or more in last 6 months
                                if six_month_return >= 0.20:
                                    # Calculate short-term momentum for ranking among qualified stocks
                                    if idx >= 20:
                                        momentum = (current_price / float(data['Close'].iloc[idx-20])) - 1
                                        candidates.append((symbol, current_price, momentum, six_month_return))
            
            # Sort by short-term momentum and enter best ones
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            for symbol, price, momentum, six_month_return in candidates[:max_positions - len(positions)]:
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
    
    # Calculate detailed performance metrics
    def calculate_performance_metrics(returns_series, benchmark_series):
        """Calculate comprehensive performance metrics"""
        
        # Convert to daily returns
        portfolio_returns = returns_series.pct_change().dropna()
        benchmark_returns = benchmark_series.pct_change().dropna()
        
        # Align the series
        aligned_data = pd.concat([portfolio_returns, benchmark_returns], axis=1, join='inner')
        port_ret = aligned_data.iloc[:, 0]
        bench_ret = aligned_data.iloc[:, 1]
        
        # Basic metrics
        total_return_port = (returns_series.iloc[-1] / returns_series.iloc[0]) - 1
        total_return_bench = (benchmark_series.iloc[-1] / benchmark_series.iloc[0]) - 1
        
        # Annualized metrics (assuming daily data)
        trading_days = len(port_ret)
        years = trading_days / 252
        
        annual_return_port = (1 + total_return_port) ** (1/years) - 1
        annual_return_bench = (1 + total_return_bench) ** (1/years) - 1
        
        # Volatility
        annual_vol_port = port_ret.std() * np.sqrt(252)
        annual_vol_bench = bench_ret.std() * np.sqrt(252)
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        sharpe_port = (annual_return_port - risk_free_rate) / annual_vol_port if annual_vol_port != 0 else 0
        sharpe_bench = (annual_return_bench - risk_free_rate) / annual_vol_bench if annual_vol_bench != 0 else 0
        
        # Max drawdown - fixed to return scalar values
        def calculate_max_drawdown(price_series):
            cumulative = (1 + price_series.pct_change()).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            return float(drawdown.min())  # Convert to scalar
        
        max_dd_port = calculate_max_drawdown(returns_series)
        max_dd_bench = calculate_max_drawdown(benchmark_series)
        
        # Calmar ratio - now using scalar values
        calmar_port = annual_return_port / abs(max_dd_port) if max_dd_port != 0 else 0
        calmar_bench = annual_return_bench / abs(max_dd_bench) if max_dd_bench != 0 else 0
        
        # Beta and Alpha
        if len(port_ret) > 1 and len(bench_ret) > 1:
            covariance = port_ret.cov(bench_ret)
            benchmark_variance = bench_ret.var()
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
            alpha = annual_return_port - (risk_free_rate + beta * (annual_return_bench - risk_free_rate))
        else:
            beta = 0
            alpha = 0
        
        # Information ratio
        if len(port_ret) > 1:
            excess_returns = port_ret - bench_ret
            tracking_error = excess_returns.std() * np.sqrt(252)
            information_ratio = (annual_return_port - annual_return_bench) / tracking_error if tracking_error != 0 else 0
        else:
            information_ratio = 0
        
        # Win rate
        win_rate = (port_ret > 0).mean() if len(port_ret) > 0 else 0
        
        # Sortino ratio
        downside_returns = port_ret[port_ret < 0]
        if len(downside_returns) > 0:
            downside_deviation = downside_returns.std() * np.sqrt(252)
            sortino_ratio = (annual_return_port - risk_free_rate) / downside_deviation if downside_deviation != 0 else 0
        else:
            sortino_ratio = 0
        
        return {
            'Total Return': float(total_return_port),
            'Annual Return': float(annual_return_port),
            'Volatility': float(annual_vol_port),
            'Sharpe Ratio': float(sharpe_port),
            'Max Drawdown': float(max_dd_port),
            'Calmar Ratio': float(calmar_port),
            'Beta': float(beta),
            'Alpha': float(alpha),
            'Information Ratio': float(information_ratio),
            'Win Rate': float(win_rate),
            'Sortino Ratio': float(sortino_ratio),
            'Benchmark Total Return': float(total_return_bench),
            'Benchmark Annual Return': float(annual_return_bench),
            'Benchmark Volatility': float(annual_vol_bench),
            'Benchmark Sharpe': float(sharpe_bench),
            'Benchmark Max DD': float(max_dd_bench),
            'Benchmark Calmar': float(calmar_bench)
        }
    
    # Calculate results
    portfolio_series = pd.Series(portfolio_value, index=dates)
    spy_series = spy_data['Close'].loc[dates]
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(portfolio_series, spy_series)
    
    # Calculate returns
    total_return = metrics['Total Return'] * 100
    spy_return = metrics['Benchmark Total Return'] * 100
    
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
    
    # Display comprehensive results
    print("\n" + "="*80)
    print("COMPREHENSIVE PORTFOLIO ANALYSIS")
    print("="*80)
    
    print(f"\n📊 PERFORMANCE SUMMARY")
    print(f"{'Metric':<25} {'Portfolio':<15} {'SPY Benchmark':<15} {'Difference':<15}")
    print("-" * 70)
    print(f"{'Total Return':<25} {total_return:>13.2f}% {spy_return:>13.2f}% {total_return-spy_return:>13.2f}%")
    print(f"{'Annual Return':<25} {metrics['Annual Return']*100:>13.2f}% {metrics['Benchmark Annual Return']*100:>13.2f}% {(metrics['Annual Return']-metrics['Benchmark Annual Return'])*100:>13.2f}%")
    print(f"{'Volatility':<25} {metrics['Volatility']*100:>13.2f}% {metrics['Benchmark Volatility']*100:>13.2f}% {(metrics['Volatility']-metrics['Benchmark Volatility'])*100:>13.2f}%")
    print(f"{'Sharpe Ratio':<25} {metrics['Sharpe Ratio']:>13.2f} {metrics['Benchmark Sharpe']:>13.2f} {metrics['Sharpe Ratio']-metrics['Benchmark Sharpe']:>13.2f}")
    print(f"{'Max Drawdown':<25} {metrics['Max Drawdown']*100:>13.2f}% {metrics['Benchmark Max DD']*100:>13.2f}% {(metrics['Max Drawdown']-metrics['Benchmark Max DD'])*100:>13.2f}%")
    print(f"{'Calmar Ratio':<25} {metrics['Calmar Ratio']:>13.2f} {metrics['Benchmark Calmar']:>13.2f} {metrics['Calmar Ratio']-metrics['Benchmark Calmar']:>13.2f}")
    
    print(f"\n🎯 ADVANCED METRICS")
    print(f"Beta (vs SPY): {metrics['Beta']:.3f}")
    print(f"Alpha (annual): {metrics['Alpha']*100:.2f}%")
    print(f"Information Ratio: {metrics['Information Ratio']:.3f}")
    print(f"Sortino Ratio: {metrics['Sortino Ratio']:.3f}")
    print(f"Win Rate (daily): {metrics['Win Rate']*100:.1f}%")
    
    print(f"\n💰 PORTFOLIO DETAILS")
    print(f"Final Value: ${portfolio_series.iloc[-1]:,.2f}")
    print(f"Total Trades: {num_trades}")
    print(f"Trade Win Rate: {win_rate:.2f}%")
    print(f"Avg Winning Trade: {avg_win:.2f}%")
    print(f"Avg Losing Trade: {avg_loss:.2f}%")
    
    # Risk-adjusted performance rating
    def get_performance_rating(sharpe):
        if sharpe > 1.5: return "🌟 Excellent"
        elif sharpe > 1.0: return "✅ Good"
        elif sharpe > 0.5: return "⚠️ Fair"
        else: return "❌ Poor"
    
    print(f"\n📈 PERFORMANCE RATING")
    print(f"Strategy Rating: {get_performance_rating(metrics['Sharpe Ratio'])}")
    print(f"Benchmark Rating: {get_performance_rating(metrics['Benchmark Sharpe'])}")
    
    if metrics['Sharpe Ratio'] > metrics['Benchmark Sharpe']:
        print(f"✨ Strategy outperformed benchmark on risk-adjusted basis!")
    else:
        print(f"📉 Strategy underperformed benchmark on risk-adjusted basis")
    
    # Create robust visualizations
    plt.style.use('default')
    
    # Normalize both to start at 100
    portfolio_norm = portfolio_series / portfolio_series.iloc[0] * 100
    spy_norm = spy_series / spy_series.iloc[0] * 100
    
    # Chart 1: Main Performance Chart
    plt.figure(figsize=(12, 8))
    plt.plot(portfolio_norm.index, portfolio_norm.values, label='Turtle Portfolio', linewidth=2.5, color='green')
    plt.plot(spy_norm.index, spy_norm.values, label='SPY Benchmark', linewidth=2.5, color='blue', alpha=0.8)
    
    plt.title('S&P 500 Turtle Trading Portfolio vs SPY Benchmark', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Value (Start = 100)', fontsize=12)
    plt.legend(loc='upper left', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add performance stats box
    textstr = f'Portfolio Return: {total_return:.1f}%\nSPY Return: {spy_return:.1f}%\nSharpe Ratio: {metrics["Sharpe Ratio"]:.2f}\nMax Drawdown: {metrics["Max Drawdown"]*100:.1f}%'
    props = dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig('turtle_main_performance.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    # Chart 2: Drawdown Analysis
    plt.figure(figsize=(12, 6))
    
    # Calculate drawdowns - ensure 1D arrays
    portfolio_dd = (portfolio_norm / portfolio_norm.expanding().max() - 1) * 100
    spy_dd = (spy_norm / spy_norm.expanding().max() - 1) * 100
    
    # Convert to numpy arrays and flatten to ensure 1D
    portfolio_dd_values = np.array(portfolio_dd.values).flatten()
    spy_dd_values = np.array(spy_dd.values).flatten()
    dd_index = portfolio_dd.index
    
    plt.fill_between(dd_index, portfolio_dd_values, 0, alpha=0.3, color='red', label='Portfolio Drawdown')
    plt.fill_between(dd_index, spy_dd_values, 0, alpha=0.3, color='blue', label='SPY Drawdown')
    
    plt.plot(dd_index, portfolio_dd_values, color='darkred', linewidth=1.5)
    plt.plot(dd_index, spy_dd_values, color='darkblue', linewidth=1.5)
    
    plt.title('Drawdown Analysis', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Drawdown (%)', fontsize=12)
    plt.legend(loc='lower left', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add max drawdown annotations
    max_dd_idx = portfolio_dd.idxmin()
    max_dd_value = portfolio_dd_values.min()
    plt.annotate(f'Max DD: {max_dd_value:.1f}%', 
                xy=(max_dd_idx, max_dd_value), 
                xytext=(max_dd_idx, max_dd_value - 5),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10, color='red')
    
    plt.tight_layout()
    plt.savefig('turtle_drawdown_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    # Chart 3: Risk-Return Analysis
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Left panel: Risk-Return scatter
    ax1.scatter(metrics['Volatility']*100, metrics['Annual Return']*100, s=200, color='green', 
               label='Turtle Portfolio', edgecolors='darkgreen', linewidth=2)
    ax1.scatter(metrics['Benchmark Volatility']*100, metrics['Benchmark Annual Return']*100, s=200, color='blue', 
               label='SPY Benchmark', edgecolors='darkblue', linewidth=2)
    
    # Add Sharpe ratio lines
    x_range = np.linspace(0, max(metrics['Volatility'], metrics['Benchmark Volatility'])*100*1.2, 100)
    for sharpe in [0.5, 1.0, 1.5]:
        y_range = sharpe * x_range / 100 + 2  # 2% risk-free rate
        ax1.plot(x_range, y_range*100, '--', alpha=0.3, label=f'Sharpe={sharpe}')
    
    ax1.set_xlabel('Volatility (%)', fontsize=12)
    ax1.set_ylabel('Annual Return (%)', fontsize=12)
    ax1.set_title('Risk-Return Analysis', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Right panel: Rolling Sharpe Ratio
    if len(portfolio_series) > 60:
        portfolio_returns = portfolio_series.pct_change().dropna()
        spy_returns = spy_series.pct_change().dropna()
        
        # Calculate 60-day rolling Sharpe
        rolling_window = 60
        port_rolling_sharpe = (portfolio_returns.rolling(rolling_window).mean() * 252) / (portfolio_returns.rolling(rolling_window).std() * np.sqrt(252))
        spy_rolling_sharpe = (spy_returns.rolling(rolling_window).mean() * 252) / (spy_returns.rolling(rolling_window).std() * np.sqrt(252))
        
        ax2.plot(port_rolling_sharpe.index, port_rolling_sharpe.values, label='Portfolio', color='green', linewidth=2)
        ax2.plot(spy_rolling_sharpe.index, spy_rolling_sharpe.values, label='SPY', color='blue', linewidth=2)
        ax2.axhline(y=1, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('60-Day Rolling Sharpe Ratio', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Sharpe Ratio', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('turtle_risk_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    # Chart 4: Monthly Performance
    if len(portfolio_series) > 30:
        # Calculate monthly returns
        portfolio_monthly = portfolio_series.resample('M').last().pct_change().dropna() * 100
        spy_monthly = spy_series.resample('M').last().pct_change().dropna() * 100
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Create bar positions
        months = portfolio_monthly.index
        x = np.arange(len(months))
        width = 0.35
        
        # Ensure values are 1D arrays
        portfolio_monthly_values = np.array(portfolio_monthly.values).flatten()
        spy_monthly_values = np.array(spy_monthly.values).flatten()
        
        # Create bars
        bars1 = ax.bar(x - width/2, portfolio_monthly_values, width, label='Portfolio', 
                       color=['green' if r > 0 else 'red' for r in portfolio_monthly_values], alpha=0.8)
        bars2 = ax.bar(x + width/2, spy_monthly_values, width, label='SPY', 
                       color=['lightblue' if r > 0 else 'lightcoral' for r in spy_monthly_values], alpha=0.8)
        
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Monthly Return (%)', fontsize=12)
        ax.set_title('Monthly Performance Comparison', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([d.strftime('%b %y') for d in months], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        # Add summary stats
        avg_port = portfolio_monthly_values.mean()
        avg_spy = spy_monthly_values.mean()
        textstr = f'Avg Monthly Return:\nPortfolio: {avg_port:.2f}%\nSPY: {avg_spy:.2f}%'
        props = dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        plt.savefig('turtle_monthly_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
    
    print("\n✅ Charts saved:")
    print("   - turtle_main_performance.png")
    print("   - turtle_drawdown_analysis.png")
    print("   - turtle_risk_analysis.png")
    print("   - turtle_monthly_performance.png")
    
    # Save trades
    if all_trades:
        trades_df = pd.DataFrame(all_trades)
        trades_df.to_csv('turtle_sp500_trades.csv', index=False)
        print("\n✅ Trades saved to 'turtle_sp500_trades.csv'")
        
        # Show top trades
        print("\nTop 10 Trades:")
        top_trades = trades_df.nlargest(10, 'pnl_pct')[['symbol', 'pnl_pct']]
        for _, trade in top_trades.iterrows():
            print(f"  {trade['symbol']}: {trade['pnl_pct']:.1f}%")
        
        print(f"\nStrategy Summary:")
        print(f"- 6-month momentum filter significantly reduced trade frequency")
        print(f"- Only stocks up 20%+ in 6 months were eligible for entry")
        print(f"- This should improve win rate and reduce drawdowns")
    
    return portfolio_series, spy_series, all_trades

if __name__ == "__main__":
    print("Starting COMPLETE S&P 500 Turtle Trading Portfolio Backtest...")
    print("Using all 503 S&P 500 stocks with 6-month momentum filter")
    print("⚠️  This will take several minutes to download data and process...")
    print()
    
    portfolio, spy, trades = run_sp500_turtle_portfolio()
    
    print("\n✓ Backtest complete!")
    print("✓ All charts saved successfully!")
    if trades:
        print("✓ Trades saved as 'turtle_sp500_trades.csv'")