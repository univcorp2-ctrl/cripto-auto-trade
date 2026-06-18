# Trading Strategies

## `regime_guard`

Recommended default. It combines EMA trend, Donchian breakout, ATR shock filter, z-score mean reversion, and range efficiency.

Rules:

- Long only.
- Avoid shock volatility.
- Avoid downtrend.
- Buy breakout only when trend is clean.
- Small mean-reversion entries only in sideways conditions.

## `ema_cross`

- Buy when fast EMA is above slow EMA.
- Sell when fast EMA is below slow EMA.

Simple and transparent, but weak during ranges.

## `donchian_trend`

- Buy previous channel breakout.
- Exit previous channel breakdown.

Good for strong breakouts, weak against fake breakouts.

## `rsi_reversion`

- Buy oversold RSI.
- Exit on RSI recovery.
- Exit/avoid shock volatility.

Good for ranges, dangerous in persistent downtrends.

## `bollinger_breakout`

- Buy upper band breakout with trend filter.
- Exit below middle band.

Good during volatility expansion.
