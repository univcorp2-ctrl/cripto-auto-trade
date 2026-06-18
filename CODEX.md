# Agent Notes

## Commands

```bash
pip install -e '.[dev,web,live]'
ruff check .
pytest -q
python -m cripto_auto_trade.cli validate --iterations 200
python -m cripto_auto_trade.web
```

## Guardrails

- Never commit secrets.
- Keep live trading blocked unless ACK and exchange keys are set.
- Any new strategy must work in backtest, forward test, realtime validation, and UI comparison.
- Prefer simple UI changes over complex frameworks.
