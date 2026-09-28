# Warman Quant v0.5 — scan research

Run GitHub Actions as before; download the artifact, upload SCANNA.zip in ChatGPT. `scan.py` is an additional reproducible research scanner: `python scan.py output/SCANNA.zip --output scan_report.json`.

It filters to structurally eligible instruments, drops current unfinished hourly candle and current UTC-date daily candle, computes 1H EMA20/50, ATR14, 20-bar breakouts and prior-session Daily EMA50/200 regime. It warns if latest bar is stale; **this is not a complete exchange calendar**. No live orders, no automatic Nordnet prices, no performance claims. Daily exchange-local dates and session-aware 4H remain a further improvement; current 1H/Daily alignment is conservative but not a substitute for exchange calendars. Yahoo terms must be checked for company use.

## Manual live gate
1. Candidate from completed bars and sufficient history.
2. Verify event/news, source timestamps, exchange open and independent reference quote.
3. Select exact tradable Nordnet KF instrument; verify actual bid/ask, spread, leverage, knockout, FX and funding.
4. Underlying stop must map to product stop with room before knockout; estimate worst-case risk including gap/slippage. Do not assume a stop guarantees loss cap.
5. Max 1 new order per scan, initial budget 1% of capital; no trade if any gate fails.
6. Journal fill, exit and all costs. No evidence of edge yet: paper trade first.
