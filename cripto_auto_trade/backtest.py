from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cripto_auto_trade.indicators import max_drawdown, sharpe_like
from cripto_auto_trade.models import BacktestResult, Candle, Trade
from cripto_auto_trade.strategies import Strategy


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 10_000.0
    fee_rate: float = 0.001
    slippage_bps: float = 5.0


class Backtester:
    def __init__(self, strategy: Strategy, config: BacktestConfig | None = None) -> None:
        self.strategy = strategy
        self.config = config or BacktestConfig()

    def run(self, candles: list[Candle]) -> BacktestResult:
        if len(candles) < 90:
            raise ValueError("at least 90 candles are recommended for meaningful validation")
        signals = self.strategy.generate_signals(candles)
        cash = self.config.initial_cash
        units = 0.0
        avg_entry = 0.0
        round_trips = 0
        wins = 0
        trades: list[Trade] = []
        equity_curve: list[tuple[str, float]] = []
        slippage = self.config.slippage_bps / 10_000
        for candle, signal in zip(candles, signals, strict=True):
            price = candle.close
            equity_before = cash + units * price
            target_units = equity_before * signal.target_position / price
            delta = target_units - units
            if abs(delta) > 1e-10:
                if delta > 0:
                    execution_price = price * (1 + slippage)
                    max_units = cash / (execution_price * (1 + self.config.fee_rate))
                    quantity = min(delta, max_units)
                    notional = quantity * execution_price
                    fee = notional * self.config.fee_rate
                    previous_units = units
                    cash -= notional + fee
                    units += quantity
                    avg_entry = (avg_entry * previous_units + execution_price * quantity) / units if units else 0.0
                    side = "BUY"
                else:
                    execution_price = price * (1 - slippage)
                    quantity = min(abs(delta), units)
                    notional = quantity * execution_price
                    fee = notional * self.config.fee_rate
                    cash += notional - fee
                    units -= quantity
                    side = "SELL"
                    if units <= 1e-10:
                        pnl = (execution_price - avg_entry) * quantity - fee
                        round_trips += 1
                        wins += 1 if pnl > 0 else 0
                        units = 0.0
                        avg_entry = 0.0
                equity_after = cash + units * price
                trades.append(Trade(candle.timestamp, side, execution_price, quantity, fee, cash, equity_after, signal.reason))
            equity_curve.append((candle.timestamp, cash + units * price))
        final_equity = equity_curve[-1][1]
        return BacktestResult(
            strategy=self.strategy.name,
            initial_cash=self.config.initial_cash,
            final_equity=final_equity,
            total_return=final_equity / self.config.initial_cash - 1,
            max_drawdown=max_drawdown([value for _, value in equity_curve]),
            sharpe_like=sharpe_like(equity_curve),
            win_rate=wins / round_trips if round_trips else 0.0,
            trades=trades,
            equity_curve=equity_curve,
            signals=signals,
        )


def forward_test(strategy: Strategy, candles: list[Candle], split_ratio: float = 0.7) -> dict[str, object]:
    if not 0.5 <= split_ratio <= 0.9:
        raise ValueError("split_ratio must be between 0.5 and 0.9")
    split = int(len(candles) * split_ratio)
    train = candles[:split]
    forward = candles[max(0, split - 90) :]
    train_result = Backtester(strategy).run(train)
    forward_result = Backtester(strategy).run(forward)
    return {
        "strategy": strategy.name,
        "split_index": split,
        "train": train_result.as_dict(),
        "forward": forward_result.as_dict(),
        "verdict": judge_forward(train_result.total_return, forward_result.total_return, forward_result.max_drawdown),
    }


def judge_forward(train_return: float, forward_return: float, forward_drawdown: float) -> str:
    if forward_return > 0 and forward_drawdown < 0.25:
        return "healthy"
    if train_return > 0 and forward_return < 0:
        return "overfit_or_regime_changed"
    if forward_drawdown >= 0.35:
        return "drawdown_too_high"
    return "watch"


def write_json(payload: object, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
