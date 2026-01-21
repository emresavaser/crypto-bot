# execution/heartbeat.py — SCALPER ETERNAL — HEARTBEAT ORACLE — 2026 v1.0
# Component health monitoring through heartbeat tracking
# Features:
# - Component registration with expected intervals
# - Stale detection and alerting
# - Health report generation
# - Automatic recovery suggestions

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import deque

from utils.logging import log_core


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    expected_interval_sec: float
    last_beat_ts: float = 0.0
    beat_count: int = 0
    miss_count: int = 0
    last_miss_ts: float = 0.0
    is_stale: bool = False
    stale_since_ts: float = 0.0
    recovery_attempts: int = 0
    beat_history: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class HeartbeatConfig:
    """Heartbeat monitoring configuration."""
    enabled: bool = True
    data_loop_interval_sec: float = 30.0
    signal_loop_interval_sec: float = 120.0
    guardian_interval_sec: float = 15.0
    entry_loop_interval_sec: float = 60.0
    alert_after_miss: int = 3
    recovery_cooldown_sec: float = 60.0


class HeartbeatMonitor:
    """
    HEARTBEAT ORACLE — Monitor component health through periodic beats.

    Components must call beat() regularly. If a component stops beating,
    it's marked as stale and alerts are triggered.
    """

    def __init__(self, config: Optional[HeartbeatConfig] = None):
        self.config = config or HeartbeatConfig()
        self._components: Dict[str, ComponentHealth] = {}
        self._alert_callbacks: List[Callable] = []
        self._recovery_callbacks: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    def register_component(
        self,
        name: str,
        expected_interval_sec: float,
        recovery_callback: Optional[Callable] = None,
    ) -> None:
        """
        Register a component for health monitoring.

        Args:
            name: Unique component name
            expected_interval_sec: Expected time between beats
            recovery_callback: Optional callback to attempt recovery
        """
        self._components[name] = ComponentHealth(
            name=name,
            expected_interval_sec=expected_interval_sec,
        )

        if recovery_callback is not None:
            self._recovery_callbacks[name] = recovery_callback

        log_core.info(f"HEARTBEAT: Registered component: {name} (interval={expected_interval_sec}s)")

    def register_alert_callback(self, callback: Callable) -> None:
        """Register callback for stale alerts: callback(component_name, health)"""
        self._alert_callbacks.append(callback)

    def beat(self, component_name: str) -> None:
        """
        Record a heartbeat from a component.

        Args:
            component_name: Name of the component sending the beat
        """
        now = time.time()

        health = self._components.get(component_name)
        if health is None:
            # Auto-register with default interval
            health = ComponentHealth(
                name=component_name,
                expected_interval_sec=60.0,
            )
            self._components[component_name] = health

        # Record beat
        health.last_beat_ts = now
        health.beat_count += 1
        health.beat_history.append(now)

        # Clear stale status if it was stale
        if health.is_stale:
            log_core.info(f"HEARTBEAT: {component_name} recovered after {health.miss_count} misses")
            health.is_stale = False
            health.stale_since_ts = 0.0
            health.miss_count = 0

    def check_health(self) -> Dict[str, Any]:
        """
        Check health of all registered components.

        Returns:
            Health report dict
        """
        now = time.time()
        report = {
            "timestamp": now,
            "healthy": [],
            "stale": [],
            "critical": [],
        }

        for name, health in self._components.items():
            age = now - health.last_beat_ts if health.last_beat_ts > 0 else float("inf")
            grace = health.expected_interval_sec * 1.5  # 50% grace period

            if age <= grace:
                # Healthy
                report["healthy"].append({
                    "name": name,
                    "age_sec": age,
                    "beat_count": health.beat_count,
                })
            else:
                # Stale
                miss_periods = int(age / health.expected_interval_sec) if health.expected_interval_sec > 0 else 1

                if not health.is_stale:
                    health.is_stale = True
                    health.stale_since_ts = now - age + grace
                    health.miss_count = miss_periods

                health.miss_count = miss_periods

                status = {
                    "name": name,
                    "age_sec": age,
                    "miss_count": health.miss_count,
                    "stale_since": health.stale_since_ts,
                }

                if health.miss_count >= self.config.alert_after_miss:
                    report["critical"].append(status)
                else:
                    report["stale"].append(status)

        return report

    def get_stale_components(self) -> List[str]:
        """Get list of stale component names."""
        now = time.time()
        stale = []

        for name, health in self._components.items():
            age = now - health.last_beat_ts if health.last_beat_ts > 0 else float("inf")
            grace = health.expected_interval_sec * 1.5

            if age > grace:
                stale.append(name)

        return stale

    def is_component_stale(self, name: str) -> bool:
        """Check if a specific component is stale."""
        health = self._components.get(name)
        if health is None:
            return False

        now = time.time()
        age = now - health.last_beat_ts if health.last_beat_ts > 0 else float("inf")
        grace = health.expected_interval_sec * 1.5

        return age > grace

    def get_component_age(self, name: str) -> float:
        """Get age (seconds since last beat) for a component."""
        health = self._components.get(name)
        if health is None or health.last_beat_ts <= 0:
            return float("inf")

        return time.time() - health.last_beat_ts

    async def trigger_alerts(self) -> int:
        """
        Check for stale components and trigger alerts.

        Returns:
            Number of alerts triggered
        """
        report = self.check_health()
        alert_count = 0

        # Alert for critical components
        for status in report["critical"]:
            name = status["name"]
            health = self._components.get(name)

            if health is None:
                continue

            # Trigger alert callbacks
            for callback in self._alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(name, health)
                    else:
                        callback(name, health)
                    alert_count += 1
                except Exception as e:
                    log_core.error(f"HEARTBEAT: Alert callback error: {e}")

            # Attempt recovery if configured
            recovery_fn = self._recovery_callbacks.get(name)
            if recovery_fn is not None:
                # Check cooldown
                now = time.time()
                if now - health.last_miss_ts >= self.config.recovery_cooldown_sec:
                    health.last_miss_ts = now
                    health.recovery_attempts += 1

                    log_core.warning(f"HEARTBEAT: Attempting recovery for {name} (attempt {health.recovery_attempts})")

                    try:
                        if asyncio.iscoroutinefunction(recovery_fn):
                            await recovery_fn()
                        else:
                            recovery_fn()
                    except Exception as e:
                        log_core.error(f"HEARTBEAT: Recovery failed for {name}: {e}")

        return alert_count

    def get_health_summary(self) -> str:
        """Get a human-readable health summary."""
        report = self.check_health()

        lines = [f"HEARTBEAT STATUS ({len(self._components)} components):"]

        if report["healthy"]:
            names = [s["name"] for s in report["healthy"]]
            lines.append(f"  HEALTHY: {', '.join(names)}")

        if report["stale"]:
            items = [f"{s['name']}({s['age_sec']:.0f}s)" for s in report["stale"]]
            lines.append(f"  STALE: {', '.join(items)}")

        if report["critical"]:
            items = [f"{s['name']}({s['miss_count']} misses)" for s in report["critical"]]
            lines.append(f"  CRITICAL: {', '.join(items)}")

        return "\n".join(lines)

    def reset_component(self, name: str) -> None:
        """Reset health tracking for a component."""
        health = self._components.get(name)
        if health is not None:
            health.last_beat_ts = 0.0
            health.beat_count = 0
            health.miss_count = 0
            health.is_stale = False
            health.stale_since_ts = 0.0
            health.recovery_attempts = 0
            health.beat_history.clear()

    def get_beat_rate(self, name: str, window_sec: float = 60.0) -> float:
        """
        Get the beat rate (beats per minute) for a component.

        Args:
            name: Component name
            window_sec: Time window to consider

        Returns:
            Beats per minute
        """
        health = self._components.get(name)
        if health is None:
            return 0.0

        now = time.time()
        cutoff = now - window_sec

        # Count beats in window
        beats_in_window = sum(1 for ts in health.beat_history if ts >= cutoff)

        # Convert to beats per minute
        minutes = window_sec / 60.0
        return beats_in_window / minutes if minutes > 0 else 0.0


# Global singleton
_heartbeat: Optional[HeartbeatMonitor] = None


def get_heartbeat_monitor(config: Optional[HeartbeatConfig] = None) -> HeartbeatMonitor:
    """Get or create the global heartbeat monitor."""
    global _heartbeat

    if _heartbeat is None:
        _heartbeat = HeartbeatMonitor(config)

    return _heartbeat


def beat(component_name: str) -> None:
    """Convenience function to send a heartbeat."""
    monitor = get_heartbeat_monitor()
    monitor.beat(component_name)


def is_stale(component_name: str) -> bool:
    """Convenience function to check if a component is stale."""
    monitor = get_heartbeat_monitor()
    return monitor.is_component_stale(component_name)


def get_stale_components() -> List[str]:
    """Convenience function to get stale components."""
    monitor = get_heartbeat_monitor()
    return monitor.get_stale_components()


async def initialize_heartbeat(bot) -> HeartbeatMonitor:
    """
    Initialize heartbeat monitor with standard components.

    Args:
        bot: Bot instance to get config from

    Returns:
        Configured HeartbeatMonitor
    """
    cfg = getattr(bot, "cfg", None)

    config = HeartbeatConfig()
    if cfg is not None:
        if hasattr(cfg, "HEARTBEAT_ENABLED"):
            config.enabled = bool(cfg.HEARTBEAT_ENABLED)
        if hasattr(cfg, "HEARTBEAT_DATA_LOOP_SEC"):
            config.data_loop_interval_sec = float(cfg.HEARTBEAT_DATA_LOOP_SEC)
        if hasattr(cfg, "HEARTBEAT_GUARDIAN_SEC"):
            config.guardian_interval_sec = float(cfg.HEARTBEAT_GUARDIAN_SEC)
        if hasattr(cfg, "HEARTBEAT_ALERT_AFTER_MISS"):
            config.alert_after_miss = int(cfg.HEARTBEAT_ALERT_AFTER_MISS)

    monitor = get_heartbeat_monitor(config)

    if not config.enabled:
        return monitor

    # Register standard components
    monitor.register_component("guardian", config.guardian_interval_sec)
    monitor.register_component("data_loop", config.data_loop_interval_sec)
    monitor.register_component("entry_loop", config.entry_loop_interval_sec)
    monitor.register_component("signal_loop", config.signal_loop_interval_sec)

    # Register alert callback for notifications
    notify = getattr(bot, "notify", None)
    if notify is not None:
        async def alert_callback(name: str, health: ComponentHealth):
            try:
                await notify.speak(
                    f"HEARTBEAT ALERT: {name} stale for {health.miss_count} periods",
                    "critical"
                )
            except Exception:
                pass

        monitor.register_alert_callback(alert_callback)

    log_core.info("HEARTBEAT: Monitor initialized with standard components")
    return monitor
