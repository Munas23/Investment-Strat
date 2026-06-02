
"""
Market Universe Reference
========================

This file shows all available market universes for testing
the professional growth strategy.
"""

MARKET_UNIVERSES = {
    "US_LARGE_CAP": [
        # S&P 100 Large Cap Growth Leaders
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX",
        "ADBE", "CRM", "ORCL", "INTC", "AMD", "QCOM", "AVGO", "TXN",
        "NOW", "INTU", "CSCO", "IBM", "AMAT", "MU", "ADI", "KLAC"
    ],
    
    "US_MID_CAP": [
        # Mid-cap growth and emerging leaders
        "PLTR", "SNOW", "DDOG", "NET", "CRWD", "ZM", "DOCU", "TWLO",
        "ROKU", "SQ", "SHOP", "UBER", "LYFT", "PINS", "SNAP", "SPOT"
    ],
    
    "TECHNOLOGY": [
        # Pure tech plays
        "NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN", "ADI", "KLAC",
        "LRCX", "AMAT", "MU", "WDC", "STX", "MRVL", "SWKS", "MXIM"
    ],
    
    "HEALTHCARE": [
        # Healthcare and biotech focus  
        "JNJ", "PFE", "UNH", "ABBV", "TMO", "DHR", "ABT", "BMY",
        "LLY", "MRK", "AMGN", "GILD", "REGN", "VRTX", "BIIB", "MRNA"
    ],
    
    "CONSUMER": [
        # Consumer growth stocks
        "AMZN", "SHOP", "ETSY", "W", "CHWY", "PTON", "NKE", "LULU",
        "SBUX", "MCD", "CMG", "DKNG", "PENN", "MGM", "WYNN", "LVS"
    ]
}

def get_market_symbols(market_name):
    """Get symbols for a specific market"""
    return MARKET_UNIVERSES.get(market_name, [])

def list_all_markets():
    """List all available markets"""
    print("AVAILABLE MARKETS:")
    print("=" * 20)
    for market in MARKET_UNIVERSES.keys():
        count = len(MARKET_UNIVERSES[market])
        print(f"{market}: {count} stocks")

if __name__ == "__main__":
    list_all_markets()
