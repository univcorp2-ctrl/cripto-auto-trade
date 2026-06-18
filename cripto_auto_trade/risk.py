from __future__ import annotations

from dataclasses import dataclass

from cripto_auto_trade.models import Signal


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    quote_order_size: float


@dataclass(frozen=True)
class RiskConfig:
    min_quote_order: float = 10.0
    max_quote_order: float = 25.0
    max_risk_score: float = 80.0


class RiskGuard:
    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()

    def check(self, signal: Signal, quote_order_size: float) -> RiskDecision:
        if signal.action == "HOLD":
            return RiskDecision(False, "no action", 0.0)
        if signal.risk_score > self.config.max_risk_score:
            return RiskDecision(False, "risk score too high", 0.0)
        if signal.action == "BUY" and quote_order_size < self.config.min_quote_order:
            return RiskDecision(False, "order below exchange-like minimum", 0.0)
        return RiskDecision(True, "risk checks passed", min(quote_order_size, self.config.max_quote_order))
