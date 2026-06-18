from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cripto_auto_trade.indicators import (
    atr,
    bollinger_bands,
    ema,
    range_efficiency,
    rolling_high,
    rolling_low,
    rolling_zscore,
    rsi,
)
from cripto_auto_trade.models import Candle, Signal


class Strategy(Protocol):
    name: str

    def generate_signals(self, candles: list[Candle]) -> list[Signal]: ...


def _make_signal(candle: Candle, previous: float, target: float, regime: str, reason: str, risk: float = 0.0) -> Signal:
    action = "HOLD"
    if target > previous:
        action = "BUY"
    elif target < previous:
        action = "SELL"
    return Signal(candle.timestamp, action, round(target, 6), regime, reason, round(risk, 2))


@dataclass(frozen=True)
class RegimeGuardStrategy:
    name: str = "regime_guard"
    fast_ema: int = 20
    slow_ema: int = 80
    atr_window: int = 14
    breakout_lookback: int = 55
    z_window: int = 40
    max_atr_ratio: float = 0.08
    shock_atr_multiple: float = 3.0
    efficiency_threshold: float = 0.25
    max_position: float = 1.0
    sideways_position: float = 0.35

    def generate_signals(self, candles: list[Candle]) -> list[Signal]:
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        fast = ema(closes, self.fast_ema)
        slow = ema(closes, self.slow_ema)
        atrs = atr(highs, lows, closes, self.atr_window)
        zs = rolling_zscore(closes, self.z_window)
        target = 0.0
        out: list[Signal] = []
        min_history = max(self.slow_ema + 10, self.breakout_lookback + 1, self.z_window, self.atr_window + 1)
        for i, candle in enumerate(candles):
            previous = target
            if i < min_history or fast[i] is None or slow[i] is None or atrs[i] is None or zs[i] is None:
                out.append(_make_signal(candle, previous, 0.0, "warmup", "not enough history"))
                continue
            previous_high = max(highs[i - self.breakout_lookback : i])
            previous_low = min(lows[i - self.breakout_lookback : i])
            atr_ratio = (atrs[i] or 0.0) / candle.close
            prev_atr = atrs[i - 1] or atrs[i] or 0.0
            true_range = max(candle.high - candle.low, abs(candle.high - candles[i - 1].close), abs(candle.low - candles[i - 1].close))
            shock = atr_ratio > self.max_atr_ratio or (prev_atr > 0 and true_range > self.shock_atr_multiple * prev_atr)
            risk = min(100.0, 100.0 * atr_ratio / self.max_atr_ratio)
            efficiency = range_efficiency(closes, self.breakout_lookback, i) or 0.0
            trend_up = candle.close > (slow[i] or 0.0) and (fast[i] or 0.0) > (slow[i] or 0.0) and efficiency >= self.efficiency_threshold
            trend_down = candle.close < (slow[i] or 0.0) and (fast[i] or 0.0) < (slow[i] or 0.0)
            if shock:
                target = 0.0
                out.append(_make_signal(candle, previous, target, "shock", "exit/avoid shock volatility", risk))
            elif trend_down:
                target = 0.0
                out.append(_make_signal(candle, previous, target, "trend_down", "flat during downtrend", risk))
            elif trend_up and candle.close > previous_high:
                target = self.max_position
                out.append(_make_signal(candle, previous, target, "trend_up", "Donchian breakout with trend filter", risk))
            elif previous > 0 and (candle.close < previous_low or candle.close < (slow[i] or 0.0)):
                target = 0.0
                out.append(_make_signal(candle, previous, target, "trend_exit", "price broke exit reference", risk))
            elif target == 0.0 and (zs[i] or 0.0) <= -1.8:
                target = self.sideways_position
                out.append(_make_signal(candle, previous, target, "sideways", "small mean reversion entry", risk))
            elif target > 0 and (zs[i] or 0.0) >= 0.4:
                target = 0.0
                out.append(_make_signal(candle, previous, target, "sideways_exit", "mean reversion recovered", risk))
            else:
                out.append(_make_signal(candle, previous, target, "wait", "no confirmed edge", risk))
        return out


@dataclass(frozen=True)
class EmaCrossStrategy:
    name: str = "ema_cross"
    fast_ema: int = 12
    slow_ema: int = 48
    target_position: float = 1.0

    def generate_signals(self, candles: list[Candle]) -> list[Signal]:
        closes = [c.close for c in candles]
        fast = ema(closes, self.fast_ema)
        slow = ema(closes, self.slow_ema)
        target = 0.0
        out: list[Signal] = []
        for i, candle in enumerate(candles):
            previous = target
            if i < self.slow_ema or fast[i] is None or slow[i] is None:
                out.append(_make_signal(candle, previous, 0.0, "warmup", "not enough history"))
                continue
            if (fast[i] or 0.0) > (slow[i] or 0.0):
                target = self.target_position
                out.append(_make_signal(candle, previous, target, "trend_up", "fast EMA above slow EMA"))
            else:
                target = 0.0
                out.append(_make_signal(candle, previous, target, "trend_down", "fast EMA below slow EMA"))
        return out


@dataclass(frozen=True)
class DonchianTrendStrategy:
    name: str = "donchian_trend"
    lookback: int = 55
    target_position: float = 1.0

    def generate_signals(self, candles: list[Candle]) -> list[Signal]:
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        high_band = rolling_high(highs, self.lookback)
        low_band = rolling_low(lows, self.lookback)
        target = 0.0
        out: list[Signal] = []
        for i, candle in enumerate(candles):
            previous = target
            if i <= self.lookback or high_band[i - 1] is None or low_band[i - 1] is None:
                out.append(_make_signal(candle, previous, 0.0, "warmup", "not enough history"))
                continue
            if candle.close > (high_band[i - 1] or 0.0):
                target = self.target_position
                out.append(_make_signal(candle, previous, target, "breakout_up", "close broke previous channel high"))
            elif candle.close < (low_band[i - 1] or 0.0):
                target = 0.0
                out.append(_make_signal(candle, previous, target, "breakout_down", "close broke previous channel low"))
            else:
                out.append(_make_signal(candle, previous, target, "channel", "inside channel"))
        return out


@dataclass(frozen=True)
class RsiReversionStrategy:
    name: str = "rsi_reversion"
    rsi_window: int = 14
    atr_window: int = 14
    entry_rsi: float = 30.0
    exit_rsi: float = 52.0
    target_position: float = 0.5
    max_atr_ratio: float = 0.08

    def generate_signals(self, candles: list[Candle]) -> list[Signal]:
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        rsis = rsi(closes, self.rsi_window)
        atrs = atr(highs, lows, closes, self.atr_window)
        target = 0.0
        out: list[Signal] = []
        for i, candle in enumerate(candles):
            previous = target
            if i < max(self.rsi_window, self.atr_window) or rsis[i] is None or atrs[i] is None:
                out.append(_make_signal(candle, previous, 0.0, "warmup", "not enough history"))
                continue
            atr_ratio = (atrs[i] or 0.0) / candle.close
            risk = min(100.0, 100.0 * atr_ratio / self.max_atr_ratio)
            if atr_ratio > self.max_atr_ratio:
                target = 0.0
                out.append(_make_signal(candle, previous, target, "shock", "avoid mean reversion during shock", risk))
            elif target == 0.0 and (rsis[i] or 0.0) <= self.entry_rsi:
                target = self.target_position
                out.append(_make_signal(candle, previous, target, "oversold", "RSI oversold entry", risk))
            elif target > 0.0 and (rsis[i] or 0.0) >= self.exit_rsi:
                target = 0.0
                out.append(_make_signal(candle, previous, target, "recovered", "RSI recovery exit", risk))
            else:
                out.append(_make_signal(candle, previous, target, "range_wait", "RSI between thresholds", risk))
        return out


@dataclass(frozen=True)
class BollingerBreakoutStrategy:
    name: str = "bollinger_breakout"
    window: int = 20
    multiple: float = 2.0
    trend_ema: int = 80
    target_position: float = 0.75

    def generate_signals(self, candles: list[Candle]) -> list[Signal]:
        closes = [c.close for c in candles]
        middle, upper, _lower = bollinger_bands(closes, self.window, self.multiple)
        trend = ema(closes, self.trend_ema)
        target = 0.0
        out: list[Signal] = []
        for i, candle in enumerate(candles):
            previous = target
            if i < max(self.window, self.trend_ema) or middle[i] is None or upper[i] is None or trend[i] is None:
                out.append(_make_signal(candle, previous, 0.0, "warmup", "not enough history"))
                continue
            if target == 0.0 and candle.close > (upper[i] or 0.0) and candle.close > (trend[i] or 0.0):
                target = self.target_position
                out.append(_make_signal(candle, previous, target, "volatility_expansion", "Bollinger breakout with trend filter"))
            elif target > 0 and candle.close < (middle[i] or 0.0):
                target = 0.0
                out.append(_make_signal(candle, previous, target, "breakout_exit", "close below Bollinger middle"))
            else:
                out.append(_make_signal(candle, previous, target, "breakout_wait", "waiting for clean expansion"))
        return out


STRATEGY_BUILDERS = {
    "regime_guard": RegimeGuardStrategy,
    "ema_cross": EmaCrossStrategy,
    "donchian_trend": DonchianTrendStrategy,
    "rsi_reversion": RsiReversionStrategy,
    "bollinger_breakout": BollingerBreakoutStrategy,
}


def strategy_names() -> list[str]:
    return sorted(STRATEGY_BUILDERS)


def strategy_descriptions() -> list[dict[str, str]]:
    return [
        {"name": "regime_guard", "label": "Regime Guard", "style": "trend + range + shock filter", "best_for": "mixed markets", "risk": "may skip fast pumps"},
        {"name": "ema_cross", "label": "EMA Cross", "style": "trend follow", "best_for": "clean trends", "risk": "range whipsaw"},
        {"name": "donchian_trend", "label": "Donchian Trend", "style": "breakout", "best_for": "strong breakouts", "risk": "fake breakout"},
        {"name": "rsi_reversion", "label": "RSI Reversion", "style": "mean reversion", "best_for": "ranges", "risk": "strong downtrend"},
        {"name": "bollinger_breakout", "label": "Bollinger Breakout", "style": "volatility expansion", "best_for": "expansion phases", "risk": "upper-wick reversal"},
    ]


def build_strategy(name: str) -> Strategy:
    if name not in STRATEGY_BUILDERS:
        raise ValueError(f"unknown strategy: {name}")
    return STRATEGY_BUILDERS[name]()
