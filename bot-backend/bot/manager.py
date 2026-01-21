"""
Bot Manager - Ana Bot Yönetim Sınıfı

██████████████████████████████████████████████████████████████████████████████
█  SENİN PYTHON KODLARINI BURAYA ENTEGRE EDECEKSIN                           █
█  Bu dosya bot mantığının merkezi - strateji çalıştırma, işlem yapma vs.    █
██████████████████████████████████████████████████████████████████████████████
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager

from .config import BotConfig
from .strategies import get_strategy


class BotManager:
    """
    Ana bot yönetim sınıfı.

    YAPILACAKLAR:
    1. Kendi Binance bağlantı kodlarını buraya ekle
    2. Strateji çalıştırma mantığını ekle
    3. İşlem (trade) mantığını ekle
    4. Risk yönetimi ekle
    """

    def __init__(self):
        # Binance client
        self.client: Optional[Client] = None
        self.async_client: Optional[AsyncClient] = None
        self.socket_manager: Optional[BinanceSocketManager] = None

        # Bot durumu
        self.is_running: bool = False
        self.config: Optional[BotConfig] = None
        self.start_time: Optional[datetime] = None

        # İstatistikler
        self.total_trades: int = 0
        self.winning_trades: int = 0
        self.profit: float = 0.0
        self.trades: List[Dict] = []
        self.signals: List[Dict] = []

        # Son durum
        self.last_signal: Optional[str] = None
        self.last_price: Optional[float] = None

        # Callback'ler (main.py'den ayarlanacak)
        self.on_signal: Optional[Callable] = None
        self.on_trade: Optional[Callable] = None

        # Background task
        self._task: Optional[asyncio.Task] = None

    async def connect(self, api_key: str, api_secret: str, testnet: bool = True) -> bool:
        """
        Binance API'ye bağlan.

        ████████████████████████████████████████████████████████████████
        █  BURAYA KENDİ BINANCE BAĞLANTI KODLARINI EKLE                █
        ████████████████████████████████████████████████████████████████
        """
        try:
            if testnet:
                self.client = Client(
                    api_key,
                    api_secret,
                    testnet=True
                )
                # Testnet base URL
                self.client.API_URL = 'https://testnet.binance.vision/api'
            else:
                self.client = Client(api_key, api_secret)

            # Bağlantıyı test et
            account = self.client.get_account()
            print(f"Binance bağlantısı başarılı. Bakiye sayısı: {len(account['balances'])}")

            # Async client oluştur (WebSocket için)
            self.async_client = await AsyncClient.create(api_key, api_secret, testnet=testnet)
            self.socket_manager = BinanceSocketManager(self.async_client)

            return True

        except Exception as e:
            print(f"Binance bağlantı hatası: {e}")
            return False

    async def start(self, config: BotConfig) -> bool:
        """
        Botu başlat.

        ████████████████████████████████████████████████████████████████
        █  BURAYA BOT BAŞLATMA KODLARINI EKLE                          █
        █  - Strateji seçimi                                           █
        █  - Fiyat takibi başlatma                                     █
        █  - Ana döngüyü başlatma                                      █
        ████████████████████████████████████████████████████████████████
        """
        if self.is_running:
            return False

        if not self.client:
            print("Önce Binance'e bağlanmalısınız!")
            return False

        self.config = config
        self.is_running = True
        self.start_time = datetime.now()

        # Stratejiyi al
        strategy = get_strategy(config.strategy)

        # Ana bot döngüsünü başlat
        self._task = asyncio.create_task(self._run_loop(strategy))

        print(f"Bot başlatıldı: {config.symbol} - {config.strategy}")
        return True

    async def stop(self) -> bool:
        """Botu durdur"""
        if not self.is_running:
            return False

        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        print("Bot durduruldu")
        return True

    async def _run_loop(self, strategy):
        """
        Ana bot döngüsü.

        ████████████████████████████████████████████████████████████████
        █  BURAYA ANA BOT DÖNGÜSÜNÜ EKLE                               █
        █  - Fiyat verisi al                                           █
        █  - Strateji sinyali hesapla                                  █
        █  - Sinyal varsa işlem yap                                    █
        ████████████████████████████████████████████████████████████████
        """
        print(f"Bot döngüsü başladı: {self.config.symbol}")

        while self.is_running:
            try:
                # 1. Fiyat verisi al
                klines = self.client.get_klines(
                    symbol=self.config.symbol,
                    interval=self.config.interval,
                    limit=100
                )

                # Son fiyatı kaydet
                self.last_price = float(klines[-1][4])  # Close price

                # 2. Strateji sinyali hesapla
                signal = strategy.calculate(klines, self.config)

                if signal and signal != "HOLD":
                    self.last_signal = signal

                    # Sinyal bilgisini kaydet
                    signal_data = {
                        "type": signal,
                        "price": self.last_price,
                        "timestamp": datetime.now().isoformat(),
                        "reason": strategy.get_reason(),
                        "confidence": strategy.get_confidence()
                    }
                    self.signals.append(signal_data)

                    # Callback ile bildir
                    if self.on_signal:
                        await self.on_signal(signal_data)

                    # 3. İşlem yap (eğer sinyal varsa)
                    # ████████████████████████████████████████████████████
                    # █  BURAYA İŞLEM YAPMA KODLARINI EKLE               █
                    # ████████████████████████████████████████████████████
                    # await self._execute_trade(signal)

                # Bir sonraki kontrole kadar bekle
                await asyncio.sleep(60)  # 1 dakika bekle

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Bot döngüsü hatası: {e}")
                await asyncio.sleep(10)

    async def _execute_trade(self, signal: str):
        """
        İşlem yap.

        ████████████████████████████████████████████████████████████████
        █  BURAYA İŞLEM YAPMA KODLARINI EKLE                           █
        █  - Market/Limit order                                        █
        █  - Stop loss / Take profit                                   █
        █  - Pozisyon yönetimi                                         █
        ████████████████████████████████████████████████████████████████
        """
        try:
            if signal == "BUY":
                # Alım işlemi
                # order = self.client.order_market_buy(
                #     symbol=self.config.symbol,
                #     quantity=self.config.amount
                # )
                pass

            elif signal == "SELL":
                # Satım işlemi
                # order = self.client.order_market_sell(
                #     symbol=self.config.symbol,
                #     quantity=self.config.amount
                # )
                pass

            # İşlem kaydını ekle
            trade_data = {
                "id": str(len(self.trades) + 1),
                "type": signal,
                "symbol": self.config.symbol,
                "price": self.last_price,
                "amount": self.config.amount,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            self.trades.append(trade_data)
            self.total_trades += 1

            # Callback ile bildir
            if self.on_trade:
                await self.on_trade(trade_data)

        except Exception as e:
            print(f"İşlem hatası: {e}")

    async def update_config(self, config: BotConfig) -> bool:
        """Bot ayarlarını güncelle"""
        self.config = config
        return True

    def get_status(self) -> Dict[str, Any]:
        """Bot durumunu getir"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        return {
            "is_running": self.is_running,
            "strategy": self.config.strategy if self.config else "none",
            "symbol": self.config.symbol if self.config else "BTCUSDT",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "total_trades": self.total_trades,
            "profit": self.profit,
            "win_rate": win_rate,
            "last_signal": self.last_signal,
            "last_price": self.last_price,
        }

    def get_trades(self, limit: int = 50) -> List[Dict]:
        """Son işlemleri getir"""
        return self.trades[-limit:]

    def get_signals(self, limit: int = 20) -> List[Dict]:
        """Son sinyalleri getir"""
        return self.signals[-limit:]
