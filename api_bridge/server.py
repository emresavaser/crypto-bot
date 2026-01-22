# api_bridge/server.py — ECLIPSE SCALPER FULL INTEGRATION — 2026 v2.0
# Bu dosya Eclipse Scalper'i frontend ile tam entegre eder
# Artik entry.py, exit.py, guardian.py ve stratejiler gercekten calisacak

import asyncio
import os
import sys
import io
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

# Windows console encoding fix - must be before any print
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Eclipse Scalper path'ini ekle
ECLIPSE_PATH = Path(__file__).parent.parent / "eclipse_scalper"
sys.path.insert(0, str(ECLIPSE_PATH))

load_dotenv()

# Eclipse modullerini import et
try:
  
    from bot.core import EclipseEternal
    from config.settings import Config, MicroConfig
    from utils.logging import log_core, log_entry
    ECLIPSE_AVAILABLE = True
    print("[OK] Eclipse Scalper modulleri yuklendi")
except ImportError as e:
    ECLIPSE_AVAILABLE = False
    print(f"[WARN] Eclipse Scalper modulleri yuklenemedi: {e}")
    log_core = None
    log_entry = None

# Guardian ve diger loop'lari import et
try:
    from execution.guardian import guardian_loop
    GUARDIAN_AVAILABLE = True
    print("[OK] Guardian loop yuklendi")
except ImportError as e:
    GUARDIAN_AVAILABLE = False
    guardian_loop = None
    print(f"[WARN] Guardian yuklenemedi: {e}")

try:
    from execution.entry_loop import entry_loop
    ENTRY_LOOP_AVAILABLE = True
    print("[OK] Entry loop yuklendi")
except ImportError as e:
    ENTRY_LOOP_AVAILABLE = False
    entry_loop = None
    print(f"[WARN] Entry loop yuklenemedi: {e}")

try:
    from execution.data_loop import data_loop
    DATA_LOOP_AVAILABLE = True
    print("[OK] Data loop yuklendi")
except ImportError as e:
    DATA_LOOP_AVAILABLE = False
    data_loop = None
    print(f"[WARN] Data loop yuklenemedi: {e}")

# CCXT fallback
try:
    import ccxt.async_support as ccxt
    import aiohttp
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    ccxt = None
    aiohttp = None

app = FastAPI(
    title="Eclipse Scalper API Bridge - Full Integration",
    description="Frontend ile Eclipse Scalper tam entegrasyonu",
    version="2.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Global State ==============

@dataclass
class BridgeState:
    # Eclipse Bot instance
    bot: Optional[Any] = None

    # Asyncio tasks
    tasks: Dict[str, asyncio.Task] = field(default_factory=dict)

    # State flags
    is_running: bool = False
    is_connected: bool = False
    startup_time: Optional[float] = None

    # WebSocket clients
    connected_clients: List[WebSocket] = field(default_factory=list)

    # Fallback mode (CCXT only, no Eclipse)
    fallback_exchange: Optional[Any] = None
    is_fallback_mode: bool = False

    # Trade history (for fallback mode)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    total_pnl: float = 0.0
    win_count: int = 0
    loss_count: int = 0

    # Logs (frontend için)
    logs: List[Dict[str, Any]] = field(default_factory=list)


bridge_state = BridgeState()


def add_log(level: str, message: str):
    """Frontend'e gönderilecek log ekle"""
    log_entry_dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message
    }
    bridge_state.logs.append(log_entry_dict)
    # Max 200 log tut
    if len(bridge_state.logs) > 200:
        bridge_state.logs = bridge_state.logs[-200:]

    # WebSocket'e broadcast et
    asyncio.create_task(broadcast_log(log_entry_dict))


async def broadcast_log(log_entry: dict):
    """Log'u tüm WebSocket client'lara gönder"""
    await manager.broadcast({
        "type": "log",
        "data": log_entry
    })


# ============== Pydantic Models ==============

class ConnectRequest(BaseModel):
    api_key: str = Field(default=None)
    api_secret: str = Field(default=None)
    apiKey: str = Field(default=None)
    apiSecret: str = Field(default=None)
    testnet: bool = False

    def get_api_key(self) -> str:
        return self.api_key or self.apiKey or ""

    def get_api_secret(self) -> str:
        return self.api_secret or self.apiSecret or ""


class BotStartRequest(BaseModel):
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    mode: str = "auto"  # auto, micro, production
    dry_run: bool = True
    strategy: str = "eclipse"  # eclipse, rsi, sma, macd, bollinger
    interval: str = "1m"
    amount: float = 0.002
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class ManualTradeRequest(BaseModel):
    symbol: str
    side: str  # "BUY" or "SELL"
    amount: float


# ============== WebSocket Manager ==============

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ============== Bot Event Handlers ==============

class BotEventForwarder:
    """Eclipse bot olaylarını WebSocket'e ilet"""

    def __init__(self):
        self.last_signal_time = 0

    async def on_signal(self, symbol: str, side: str, confidence: float, reason: str):
        """Yeni sinyal oluştuğunda"""
        add_log("info", f"[SIGNAL] SİNYAL: {symbol} {side} (güven: {confidence:.2f}) - {reason}")
        await manager.broadcast({
            "type": "new_signal",
            "data": {
                "symbol": symbol,
                "side": side,
                "confidence": confidence,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })

    async def on_trade(self, symbol: str, side: str, amount: float, price: float, pnl: Optional[float] = None):
        """Trade gerçekleştiğinde"""
        trade_type = "entry" if pnl is None else "exit"
        add_log("trade", f"[TRADE] TRADE: {side} {amount} {symbol} @ ${price:.2f}" + (f" PnL: ${pnl:+.2f}" if pnl else ""))

        trade_record = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "pnl": pnl,
            "type": trade_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        bridge_state.trades.insert(0, trade_record)
        if len(bridge_state.trades) > 100:
            bridge_state.trades = bridge_state.trades[:100]

        await manager.broadcast({
            "type": "new_trade",
            "data": trade_record
        })

    async def on_position_update(self, positions: dict):
        """Pozisyon değişikliğinde"""
        await manager.broadcast({
            "type": "positions_update",
            "data": positions
        })

    async def on_error(self, error: str):
        """Hata oluştuğunda"""
        add_log("error", f"[ERROR] HATA: {error}")
        await manager.broadcast({
            "type": "error",
            "data": {"message": error}
        })


event_forwarder = BotEventForwarder()


# ============== Eclipse Bot Helpers ==============

def _safe_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v  # NaN check
    except:
        return default


def _extract_usdt_equity(balance: Any) -> float:
    """Balance'dan USDT equity çıkar"""
    if not isinstance(balance, dict):
        return 0.0

    # total.USDT
    total = balance.get("total")
    if isinstance(total, dict):
        v = _safe_float(total.get("USDT"), 0.0)
        if v > 0:
            return v

    # info içinden
    info = balance.get("info")
    if isinstance(info, dict):
        for k in ("totalWalletBalance", "totalMarginBalance", "walletBalance", "equity"):
            v = _safe_float(info.get(k), 0.0)
            if v > 0:
                return v

    return 0.0


async def get_bot_status() -> Dict[str, Any]:
    """Bot durumunu al"""

    # Eclipse bot aktif mi?
    if bridge_state.bot is not None and not bridge_state.is_fallback_mode:
        bot = bridge_state.bot
        state = getattr(bot, "state", None)  # PsycheState
        data = getattr(bot, "data", None)    # DataCache

        # Pozisyonları formatla ve PnL hesapla
        positions = []
        if state and hasattr(state, "positions"):
            for sym, pos in (state.positions or {}).items():
                try:
                    entry_price = float(getattr(pos, "entry_price", 0) or 0)
                    size = float(getattr(pos, "size", 0) or 0)
                    side = str(getattr(pos, "side", "long") or "long").lower()
                    leverage = int(getattr(pos, "leverage", 1) or 1)

                    # Current price'i data cache'den al
                    current_price = 0.0
                    if data:
                        try:
                            price_map = getattr(data, "price", {}) or {}
                            current_price = _safe_float(price_map.get(sym, 0), 0.0)
                        except:
                            pass

                    # PnL hesapla: (current - entry) * size * direction
                    pnl = 0.0
                    if current_price > 0 and entry_price > 0 and size > 0:
                        direction = 1 if side == "long" else -1
                        pnl = (current_price - entry_price) * size * direction

                    positions.append({
                        "symbol": sym,
                        "side": side,
                        "size": size,
                        "entry_price": entry_price,
                        "leverage": leverage,
                        "pnl": pnl,
                        "confidence": float(getattr(pos, "confidence", 0) or 0),
                        "current_price": current_price,
                        "atr": float(getattr(pos, "atr", 0) or 0),
                        "entry_ts": float(getattr(pos, "entry_ts", 0) or 0)
                    })
                except:
                    pass

        uptime = 0
        if bridge_state.startup_time:
            uptime = time.time() - bridge_state.startup_time

        # PsycheState alanlari
        total_trades = int(getattr(state, "total_trades", 0) if state else 0)
        total_wins = int(getattr(state, "total_wins", 0) if state else 0)
        win_rate = float(getattr(state, "win_rate", 0) if state else 0) * 100  # 0-1 -> 0-100
        if win_rate == 0 and total_trades > 0:
            win_rate = (total_wins / total_trades) * 100

        current_equity = float(getattr(state, "current_equity", 0) if state else 0)
        peak_equity = float(getattr(state, "peak_equity", 0) if state else 0)
        daily_pnl = float(getattr(state, "daily_pnl", 0) if state else 0)
        max_drawdown = float(getattr(state, "max_drawdown", 0) if state else 0) * 100  # 0-1 -> 0-100

        return {
            "status": "running" if bridge_state.is_running else "connected",
            "is_running": bridge_state.is_running,
            "mode": "eclipse",
            "positions": positions,
            "position_count": len(positions),
            "equity": current_equity,
            "peak_equity": peak_equity,
            "daily_pnl": daily_pnl,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "uptime": int(uptime),
            "active_symbols": list(getattr(bot, "active_symbols", set()) or []),
            "tasks_running": list(bridge_state.tasks.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # Fallback mode (CCXT only)
    if bridge_state.is_fallback_mode and bridge_state.fallback_exchange:
        uptime = 0
        if bridge_state.startup_time:
            uptime = time.time() - bridge_state.startup_time

        total_trades = len(bridge_state.trades)
        win_rate = (bridge_state.win_count / total_trades * 100) if total_trades > 0 else 0

        return {
            "status": "running" if bridge_state.is_running else "connected",
            "is_running": bridge_state.is_running,
            "mode": "fallback",
            "positions": [],
            "position_count": 0,
            "equity": 5000.0,  # Demo bakiye
            "peak_equity": 5000.0,
            "daily_pnl": bridge_state.total_pnl,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "max_drawdown": 0,
            "uptime": int(uptime),
            "active_symbols": ["BTCUSDT", "ETHUSDT"],
            "tasks_running": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return {
        "status": "disconnected",
        "is_running": False,
        "mode": None,
        "positions": [],
        "equity": 0,
        "daily_pnl": 0,
        "total_trades": 0,
        "win_rate": 0,
        "uptime": 0
    }


async def run_bot_loop(name: str, loop_fn, bot):
    """Bot loop'unu güvenli çalıştır"""
    add_log("info", f"[START] {name} başlatılıyor...")
    try:
        await loop_fn(bot)
    except asyncio.CancelledError:
        add_log("info", f"[STOP] {name} durduruldu")
        raise
    except Exception as e:
        add_log("error", f"[ERROR] {name} hatası: {str(e)}")
        raise


# ============== API Endpoints ==============

@app.get("/")
async def root():
    return {
        "name": "Eclipse Scalper API Bridge - Full Integration",
        "version": "2.0.0",
        "eclipse_available": ECLIPSE_AVAILABLE,
        "guardian_available": GUARDIAN_AVAILABLE,
        "entry_loop_available": ENTRY_LOOP_AVAILABLE,
        "data_loop_available": DATA_LOOP_AVAILABLE,
        "status": "online"
    }


@app.get("/api/status")
async def get_status():
    """Bot durumunu al"""
    return await get_bot_status()


@app.post("/api/auth/connect")
async def connect_exchange(request: ConnectRequest):
    """Binance'e bağlan ve Eclipse bot'u hazırla"""
    try:
        api_key = request.get_api_key()
        api_secret = request.get_api_secret()

        if not api_key or not api_secret:
            raise HTTPException(status_code=400, detail="API key ve secret gerekli")

        add_log("info", f"[CONNECT] Binance baglantisi baslatiliyor... (Testnet: {request.testnet})")

        # Eclipse modülleri mevcut mu?
        if ECLIPSE_AVAILABLE and not request.testnet:
            # Production mode - Eclipse bot kullan
            add_log("info", "[ECLIPSE] Eclipse Scalper modu aktif")

            # Environment variables ayarla
            os.environ["BINANCE_API_KEY"] = api_key
            os.environ["BINANCE_API_SECRET"] = api_secret

            # Eclipse bot oluştur
            bot = EclipseEternal()

            # Config seç (equity'ye göre otomatik seçilecek)
            bot.cfg = MicroConfig() if request.testnet else Config()

            # Exchange bağlantısı yap
            try:
                await bot.ex._ensure_markets_loaded()
                balance = await bot.ex.fetch_balance()
                usdt_balance = _extract_usdt_equity(balance)
                add_log("info", f"[OK] Exchange bağlantısı başarılı - Bakiye: ${usdt_balance:.2f}")

                # State'i güncelle
                bot.state.current_equity = usdt_balance
                bot.state.peak_equity = usdt_balance
                bot.state.start_of_day_equity = usdt_balance

            except Exception as e:
                add_log("error", f"Exchange bağlantı hatası: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

            bridge_state.bot = bot
            bridge_state.is_connected = True
            bridge_state.is_fallback_mode = False

            return {
                "success": True,
                "message": "Eclipse Scalper bağlantısı başarılı",
                "mode": "eclipse",
                "balance": {"USDT": usdt_balance},
                "testnet": request.testnet
            }

        else:
            # Fallback mode - sadece CCXT kullan (Testnet için)
            add_log("info", "[SIGNAL] CCXT fallback modu aktif (Testnet)")

            if not CCXT_AVAILABLE:
                raise HTTPException(status_code=500, detail="CCXT modülü bulunamadı")

            # Windows'ta aiodns DNS çözümlemesi sorunlu olabilir
            # ThreadedResolver kullanarak bu sorunu çözüyoruz
            connector = aiohttp.TCPConnector(
                resolver=aiohttp.resolver.ThreadedResolver(),
                limit=10,
                limit_per_host=5
            )
            session = aiohttp.ClientSession(connector=connector)

            exchange = ccxt.binanceusdm({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'session': session,
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                },
                'timeout': 30000,
            })

            if request.testnet:
                # Binance Futures testnet URL'lerini manuel olarak ayarla
                # CCXT sandbox mode bypass - doğrudan URL güncelleme
                testnet_base = 'https://testnet.binancefuture.com'
                for key in list(exchange.urls['api'].keys()):
                    url = exchange.urls['api'][key]
                    if isinstance(url, str):
                        if 'fapi.binance.com' in url:
                            exchange.urls['api'][key] = url.replace('https://fapi.binance.com', testnet_base)
                        elif 'dapi.binance.com' in url:
                            exchange.urls['api'][key] = url.replace('https://dapi.binance.com', testnet_base)
                # sapi endpoint'lerini de ayarla (yoksa hata verir)
                exchange.urls['api']['sapi'] = testnet_base + '/sapi/v1'
                exchange.urls['api']['sapiV2'] = testnet_base + '/sapi/v2'
                exchange.urls['api']['sapiV3'] = testnet_base + '/sapi/v3'
                exchange.urls['api']['sapiV4'] = testnet_base + '/sapi/v4'
                # Testnet hostname
                exchange.hostname = 'testnet.binancefuture.com'
                add_log("info", "[OK] Binance Futures Testnet URL'leri ayarlandi")

            try:
                add_log("info", "[WAIT] Markets yukleniyor...")
                await exchange.load_markets()
                add_log("info", f"[OK] Markets yuklendi: {len(exchange.markets)} sembol")
            except Exception as me:
                add_log("error", f"Market yukleme hatası: {type(me).__name__}: {str(me)}")
                raise HTTPException(status_code=400, detail=f"Market yukleme hatası: {str(me)}")

            try:
                add_log("info", "[WAIT] Bakiye aliniyor...")
                balance = await exchange.fetch_balance()
                usdt_balance = float((balance.get('total', {}) or {}).get('USDT', 0))
                add_log("info", f"[OK] CCXT bağlantısı başarılı - Bakiye: ${usdt_balance:.2f}")
            except Exception as be:
                add_log("error", f"Bakiye alma hatası: {type(be).__name__}: {str(be)}")
                raise HTTPException(status_code=400, detail=f"Bakiye alma hatası: {str(be)}")

            bridge_state.fallback_exchange = exchange
            bridge_state.is_connected = True
            bridge_state.is_fallback_mode = True

            return {
                "success": True,
                "message": "CCXT bağlantısı başarılı (Fallback mode)",
                "mode": "fallback",
                "balance": {"USDT": usdt_balance},
                "testnet": request.testnet
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[CONNECT ERROR] {error_details}")
        add_log("error", f"Bağlantı hatası: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {str(e)}")


@app.post("/api/bot/start")
async def start_bot(request: BotStartRequest):
    """Eclipse Scalper'ı tam olarak başlat"""

    if not bridge_state.is_connected:
        raise HTTPException(status_code=400, detail="Önce Binance'e bağlanın")

    if bridge_state.is_running:
        raise HTTPException(status_code=400, detail="Bot zaten çalışıyor")

    try:
        add_log("info", f"[START] Bot başlatılıyor... Mod: {request.mode}, Semboller: {request.symbols}")

        # Eclipse mode
        if bridge_state.bot is not None and not bridge_state.is_fallback_mode:
            bot = bridge_state.bot

            # Sembolleri ayarla
            bot.active_symbols = set(request.symbols)

            # Config'i güncelle
            if hasattr(bot.cfg, 'ACTIVE_SYMBOLS'):
                bot.cfg.ACTIVE_SYMBOLS = request.symbols

            # Dry run mode
            if request.dry_run:
                os.environ["SCALPER_DRY_RUN"] = "1"
                add_log("info", "[WARN] DRY RUN modu aktif - Gerçek işlem yapılmayacak")
            else:
                os.environ.pop("SCALPER_DRY_RUN", None)

            # Bot loop'larını başlat
            bridge_state.startup_time = time.time()

            # Core start (arka planda)
            async def core_start_wrapper():
                try:
                    add_log("info", "[ECLIPSE] Eclipse Core başlatılıyor...")
                    await bot.start()
                except asyncio.CancelledError:
                    add_log("info", "Eclipse Core durduruldu")
                except Exception as e:
                    add_log("error", f"Eclipse Core hatası: {str(e)}")

            bridge_state.tasks["core"] = asyncio.create_task(core_start_wrapper())

            # Guardian loop
            if GUARDIAN_AVAILABLE and guardian_loop:
                bridge_state.tasks["guardian"] = asyncio.create_task(
                    run_bot_loop("Guardian", guardian_loop, bot)
                )

            # Data loop
            if DATA_LOOP_AVAILABLE and data_loop:
                bridge_state.tasks["data"] = asyncio.create_task(
                    run_bot_loop("Data Loop", data_loop, bot)
                )

            # Entry loop (data hazır olunca)
            if ENTRY_LOOP_AVAILABLE and entry_loop:
                async def gated_entry_loop():
                    # Data hazır olana kadar bekle
                    add_log("info", "[WAIT] Entry loop data hazır olmasını bekliyor...")
                    try:
                        await asyncio.wait_for(bot.data_ready.wait(), timeout=30.0)
                        add_log("info", "[OK] Data hazır, entry loop başlıyor")
                    except asyncio.TimeoutError:
                        add_log("warn", "[WARN] Data timeout, entry loop yine de başlıyor")
                    await entry_loop(bot)

                bridge_state.tasks["entry"] = asyncio.create_task(
                    run_bot_loop("Entry Loop", lambda b: gated_entry_loop(), bot)
                )

            # Status update loop (WebSocket için)
            async def status_update_loop():
                while bridge_state.is_running:
                    try:
                        status = await get_bot_status()
                        await manager.broadcast({
                            "type": "status",
                            "data": status
                        })
                    except:
                        pass
                    await asyncio.sleep(5)

            bridge_state.tasks["status_updater"] = asyncio.create_task(status_update_loop())

            # Signal monitor loop - strateji sinyallerini frontend'e gonder
            async def signal_monitor_loop():
                strategy = getattr(bot, "strategy", None)
                last_signals = {}

                while bridge_state.is_running:
                    try:
                        if strategy and hasattr(strategy, "generate_signal"):
                            for symbol in bot.active_symbols:
                                try:
                                    result = strategy.generate_signal(bot, symbol)
                                    if result and len(result) >= 3:
                                        long_ok, short_ok, confidence = result[0], result[1], result[2]

                                        # Signal degisti mi?
                                        sig_key = f"{symbol}_{long_ok}_{short_ok}_{round(confidence, 2)}"
                                        if sig_key != last_signals.get(symbol):
                                            last_signals[symbol] = sig_key

                                            # Log ve broadcast
                                            side = "LONG" if long_ok else ("SHORT" if short_ok else "BEKLE")
                                            conf_pct = confidence * 100

                                            add_log("info", f"[SIGNAL] {symbol}: {side} | Guven: {conf_pct:.1f}% | Giris: {'EVET' if conf_pct >= 60 else 'HAYIR'}")

                                            await manager.broadcast({
                                                "type": "signal_update",
                                                "data": {
                                                    "symbol": symbol,
                                                    "long": long_ok,
                                                    "short": short_ok,
                                                    "confidence": confidence,
                                                    "confidence_pct": conf_pct,
                                                    "side": side,
                                                    "will_enter": conf_pct >= 60,
                                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                                }
                                            })
                                except Exception as e:
                                    pass
                    except Exception as e:
                        pass
                    await asyncio.sleep(10)  # Her 10 saniyede bir kontrol

            bridge_state.tasks["signal_monitor"] = asyncio.create_task(signal_monitor_loop())

            bridge_state.is_running = True

            add_log("info", f"[OK] Eclipse Scalper başlatıldı! Çalışan task'ler: {list(bridge_state.tasks.keys())}")

            await manager.broadcast({
                "type": "bot_started",
                "symbols": request.symbols,
                "mode": "eclipse",
                "dry_run": request.dry_run,
                "tasks": list(bridge_state.tasks.keys())
            })

            return {
                "success": True,
                "message": "Eclipse Scalper başlatıldı",
                "mode": "eclipse",
                "symbols": request.symbols,
                "dry_run": request.dry_run,
                "tasks_started": list(bridge_state.tasks.keys())
            }

        # Fallback mode
        else:
            add_log("info", "[SIGNAL] Fallback mode bot başlatılıyor...")
            bridge_state.is_running = True
            bridge_state.startup_time = time.time()

            await manager.broadcast({
                "type": "bot_started",
                "symbols": request.symbols,
                "mode": "fallback",
                "dry_run": request.dry_run
            })

            return {
                "success": True,
                "message": "Fallback bot başlatıldı",
                "mode": "fallback",
                "symbols": request.symbols,
                "dry_run": request.dry_run
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        add_log("error", f"Bot başlatma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/stop")
async def stop_bot():
    """Botu durdur"""
    if not bridge_state.is_running:
        raise HTTPException(status_code=400, detail="Bot zaten durmuş")

    try:
        add_log("info", "[STOP] Bot durduruluyor...")

        # Eclipse bot shutdown
        if bridge_state.bot is not None and not bridge_state.is_fallback_mode:
            bot = bridge_state.bot

            # Shutdown event'i tetikle
            shutdown_ev = getattr(bot, "_shutdown", None)
            if shutdown_ev:
                shutdown_ev.set()

            # Shutdown metodunu çağır
            if hasattr(bot, "shutdown"):
                try:
                    await asyncio.wait_for(bot.shutdown(), timeout=10.0)
                except asyncio.TimeoutError:
                    add_log("warn", "Bot shutdown timeout")

        # Tüm task'leri iptal et
        for name, task in list(bridge_state.tasks.items()):
            if task and not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            add_log("info", f"Task durduruldu: {name}")

        bridge_state.tasks.clear()
        bridge_state.is_running = False

        add_log("info", "[OK] Bot durduruldu")

        await manager.broadcast({"type": "bot_stopped"})

        return {"success": True, "message": "Bot durduruldu"}

    except Exception as e:
        add_log("error", f"Bot durdurma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trade")
async def execute_trade(request: ManualTradeRequest):
    """Manuel işlem yap"""
    if not bridge_state.is_connected:
        raise HTTPException(status_code=400, detail="Önce Binance'e bağlanın")

    try:
        # Exchange seç
        exchange = None
        if bridge_state.bot and not bridge_state.is_fallback_mode:
            exchange = bridge_state.bot.ex
        elif bridge_state.fallback_exchange:
            exchange = bridge_state.fallback_exchange

        if not exchange:
            raise HTTPException(status_code=400, detail="Exchange bağlantısı yok")

        symbol = request.symbol
        side = request.side.lower()
        amount = request.amount

        add_log("info", f"[ORDER] Manuel işlem: {side.upper()} {amount} {symbol}")

        # Market order
        if side == "buy":
            order = await exchange.create_market_buy_order(symbol, amount)
        else:
            order = await exchange.create_market_sell_order(symbol, amount)

        price = order.get("average") or order.get("price") or 0

        # Trade kaydı
        trade_record = {
            "id": order.get("id"),
            "symbol": symbol,
            "side": side.upper(),
            "amount": amount,
            "price": price,
            "cost": float(amount) * float(price),
            "status": order.get("status"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        bridge_state.trades.insert(0, trade_record)

        add_log("trade", f"[OK] İşlem başarılı: {side.upper()} {amount} {symbol} @ ${price:.2f}")

        await manager.broadcast({
            "type": "new_trade",
            "data": trade_record
        })

        return {
            "success": True,
            "message": f"{side.upper()} {amount} {symbol} işlemi başarılı",
            "order": trade_record
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        add_log("error", f"İşlem hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions")
async def get_positions():
    """Açık pozisyonları al"""
    status = await get_bot_status()
    return {
        "positions": status.get("positions", []),
        "count": status.get("position_count", 0)
    }


@app.get("/api/trades")
async def get_trades():
    """İşlem geçmişini al"""
    # Eclipse bot'tan
    if bridge_state.bot and not bridge_state.is_fallback_mode:
        state = getattr(bridge_state.bot, "state", None)
        if state:
            return {
                "trades": bridge_state.trades,
                "count": len(bridge_state.trades),
                "total_trades": getattr(state, "total_trades", 0),
                "total_wins": getattr(state, "total_wins", 0),
                "win_rate": getattr(state, "win_rate", 0)
            }

    # Fallback mode
    return {
        "trades": bridge_state.trades,
        "count": len(bridge_state.trades),
        "total_pnl": bridge_state.total_pnl,
        "win_count": bridge_state.win_count,
        "loss_count": bridge_state.loss_count
    }


@app.get("/api/balance")
async def get_balance():
    """Bakiye bilgisini al"""
    try:
        exchange = None
        if bridge_state.bot and not bridge_state.is_fallback_mode:
            exchange = bridge_state.bot.ex
        elif bridge_state.fallback_exchange:
            exchange = bridge_state.fallback_exchange

        if not exchange:
            raise HTTPException(status_code=400, detail="Bağlı değil")

        balance = await exchange.fetch_balance()
        usdt_total = _extract_usdt_equity(balance)
        usdt_free = float((balance.get("free", {}) or {}).get("USDT", 0))
        usdt_used = float((balance.get("used", {}) or {}).get("USDT", 0))

        return {
            "total": usdt_total,
            "free": usdt_free,
            "used": usdt_used,
            "currency": "USDT"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Bot loglarını al"""
    return {
        "logs": bridge_state.logs[-limit:],
        "count": len(bridge_state.logs)
    }


@app.delete("/api/logs")
async def clear_logs():
    """Logları temizle"""
    bridge_state.logs.clear()
    return {"success": True, "message": "Loglar temizlendi"}


# ============== WebSocket Endpoint ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time güncellemeler için WebSocket"""
    await manager.connect(websocket)

    try:
        # İlk durum gönder
        status = await get_bot_status()
        await websocket.send_json({
            "type": "status",
            "data": status
        })

        # Son logları gönder
        await websocket.send_json({
            "type": "logs_init",
            "data": bridge_state.logs[-50:]
        })

        # Mesaj döngüsü
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                elif data.get("type") == "get_status":
                    status = await get_bot_status()
                    await websocket.send_json({
                        "type": "status",
                        "data": status
                    })

                elif data.get("type") == "get_logs":
                    await websocket.send_json({
                        "type": "logs",
                        "data": bridge_state.logs[-100:]
                    })

            except asyncio.TimeoutError:
                # Periyodik status update
                if bridge_state.is_running:
                    status = await get_bot_status()
                    await websocket.send_json({
                        "type": "status",
                        "data": status
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============== Startup/Shutdown ==============

@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("ECLIPSE SCALPER API BRIDGE - FULL INTEGRATION")
    print(f"   Eclipse Available: {ECLIPSE_AVAILABLE}")
    print(f"   Guardian Available: {GUARDIAN_AVAILABLE}")
    print(f"   Entry Loop Available: {ENTRY_LOOP_AVAILABLE}")
    print(f"   Data Loop Available: {DATA_LOOP_AVAILABLE}")
    print("=" * 60)
    add_log("info", "API Bridge baslatildi")


@app.on_event("shutdown")
async def shutdown_event():
    add_log("info", "API Bridge kapatılıyor...")

    if bridge_state.is_running:
        try:
            await stop_bot()
        except:
            pass

    # Exchange bağlantılarını kapat
    if bridge_state.bot and hasattr(bridge_state.bot, 'ex'):
        try:
            await bridge_state.bot.ex.close()
        except:
            pass

    if bridge_state.fallback_exchange:
        try:
            await bridge_state.fallback_exchange.close()
        except:
            pass

    print("API Bridge kapatıldı")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
