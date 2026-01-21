# data/websocket_stream.py — SCALPER ETERNAL — REAL-TIME COSMIC STREAM — 2026 v1.0
# WebSocket streaming manager using ccxtpro for real-time market data
# Features:
# - Auto-reconnect with exponential backoff
# - Fallback to REST on persistent failure
# - Multi-stream support: ticker, OHLCV, orderbook, trades
# - Thread-safe cache updates

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from utils.logging import log_data

# Try to import ccxtpro, fall back gracefully
try:
    import ccxt.pro as ccxtpro
    CCXTPRO_AVAILABLE = True
except ImportError:
    ccxtpro = None
    CCXTPRO_AVAILABLE = False
    log_data.warning("ccxtpro not available — WebSocket features disabled")


def _symkey(sym: str) -> str:
    """Canonical symbol key."""
    s = str(sym or "").upper().strip()
    s = s.replace("/USDT:USDT", "USDT").replace("/USDT", "USDT")
    s = s.replace(":USDT", "USDT").replace(":", "")
    s = s.replace("/", "")
    if s.endswith("USDTUSDT"):
        s = s[:-4]
    return s


def _safe_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v  # NaN check
    except Exception:
        return default


@dataclass
class StreamHealth:
    """Track health of a single stream."""
    last_update_ts: float = 0.0
    last_error_ts: float = 0.0
    last_error: str = ""
    reconnect_count: int = 0
    message_count: int = 0
    is_connected: bool = False


@dataclass
class WebSocketConfig:
    """WebSocket configuration."""
    enabled: bool = True
    reconnect_delay_sec: float = 5.0
    reconnect_max_delay_sec: float = 300.0
    reconnect_backoff_mult: float = 1.5
    fallback_to_rest: bool = True
    health_check_sec: float = 30.0
    stale_threshold_sec: float = 60.0


class WebSocketStreamManager:
    """
    COSMIC STREAM MANAGER — Real-time data streaming using ccxtpro.

    Manages WebSocket connections for:
    - Ticker (real-time price updates)
    - OHLCV (real-time candle updates)
    - Order Book (depth data for order flow analysis)
    - Trades (real-time trade stream for CVD calculation)
    """

    def __init__(
        self,
        exchange_id: str = "binanceusdm",
        api_key: str = "",
        api_secret: str = "",
        config: Optional[WebSocketConfig] = None,
    ):
        self.exchange_id = exchange_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or WebSocketConfig()

        self.ws_exchange: Optional[Any] = None
        self._shutdown = asyncio.Event()

        # Stream health tracking
        self._health: Dict[str, StreamHealth] = {}  # key: "ticker_BTCUSDT", "ohlcv_BTCUSDT_1m", etc.

        # Subscribed symbols
        self._subscribed_tickers: Set[str] = set()
        self._subscribed_ohlcv: Set[str] = set()  # "BTCUSDT_1m" format
        self._subscribed_orderbook: Set[str] = set()
        self._subscribed_trades: Set[str] = set()

        # Callbacks for data updates
        self._ticker_callbacks: List[Callable] = []
        self._ohlcv_callbacks: List[Callable] = []
        self._orderbook_callbacks: List[Callable] = []
        self._trades_callbacks: List[Callable] = []

        # Running tasks
        self._tasks: Dict[str, asyncio.Task] = {}

        # Connection state
        self._connected = False
        self._last_connect_attempt = 0.0
        self._current_backoff = self.config.reconnect_delay_sec

    async def initialize(self) -> bool:
        """Initialize WebSocket exchange connection."""
        if not CCXTPRO_AVAILABLE:
            log_data.warning("WEBSOCKET INIT FAILED — ccxtpro not installed")
            return False

        if not self.config.enabled:
            log_data.info("WEBSOCKET DISABLED by config")
            return False

        try:
            exchange_class = getattr(ccxtpro, self.exchange_id, None)
            if exchange_class is None:
                log_data.error(f"WEBSOCKET: Unknown exchange {self.exchange_id}")
                return False

            params = {
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
            }

            if self.api_key and self.api_secret:
                params["apiKey"] = self.api_key
                params["secret"] = self.api_secret

            self.ws_exchange = exchange_class(params)

            # Load markets for symbol resolution
            await self.ws_exchange.load_markets()

            self._connected = True
            self._current_backoff = self.config.reconnect_delay_sec

            log_data.critical(f"WEBSOCKET INITIALIZED — {self.exchange_id} | markets={len(self.ws_exchange.markets)}")
            return True

        except Exception as e:
            log_data.error(f"WEBSOCKET INIT ERROR: {e}")
            return False

    async def close(self) -> None:
        """Close WebSocket connection and all streams."""
        self._shutdown.set()

        # Cancel all running tasks
        for name, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    pass

        self._tasks.clear()

        # Close exchange connection
        if self.ws_exchange:
            try:
                await self.ws_exchange.close()
            except Exception:
                pass

        self._connected = False
        log_data.info("WEBSOCKET CLOSED")

    def register_ticker_callback(self, callback: Callable) -> None:
        """Register callback for ticker updates: callback(symbol, price, bid, ask, timestamp)"""
        self._ticker_callbacks.append(callback)

    def register_ohlcv_callback(self, callback: Callable) -> None:
        """Register callback for OHLCV updates: callback(symbol, timeframe, candles)"""
        self._ohlcv_callbacks.append(callback)

    def register_orderbook_callback(self, callback: Callable) -> None:
        """Register callback for orderbook updates: callback(symbol, bids, asks, timestamp)"""
        self._orderbook_callbacks.append(callback)

    def register_trades_callback(self, callback: Callable) -> None:
        """Register callback for trade updates: callback(symbol, trades)"""
        self._trades_callbacks.append(callback)

    async def subscribe_ticker(self, symbol: str) -> bool:
        """Subscribe to ticker stream for a symbol."""
        if not self._connected or self.ws_exchange is None:
            return False

        k = _symkey(symbol)
        if k in self._subscribed_tickers:
            return True

        raw_sym = self._resolve_symbol(symbol)
        if not raw_sym:
            log_data.warning(f"WEBSOCKET: Cannot resolve symbol {symbol}")
            return False

        task_name = f"ticker_{k}"
        if task_name not in self._tasks or self._tasks[task_name].done():
            self._tasks[task_name] = asyncio.create_task(
                self._ticker_loop(k, raw_sym),
                name=task_name
            )
            self._subscribed_tickers.add(k)
            self._health[task_name] = StreamHealth()
            log_data.info(f"WEBSOCKET: Subscribed to ticker {k}")
            return True

        return True

    async def subscribe_ohlcv(self, symbol: str, timeframe: str = "1m") -> bool:
        """Subscribe to OHLCV stream for a symbol."""
        if not self._connected or self.ws_exchange is None:
            return False

        k = _symkey(symbol)
        sub_key = f"{k}_{timeframe}"

        if sub_key in self._subscribed_ohlcv:
            return True

        raw_sym = self._resolve_symbol(symbol)
        if not raw_sym:
            log_data.warning(f"WEBSOCKET: Cannot resolve symbol {symbol}")
            return False

        task_name = f"ohlcv_{sub_key}"
        if task_name not in self._tasks or self._tasks[task_name].done():
            self._tasks[task_name] = asyncio.create_task(
                self._ohlcv_loop(k, raw_sym, timeframe),
                name=task_name
            )
            self._subscribed_ohlcv.add(sub_key)
            self._health[task_name] = StreamHealth()
            log_data.info(f"WEBSOCKET: Subscribed to OHLCV {k} {timeframe}")
            return True

        return True

    async def subscribe_orderbook(self, symbol: str, limit: int = 20) -> bool:
        """Subscribe to order book stream for a symbol."""
        if not self._connected or self.ws_exchange is None:
            return False

        k = _symkey(symbol)
        if k in self._subscribed_orderbook:
            return True

        raw_sym = self._resolve_symbol(symbol)
        if not raw_sym:
            log_data.warning(f"WEBSOCKET: Cannot resolve symbol {symbol}")
            return False

        task_name = f"orderbook_{k}"
        if task_name not in self._tasks or self._tasks[task_name].done():
            self._tasks[task_name] = asyncio.create_task(
                self._orderbook_loop(k, raw_sym, limit),
                name=task_name
            )
            self._subscribed_orderbook.add(k)
            self._health[task_name] = StreamHealth()
            log_data.info(f"WEBSOCKET: Subscribed to orderbook {k}")
            return True

        return True

    async def subscribe_trades(self, symbol: str) -> bool:
        """Subscribe to trades stream for a symbol."""
        if not self._connected or self.ws_exchange is None:
            return False

        k = _symkey(symbol)
        if k in self._subscribed_trades:
            return True

        raw_sym = self._resolve_symbol(symbol)
        if not raw_sym:
            log_data.warning(f"WEBSOCKET: Cannot resolve symbol {symbol}")
            return False

        task_name = f"trades_{k}"
        if task_name not in self._tasks or self._tasks[task_name].done():
            self._tasks[task_name] = asyncio.create_task(
                self._trades_loop(k, raw_sym),
                name=task_name
            )
            self._subscribed_trades.add(k)
            self._health[task_name] = StreamHealth()
            log_data.info(f"WEBSOCKET: Subscribed to trades {k}")
            return True

        return True

    def _resolve_symbol(self, symbol: str) -> Optional[str]:
        """Resolve canonical symbol to exchange raw symbol."""
        if self.ws_exchange is None:
            return None

        k = _symkey(symbol)
        markets = self.ws_exchange.markets or {}

        # Try exact match first
        if symbol in markets:
            return symbol

        # Try common futures formats
        candidates = [
            f"{k[:len(k)-4]}/USDT:USDT" if k.endswith("USDT") else f"{k}/USDT:USDT",
            f"{k[:len(k)-4]}/USDT" if k.endswith("USDT") else f"{k}/USDT",
            k,
        ]

        for cand in candidates:
            if cand in markets:
                return cand

        return None

    async def _ticker_loop(self, k: str, raw_sym: str) -> None:
        """Ticker streaming loop with auto-reconnect."""
        health_key = f"ticker_{k}"
        backoff = self.config.reconnect_delay_sec

        while not self._shutdown.is_set():
            try:
                ticker = await self.ws_exchange.watch_ticker(raw_sym)

                # Update health
                self._health[health_key].last_update_ts = time.time()
                self._health[health_key].message_count += 1
                self._health[health_key].is_connected = True

                # Reset backoff on success
                backoff = self.config.reconnect_delay_sec

                # Extract data
                price = _safe_float(ticker.get("last") or ticker.get("close"), 0.0)
                bid = _safe_float(ticker.get("bid"), price)
                ask = _safe_float(ticker.get("ask"), price)
                ts = _safe_float(ticker.get("timestamp"), time.time() * 1000) / 1000.0

                # Call registered callbacks
                for cb in self._ticker_callbacks:
                    try:
                        cb(k, price, bid, ask, ts)
                    except Exception as e:
                        log_data.error(f"WEBSOCKET: Ticker callback error: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._health[health_key].last_error_ts = time.time()
                self._health[health_key].last_error = str(e)
                self._health[health_key].is_connected = False
                self._health[health_key].reconnect_count += 1

                log_data.warning(f"WEBSOCKET: Ticker {k} error: {e} — reconnecting in {backoff:.1f}s")

                await asyncio.sleep(backoff)
                backoff = min(backoff * self.config.reconnect_backoff_mult, self.config.reconnect_max_delay_sec)

    async def _ohlcv_loop(self, k: str, raw_sym: str, timeframe: str) -> None:
        """OHLCV streaming loop with auto-reconnect."""
        health_key = f"ohlcv_{k}_{timeframe}"
        backoff = self.config.reconnect_delay_sec

        while not self._shutdown.is_set():
            try:
                candles = await self.ws_exchange.watch_ohlcv(raw_sym, timeframe)

                # Update health
                self._health[health_key].last_update_ts = time.time()
                self._health[health_key].message_count += 1
                self._health[health_key].is_connected = True

                # Reset backoff on success
                backoff = self.config.reconnect_delay_sec

                # Call registered callbacks
                for cb in self._ohlcv_callbacks:
                    try:
                        cb(k, timeframe, candles)
                    except Exception as e:
                        log_data.error(f"WEBSOCKET: OHLCV callback error: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._health[health_key].last_error_ts = time.time()
                self._health[health_key].last_error = str(e)
                self._health[health_key].is_connected = False
                self._health[health_key].reconnect_count += 1

                log_data.warning(f"WEBSOCKET: OHLCV {k} {timeframe} error: {e} — reconnecting in {backoff:.1f}s")

                await asyncio.sleep(backoff)
                backoff = min(backoff * self.config.reconnect_backoff_mult, self.config.reconnect_max_delay_sec)

    async def _orderbook_loop(self, k: str, raw_sym: str, limit: int) -> None:
        """Order book streaming loop with auto-reconnect."""
        health_key = f"orderbook_{k}"
        backoff = self.config.reconnect_delay_sec

        while not self._shutdown.is_set():
            try:
                orderbook = await self.ws_exchange.watch_order_book(raw_sym, limit)

                # Update health
                self._health[health_key].last_update_ts = time.time()
                self._health[health_key].message_count += 1
                self._health[health_key].is_connected = True

                # Reset backoff on success
                backoff = self.config.reconnect_delay_sec

                # Extract data
                bids = orderbook.get("bids", [])
                asks = orderbook.get("asks", [])
                ts = _safe_float(orderbook.get("timestamp"), time.time() * 1000) / 1000.0

                # Call registered callbacks
                for cb in self._orderbook_callbacks:
                    try:
                        cb(k, bids, asks, ts)
                    except Exception as e:
                        log_data.error(f"WEBSOCKET: Orderbook callback error: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._health[health_key].last_error_ts = time.time()
                self._health[health_key].last_error = str(e)
                self._health[health_key].is_connected = False
                self._health[health_key].reconnect_count += 1

                log_data.warning(f"WEBSOCKET: Orderbook {k} error: {e} — reconnecting in {backoff:.1f}s")

                await asyncio.sleep(backoff)
                backoff = min(backoff * self.config.reconnect_backoff_mult, self.config.reconnect_max_delay_sec)

    async def _trades_loop(self, k: str, raw_sym: str) -> None:
        """Trades streaming loop with auto-reconnect."""
        health_key = f"trades_{k}"
        backoff = self.config.reconnect_delay_sec

        while not self._shutdown.is_set():
            try:
                trades = await self.ws_exchange.watch_trades(raw_sym)

                # Update health
                self._health[health_key].last_update_ts = time.time()
                self._health[health_key].message_count += 1
                self._health[health_key].is_connected = True

                # Reset backoff on success
                backoff = self.config.reconnect_delay_sec

                # Call registered callbacks
                for cb in self._trades_callbacks:
                    try:
                        cb(k, trades)
                    except Exception as e:
                        log_data.error(f"WEBSOCKET: Trades callback error: {e}")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._health[health_key].last_error_ts = time.time()
                self._health[health_key].last_error = str(e)
                self._health[health_key].is_connected = False
                self._health[health_key].reconnect_count += 1

                log_data.warning(f"WEBSOCKET: Trades {k} error: {e} — reconnecting in {backoff:.1f}s")

                await asyncio.sleep(backoff)
                backoff = min(backoff * self.config.reconnect_backoff_mult, self.config.reconnect_max_delay_sec)

    def get_health_report(self) -> Dict[str, Any]:
        """Get health status of all streams."""
        now = time.time()
        report = {
            "connected": self._connected,
            "streams": {},
            "stale_streams": [],
        }

        for key, health in self._health.items():
            age = now - health.last_update_ts if health.last_update_ts > 0 else float("inf")
            is_stale = age > self.config.stale_threshold_sec

            report["streams"][key] = {
                "connected": health.is_connected,
                "age_sec": age,
                "stale": is_stale,
                "message_count": health.message_count,
                "reconnect_count": health.reconnect_count,
                "last_error": health.last_error if health.last_error else None,
            }

            if is_stale:
                report["stale_streams"].append(key)

        return report

    def is_stream_healthy(self, stream_key: str) -> bool:
        """Check if a specific stream is healthy."""
        health = self._health.get(stream_key)
        if health is None:
            return False

        if not health.is_connected:
            return False

        age = time.time() - health.last_update_ts
        return age <= self.config.stale_threshold_sec


# Global singleton for easy access
_ws_manager: Optional[WebSocketStreamManager] = None


def get_ws_manager() -> Optional[WebSocketStreamManager]:
    """Get the global WebSocket manager instance."""
    return _ws_manager


async def initialize_ws_manager(
    exchange_id: str = "binanceusdm",
    api_key: str = "",
    api_secret: str = "",
    config: Optional[WebSocketConfig] = None,
) -> Optional[WebSocketStreamManager]:
    """Initialize and return the global WebSocket manager."""
    global _ws_manager

    if _ws_manager is not None:
        return _ws_manager

    _ws_manager = WebSocketStreamManager(exchange_id, api_key, api_secret, config)

    if await _ws_manager.initialize():
        return _ws_manager

    _ws_manager = None
    return None


async def close_ws_manager() -> None:
    """Close the global WebSocket manager."""
    global _ws_manager

    if _ws_manager is not None:
        await _ws_manager.close()
        _ws_manager = None
