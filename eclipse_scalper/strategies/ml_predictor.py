# strategies/ml_predictor.py — SCALPER ETERNAL — ML PREDICTOR ORACLE — 2026 v1.0
# Machine learning integration for signal enhancement
# Features:
# - Lightweight online learning model
# - Signal filtering based on ML confidence
# - Online retraining from exit outcomes
# - Model persistence and loading

from __future__ import annotations

import os
import time
import pickle
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path

from utils.logging import log_data

# Try to import sklearn
try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import SGDClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    log_data.warning("scikit-learn not available — ML features disabled")


def _safe_float(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        return default if v != v else v
    except Exception:
        return default


@dataclass
class MLConfig:
    """ML predictor configuration."""
    enabled: bool = False  # Off by default, opt-in
    model_type: str = "gradient_boosting"  # "gradient_boosting", "random_forest", "sgd"
    model_path: str = ""  # Path to save/load model
    min_confidence: float = 0.6
    retrain_on_exit: bool = True
    min_samples_for_training: int = 100
    retrain_interval_samples: int = 50
    feature_window: int = 50
    ensemble_weight: float = 0.4  # 40% ML, 60% rules


@dataclass
class TrainingSample:
    """Single training sample."""
    features: np.ndarray
    direction: int  # 1 = long profitable, 0 = loss, -1 = short profitable
    confidence: float
    pnl: float
    timestamp: float


class FeatureExtractor:
    """
    FEATURE EXTRACTOR — Transform indicators to feature vectors.
    """

    def __init__(self, feature_names: Optional[List[str]] = None):
        if feature_names is None:
            from strategies.ml_features import TECHNICAL_FEATURES, MICROSTRUCTURE_FEATURES, TIME_FEATURES
            self.feature_names = TECHNICAL_FEATURES + MICROSTRUCTURE_FEATURES + TIME_FEATURES
        else:
            self.feature_names = feature_names

        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self._fitted = False

    def extract(self, feature_dict: Dict[str, float]) -> np.ndarray:
        """
        Extract features from dict to array.

        Args:
            feature_dict: Dict of feature name -> value

        Returns:
            Feature array
        """
        values = []
        for name in self.feature_names:
            values.append(_safe_float(feature_dict.get(name, 0.0), 0.0))

        return np.array(values, dtype=np.float32)

    def fit_scaler(self, X: np.ndarray) -> None:
        """Fit the scaler on training data."""
        if self.scaler is not None and len(X) > 0:
            self.scaler.fit(X)
            self._fitted = True

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform features using fitted scaler."""
        if self.scaler is not None and self._fitted:
            return self.scaler.transform(X.reshape(1, -1) if X.ndim == 1 else X)
        return X.reshape(1, -1) if X.ndim == 1 else X


class OnlinePredictor:
    """
    ONLINE PREDICTOR — Lightweight model for signal filtering.

    Supports:
    - Gradient Boosting (best accuracy, slower)
    - Random Forest (good accuracy, faster)
    - SGD Classifier (supports online learning)
    """

    def __init__(self, config: Optional[MLConfig] = None):
        self.config = config or MLConfig()
        self.model = None
        self.feature_extractor = FeatureExtractor()

        # Training data buffer
        self._samples: deque = deque(maxlen=5000)
        self._last_train_count = 0

        # Performance tracking
        self._predictions: deque = deque(maxlen=1000)
        self._correct: int = 0
        self._total: int = 0

        if self.config.enabled and SKLEARN_AVAILABLE:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the ML model based on config."""
        if not SKLEARN_AVAILABLE:
            return

        model_type = self.config.model_type.lower()

        if model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )
        elif model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42,
                n_jobs=-1,
            )
        elif model_type == "sgd":
            self.model = SGDClassifier(
                loss="log_loss",
                penalty="l2",
                random_state=42,
            )
        else:
            log_data.warning(f"Unknown model type: {model_type}, using gradient_boosting")
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )

        log_data.info(f"ML PREDICTOR: Initialized {model_type} model")

    def predict_direction(
        self,
        features: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Predict direction probabilities.

        Args:
            features: Feature array

        Returns:
            (long_probability, short_probability)
        """
        if not self.config.enabled or self.model is None:
            return 0.5, 0.5

        if not hasattr(self.model, 'classes_'):
            # Model not trained yet
            return 0.5, 0.5

        try:
            X = self.feature_extractor.transform(features)
            proba = self.model.predict_proba(X)[0]

            # Map class probabilities
            # Classes: 0 = loss, 1 = profitable
            if len(proba) == 2:
                profit_prob = proba[1]
                return profit_prob, 1.0 - profit_prob

            return 0.5, 0.5

        except Exception as e:
            log_data.warning(f"ML prediction error: {e}")
            return 0.5, 0.5

    def should_trade(
        self,
        features: np.ndarray,
        rule_signal: bool,
        direction: str,
    ) -> Tuple[bool, float, str]:
        """
        Determine if trade should be taken based on ML confidence.

        Args:
            features: Feature array
            rule_signal: Whether rule-based signal triggered
            direction: "long" or "short"

        Returns:
            (should_trade, ml_confidence, reason)
        """
        if not self.config.enabled:
            return rule_signal, 0.5, "ML disabled"

        if not rule_signal:
            return False, 0.0, "No rule signal"

        long_prob, short_prob = self.predict_direction(features)

        if direction.lower() == "long":
            ml_conf = long_prob
        else:
            ml_conf = short_prob

        if ml_conf < self.config.min_confidence:
            return False, ml_conf, f"ML confidence {ml_conf:.2f} < {self.config.min_confidence}"

        return True, ml_conf, "ML approved"

    def add_training_sample(
        self,
        features: np.ndarray,
        direction: str,
        confidence: float,
        pnl: float,
    ) -> None:
        """
        Add a training sample from exit outcome.

        Args:
            features: Feature array at entry time
            direction: "long" or "short"
            confidence: Rule-based confidence at entry
            pnl: Realized PnL
        """
        if not self.config.retrain_on_exit:
            return

        # Label: profitable (1) or not (0)
        label = 1 if pnl > 0 else 0

        sample = TrainingSample(
            features=features.copy(),
            direction=1 if direction.lower() == "long" else -1,
            confidence=confidence,
            pnl=pnl,
            timestamp=time.time(),
        )

        self._samples.append((sample.features, label))

        # Check if we should retrain
        samples_since_train = len(self._samples) - self._last_train_count

        if (len(self._samples) >= self.config.min_samples_for_training and
                samples_since_train >= self.config.retrain_interval_samples):
            self._retrain()

    def _retrain(self) -> None:
        """Retrain the model on accumulated samples."""
        if not SKLEARN_AVAILABLE or self.model is None:
            return

        if len(self._samples) < self.config.min_samples_for_training:
            return

        try:
            # Prepare training data
            X = np.array([s[0] for s in self._samples])
            y = np.array([s[1] for s in self._samples])

            # Fit scaler
            self.feature_extractor.fit_scaler(X)
            X_scaled = self.feature_extractor.scaler.transform(X)

            # Train model
            self.model.fit(X_scaled, y)

            self._last_train_count = len(self._samples)

            # Calculate training accuracy
            train_pred = self.model.predict(X_scaled)
            accuracy = (train_pred == y).mean()

            log_data.info(f"ML PREDICTOR: Retrained on {len(self._samples)} samples, accuracy={accuracy:.2%}")

            # Save model if path configured
            if self.config.model_path:
                self.save_model()

        except Exception as e:
            log_data.error(f"ML retraining error: {e}")

    def save_model(self, path: Optional[str] = None) -> bool:
        """Save model to disk."""
        if self.model is None:
            return False

        save_path = path or self.config.model_path
        if not save_path:
            return False

        try:
            save_path = os.path.expanduser(save_path)
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.feature_extractor.scaler,
                    'feature_names': self.feature_extractor.feature_names,
                    'samples_count': len(self._samples),
                }, f)

            log_data.info(f"ML PREDICTOR: Model saved to {save_path}")
            return True

        except Exception as e:
            log_data.error(f"ML save error: {e}")
            return False

    def load_model(self, path: Optional[str] = None) -> bool:
        """Load model from disk."""
        load_path = path or self.config.model_path
        if not load_path:
            return False

        load_path = os.path.expanduser(load_path)
        if not os.path.exists(load_path):
            return False

        try:
            with open(load_path, 'rb') as f:
                data = pickle.load(f)

            self.model = data['model']
            self.feature_extractor.scaler = data['scaler']
            self.feature_extractor.feature_names = data['feature_names']
            self.feature_extractor._fitted = True

            log_data.info(f"ML PREDICTOR: Model loaded from {load_path}")
            return True

        except Exception as e:
            log_data.error(f"ML load error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get predictor statistics."""
        return {
            "enabled": self.config.enabled,
            "model_type": self.config.model_type,
            "samples_collected": len(self._samples),
            "last_train_count": self._last_train_count,
            "model_trained": hasattr(self.model, 'classes_') if self.model else False,
            "accuracy": self._correct / self._total if self._total > 0 else 0.0,
        }


class SignalFilter:
    """
    SIGNAL FILTER — Combine rule-based signals with ML confidence.

    Provides ensemble scoring: final_conf = (1 - weight) * rule_conf + weight * ml_conf
    """

    def __init__(self, config: Optional[MLConfig] = None):
        self.config = config or MLConfig()
        self.predictor = OnlinePredictor(config)

    def filter_signal(
        self,
        features: Dict[str, float],
        long_signal: bool,
        short_signal: bool,
        rule_confidence: float,
    ) -> Tuple[bool, bool, float]:
        """
        Filter signals through ML.

        Args:
            features: Feature dictionary
            long_signal: Rule-based long signal
            short_signal: Rule-based short signal
            rule_confidence: Rule-based confidence

        Returns:
            (filtered_long, filtered_short, ensemble_confidence)
        """
        if not self.config.enabled:
            return long_signal, short_signal, rule_confidence

        # Extract features
        feat_array = self.predictor.feature_extractor.extract(features)

        # Get ML predictions
        long_prob, short_prob = self.predictor.predict_direction(feat_array)

        # Filter signals
        filtered_long = long_signal
        filtered_short = short_signal

        if long_signal and long_prob < self.config.min_confidence:
            filtered_long = False
            log_data.debug(f"ML filtered long: prob={long_prob:.2f}")

        if short_signal and short_prob < self.config.min_confidence:
            filtered_short = False
            log_data.debug(f"ML filtered short: prob={short_prob:.2f}")

        # Calculate ensemble confidence
        if filtered_long:
            ml_conf = long_prob
        elif filtered_short:
            ml_conf = short_prob
        else:
            ml_conf = 0.5

        weight = self.config.ensemble_weight
        ensemble_conf = (1 - weight) * rule_confidence + weight * ml_conf

        return filtered_long, filtered_short, ensemble_conf

    def record_outcome(
        self,
        features: Dict[str, float],
        direction: str,
        confidence: float,
        pnl: float,
    ) -> None:
        """Record trade outcome for online learning."""
        feat_array = self.predictor.feature_extractor.extract(features)
        self.predictor.add_training_sample(feat_array, direction, confidence, pnl)


# Global singleton
_ml_filter: Optional[SignalFilter] = None


def get_ml_filter(config: Optional[MLConfig] = None) -> SignalFilter:
    """Get or create the global ML signal filter."""
    global _ml_filter

    if _ml_filter is None:
        _ml_filter = SignalFilter(config)

    return _ml_filter


def filter_signal_with_ml(
    features: Dict[str, float],
    long_signal: bool,
    short_signal: bool,
    rule_confidence: float,
    config: Optional[MLConfig] = None,
) -> Tuple[bool, bool, float]:
    """
    Convenience function to filter signals with ML.

    Returns:
        (filtered_long, filtered_short, ensemble_confidence)
    """
    ml_filter = get_ml_filter(config)
    return ml_filter.filter_signal(features, long_signal, short_signal, rule_confidence)


async def initialize_ml(bot) -> Optional[SignalFilter]:
    """
    Initialize ML filter from bot config.

    Args:
        bot: Bot instance

    Returns:
        Configured SignalFilter or None
    """
    cfg = getattr(bot, "cfg", None)

    config = MLConfig()
    if cfg is not None:
        if hasattr(cfg, "ML_ENABLED"):
            config.enabled = bool(cfg.ML_ENABLED)
        if hasattr(cfg, "ML_MODEL_PATH"):
            config.model_path = str(cfg.ML_MODEL_PATH)
        if hasattr(cfg, "ML_MIN_CONFIDENCE"):
            config.min_confidence = float(cfg.ML_MIN_CONFIDENCE)
        if hasattr(cfg, "ML_RETRAIN_ON_EXIT"):
            config.retrain_on_exit = bool(cfg.ML_RETRAIN_ON_EXIT)
        if hasattr(cfg, "ML_ENSEMBLE_WEIGHT"):
            config.ensemble_weight = float(cfg.ML_ENSEMBLE_WEIGHT)

    ml_filter = get_ml_filter(config)

    # Try to load existing model
    if config.enabled and config.model_path:
        ml_filter.predictor.load_model()

    log_data.info(f"ML FILTER: Initialized (enabled={config.enabled})")
    return ml_filter
