from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from cripto_auto_trade.data import choose_candles
from cripto_auto_trade.risk import RiskGuard
from cripto_auto_trade.strategies import build_strategy

LIVE_ACK = "I_UNDERSTAND_THIS_CAN_LOSE_MONEY"


def paper_once(strategy_name: str, data: str | None = None, quote_order_size: float = 25.0) -> dict[str, Any]:
    candles = choose_candles(data, False, "binance", "BTC/USDT", "1h", 350)
    signal = build_strategy(strategy_name).generate_signals(candles)[-1]
    decision = RiskGuard().check(signal, quote_order_size)
    price = candles[-1].close
    if not decision.allowed:
        return {"mode": "paper", "signal": signal.__dict__, "risk": decision.__dict__, "execution": None}
    state_path = Path("state/paper_state.json")
    log_path = Path("logs/paper_trades.csv")
    state = {"base": 0.0, "quote": 1000.0}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    base = float(state.get("base", 0.0))
    quote = float(state.get("quote", 1000.0))
    if signal.action == "BUY":
        spend = min(quote, decision.quote_order_size)
        fee = spend * 0.001
        qty = max(0.0, spend - fee) / price
        quote -= spend
        base += qty
        side = "BUY"
    else:
        qty = base
        fee = qty * price * 0.001
        quote += qty * price - fee
        base = 0.0
        side = "SELL"
    state = {"base": base, "quote": quote, "last_price": price}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    row = {"timestamp": signal.timestamp, "side": side, "price": price, "quantity": qty, "quote_after": quote, "base_after": base, "reason": signal.reason}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    return {"mode": "paper", "signal": signal.__dict__, "risk": decision.__dict__, "execution": row}


def live_once(strategy_name: str, exchange_id: str, symbol: str, timeframe: str, quote_order_size: float) -> dict[str, Any]:
    if os.getenv("CRIPTO_AUTO_TRADE_LIVE_ACK") != LIVE_ACK:
        raise PermissionError("live trading blocked: CRIPTO_AUTO_TRADE_LIVE_ACK is not set correctly")
    api_key = os.getenv("EXCHANGE_API_KEY")
    api_secret = os.getenv("EXCHANGE_API_SECRET")
    if not api_key or not api_secret:
        raise PermissionError("live trading blocked: EXCHANGE_API_KEY and EXCHANGE_API_SECRET are required")
    try:
        import ccxt  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError("Install live dependencies first: pip install -e '.[live]'") from exc
    exchange_cls: Any = getattr(ccxt, exchange_id)
    exchange = exchange_cls({"apiKey": api_key, "secret": api_secret, "enableRateLimit": True})
    candles = choose_candles(None, True, exchange_id, symbol, timeframe, 350)
    signal = build_strategy(strategy_name).generate_signals(candles)[-1]
    decision = RiskGuard().check(signal, quote_order_size)
    price = candles[-1].close
    if not decision.allowed:
        return {"mode": "live", "signal": signal.__dict__, "risk": decision.__dict__, "execution": None}
    if signal.action == "BUY":
        amount = decision.quote_order_size / price
        order = exchange.create_market_buy_order(symbol, amount)
    elif signal.action == "SELL":
        base_asset = symbol.split("/")[0]
        balance = exchange.fetch_balance()
        amount = float(balance.get("free", {}).get(base_asset, 0.0))
        if amount <= 0:
            return {"mode": "live", "signal": signal.__dict__, "risk": decision.__dict__, "execution": {"status": "skipped", "reason": "no base balance"}}
        order = exchange.create_market_sell_order(symbol, amount)
    else:
        order = {"status": "skipped", "reason": "hold"}
    return {"mode": "live", "signal": signal.__dict__, "risk": decision.__dict__, "execution": order}
