# Warman Quant — edge validation protocol (2026-09-29)

**Objective:** scalable asymmetric capital growth, not optimizing historical screenshots. No live orders authorized.

## Findings to preserve, including negative evidence

* Genuine claimed VIRBTC product OHLCV: 665 complete sessions, 2024-01-31 through 2026-09-28. User-provided source is not independently authenticated; missing 2024-09-16 volume remains a disclosed data-quality issue. The in-progress 2026-09-29 bar is excluded.
* Original VIRBTC breakout, 0.5% initial capital risk and 50% max initial exposure: SEK 25,814 ending equity, 10 completed trades; not a demonstrated growth engine.
* VIRBTC 2026 trend regime, 25k initial, SMA50: SEK 32,664 ending equity, 12.4% historical max drawdown at nominal 20bps roundtrip. **2026 was inspected; this is NOT out-of-sample evidence.**
* Diagnostic cross-market scan of user archive `Warman-Quant-Data 10.zip` (SHA256 `93595d9690713600412e5a999b1ce25b8072c298d57c3f3b5804b5bdce530fc1`): 22 eligible source series; SMA50 outperformed gross buy-and-hold in **5/22**, SMA60 in **6/22**. Fractional notional was used for cross-asset comparability (otherwise a 25k SEK account cannot buy a whole BTC); these are **not executable Nordnet product returns**. Source includes indices, continuous futures, FX and foreign-currency assets, with differing effective evaluation dates. No portfolio performance inference. Detailed audit held outside public repository; do not publish raw vendor data.

## Frozen research hypothesis H1

Long only when previous session's close is above the average of the N closes *preceding that previous session* (current research implementation). Evaluate N=50 and N=60 as predeclared adjacent sensitivity, **not choose a winner after seeing evaluation data**. Enter or exit at next session open, one position, cash-backed, no short/leverage, no 2R take profit, 10bps per side nominal, also 20 and 30bps per side stress. Mark open holdings to close. Benchmark net product buy-and-hold over identical dates and starting cash. Validate the exact signal indexing with tests before any forward evaluation.

## Promotion gates — all mandatory

1. Verify actual Nordnet-tradable instrument ISIN, SEK price, session calendar, issuer and product charges; do not replace exchange-traded product with crypto spot, NAV, index, futures proxy or synthetic candles.
2. Confirm source provenance and immutable raw + canonical hashes; no silent missing-value fills, retrospective revisions or incomplete-day use.
3. Independent tests: next-open chronology, cost/cash conservation, open-gap adverse fills, stop assumptions if used, missing sessions, no future-data leakage, benchmark alignment, forced final liquidation separately from mark-to-market.
4. Freeze implementation SHA, source SHA, start date, parameter grid and rejection thresholds **before** a prospective period. No retrospective parameter changes; record every observation and rejected candidate.
5. Compare net return, max drawdown, turnover, gap/tail exposure, trade distribution and largest winner contribution to net buy-and-hold and an uninvested cash reference; stress costs at 1x/2x/3x.
6. Show robustness on actual accessible product series. The 22-source diagnostic is a **falsification warning**, not cross-product confirmation.
7. Restore immutable, durable, replayable paper ledger; abort on missing/corrupt checkpoint. No silent journal reset.
8. Explicitly verify separate corporate operating/VAT liquidity and ask user for funding and manual launch approval. Initial proposed pilot 25k SEK is a proposal only. No automated order placement.

**Decision today:** RESEARCH_ONLY_BLOCKED. Cross-market evidence does not justify promoting the 50-day regime. Prioritize cross-market product mapping, independently prospective observations, and trustworthy journal before sizing optimization.
