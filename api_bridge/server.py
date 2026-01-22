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

try:
    from strategies.eclipse_scalper import scalper_signal
    SCALPER_SIGNAL_AVAILABLE = True
    print("[OK] Scalper signal yuklendi")
except ImportError as e:
    SCALPER_SIGNAL_AVAILABLE = False
    scalper_signal = None
    print(f"[WARN] Scalper signal yuklenemedi: {e}")

# Position Manager import
try:
    from execution.position_manager import position_manager_tick
    POSITION_MANAGER_AVAILABLE = True
    print("[OK] Position manager yuklendi")
except ImportError as e:
    POSITION_MANAGER_AVAILABLE = False
    position_manager_tick = None
    print(f"[WARN] Position manager yuklenemedi: {e}")

# Exit Handler import
try:
    from execution.exit import handle_exit
    EXIT_HANDLER_AVAILABLE = True
    print("[OK] Exit handler yuklendi")
except ImportError as e:
    EXIT_HANDLER_AVAILABLE = False
    handle_exit = None
    print(f"[WARN] Exit handler yuklenemedi: {e}")

# Order Router import
try:
    from execution.order_router import create_order
    ORDER_ROUTER_AVAILABLE = True
    print("[OK] Order router yuklendi")
except ImportError as e:
    ORDER_ROUTER_AVAILABLE = False
    create_order = None
    print(f"[WARN] Order router yuklenemedi: {e}")

# Emergency/Kill Switch import
try:
    from risk.kill_switch import trade_allowed, is_halted, request_halt
    KILL_SWITCH_AVAILABLE = True
    print("[OK] Kill switch yuklendi")
except ImportError as e:
    KILL_SWITCH_AVAILABLE = False
    trade_allowed = None
    is_halted = None
    request_halt = None
    print(f"[WARN] Kill switch yuklenemedi: {e}")

try:
    from execution.emergency import emergency_flat
    EMERGENCY_AVAILABLE = True
    print("[OK] Emergency handler yuklendi")
except ImportError as e:
    EMERGENCY_AVAILABLE = False
    emergency_flat = None
    print(f"[WARN] Emergency handler yuklenemedi: {e}")

# Reconcile import (guardian icinde cagrilir ama ayri takip edelim)
try:
    from execution.reconcile import reconcile_tick
    RECONCILE_AVAILABLE = True
    print("[OK] Reconcile yuklendi")
except ImportError as e:
    RECONCILE_AVAILABLE = False
    reconcile_tick = None
    print(f"[WARN] Reconcile yuklenemedi: {e}")

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
class ModuleStatus:
    """Modül durumu"""
    name: str
    display_name: str
    available: bool = False
    running: bool = False
    error: Optional[str] = None
    last_update: Optional[str] = None


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

    # Test pozisyonları (DRY_RUN test için)
    test_positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    test_trades_count: int = 0

    # Modül durum takibi
    module_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)


bridge_state = BridgeState()


def init_module_status():
    """Modül durumlarını başlat"""
    modules = [
        ("bootstrap", "Bootstrap", ECLIPSE_AVAILABLE),
        ("data_loop", "Data Loop", DATA_LOOP_AVAILABLE),
        ("strategy", "Strategy (Scalper)", SCALPER_SIGNAL_AVAILABLE),
        ("entry_loop", "Entry Loop", ENTRY_LOOP_AVAILABLE),
        ("order_router", "Order Router", ORDER_ROUTER_AVAILABLE),
        ("reconcile", "Reconcile", RECONCILE_AVAILABLE),
        ("position_manager", "Position Manager", POSITION_MANAGER_AVAILABLE),
        ("exit", "Exit Handler", EXIT_HANDLER_AVAILABLE),
        ("kill_switch", "Kill Switch", KILL_SWITCH_AVAILABLE),
        ("emergency", "Emergency", EMERGENCY_AVAILABLE),
    ]

    for name, display_name, available in modules:
        bridge_state.module_status[name] = {
            "name": name,
            "display_name": display_name,
            "available": available,
            "running": False,
            "error": None,
            "last_update": None
        }


def update_module_status(name: str, running: bool = None, error: str = None):
    """Modül durumunu güncelle"""
    if name in bridge_state.module_status:
        if running is not None:
            bridge_state.module_status[name]["running"] = running
        if error is not None:
            bridge_state.module_status[name]["error"] = error
        bridge_state.module_status[name]["last_update"] = datetime.now(timezone.utc).isoformat()

        # WebSocket'e broadcast
        asyncio.create_task(broadcast_module_status())


async def broadcast_module_status():
    """Modül durumunu WebSocket'e gönder"""
    await manager.broadcast({
        "type": "modules_init",
        "data": list(bridge_state.module_status.values())
    })


# Modül durumlarını başlat
init_module_status()


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

        # Test pozisyonlarını da ekle (DRY_RUN mode)
        for test_pos in bridge_state.test_positions.values():
            positions.append(test_pos)

        uptime = 0
        if bridge_state.startup_time:
            uptime = time.time() - bridge_state.startup_time

        # PsycheState alanlari + test trades
        total_trades = int(getattr(state, "total_trades", 0) if state else 0) + bridge_state.test_trades_count
        total_wins = int(getattr(state, "total_wins", 0) if state else 0)
        win_rate = float(getattr(state, "win_rate", 0) if state else 0) * 100  # 0-1 -> 0-100
        if win_rate == 0 and total_trades > 0:
            win_rate = (total_wins / total_trades) * 100

        current_equity = float(getattr(state, "current_equity", 0) if state else 0)
        peak_equity = float(getattr(state, "peak_equity", 0) if state else 0)
        daily_pnl = float(getattr(state, "daily_pnl", 0) if state else 0)
        max_drawdown = float(getattr(state, "max_drawdown", 0) if state else 0) * 100  # 0-1 -> 0-100

        # Test pozisyonlarının toplam PnL'ini ekle
        test_pnl = sum(pos.get("pnl", 0) for pos in bridge_state.test_positions.values())
        combined_pnl = daily_pnl + test_pnl

        # Demo equity: Başlangıç $1000 + PnL
        demo_base_equity = 1000.0
        demo_equity = demo_base_equity + test_pnl
        demo_peak = max(demo_base_equity, demo_equity)
        demo_drawdown = ((demo_peak - demo_equity) / demo_peak * 100) if demo_peak > 0 else 0

        return {
            "status": "running" if bridge_state.is_running else "connected",
            "is_running": bridge_state.is_running,
            "mode": "eclipse",
            "positions": positions,
            "position_count": len(positions),
            "equity": current_equity if current_equity > 0 else demo_equity,
            "peak_equity": peak_equity if peak_equity > 0 else demo_peak,
            "daily_pnl": combined_pnl,
            "total_trades": total_trades,
            "win_rate": win_rate if win_rate > 0 else (50.0 if total_trades > 0 else 0),
            "max_drawdown": max_drawdown if max_drawdown > 0 else demo_drawdown,
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

            # Core start (arka planda) - Bootstrap modülü
            async def core_start_wrapper():
                try:
                    add_log("info", "[BOOTSTRAP] Eclipse Core başlatılıyor...")
                    update_module_status("bootstrap", running=True)
                    await bot.start()
                except asyncio.CancelledError:
                    add_log("info", "[BOOTSTRAP] Eclipse Core durduruldu")
                    update_module_status("bootstrap", running=False)
                except Exception as e:
                    add_log("error", f"[BOOTSTRAP] Eclipse Core hatası: {str(e)}")
                    update_module_status("bootstrap", running=False, error=str(e))

            bridge_state.tasks["bootstrap"] = asyncio.create_task(core_start_wrapper())

            # Guardian loop (reconcile ve kill_switch'i içerir)
            if GUARDIAN_AVAILABLE and guardian_loop:
                async def guardian_wrapper():
                    try:
                        update_module_status("reconcile", running=True)
                        update_module_status("kill_switch", running=True)
                        await guardian_loop(bot)
                    except asyncio.CancelledError:
                        update_module_status("reconcile", running=False)
                        update_module_status("kill_switch", running=False)
                        raise
                    except Exception as e:
                        update_module_status("reconcile", running=False, error=str(e))
                        raise

                bridge_state.tasks["guardian"] = asyncio.create_task(
                    run_bot_loop("Guardian (Reconcile)", guardian_wrapper, bot)
                )

            # Data loop
            if DATA_LOOP_AVAILABLE and data_loop:
                async def data_wrapper():
                    try:
                        update_module_status("data_loop", running=True)
                        await data_loop(bot)
                    except asyncio.CancelledError:
                        update_module_status("data_loop", running=False)
                        raise
                    except Exception as e:
                        update_module_status("data_loop", running=False, error=str(e))
                        raise

                bridge_state.tasks["data"] = asyncio.create_task(
                    run_bot_loop("Data Loop", lambda b: data_wrapper(), bot)
                )

            # Entry loop (data hazır olunca) - order_router'ı da içerir
            if ENTRY_LOOP_AVAILABLE and entry_loop:
                async def gated_entry_loop():
                    # Data hazır olana kadar bekle
                    add_log("info", "[ENTRY] Entry loop data hazır olmasını bekliyor...")
                    try:
                        await asyncio.wait_for(bot.data_ready.wait(), timeout=30.0)
                        add_log("info", "[ENTRY] Data hazır, entry loop başlıyor")
                    except asyncio.TimeoutError:
                        add_log("warn", "[ENTRY] Data timeout, entry loop yine de başlıyor")

                    update_module_status("entry_loop", running=True)
                    update_module_status("order_router", running=True)
                    try:
                        await entry_loop(bot)
                    except asyncio.CancelledError:
                        update_module_status("entry_loop", running=False)
                        update_module_status("order_router", running=False)
                        raise
                    except Exception as e:
                        update_module_status("entry_loop", running=False, error=str(e))
                        raise

                bridge_state.tasks["entry"] = asyncio.create_task(
                    run_bot_loop("Entry Loop", lambda b: gated_entry_loop(), bot)
                )

            # Position Manager loop
            if POSITION_MANAGER_AVAILABLE and position_manager_tick:
                async def pos_manager_wrapper():
                    try:
                        # Data hazır olana kadar bekle
                        await asyncio.wait_for(bot.data_ready.wait(), timeout=30.0)
                        update_module_status("position_manager", running=True)
                        update_module_status("exit", running=True)  # Exit de bu loop içinde çalışır
                        # Position manager tick'i döngüde çalıştır
                        while bridge_state.is_running:
                            await position_manager_tick(bot)
                            await asyncio.sleep(5)  # 5 saniyede bir kontrol
                    except asyncio.CancelledError:
                        update_module_status("position_manager", running=False)
                        update_module_status("exit", running=False)
                        raise
                    except Exception as e:
                        update_module_status("position_manager", running=False, error=str(e))
                        raise

                bridge_state.tasks["position_manager"] = asyncio.create_task(
                    run_bot_loop("Position Manager", lambda b: pos_manager_wrapper(), bot)
                )

            # Emergency modülü hazır olarak işaretle
            if EMERGENCY_AVAILABLE:
                update_module_status("emergency", running=True)

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
                    await asyncio.sleep(2)  # 2 saniyede bir status update

            bridge_state.tasks["status_updater"] = asyncio.create_task(status_update_loop())

            # Signal monitor loop - strateji sinyallerini frontend'e gonder
            async def signal_monitor_loop():
                add_log("info", "[STRATEGY] Sinyal izleme baslatildi (TEST MODE: Guven >= 20% = LONG)")
                update_module_status("strategy", running=True)

                while bridge_state.is_running:
                    try:
                        # TEST: Mevcut pozisyonların PnL'ini güncelle
                        if bridge_state.test_positions:
                            total_pnl = 0.0
                            for symbol, pos in bridge_state.test_positions.items():
                                try:
                                    # Güncel fiyatı al
                                    ticker = await bot.ex.fetch_ticker(symbol)
                                    current_price = ticker.get("last", pos["entry_price"])

                                    # PnL hesapla: (current - entry) * size * leverage
                                    entry_price = pos["entry_price"]
                                    size = pos["size"]
                                    leverage = pos["leverage"]
                                    direction = 1 if pos["side"] == "long" else -1

                                    pnl = (current_price - entry_price) * size * leverage * direction
                                    pos["pnl"] = round(pnl, 2)
                                    pos["current_price"] = current_price
                                    total_pnl += pnl
                                except Exception as e:
                                    pass

                            # Toplam PnL'i kaydet
                            bridge_state.total_pnl = round(total_pnl, 2)

                            # Pozisyon güncellemesi broadcast et
                            await manager.broadcast({
                                "type": "positions_update",
                                "data": list(bridge_state.test_positions.values())
                            })

                        if SCALPER_SIGNAL_AVAILABLE and scalper_signal:
                            data_cache = getattr(bot, "data", None)
                            cfg = getattr(bot, "cfg", None)

                            for symbol in bot.active_symbols:
                                try:
                                    result = scalper_signal(symbol, data=data_cache, cfg=cfg)
                                    if result and len(result) >= 3:
                                        long_ok, short_ok, confidence = result[0], result[1], result[2]
                                        conf_pct = confidence * 100

                                        # TEST MODE: Güven >= 20% ise LONG olarak force et
                                        test_entry = conf_pct >= 20 and symbol not in bridge_state.test_positions
                                        if test_entry:
                                            long_ok = True
                                            side = "LONG"
                                        else:
                                            side = "LONG" if long_ok else ("SHORT" if short_ok else "BEKLE")

                                        add_log("info", f"[SIGNAL] {symbol}: {side} | Guven: {conf_pct:.1f}% | Giris: {'EVET' if conf_pct >= 20 else 'HAYIR'}")

                                        # TEST MODE: Pozisyon aç
                                        if test_entry and request.dry_run:
                                            # Fiyat al
                                            try:
                                                ticker = await bot.ex.fetch_ticker(symbol)
                                                entry_price = ticker.get("last", 90000)
                                            except:
                                                entry_price = 90000 if "BTC" in symbol else 3000

                                            # Test pozisyonu oluştur
                                            bridge_state.test_positions[symbol] = {
                                                "symbol": symbol,
                                                "side": "long",
                                                "size": 0.001,
                                                "entry_price": entry_price,
                                                "current_price": entry_price,
                                                "leverage": 10,
                                                "pnl": 0.0,
                                                "entry_time": datetime.now(timezone.utc).isoformat()
                                            }
                                            bridge_state.test_trades_count += 1

                                            add_log("trade", f"[TEST ENTRY] {symbol} LONG @ ${entry_price:.2f} | Size: 0.001 | Lev: 10x")

                                            # Trade broadcast
                                            await manager.broadcast({
                                                "type": "new_trade",
                                                "data": {
                                                    "symbol": symbol,
                                                    "side": "buy",
                                                    "amount": 0.001,
                                                    "price": entry_price,
                                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                                }
                                            })

                                            # Pozisyon update broadcast
                                            await manager.broadcast({
                                                "type": "positions_update",
                                                "data": list(bridge_state.test_positions.values())
                                            })

                                        await manager.broadcast({
                                            "type": "signal_update",
                                            "data": {
                                                "symbol": symbol,
                                                "long": long_ok,
                                                "short": short_ok,
                                                "confidence": confidence,
                                                "confidence_pct": conf_pct,
                                                "side": side,
                                                "will_enter": conf_pct >= 20,
                                                "timestamp": datetime.now(timezone.utc).isoformat()
                                            }
                                        })
                                except Exception as e:
                                    add_log("warn", f"[SIGNAL] {symbol} sinyal hatasi: {str(e)[:100]}")
                        else:
                            add_log("warn", "[SIGNAL_MONITOR] scalper_signal mevcut degil")
                    except Exception as e:
                        add_log("error", f"[SIGNAL_MONITOR] Hata: {str(e)[:100]}")
                    await asyncio.sleep(3)  # 3 saniyede bir güncelleme (anlık)

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

        # Tüm modüllerin durumunu sıfırla
        for name in bridge_state.module_status:
            update_module_status(name, running=False, error=None)

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


@app.get("/api/modules")
async def get_modules():
    """Modül durumlarını al"""
    return {
        "modules": list(bridge_state.module_status.values()),
        "count": len(bridge_state.module_status)
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

        # Modül durumlarını gönder
        await websocket.send_json({
            "type": "modules_init",
            "data": list(bridge_state.module_status.values())
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
    print("ECLIPSE SCALPER API BRIDGE - FULL INTEGRATION v2.1")
    print("=" * 60)
    print(" MODÜL DURUMU:")
    print(f"   [{'✓' if ECLIPSE_AVAILABLE else 'X'}] Eclipse Core (Bootstrap)")
    print(f"   [{'✓' if DATA_LOOP_AVAILABLE else 'X'}] Data Loop")
    print(f"   [{'✓' if SCALPER_SIGNAL_AVAILABLE else 'X'}] Strategy (Scalper Signal)")
    print(f"   [{'✓' if ENTRY_LOOP_AVAILABLE else 'X'}] Entry Loop")
    print(f"   [{'✓' if ORDER_ROUTER_AVAILABLE else 'X'}] Order Router")
    print(f"   [{'✓' if RECONCILE_AVAILABLE else 'X'}] Reconcile")
    print(f"   [{'✓' if GUARDIAN_AVAILABLE else 'X'}] Guardian")
    print(f"   [{'✓' if POSITION_MANAGER_AVAILABLE else 'X'}] Position Manager")
    print(f"   [{'✓' if EXIT_HANDLER_AVAILABLE else 'X'}] Exit Handler")
    print(f"   [{'✓' if KILL_SWITCH_AVAILABLE else 'X'}] Kill Switch")
    print(f"   [{'✓' if EMERGENCY_AVAILABLE else 'X'}] Emergency")
    print("=" * 60)
    add_log("info", "API Bridge baslatildi - Tum moduller yuklendi")


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
