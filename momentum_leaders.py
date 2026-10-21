"""Warman Momentum Leaders v2: conservative diagnostic, NEVER a trade signal.

Strict gates: historical membership coverage, stale/delisted data, next-session
opening fills, FX conversion, dividend-adjusted prices, Investor benchmark.
Free Yahoo prices and community membership cannot establish validated PIT edge.
"""
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

BASE = "https://raw.githubusercontent.com/thuningxu/sp500nq100/main/"
FILES = {"sp500": "sp500_components_history.csv", "nasdaq100": "nasdaq100_components_history.csv"}
START = "2015-01-01"
END = "2026-10-01"  # exclusive; last fully completed month September 2026
MIN_COVERAGE = 0.98
MAX_CLOSE_AGE_DAYS = 5
MAX_OPEN_DELAY_DAYS = 7
COST_PER_SIDE = 0.0025  # 25 bps each side, includes indicative FX and dealing friction
BENCHMARK = "INVE-B.ST"
FX = "SEK=X"
REPORT = Path("reports/momentum_leaders_report.json")


def historical_membership():
    frames = {}
    for index, filename in FILES.items():
        response = requests.get(BASE + filename, timeout=45)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        if not {"date", "tickers"}.issubset(df.columns):
            raise ValueError("Constituent source schema changed for " + index)
        df["date"] = pd.to_datetime(df["date"], errors="raise").dt.tz_localize(None)
        frames[index] = df.sort_values("date")
    return frames


def members_on(frames, date):
    symbols = set()
    for df in frames.values():
        before = df[df["date"] <= date]
        if before.empty:
            raise ValueError("No historical membership snapshot by " + str(date))
        raw = str(before.iloc[-1]["tickers"])
        symbols.update(x.strip().replace(".", "-") for x in raw.split(",") if x.strip())
    return sorted(symbols)


def get_prices(symbols):
    result = {}
    for offset in range(0, len(symbols), 25):
        batch = symbols[offset:offset + 25]
        try:
            data = yf.download(batch, start=START, end=END, auto_adjust=True,
                               actions=False, progress=False, threads=True,
                               group_by="ticker", timeout=30)
            for symbol in batch:
                try:
                    frame = data[symbol] if isinstance(data.columns, pd.MultiIndex) else data
                    frame = frame[["Open", "Close"]].apply(pd.to_numeric, errors="coerce").dropna()
                    if frame.empty:
                        continue
                    idx = pd.to_datetime(frame.index)
                    if idx.tz is not None:
                        idx = idx.tz_localize(None)
                    frame.index = idx.normalize()
                    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
                    result[symbol] = frame
                except (KeyError, TypeError, ValueError):
                    continue
        except Exception as error:
            print("Batch download failed:", offset, str(error)[:200], flush=True)
        print("Downloaded", min(offset + 25, len(symbols)), "of", len(symbols),
              "symbols; nonempty:", len(result), flush=True)
    return result


def close_at(data, symbol, date):
    frame = data.get(symbol)
    if frame is None:
        return None
    before = frame.loc[frame.index <= date, "Close"].dropna()
    if before.empty:
        return None
    observed = before.index[-1]
    if (date - observed).days > MAX_CLOSE_AGE_DAYS:
        return None  # CRITICAL: never recycle stale/delisted prices
    price = float(before.iloc[-1])
    return price if np.isfinite(price) and price > 0 else None


def next_open(data, symbol, month_end):
    frame = data.get(symbol)
    if frame is None:
        return None
    candidates = frame.loc[(frame.index > month_end) &
                           (frame.index <= month_end + pd.Timedelta(days=MAX_OPEN_DELAY_DAYS)),
                           "Open"].dropna()
    if candidates.empty:
        return None
    price = float(candidates.iloc[0])
    return (candidates.index[0], price) if np.isfinite(price) and price > 0 else None


def fx_before(data, date):
    # Prior day's FX close, not same-day FX close that occurs after US market open.
    frame = data.get(FX)
    if frame is None:
        return None
    earlier = frame.loc[frame.index < date, "Close"].dropna()
    if earlier.empty or (date - earlier.index[-1]).days > MAX_CLOSE_AGE_DAYS:
        return None
    rate = float(earlier.iloc[-1])
    return rate if np.isfinite(rate) and rate > 0 else None


def metrics(months):
    if not months:
        return None
    returns = np.array([m["net_return_sek"] for m in months], dtype=float)
    if not np.all(np.isfinite(returns)) or np.any(returns <= -1):
        return None
    curve = np.cumprod(1 + returns)
    peaks = np.maximum.accumulate(np.r_[1., curve])[1:]
    return {
        "months": len(months),
        "cagr": float(curve[-1] ** (12 / len(months)) - 1),
        "max_drawdown": float(np.min(curve / peaks - 1)),
        "total_return": float(curve[-1] - 1),
        "mean_monthly_return": float(np.mean(returns))
    }


def self_test():
    dates = pd.to_datetime(["2020-01-30", "2020-02-03", "2020-02-28", "2020-03-02"])
    sample = {"X": pd.DataFrame({"Open": [10., 11., 12., 13.],
                                 "Close": [10., 11., 12., 13.]}, index=dates)}
    assert close_at(sample, "X", pd.Timestamp("2020-01-31")) == 10.
    assert close_at(sample, "X", pd.Timestamp("2020-02-10")) is None
    assert next_open(sample, "X", pd.Timestamp("2020-01-31")) == (pd.Timestamp("2020-02-03"), 11.)
    assert next_open(sample, "X", pd.Timestamp("2020-02-28")) == (pd.Timestamp("2020-03-02"), 13.)
    assert metrics([{"net_return_sek": 0.1}, {"net_return_sek": -0.05}])["months"] == 2
    print("Self-test passed")


def run():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    history = historical_membership()
    month_ends = pd.date_range("2017-01-31", "2026-09-30", freq="ME")
    universes = {str(d.date()): members_on(history, d) for d in month_ends}
    all_symbols = sorted(set().union(*(set(v) for v in universes.values())) |
                         {BENCHMARK, FX})
    data = get_prices(all_symbols)
    coverage_audit = []
    for d in month_ends:
        pool = universes[str(d.date())]
        present = [s for s in pool if close_at(data, s, d) is not None]
        missing = sorted(set(pool) - set(present))
        coverage_audit.append({
            "month": str(d.date()), "membership_count": len(pool),
            "rankable_current_close": len(present),
            "coverage_ratio": round(len(present) / len(pool), 5) if pool else 0,
            "missing_count": len(missing), "missing_examples": missing[:20]
        })

    results = {}
    for lookback in (1, 3, 6, 12):
        for top_n in (5, 10):
            monthly = []
            for j in range(lookback, len(month_ends) - 1):
                d0, d1, dp = month_ends[j], month_ends[j + 1], month_ends[j - lookback]
                audit = coverage_audit[j]
                record = {"signal_month": str(d0.date()), "exit_month": str(d1.date()),
                          "universe_size": audit["membership_count"],
                          "rankable_count": audit["rankable_current_close"],
                          "coverage_ratio": audit["coverage_ratio"]}
                if audit["coverage_ratio"] < MIN_COVERAGE:
                    record["status"] = "FAIL_INSUFFICIENT_UNIVERSE_COVERAGE"
                    monthly.append(record)
                    continue
                ranks = []
                for s in universes[str(d0.date())]:
                    old, recent = close_at(data, s, dp), close_at(data, s, d0)
                    if old is not None and recent is not None:
                        ranks.append((recent / old - 1, s))
                record["rankable_momentum_count"] = len(ranks)
                if len(ranks) < top_n or len(ranks) / max(len(universes[str(d0.date())]), 1) < MIN_COVERAGE:
                    record["status"] = "FAIL_INSUFFICIENT_LOOKBACK_COVERAGE"
                    monthly.append(record)
                    continue
                picks = [s for _, s in sorted(ranks, reverse=True)[:top_n]]
                record["holdings"] = picks
                entries = [next_open(data, s, d0) for s in picks]
                exits = [next_open(data, s, d1) for s in picks]
                if any(v is None for v in entries + exits):
                    record["status"] = "FAIL_MISSING_NEXT_OPEN_OR_DELISTED_EXIT"
                    monthly.append(record)
                    continue
                entry_dates = {v[0] for v in entries}
                exit_dates = {v[0] for v in exits}
                if len(entry_dates) != 1 or len(exit_dates) != 1:
                    record["status"] = "FAIL_MISMATCHED_EXECUTION_DATES"
                    monthly.append(record)
                    continue
                fx_entry = fx_before(data, entries[0][0])
                fx_exit = fx_before(data, exits[0][0])
                b0 = next_open(data, BENCHMARK, d0)
                b1 = next_open(data, BENCHMARK, d1)
                if fx_entry is None or fx_exit is None or b0 is None or b1 is None:
                    record["status"] = "FAIL_MISSING_FX_OR_INVESTOR_BENCHMARK"
                    monthly.append(record)
                    continue
                gross = float(np.mean([exits[k][1] / entries[k][1] * fx_exit / fx_entry - 1
                                       for k in range(top_n)]))
                # Conservative: full liquidation and repurchase each month.
                net = (1 + gross) * (1 - COST_PER_SIDE) ** 2 - 1
                bench = b1[1] / b0[1] - 1  # SEK, dividend-adjusted Investor OHLC
                record.update(status="DIAGNOSTIC_ONLY", entry_date=str(entries[0][0].date()),
                              exit_date=str(exits[0][0].date()),
                              net_return_sek=net, gross_return_sek=gross,
                              investor_return_sek=bench, fx_entry=fx_entry, fx_exit=fx_exit)
                monthly.append(record)

            valid = [x for x in monthly if x["status"] == "DIAGNOSTIC_ONLY"]
            complete = len(valid) == len(monthly) and bool(monthly)
            # Never annualize a gappy history: skipped periods inflate CAGR.
            all_metrics = metrics(valid) if complete else None
            holdout = [x for x in valid if x["signal_month"] >= "2023-01-01"]
            holdout_complete = complete or (len(holdout) == len(
                [x for x in monthly if x["signal_month"] >= "2023-01-01"]))
            results[f"{lookback}m_top{top_n}"] = {
                "total_months": len(monthly), "valid_months": len(valid),
                "failed_months": len(monthly) - len(valid),
                "failed_status_counts": {k: sum(x["status"] == k for x in monthly)
                                          for k in sorted(set(x["status"] for x in monthly))
                                          if k != "DIAGNOSTIC_ONLY"},
                "full_sample_diagnostic": all_metrics,
                "holdout_2023plus_diagnostic": metrics(holdout) if holdout_complete else None,
                "investor_same_months_diagnostic": (
                    metrics([{"net_return_sek": x["investor_return_sek"]} for x in valid])
                    if complete else None),
                "monthly": monthly
            }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "research_only": True, "validated_edge": False, "trading_authorized": False,
        "prior_report_36pct_cagr_status": "INVALIDATED_UNVERIFIED",
        "coverage_threshold": MIN_COVERAGE,
        "membership_source": BASE,
        "markets_tested": ["S&P500", "Nasdaq100"],
        "markets_missing": ["OMXS30 historical point-in-time constituents"],
        "price_source": "Yahoo Finance auto-adjusted OHLC (unverified delisted coverage)",
        "currency": "SEK; USD assets converted using prior FX close as executable-price proxy",
        "execution": "Rank at calendar month-end using last close max 5 days old; enter at next exchange open; exit at next month next open",
        "costs": {"per_side": COST_PER_SIDE,
                  "round_trip_approx": 2 * COST_PER_SIDE,
                  "method": "Full liquidation/reinvestment assumed monthly, even when holdings unchanged"},
        "sample": {"start": str(month_ends[0].date()), "last_exit_month": str(month_ends[-1].date())},
        "coverage_audit": coverage_audit,
        "critical_limitations": [
            "Not verified: missing delisted price histories may bias even fully covered months",
            "Historical index membership is community-maintained and not independently audited",
            "OMXS30 point-in-time history missing; three-market strategy not tested",
            "Adjusted opening prices approximate total return; corporate actions not independently checked",
            "FX uses prior daily close proxy, not actual executable USDSEK conversion",
            "Investor adjusted prices are a provisional dividend-reinvested benchmark",
            "Holding selection was explored on earlier data; 2023+ is not untouched OOS",
            "Selection from current data source may exclude renamed, merged, or delisted securities",
            "Costs are assumptions; Nordnet KF product spreads and financing not modelled"
        ],
        "results": results
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print("Coverage:", min(x["coverage_ratio"] for x in coverage_audit),
          "min; failing months:", sum(x["coverage_ratio"] < MIN_COVERAGE for x in coverage_audit))
    print("Validation: NOT APPROVED; results are research diagnostics only")


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
