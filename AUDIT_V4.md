# Research audit v4 — 2026-09-29

The objective is asymmetric **net** payoff under independently tested evidence, not a large indicator search or an annual return promise.

## Findings requiring controls
1. The v3 `rsi2_macd` condition was unreachable because `startswith('rsi')` intercepted it. Corrected; prior reported results for that family are invalid and must be superseded.
2. A 70/30 holdout repeatedly inspected across 418 hypotheses is no longer pristine. Treat prior holdout as exploratory; reserve a genuinely unseen forward period. Correlated signals mean counts of positive results are not independent discoveries.
3. A candidate's compounded per-trade returns are NOT a portfolio return: independent candidates ignore overlapping exposures, available cash, borrowing and contract economics.
4. The collector uses Yahoo prices, not executable quotes. Short positions and futures proxies require borrow, financing, rolls and actual contract specifications.
5. The paper journal currently uses Actions cache with expiration/reset risk. Do not regard it as durable until independent recovery and fail-closed continuity are tested.
6. Classic Turtle requires full unit additions/pyramiding and correlated-market risk caps. Current Turtle is a simplified channel model, not a replication.
7. A high R multiple does not justify increasing size without a verified distribution, tail-loss stress, liquidity and portfolio risk budget.

## New exploratory asymmetry models
- Compression-to-expansion: compressed short-term range, followed by 20-bar breakout.
- Failed breakout: intrabar breach of prior range followed by close back inside.
- Trend pullback: 200-bar regime with short-term reversal confirmation.
- ATR initial stop, uncapped 3-ATR trailing exit, maximum 60 bars; stop evaluated before any trailing update; next-open entry, gap-aware stops.
- Holdout tail-win and payoff diagnostics; separate 3x round-trip costs plus 10bps slippage per side.
- No automatic position-size increase. No live orders.

## Next engineering gates
Historical point-in-time data and session calendars; locked walk-forward and untouched forward test; White reality-check or block bootstrap with multiple-testing adjustment; parameter neighborhood and 2x/3x cost stress for ALL families; exposure-aware portfolio engine; durable journal with continuity fail-close; strategy-specific exit economics; passive long-only benchmark. Do not promote candidates on this exploratory holdout.
