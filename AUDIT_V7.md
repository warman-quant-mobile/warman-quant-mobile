# Independent audit v7 — BLOCKED FOR TRADING

## Evidence reviewed
Artifact from GitHub run 36530159621: 119 crypto spot-proxy closed trades, initial 100,000, reported final marked equity 862,198.88; period 2016-09-29 to 2026-09-27. Three very large individual winners: BTC 2020-10-11 to 2021-03-25 ~171,594, SOL 2023-10-20 to 2024-01-08 ~166,832, ETH 2020-10-13 to 2021-02-24 ~92,017. This is historical crypto spot exposure, not a verified Nordnet strategy or ten-year Nordnet ETP backtest. Do not extrapolate.

## Confirmed defects and controls
1. Previous portfolio charged both entry and exit fees only on exit; open equity omitted entry fees. v7 charges entry fee immediately, exit fee upon exit; limits entry quantity to available cash including fee. Previous headline result is superseded and invalid for trading decisions.
2. Journal cache restore-keys can silently restore unrelated/stale snapshot, and paperdesk.py silently initializes a fresh 100k state when absent. Scheduled paperdesk is QUARANTINED; neither cache restore nor save nor paperdesk processing runs. audit_journal.py records why continuity is unverified without resetting.
3. Existing 10-test suite proved little about executable prices, survivorship, exchange hours, gaps, or independent strategy edge. Additional invariants are added; no promotion is permitted.
4. No confirmed matching Nordnet company-KF instrument data; Yahoo 24/7 crypto spot cannot stand in for exchange-hours ETP fills.
5. Current 'holdout' has been repeatedly inspected while developing strategy families, so it is no longer untouched. The 506 hypotheses are correlated and subject to multiple comparisons. Hourly Yahoo history is limited.
6. Marked crypto historical equity is dominated by long historical trends. Compare to buy-and-hold BTC/ETH/SOL, cash and core benchmarks over identical availability windows before any alpha claim.
7. Existing research simulator has potential same-bar fill/stop ambiguity, simplified Turtle exits, independent notional trade compounding, and incomplete currency/corporate-action/futures-roll modeling. All its performance outputs are exploratory only.

## Conditions for any future trading status
- An identified Nordnet product with ISIN, actual historical traded product OHLC, spread, currency, fees, corporate actions, session/holiday calendar and eligibility confirmed in the user's company KF.
- Independent daily chronological ledger with deterministic replay, persisted immutable checkpoint and fail-closed recovery; mark-to-market reconciles with cash and open positions.
- Independent implementation cross-check, zero-lookahead tests, adversarial gap and simultaneous-bar tests, cost/impact stress, passive benchmark and untouched future evaluation.
- No orders or real-money sizing are enabled in this repository. Research outputs must always display validated_edge=false, nordnet_executable=false.
