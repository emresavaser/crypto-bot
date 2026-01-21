# execution/time_exit.py — SCALPER ETERNAL — TIME EXIT ORACLE — 2026 v1.0
# Time-based exit enforcement for maximum holding periods
# Features:
# - Maximum holding period enforcement
# - Warning alerts before forced exit
# - Time decay factor for position sizing
# - Session-aware time limits

from __future__ import annotations

import time
from typing import Any, Optional, Tuple
from dataclasses import dataclass

from utils.logging import log_entry


def _safe_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v
    except Exception:
        return default


@dataclass
class TimeExitConfig:
    """Time exit configuration."""
    enabled: bool = True
    max_holding_minutes: float = 240.0  # 4 hours default
    warning_minutes: float = 180.0  # Warn at 3 hours
    grace_period_minutes: float = 5.0  # Grace period after warning
    use_time_decay: bool = True
    decay_start_pct: float = 0.5  # Start decay at 50% of max time


@dataclass
class TimeExitResult:
    """Result of time exit check."""
    should_exit: bool
    should_warn: bool
    reason: str
    time_held_minutes: float
    time_remaining_minutes: float
    time_decay_factor: float


def should_time_exit(
    pos: Any,
    cfg: Any,
    config: Optional[TimeExitConfig] = None,
) -> Tuple[bool, str]:
    """
    Check if a position should be time-exited.

    Args:
        pos: Position object with entry_ts attribute
        cfg: Bot configuration
        config: Optional TimeExitConfig override

    Returns:
        (should_exit, reason)
    """
    # Get config
    if config is None:
        config = TimeExitConfig()

        # Apply from bot config
        if cfg is not None:
            if hasattr(cfg, "TIME_EXIT_ENABLED"):
                config.enabled = bool(cfg.TIME_EXIT_ENABLED)
            if hasattr(cfg, "MAX_HOLDING_MINUTES"):
                config.max_holding_minutes = float(cfg.MAX_HOLDING_MINUTES)
            if hasattr(cfg, "TIME_EXIT_WARNING_MINUTES"):
                config.warning_minutes = float(cfg.TIME_EXIT_WARNING_MINUTES)

    if not config.enabled:
        return False, "Time exit disabled"

    # Get entry timestamp
    entry_ts = _safe_float(getattr(pos, "entry_ts", 0.0), 0.0)
    if entry_ts <= 0:
        return False, "No entry timestamp"

    # Calculate time held
    now = time.time()
    time_held_sec = now - entry_ts
    time_held_min = time_held_sec / 60.0

    max_min = config.max_holding_minutes

    if time_held_min >= max_min:
        return True, f"Max holding time exceeded: {time_held_min:.1f}m >= {max_min:.0f}m"

    return False, f"Time OK: {time_held_min:.1f}m / {max_min:.0f}m"


def get_time_remaining(
    pos: Any,
    cfg: Any,
    config: Optional[TimeExitConfig] = None,
) -> float:
    """
    Get remaining time before forced exit.

    Args:
        pos: Position object
        cfg: Bot configuration
        config: Optional TimeExitConfig override

    Returns:
        Remaining time in minutes (0 if should exit now)
    """
    if config is None:
        config = TimeExitConfig()
        if cfg is not None and hasattr(cfg, "MAX_HOLDING_MINUTES"):
            config.max_holding_minutes = float(cfg.MAX_HOLDING_MINUTES)

    entry_ts = _safe_float(getattr(pos, "entry_ts", 0.0), 0.0)
    if entry_ts <= 0:
        return config.max_holding_minutes

    now = time.time()
    time_held_min = (now - entry_ts) / 60.0

    remaining = config.max_holding_minutes - time_held_min
    return max(0.0, remaining)


def calculate_time_decay_factor(
    pos: Any,
    cfg: Any,
    config: Optional[TimeExitConfig] = None,
) -> float:
    """
    Calculate time decay factor for position sizing.
    Factor decreases as position approaches max holding time.

    Args:
        pos: Position object
        cfg: Bot configuration
        config: Optional TimeExitConfig override

    Returns:
        Decay factor in range [0.0, 1.0]
    """
    if config is None:
        config = TimeExitConfig()
        if cfg is not None:
            if hasattr(cfg, "MAX_HOLDING_MINUTES"):
                config.max_holding_minutes = float(cfg.MAX_HOLDING_MINUTES)
            if hasattr(cfg, "TIME_DECAY_START_PCT"):
                config.decay_start_pct = float(cfg.TIME_DECAY_START_PCT)

    if not config.use_time_decay:
        return 1.0

    entry_ts = _safe_float(getattr(pos, "entry_ts", 0.0), 0.0)
    if entry_ts <= 0:
        return 1.0

    now = time.time()
    time_held_min = (now - entry_ts) / 60.0

    max_min = config.max_holding_minutes
    decay_start_min = max_min * config.decay_start_pct

    if time_held_min <= decay_start_min:
        return 1.0

    # Linear decay from decay_start to max
    decay_duration = max_min - decay_start_min
    if decay_duration <= 0:
        return 1.0

    time_in_decay = time_held_min - decay_start_min
    decay_factor = 1.0 - (time_in_decay / decay_duration)

    return max(0.0, min(1.0, decay_factor))


def get_full_time_analysis(
    pos: Any,
    cfg: Any,
    config: Optional[TimeExitConfig] = None,
) -> TimeExitResult:
    """
    Get complete time analysis for a position.

    Args:
        pos: Position object
        cfg: Bot configuration
        config: Optional TimeExitConfig override

    Returns:
        TimeExitResult with all computed values
    """
    if config is None:
        config = TimeExitConfig()
        if cfg is not None:
            if hasattr(cfg, "TIME_EXIT_ENABLED"):
                config.enabled = bool(cfg.TIME_EXIT_ENABLED)
            if hasattr(cfg, "MAX_HOLDING_MINUTES"):
                config.max_holding_minutes = float(cfg.MAX_HOLDING_MINUTES)
            if hasattr(cfg, "TIME_EXIT_WARNING_MINUTES"):
                config.warning_minutes = float(cfg.TIME_EXIT_WARNING_MINUTES)

    entry_ts = _safe_float(getattr(pos, "entry_ts", 0.0), 0.0)

    if entry_ts <= 0 or not config.enabled:
        return TimeExitResult(
            should_exit=False,
            should_warn=False,
            reason="Time exit disabled or no entry timestamp",
            time_held_minutes=0.0,
            time_remaining_minutes=config.max_holding_minutes,
            time_decay_factor=1.0,
        )

    now = time.time()
    time_held_min = (now - entry_ts) / 60.0
    time_remaining_min = max(0.0, config.max_holding_minutes - time_held_min)
    decay_factor = calculate_time_decay_factor(pos, cfg, config)

    should_exit = time_held_min >= config.max_holding_minutes
    should_warn = time_held_min >= config.warning_minutes and not should_exit

    if should_exit:
        reason = f"MAX TIME: {time_held_min:.1f}m >= {config.max_holding_minutes:.0f}m"
    elif should_warn:
        reason = f"WARNING: {time_remaining_min:.1f}m remaining"
    else:
        reason = f"OK: {time_held_min:.1f}m / {config.max_holding_minutes:.0f}m"

    return TimeExitResult(
        should_exit=should_exit,
        should_warn=should_warn,
        reason=reason,
        time_held_minutes=time_held_min,
        time_remaining_minutes=time_remaining_min,
        time_decay_factor=decay_factor,
    )


async def check_and_execute_time_exits(bot) -> int:
    """
    Check all positions for time-based exits and execute if needed.

    Args:
        bot: Bot instance with state and exchange access

    Returns:
        Number of positions time-exited
    """
    cfg = getattr(bot, "cfg", None)

    # Check if enabled
    if cfg is not None:
        enabled = getattr(cfg, "TIME_EXIT_ENABLED", True)
        if not enabled:
            return 0

    state = getattr(bot, "state", None)
    if state is None:
        return 0

    positions = getattr(state, "positions", {})
    if not positions:
        return 0

    exits_executed = 0

    for k, pos in list(positions.items()):
        should_exit, reason = should_time_exit(pos, cfg)

        if should_exit:
            log_entry.critical(f"TIME EXIT TRIGGERED {k}: {reason}")

            # Try to execute market exit
            try:
                from execution.order_router import create_order

                side = getattr(pos, "side", "long")
                size = _safe_float(getattr(pos, "size", 0.0), 0.0)

                if size <= 0:
                    continue

                # Get raw symbol
                data = getattr(bot, "data", None)
                raw_sym = k
                if data is not None:
                    raw_sym = getattr(data, "raw_symbol", {}).get(k, k)

                # Place market close order
                close_side = "sell" if side == "long" else "buy"

                await create_order(
                    bot,
                    symbol=raw_sym,
                    type="MARKET",
                    side=close_side,
                    amount=float(size),
                    price=None,
                    params={},
                    intent_reduce_only=True,
                    retries=3,
                )

                exits_executed += 1

                # Notify
                notify = getattr(bot, "notify", None)
                if notify is not None:
                    try:
                        await notify.speak(f"TIME EXIT {k}: {reason}", "critical")
                    except Exception:
                        pass

            except Exception as e:
                log_entry.error(f"TIME EXIT FAILED {k}: {e}")

    return exits_executed


def format_time_status(pos: Any, cfg: Any) -> str:
    """Format time status for logging/display."""
    result = get_full_time_analysis(pos, cfg)

    status = "EXIT" if result.should_exit else ("WARN" if result.should_warn else "OK")

    return (
        f"[{status}] held={result.time_held_minutes:.1f}m "
        f"remaining={result.time_remaining_minutes:.1f}m "
        f"decay={result.time_decay_factor:.2f}"
    )
