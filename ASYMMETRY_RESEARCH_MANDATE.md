# High-asymmetry research mandate

Objective: search for exceptional *realized net* compounding through a small number of outsized winners, without promising an outcome.

- Never impose an arbitrary 2R take-profit or fixed profit ceiling on a trend strategy. Exit rules must be independently justified and frozen before prospective observations.
- Report distribution of realized R, including maximum winner, median, top-decile contribution, fraction of P&L from top five winners, longest loss streak, gap loss, tail drawdown, turnover and capital efficiency. Do not optimize a single headline Sharpe or terminal equity.
- Study trend persistence, breakout and regime effects, asymmetric convex payoffs, and independently justified structural mechanisms. Compare after realistic product costs and against investable alternatives.
- Explore the full 23-instrument universe, but do not mistake correlated parameter combinations for independent discoveries.
- BTC/VIRBTC is an instrument-validation pilot, not the exclusive or necessarily highest-return strategy.
- 25,000 SEK manual pilot requires separate capital authorization and all preflight controls. No order routing, no claims of verified edge.

## v13 diagnostic repair
The previous portfolio_v6 settled intraday stops before placing opening entries, potentially financing purchases with cash unavailable at that time. Opening exits now precede entries; intraday stops and close-derived next-open exits are evaluated afterwards. Historical Yahoo spot remains a proxy, not executable ETP performance. Daily OHLC cannot resolve all intraday sequences.
