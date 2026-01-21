# execution/slippage_estimator.py — SCALPER ETERNAL — SLIPPAGE ORACLE — 2026 v1.0
# Pre-entry slippage estimation using order book data
# Features:
# - Market impact calculation
# - Effective price estimation
# - Slippage prediction before entry
# - Liquidity depth analysis

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from utils.logging import log_entry


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
class SlippageEstimatorConfig:
    """Slippage estimator configuration."""
    enabled: bool = True
    orderbook_depth: int = 20
    default_slippage_pct: float = 0.001  # 0.1% default assumption
    max_acceptable_slippage_pct: float = 0.006  # 0.6%


@dataclass
class SlippageEstimate:
    """Result of slippage estimation."""
    symbol: str
    side: str  # "buy" or "sell"
    amount_usdt: float
    mid_price: float
    effective_price: float
    slippage_pct: float
    market_impact_pct: float
    available_liquidity_usdt: float
    depth_levels_used: int
    is_acceptable: bool
    reason: str


class SlippageEstimator:
    """
    SLIPPAGE ORACLE — Estimate slippage before placing market orders.

    Uses order book depth to calculate:
    - Effective fill price for a given order size
    - Expected slippage percentage
    - Market impact
    - Available liquidity at each price level
    """

    def __init__(self, config: Optional[SlippageEstimatorConfig] = None):
        self.config = config or SlippageEstimatorConfig()

    def estimate_slippage(
        self,
        orderbook: Dict[str, Any],
        side: str,
        amount_usdt: float,
        symbol: str = "",
    ) -> SlippageEstimate:
        """
        Estimate slippage for a market order.

        Args:
            orderbook: Dict with "bids" and "asks" keys, each containing [[price, amount], ...]
            side: "buy" or "sell" (from trader's perspective)
            amount_usdt: Order size in USDT
            symbol: Symbol for logging

        Returns:
            SlippageEstimate with all calculated values
        """
        k = _symkey(symbol) if symbol else "UNKNOWN"
        side_lower = str(side).lower().strip()

        # Get relevant side of the book
        if side_lower in ("buy", "long"):
            levels = orderbook.get("asks", [])  # Buying hits asks
            side_label = "buy"
        else:
            levels = orderbook.get("bids", [])  # Selling hits bids
            side_label = "sell"

        # Calculate mid price
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])

        best_bid = _safe_float(bids[0][0], 0.0) if bids else 0.0
        best_ask = _safe_float(asks[0][0], 0.0) if asks else 0.0

        if best_bid <= 0 or best_ask <= 0:
            return SlippageEstimate(
                symbol=k,
                side=side_label,
                amount_usdt=amount_usdt,
                mid_price=0.0,
                effective_price=0.0,
                slippage_pct=self.config.default_slippage_pct,
                market_impact_pct=0.0,
                available_liquidity_usdt=0.0,
                depth_levels_used=0,
                is_acceptable=False,
                reason="Invalid orderbook: no bid/ask",
            )

        mid_price = (best_bid + best_ask) / 2.0

        if not levels:
            return SlippageEstimate(
                symbol=k,
                side=side_label,
                amount_usdt=amount_usdt,
                mid_price=mid_price,
                effective_price=mid_price,
                slippage_pct=self.config.default_slippage_pct,
                market_impact_pct=0.0,
                available_liquidity_usdt=0.0,
                depth_levels_used=0,
                is_acceptable=False,
                reason="Empty orderbook levels",
            )

        # Walk through order book to fill the order
        remaining_usdt = amount_usdt
        total_base_filled = 0.0
        total_cost = 0.0
        levels_used = 0

        for level in levels[:self.config.orderbook_depth]:
            if remaining_usdt <= 0:
                break

            price = _safe_float(level[0], 0.0)
            amount = _safe_float(level[1], 0.0)

            if price <= 0 or amount <= 0:
                continue

            level_value_usdt = price * amount

            if level_value_usdt >= remaining_usdt:
                # This level can fill the rest
                base_to_fill = remaining_usdt / price
                total_base_filled += base_to_fill
                total_cost += remaining_usdt
                remaining_usdt = 0
            else:
                # Take entire level
                total_base_filled += amount
                total_cost += level_value_usdt
                remaining_usdt -= level_value_usdt

            levels_used += 1

        # Calculate available liquidity
        available_liquidity = sum(
            _safe_float(l[0], 0.0) * _safe_float(l[1], 0.0)
            for l in levels[:self.config.orderbook_depth]
        )

        # Calculate effective price and slippage
        if total_base_filled <= 0:
            return SlippageEstimate(
                symbol=k,
                side=side_label,
                amount_usdt=amount_usdt,
                mid_price=mid_price,
                effective_price=mid_price,
                slippage_pct=self.config.default_slippage_pct,
                market_impact_pct=0.0,
                available_liquidity_usdt=available_liquidity,
                depth_levels_used=levels_used,
                is_acceptable=False,
                reason="Could not fill any amount",
            )

        effective_price = total_cost / total_base_filled

        # Calculate slippage percentage
        if side_label == "buy":
            slippage_pct = (effective_price - mid_price) / mid_price if mid_price > 0 else 0.0
        else:
            slippage_pct = (mid_price - effective_price) / mid_price if mid_price > 0 else 0.0

        # Market impact: how much the price moves from best to worst filled level
        best_price = _safe_float(levels[0][0], 0.0) if levels else 0.0
        if best_price > 0:
            market_impact_pct = abs(effective_price - best_price) / best_price
        else:
            market_impact_pct = 0.0

        # Check if we could fill the entire order
        if remaining_usdt > 0:
            filled_pct = (amount_usdt - remaining_usdt) / amount_usdt
            reason = f"Insufficient liquidity: only {filled_pct:.1%} fillable"
            is_acceptable = False
        elif slippage_pct > self.config.max_acceptable_slippage_pct:
            reason = f"Slippage {slippage_pct:.3%} > max {self.config.max_acceptable_slippage_pct:.3%}"
            is_acceptable = False
        else:
            reason = "OK"
            is_acceptable = True

        return SlippageEstimate(
            symbol=k,
            side=side_label,
            amount_usdt=amount_usdt,
            mid_price=mid_price,
            effective_price=effective_price,
            slippage_pct=slippage_pct,
            market_impact_pct=market_impact_pct,
            available_liquidity_usdt=available_liquidity,
            depth_levels_used=levels_used,
            is_acceptable=is_acceptable,
            reason=reason,
        )

    def get_effective_price(
        self,
        orderbook: Dict[str, Any],
        side: str,
        amount_usdt: float,
    ) -> float:
        """
        Get the effective fill price for a market order.

        Args:
            orderbook: Order book data
            side: "buy" or "sell"
            amount_usdt: Order size in USDT

        Returns:
            Effective fill price
        """
        estimate = self.estimate_slippage(orderbook, side, amount_usdt)
        return estimate.effective_price

    def should_enter_at_market(
        self,
        orderbook: Dict[str, Any],
        side: str,
        amount_usdt: float,
        threshold: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Determine if market entry is acceptable.

        Args:
            orderbook: Order book data
            side: "buy" or "sell"
            amount_usdt: Order size in USDT
            threshold: Optional slippage threshold override

        Returns:
            (should_enter, reason)
        """
        estimate = self.estimate_slippage(orderbook, side, amount_usdt)

        max_slip = threshold if threshold is not None else self.config.max_acceptable_slippage_pct

        if estimate.slippage_pct > max_slip:
            return False, f"Slippage {estimate.slippage_pct:.3%} > {max_slip:.3%}"

        if not estimate.is_acceptable:
            return False, estimate.reason

        return True, "OK"

    def calculate_optimal_order_size(
        self,
        orderbook: Dict[str, Any],
        side: str,
        max_slippage_pct: float,
        max_amount_usdt: float,
    ) -> float:
        """
        Calculate the maximum order size that stays within slippage limits.

        Args:
            orderbook: Order book data
            side: "buy" or "sell"
            max_slippage_pct: Maximum acceptable slippage
            max_amount_usdt: Maximum order size to consider

        Returns:
            Optimal order size in USDT
        """
        # Binary search for optimal size
        low = 0.0
        high = max_amount_usdt
        best_size = 0.0

        for _ in range(20):  # 20 iterations should be enough precision
            mid = (low + high) / 2.0

            estimate = self.estimate_slippage(orderbook, side, mid)

            if estimate.slippage_pct <= max_slippage_pct and estimate.is_acceptable:
                best_size = mid
                low = mid
            else:
                high = mid

            if high - low < 1.0:  # $1 precision
                break

        return best_size


# Global singleton
_estimator: Optional[SlippageEstimator] = None


def get_slippage_estimator() -> SlippageEstimator:
    """Get the global slippage estimator instance."""
    global _estimator
    if _estimator is None:
        _estimator = SlippageEstimator()
    return _estimator


def estimate_slippage(
    orderbook: Dict[str, Any],
    side: str,
    amount_usdt: float,
    symbol: str = "",
) -> float:
    """
    Convenience function to estimate slippage.

    Returns:
        Estimated slippage as a percentage (e.g., 0.001 = 0.1%)
    """
    estimator = get_slippage_estimator()
    estimate = estimator.estimate_slippage(orderbook, side, amount_usdt, symbol)
    return estimate.slippage_pct


async def check_slippage_before_entry(
    bot,
    symbol: str,
    side: str,
    notional_usdt: float,
) -> Tuple[bool, float, str]:
    """
    Check slippage before placing an entry order.
    Fetches order book and estimates slippage.

    Args:
        bot: Bot instance with exchange access
        symbol: Trading symbol
        side: "long" or "short"
        notional_usdt: Order size in USDT

    Returns:
        (should_enter, estimated_slippage, reason)
    """
    cfg = getattr(bot, "cfg", None)

    # Check if pre-entry slippage check is enabled
    if cfg is not None:
        enabled = getattr(cfg, "SLIPPAGE_PRE_CHECK_ENABLED", True)
        if not enabled:
            return True, 0.0, "Slippage check disabled"

    ex = getattr(bot, "ex", None)
    if ex is None:
        return True, 0.0, "No exchange available"

    try:
        # Fetch order book
        depth = getattr(cfg, "SLIPPAGE_ORDERBOOK_DEPTH", 20) if cfg else 20

        # Try to resolve symbol
        data = getattr(bot, "data", None)
        raw_sym = symbol
        if data is not None:
            raw_sym = getattr(data, "raw_symbol", {}).get(_symkey(symbol), symbol)

        orderbook = await ex.fetch_order_book(raw_sym, limit=depth)

        if not orderbook:
            return True, 0.0, "Could not fetch orderbook"

        # Convert side
        order_side = "buy" if str(side).lower() in ("long", "buy") else "sell"

        # Estimate slippage
        estimator = get_slippage_estimator()

        # Apply config
        if cfg is not None:
            if hasattr(cfg, "SLIPPAGE_MAX_PCT"):
                estimator.config.max_acceptable_slippage_pct = float(cfg.SLIPPAGE_MAX_PCT)

        estimate = estimator.estimate_slippage(orderbook, order_side, notional_usdt, symbol)

        log_entry.info(
            f"SLIPPAGE ESTIMATE {_symkey(symbol)} {order_side}: "
            f"slip={estimate.slippage_pct:.3%} impact={estimate.market_impact_pct:.3%} "
            f"liq=${estimate.available_liquidity_usdt:,.0f} levels={estimate.depth_levels_used}"
        )

        return estimate.is_acceptable, estimate.slippage_pct, estimate.reason

    except Exception as e:
        log_entry.warning(f"SLIPPAGE CHECK FAILED {symbol}: {e}")
        return True, 0.0, f"Check failed: {e}"
