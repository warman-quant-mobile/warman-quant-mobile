# Warman Quant v6 — Crypto research, segregated capital

Crypto is not an institution-free market. Hypotheses: 24/7 regime transitions, forced deleveraging, fragmented spot/perpetual liquidity, funding dislocations and volatility clustering. These require timestamped venue-specific funding, open interest, liquidations and order-book snapshots; NEVER substitute synthetic values or claim these are currently tested.

## Deployed research in this branch
- BTC, ETH and SOL spot daily history (Yahoo proxies, source manifest).
- Chronological long-only daily Turtle 20-day breakout cash-backed portfolio research, 1% initial stop risk, max two concurrent holdings, 100% gross exposure cap, daily mark-to-market, gap-aware stop, 10-day channel exit next open, 20bps modeled round-trip costs.
- No broker orders, no perpetual leverage, no custody integration. Output portfolio_v6_report.json, equity and trade CSV.
- This is an **exploratory comparison**, NOT verified edge or a clean holdout. A separate untouched forward period is needed.

## Capital architecture (research design, not account instructions)
Core investment-company holdings and speculative research capital must have separate ledgers and risk budgets. Never finance speculative drawdowns from taxes, operating liquidity, or the long-only core. Stress at -20%, -40%, -60% crypto spot shock and venue outage before any position-size escalation.

## Remaining blockers to completion
- Durable external journal with cross-run checkpoint restore and fail-closed continuity. GitHub Actions cache alone is insufficient; existing paperdesk is still not production-grade.
- Proper instrument-specific calendar and point-in-time crypto exchange feed, fee tiers, spread, order-book depth, funding and borrow.
- Cross-asset portfolio mark-to-market across ALL strategy families; benchmark Investor/Berkshire adjusted for currencies and cash flows.
- Multiple-testing correction, anchored walk-forward and truly untouched forward observations.
- 1x/2x/3x cost and venue outage stress; independent implementation review.
- Never authorize live execution or large risk from an exploratory backtest.

## HARD NORDNET GATE (user mandate)
No candidate may be called executable or promoted without a specific Nordnet-listed instrument, confirmed eligibility in the company-owned KF, and a realistic instrument-level backtest. BTC/ETH/SOL spot are research signals only. ETPs trade during exchange sessions, not crypto's 24/7 schedule; weekend gaps, currency, issuer, tracking, spread and fees are material. See `nordnet_universe.json`. Funding/open-interest/liquidation signals may be researched as predictors, but no perpetual or short implementation without a matching verified Nordnet instrument. If no match, discard from tradable research queue.
