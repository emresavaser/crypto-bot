# execution/distributed_lock.py — SCALPER ETERNAL — DISTRIBUTED LOCK ORACLE — 2026 v1.0
# Multi-instance safety through distributed locking
# Features:
# - File-based locking for single-machine deployments
# - Redis-based locking for distributed deployments
# - Instance-level and symbol-level locks
# - Automatic lock cleanup on crash

from __future__ import annotations

import asyncio
import os
import time
import socket
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

from utils.logging import log_core

# Try to import filelock
try:
    from filelock import FileLock, Timeout
    FILELOCK_AVAILABLE = True
except ImportError:
    FileLock = None
    Timeout = None
    FILELOCK_AVAILABLE = False

# Try to import redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False


def _get_instance_id() -> str:
    """Generate a unique instance ID."""
    hostname = socket.gethostname()
    pid = os.getpid()
    return f"eclipse_{hostname}_{pid}"


@dataclass
class DistributedLockConfig:
    """Distributed lock configuration."""
    enabled: bool = False
    lock_type: str = "file"  # "file" or "redis"
    lock_path: str = "~/.eclipse_locks/"
    redis_url: str = ""  # redis://localhost:6379
    lock_timeout_sec: float = 60.0
    refresh_interval_sec: float = 15.0
    stale_lock_sec: float = 120.0  # Consider lock stale after this


class FileLockManager:
    """
    FILE LOCK MANAGER — File-based locking for single-machine safety.

    Uses file locks to prevent multiple instances from:
    - Running simultaneously (instance lock)
    - Trading the same symbol (symbol lock)
    """

    def __init__(self, config: DistributedLockConfig):
        self.config = config
        self.lock_dir = Path(os.path.expanduser(config.lock_path))
        self.instance_id = _get_instance_id()

        # Track held locks
        self._instance_lock: Optional[Any] = None
        self._symbol_locks: Dict[str, Any] = {}

        # Ensure lock directory exists
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _get_instance_lock_path(self) -> Path:
        """Get path for instance lock file."""
        return self.lock_dir / "instance.lock"

    def _get_symbol_lock_path(self, symbol: str) -> Path:
        """Get path for symbol lock file."""
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        return self.lock_dir / f"symbol_{safe_symbol}.lock"

    def acquire_instance_lock(self, timeout: float = 0.0) -> bool:
        """
        Acquire instance-level lock.
        Prevents multiple bot instances from running.

        Args:
            timeout: Timeout in seconds (0 = non-blocking)

        Returns:
            True if lock acquired, False otherwise
        """
        if not FILELOCK_AVAILABLE:
            log_core.warning("DISTRIBUTED LOCK: filelock not installed")
            return True

        if self._instance_lock is not None:
            return True  # Already held

        lock_path = self._get_instance_lock_path()

        try:
            lock = FileLock(str(lock_path), timeout=timeout)
            lock.acquire(timeout=timeout)

            # Write instance info
            with open(str(lock_path) + ".info", "w") as f:
                f.write(f"{self.instance_id}\n{time.time()}")

            self._instance_lock = lock
            log_core.info(f"DISTRIBUTED LOCK: Instance lock acquired: {self.instance_id}")
            return True

        except Timeout:
            # Check if existing lock is stale
            if self._is_lock_stale(lock_path):
                log_core.warning("DISTRIBUTED LOCK: Removing stale instance lock")
                self._force_release_lock(lock_path)
                return self.acquire_instance_lock(timeout)

            log_core.warning("DISTRIBUTED LOCK: Instance lock held by another process")
            return False

        except Exception as e:
            log_core.error(f"DISTRIBUTED LOCK: Failed to acquire instance lock: {e}")
            return False

    def release_instance_lock(self) -> None:
        """Release instance-level lock."""
        if self._instance_lock is not None:
            try:
                self._instance_lock.release()
                # Clean up info file
                info_path = str(self._get_instance_lock_path()) + ".info"
                if os.path.exists(info_path):
                    os.remove(info_path)
            except Exception as e:
                log_core.warning(f"DISTRIBUTED LOCK: Error releasing instance lock: {e}")
            finally:
                self._instance_lock = None

        log_core.info("DISTRIBUTED LOCK: Instance lock released")

    def acquire_symbol_lock(self, symbol: str, timeout: float = 0.0) -> bool:
        """
        Acquire symbol-level lock.
        Prevents multiple instances from trading the same symbol.

        Args:
            symbol: Trading symbol
            timeout: Timeout in seconds

        Returns:
            True if lock acquired, False otherwise
        """
        if not FILELOCK_AVAILABLE:
            return True

        if symbol in self._symbol_locks:
            return True  # Already held

        lock_path = self._get_symbol_lock_path(symbol)

        try:
            lock = FileLock(str(lock_path), timeout=timeout)
            lock.acquire(timeout=timeout)

            # Write lock info
            with open(str(lock_path) + ".info", "w") as f:
                f.write(f"{self.instance_id}\n{time.time()}")

            self._symbol_locks[symbol] = lock
            log_core.debug(f"DISTRIBUTED LOCK: Symbol lock acquired: {symbol}")
            return True

        except Timeout:
            if self._is_lock_stale(lock_path):
                self._force_release_lock(lock_path)
                return self.acquire_symbol_lock(symbol, timeout)
            return False

        except Exception as e:
            log_core.error(f"DISTRIBUTED LOCK: Failed to acquire symbol lock {symbol}: {e}")
            return False

    def release_symbol_lock(self, symbol: str) -> None:
        """Release symbol-level lock."""
        lock = self._symbol_locks.pop(symbol, None)
        if lock is not None:
            try:
                lock.release()
                info_path = str(self._get_symbol_lock_path(symbol)) + ".info"
                if os.path.exists(info_path):
                    os.remove(info_path)
            except Exception as e:
                log_core.warning(f"DISTRIBUTED LOCK: Error releasing symbol lock {symbol}: {e}")

    def release_all_locks(self) -> None:
        """Release all held locks."""
        for symbol in list(self._symbol_locks.keys()):
            self.release_symbol_lock(symbol)
        self.release_instance_lock()

    def is_symbol_locked(self, symbol: str) -> bool:
        """Check if a symbol is locked by this instance."""
        return symbol in self._symbol_locks

    def _is_lock_stale(self, lock_path: Path) -> bool:
        """Check if a lock file is stale."""
        info_path = str(lock_path) + ".info"
        if not os.path.exists(info_path):
            return True

        try:
            with open(info_path, "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    ts = float(lines[1].strip())
                    age = time.time() - ts
                    return age > self.config.stale_lock_sec
        except Exception:
            return True

        return False

    def _force_release_lock(self, lock_path: Path) -> None:
        """Force release a stale lock."""
        try:
            if lock_path.exists():
                os.remove(str(lock_path))
            info_path = str(lock_path) + ".info"
            if os.path.exists(info_path):
                os.remove(info_path)
        except Exception as e:
            log_core.warning(f"DISTRIBUTED LOCK: Error force-releasing lock: {e}")


class RedisLockManager:
    """
    REDIS LOCK MANAGER — Redis-based locking for distributed deployments.

    Uses Redis for distributed locking across multiple machines.
    """

    def __init__(self, config: DistributedLockConfig):
        self.config = config
        self.instance_id = _get_instance_id()
        self._redis: Optional[Any] = None
        self._held_locks: Set[str] = set()

    async def initialize(self) -> bool:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            log_core.warning("DISTRIBUTED LOCK: redis not installed")
            return False

        try:
            self._redis = await aioredis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            log_core.info(f"DISTRIBUTED LOCK: Redis connected: {self.config.redis_url}")
            return True

        except Exception as e:
            log_core.error(f"DISTRIBUTED LOCK: Redis connection failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        await self.release_all_locks()
        if self._redis is not None:
            await self._redis.close()

    async def acquire_instance_lock(self, timeout: float = 0.0) -> bool:
        """Acquire instance lock via Redis."""
        return await self._acquire_lock("eclipse:instance", timeout)

    async def release_instance_lock(self) -> None:
        """Release instance lock."""
        await self._release_lock("eclipse:instance")

    async def acquire_symbol_lock(self, symbol: str, timeout: float = 0.0) -> bool:
        """Acquire symbol lock via Redis."""
        key = f"eclipse:symbol:{symbol}"
        return await self._acquire_lock(key, timeout)

    async def release_symbol_lock(self, symbol: str) -> None:
        """Release symbol lock."""
        key = f"eclipse:symbol:{symbol}"
        await self._release_lock(key)

    async def release_all_locks(self) -> None:
        """Release all held locks."""
        for key in list(self._held_locks):
            await self._release_lock(key)

    async def _acquire_lock(self, key: str, timeout: float) -> bool:
        """Internal lock acquisition."""
        if self._redis is None:
            return True

        try:
            # Try to set lock with NX (only if not exists) and EX (expiration)
            ttl = int(self.config.lock_timeout_sec)
            result = await self._redis.set(key, self.instance_id, nx=True, ex=ttl)

            if result:
                self._held_locks.add(key)
                return True

            # Check if we already own it
            owner = await self._redis.get(key)
            if owner == self.instance_id:
                # Refresh TTL
                await self._redis.expire(key, ttl)
                self._held_locks.add(key)
                return True

            return False

        except Exception as e:
            log_core.error(f"DISTRIBUTED LOCK: Redis acquire failed: {e}")
            return True  # Fail open for safety

    async def _release_lock(self, key: str) -> None:
        """Internal lock release."""
        if self._redis is None:
            return

        try:
            # Only release if we own it
            owner = await self._redis.get(key)
            if owner == self.instance_id:
                await self._redis.delete(key)
            self._held_locks.discard(key)
        except Exception as e:
            log_core.warning(f"DISTRIBUTED LOCK: Redis release failed: {e}")


# Global lock manager
_lock_manager: Optional[Any] = None


def get_lock_manager(config: Optional[DistributedLockConfig] = None) -> Optional[Any]:
    """Get or create the global lock manager."""
    global _lock_manager

    if _lock_manager is not None:
        return _lock_manager

    if config is None:
        config = DistributedLockConfig()

    if not config.enabled:
        return None

    if config.lock_type == "redis" and REDIS_AVAILABLE:
        _lock_manager = RedisLockManager(config)
    elif FILELOCK_AVAILABLE:
        _lock_manager = FileLockManager(config)
    else:
        log_core.warning("DISTRIBUTED LOCK: No lock backend available")
        return None

    return _lock_manager


def acquire_instance_lock(instance_id: Optional[str] = None) -> bool:
    """
    Convenience function to acquire instance lock.
    Used by bootstrap/guardian.
    """
    manager = get_lock_manager()
    if manager is None:
        return True

    if isinstance(manager, FileLockManager):
        return manager.acquire_instance_lock()

    # For Redis, we need to run in async context
    return True  # Caller should use async version


def release_instance_lock(instance_id: Optional[str] = None) -> None:
    """Convenience function to release instance lock."""
    manager = get_lock_manager()
    if manager is None:
        return

    if isinstance(manager, FileLockManager):
        manager.release_instance_lock()


def acquire_symbol_lock(symbol: str, instance_id: Optional[str] = None) -> bool:
    """Convenience function to acquire symbol lock."""
    manager = get_lock_manager()
    if manager is None:
        return True

    if isinstance(manager, FileLockManager):
        return manager.acquire_symbol_lock(symbol)

    return True


def release_symbol_lock(symbol: str, instance_id: Optional[str] = None) -> None:
    """Convenience function to release symbol lock."""
    manager = get_lock_manager()
    if manager is None:
        return

    if isinstance(manager, FileLockManager):
        manager.release_symbol_lock(symbol)


def is_symbol_locked(symbol: str) -> bool:
    """Check if symbol is locked by this instance."""
    manager = get_lock_manager()
    if manager is None:
        return False

    if isinstance(manager, FileLockManager):
        return manager.is_symbol_locked(symbol)

    return False
