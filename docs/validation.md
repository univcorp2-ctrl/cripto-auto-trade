# Validation

This repo validates strategy health in three layers.

## 1. Backtest

Runs the strategy over candles.

## 2. Forward test

Splits candles into an earlier period and a later forward period. The strategy is not optimized here; this is a simple overfit/regime-change check.

## 3. Realtime validation

Uses public live OHLCV through CCXT when live dependencies are installed.

## 4. Matrix validation

```bash
python -m cripto_auto_trade.cli validate --iterations 200
```

This runs deterministic rolling windows across all strategies and reports positive rate, healthy rate, average return, and average drawdown.
