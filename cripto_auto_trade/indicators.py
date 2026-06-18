from __future__ import annotations

import math
from collections.abc import Sequence


def sma(values: Sequence[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    out: list[float | None] = []
    total = 0.0
    for i, value in enumerate(values):
        total += value
        if i >= window:
            total -= values[i - window]
        out.append(total / window if i + 1 >= window else None)
    return out


def ema(values: Sequence[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    if not values:
        return []
    alpha = 2 / (window + 1)
    out: list[float | None] = []
    current = values[0]
    for i, value in enumerate(values):
        current = value if i == 0 else alpha * value + (1 - alpha) * current
        out.append(current if i + 1 >= window else None)
    return out


def rsi(values: Sequence[float], window: int = 14) -> list[float | None]:
    if len(values) < 2:
        return [None for _ in values]
    out: list[float | None] = [None]
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
        if i < window:
            out.append(None)
            continue
        avg_gain = sum(gains[i - window : i]) / window
        avg_loss = sum(losses[i - window : i]) / window
        out.append(100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss))
    return out


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], window: int) -> list[float | None]:
    tr: list[float] = []
    for i, high in enumerate(highs):
        low = lows[i]
        if i == 0:
            tr.append(high - low)
        else:
            prev = closes[i - 1]
            tr.append(max(high - low, abs(high - prev), abs(low - prev)))
    return sma(tr, window)


def rolling_high(values: Sequence[float], window: int) -> list[float | None]:
    return [None if i + 1 < window else max(values[i + 1 - window : i + 1]) for i in range(len(values))]


def rolling_low(values: Sequence[float], window: int) -> list[float | None]:
    return [None if i + 1 < window else min(values[i + 1 - window : i + 1]) for i in range(len(values))]


def rolling_zscore(values: Sequence[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
            continue
        segment = values[i + 1 - window : i + 1]
        mean = sum(segment) / window
        variance = sum((value - mean) ** 2 for value in segment) / window
        std = math.sqrt(variance)
        out.append(0.0 if std == 0 else (values[i] - mean) / std)
    return out


def bollinger_bands(values: Sequence[float], window: int = 20, multiple: float = 2.0) -> tuple[list[float | None], list[float | None], list[float | None]]:
    middle = sma(values, window)
    upper: list[float | None] = []
    lower: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < window or middle[i] is None:
            upper.append(None)
            lower.append(None)
            continue
        segment = values[i + 1 - window : i + 1]
        mean = middle[i] or 0.0
        std = math.sqrt(sum((value - mean) ** 2 for value in segment) / window)
        upper.append(mean + multiple * std)
        lower.append(mean - multiple * std)
    return middle, upper, lower


def range_efficiency(values: Sequence[float], lookback: int, index: int) -> float | None:
    if index < lookback:
        return None
    displacement = abs(values[index] - values[index - lookback])
    path = sum(abs(values[i] - values[i - 1]) for i in range(index - lookback + 1, index + 1))
    return 0.0 if path == 0 else displacement / path


def max_drawdown(equity_values: Sequence[float]) -> float:
    peak = -math.inf
    worst = 0.0
    for value in equity_values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1)
    return abs(worst)


def sharpe_like(equity_curve: Sequence[tuple[str, float]], periods_per_year: int = 365 * 24) -> float:
    returns = [(equity_curve[i][1] / equity_curve[i - 1][1]) - 1 for i in range(1, len(equity_curve)) if equity_curve[i - 1][1] > 0]
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    return 0.0 if std == 0 else mean / std * math.sqrt(periods_per_year)
