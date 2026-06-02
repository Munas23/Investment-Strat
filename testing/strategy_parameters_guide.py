
"""
Strategy Parameters Guide
========================

This guide explains all configurable parameters for the
Professional Growth Strategy.
"""

STRATEGY_PARAMETERS = {
    # FUNDAMENTAL SCREENING
    "fundamental_score_threshold": {
        "default": 60.0,
        "range": "50.0 - 80.0",
        "description": "Minimum fundamental score for stock selection"
    },
    
    "rescreen_frequency": {
        "default": 30,
        "range": "7 - 90 days", 
        "description": "How often to rescreen fundamentals"
    },
    
    # POSITION MANAGEMENT
    "max_positions": {
        "default": 8,
        "range": "4 - 12",
        "description": "Maximum number of concurrent positions"
    },
    
    "position_size_pct": {
        "default": 0.125,
        "range": "0.08 - 0.20",
        "description": "Position size as percentage of portfolio"
    },
    
    # ENTRY SIGNALS
    "min_conviction": {
        "default": 3,
        "range": "1 - 5",
        "description": "Minimum conviction level for entry"
    },
    
    "volume_threshold": {
        "default": 1.5,
        "range": "1.2 - 3.0",
        "description": "Minimum volume surge for entry"
    },
    
    # HYBRID EXIT STRATEGY (OPTIMAL SETTINGS)
    "profit_trigger": {
        "default": 50.0,
        "range": "30.0 - 100.0",
        "description": "Profit level to activate trailing stop"
    },
    
    "trailing_stop_pct": {
        "default": 15.0,
        "range": "10.0 - 25.0", 
        "description": "Trailing stop percentage"
    },
    
    "stop_loss_pct": {
        "default": 7.0,
        "range": "5.0 - 10.0",
        "description": "Disaster stop loss percentage"
    }
}

def print_parameter_guide():
    """Print formatted parameter guide"""
    print("STRATEGY PARAMETERS GUIDE")
    print("=" * 40)
    
    for param, info in STRATEGY_PARAMETERS.items():
        print(f"\n{param}:")
        print(f"  Default: {info['default']}")
        print(f"  Range: {info['range']}")
        print(f"  Description: {info['description']}")

def get_optimal_parameters():
    """Get the optimal parameters from our testing"""
    return {
        "fundamental_score_threshold": 60.0,
        "max_positions": 8,
        "profit_trigger": 50.0,        # From hybrid testing - best performer
        "trailing_stop_pct": 15.0,     # From hybrid testing - best performer  
        "stop_loss_pct": 7.0,
        "min_conviction": 3,
        "volume_threshold": 1.5
    }

if __name__ == "__main__":
    print_parameter_guide()
    print("\n" + "=" * 40)
    print("OPTIMAL PARAMETERS (from testing):")
    optimal = get_optimal_parameters()
    for param, value in optimal.items():
        print(f"  {param}: {value}")
