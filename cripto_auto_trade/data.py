from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from cripto_auto_trade.models import Candle


def generate_sample_candles(count: int = 360) -> list[Candle]:
    candles: list[Candle] = []
    price = 100.0
    for i in range(count):
        drift = 0.0025 if i < count * 0.38 else (-0.0018 if i < count * 0.62 else 0.001)
        cycle = math.sin(i / 9) * 0.008 + math.sin(i / 31) * 0.01
        shock = -0.08 if i in {160, 161} else (0.05 if i in {250, 251} else 0.0)
        prev = price
        price = max(5.0, price * (1 + drift + cycle + shock))
        high = max(prev, price) * 1.006
        low = min(prev, price) * 0.994
        candles.append(Candle(f"2026-01-01T{i:04d}:00:00Z", prev, high, low, price, 1000 + i))
    return candles


def load_candles_csv(path: str | Path | None) -> list[Candle]:
    if path is None or str(path) == "" or not Path(path).exists():
        return generate_sample_candles()
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [Candle.from_mapping(row) for row in csv.DictReader(handle)]


def fetch_live_ohlcv(exchange_id: str, symbol: str, timeframe: str, limit: int = 350) -> list[Candle]:
    try:
        import ccxt  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError("Install live dependencies first: pip install -e '.[live]'") from exc
    exchange_cls: Any = getattr(ccxt, exchange_id)
    exchange = exchange_cls({"enableRateLimit": True})
    rows = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    return [Candle(str(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in rows]


def choose_candles(data: str | None, live_data: bool, exchange: str, symbol: str, timeframe: str, limit: int) -> list[Candle]:
    if live_data:
        return fetch_live_ohlcv(exchange, symbol, timeframe, limit)
    return load_candles_csv(data)[-limit:]
