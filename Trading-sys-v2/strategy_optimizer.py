import itertools
import pandas as pd
from v2 import *  # Import your existing strategy code

class StrategyOptimizer:
    def __init__(self):
        self.parameter_ranges = {
            'flagpole_min_gain': [0.15, 0.20, 0.25],
            'consolidation_volatility_threshold': [0.3, 0.4, 0.5],
            'ma_fast': [5, 10, 15],
            'ma_medium': [20, 25, 30],
            'ma_slow': [50, 60, 70],
            'max_stop_loss': [0.05, 0.08, 0.10],
            'max_position_size': [0.05, 0.10, 0.15]
        }
        
        self.results = []
        
    def run_optimization(self, data_cache=None):
        """Run strategy with different parameter combinations"""
        # Generate all parameter combinations
        param_names = list(self.parameter_ranges.keys())
        param_values = list(self.parameter_ranges.values())
        combinations = list(itertools.product(*param_values))
        
        print(f"Testing {len(combinations)} parameter combinations...")
        
        # If no cached data, download it once
        if data_cache is None:
            config = StrategyConfig()
            tickers = get_sp500_tickers()[:50]  # Use subset for faster testing
            data_cache = download_data(tickers, config.start_date, config.end_date)
        
        # Test each combination
        for i, params in enumerate(combinations):
            config = StrategyConfig()
            
            # Update config with new parameters
            for name, value in zip(param_names, params):
                setattr(config, name, value)
            
            print(f"\nTesting combination {i+1}/{len(combinations)}:")
            print(" ".join(f"{name}={value:.2f}" for name, value in zip(param_names, params)))
            
            try:
                # Run backtest with current parameters
                indicators = calculate_indicators(data_cache, config)
                portfolio = run_backtest(indicators, config)
                stats = portfolio.stats()
                
                # Store results
                result = {
                    'params': dict(zip(param_names, params)),
                    'total_return': stats['Total Return [%]'],
                    'max_drawdown': stats['Max Drawdown [%]'],
                    'sharpe_ratio': stats['Sharpe Ratio'],
                    'total_trades': stats['Total Trades']
                }
                self.results.append(result)
                
                print(f"Return: {result['total_return']:.2f}%, "
                      f"Sharpe: {result['sharpe_ratio']:.2f}, "
                      f"Trades: {result['total_trades']}")
                
            except Exception as e:
                print(f"Error testing combination: {e}")
                continue
    
    def get_best_parameters(self, metric='total_return'):
        """Find best performing parameters based on chosen metric"""
        if not self.results:
            return None
            
        # Convert results to DataFrame
        df_results = pd.DataFrame(self.results)
        
        # Sort by chosen metric
        best_idx = df_results[metric].idxmax()
        best_result = df_results.iloc[best_idx]
        
        print("\n=== Best Parameters ===")
        print(f"Based on {metric}:")
        for param, value in best_result['params'].items():
            print(f"{param}: {value:.3f}")
        print(f"\nPerformance Metrics:")
        print(f"Total Return: {best_result['total_return']:.2f}%")
        print(f"Sharpe Ratio: {best_result['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {best_result['max_drawdown']:.2f}%")
        print(f"Total Trades: {best_result['total_trades']}")
        
        return best_result['params']

def main():
    # Initialize optimizer
    optimizer = StrategyOptimizer()
    
    # Run optimization
    optimizer.run_optimization()
    
    # Get best parameters
    best_params = optimizer.get_best_parameters()
    
    # Save results to CSV
    if optimizer.results:
        df_results = pd.DataFrame(optimizer.results)
        df_results.to_csv('optimization_results.csv', index=False)
        print("\nResults saved to optimization_results.csv")

if __name__ == "__main__":
    main()