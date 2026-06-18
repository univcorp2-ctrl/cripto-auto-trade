from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cripto_auto_trade.backtest import Backtester, forward_test
from cripto_auto_trade.data import choose_candles
from cripto_auto_trade.strategies import build_strategy, strategy_descriptions, strategy_names
from cripto_auto_trade.trader import paper_once
from cripto_auto_trade.validation import compare_all_strategies, forward_all_strategies, run_validation_matrix

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"


def create_app() -> Any:
    try:
        from fastapi import FastAPI, Query
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:
        raise ImportError("Install web dependencies first: pip install -e '.[web]'") from exc

    app = FastAPI(title="Cripto Auto Trade", version="0.1.0")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"ok": "true", "service": "cripto-auto-trade"}

    @app.get("/api/strategies")
    def strategies() -> dict[str, object]:
        return {"strategies": strategy_descriptions()}

    @app.get("/api/backtest")
    def api_backtest(
        strategy: str = Query("regime_guard", enum=strategy_names()),
        data_source: str = "sample",
        exchange: str = "binance",
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        limit: int = 350,
    ) -> dict[str, object]:
        candles = choose_candles("data/sample_btc_usdt_1h.csv", data_source == "live", exchange, symbol, timeframe, limit)
        return Backtester(build_strategy(strategy)).run(candles).as_dict()

    @app.get("/api/forward-test")
    def api_forward(
        strategy: str = Query("regime_guard", enum=strategy_names()),
        data_source: str = "sample",
        exchange: str = "binance",
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        limit: int = 350,
    ) -> dict[str, object]:
        candles = choose_candles("data/sample_btc_usdt_1h.csv", data_source == "live", exchange, symbol, timeframe, limit)
        return forward_test(build_strategy(strategy), candles)

    @app.get("/api/realtime")
    def api_realtime(
        strategy: str = Query("regime_guard", enum=strategy_names()),
        exchange: str = "binance",
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        live: bool = False,
        limit: int = 350,
    ) -> dict[str, object]:
        candles = choose_candles("data/sample_btc_usdt_1h.csv", live, exchange, symbol, timeframe, limit)
        result = Backtester(build_strategy(strategy)).run(candles).as_dict()
        result["source"] = "live" if live else "sample"
        result["symbol"] = symbol
        result["timeframe"] = timeframe
        return result

    @app.get("/api/compare")
    def api_compare(data_source: str = "sample", exchange: str = "binance", symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 350) -> dict[str, object]:
        candles = choose_candles("data/sample_btc_usdt_1h.csv", data_source == "live", exchange, symbol, timeframe, limit)
        return {"backtest": compare_all_strategies(candles), "forward": forward_all_strategies(candles)}

    @app.get("/api/validate")
    def api_validate(iterations: int = 200, data_source: str = "sample", exchange: str = "binance", symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 350) -> dict[str, object]:
        candles = choose_candles("data/sample_btc_usdt_1h.csv", data_source == "live", exchange, symbol, timeframe, limit)
        return run_validation_matrix(candles, iterations)

    @app.post("/api/paper-once")
    def api_paper(strategy: str = Query("regime_guard", enum=strategy_names()), quote_order_size: float = 25.0) -> dict[str, object]:
        return paper_once(strategy, "data/sample_btc_usdt_1h.csv", quote_order_size)

    return app


def main() -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError("Install web dependencies first: pip install -e '.[web]'") from exc
    uvicorn.run("cripto_auto_trade.web:create_app", factory=True, host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
