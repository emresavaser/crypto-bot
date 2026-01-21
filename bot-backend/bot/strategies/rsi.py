"""
RSI (Relative Strength Index) Stratejisi

████████████████████████████████████████████████████████████████
█  KENDİ RSI KODLARINI BURAYA EKLEYEBİLİRSİN                   █
████████████████████████████████████████████████████████████████
"""

from typing import List, Optional
from .base import BaseStrategy
from ..config import BotConfig


class RSIStrategy(BaseStrategy):
    """
    RSI Stratejisi

    - RSI < oversold (30) -> AL sinyali
    - RSI > overbought (70) -> SAT sinyali
    """

    def __init__(self):
        super().__init__()
        self.name = "rsi"

    def calculate(self, klines: List, config: BotConfig) -> Optional[str]:
        """RSI sinyali hesapla"""
        closes = self._extract_closes(klines)

        if len(closes) < config.rsi_period + 1:
            return None

        # RSI hesapla
        rsi = self._calculate_rsi(closes, config.rsi_period)

        if rsi is None:
            return None

        # Sinyal üret
        if rsi < config.rsi_oversold:
            self.last_reason = f"RSI ({rsi:.1f}) aşırı satım bölgesinde (< {config.rsi_oversold})"
            self.confidence = min(1.0, (config.rsi_oversold - rsi) / config.rsi_oversold)
            return "BUY"

        elif rsi > config.rsi_overbought:
            self.last_reason = f"RSI ({rsi:.1f}) aşırı alım bölgesinde (> {config.rsi_overbought})"
            self.confidence = min(1.0, (rsi - config.rsi_overbought) / (100 - config.rsi_overbought))
            return "SELL"

        return None

    def _calculate_rsi(self, prices: List[float], period: int) -> Optional[float]:
        """
        RSI hesapla

        ████████████████████████████████████████████████████████
        █  KENDİ RSI HESAPLAMA KODUNU BURAYA EKLEYEBİLİRSİN    █
        ████████████████████████████████████████████████████████
        """
        if len(prices) < period + 1:
            return None

        # Fiyat değişimlerini hesapla
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # Son 'period' kadar değişimi al
        recent_deltas = deltas[-(period):]

        # Kazançları ve kayıpları ayır
        gains = [d if d > 0 else 0 for d in recent_deltas]
        losses = [-d if d < 0 else 0 for d in recent_deltas]

        # Ortalama kazanç ve kayıp
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi
