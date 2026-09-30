# Warman Quant Research Mandate v3

Effective: 2026-09-30. Research only; no live broker orders.

## Objective and champion
Find robust, implementable sources of positive expected return that add value after realistic costs versus simple passive exposure. Passive long-term exposure is the champion/default. If evidence is insufficient, the correct conclusion is NO TRADE / PASSIVE CHAMPION. Research strategies are challengers, not assumed improvements.

## Autonomous hypothesis program
Kvanta should generate, freeze, test and attempt to falsify hypotheses without requiring user-supplied ideas. Priority families:
1. Time-series momentum/trend.
2. Cross-sectional momentum/relative strength.
3. Mean reversion after objectively extreme moves.
4. Post-event drift, gaps, breakouts and failed breakouts.
5. Crash/recovery and regime-conditioned asymmetry.
6. Implementable volatility/risk-premium proxies.
7. Simple entry information plus convex exits and risk sizing.
8. Pattern recognition and ML only for incremental OOS value over simpler baselines.

10R/15R/20R are outcome diagnostics, not optimization objectives.

## Required research gates
- Completed bars, next-tradable fills, no lookahead/label leakage; fail closed on stale or absent state.
- Chronological train/validation/final untouched test or walk-forward; purge boundary-overlapping trades.
- Realistic spread, commissions, financing, FX, slippage and instrument economics; stress costs.
- Parameter perturbation, bootstrap/seed robustness where relevant, overlap/dependence checks and multiple-testing awareness.
- Cross-market, side and regime attribution; explicitly flag results driven by a few instruments or extreme observations.
- Report sample size, expectancy in R, median, tail behavior, drawdown/exposure/turnover where applicable.
- Compare against passive champion and simple baselines. Never use final untouched test to tune the tested version.

## Promotion and execution
A challenger remains RESEARCH_ONLY until the gates above are passed. No autonomous broker execution. Any future executable proposal must pass the deterministic fail-closed Nordnet-KF execution/risk gate and explicit human approval.

## Capital
Research does not imply capital allocation. Opportunistic capital must be earned by validated evidence. Until then, passive investment remains champion and speculative research capital stays separate.
