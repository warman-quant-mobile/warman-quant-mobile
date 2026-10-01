# Winner Funnel v1 — frozen historical validation protocol

Status: PRE-REGISTERED BEFORE HISTORICAL FUNDAMENTAL TEST

## Frozen signal
No tuning after observing validation results.
- Quality 30%
- Value 15%
- Growth 30%
- Momentum 25%
- Breadth bonus: 20% of final score, where breadth is count of factor families >= 70th percentile / 4
- Minimum each family: 30th percentile
- Quality >= 55th percentile
- Growth >= 55th percentile
- Momentum >= 55th percentile
- Minimum market cap: USD 2bn for US; SEK 2bn for Sweden
- All four factor families required.

## Point-in-time rule
A fundamental fact may only be used on or after its public filing/publication date. No fiscal-period-end lookahead.
Prices used for ranking must be known at rebalance close. Portfolio enters next tradable session.

## Test design
- Primary validation: quarterly rebalancing, top 20 equal weight.
- Secondary diagnostics (not optimization): top decile and top 10 equal weight.
- Momentum: information ending at rebalance date; no future prices.
- Transaction cost stress: 20 bps and 50 bps per one-way turnover.
- FX: foreign-stock returns evaluated in SEK where FX history is available; otherwise report local-currency diagnostic separately and do not label it final net wealth.
- Benchmarks: broad market and equal-weight eligible universe.

## Required outputs
- CAGR and cumulative return net of costs
- active CAGR / cumulative active return
- max drawdown
- turnover
- 1y/3y forward winner capture: 2x, 3x, 5x
- factor-family ablations
- sector and size contribution
- remove top 1 / top 5 winners stress
- subperiod stability

## Bias controls
Current-survivor-universe tests are DIAGNOSTIC ONLY. They cannot validate the strategy.
Final evidence requires a historical investable universe including delisted/failed names where data permits.
Swedish current Yahoo fundamentals are not historical PIT and cannot be used as final historical evidence.

## Kill rule
Reject Winner Funnel as an active-stock-selection strategy if robust positive active net CAGR does not persist across multiple subperiods/universes/cost assumptions, or if apparent alpha depends materially on a few extreme winners, sectors, or survivorship bias.
