# Live Trading

Live trading can lose money. This repo blocks live trading unless all safety switches are present.

## Required environment variables

```bash
export EXCHANGE_ID=binance
export EXCHANGE_API_KEY='your_key'
export EXCHANGE_API_SECRET='your_secret'
export CRIPTO_AUTO_TRADE_LIVE_ACK='I_UNDERSTAND_THIS_CAN_LOSE_MONEY'
```

## Run once

```bash
python -m cripto_auto_trade.cli live-once --strategy regime_guard --exchange binance --symbol BTC/USDT --timeframe 1h --quote-order-size 15
```

## Security rules

- Disable withdrawals on API keys.
- Use small order size first.
- Use IP allowlist if available.
- Start with paper mode.
- Stop if real-time validation gets worse.
