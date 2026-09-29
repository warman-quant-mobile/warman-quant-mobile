# Macro regime / Fidelity-inspired research specification

Research-only. Fidelity's business-cycle framework distinguishes early, mid, late and recession phases; it does NOT validate any 10R trade. See:
- https://institutional.fidelity.com/app/item/SCIC_D00001569/the-business-cycle-approach-to-equity-sector-investing.html
- https://www.fidelity.com/viewpoints/investing-ideas/sector-investing-business-cycle
- Daniel & Moskowitz, Momentum Crashes: https://www.nber.org/papers/w20439

## Proposed regime inputs (not yet collected)
- Policy rate and announcement timestamps: Fed, ECB, Riksbank; historical data must use what was known at the time.
- 2y/10y sovereign yields and curve slope; inflation releases and revisions; PMI/industrial activity; credit spreads.
- Real-time release calendar with availability timestamp to avoid look-ahead.
- Equity, bond and commodity market proxies with adjusted, consistent histories.

## Hypotheses to test independently
1. HIKING_ACCELERATION: consecutive hikes and rising front-end yields; examine equity-sector relative moves and long/short trends.
2. LATE_HIKING_PAUSE: unchanged policy rate following a hiking sequence; examine duration-sensitive assets and false dawns.
3. FIRST_CUT_STRESS: first cut accompanied by deteriorating credit/growth; do not assume immediate equity recovery.
4. FIRST_CUT_RECOVERY: first cut with stabilizing credit/growth; separately examine cyclical rebound.
5. CRASH_REVERSAL: >=20% trailing peak-to-close decline plus a completed-session reclaim of prior 20-session low. A watch, never an automatic buy.

## Validation gate
- Multiple historical cycles, point-in-time macro vintages, independent out-of-sample evaluation.
- Report event counts, realized R, hit rate, adverse gap fills, maximum drawdown, sensitivity to costs and alternative thresholds.
- Compare with unconditional market baseline, simple momentum and random entry matched on regime.
- Exclude incomplete or unverified macro data; never infer a central bank regime solely from prices.
- Only the existing manually verified 10R signal pipeline may surface a trade. No orders.
