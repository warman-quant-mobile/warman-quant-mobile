# VIRBTC source audit — 2026-09-29

Verified instrument: Virtune Bitcoin ETP, Nasdaq Stockholm, VIRBTC, ISIN SE0020845709, SEK, first trade 2023-09-12. Issuer fee 1.49% p.a. (already reflected in traded ETP market prices; do not charge again as a transaction fee).

Independent public product references:
- https://www.nordnet.se/etp/certifikat/trackers/lista/virtune-bitcoin-virbtc-xsto
- https://www.virtune.com/en/product/bitcoin
- https://www.nasdaq.com/sv/european-market-activity/etn-etc/virbtc?id=TX4995846

Potential traded-product daily OHLCV source:
- https://se.investing.com/etfs/virbtc-historical-data — publicly displays SEK daily close, open, high, low and volume for selected range. A visible page is NOT yet a verified complete export or a licence to redistribute.
- Nasdaq indicative close history is not interchangeable with exchange trade OHLC.
- Virtune NAV/returns are not exchange traded OHLC and cannot substitute for bid/ask fills.
- Nordnet page has latest trades, not a verified complete historical export.

Acquisition requirements:
1. Obtain licensed/exportable actual Nasdaq Stockholm VIRBTC OHLCV from first trade to latest *completed* session, with timestamp/date convention and original raw file.
2. Record provider, extraction time, corporate-action adjustment, provenance checksum and terms of use. Cross-check selected dates with a second independent product source.
3. Pass virbtc_import.py with attested ISIN and source. Investigate missing sessions; never interpolate with BTC spot or weekend prices.
4. Add observed historical spread/turnover, Nordnet commission and session calendar before claiming executable historical performance.
5. Do not change promotion_gate.py to green based on this document. Data remains NOT ACQUIRED / NOT VERIFIED.

User action ONLY if acquisition cannot be done programmatically: request a genuine historical VIRBTC CSV export from a provider available to the user. Never ask for credentials or require a real trade.
