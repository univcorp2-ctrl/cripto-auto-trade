from cripto_auto_trade.indicators import bollinger_bands, ema, max_drawdown, rsi, sma


def test_indicators_lengths() -> None:
    values = [float(i) for i in range(1, 50)]
    assert sma(values, 5)[-1] == 47.0
    assert len(ema(values, 8)) == len(values)
    assert len(rsi(values, 14)) == len(values)
    middle, upper, lower = bollinger_bands(values, 20)
    assert middle[-1] is not None
    assert upper[-1] is not None
    assert lower[-1] is not None


def test_max_drawdown() -> None:
    assert max_drawdown([100, 120, 90, 130]) == 0.25
