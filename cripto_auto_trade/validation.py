from __future__ import annotations

from dataclasses import dataclass

from cripto_auto_trade.backtest import Backtester, forward_test
from cripto_auto_trade.models import Candle
from cripto_auto_trade.strategies import build_strategy, strategy_names


@dataclass(frozen=True)
class ValidationRow:
    strategy: str
    window: int
    start: int
    total_return: float
    max_drawdown: float
    sharpe_like: float
    trade_count: int
    verdict: str

    def as_dict(self) -> dict[str, object]:
        return self.__dict__


def run_validation_matrix(candles: list[Candle], iterations: int = 200) -> dict[str, object]:
    rows: list[ValidationRow] = []
    names = strategy_names()
    if len(candles) < 120:
        raise ValueError("validation needs at least 120 candles")
    min_window = min(120, len(candles))
    max_window = len(candles)
    for i in range(iterations):
        strategy_name = names[i % len(names)]
        strategy = build_strategy(strategy_name)
        window = min(max_window, min_window + (i * 17) % max(1, max_window - min_window + 1))
        start_space = max(1, len(candles) - window + 1)
        start = (i * 13) % start_space
        segment = candles[start : start + window]
        result = Backtester(strategy).run(segment)
        verdict = "healthy" if result.total_return > 0 and result.max_drawdown < 0.25 else "watch"
        if result.max_drawdown >= 0.35:
            verdict = "risk_high"
        rows.append(
            ValidationRow(
                strategy_name,
                window,
                start,
                round(result.total_return, 6),
                round(result.max_drawdown, 6),
                round(result.sharpe_like, 6),
                len(result.trades),
                verdict,
            )
        )
    summary = summarize_rows(rows)
    return {"iterations": iterations, "summary": summary, "rows": [row.as_dict() for row in rows]}


def summarize_rows(rows: list[ValidationRow]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for name in sorted({row.strategy for row in rows}):
        selected = [row for row in rows if row.strategy == name]
        positive = sum(1 for row in selected if row.total_return > 0)
        avg_return = sum(row.total_return for row in selected) / len(selected)
        avg_drawdown = sum(row.max_drawdown for row in selected) / len(selected)
        healthy = sum(1 for row in selected if row.verdict == "healthy")
        summary.append(
            {
                "strategy": name,
                "runs": len(selected),
                "positive_rate": round(positive / len(selected), 4),
                "healthy_rate": round(healthy / len(selected), 4),
                "avg_return": round(avg_return, 6),
                "avg_drawdown": round(avg_drawdown, 6),
            }
        )
    summary.sort(key=lambda row: (float(row["healthy_rate"]), float(row["avg_return"])), reverse=True)
    return summary


def compare_all_strategies(candles: list[Candle]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in strategy_names():
        result = Backtester(build_strategy(name)).run(candles)
        rows.append(result.as_dict())
    rows.sort(key=lambda row: (float(row["total_return"]), -float(row["max_drawdown"])), reverse=True)
    return rows


def forward_all_strategies(candles: list[Candle]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for name in strategy_names():
        rows.append(forward_test(build_strategy(name), candles))
    rows.sort(key=lambda row: float(row["forward"]["total_return"]), reverse=True)  # type: ignore[index]
    return rows
