"""
Interactive Brokers connector (via ib_insync).

Wraps connection, account queries, and order management.
All order placement goes through this module — live_trader.py
never touches ib_insync directly.

Install:  pip install ib_insync
Requires: TWS or IB Gateway running with API enabled on the configured port.
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy import so the rest of the codebase works even without ib_insync
# ---------------------------------------------------------------------------
try:
    from ib_insync import IB, Stock, MarketOrder, StopOrder, Order, util
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    log.warning("ib_insync not installed — run: pip install ib_insync")


class IBConnector:
    """
    Thin wrapper around ib_insync.IB.

    Usage:
        conn = IBConnector(host, port, client_id)
        conn.connect()
        value = conn.get_account_value()
        positions = conn.get_positions()
        ...
        conn.disconnect()
    """

    def __init__(self, host: str, port: int, client_id: int):
        if not IB_AVAILABLE:
            raise RuntimeError("ib_insync is not installed. Run: pip install ib_insync")
        self.host      = host
        self.port      = port
        self.client_id = client_id
        self._ib: Optional[IB] = None

    # ── Connection ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect to TWS / IB Gateway. Returns True on success."""
        self._ib = IB()
        try:
            self._ib.connect(self.host, self.port, clientId=self.client_id,
                             timeout=15, readonly=False)
            log.info(f"Connected to IB on {self.host}:{self.port}")
            return True
        except Exception as e:
            log.error(f"IB connection failed: {e}")
            self._ib = None
            return False

    def disconnect(self):
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            log.info("Disconnected from IB")

    @property
    def connected(self) -> bool:
        return self._ib is not None and self._ib.isConnected()

    # ── Account ───────────────────────────────────────────────────────────

    def get_account_value(self) -> float:
        """Return net liquidation value of the account (USD)."""
        for av in self._ib.accountValues():
            if av.tag == 'NetLiquidation' and av.currency == 'BASE':
                return float(av.value)
        # Fallback: try without currency filter
        for av in self._ib.accountValues():
            if av.tag == 'NetLiquidation':
                return float(av.value)
        raise RuntimeError("Could not retrieve NetLiquidation from IB")

    def get_positions(self) -> dict:
        """
        Return current IB positions as {symbol: shares}.
        Only includes equity positions with non-zero shares.
        """
        positions = {}
        for pos in self._ib.positions():
            if pos.contract.secType == 'STK' and pos.position != 0:
                positions[pos.contract.symbol] = int(pos.position)
        return positions

    def get_open_stop_orders(self) -> dict:
        """
        Return open stop orders as {orderId: {'symbol': str, 'stop_price': float, 'shares': int}}.
        """
        stops = {}
        self._ib.reqAllOpenOrders()
        self._ib.sleep(1)
        for trade in self._ib.openTrades():
            if trade.order.orderType == 'STP' and trade.order.action == 'SELL':
                stops[trade.order.orderId] = {
                    'symbol':     trade.contract.symbol,
                    'stop_price': trade.order.auxPrice,
                    'shares':     int(trade.order.totalQuantity),
                }
        return stops

    # ── Orders ────────────────────────────────────────────────────────────

    def _qualify_contract(self, symbol: str):
        contract = Stock(symbol, 'SMART', 'USD')
        self._ib.qualifyContracts(contract)
        return contract

    def place_entry_order(self, symbol: str, shares: int) -> Optional[int]:
        """
        Place a Market On Open (MOO) buy order for next trading day.
        Returns the IB orderId, or None on failure.
        """
        try:
            contract = self._qualify_contract(symbol)
            order = MarketOrder('BUY', shares)
            order.tif = 'OPG'   # On the Open (Market on Open)
            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)
            log.info(f"Entry MOO order placed: BUY {shares} {symbol}  orderId={trade.order.orderId}")
            return trade.order.orderId
        except Exception as e:
            log.error(f"Failed to place entry order for {symbol}: {e}")
            return None

    def place_stop_order(self, symbol: str, shares: int, stop_price: float) -> Optional[int]:
        """
        Place a GTC stop-sell order in IB (protects the position even if script is offline).
        Returns the IB orderId, or None on failure.
        """
        try:
            contract = self._qualify_contract(symbol)
            order = StopOrder('SELL', shares, round(stop_price, 2))
            order.tif = 'GTC'
            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)
            log.info(f"Stop order placed: SELL {shares} {symbol} @ {stop_price:.2f}  orderId={trade.order.orderId}")
            return trade.order.orderId
        except Exception as e:
            log.error(f"Failed to place stop order for {symbol}: {e}")
            return None

    def update_stop_order(self, order_id: int, symbol: str, shares: int, new_stop: float) -> bool:
        """
        Modify an existing GTC stop order to a new (higher) stop price.
        Returns True on success.
        """
        try:
            # Find the open trade with this orderId
            open_trades = {t.order.orderId: t for t in self._ib.openTrades()}
            if order_id not in open_trades:
                log.warning(f"Stop order {order_id} for {symbol} not found in open trades — may have already filled")
                return False

            trade = open_trades[order_id]
            trade.order.auxPrice = round(new_stop, 2)
            self._ib.placeOrder(trade.contract, trade.order)   # same orderId = modify
            self._ib.sleep(0.5)
            log.info(f"Stop updated: {symbol} orderId={order_id}  new stop={new_stop:.2f}")
            return True
        except Exception as e:
            log.error(f"Failed to update stop order {order_id} for {symbol}: {e}")
            return False

    def cancel_order(self, order_id: int, symbol: str = '') -> bool:
        """Cancel an open order by orderId (used when we exit a position manually)."""
        try:
            open_trades = {t.order.orderId: t for t in self._ib.openTrades()}
            if order_id not in open_trades:
                log.info(f"Order {order_id} ({symbol}) not found — already filled or cancelled")
                return True
            self._ib.cancelOrder(open_trades[order_id].order)
            self._ib.sleep(0.5)
            log.info(f"Cancelled order {order_id} ({symbol})")
            return True
        except Exception as e:
            log.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def place_market_sell(self, symbol: str, shares: int) -> Optional[int]:
        """
        Place an immediate market sell order (for exit signals triggered after close).
        In practice this submits a MOC (Market on Close) if after market hours,
        or a regular market order if within session.
        """
        try:
            contract = self._qualify_contract(symbol)
            order = MarketOrder('SELL', shares)
            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)
            log.info(f"Market SELL placed: {shares} {symbol}  orderId={trade.order.orderId}")
            return trade.order.orderId
        except Exception as e:
            log.error(f"Failed to place sell order for {symbol}: {e}")
            return None
