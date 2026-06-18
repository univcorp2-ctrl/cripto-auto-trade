from cripto_auto_trade.backtest import Backtester, forward_test
from cripto_auto_trade.data import generate_sample_candles
from cripto_auto_trade.strategies import build_strategy
from cripto_auto_trade.validation import compare_all_strategies, run_validation_matrix


def test_backtest_and_forward() -> None:
    candles = generate_sample_candles()
    result = Backtester(build_strategy("regime_guard")).run(candles)
    assert result.final_equity > 0
    payload = forward_test(build_strategy("regime_guard"), candles)
    assert payload["verdict"] in {"healthy", "overfit_or_regime_changed", "drawdown_too_high", "watch"}


def test_validation_matrix() -> None:
    candles = generate_sample_candles()
    result = run_validation_matrix(candles, iterations=20)
    assert result["iterations"] == 20
    assert len(result["summary"]) >= 1


def test_compare_all_strategies() -> None:
    candles = generate_sample_candles()
    rows = compare_all_strategies(candles)
    assert len(rows) >= 5
