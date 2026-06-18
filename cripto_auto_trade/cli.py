from __future__ import annotations

import argparse
import json

from cripto_auto_trade.backtest import Backtester, forward_test
from cripto_auto_trade.data import choose_candles, load_candles_csv
from cripto_auto_trade.strategies import build_strategy, strategy_descriptions, strategy_names
from cripto_auto_trade.trader import live_once, paper_once
from cripto_auto_trade.validation import compare_all_strategies, forward_all_strategies, run_validation_matrix


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cripto Auto Trade")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-strategies")
    backtest = sub.add_parser("backtest")
    backtest.add_argument("--strategy", choices=strategy_names(), default="regime_guard")
    backtest.add_argument("--data", default="data/sample_btc_usdt_1h.csv")
    forward = sub.add_parser("forward-test")
    forward.add_argument("--strategy", choices=strategy_names(), default="regime_guard")
    forward.add_argument("--data", default="data/sample_btc_usdt_1h.csv")
    validate = sub.add_parser("validate")
    validate.add_argument("--iterations", type=int, default=200)
    validate.add_argument("--data", default="data/sample_btc_usdt_1h.csv")
    realtime = sub.add_parser("realtime")
    realtime.add_argument("--strategy", choices=strategy_names(), default="regime_guard")
    realtime.add_argument("--exchange", default="binance")
    realtime.add_argument("--symbol", default="BTC/USDT")
    realtime.add_argument("--timeframe", default="1h")
    realtime.add_argument("--limit", type=int, default=350)
    realtime.add_argument("--live-data", action="store_true")
    paper = sub.add_parser("paper-once")
    paper.add_argument("--strategy", choices=strategy_names(), default="regime_guard")
    paper.add_argument("--data", default="data/sample_btc_usdt_1h.csv")
    paper.add_argument("--quote-order-size", type=float, default=25.0)
    live = sub.add_parser("live-once")
    live.add_argument("--strategy", choices=strategy_names(), default="regime_guard")
    live.add_argument("--exchange", default="binance")
    live.add_argument("--symbol", default="BTC/USDT")
    live.add_argument("--timeframe", default="1h")
    live.add_argument("--quote-order-size", type=float, default=15.0)
    sub.add_parser("compare")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list-strategies":
        print(json.dumps(strategy_descriptions(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "backtest":
        result = Backtester(build_strategy(args.strategy)).run(load_candles_csv(args.data))
        print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "forward-test":
        print(json.dumps(forward_test(build_strategy(args.strategy), load_candles_csv(args.data)), indent=2, ensure_ascii=False))
        return 0
    if args.command == "validate":
        print(json.dumps(run_validation_matrix(load_candles_csv(args.data), args.iterations), indent=2, ensure_ascii=False))
        return 0
    if args.command == "realtime":
        candles = choose_candles(None, args.live_data, args.exchange, args.symbol, args.timeframe, args.limit)
        result = Backtester(build_strategy(args.strategy)).run(candles)
        print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "paper-once":
        print(json.dumps(paper_once(args.strategy, args.data, args.quote_order_size), indent=2, ensure_ascii=False))
        return 0
    if args.command == "live-once":
        print(json.dumps(live_once(args.strategy, args.exchange, args.symbol, args.timeframe, args.quote_order_size), indent=2, ensure_ascii=False, default=str))
        return 0
    if args.command == "compare":
        candles = load_candles_csv("data/sample_btc_usdt_1h.csv")
        print(json.dumps({"backtest": compare_all_strategies(candles), "forward": forward_all_strategies(candles)}, indent=2, ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
