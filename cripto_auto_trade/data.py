from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from cripto_auto_trade.models import Candle


def load_candles_csv(path: str | Path) -> list[Candle]:
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
    candles: list[Candle] = []
    for row in rows:
        timestamp, open_, high, low, close, volume = row[:6]
        candles.append(Candle(str(timestamp), float(open_), float(high), float(low), float(close), float(volume)))
    return candles


def choose_candles(data: str | None, live_data: bool, exchange: str, symbol: str, timeframe: str, limit: int) -> list[Candle]:
    if live_data:
        return fetch_live_ohlcv(exchange, symbol, timeframe, limit)
    return load_candles_csv(data or "data/sample_btc_usdt_1h.csv")[-limit:]
