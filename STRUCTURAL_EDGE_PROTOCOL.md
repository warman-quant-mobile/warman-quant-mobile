# Warman Quant: Structural Edge Protocol — 2026-09-29

STATUS: RESEARCH_ONLY_BLOCKED. No trade authorization, no automatic orders, no funding instructions.

## Economic objective
Build net capital for Warman Finans, not maximize backtest count. Compare every active strategy against an investable long-only baseline with matching SEK dates and costs, including the cost of idle cash and researcher time. Do not borrow operating cash or VAT reserves.

## Primary candidate: post-earnings announcement drift (PEAD)
Mechanism: slow incorporation of genuinely unexpected public accounting information, conditional on liquidity and attention. Not equivalent to trading an arbitrary large daily price move. Require timestamped publication, pre-event consensus estimates and actual results, corporate-action-adjusted executable quotes, bid-ask spread and turnover. Record survivorship including delisted securities and failed signals. Universe: predeclared liquid Nordnet-tradable equities. Event eligibility based solely on information available before entry. Signal defined before inspecting evaluation returns. Entries cannot precede public release or feasible order time. No trading on leaked/private information. Compare post-event drift to industry/market beta and passive portfolio. Simulate 1x/2x/3x execution costs and adverse gap fills. Record overlapping events, concentration, drawdown, max loss, largest winner contribution and net capacity.

## Secondary candidate: mechanical institutional flows
Mechanism: index additions/deletions or publicly scheduled rebalancing where passive flows may distort price. Require timestamped announcement and effective date, index weights, free float, market capitalization, volume, index tracking AUM and realistic participation rate. Avoid hindsight membership and claims of guaranteed front-running profits. Test both pre-effective pressure and post-effective reversal. Reject if spread/impact eliminates benefit.

## Third candidate: volatility-risk dislocations
Require historical bid/ask option chains, expiries, underlying quotes, dividends, borrow and exercise/assignment handling; quantify tail risk. No naked short options or leveraged deployment without separate risk approval.

## Decision framework
A) Data provenance and event timestamps verified.
B) Economic mechanism survives non-event controls and costs.
C) Predeclared holdout / prospective sample; no parameter tuning on holdout.
D) Net portfolio beats a feasible passive alternative by an economically meaningful margin, with comparable drawdown and operational workload.
E) Trade-level distribution and realistic capacity documented; model uncertainty included.
F) Immutable ledger and executable Nordnet product mapping verified.
G) User explicitly approves any separate, bounded pilot and each manual order.

If source event/consensus/flow/options data is missing: mark DATA_BLOCKED. Do not substitute OHLC-derived proxies and claim a causal edge. The 22-series historical scan and VIRBTC 2026 are previously inspected and cannot be called untouched validation.

Research reference examples (not proof of current profits):
- Review of PEAD: https://doi.org/10.1016/j.jbef.2020.100446
- Trading-friction caveat: https://doi.org/10.2469/faj.v65.n4.3
- Institutional rebalancing, NBER working paper 33554: https://www.nber.org/papers/w33554
- MSCI reconstitution: https://doi.org/10.1016/j.pacfin.2025.102900
