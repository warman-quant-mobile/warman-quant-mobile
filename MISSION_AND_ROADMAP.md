# Warman Quant — mission and execution priorities (v11)

## Primary objective
Research, identify, validate and—only after explicit human approval—manually exploit executable, high-asymmetry trading opportunities to pursue exceptional long-term capital growth. The objective is not to maximize backtest scores, build a generic dashboard, or replace the user's long-only core portfolio. No strategy is assumed profitable.

## Non-negotiable constraints
- Real products tradable in Warman Finans AB's corporate Nordnet KF; observed order form does not establish final order acceptance.
- Research across the existing 23-symbol universe continues; BTC/VIRBTC is first *instrument validation pilot*, not exclusive strategy focus.
- 506 exploratory hypotheses are correlated tests, not 506 independent opportunities. Freeze candidate rules before prospective evaluation.
- Live experiment proposal: 25,000 SEK separately allocated, planned 0.5% risk/trade, max 50% exposure, 5% pilot drawdown halt, no leverage; gap losses can exceed planned risk. Human-only order entry, explicit funding and launch approval.
- No use of VAT, operating reserves, borrowed funds or long-only core collateral. No broker automation.
- Failed/missing evidence => RESEARCH_ONLY_BLOCKED; a green workflow is not trade authorization.

## Priority order
P0: authentic VIRBTC product OHLC, documented provenance, SEK costs, exchange calendar and corporate-KF quote checks.
P0: correct chronology in event-driven simulator. Scheduled open exits precede entries; proceeds from intraday stops cannot finance orders at that day's open. Explicit gap behavior and tests.
P1: immutable, replayable, durable shadow ledger with no silent bootstrap.
P1: pre-register high-asymmetry hypotheses with economic mechanism, cost assumptions, robustness and independent untouched observations; preserve broad research.
P2: compare realistic net opportunity and capital efficiency against passive and cash benchmarks, including liquidity and tail risk.
P2: update obsolete README and publish machine-readable blockers/next required user action.

## Status on 2026-09-29
PR #10 merged. 17 tests passed, 23/23 instruments validated, 506 hypotheses explored (161 adequate sample in latest run); historical Yahoo spot-proxy portfolio result 853190.10 is DIAGNOSTIC ONLY and has possible event-ordering bias. Paper journal QUARANTINED. BTC/ETH/SOL promotion gate RESEARCH_ONLY_BLOCKED. No live orders.
