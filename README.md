# Warman Quant Mobile v0.3 — research prototype

**No live-order authorization.** Yahoo/yfinance is unofficial. Verify corporate data-use rights. A green workflow means structural collection passed, NOT that any instrument is executable.

## Upgrade on iPhone (Safari)
Replace the root files `collector.py`, `validate.py`, `requirements.txt` and add `research_backtest.py`.
Replace `.github/workflows/collector.yml` with the supplied file. Do not retain an older duplicate workflow.
Commit to `main`. Actions → Warman Quant Collector → Run workflow.
Download the artifact; inside it `SCANNA.zip` contains the CSVs and reports. Upload `SCANNA.zip` in ChatGPT.

## Fixes
* Daily Yahoo session dates are preserved as `session_date`, not misrepresented as market-open UTC quotes.
* Intraday `timestamp_utc` is BAR START, not bar close. Latest still-forming hour is flagged; at scan time exclude any hour beginning at/after export's UTC hour. Actual exchange-specific calendar checks are still needed.
* Validator checks both intervals for at least 18 complete symbols, row counts, OHLC, duplicate timestamps; fails closed on errors.
* Indices and FX may have zero/unavailable volume: never treat as zero trading activity.
* 4H session-aware resampling and current Nordnet product quotes are not implemented.

## Exploratory test (optional, desktop/cloud)
`python research_backtest.py output/SCANNA.zip`
This fixed-rule research demonstration has 70/30 chronological split, next-bar-open entries, six-bar holds, 20 bps assumed round-trip cost, and DOES NOT model actual Nordnet product leverage, KO, spreads, slippage, FX conversion or financing. It cannot establish live trading edge. Intraday 60-day data is too short for robust validation.

## Important
Manual workflow only. This avoids GitHub scheduled job latency being mistaken for exact-time real-time availability. Snapshot must be checked for freshness before a scan.

## v0.4 update
- Isolates invalid source OHLC rows into `*_rejected.csv` for audit rather than changing prices.
- Each symbol is independently eligible/excluded. Workflow passes with at least 18 fully validated 1H+Daily symbols; excluded symbols are never trade candidates.
- Current UTC-date daily bars are marked provisional (conservative; actual session-calendar validation remains outstanding).
- `quality.json` contains `eligible_symbols` and `excluded_symbols`. A passing structural test does NOT establish fresh executable prices or live-trading readiness.
- Upgrade all root Python files and the workflow. Start a NEW Actions run, not a re-run of an old commit.

## v0.6 research-only addition
`economics_gate.py` sizes a **hypothetical** product trade using verified ask/bid, estimated executable stop/target bids, fees, financing/FX drag and a capital cap. See `GO_NO_GO.md`. This release does not enable live orders or assert a profitable strategy.
