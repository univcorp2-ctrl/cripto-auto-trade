# Setup

## 1. Clone

```bash
git clone https://github.com/univcorp2-ctrl/cripto-auto-trade.git
cd cripto-auto-trade
```

## 2. Create environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install

```bash
pip install -e '.[dev,web,live]'
```

## 4. Test and validate

```bash
pytest
python -m cripto_auto_trade.cli validate --iterations 200
```

## 5. Open UI

```bash
python -m cripto_auto_trade.web
```

Open `http://127.0.0.1:8000`.

## 6. Real data validation

In the UI, set Data to `Live OHLCV` and click `Realtime Validate`.

CLI:

```bash
python -m cripto_auto_trade.cli realtime --live-data --exchange binance --symbol BTC/USDT --timeframe 1h
```
