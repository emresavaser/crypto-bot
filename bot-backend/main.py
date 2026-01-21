"""
CryptoBot Backend - FastAPI Server
Bu dosya Next.js frontend ile Python bot arasındaki köprüyü sağlar.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
from datetime import datetime

# Bot modüllerini import et
from bot.manager import BotManager
from bot.config import BotConfig

app = FastAPI(title="CryptoBot API", version="1.0.0")

# CORS ayarları - Next.js frontend'in bağlanabilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot manager instance
bot_manager = BotManager()

# WebSocket bağlantılarını takip et
active_connections: List[WebSocket] = []


# ============== Pydantic Modeller ==============

class ApiCredentials(BaseModel):
    api_key: str
    api_secret: str
    is_testnet: bool = True


class BotConfigRequest(BaseModel):
    symbol: str = "BTCUSDT"
    strategy: str = "rsi"  # rsi, macd, sma, custom
    amount: float = 0.001
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    # Strateji parametreleri
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    sma_short: int = 10
    sma_long: int = 50


class BotStatusResponse(BaseModel):
    is_running: bool
    strategy: str
    symbol: str
    start_time: Optional[str]
    total_trades: int
    profit: float
    win_rate: float
    last_signal: Optional[str]
    last_price: Optional[float]


class TradeSignal(BaseModel):
    type: str  # BUY, SELL, HOLD
    price: float
    timestamp: str
    reason: str
    confidence: float


# ============== REST API Endpoints ==============

@app.get("/")
async def root():
    return {"message": "CryptoBot API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/auth/connect")
async def connect_binance(credentials: ApiCredentials):
    """Binance API'ye bağlan ve doğrula"""
    try:
        success = await bot_manager.connect(
            api_key=credentials.api_key,
            api_secret=credentials.api_secret,
            testnet=credentials.is_testnet
        )
        if success:
            return {"success": True, "message": "Binance bağlantısı başarılı"}
        else:
            raise HTTPException(status_code=401, detail="API bağlantısı başarısız")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/start")
async def start_bot(config: BotConfigRequest):
    """Botu başlat"""
    try:
        bot_config = BotConfig(
            symbol=config.symbol,
            strategy=config.strategy,
            amount=config.amount,
            stop_loss=config.stop_loss,
            take_profit=config.take_profit,
            rsi_period=config.rsi_period,
            rsi_oversold=config.rsi_oversold,
            rsi_overbought=config.rsi_overbought,
            sma_short=config.sma_short,
            sma_long=config.sma_long,
        )

        success = await bot_manager.start(bot_config)

        if success:
            # Tüm bağlı client'lara bildir
            await broadcast_message({
                "type": "bot_started",
                "config": config.dict()
            })
            return {"success": True, "message": "Bot başlatıldı"}
        else:
            raise HTTPException(status_code=400, detail="Bot başlatılamadı")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/stop")
async def stop_bot():
    """Botu durdur"""
    try:
        success = await bot_manager.stop()

        if success:
            await broadcast_message({"type": "bot_stopped"})
            return {"success": True, "message": "Bot durduruldu"}
        else:
            raise HTTPException(status_code=400, detail="Bot durdurulamadı")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bot/status", response_model=BotStatusResponse)
async def get_bot_status():
    """Bot durumunu getir"""
    status = bot_manager.get_status()
    return BotStatusResponse(**status)


@app.get("/api/bot/trades")
async def get_bot_trades(limit: int = 50):
    """Bot tarafından yapılan işlemleri getir"""
    trades = bot_manager.get_trades(limit)
    return {"trades": trades}


@app.get("/api/bot/signals")
async def get_recent_signals(limit: int = 20):
    """Son sinyalleri getir"""
    signals = bot_manager.get_signals(limit)
    return {"signals": signals}


@app.post("/api/bot/config")
async def update_config(config: BotConfigRequest):
    """Bot ayarlarını güncelle (çalışırken)"""
    try:
        bot_config = BotConfig(**config.dict())
        success = await bot_manager.update_config(bot_config)

        if success:
            await broadcast_message({
                "type": "config_updated",
                "config": config.dict()
            })
            return {"success": True, "message": "Ayarlar güncellendi"}
        else:
            raise HTTPException(status_code=400, detail="Ayarlar güncellenemedi")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== WebSocket Endpoint ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Real-time iletişim için WebSocket endpoint.
    Frontend bu endpoint'e bağlanarak anlık güncellemeler alır:
    - Bot durumu değişiklikleri
    - Yeni trade sinyalleri
    - Fiyat güncellemeleri
    - İşlem bildirimleri
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        # İlk bağlantıda mevcut durumu gönder
        status = bot_manager.get_status()
        await websocket.send_json({
            "type": "initial_status",
            "data": status
        })

        while True:
            # Client'tan mesaj bekle
            data = await websocket.receive_text()
            message = json.loads(data)

            # Mesaj tipine göre işle
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            elif message.get("type") == "get_status":
                status = bot_manager.get_status()
                await websocket.send_json({
                    "type": "status_update",
                    "data": status
                })

    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_message(message: dict):
    """Tüm bağlı WebSocket client'larına mesaj gönder"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass


# Bot manager'ın sinyal callback'i
async def on_signal(signal: dict):
    """Bot yeni bir sinyal ürettiğinde çağrılır"""
    await broadcast_message({
        "type": "new_signal",
        "data": signal
    })


async def on_trade(trade: dict):
    """Bot bir işlem yaptığında çağrılır"""
    await broadcast_message({
        "type": "new_trade",
        "data": trade
    })


# Bot manager callback'lerini ayarla
bot_manager.on_signal = on_signal
bot_manager.on_trade = on_trade


# ============== Startup/Shutdown ==============

@app.on_event("startup")
async def startup_event():
    print("CryptoBot API başlatılıyor...")


@app.on_event("shutdown")
async def shutdown_event():
    print("CryptoBot API kapatılıyor...")
    await bot_manager.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
