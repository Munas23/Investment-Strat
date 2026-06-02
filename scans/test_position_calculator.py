"""
Test Position Calculator with Real Data

Tests the position calculator with NVDA from screening results.
"""

from position_calculator import PositionSizingCalculator
import pandas as pd

def test_nvda_position():
    """
    Test position sizing for NVDA (from screening results).
    """
    print("="*80)
    print("TEST: Position Sizing Calculator")
    print("="*80)

    # Initialize calculator
    calc = PositionSizingCalculator(account_size=2_000_000)

    # NVDA data from screening results
    print("\nStock: NVDA (from fundamental screening)")
    print("   Fundamental Score: 83.3% (A)")
    print("   Liquidity Tier: TIER 2 - GOOD")
    print("   DDV: $34.9 billion")

    # Fetch current data
    print("\nFetching current price and ATR...")
    symbol = 'NVDA'
    current_price = calc.get_current_price(symbol)
    atr = calc.calculate_atr(symbol)

    if current_price is None or atr is None:
        print("ERROR: Could not fetch data for NVDA")
        # Use manual values for demo
        current_price = 140.00
        atr = 5.50
        print(f"   Using manual values: Price=${current_price}, ATR=${atr}")
    else:
        print(f"SUCCESS: Current Price: ${current_price:.2f}")
        print(f"SUCCESS: ATR (14-day): ${atr:.2f}")

    # Test scenarios
    scenarios = [
        {
            'name': 'Level 5 - Bull Market',
            'conviction': 5,
            'market': 'bull',
            'pattern': 'vcp',
        },
        {
            'name': 'Level 4 - Uptrend',
            'conviction': 4,
            'market': 'uptrend',
            'pattern': 'standard',
        },
        {
            'name': 'Level 3 - Neutral Market',
            'conviction': 3,
            'market': 'neutral',
            'pattern': 'standard',
        },
    ]

    results = []

    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'='*80}")

        position = calc.calculate_position_size(
            symbol='NVDA',
            entry_price=current_price,
            atr=atr,
            conviction_level=scenario['conviction'],
            market_health=scenario['market'],
            liquidity_tier='TIER 2 - GOOD',
            ddv=34_858_610_000,  # $34.9B from screening
            fundamental_score=83.3,
            pattern_type=scenario['pattern']
        )

        # Print summary
        print(f"\nPosition: {position['shares']:,} shares @ ${position['entry_price']:.2f}")
        print(f"   Value: ${position['position_value']:,.2f} ({position['position_pct_of_account']:.1f}% of account)")
        print(f"   Risk: ${position['dollar_risk']:,.2f} ({position['final_risk_pct']:.2f}%)")
        print(f"   Stop: ${position['stop_price']:.2f} ({position['stop_percent']:.1f}%)")
        print(f"   Target 1: ${position['target_1_price']:.2f} (+{position['target_1_percent']:.1f}%) = {position['target_1_r_multiple']:.1f}R")
        print(f"   R:R Ratio: 1:{position['risk_reward_ratio']:.1f}")

        if position['limited']:
            print(f"   WARNING: LIMITED BY: {position['limiting_factor']}")

        results.append(position)

    # Comparison table
    print("\n" + "="*80)
    print("COMPARISON: All Scenarios")
    print("="*80)

    comparison = pd.DataFrame([
        {
            'Scenario': r['pattern_type'] + ' L' + str(r['conviction_level']),
            'Market': r['market_health'],
            'Shares': f"{r['shares']:,}",
            'Position $': f"${r['position_value']:,.0f}",
            'Pos %': f"{r['position_pct_of_account']:.1f}%",
            'Risk %': f"{r['final_risk_pct']:.2f}%",
            'Stop %': f"{r['stop_percent']:.1f}%",
            'Target 1': f"+{r['target_1_percent']:.1f}%",
            'R:R': f"1:{r['risk_reward_ratio']:.1f}",
        }
        for r in results
    ])

    print(comparison.to_string(index=False))

    # Portfolio simulation
    print("\n" + "="*80)
    print("PORTFOLIO SIMULATION")
    print("="*80)

    # Add all positions to portfolio
    calc_portfolio = PositionSizingCalculator(account_size=2_000_000)

    for i, position in enumerate(results, 1):
        can_add, message = calc_portfolio.check_portfolio_limits(position['final_risk_pct'])
        if can_add:
            calc_portfolio.add_position_to_portfolio(position)
            print(f"SUCCESS: Added Scenario {i}: {position['final_risk_pct']:.2f}% risk")
        else:
            print(f"ERROR: Cannot add Scenario {i}: {message}")

    summary = calc_portfolio.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"   Positions: {summary['total_positions']}")
    print(f"   Total Risk: {summary['total_risk_pct']:.2f}% / {calc_portfolio.max_total_portfolio_risk}%")
    print(f"   Capital Deployed: ${summary['total_capital_deployed']:,.2f} ({summary['capital_deployed_pct']:.1f}%)")
    print(f"   Average Position: ${summary['average_position_size']:,.2f}")
    print(f"   Available Risk: {summary['available_risk']:.2f}%")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    test_nvda_position()
