"""
Interactive Brokers connector (via ib_insync) — multi-system edition.

Differences from the single-system live/ib_connector.py:
  * Every order is tagged with an `order_ref` (IB orderRef) so fills can be
    attributed to a specific system, even when two systems hold the same
    symbol on one paper account.
  * Adds order-status / fill-price queries so each system reconciles against
    ITS OWN orders rather than the net account position (which would be the
    SUM across systems under the full-equity capital model).

Install:  pip install ib_insync
Requires: TWS or IB Gateway running with the API enabled on the configured port.
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)

try:
    from ib_insync import IB, Stock, MarketOrder, StopOrder
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    log.warning("ib_insync not installed — run: pip install ib_insync")


class IBConnector:
    """Thin wrapper around ib_insync.IB with per-order tagging."""

    def __init__(self, host: str, port: int, client_id: int):
        if not IB_AVAILABLE:
            raise RuntimeError("ib_insync is not installed. Run: pip install ib_insync")
        self.host = host
        self.port = port
        self.client_id = client_id
        self._ib: Optional["IB"] = None

    # ── Connection ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        self._ib = IB()
        try:
            self._ib.connect(self.host, self.port, clientId=self.client_id,
                             timeout=15, readonly=False)
            log.info(f"Connected to IB on {self.host}:{self.port} (clientId={self.client_id})")
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

    def sleep(self, seconds: float):
        if self._ib:
            self._ib.sleep(seconds)

    # ── Account ───────────────────────────────────────────────────────────

    def get_account_value(self) -> float:
        """Net liquidation value of the account (USD)."""
        for av in self._ib.accountValues():
            if av.tag == 'NetLiquidation' and av.currency == 'BASE':
                return float(av.value)
        for av in self._ib.accountValues():
            if av.tag == 'NetLiquidation':
                return float(av.value)
        raise RuntimeError("Could not retrieve NetLiquidation from IB")

    def get_positions(self) -> dict:
        """
        Net equity positions as {symbol: shares}. Under full-equity capital
        model this is the SUM across systems — use only for sanity logging,
        not per-system reconciliation.
        """
        positions = {}
        for pos in self._ib.positions():
            if pos.contract.secType == 'STK' and pos.position != 0:
                positions[pos.contract.symbol] = int(pos.position)
        return positions

    # ── Order status / fills (per-system reconciliation) ──────────────────

    def _trade_for_order(self, order_id: int):
        for t in self._ib.trades():
            if t.order.orderId == order_id:
                return t
        return None

    def get_order_status(self, order_id: int) -> Optional[str]:
        """
        Return IB order status for an orderId:
        'PendingSubmit' | 'Submitted' | 'Filled' | 'Cancelled' | 'Inactive' | ...
        None if the order is unknown to this session.
        """
        self._ib.reqAllOpenOrders()
        self._ib.sleep(0.5)
        trade = self._trade_for_order(order_id)
        if trade is None:
            return None
        return trade.orderStatus.status

    def get_fill(self, order_id: int) -> Optional[dict]:
        """
        Return {'shares': int, 'avg_price': float, 'status': str} for a filled
        order, or None if not yet filled / unknown.
        """
        trade = self._trade_for_order(order_id)
        if trade is None:
            return None
        st = trade.orderStatus
        if st.status == 'Filled' and st.filled:
            return {
                'shares': int(st.filled),
                'avg_price': float(st.avgFillPrice or 0.0),
                'status': st.status,
            }
        return None

    # ── Orders (all tagged with order_ref) ────────────────────────────────

    def _qualify_contract(self, symbol: str):
        contract = Stock(symbol, 'SMART', 'USD')
        self._ib.qualifyContracts(contract)
        return contract

    def place_entry_order(self, symbol: str, shares: int, order_ref: str) -> Optional[int]:
        """Market-On-Open BUY for the next session, tagged with order_ref."""
        try:
            contract = self._qualify_contract(symbol)
            order = MarketOrder('BUY', shares)
            order.tif = 'OPG'              # On the Open
            order.orderRef = order_ref     # system attribution tag
            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)
            log.info(f"[{order_ref}] Entry MOO: BUY {shares} {symbol}  orderId={trade.order.orderId}")
            return trade.order.orderId
        except Exception as e:
            log.error(f"[{order_ref}] Failed entry order for {symbol}: {e}")
            return None

    def place_stop_order(self, symbol: str, shares: int, stop_price: float,
                         order_ref: str) -> Optional[int]:
        """GTC stop-sell (protects even if the script is offline), tagged."""
        try:
            contract = self._qualify_contract(symbol)
            order = StopOrder('SELL', shares, round(stop_price, 2))
            order.tif = 'GTC'
            order.orderRef = order_ref
            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)
            log.info(f"[{order_ref}] Stop GTC: SELL {shares} {symbol} @ {stop_price:.2f}  "
                     f"orderId={trade.order.orderId}")
            return trade.order.orderId
        except Exception as e:
            log.error(f"[{order_ref}] Failed stop order for {symbol}: {e}")
            return None

    def update_stop_order(self, order_id: int, symbol: str, shares: int,
                          new_stop: float, order_ref: str = '') -> bool:
        """Modify an existing GTC stop to a higher price (same orderId = modify)."""
        try:
            open_trades = {t.order.orderId: t for t in self._ib.openTrades()}
            if order_id not in open_trades:
                log.warning(f"[{order_ref}] Stop {order_id} for {symbol} not open — may have filled")
                return False
            trade = open_trades[order_id]
            trade.order.auxPrice = round(new_stop, 2)
            self._ib.placeOrder(trade.contract, trade.order)
            self._ib.sleep(0.5)
            log.info(f"[{order_ref}] Stop updated: {symbol} orderId={order_id} -> {new_stop:.2f}")
            return True
        except Exception as e:
            log.error(f"[{order_ref}] Failed to update stop {order_id} for {symbol}: {e}")
            return False

    def cancel_order(self, order_id: int, symbol: str = '', order_ref: str = '') -> bool:
        try:
            open_trades = {t.order.orderId: t for t in self._ib.openTrades()}
            if order_id not in open_trades:
                log.info(f"[{order_ref}] Order {order_id} ({symbol}) not open — already filled/cancelled")
                return True
            self._ib.cancelOrder(open_trades[order_id].order)
            self._ib.sleep(0.5)
            log.info(f"[{order_ref}] Cancelled order {order_id} ({symbol})")
            return True
        except Exception as e:
            log.error(f"[{order_ref}] Failed to cancel order {order_id}: {e}")
            return False

    def place_market_sell(self, symbol: str, shares: int, order_ref: str) -> Optional[int]:
        """Immediate market SELL (exit signal), tagged."""
        try:
            contract = self._qualify_contract(symbol)
            order = MarketOrder('SELL', shares)
            order.orderRef = order_ref
            trade = self._ib.placeOrder(contract, order)
            self._ib.sleep(1)
            log.info(f"[{order_ref}] Market SELL: {shares} {symbol}  orderId={trade.order.orderId}")
            return trade.order.orderId
        except Exception as e:
            log.error(f"[{order_ref}] Failed sell order for {symbol}: {e}")
            return None
