from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "Candle":
        candle = cls(
            timestamp=str(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row.get("volume") or 0.0),
        )
        candle.validate()
        return candle

    def validate(self) -> None:
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError(f"non-positive OHLC at {self.timestamp}")
        if self.high < self.low:
            raise ValueError(f"high < low at {self.timestamp}")
        if not self.low <= self.open <= self.high:
            raise ValueError(f"open outside candle range at {self.timestamp}")
        if not self.low <= self.close <= self.high:
            raise ValueError(f"close outside candle range at {self.timestamp}")


@dataclass(frozen=True)
class Signal:
    timestamp: str
    action: str
    target_position: float
    regime: str
    reason: str
    risk_score: float = 0.0


@dataclass(frozen=True)
class Trade:
    timestamp: str
    side: str
    price: float
    quantity: float
    fee: float
    cash_after: float
    equity_after: float
    reason: str


@dataclass(frozen=True)
class BacktestResult:
    strategy: str
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float
    sharpe_like: float
    win_rate: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[str, float]] = field(default_factory=list)
    signals: list[Signal] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "initial_cash": round(self.initial_cash, 6),
            "final_equity": round(self.final_equity, 6),
            "total_return": round(self.total_return, 6),
            "max_drawdown": round(self.max_drawdown, 6),
            "sharpe_like": round(self.sharpe_like, 6),
            "win_rate": round(self.win_rate, 6),
            "trade_count": len(self.trades),
            "equity_curve": [
                {"timestamp": timestamp, "equity": round(equity, 6)}
                for timestamp, equity in self.equity_curve
            ],
            "trades": [trade.__dict__ for trade in self.trades],
            "latest_signal": self.signals[-1].__dict__ if self.signals else None,
        }
