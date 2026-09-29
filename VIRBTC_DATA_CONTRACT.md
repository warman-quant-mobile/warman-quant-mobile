# VIRBTC data acquisition contract

The repository must never label BTC-USD spot candles as historical VIRBTC fills. Obtain genuine traded-product SEK daily OHLCV CSV from a documented issuer, exchange or licensed vendor. Required headers: date,open,high,low,close,volume; ascending YYYY-MM-DD dates, no synthetic weekend rows. Record original URL/export date, data vendor, quote convention, adjusted/unadjusted status and known splits/distributions separately. Verify raw file against independent product reference before promotion.

Command after genuine CSV is acquired:
python virbtc_import.py path/to/virbtc.csv --out output/virbtc --isin SE0020845709 --source "Actual vendor and export reference"

Importer records raw SHA-256 and rejects prelisting dates, duplicates, malformed bars, weekend sessions, wrong ISIN, non-SEK, and declared spot proxies. Its caller-provided source string is NOT proof of authenticity. Missing exchange sessions, holidays, corporate actions, venue spreads, turnover, TER embedded in NAV, broker commission and actual fill assumptions still need verification. Imported data does not change promotion_gate.py or enable orders.

The CSV has not yet been obtained or independently verified. Do not create fictional sample prices in production output.
