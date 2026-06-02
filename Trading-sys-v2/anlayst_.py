import pandas as pd
import os

def analyze_optimization_results():
    """Analyze optimization results and create optimized strategy version"""
    # Set up file paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_path, 'optimization_results.csv')
    template_path = os.path.join(base_path, 'v2.py')
    output_path = os.path.join(base_path, 'v2_optimized.py')

    try:
        # Read and analyze optimization results
        if not os.path.exists(csv_path):
            raise FileNotFoundError("optimization_results.csv not found in Trading-sys-v2 folder")
            
        df = pd.read_csv(csv_path)
        
        # Parse parameters from params column
        params_df = pd.json_normalize(df['params'].apply(eval))
        
        # Combine parameters with metrics
        analysis_df = pd.concat([params_df, df[['total_return', 'sharpe_ratio', 'max_drawdown', 'total_trades']]], axis=1)
        
        # Sort by performance metrics
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        for metric in metrics:
            print(f"\nTop 5 configurations by {metric}:")
            df_sorted = analysis_df.sort_values(by=metric, ascending=False if metric != 'max_drawdown' else True)
            display_cols = ['flagpole_min_gain', 'consolidation_volatility_threshold', 
                          'max_stop_loss', metric, 'total_trades']
            print(df_sorted[display_cols].head().to_string())
        
        # Get best overall parameters (using total return)
        best_params = df_sorted.iloc[0]
        
        # Create optimized version
        param_replacements = {
            'FLAGPOLE_MIN_GAIN': best_params['flagpole_min_gain'],
            'VOLATILITY_THRESHOLD': best_params['consolidation_volatility_threshold'],
            'MAX_STOP_LOSS': best_params['max_stop_loss'],
            'MAX_POSITION_SIZE': 0.10  # Default value
        }
        
        # Read and modify template
        if not os.path.exists(template_path):
            raise FileNotFoundError("v2.py template not found in Trading-sys-v2 folder")
            
        with open(template_path, 'r') as template_file:
            template_content = template_file.read()
            
        new_content = template_content
        for param, value in param_replacements.items():
            placeholder = f"#{param}#"
            new_content = new_content.replace(placeholder, str(value))
        
        # Write optimized version
        with open(output_path, 'w') as new_file:
            new_file.write(new_content)
        
        print(f"\nSuccessfully created optimized version: {output_path}")
        print("\nBest parameters:")
        for param, value in param_replacements.items():
            print(f"{param}: {value:.4f}")
        
        # Print additional statistics
        print("\nStrategy Performance:")
        print(f"Total Return: {best_params['total_return']:.2f}%")
        print(f"Sharpe Ratio: {best_params['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {best_params['max_drawdown']:.2f}%")
        print(f"Total Trades: {best_params['total_trades']}")
        
    except Exception as e:
        print(f"Error analyzing results: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_optimization_results()