# strategies/order_flow.py — SCALPER ETERNAL — ORDER FLOW ORACLE — 2026 v1.0
# Order book and trade flow analysis for enhanced signal quality
# Features:
# - Order book imbalance detection
# - Cumulative Volume Delta (CVD) calculation
# - Large order detection
# - Absorption detection
# - Spoofing detection (basic)

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field

from utils.logging import log_data


def _safe_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v
    except Exception:
        return default


def _symkey(sym: str) -> str:
    """Canonical symbol key."""
    s = str(sym or "").upper().strip()
    s = s.replace("/USDT:USDT", "USDT").replace("/USDT", "USDT")
    s = s.replace(":USDT", "USDT").replace(":", "")
    s = s.replace("/", "")
    if s.endswith("USDTUSDT"):
        s = s[:-4]
    return s


@dataclass
class OrderFlowConfig:
    """Order flow analysis configuration."""
    enabled: bool = True
    depth_levels: int = 10
    imbalance_threshold: float = 0.6
    cvd_window: int = 100
    large_order_threshold_usdt: float = 50000.0
    absorption_threshold: float = 0.7
    stale_threshold_sec: float = 30.0


@dataclass
class OrderFlowState:
    """State for order flow analysis per symbol."""
    # Order book state
    last_bids: List[List[float]] = field(default_factory=list)
    last_asks: List[List[float]] = field(default_factory=list)
    last_orderbook_ts: float = 0.0

    # Trade flow state
    recent_trades: deque = field(default_factory=lambda: deque(maxlen=500))
    cvd: float = 0.0
    cvd_history: deque = field(default_factory=lambda: deque(maxlen=100))

    # Large order tracking
    large_buys: deque = field(default_factory=lambda: deque(maxlen=50))
    large_sells: deque = field(default_factory=lambda: deque(maxlen=50))

    # Computed signals
    last_imbalance: float = 0.0
    last_cvd_signal: float = 0.0
    last_absorption_signal: str = ""


class OrderFlowAnalyzer:
    """
    ORDER FLOW ORACLE — Analyze order book and trade flow for trading signals.

    Signals:
    - imbalance > 0.6: Strong bid pressure (bullish)
    - imbalance < -0.6: Strong ask pressure (bearish)
    - cvd_signal > 0: Aggressive buying dominates
    - cvd_signal < 0: Aggressive selling dominates
    - absorption: "BID_ABSORPTION" or "ASK_ABSORPTION"
    """

    def __init__(self, config: Optional[OrderFlowConfig] = None):
        self.config = config or OrderFlowConfig()
        self._state: Dict[str, OrderFlowState] = {}

    def _get_state(self, symbol: str) -> OrderFlowState:
        """Get or create state for a symbol."""
        k = _symkey(symbol)
        if k not in self._state:
            self._state[k] = OrderFlowState()
        return self._state[k]

    def update_orderbook(
        self,
        symbol: str,
        bids: List[List[float]],
        asks: List[List[float]],
        timestamp: Optional[float] = None,
    ) -> None:
        """Update order book state for a symbol."""
        state = self._get_state(symbol)
        state.last_bids = list(bids) if bids else []
        state.last_asks = list(asks) if asks else []
        state.last_orderbook_ts = timestamp or time.time()

    def update_trades(self, symbol: str, trades: List[Dict]) -> None:
        """Update trade flow state for a symbol."""
        state = self._get_state(symbol)

        for trade in trades:
            # Normalize trade data
            price = _safe_float(trade.get("price"), 0.0)
            amount = _safe_float(trade.get("amount"), 0.0)
            side = str(trade.get("side", "")).lower()
            ts = _safe_float(trade.get("timestamp"), time.time() * 1000) / 1000.0

            if price <= 0 or amount <= 0:
                continue

            notional = price * amount

            # Add to recent trades
            state.recent_trades.append({
                "price": price,
                "amount": amount,
                "side": side,
                "notional": notional,
                "ts": ts,
            })

            # Update CVD (Cumulative Volume Delta)
            if side == "buy":
                state.cvd += notional
            elif side == "sell":
                state.cvd -= notional

            # Track large orders
            if notional >= self.config.large_order_threshold_usdt:
                if side == "buy":
                    state.large_buys.append({"price": price, "notional": notional, "ts": ts})
                else:
                    state.large_sells.append({"price": price, "notional": notional, "ts": ts})

        # Update CVD history
        state.cvd_history.append(state.cvd)

    def calculate_order_imbalance(
        self,
        symbol: str,
        depth_levels: Optional[int] = None,
    ) -> float:
        """
        Calculate order book imbalance.

        Returns:
            float: Imbalance ratio in range [-1, 1]
                   > 0: More bid pressure (bullish)
                   < 0: More ask pressure (bearish)
        """
        state = self._get_state(symbol)
        depth = depth_levels or self.config.depth_levels

        bids = state.last_bids[:depth]
        asks = state.last_asks[:depth]

        if not bids or not asks:
            return 0.0

        # Calculate total bid/ask volume
        bid_volume = sum(_safe_float(level[1], 0.0) for level in bids)
        ask_volume = sum(_safe_float(level[1], 0.0) for level in asks)

        total = bid_volume + ask_volume
        if total <= 0:
            return 0.0

        # Imbalance: (bid - ask) / (bid + ask)
        imbalance = (bid_volume - ask_volume) / total

        state.last_imbalance = imbalance
        return imbalance

    def calculate_weighted_imbalance(
        self,
        symbol: str,
        depth_levels: Optional[int] = None,
    ) -> float:
        """
        Calculate distance-weighted order book imbalance.
        Orders closer to mid price have more weight.
        """
        state = self._get_state(symbol)
        depth = depth_levels or self.config.depth_levels

        bids = state.last_bids[:depth]
        asks = state.last_asks[:depth]

        if not bids or not asks:
            return 0.0

        # Get mid price
        best_bid = _safe_float(bids[0][0], 0.0)
        best_ask = _safe_float(asks[0][0], 0.0)
        if best_bid <= 0 or best_ask <= 0:
            return 0.0

        mid_price = (best_bid + best_ask) / 2.0

        # Calculate weighted volumes
        bid_weighted = 0.0
        for level in bids:
            price = _safe_float(level[0], 0.0)
            volume = _safe_float(level[1], 0.0)
            if price > 0:
                distance = abs(mid_price - price) / mid_price
                weight = 1.0 / (1.0 + distance * 100)  # Decay with distance
                bid_weighted += volume * weight

        ask_weighted = 0.0
        for level in asks:
            price = _safe_float(level[0], 0.0)
            volume = _safe_float(level[1], 0.0)
            if price > 0:
                distance = abs(price - mid_price) / mid_price
                weight = 1.0 / (1.0 + distance * 100)
                ask_weighted += volume * weight

        total = bid_weighted + ask_weighted
        if total <= 0:
            return 0.0

        return (bid_weighted - ask_weighted) / total

    def calculate_cvd(self, symbol: str, window: Optional[int] = None) -> float:
        """
        Calculate Cumulative Volume Delta over a window.

        Returns:
            float: CVD value (positive = buying pressure, negative = selling pressure)
        """
        state = self._get_state(symbol)
        win = window or self.config.cvd_window

        history = list(state.cvd_history)
        if len(history) < 2:
            return 0.0

        # Get CVD change over window
        start_idx = max(0, len(history) - win)
        cvd_change = history[-1] - history[start_idx]

        return cvd_change

    def calculate_cvd_signal(self, symbol: str) -> float:
        """
        Calculate normalized CVD signal.

        Returns:
            float: Signal in range [-1, 1]
        """
        state = self._get_state(symbol)
        cvd = self.calculate_cvd(symbol)

        if len(state.cvd_history) < 10:
            return 0.0

        # Normalize by recent range
        history = list(state.cvd_history)
        cvd_range = max(history) - min(history) if history else 1.0

        if cvd_range <= 0:
            return 0.0

        normalized = cvd / cvd_range
        signal = max(-1.0, min(1.0, normalized))

        state.last_cvd_signal = signal
        return signal

    def detect_large_orders(
        self,
        symbol: str,
        lookback_sec: float = 60.0,
    ) -> Dict[str, List[Dict]]:
        """
        Detect recent large orders.

        Returns:
            Dict with "buys" and "sells" lists of large orders
        """
        state = self._get_state(symbol)
        now = time.time()
        cutoff = now - lookback_sec

        recent_buys = [o for o in state.large_buys if o["ts"] >= cutoff]
        recent_sells = [o for o in state.large_sells if o["ts"] >= cutoff]

        return {
            "buys": recent_buys,
            "sells": recent_sells,
            "buy_volume": sum(o["notional"] for o in recent_buys),
            "sell_volume": sum(o["notional"] for o in recent_sells),
        }

    def detect_absorption(self, symbol: str) -> Tuple[bool, str]:
        """
        Detect absorption patterns.
        Absorption = large orders being filled without price moving significantly.

        Returns:
            (is_absorption, type): ("BID_ABSORPTION", "ASK_ABSORPTION", or "")
        """
        state = self._get_state(symbol)

        if not state.last_bids or not state.last_asks:
            return False, ""

        # Get recent price movement
        if len(state.recent_trades) < 20:
            return False, ""

        trades = list(state.recent_trades)[-50:]

        # Calculate price range
        prices = [t["price"] for t in trades if t["price"] > 0]
        if not prices:
            return False, ""

        price_range_pct = (max(prices) - min(prices)) / min(prices) if min(prices) > 0 else 0.0

        # Calculate volume
        buy_vol = sum(t["notional"] for t in trades if t["side"] == "buy")
        sell_vol = sum(t["notional"] for t in trades if t["side"] == "sell")
        total_vol = buy_vol + sell_vol

        if total_vol <= 0:
            return False, ""

        # Absorption: High volume but low price movement
        if price_range_pct < 0.002:  # Less than 0.2% movement
            vol_ratio = buy_vol / total_vol if total_vol > 0 else 0.5

            if vol_ratio > self.config.absorption_threshold:
                state.last_absorption_signal = "BID_ABSORPTION"
                return True, "BID_ABSORPTION"
            elif vol_ratio < (1 - self.config.absorption_threshold):
                state.last_absorption_signal = "ASK_ABSORPTION"
                return True, "ASK_ABSORPTION"

        state.last_absorption_signal = ""
        return False, ""

    def get_order_flow_signal(
        self,
        symbol: str,
    ) -> Tuple[float, str]:
        """
        Get combined order flow signal.

        Returns:
            (strength, bias):
                strength: 0.0 to 1.0 signal strength
                bias: "BULLISH", "BEARISH", or "NEUTRAL"
        """
        if not self.config.enabled:
            return 0.0, "NEUTRAL"

        state = self._get_state(symbol)

        # Check if data is stale
        now = time.time()
        if state.last_orderbook_ts > 0:
            age = now - state.last_orderbook_ts
            if age > self.config.stale_threshold_sec:
                return 0.0, "NEUTRAL"

        # Calculate components
        imbalance = self.calculate_order_imbalance(symbol)
        weighted_imb = self.calculate_weighted_imbalance(symbol)
        cvd_signal = self.calculate_cvd_signal(symbol)
        is_absorb, absorb_type = self.detect_absorption(symbol)

        # Combine signals
        combined = (imbalance * 0.3) + (weighted_imb * 0.3) + (cvd_signal * 0.4)

        # Absorption modifier
        if is_absorb:
            if absorb_type == "BID_ABSORPTION":
                combined += 0.2
            elif absorb_type == "ASK_ABSORPTION":
                combined -= 0.2

        # Determine bias
        if combined > self.config.imbalance_threshold:
            bias = "BULLISH"
        elif combined < -self.config.imbalance_threshold:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        strength = min(1.0, abs(combined))

        return strength, bias

    def get_full_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get complete order flow analysis for a symbol."""
        state = self._get_state(symbol)

        imbalance = self.calculate_order_imbalance(symbol)
        weighted_imb = self.calculate_weighted_imbalance(symbol)
        cvd = self.calculate_cvd(symbol)
        cvd_signal = self.calculate_cvd_signal(symbol)
        large_orders = self.detect_large_orders(symbol)
        is_absorb, absorb_type = self.detect_absorption(symbol)
        strength, bias = self.get_order_flow_signal(symbol)

        return {
            "symbol": _symkey(symbol),
            "timestamp": time.time(),
            "orderbook_age_sec": time.time() - state.last_orderbook_ts if state.last_orderbook_ts > 0 else float("inf"),
            "imbalance": imbalance,
            "weighted_imbalance": weighted_imb,
            "cvd": cvd,
            "cvd_signal": cvd_signal,
            "large_orders": large_orders,
            "absorption": {"detected": is_absorb, "type": absorb_type},
            "signal": {"strength": strength, "bias": bias},
            "trade_count": len(state.recent_trades),
        }


# Global singleton for easy access
_analyzer: Optional[OrderFlowAnalyzer] = None


def get_order_flow_analyzer() -> OrderFlowAnalyzer:
    """Get the global order flow analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = OrderFlowAnalyzer()
    return _analyzer


def get_order_flow_signal(bot, symbol: str) -> Tuple[float, str]:
    """
    Convenience function to get order flow signal.
    Compatible with existing strategy signature.
    """
    analyzer = get_order_flow_analyzer()

    # Try to get config from bot
    cfg = getattr(bot, "cfg", None)
    if cfg is not None:
        if hasattr(cfg, "ORDER_FLOW_ENABLED"):
            analyzer.config.enabled = bool(cfg.ORDER_FLOW_ENABLED)
        if hasattr(cfg, "ORDER_FLOW_DEPTH_LEVELS"):
            analyzer.config.depth_levels = int(cfg.ORDER_FLOW_DEPTH_LEVELS)
        if hasattr(cfg, "ORDER_FLOW_IMBALANCE_THRESHOLD"):
            analyzer.config.imbalance_threshold = float(cfg.ORDER_FLOW_IMBALANCE_THRESHOLD)

    return analyzer.get_order_flow_signal(symbol)
