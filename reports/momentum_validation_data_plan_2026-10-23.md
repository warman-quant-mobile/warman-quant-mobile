# Momentum Leaders: validation status and data migration plan (2026-10-23)

**Status: NOT VALIDATED. Research only. Do not issue live signals from historical CAGR.**

Latest inspected published report: `reports/momentum_leaders_report.json`, generated 2026-10-22T05:26:30Z.
- 6-month, top-five: **8 valid diagnostic months / 110**; 102 failed. There is no reportable full-period CAGR, max drawdown, or untouched holdout.
- The previous 36.0% annualized result is **invalidated/unverified**, not a strategy estimate.
- 98% universe-coverage gate is not satisfied historically. Historical US universe snapshot membership is community-maintained; delisted/renamed security histories are missing.
- OMXS30 historical point-in-time members and constituent returns remain unavailable.

## Already corrected in momentum_leaders.py (v2)
- Explicit PIT membership snapshot lookup and monthly universe coverage audit.
- Stale price rejection (max five calendar days).
- Selection at month-end, fills at next available market opening, and rejection of missing exit prices.
- USD/SEK conversion using prior daily FX close proxy; USD share execution and SEK benchmark separated.
- Provisional dividend-adjusted Investor B comparator and conservative 25 bps each side.
- Missing months do **not** get silently dropped from annualized full-period CAGR.
- Reports retain explicit research_only/validated_edge=false/trading_authorized=false.

## Blocking dataset upgrade
A reproducible survivorship-aware source with corporate actions, mergers, delisting proceeds, ticker identity mappings, and effective-date constituent membership is required. Two possible paths:
1. Norgate Data Platinum: US listed/delisted stocks + PIT S&P 500 and Nasdaq 100 memberships, official details https://norgatedata.com/data-content-tables.php ; Windows integration and paid license required. Their trial is capped at two years of history, so cannot validate the whole 2017-2026 sample (https://norgatedata.com/data-package-faq.php).
2. QuantConnect LEAN hosted research/backtesting: dynamic ETF constituent universes and delisted US equities, official docs https://www.quantconnect.com/docs/v2/writing-algorithms/universes/equity/etf-constituents-universes and https://www.quantconnect.com/docs/v2/writing-algorithms/universes/equity/fundamental-universes. Need workspace access and verification of exact historical SPY/QQQ constituents availability/licensing. Results must be reproduced within their platform; do not presume data export rights.

For OMXS30, obtain dated constituent history from Nasdaq or a licensed provider. Verify changes' effective dates, dual share classes and de-listings. Do not silently substitute today's constituents.

## Acceptance criteria before announcing a result
- >=98% PIT membership and price coverage **throughout** 2017-2026; audit all unresolved symbols and delistings, do not silently skip exits.
- Timestamp-safe signals and next-session executable fills; price adjustments and dividends reconciled.
- USD/SEK costs and actual Nordnet KF dealing friction; same SEK calendar for Investor B total-return benchmark.
- Full consecutive monthly returns, CAGR, drawdown, turnover, comparison to Investor, stress regimes and clearly untouched OOS; avoid selecting best of eight variants on OOS.
- Only announce a newly verified test if all gates pass; otherwise keep research_only and no trading authorization.

The current forward-looking investment process in `reports/momentum_forward_playbook_2026-10-21.md` is separate from historical validation.
