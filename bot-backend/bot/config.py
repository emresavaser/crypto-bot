"""
Bot Konfigürasyon Sınıfı
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class BotConfig:
    """
    Bot ayarları için konfigürasyon sınıfı.

    ŞİMDİKİ PYTHON KODLARINDAN BU AYARLARI AL:
    - Hangi coin/parite ile işlem yapılacak
    - Hangi strateji kullanılacak
    - İşlem miktarı
    - Stop loss / Take profit değerleri
    - Strateji parametreleri
    """

    # Temel ayarlar
    symbol: str = "BTCUSDT"
    strategy: str = "rsi"  # rsi, macd, sma, bollinger, custom
    amount: float = 0.001  # İşlem miktarı (BTC cinsinden)

    # Risk yönetimi
    stop_loss: Optional[float] = None  # Yüzde olarak (örn: 2.0 = %2)
    take_profit: Optional[float] = None  # Yüzde olarak (örn: 5.0 = %5)
    max_trades_per_day: int = 10
    max_position_size: float = 0.1  # Maksimum pozisyon (BTC)

    # RSI Stratejisi parametreleri
    rsi_period: int = 14
    rsi_oversold: int = 30  # Bu değerin altında AL sinyali
    rsi_overbought: int = 70  # Bu değerin üstünde SAT sinyali

    # SMA/EMA Stratejisi parametreleri
    sma_short: int = 10  # Kısa vadeli hareketli ortalama
    sma_long: int = 50  # Uzun vadeli hareketli ortalama

    # MACD Stratejisi parametreleri
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Bollinger Bands parametreleri
    bb_period: int = 20
    bb_std: float = 2.0

    # Genel ayarlar
    interval: str = "1h"  # Mum aralığı: 1m, 5m, 15m, 1h, 4h, 1d
    use_testnet: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Config'i dictionary olarak döndür"""
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "amount": self.amount,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "max_trades_per_day": self.max_trades_per_day,
            "max_position_size": self.max_position_size,
            "rsi_period": self.rsi_period,
            "rsi_oversold": self.rsi_oversold,
            "rsi_overbought": self.rsi_overbought,
            "sma_short": self.sma_short,
            "sma_long": self.sma_long,
            "macd_fast": self.macd_fast,
            "macd_slow": self.macd_slow,
            "macd_signal": self.macd_signal,
            "bb_period": self.bb_period,
            "bb_std": self.bb_std,
            "interval": self.interval,
            "use_testnet": self.use_testnet,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotConfig":
        """Dictionary'den BotConfig oluştur"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
