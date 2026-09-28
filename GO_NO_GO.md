# Warman Quant v0.6 — economics gate / no live approval

## Portfolio decision gate
Compare active trading against a passive Investor/Berkshire (or diversified index) alternative. Track deposits, total return, drawdown, time spent, and all costs. Do not infer edge from a single signal or a synthetic fixture.

## Mandatory before any executable instruction
- Validated, sufficiently fresh underlying candles; market session and futures contract correctly mapped.
- Walk-forward/out-of-sample backtest with no lookahead or overlapping positions; realistic spread, slippage, financing, FX and product availability; forward paper trading.
- Exact Nordnet product identifier/ISIN, KID/terms, underlying contract, current timestamped bid/ask, multiplier/parity, financing and KO/stop levels.
- Underlying stop mapped to **estimated executable product bid**, not inferred from headline leverage alone.
- Position cap and risk cap; check full-stake-loss/KO scenario separately. A stop order cannot guarantee 1% maximum loss.
- Positive net expected value and adequate benefit relative to work and passive alternative; otherwise NO TRADE.
- No order submission or automation of brokerage account. Manual user execution only.

## Demonstration economics
`python economics_gate.py --ask 20 --bid 19.8 --stop-bid 19 --target-bid 23 --fees 20 --carry 20`
All example values are fictional. Outputs are scenario arithmetic, not a trade instruction. The max-allocation default is 25% of equity and risk budget default is 1%; both may be adjusted only deliberately.

## Research status
Current 1H breakout scanner is exploratory; Yahoo futures continuous-series/roll issues and exchange-session handling remain unvalidated. Do not promote WATCH to ORDER automatically.
