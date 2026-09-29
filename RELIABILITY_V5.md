# Reliability programme v5 (staged; research-only)

## Included in this increment
- Collector daily lookback extended from 2y to 10y. Yahoo may return less; manifest records actual bars.
- `journal.py`: explicit bootstrap, legacy migration, chained SHA-256 snapshot integrity, tamper detection and atomic individual file replacements. **Not wired to scheduled paperdesk yet**: migration and restore need separate acceptance tests before enabling.
- `portfolio_audit.py`: chronological exit-before-entry, simultaneous capacity, one position per symbol, 1% risk budget, 100% gross exposure ceiling, 20bps assumed costs. Prototype is realized-only; it cannot certify actual portfolio performance.
- Offline regression tests for integrity and capital constraints.

## Blocking next increments
1. Durable journal across workflow runs: independent persistent backing store, restore checksum and sequence verification, two-phase snapshot recovery, no silent genesis if expected snapshot missing. Cache is NOT durable.
2. Replay chronological events across ALL symbols (existing paperdesk iterates symbol-by-symbol). Ensure identical outcomes under shuffled symbol order, holidays, delayed quotes and reruns.
3. Mark-to-market equity, instrument-specific contract multiplier, currency conversion, borrow/margin, slippage, cash reservation, concurrent signal allocation and correlation clusters.
4. Historical point-in-time provenance, corporate actions and futures rolls; daily session calendars; multiple independent walk-forward windows and untouched future sample.
5. Costs 1x/2x/3x, block bootstrap, multiple testing, passive benchmark and independent reproduction.
6. Promotion remains forbidden; no broker credentials, orders, live sizing or automatic strategy promotion.
