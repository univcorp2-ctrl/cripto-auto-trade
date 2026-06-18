import pytest

from cripto_auto_trade.trader import live_once, paper_once
from cripto_auto_trade.web import create_app


def test_paper_once_runs() -> None:
    result = paper_once("ema_cross", None, 25)
    assert result["mode"] == "paper"
    assert "signal" in result


def test_live_requires_ack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRIPTO_AUTO_TRADE_LIVE_ACK", raising=False)
    with pytest.raises(PermissionError):
        live_once("regime_guard", "binance", "BTC/USDT", "1h", 15)


def test_web_app_health() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["service"] == "cripto-auto-trade"
