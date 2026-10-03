# 1H price-action research, 2026-09-29

Research only. Daily/4H context, completed 1H signals, earliest next 1H open execution. Bitcoin and Nasdaq 100 only. No scalp or HFT requirement. No live orders.

First diagnostic on existing Warman-Quant-Data 10.zip: previous UTC-day high/low swept intrabar and signal candle closes back inside the level; next 1H open entry, stop at signal-bar extreme, exit at invalidation or after 12 hourly bars; conservative adverse gap; one position at a time; nominal 20bps roundtrip. Bitcoin 1433 1H bars, 61 events, mean -0.109% net/event, total -23.095 R. Nasdaq 100 417 1H bars, 26 events, mean -0.350% net/event, total -10.291 R. Prototype rejected, not an established edge. Both directions are research diagnostics, not executable product trades. UTC days are not Nasdaq exchange sessions. Underlying/proxy series do not capture SEK Nordnet minifuture quotes, spreads, funding, FX or knockout.

Research next: session-correct levels, independent predeclared sweep/reclaim, breakout/retest, failed auction; multi-year hourly source; realistic 1H intrabar stop ambiguity; actual instrument mapping; same-date SEK buy/hold comparator; untouched prospective evaluation. Existing 1H history spans only ~2–3 months and cannot validate profitability. No pilot or order alerts until gates pass.
