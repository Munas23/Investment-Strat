"""Quick test to verify yfinance data retrieval works"""
import yfinance as yf
import sys
import os

# Test known good tickers
test_tickers = ['AAPL', 'MSFT', 'CBA.AX', 'BHP.AX']

print("Testing yfinance data retrieval...")
print("=" * 50)

for ticker_symbol in test_tickers:
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1mo")
        info = ticker.info

        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            volume = hist['Volume'].iloc[-1]
            market_cap = info.get('marketCap', 'N/A')
            print(f"OK {ticker_symbol}: Price=${current_price:.2f}, Volume={volume:,.0f}, MarketCap={market_cap}")
        else:
            print(f"FAIL {ticker_symbol}: No price data available")

    except Exception as e:
        print(f"ERROR {ticker_symbol}: {e}")

print("=" * 50)
print("Test complete.")