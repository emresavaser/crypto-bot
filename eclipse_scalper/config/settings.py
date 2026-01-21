# config/settings.py — SCALPER ETERNAL — MICRO CAPITAL ASCENDANT MODE — 2026 v3.3
# Patch vs v3.2:
# - ✅ Adds ENTRY LOOP compatibility keys (ENTRY_* + ACTIVE_SYMBOLS + FIXED_NOTIONAL sizing)
# - ✅ Adds kill-switch / telemetry defaults (safe)
# - ✅ Keeps your production + micro risk logic intact
#
# Why this matters:
# - execution/entry_loop.py reads ENTRY_MIN_CONFIDENCE / ENTRY_POLL_SEC / ACTIVE_SYMBOLS / FIXED_NOTIONAL_USDT
# - Without these, you’ll default to BTCUSDT only + sizing None + silent starvation

from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """
    OMNIPOTENT PRODUCTION MODE — 2026 v2 (Baseline)
    Foundation for mid-to-large accounts (equity ≥ $100).
    """

    # === TRANSCENDENT TIMEFRAMES ===
    TIMEFRAME: str = "1m"
    TIMEFRAME_5M: str = "5m"
    TIMEFRAME_15M: str = "15m"

    # === DIVINE RISK & ETERNAL PRESERVATION (PRODUCTION BALANCE) ===
    MAX_RISK_PER_TRADE: float = 0.10
    MAX_PORTFOLIO_HEAT: float = 0.45
    MAX_CONCURRENT_POSITIONS: int = 6
    MIN_RISK_DOLLARS: float = 5.0
    MAX_DAILY_LOSS_PCT: float = 0.15
    SYMBOL_COOLDOWN_MINUTES: int = 20
    CONSECUTIVE_LOSS_BLACKLIST_COUNT: int = 3
    SYMBOL_BLACKLIST_DURATION_HOURS: int = 4
    BLACKLIST_AUTO_RESET_ON_PROFIT: bool = True

    # === OMNIPOTENT MODES ===
    OMNIPOTENT_MODE: bool = True
    ADAPTIVE_RISK_SCALING: bool = True

    # === CORRELATION & VELOCITY GUARDS ===
    CORRELATION_HEAT_CAP: float = 0.30
    SESSION_EQUITY_PEAK_PROTECTION_PCT: float = 0.10
    VELOCITY_DRAWDOWN_PCT: float = 0.06
    VELOCITY_MINUTES: int = 6
    MIN_ATR_PCT_FOR_ENTRY: float = 0.007

    # === LEVERAGE & EXECUTION ===
    LEVERAGE: int = 20
    MIN_FILL_RATIO: float = 0.85
    SLIPPAGE_MAX_PCT: float = 0.006

    # === STOP, TAKE PROFIT & TRAILING ===
    STOP_ATR_MULT: float = 1.10
    MAX_STOP_PCT: float = 0.03
    BREAKEVEN_BUFFER_ATR_MULT: float = 0.30
    TP1_RR_MULT: float = 1.00
    TP2_RR_MULT: float = 2.00
    TRAILING_ACTIVATION_RR: float = 1.30
    TRAILING_CALLBACK_RATE: int = 45
    TRAILING_TIGHT_PCT: int = 35
    TRAILING_LOOSE_PCT: int = 75

    # === FUNDING RATE FILTERS ===
    MAX_FUNDING_LONG: float = 0.0006
    MIN_FUNDING_SHORT: float = -0.0004

    # === SIGNAL THRESHOLD ===
    MIN_CONFIDENCE: float = 0.72
    MIN_CONFIDENCE_HIGH_VOL: float = 0.65

    # === ENTRY LOOP COMPATIBILITY (NEW) ===
    # entry_loop.py uses these keys (kept separate from strategy MIN_CONFIDENCE)
    ENTRY_MIN_CONFIDENCE: float = 0.72
    ENTRY_POLL_SEC: float = 1.0
    ENTRY_PER_SYMBOL_GAP_SEC: float = 2.5
    ENTRY_LOCAL_COOLDOWN_SEC: float = 8.0
    ENTRY_RESPECT_KILL_SWITCH: bool = True
    ENTRY_ROUTER_RETRIES: int = 6
    ENTRY_NOTIFY: bool = False

    # Simple sizing fallback used by entry_loop when signal doesn't provide amount:
    # qty = FIXED_NOTIONAL_USDT / price
    FIXED_QTY: float = 0.0
    FIXED_NOTIONAL_USDT: float = 25.0
    MIN_ENTRY_QTY: float = 0.0

    # Symbol universe
    ACTIVE_SYMBOLS: List[str] = field(default_factory=lambda: ["BTCUSDT"])

    # === TRADING HOURS ===
    TRADING_HOURS_UTC: List[int] = field(default_factory=lambda: list(range(24)))

    # === LOGGING & NOTIFICATION ===
    LOGGING_LEVEL: str = "INFO"
    NOTIFY_ON_ENTRY: bool = True
    NOTIFY_ON_EXIT: bool = True
    NOTIFY_ON_BREAKEVEN: bool = True
    NOTIFY_ON_BLACKLIST: bool = True

    # === FLAGS ===
    CONFIDENCE_SCALING: bool = True
    DYNAMIC_TRAILING_FULL: bool = True
    DUAL_TRAILING: bool = True
    MAX_HEAT_POST_ENTRY_ENFORCE: bool = True

    # === MICRO-RELATED EXECUTION MINIMUMS (SAFE DEFAULTS) ===
    MIN_NOTIONAL_USDT: float = 5.0
    MIN_MARGIN_USDT: float = 2.0
    MAX_ORDER_RETRIES: int = 2
    ORDER_RETRY_SLEEP_SEC: float = 0.25

    # === KILL SWITCH DEFAULTS (SAFE) ===
    KILL_SWITCH_ENABLED: bool = True
    KILL_SWITCH_COOLDOWN_SEC: float = 300.0
    KILL_MAX_DATA_STALENESS_SEC: float = 150.0
    KILL_DATA_BOOT_GRACE_SEC: float = 120.0
    KILL_MIN_DATA_SAMPLES_BEFORE_ENFORCE: int = 1
    KILL_MAX_API_ERROR_RATE: float = 0.35
    KILL_MAX_API_ERROR_BURST: int = 12
    KILL_MIN_REQ_WINDOW: int = 10
    KILL_SWITCH_EMERGENCY_FLAT: bool = False  # keep OFF unless you're confident
    KILL_ESCALATE_FLAT_AFTER_TRIPS: int = 0
    KILL_ESCALATE_SHUTDOWN_AFTER_TRIPS: int = 0
    KILL_ESCALATE_WINDOW_SEC: float = 900.0
    KILL_SWITCH_TRIP_HISTORY_MAX: int = 12

    # === TELEMETRY DEFAULTS (SAFE) ===
    TELEMETRY_WRITE_FILE: bool = True
    TELEMETRY_MIRROR_STDOUT: bool = False
    TELEMETRY_RING_MAX: int = 250
    TELEMETRY_PATH: str = ""  # empty => logs/telemetry.jsonl

    # === METADATA ===
    CONFIG_VERSION: str = "omnipotent-production-2026-v3"
    CONFIG_FORGED_DATE: str = "2026-01-21"

    # ============================================================
    # === 10/10 UPGRADE FEATURES (2026 v3.0) ===
    # ============================================================

    # === WEBSOCKET STREAMING ===
    WS_ENABLED: bool = True
    WS_RECONNECT_DELAY_SEC: float = 5.0
    WS_RECONNECT_MAX_DELAY_SEC: float = 300.0
    WS_FALLBACK_TO_REST: bool = True
    WS_HEALTH_CHECK_SEC: float = 30.0
    WS_STALE_THRESHOLD_SEC: float = 60.0

    # === MEMORY OPTIMIZATION ===
    CACHE_USE_NUMPY: bool = True
    CACHE_MEMORY_LIMIT_MB: float = 500.0

    # === ORDER FLOW ANALYSIS ===
    ORDER_FLOW_ENABLED: bool = True
    ORDER_FLOW_DEPTH_LEVELS: int = 10
    ORDER_FLOW_IMBALANCE_THRESHOLD: float = 0.6
    ORDER_FLOW_CVD_WINDOW: int = 100
    ORDER_FLOW_LARGE_ORDER_THRESHOLD_USDT: float = 50000.0

    # === FUNDING RATE STRATEGY ===
    FUNDING_STRATEGY_ENABLED: bool = True
    FUNDING_PLAY_THRESHOLD: float = 0.0003
    FUNDING_TREND_PERIODS: int = 3

    # === MACHINE LEARNING ===
    ML_ENABLED: bool = False  # Off by default, opt-in
    ML_MODEL_TYPE: str = "gradient_boosting"
    ML_MODEL_PATH: str = ""
    ML_MIN_CONFIDENCE: float = 0.6
    ML_RETRAIN_ON_EXIT: bool = True
    ML_MIN_SAMPLES_FOR_TRAINING: int = 100
    ML_ENSEMBLE_WEIGHT: float = 0.4  # 40% ML, 60% rules

    # === PRE-ENTRY SLIPPAGE ESTIMATION ===
    SLIPPAGE_PRE_CHECK_ENABLED: bool = True
    SLIPPAGE_ORDERBOOK_DEPTH: int = 20

    # === LIQUIDITY CHECK ===
    LIQUIDITY_CHECK_ENABLED: bool = True
    LIQUIDITY_DEPTH_LEVELS: int = 10
    LIQUIDITY_MAX_IMPACT_PCT: float = 0.10  # Max 10% of visible liquidity

    # === TIME-BASED EXIT ===
    TIME_EXIT_ENABLED: bool = True
    MAX_HOLDING_MINUTES: float = 240.0  # 4 hours default
    TIME_EXIT_WARNING_MINUTES: float = 180.0  # Warn at 3 hours
    TIME_DECAY_START_PCT: float = 0.5  # Start decay at 50% of max time

    # === VOLATILITY-ADJUSTED TRAILING ===
    VOLATILITY_ADJUSTED_TRAILING: bool = True
    TRAILING_VOL_MULT_MIN: float = 0.5
    TRAILING_VOL_MULT_MAX: float = 2.0
    TRAILING_ATR_REFERENCE_PCT: float = 0.01  # 1% ATR = 1x multiplier

    # === DISTRIBUTED LOCKING ===
    DISTRIBUTED_LOCK_ENABLED: bool = False  # Off by default
    DISTRIBUTED_LOCK_TYPE: str = "file"  # "file" or "redis"
    DISTRIBUTED_LOCK_PATH: str = "~/.eclipse_locks/"
    DISTRIBUTED_REDIS_URL: str = ""  # redis://localhost:6379
    DISTRIBUTED_LOCK_TIMEOUT_SEC: float = 60.0
    DISTRIBUTED_STALE_LOCK_SEC: float = 120.0

    # === HEARTBEAT MONITORING ===
    HEARTBEAT_ENABLED: bool = True
    HEARTBEAT_DATA_LOOP_SEC: float = 30.0
    HEARTBEAT_SIGNAL_LOOP_SEC: float = 120.0
    HEARTBEAT_GUARDIAN_SEC: float = 15.0
    HEARTBEAT_ENTRY_LOOP_SEC: float = 60.0
    HEARTBEAT_ALERT_AFTER_MISS: int = 3
    HEARTBEAT_RECOVERY_COOLDOWN_SEC: float = 60.0

    def __post_init__(self):
        # Keep your sanity checks
        if not (0.0 < self.MAX_RISK_PER_TRADE <= 0.50):
            raise ValueError("MAX_RISK_PER_TRADE must be in (0, 0.50].")
        if not (0.0 < self.MAX_PORTFOLIO_HEAT <= 1.00):
            raise ValueError("MAX_PORTFOLIO_HEAT must be in (0, 1.00].")
        if self.MAX_CONCURRENT_POSITIONS < 1:
            raise ValueError("MAX_CONCURRENT_POSITIONS must be >= 1.")
        if self.LEVERAGE < 1:
            raise ValueError("LEVERAGE must be >= 1.")
        if not (0.0 < self.MIN_FILL_RATIO <= 1.0):
            raise ValueError("MIN_FILL_RATIO must be in (0, 1].")
        if not (0.0 < self.MIN_CONFIDENCE <= 1.0):
            raise ValueError("MIN_CONFIDENCE must be in (0, 1].")
        if not (0.0 <= self.MAX_DAILY_LOSS_PCT <= 1.0):
            raise ValueError("MAX_DAILY_LOSS_PCT must be in [0, 1].")
        if not (0.0 < self.CORRELATION_HEAT_CAP <= 1.0):
            raise ValueError("CORRELATION_HEAT_CAP must be in (0, 1].")

        # Keep ENTRY_MIN_CONFIDENCE aligned by default if user didn't override
        try:
            if float(self.ENTRY_MIN_CONFIDENCE or 0.0) <= 0:
                self.ENTRY_MIN_CONFIDENCE = float(self.MIN_CONFIDENCE)
        except Exception:
            pass


@dataclass
class MicroConfig(Config):
    """
    MICRO CAPITAL ASCENDANT MODE — 2026 v3.2
    Recommended when equity < $100.

    v3.2 core fix:
    - Confidence floor lowered to match real signal output distribution
    - Risk reduced to survive exchange minimums + slippage reality
    """

    # === RISK & PRESERVATION OVERRIDES (MICRO-SCALE) ===
    MAX_RISK_PER_TRADE: float = 0.06
    MAX_PORTFOLIO_HEAT: float = 0.15
    MAX_CONCURRENT_POSITIONS: int = 1
    MIN_RISK_DOLLARS: float = 0.0
    MAX_DAILY_LOSS_PCT: float = 0.20
    SYMBOL_COOLDOWN_MINUTES: int = 12

    # === CORRELATION & VELOCITY OVERRIDES (MICRO-SCALE) ===
    CORRELATION_HEAT_CAP: float = 0.12
    SESSION_EQUITY_PEAK_PROTECTION_PCT: float = 0.12
    VELOCITY_DRAWDOWN_PCT: float = 0.07
    VELOCITY_MINUTES: int = 5
    MIN_ATR_PCT_FOR_ENTRY: float = 0.006

    # === EXECUTION OVERRIDES ===
    LEVERAGE: int = 35
    MIN_FILL_RATIO: float = 0.80
    SLIPPAGE_MAX_PCT: float = 0.010

    # === REWARD STRUCTURE OVERRIDES (MICRO) ===
    STOP_ATR_MULT: float = 1.00
    MAX_STOP_PCT: float = 0.035
    BREAKEVEN_BUFFER_ATR_MULT: float = 0.20
    TP1_RR_MULT: float = 1.00
    TP2_RR_MULT: float = 2.20
    TRAILING_ACTIVATION_RR: float = 1.20
    TRAILING_CALLBACK_RATE: int = 40
    TRAILING_TIGHT_PCT: int = 30
    TRAILING_LOOSE_PCT: int = 70

    # === SIGNAL THRESHOLD OVERRIDE (MICRO) ===
    MIN_CONFIDENCE: float = 0.35
    MIN_CONFIDENCE_HIGH_VOL: float = 0.30

    # Mirror into entry-loop gate
    ENTRY_MIN_CONFIDENCE: float = 0.35

    # === MICRO MINIMUMS (MORE REALISTIC FOR $25–$99) ===
    MIN_NOTIONAL_USDT: float = 5.0
    MIN_MARGIN_USDT: float = 0.75
    MAX_ORDER_RETRIES: int = 3
    ORDER_RETRY_SLEEP_SEC: float = 0.35

    # Micro sizing fallback (if signal omits amount)
    FIXED_NOTIONAL_USDT: float = 8.0

    # === METADATA OVERRIDE ===
    CONFIG_VERSION: str = "micro-capital-ascendant-2026-v3"
    CONFIG_FORGED_DATE: str = "2026-01-07"
