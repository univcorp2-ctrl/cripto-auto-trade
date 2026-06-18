from cripto_auto_trade.data import generate_sample_candles
from cripto_auto_trade.strategies import build_strategy, strategy_names


def test_all_strategies_generate_signals() -> None:
    candles = generate_sample_candles()
    for name in strategy_names():
        strategy = build_strategy(name)
        signals = strategy.generate_signals(candles)
        assert len(signals) == len(candles)
        assert signals[-1].action in {"BUY", "SELL", "HOLD"}


def test_unknown_strategy_rejected() -> None:
    try:
        build_strategy("does_not_exist")
    except ValueError as exc:
        assert "unknown strategy" in str(exc)
    else:
        raise AssertionError("expected ValueError")
