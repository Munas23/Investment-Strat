"""
Comprehensive Backtesting Engine for $2M Trading Account

Integrates:
- Position sizing calculator
- Multiple trading systems
- Risk management framework
- Historical data processing
- Performance metrics

Based on existing backtest frameworks with enhancements.

Author: Trading System
Date: 2026-01-02
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add parent directory to path to import position calculator
sys.path.append(str(Path(__file__).parent.parent))
from position_calculator import PositionSizingCalculator


@dataclass
class Trade:
    """Record of a single trade."""
    symbol: str
    entry_date: str
    entry_price: float
    shares: int
    position_value: float
    conviction_level: int
    stop_price: float
    stop_percent: float
    target_1_price: float
    target_2_price: float
    target_3_price: float
    position_risk_pct: float
    dollar_risk: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl_dollars: Optional[float] = None
    pnl_percent: Optional[float] = None
    r_multiple: Optional[float] = None
    holding_days: Optional[int] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for backtest."""
    # Returns
    total_return_pct: float
    total_return_dollars: float
    cagr: float

    # Risk metrics
    max_drawdown_pct: float
    max_drawdown_dollars: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # P&L statistics
    avg_win_pct: float
    avg_loss_pct: float
    avg_win_dollars: float
    avg_loss_dollars: float
    largest_win_pct: float
    largest_loss_pct: float
    profit_factor: float

    # R-multiple statistics
    avg_r_multiple: float
    expectancy: float

    # Position statistics
    avg_holding_days: float
    max_positions_held: int
    avg_position_size_pct: float
    exposure_pct: float        # % of days with at least one open position
    turnover: float            # total traded $ volume / initial capital

    # System health
    max_consecutive_losses: int
    recovery_days: int


class BacktestEngine:
    """
    Core backtesting engine with integrated position sizing.
    """

    def __init__(
        self,
        account_size: float = 2_000_000,
        start_date: str = '2020-01-01',
        end_date: str = '2024-12-31',
        transaction_cost_pct: float = 0.1,
        slippage_pct: float = 0.05,
        risk_free_rate: float = 3.0
    ):
        """
        Initialize backtest engine.

        Args:
            account_size: Starting capital
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            transaction_cost_pct: Transaction cost %
            slippage_pct: Slippage %
            risk_free_rate: Annual risk-free rate %
        """
        self.initial_capital = account_size
        self.current_capital = account_size
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.risk_free_rate = risk_free_rate

        # Position sizing calculator
        self.position_calculator = PositionSizingCalculator(account_size=account_size)

        # Trade tracking
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []

        # Equity curve
        self.equity_curve = []

        # Cache for historical data
        self.price_data_cache: Dict[str, pd.DataFrame] = {}

        # Pre-fetch SPY once for RS calculations and benchmark
        self._spy_data: Optional[pd.DataFrame] = self._fetch_spy()


    def _fetch_spy(self) -> Optional[pd.DataFrame]:
        """Fetch SPY data once for the full backtest period (with buffer)."""
        try:
            buffer_start = self.start_date - timedelta(days=300)
            df = yf.Ticker('SPY').history(start=buffer_start, end=self.end_date)
            if df.empty:
                return None
            df.columns = [c.lower() for c in df.columns]
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            return df
        except Exception as e:
            print(f"  Warning: Could not fetch SPY data: {e}")
            return None


    def fetch_historical_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data for a symbol.

        Args:
            symbol: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if error
        """
        # Check cache
        cache_key = f"{symbol}_{start_date}_{end_date}"
        if cache_key in self.price_data_cache:
            return self.price_data_cache[cache_key]

        try:
            start = start_date or self.start_date
            end = end_date or self.end_date

            # Add buffer for indicator calculation (200-day MA needs ~300 days warmup)
            buffer_start = pd.to_datetime(start) - timedelta(days=300)

            stock = yf.Ticker(symbol)
            df = stock.history(start=buffer_start, end=end)

            if df.empty:
                print(f"  Warning: No data for {symbol}")
                return None

            # Standardize column names
            df.columns = [col.lower() for col in df.columns]

            # FIX: Strip timezone so dates are comparable with pd.date_range (which is tz-naive)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            # Calculate ATR
            df = self._calculate_atr(df)

            # Calculate moving averages
            df['ma_10']  = df['close'].rolling(window=10).mean()
            df['ma_20']  = df['close'].rolling(window=20).mean()
            df['ma_50']  = df['close'].rolling(window=50).mean()
            df['ma_150'] = df['close'].rolling(window=150).mean()
            df['ma_200'] = df['close'].rolling(window=200).mean()

            # RS vs SPY — use cached SPY data fetched once on the engine
            if self._spy_data is not None:
                spy_returns   = self._spy_data['close'].pct_change(63)
                stock_returns = df['close'].pct_change(63)
                # Align on common index before dividing
                aligned_spy   = spy_returns.reindex(df.index)
                df['relative_strength'] = (stock_returns - aligned_spy) / aligned_spy.abs() * 100
            else:
                df['relative_strength'] = 0

            # Cache it
            self.price_data_cache[cache_key] = df

            return df

        except Exception as e:
            print(f"  Error fetching data for {symbol}: {e}")
            return None


    def enrich_cached_data(self, symbol: str, raw_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Add ATR, moving averages and RS to a pre-downloaded DataFrame.

        Used by run_backtest.py to reuse data already fetched by the
        HistoricalScreener, avoiding a second round of yfinance downloads.

        Args:
            symbol: Ticker symbol (for caching)
            raw_df: OHLCV DataFrame already stripped of timezone

        Returns:
            Enriched DataFrame (also stored in price_data_cache)
        """
        if raw_df is None or raw_df.empty:
            return None
        try:
            df = raw_df.copy()

            # Ensure column names are lowercase
            df.columns = [c.lower() for c in df.columns]
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            df = self._calculate_atr(df)

            df['ma_10']  = df['close'].rolling(window=10).mean()
            df['ma_20']  = df['close'].rolling(window=20).mean()
            df['ma_50']  = df['close'].rolling(window=50).mean()
            df['ma_150'] = df['close'].rolling(window=150).mean()
            df['ma_200'] = df['close'].rolling(window=200).mean()

            if self._spy_data is not None:
                spy_returns   = self._spy_data['close'].pct_change(63)
                stock_returns = df['close'].pct_change(63)
                aligned_spy   = spy_returns.reindex(df.index)
                df['relative_strength'] = (stock_returns - aligned_spy) / aligned_spy.abs() * 100
            else:
                df['relative_strength'] = 0

            self.price_data_cache[symbol] = df
            return df
        except Exception as e:
            print(f"  Error enriching data for {symbol}: {e}")
            return None


    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Average True Range.

        Args:
            df: DataFrame with OHLCV data
            period: ATR period

        Returns:
            DataFrame with ATR column added
        """
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=period).mean()

        return df


    def enter_trade(
        self,
        symbol: str,
        date: pd.Timestamp,
        price: float,
        atr: float,
        conviction_level: int,
        market_health: str = 'neutral',
        pattern_type: str = 'standard',
        liquidity_tier: str = 'TIER 2 - GOOD',
        ddv: float = 1_000_000_000
    ) -> Optional[Trade]:
        """
        Enter a new trade with position sizing.

        Args:
            symbol: Stock ticker
            date: Entry date
            price: Entry price
            atr: Average True Range
            conviction_level: Conviction level (1-5)
            market_health: Market condition
            pattern_type: Pattern type
            liquidity_tier: Liquidity classification
            ddv: Daily dollar volume

        Returns:
            Trade object or None if rejected
        """
        # Apply slippage to entry
        entry_price = price * (1 + self.slippage_pct / 100)

        # Calculate position using position sizing calculator
        position = self.position_calculator.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            atr=atr,
            conviction_level=conviction_level,
            market_health=market_health,
            liquidity_tier=liquidity_tier,
            ddv=ddv,
            pattern_type=pattern_type
        )

        # Check portfolio limits
        can_add, message = self.position_calculator.check_portfolio_limits(
            position['final_risk_pct']
        )

        if not can_add:
            print(f"  {date.date()} {symbol}: Rejected - {message}")
            return None

        # Apply transaction costs
        transaction_cost = position['position_value'] * (self.transaction_cost_pct / 100)

        # Check if we have enough capital
        total_cost = position['position_value'] + transaction_cost
        if total_cost > self.current_capital:
            print(f"  {date.date()} {symbol}: Rejected - Insufficient capital")
            return None

        # Create trade
        trade = Trade(
            symbol=symbol,
            entry_date=date.strftime('%Y-%m-%d'),
            entry_price=entry_price,
            shares=position['shares'],
            position_value=position['position_value'],
            conviction_level=conviction_level,
            stop_price=position['stop_price'],
            stop_percent=position['stop_percent'],
            target_1_price=position['target_1_price'],
            target_2_price=position['target_2_price'],
            target_3_price=position['target_3_price'],
            position_risk_pct=position['final_risk_pct'],
            dollar_risk=position['dollar_risk']
        )

        # Update capital
        self.current_capital -= total_cost

        # Add to portfolio
        self.open_trades.append(trade)
        self.position_calculator.add_position_to_portfolio(position)

        print(f"  {date.date()} {symbol}: Entered - {trade.shares} shares @ ${entry_price:.2f}, Stop: ${trade.stop_price:.2f}")

        return trade


    def exit_trade(
        self,
        trade: Trade,
        date: pd.Timestamp,
        price: float,
        reason: str
    ):
        """
        Exit a trade.

        Args:
            trade: Trade to exit
            date: Exit date
            price: Exit price
            reason: Exit reason (STOP_LOSS, PROFIT_TARGET, etc.)
        """
        # Apply slippage
        exit_price = price * (1 - self.slippage_pct / 100) if reason != 'STOP_LOSS' else price

        # Calculate P&L
        gross_proceeds = trade.shares * exit_price
        transaction_cost = gross_proceeds * (self.transaction_cost_pct / 100)
        net_proceeds = gross_proceeds - transaction_cost

        original_cost = trade.position_value + (trade.position_value * self.transaction_cost_pct / 100)
        pnl_dollars = net_proceeds - original_cost
        pnl_percent = (pnl_dollars / original_cost) * 100

        # Calculate R-multiple
        risk_amount = trade.shares * (trade.entry_price - trade.stop_price)
        r_multiple = pnl_dollars / risk_amount if risk_amount > 0 else 0

        # Calculate holding period
        entry_dt = pd.to_datetime(trade.entry_date)
        holding_days = (date - entry_dt).days

        # Update trade
        trade.exit_date = date.strftime('%Y-%m-%d')
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.pnl_dollars = pnl_dollars
        trade.pnl_percent = pnl_percent
        trade.r_multiple = r_multiple
        trade.holding_days = holding_days

        # Update capital
        self.current_capital += net_proceeds

        # Move to closed trades
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)

        # Update position calculator portfolio — sync current_positions with open_trades
        self.position_calculator.current_total_risk -= trade.position_risk_pct
        open_symbols = {t.symbol for t in self.open_trades}
        self.position_calculator.current_positions = [
            p for p in self.position_calculator.current_positions
            if p.get('symbol') in open_symbols
        ]

        print(f"  {date.date()} {trade.symbol}: Exited @ ${exit_price:.2f} - {reason} - P&L: ${pnl_dollars:,.0f} ({pnl_percent:.1f}%) = {r_multiple:.2f}R")


    def check_exits(self, date: pd.Timestamp, price_data: Dict[str, pd.DataFrame]):
        """
        Check and execute exits for open trades.

        Exit hierarchy (checked in order):
          1. Hard stop loss (original ATR stop)
          2. Chandelier trailing stop (3 ATR from highest close since entry)
          3. Profit Target 1 (scaled exit — partial or full depending on config)
        """
        for trade in self.open_trades[:]:  # Copy list to avoid modification during iteration
            if trade.symbol not in price_data:
                continue

            df = price_data[trade.symbol]

            # Get current price using nearest available date (handles holidays/weekends)
            available = df.index[df.index <= date]
            if available.empty:
                continue
            current_price = df.loc[available[-1], 'close']

            # 1. Hard stop loss
            if current_price <= trade.stop_price:
                self.exit_trade(trade, date, trade.stop_price, 'STOP_LOSS')
                continue

            # 2. Chandelier trailing stop: highest close since entry − 3 × ATR
            entry_dt = pd.to_datetime(trade.entry_date)
            since_entry = df.loc[(df.index >= entry_dt) & (df.index <= date)]
            if not since_entry.empty:
                highest_close = since_entry['close'].max()
                current_atr   = df.loc[available[-1], 'atr']
                if not pd.isna(current_atr) and current_atr > 0:
                    chandelier_stop = highest_close - (3 * current_atr)
                    # Only raise the trailing stop (never lower it)
                    effective_stop = max(chandelier_stop, trade.stop_price)
                    if current_price <= effective_stop and chandelier_stop > trade.stop_price:
                        self.exit_trade(trade, date, current_price, 'TRAILING_STOP')
                        continue

            # 3. Profit Target 1
            if current_price >= trade.target_1_price:
                self.exit_trade(trade, date, current_price, 'PROFIT_TARGET_1')
                continue


    def _mark_to_market_value(
        self,
        trade: Trade,
        date: pd.Timestamp,
        price_data: Optional[Dict[str, pd.DataFrame]]
    ) -> float:
        """
        Current market value of an open position.

        Uses the latest available close on/before `date`. Falls back to the
        entry value (position_value) only if no price is available, so the
        equity curve never silently freezes.
        """
        if price_data and trade.symbol in price_data:
            df = price_data[trade.symbol]
            available = df.index[df.index <= date]
            if not available.empty:
                current_price = df.loc[available[-1], 'close']
                if not pd.isna(current_price):
                    return trade.shares * current_price
        return trade.position_value

    def update_equity_curve(
        self,
        date: pd.Timestamp,
        price_data: Optional[Dict[str, pd.DataFrame]] = None
    ):
        """
        Update equity curve with current portfolio value.

        Open positions are MARKED TO MARKET at the latest available close so the
        equity curve reflects unrealised P&L day by day. Without this, Sharpe,
        Sortino and max-drawdown are all computed on a near-flat curve and are
        meaningless. `price_data` should be the same dict used for exits.

        Args:
            date: Current date
            price_data: symbol -> OHLCV DataFrame, for marking positions to market
        """
        # Mark-to-market value of open positions
        open_value = sum(
            self._mark_to_market_value(trade, date, price_data)
            for trade in self.open_trades
        )

        total_equity = self.current_capital + open_value

        # Hard invariant: cash must never go negative (no implicit leverage).
        assert self.current_capital >= -1e-6, (
            f"Negative cash on {date.date()}: ${self.current_capital:,.2f} — "
            f"cash constraint violated (implicit leverage)."
        )

        self.equity_curve.append({
            'date': date,
            'equity': total_equity,
            'cash': self.current_capital,
            'positions_value': open_value,
            'open_positions': len(self.open_trades)
        })


    def fetch_benchmark_data(self, symbol: str = 'SPY') -> Optional[pd.DataFrame]:
        """
        Fetch benchmark data for comparison.

        Args:
            symbol: Benchmark ticker (default SPY)

        Returns:
            DataFrame with benchmark data
        """
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(start=self.start_date, end=self.end_date)

            if df.empty:
                return None

            df.columns = [col.lower() for col in df.columns]
            return df

        except Exception as e:
            print(f"Warning: Could not fetch benchmark {symbol}: {e}")
            return None


    def calculate_benchmark_return(self, benchmark_symbol: str = 'SPY') -> Tuple[float, float]:
        """
        Calculate buy-and-hold benchmark return.

        Args:
            benchmark_symbol: Benchmark ticker

        Returns:
            Tuple of (total_return_pct, cagr)
        """
        # Use pre-fetched SPY if available, otherwise fetch the requested symbol
        if benchmark_symbol == 'SPY' and self._spy_data is not None:
            data = self._spy_data
        else:
            data = self.fetch_benchmark_data(benchmark_symbol)

        if data is None:
            return 0.0, 0.0

        # Clip to the actual backtest window
        window = data[(data.index >= self.start_date) & (data.index <= self.end_date)]
        if window.empty:
            return 0.0, 0.0

        start_price = window['close'].iloc[0]
        end_price   = window['close'].iloc[-1]

        total_return = ((end_price - start_price) / start_price) * 100
        years = (self.end_date - self.start_date).days / 365.25
        cagr  = ((end_price / start_price) ** (1 / years) - 1) * 100

        return round(total_return, 2), round(cagr, 2)


    def calculate_metrics(self) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Returns:
            PerformanceMetrics object
        """
        if not self.closed_trades:
            # Return empty metrics
            return PerformanceMetrics(
                total_return_pct=0, total_return_dollars=0, cagr=0,
                max_drawdown_pct=0, max_drawdown_dollars=0,
                sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
                avg_win_pct=0, avg_loss_pct=0, avg_win_dollars=0, avg_loss_dollars=0,
                largest_win_pct=0, largest_loss_pct=0, profit_factor=0,
                avg_r_multiple=0, expectancy=0,
                avg_holding_days=0, max_positions_held=0, avg_position_size_pct=0,
                exposure_pct=0, turnover=0,
                max_consecutive_losses=0, recovery_days=0
            )

        # Convert equity curve to DataFrame
        eq_df = pd.DataFrame(self.equity_curve)
        eq_df.set_index('date', inplace=True)

        # Total return
        final_equity = eq_df['equity'].iloc[-1]
        total_return_dollars = final_equity - self.initial_capital
        total_return_pct = (total_return_dollars / self.initial_capital) * 100

        # CAGR
        years = (self.end_date - self.start_date).days / 365.25
        cagr = ((final_equity / self.initial_capital) ** (1 / years) - 1) * 100

        # Max drawdown — measured against the running peak at each point in
        # time (standard definition), not the global peak. Dividing by the
        # global peak understates the worst drawdown.
        rolling_max = eq_df['equity'].expanding().max()
        drawdown = eq_df['equity'] - rolling_max
        max_drawdown_dollars = drawdown.min()
        drawdown_pct_series = drawdown / rolling_max
        max_drawdown_pct = drawdown_pct_series.min() * 100

        # Trade statistics
        wins = [t for t in self.closed_trades if t.pnl_dollars > 0]
        losses = [t for t in self.closed_trades if t.pnl_dollars <= 0]

        total_trades = len(self.closed_trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # P&L statistics
        avg_win_pct = np.mean([t.pnl_percent for t in wins]) if wins else 0
        avg_loss_pct = np.mean([t.pnl_percent for t in losses]) if losses else 0
        avg_win_dollars = np.mean([t.pnl_dollars for t in wins]) if wins else 0
        avg_loss_dollars = np.mean([t.pnl_dollars for t in losses]) if losses else 0

        all_pnl_pct = [t.pnl_percent for t in self.closed_trades]
        largest_win_pct = max(all_pnl_pct) if all_pnl_pct else 0
        largest_loss_pct = min(all_pnl_pct) if all_pnl_pct else 0

        total_wins = sum([t.pnl_dollars for t in wins])
        total_losses = abs(sum([t.pnl_dollars for t in losses]))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        # R-multiple statistics
        r_multiples = [t.r_multiple for t in self.closed_trades]
        avg_r_multiple = np.mean(r_multiples) if r_multiples else 0
        expectancy = (win_rate / 100 * avg_win_pct) + ((100 - win_rate) / 100 * avg_loss_pct)

        # Sharpe ratio
        daily_returns = eq_df['equity'].pct_change().dropna()
        excess_returns = daily_returns - (self.risk_free_rate / 100 / 252)  # Daily risk-free rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0

        # Sortino ratio (downside deviation)
        downside_returns = excess_returns[excess_returns < 0]
        sortino_ratio = (excess_returns.mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

        # Calmar ratio = CAGR / |max drawdown| (risk-adjusted return that the
        # plan flags as the key bake-off metric)
        calmar_ratio = (cagr / abs(max_drawdown_pct)) if max_drawdown_pct != 0 else 0

        # Exposure = fraction of trading days with at least one open position
        exposure_pct = (eq_df['open_positions'] > 0).mean() * 100

        # Turnover = total traded notional / initial capital (entries + exits)
        traded_notional = sum(t.position_value for t in self.closed_trades)
        traded_notional += sum(
            (t.shares * t.exit_price) for t in self.closed_trades
            if t.exit_price is not None
        )
        turnover = traded_notional / self.initial_capital if self.initial_capital > 0 else 0

        # Position statistics
        holding_days = [t.holding_days for t in self.closed_trades if t.holding_days]
        avg_holding_days = np.mean(holding_days) if holding_days else 0

        max_positions_held = eq_df['open_positions'].max()

        position_sizes = [t.position_value / self.initial_capital * 100 for t in self.closed_trades]
        avg_position_size_pct = np.mean(position_sizes) if position_sizes else 0

        # Max consecutive losses
        max_consecutive = 0
        current_consecutive = 0
        for trade in self.closed_trades:
            if trade.pnl_dollars <= 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        # Recovery days (time from max drawdown to recovery)
        recovery_days = 0
        if max_drawdown_dollars < 0:
            drawdown_idx = drawdown.idxmin()
            recovery_eq = eq_df.loc[drawdown_idx:, 'equity']
            recovered = recovery_eq[recovery_eq >= rolling_max.loc[drawdown_idx]]
            if len(recovered) > 0:
                recovery_days = (recovered.index[0] - drawdown_idx).days

        return PerformanceMetrics(
            total_return_pct=round(total_return_pct, 2),
            total_return_dollars=round(total_return_dollars, 2),
            cagr=round(cagr, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            max_drawdown_dollars=round(max_drawdown_dollars, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            calmar_ratio=round(calmar_ratio, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            avg_win_pct=round(avg_win_pct, 2),
            avg_loss_pct=round(avg_loss_pct, 2),
            avg_win_dollars=round(avg_win_dollars, 2),
            avg_loss_dollars=round(avg_loss_dollars, 2),
            largest_win_pct=round(largest_win_pct, 2),
            largest_loss_pct=round(largest_loss_pct, 2),
            profit_factor=round(profit_factor, 2),
            avg_r_multiple=round(avg_r_multiple, 2),
            expectancy=round(expectancy, 2),
            avg_holding_days=round(avg_holding_days, 1),
            max_positions_held=int(max_positions_held),
            avg_position_size_pct=round(avg_position_size_pct, 2),
            exposure_pct=round(exposure_pct, 2),
            turnover=round(turnover, 2),
            max_consecutive_losses=max_consecutive,
            recovery_days=recovery_days
        )


    def save_results(self, system_name: str, output_dir: str = 'backtesting/results'):
        """
        Save backtest results to files.

        Args:
            system_name: Name of trading system
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save trades
        if self.closed_trades:
            trades_df = pd.DataFrame([asdict(t) for t in self.closed_trades])
            trades_file = output_path / f"{system_name}_{timestamp}_trades.csv"
            trades_df.to_csv(trades_file, index=False)
            print(f"\nTrades saved to {trades_file}")

        # Save equity curve
        if self.equity_curve:
            equity_df = pd.DataFrame(self.equity_curve)
            equity_file = output_path / f"{system_name}_{timestamp}_equity.csv"
            equity_df.to_csv(equity_file, index=False)
            print(f"Equity curve saved to {equity_file}")

        # Save metrics
        metrics = self.calculate_metrics()
        metrics_file = output_path / f"{system_name}_{timestamp}_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        print(f"Metrics saved to {metrics_file}")


    def append_scorecard(
        self,
        strategy: str,
        universe: str,
        period: str,
        metrics: Optional[PerformanceMetrics] = None,
        benchmark_cagr: float = 0.0,
        scorecard_path: str = 'results/scorecard.csv',
    ):
        """
        Append one standardized row to the shared scorecard.

        This is the single comparable record every strategy/universe/period run
        emits, so the Phase 2 bake-off can rank candidates fairly. One row per
        run; the file accumulates across runs.
        """
        if metrics is None:
            metrics = self.calculate_metrics()

        row = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'strategy': strategy,
            'universe': universe,
            'period': period,
            'cagr': metrics.cagr,
            'benchmark_cagr': round(benchmark_cagr, 2),
            'alpha': round(metrics.cagr - benchmark_cagr, 2),
            'sharpe': metrics.sharpe_ratio,
            'sortino': metrics.sortino_ratio,
            'calmar': metrics.calmar_ratio,
            'max_drawdown_pct': metrics.max_drawdown_pct,
            'win_rate': metrics.win_rate,
            'avg_win_pct': metrics.avg_win_pct,
            'avg_loss_pct': metrics.avg_loss_pct,
            'profit_factor': metrics.profit_factor,
            'avg_r_multiple': metrics.avg_r_multiple,
            'exposure_pct': metrics.exposure_pct,
            'turnover': metrics.turnover,
            'total_trades': metrics.total_trades,
        }

        path = Path(scorecard_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        new_df = pd.DataFrame([row])
        if path.exists():
            existing = pd.read_csv(path)
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
        combined.to_csv(path, index=False)
        print(f"Scorecard row appended to {path}")
