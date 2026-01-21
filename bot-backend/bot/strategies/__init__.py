"""
Trading Stratejileri

████████████████████████████████████████████████████████████████
█  KENDİ STRATEJİLERİNİ BURAYA EKLE                            █
████████████████████████████████████████████████████████████████
"""

from .base import BaseStrategy
from .rsi import RSIStrategy
from .sma import SMAStrategy
from .macd import MACDStrategy


def get_strategy(name: str) -> BaseStrategy:
    """
    Strateji adına göre strateji sınıfı döndür.

    KULLANIM:
    strategy = get_strategy("rsi")
    signal = strategy.calculate(klines, config)
    """
    strategies = {
        "rsi": RSIStrategy(),
        "sma": SMAStrategy(),
        "macd": MACDStrategy(),
        # Kendi stratejilerini buraya ekle:
        # "custom": CustomStrategy(),
    }

    return strategies.get(name, RSIStrategy())


__all__ = ["BaseStrategy", "RSIStrategy", "SMAStrategy", "MACDStrategy", "get_strategy"]
