# Warman Quant Research Mandate v4 — Stock Picker

Effective: 2026-09-30. Research only; no live broker orders.

## Objective and capital cadence
Stock Picker is the sole active research priority. The economic use case is a 70,000 SEK monthly contribution alongside the passive core (Investor/Berkshire). Cash arrival never forces a stock-pick trade: every challenger must beat the passive/core alternative on validated evidence.

## Champion and hypothesis
Passive long-term ownership remains champion. Build a systematic long-only stock-selection challenger from investable Nordnet equities using information available at each historical decision date.

Pre-registered families to test separately before combination:
1. Quality: profitability, margins/ROIC proxies, balance-sheet safety, earnings/cash-flow quality and stability.
2. Value: earnings/cash-flow/book/enterprise-value yields where economically meaningful.
3. Growth/GARP: durable sales/earnings growth conditioned on valuation and quality.
4. Momentum/relative strength: 12-1 and 6-1 style cross-sectional momentum, trend confirmation, excluding very recent reversal where appropriate.
5. Fundamental improvement: Piotroski-style direction-of-change signals and earnings revisions when point-in-time data are reliable.
6. Composite quality-value-momentum/GARP only after component baselines are frozen and tested.

Historical inspirations (Buffett/Munger, Graham, Fisher, Lynch, Greenblatt and systematic factor literature) generate hypotheses; names/reputations are never evidence.

## Portfolio baseline v1
- Monthly decision frequency; next-tradable execution after information availability.
- Long-only underlying equities first. No leverage in baseline.
- Compare top 5, 10 and 20 as pre-registered breadth diagnostics; equal-weight baseline plus a capped score-weight variant.
- Maximum single-name weight 20%; sector concentration reported.
- 70,000 SEK/month cash-flow simulation reported separately from strategy-return simulation.
- Dividends, FX, commissions, spread/slippage and withholding/tax assumptions documented.
- Survivorship-bias-aware universe; delisted names included where data permit. Fail closed where historical membership or point-in-time fundamentals cannot be established.
- Sweden, US and Europe evaluated separately before pooled claims.

## Exit lab v1
Every entry philosophy is tested against buy-and-hold of the SAME selected stocks. Pre-register:
A. Fundamental/rank exit: sell when thesis variables deteriorate or rank falls below a fixed threshold.
B. Price-risk exit: completed-bar trend/ATR rule.
C. Combined fundamental + price-risk exit.
D. No tactical exit control.
No exit may be tuned on final test. Report opportunity cost from false exits and re-entry churn.

## P&L objective
Primary optimization target is long-run net portfolio wealth: CAGR, cumulative net P&L and active return after realistic trading/FX costs. Drawdown, volatility, turnover and concentration are hard diagnostics/constraints, not substitutes for return. A challenger must demonstrate that excess P&L is broad enough to survive leave-one-winner-out, sector, size-bucket and subperiod tests. No final-test tuning.

## Validation
Chronological train/validation/final untouched test or walk-forward; point-in-time fundamentals with publication lags; no revised-data leakage; purge boundary overlap where relevant. Report CAGR, total return, max drawdown, volatility, turnover, exposure, concentration, hit rate, median holding period, tax/cost drag and equal-weight passive/index/core controls. Include parameter perturbation, subperiod/regime, leave-one-sector/name-out and multiple-testing awareness.

## Products and execution
Underlying equity is default. Mini futures are a separate later implementation study only when a validated equity signal exists. A mini future must demonstrate better net capital/risk economics after financing, spread, FX, leverage and knock-out/path risk; otherwise use the share.

No autonomous broker execution. Any candidate remains RESEARCH_ONLY until a deterministic Nordnet-KF gate verifies a real tradable product, executable bid/ask, spread/slippage, financing, FX, KO distance where relevant, recomputed net expected payoff/risk and explicit human approval.

## Required live output
For a validated candidate Kvanta may produce a human decision ticket: security, score/rank, thesis variables, proposed SEK size from the 70,000 SEK monthly budget, entry condition/price evidence, exit/trim rules, invalidation, expected holding horizon, costs and gate status. It must never fabricate a candidate merely to deploy monthly cash.
