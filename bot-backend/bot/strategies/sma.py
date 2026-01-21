"""
SMA (Simple Moving Average) Crossover Stratejisi

████████████████████████████████████████████████████████████████
█  KENDİ SMA/EMA KODLARINI BURAYA EKLEYEBİLİRSİN              █
████████████████████████████████████████████████████████████████
"""

from typing import List, Optional
from .base import BaseStrategy
from ..config import BotConfig


class SMAStrategy(BaseStrategy):
    """
    SMA Crossover Stratejisi

    - Kısa SMA, uzun SMA'yı yukarı keserse -> AL
    - Kısa SMA, uzun SMA'yı aşağı keserse -> SAT
    """

    def __init__(self):
        super().__init__()
        self.name = "sma"
        self.prev_short_sma = None
        self.prev_long_sma = None

    def calculate(self, klines: List, config: BotConfig) -> Optional[str]:
        """SMA crossover sinyali hesapla"""
        closes = self._extract_closes(klines)

        if len(closes) < config.sma_long + 1:
            return None

        # SMA'ları hesapla
        short_sma = self._calculate_sma(closes, config.sma_short)
        long_sma = self._calculate_sma(closes, config.sma_long)

        # Önceki değerleri kontrol et (crossover tespiti için)
        if self.prev_short_sma is None or self.prev_long_sma is None:
            self.prev_short_sma = short_sma
            self.prev_long_sma = long_sma
            return None

        signal = None

        # Golden Cross - AL sinyali
        if self.prev_short_sma <= self.prev_long_sma and short_sma > long_sma:
            self.last_reason = f"Golden Cross: SMA({config.sma_short}) SMA({config.sma_long})'ı yukarı kesti"
            self.confidence = min(1.0, (short_sma - long_sma) / long_sma * 100)
            signal = "BUY"

        # Death Cross - SAT sinyali
        elif self.prev_short_sma >= self.prev_long_sma and short_sma < long_sma:
            self.last_reason = f"Death Cross: SMA({config.sma_short}) SMA({config.sma_long})'ı aşağı kesti"
            self.confidence = min(1.0, (long_sma - short_sma) / long_sma * 100)
            signal = "SELL"

        # Değerleri güncelle
        self.prev_short_sma = short_sma
        self.prev_long_sma = long_sma

        return signal

    def _calculate_sma(self, prices: List[float], period: int) -> float:
        """
        Simple Moving Average hesapla

        ████████████████████████████████████████████████████████
        █  KENDİ SMA HESAPLAMA KODUNU BURAYA EKLEYEBİLİRSİN    █
        ████████████████████████████████████████████████████████
        """
        if len(prices) < period:
            return 0.0

        return sum(prices[-period:]) / period
