# Cripto Auto Trade

![Cripto Auto Trade overview](docs/assets/hero-overview.svg)

A simple, visual crypto auto-trading repository with selectable strategies, backtesting, forward testing, real-time validation, paper trading, and guarded live trading.

> This is trading software, not a profit guarantee. Start with backtest and paper mode. Live trading can lose money.

## What you can do

![Strategy and validation flow](docs/assets/strategy-flow.svg)

- Choose a trading strategy from the UI.
- Compare backtest and forward-test results.
- Validate strategy health with live OHLCV data through CCXT.
- Run paper trading before live trading.
- Use guarded live trading only when API keys and live acknowledgement are set.
- Keep the screen simple: strategy, symbol, timeframe, result cards, chart, latest signal.

## Quick start

![Setup guide](docs/assets/setup-guide.svg)

```bash
git clone https://github.com/univcorp2-ctrl/cripto-auto-trade.git
cd cripto-auto-trade
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,web,live]'
pytest
python -m cripto_auto_trade.cli validate --iterations 200
python -m cripto_auto_trade.web
```

Open:

```text
http://127.0.0.1:8000
```

## Simple dashboard

![Dashboard UI](docs/assets/dashboard-ui.svg)

The dashboard gives you:

- strategy selector,
- exchange / symbol / timeframe inputs,
- backtest button,
- forward-test button,
- real-time validation button,
- metric cards,
- equity curve chart,
- strategy comparison table,
- latest live signal panel.

## Strategies users can choose

| Strategy | Best case | Weakness | Default role |
|---|---|---|---|
| `regime_guard` | Mixed market, trend + range + shock filter | More conservative, may skip pumps | Recommended default |
| `ema_cross` | Clean trend | Whipsaw in ranges | Simple trend follow |
| `donchian_trend` | Strong breakouts | False breakouts | Momentum/trend |
| `rsi_reversion` | Ranging majors | Dangerous in strong downtrend | Mean reversion |
| `bollinger_breakout` | Volatility expansion | Fake breakout | Breakout timing |

List strategies:

```bash
python -m cripto_auto_trade.cli list-strategies
```

Backtest one strategy:

```bash
python -m cripto_auto_trade.cli backtest --strategy regime_guard --data data/sample_btc_usdt_1h.csv
```

Forward test one strategy:

```bash
python -m cripto_auto_trade.cli forward-test --strategy regime_guard --data data/sample_btc_usdt_1h.csv
```

Run 200 validation loops:

```bash
python -m cripto_auto_trade.cli validate --iterations 200 --data data/sample_btc_usdt_1h.csv
```

## Real-time validation with real data

Real-time validation uses public OHLCV through CCXT when `--live-data` is set:

```bash
python -m cripto_auto_trade.cli realtime \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --strategy regime_guard \
  --live-data
```

The web UI has the same function through the `Realtime Validate` button.

## Paper trading

```bash
python -m cripto_auto_trade.cli paper-once --strategy regime_guard --data data/sample_btc_usdt_1h.csv
```

Paper state is saved under:

```text
state/paper_state.json
logs/paper_trades.csv
```

## Guarded live trading

Live trading is deliberately locked. All of these are required:

```bash
export EXCHANGE_ID=binance
export EXCHANGE_API_KEY='your_key'
export EXCHANGE_API_SECRET='your_secret'
export CRIPTO_AUTO_TRADE_LIVE_ACK='I_UNDERSTAND_THIS_CAN_LOSE_MONEY'
```

Then:

```bash
python -m cripto_auto_trade.cli live-once \
  --strategy regime_guard \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --quote-order-size 15
```

Use exchange API keys with withdrawals disabled. Start with very small size.

## Architecture

```mermaid
flowchart LR
  UI[Web Dashboard] --> API[FastAPI]
  API --> Catalog[Strategy Catalog]
  API --> Data[CSV or CCXT Live OHLCV]
  Data --> Backtest[Backtest + Forward Test]
  Catalog --> Signals[BUY / SELL / HOLD]
  Signals --> Risk[Risk Guard]
  Risk --> Paper[Paper Executor]
  Risk --> Live[CCXT Live Executor]
  Backtest --> UI
  Paper --> Logs[State + Logs]
  Live --> Exchange[Exchange]
```

## Production checklist

- Run `pytest`.
- Run `python -m cripto_auto_trade.cli validate --iterations 200`.
- Compare multiple strategies in the dashboard.
- Use live public data validation.
- Paper trade first.
- Use API keys without withdrawal permission.
- Start live with a tiny quote order size.
- Stop if real-time validation health turns poor.

## Important security note

Never paste GitHub tokens, exchange API keys, or secrets into chat, issues, README, commits, or logs. If a token is exposed, revoke it and create a new one.

## License

MIT
