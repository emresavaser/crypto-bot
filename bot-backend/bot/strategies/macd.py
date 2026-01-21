"""
MACD (Moving Average Convergence Divergence) Stratejisi

████████████████████████████████████████████████████████████████
█  KENDİ MACD KODLARINI BURAYA EKLEYEBİLİRSİN                  █
████████████████████████████████████████████████████████████████
"""

from typing import List, Optional
from .base import BaseStrategy
from ..config import BotConfig


class MACDStrategy(BaseStrategy):
    """
    MACD Stratejisi

    - MACD çizgisi sinyal çizgisini yukarı keserse -> AL
    - MACD çizgisi sinyal çizgisini aşağı keserse -> SAT
    """

    def __init__(self):
        super().__init__()
        self.name = "macd"
        self.prev_macd = None
        self.prev_signal = None

    def calculate(self, klines: List, config: BotConfig) -> Optional[str]:
        """MACD sinyali hesapla"""
        closes = self._extract_closes(klines)

        if len(closes) < config.macd_slow + config.macd_signal:
            return None

        # MACD hesapla
        macd_line, signal_line, histogram = self._calculate_macd(
            closes,
            config.macd_fast,
            config.macd_slow,
            config.macd_signal
        )

        if macd_line is None or signal_line is None:
            return None

        # Önceki değerleri kontrol et
        if self.prev_macd is None or self.prev_signal is None:
            self.prev_macd = macd_line
            self.prev_signal = signal_line
            return None

        result = None

        # MACD sinyal çizgisini yukarı keserse -> AL
        if self.prev_macd <= self.prev_signal and macd_line > signal_line:
            self.last_reason = f"MACD yukarı crossover (MACD: {macd_line:.2f}, Signal: {signal_line:.2f})"
            self.confidence = min(1.0, abs(histogram) / abs(signal_line) if signal_line != 0 else 0.5)
            result = "BUY"

        # MACD sinyal çizgisini aşağı keserse -> SAT
        elif self.prev_macd >= self.prev_signal and macd_line < signal_line:
            self.last_reason = f"MACD aşağı crossover (MACD: {macd_line:.2f}, Signal: {signal_line:.2f})"
            self.confidence = min(1.0, abs(histogram) / abs(signal_line) if signal_line != 0 else 0.5)
            result = "SELL"

        # Değerleri güncelle
        self.prev_macd = macd_line
        self.prev_signal = signal_line

        return result

    def _calculate_macd(
        self,
        prices: List[float],
        fast_period: int,
        slow_period: int,
        signal_period: int
    ) -> tuple:
        """
        MACD hesapla

        ████████████████████████████████████████████████████████
        █  KENDİ MACD HESAPLAMA KODUNU BURAYA EKLEYEBİLİRSİN   █
        ████████████████████████████████████████████████████████
        """
        if len(prices) < slow_period + signal_period:
            return None, None, None

        # EMA hesaplama fonksiyonu
        def ema(data: List[float], period: int) -> List[float]:
            multiplier = 2 / (period + 1)
            ema_values = [sum(data[:period]) / period]  # İlk SMA

            for price in data[period:]:
                ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])

            return ema_values

        # Fast ve Slow EMA
        fast_ema = ema(prices, fast_period)
        slow_ema = ema(prices, slow_period)

        # MACD Line = Fast EMA - Slow EMA
        # Uzunlukları eşitle
        min_len = min(len(fast_ema), len(slow_ema))
        macd_values = [
            fast_ema[-(min_len - i)] - slow_ema[-(min_len - i)]
            for i in range(min_len)
        ]

        if len(macd_values) < signal_period:
            return None, None, None

        # Signal Line = MACD'nin EMA'sı
        signal_values = ema(macd_values, signal_period)

        # Son değerler
        macd_line = macd_values[-1]
        signal_line = signal_values[-1]
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram
