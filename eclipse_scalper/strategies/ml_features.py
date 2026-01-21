# strategies/ml_features.py — SCALPER ETERNAL — ML FEATURE ORACLE — 2026 v1.0
# Feature engineering for machine learning integration
# Features:
# - Technical indicator feature extraction
# - Microstructure feature extraction
# - Feature normalization and scaling
# - Feature validation and cleaning

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from utils.logging import log_data


def _safe_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v
    except Exception:
        return default


@dataclass
class FeatureConfig:
    """Feature extraction configuration."""
    lookback_bars: int = 50
    normalize: bool = True
    clip_outliers: bool = True
    outlier_std: float = 3.0


# Standard feature names for model compatibility
TECHNICAL_FEATURES = [
    "momentum",
    "momentum_5m",
    "momentum_15m",
    "rsi_14",
    "rsi_norm",  # 0-1 normalized
    "stoch_k",
    "stoch_d",
    "adx",
    "bb_width",
    "bb_position",  # Where price is within bands (0-1)
    "atr_pct",
    "atr_50_pct",
    "volume_z",
    "volume_ma_ratio",
    "ema_distance",  # Distance from EMA200
    "vwap_distance",
    "trend_strength",
    "candle_body_pct",
    "upper_wick_pct",
    "lower_wick_pct",
]

MICROSTRUCTURE_FEATURES = [
    "bid_ask_spread",
    "order_imbalance",
    "weighted_imbalance",
    "cvd_signal",
    "large_buy_volume",
    "large_sell_volume",
]

TIME_FEATURES = [
    "hour_sin",
    "hour_cos",
    "day_of_week",
    "is_session_active",
]


def compute_technical_features(
    df: pd.DataFrame,
    config: Optional[FeatureConfig] = None,
) -> Dict[str, float]:
    """
    Compute technical indicator features from OHLCV data.

    Args:
        df: DataFrame with columns [ts, o, h, l, c, v] or similar
        config: Feature extraction configuration

    Returns:
        Dict of feature name -> value
    """
    if config is None:
        config = FeatureConfig()

    features = {}

    if df is None or df.empty or len(df) < 20:
        return _get_default_technical_features()

    try:
        # Ensure we have the right columns
        df = df.copy()

        # Standardize column names
        col_map = {
            'open': 'o', 'high': 'h', 'low': 'l', 'close': 'c', 'volume': 'v'
        }
        for old, new in col_map.items():
            if old in df.columns and new not in df.columns:
                df[new] = df[old]

        # Get latest values
        close = df['c'].iloc[-1]
        high = df['h'].iloc[-1]
        low = df['l'].iloc[-1]
        open_ = df['o'].iloc[-1]
        volume = df['v'].iloc[-1]

        # Momentum (Heikin-Ashi style)
        ha_close = (df['o'] + df['h'] + df['l'] + df['c']) / 4
        ha_close_ma = ha_close.rolling(4).mean()
        momentum = (ha_close.iloc[-1] - ha_close_ma.iloc[-1]) / ha_close_ma.iloc[-1] if ha_close_ma.iloc[-1] > 0 else 0.0
        features['momentum'] = _clip(momentum, -0.1, 0.1)

        # RSI
        delta = df['c'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        features['rsi_14'] = _safe_float(rsi.iloc[-1], 50.0)
        features['rsi_norm'] = features['rsi_14'] / 100.0

        # Stochastic
        low_14 = df['l'].rolling(14).min()
        high_14 = df['h'].rolling(14).max()
        stoch_k = 100 * (close - low_14.iloc[-1]) / (high_14.iloc[-1] - low_14.iloc[-1]) if (high_14.iloc[-1] - low_14.iloc[-1]) > 0 else 50.0
        features['stoch_k'] = _safe_float(stoch_k, 50.0)
        features['stoch_d'] = _safe_float(df['c'].rolling(3).mean().iloc[-1], 50.0)  # Simplified

        # ADX (simplified)
        tr = pd.concat([
            df['h'] - df['l'],
            abs(df['h'] - df['c'].shift()),
            abs(df['l'] - df['c'].shift())
        ], axis=1).max(axis=1)
        atr_14 = tr.rolling(14).mean()

        plus_dm = df['h'].diff().clip(lower=0)
        minus_dm = (-df['l'].diff()).clip(lower=0)
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr_14)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr_14)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(14).mean()
        features['adx'] = _safe_float(adx.iloc[-1], 25.0)

        # Bollinger Bands
        sma_20 = df['c'].rolling(20).mean()
        std_20 = df['c'].rolling(20).std()
        bb_upper = sma_20 + 2 * std_20
        bb_lower = sma_20 - 2 * std_20
        bb_width = (bb_upper - bb_lower) / sma_20
        features['bb_width'] = _safe_float(bb_width.iloc[-1], 0.02)

        # BB position (0 = lower band, 1 = upper band)
        bb_range = bb_upper.iloc[-1] - bb_lower.iloc[-1]
        if bb_range > 0:
            features['bb_position'] = (close - bb_lower.iloc[-1]) / bb_range
        else:
            features['bb_position'] = 0.5
        features['bb_position'] = _clip(features['bb_position'], 0.0, 1.0)

        # ATR percentage
        atr_pct = atr_14.iloc[-1] / close if close > 0 else 0.0
        features['atr_pct'] = _safe_float(atr_pct, 0.01)

        # Longer ATR
        atr_50 = tr.rolling(50).mean()
        atr_50_pct = atr_50.iloc[-1] / close if close > 0 else 0.0
        features['atr_50_pct'] = _safe_float(atr_50_pct, 0.01)

        # Volume features
        vol_mean = df['v'].rolling(20).mean()
        vol_std = df['v'].rolling(20).std()
        vol_z = (volume - vol_mean.iloc[-1]) / vol_std.iloc[-1] if vol_std.iloc[-1] > 0 else 0.0
        features['volume_z'] = _clip(vol_z, -3.0, 3.0)
        features['volume_ma_ratio'] = volume / vol_mean.iloc[-1] if vol_mean.iloc[-1] > 0 else 1.0

        # EMA distance
        ema_200 = df['c'].ewm(span=200, adjust=False).mean()
        ema_dist = (close - ema_200.iloc[-1]) / ema_200.iloc[-1] if ema_200.iloc[-1] > 0 else 0.0
        features['ema_distance'] = _clip(ema_dist, -0.1, 0.1)

        # VWAP distance (simplified - using volume-weighted price)
        vwap = (df['c'] * df['v']).rolling(min(240, len(df))).sum() / df['v'].rolling(min(240, len(df))).sum()
        vwap_dist = (close - vwap.iloc[-1]) / vwap.iloc[-1] if vwap.iloc[-1] > 0 else 0.0
        features['vwap_distance'] = _clip(vwap_dist, -0.05, 0.05)

        # Trend strength (slope of EMA)
        ema_20 = df['c'].ewm(span=20, adjust=False).mean()
        ema_slope = (ema_20.iloc[-1] - ema_20.iloc[-5]) / ema_20.iloc[-5] if len(df) >= 5 and ema_20.iloc[-5] > 0 else 0.0
        features['trend_strength'] = _clip(ema_slope, -0.05, 0.05)

        # Candle features
        candle_range = high - low if high > low else 0.001
        candle_body = abs(close - open_)
        features['candle_body_pct'] = candle_body / candle_range if candle_range > 0 else 0.5
        features['upper_wick_pct'] = (high - max(open_, close)) / candle_range if candle_range > 0 else 0.25
        features['lower_wick_pct'] = (min(open_, close) - low) / candle_range if candle_range > 0 else 0.25

        # Placeholder for multi-timeframe (will be filled separately)
        features['momentum_5m'] = 0.0
        features['momentum_15m'] = 0.0

    except Exception as e:
        log_data.warning(f"Feature extraction error: {e}")
        return _get_default_technical_features()

    return features


def compute_microstructure_features(
    orderbook: Optional[Dict] = None,
    trades: Optional[List] = None,
    order_flow_analyzer: Optional[Any] = None,
    symbol: str = "",
) -> Dict[str, float]:
    """
    Compute microstructure features from order book and trade data.

    Args:
        orderbook: Order book dict with 'bids' and 'asks'
        trades: List of recent trades
        order_flow_analyzer: Optional OrderFlowAnalyzer instance
        symbol: Symbol for order flow lookup

    Returns:
        Dict of feature name -> value
    """
    features = {
        'bid_ask_spread': 0.0,
        'order_imbalance': 0.0,
        'weighted_imbalance': 0.0,
        'cvd_signal': 0.0,
        'large_buy_volume': 0.0,
        'large_sell_volume': 0.0,
    }

    # Order book features
    if orderbook is not None:
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])

        if bids and asks:
            best_bid = _safe_float(bids[0][0], 0.0)
            best_ask = _safe_float(asks[0][0], 0.0)

            if best_bid > 0 and best_ask > 0:
                mid = (best_bid + best_ask) / 2.0
                features['bid_ask_spread'] = (best_ask - best_bid) / mid

                # Simple imbalance
                bid_vol = sum(_safe_float(l[1], 0.0) for l in bids[:10])
                ask_vol = sum(_safe_float(l[1], 0.0) for l in asks[:10])
                total = bid_vol + ask_vol
                if total > 0:
                    features['order_imbalance'] = (bid_vol - ask_vol) / total

    # Order flow features (if analyzer provided)
    if order_flow_analyzer is not None and symbol:
        try:
            features['order_imbalance'] = order_flow_analyzer.calculate_order_imbalance(symbol)
            features['weighted_imbalance'] = order_flow_analyzer.calculate_weighted_imbalance(symbol)
            features['cvd_signal'] = order_flow_analyzer.calculate_cvd_signal(symbol)

            large_orders = order_flow_analyzer.detect_large_orders(symbol, lookback_sec=60.0)
            features['large_buy_volume'] = large_orders.get('buy_volume', 0.0) / 100000.0  # Normalize
            features['large_sell_volume'] = large_orders.get('sell_volume', 0.0) / 100000.0
        except Exception as e:
            log_data.warning(f"Order flow feature error: {e}")

    return features


def compute_time_features(timestamp: Optional[float] = None) -> Dict[str, float]:
    """
    Compute time-based features.

    Args:
        timestamp: Unix timestamp (uses current time if None)

    Returns:
        Dict of feature name -> value
    """
    import time
    from datetime import datetime, timezone

    if timestamp is None:
        timestamp = time.time()

    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        hour = dt.hour
        day_of_week = dt.weekday()

        # Cyclical encoding for hour
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)

        # Session activity (high volume hours: 13:00-17:00 UTC)
        is_session_active = 1.0 if 13 <= hour <= 17 else 0.0

        return {
            'hour_sin': float(hour_sin),
            'hour_cos': float(hour_cos),
            'day_of_week': float(day_of_week) / 6.0,  # Normalize to 0-1
            'is_session_active': is_session_active,
        }

    except Exception:
        return {
            'hour_sin': 0.0,
            'hour_cos': 1.0,
            'day_of_week': 0.5,
            'is_session_active': 0.0,
        }


def extract_all_features(
    df: pd.DataFrame,
    orderbook: Optional[Dict] = None,
    trades: Optional[List] = None,
    order_flow_analyzer: Optional[Any] = None,
    symbol: str = "",
    config: Optional[FeatureConfig] = None,
) -> Dict[str, float]:
    """
    Extract all features for ML model.

    Args:
        df: OHLCV DataFrame
        orderbook: Order book data
        trades: Recent trades
        order_flow_analyzer: Order flow analyzer instance
        symbol: Trading symbol
        config: Feature configuration

    Returns:
        Dict with all features
    """
    features = {}

    # Technical features
    tech = compute_technical_features(df, config)
    features.update(tech)

    # Microstructure features
    micro = compute_microstructure_features(orderbook, trades, order_flow_analyzer, symbol)
    features.update(micro)

    # Time features
    time_feat = compute_time_features()
    features.update(time_feat)

    return features


def features_to_array(
    features: Dict[str, float],
    feature_names: Optional[List[str]] = None,
) -> np.ndarray:
    """
    Convert feature dict to numpy array in consistent order.

    Args:
        features: Feature dictionary
        feature_names: List of feature names (uses all known features if None)

    Returns:
        Numpy array of feature values
    """
    if feature_names is None:
        feature_names = TECHNICAL_FEATURES + MICROSTRUCTURE_FEATURES + TIME_FEATURES

    values = []
    for name in feature_names:
        values.append(_safe_float(features.get(name, 0.0), 0.0))

    return np.array(values, dtype=np.float32)


def normalize_features(
    features: np.ndarray,
    means: Optional[np.ndarray] = None,
    stds: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Normalize features using z-score normalization.

    Args:
        features: Feature array
        means: Pre-computed means (uses defaults if None)
        stds: Pre-computed standard deviations

    Returns:
        Normalized feature array
    """
    if means is None:
        means = np.zeros(len(features))
    if stds is None:
        stds = np.ones(len(features))

    # Avoid division by zero
    stds = np.where(stds > 0, stds, 1.0)

    return (features - means) / stds


def _clip(value: float, min_val: float, max_val: float) -> float:
    """Clip value to range."""
    return max(min_val, min(max_val, _safe_float(value, 0.0)))


def _get_default_technical_features() -> Dict[str, float]:
    """Get default values for technical features."""
    return {
        'momentum': 0.0,
        'momentum_5m': 0.0,
        'momentum_15m': 0.0,
        'rsi_14': 50.0,
        'rsi_norm': 0.5,
        'stoch_k': 50.0,
        'stoch_d': 50.0,
        'adx': 25.0,
        'bb_width': 0.02,
        'bb_position': 0.5,
        'atr_pct': 0.01,
        'atr_50_pct': 0.01,
        'volume_z': 0.0,
        'volume_ma_ratio': 1.0,
        'ema_distance': 0.0,
        'vwap_distance': 0.0,
        'trend_strength': 0.0,
        'candle_body_pct': 0.5,
        'upper_wick_pct': 0.25,
        'lower_wick_pct': 0.25,
    }
