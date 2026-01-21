"""
Base Strateji Sınıfı - Tüm stratejiler bundan türetilmeli
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..config import BotConfig


class BaseStrategy(ABC):
    """
    Tüm trading stratejileri için temel sınıf.

    YENİ STRATEJİ EKLEMEK İÇİN:
    1. Bu sınıftan türet
    2. calculate() metodunu override et
    3. strategies/__init__.py'de kaydet
    """

    def __init__(self):
        self.name = "base"
        self.last_reason = ""
        self.confidence = 0.0

    @abstractmethod
    def calculate(self, klines: List, config: BotConfig) -> Optional[str]:
        """
        Strateji sinyali hesapla.

        Args:
            klines: Binance'ten gelen mum verileri
                   [[timestamp, open, high, low, close, volume, ...], ...]
            config: Bot konfigürasyonu

        Returns:
            "BUY", "SELL" veya None (sinyal yok)
        """
        pass

    def get_reason(self) -> str:
        """Son sinyalin nedenini döndür"""
        return self.last_reason

    def get_confidence(self) -> float:
        """Son sinyalin güven seviyesini döndür (0-1 arası)"""
        return self.confidence

    def _extract_closes(self, klines: List) -> List[float]:
        """Kline verilerinden kapanış fiyatlarını çıkar"""
        return [float(k[4]) for k in klines]

    def _extract_highs(self, klines: List) -> List[float]:
        """Kline verilerinden en yüksek fiyatları çıkar"""
        return [float(k[2]) for k in klines]

    def _extract_lows(self, klines: List) -> List[float]:
        """Kline verilerinden en düşük fiyatları çıkar"""
        return [float(k[3]) for k in klines]

    def _extract_volumes(self, klines: List) -> List[float]:
        """Kline verilerinden hacim verilerini çıkar"""
        return [float(k[5]) for k in klines]
