# Warman Quant research mandate v2

Research-only; no live broker orders. The existing 20-bar paper strategy is a control, not an established edge.

## Hypotheses

Evaluate momentum (12/20/36-bar), breakout (12/20/36-bar), short-horizon mean reversion (12/20/36-bar), volatility compression/expansion, relative value only when economically justified, and market-regime filters. Freeze rules before inspecting out-of-sample outcomes. Never choose a winner using holdout data.

## Required gates

- Timestamp integrity: completed bars, next-bar fills, no lookahead; fail closed on stale or absent state.
- Costs: spread, commissions, financing, short borrow, slippage and instrument-specific contract economics; stress at 2x and 3x baseline costs.
- Chronological train/validation/test, purging boundary-overlapping trades, walk-forward, bootstrap uncertainty and multiple-testing adjustment.
- Report sample size, expectancy in R, payoff ratio, drawdown, exposure, turnover, net compounded return and sensitivity to parameter perturbations.
- Compare a passive investment-company benchmark, cash flows and portfolio-level correlation. Research profiles at 2/3/5% risk are stress scenarios only; no automatic authority to trade live.
- No promotion from paper to live without explicit human approval, independently checked results, executable quotes and operational recovery drills.

## Operational priorities

Durable append-only journal with recovery checks; chronological cross-symbol processing; stale-market handling; instrument-specific calendars; portfolio cash/margin accounting; automated daily exception-only reporting. Preserve old research and never silently reset journal.

A 50-100% annualized trading return is an aspirational research question, not a forecast, baseline, promise or acceptance threshold. Family wealth and speculative research capital must remain separate.
