# Live-pilot acceptance contract — no automatic orders

## Earliest candidate
BTC via Virtune Bitcoin ETP, Nasdaq Stockholm, ticker VIRBTC, ISIN SE0020845709, first trade 2023-09-12, SEK, annual product fee 1.49% per Nordnet product page. ETH candidate Virtune Staked Ethereum ETP, VIRSETHS, ISIN SE0020541639, first trade 2023-08-09, annual fee 1.4%. Listing does NOT confirm company-owned KF order eligibility. SOL remains unidentified pending verified ISIN and exact listing. Product candidates may change based on liquidity, issuer risk and cost.

## Mandatory evidence before even a small live pilot
1. Verify actual Nordnet order ticket for Warman Finans AB company-owned KF and pass applicable knowledge test; human-only.
2. Obtain actual product-level daily OHLC, first trade date, adjusted distributions/splits, bid-ask and turnover, SEK fees and trading calendar. Backtest no earlier than instrument inception. No weekend spot fills.
3. Independent event-driven backtest and ledger replay with same-bar stop-first, gaps, cash conservation, fee timing, missing data failure, timestamp and order-size tests. Benchmark to buy-and-hold identical product and cash; report drawdown and worst-month.
4. Reserve truly untouched prospective observations, with frozen strategy/version/data manifest. Report 1x, 2x and 3x execution-cost sensitivity and robustness; if no positive net evidence, do not trade.
5. Durable checkpoint plus reproducible rebuild from immutable events, recovery tests and no silent reset.
6. Written capital segregation: no operating cash, VAT, borrowed funds or long-only core collateral; pre-set loss and shutdown limits. Pilot sizing needs explicit user decision and independent review of costs/liquidity.
7. No live order routing in this repo. Gate status REVIEW_ELIGIBLE_NOT_TRADE_AUTHORIZED is only a request for human review.

## Timing
Engineering milestones depend on data availability and tests. A 30–60 exchange-session untouched forward observation window starts ONLY after instrument-level implementation and frozen model, not from historical proxy results. No promised trading date.
