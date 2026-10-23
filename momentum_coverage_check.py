"""Fail-closed audit of Momentum Leaders research output.

This checks the *reported* diagnostics; it does not verify external price
histories, historical index membership, dividends, or execution prices.
Exit 0 only for a fully approved report. Never authorizes live trading.
"""
import json
import sys
from pathlib import Path

REPORT = Path("reports/momentum_leaders_report.json")
MIN_CONSECUTIVE_MONTHS = 60
REQUIRED_MARKETS = {"S&P500", "Nasdaq100", "OMXS30"}


def longest_valid_streak(months):
    """Longest sequence of adjacent *reported* monthly observations."""
    longest = current = 0
    for row in months:
        if row.get("status") == "DIAGNOSTIC_ONLY":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def audit(report):
    issues = []
    results = report.get("results") or {}
    if report.get("prior_report_36pct_cagr_status") != "INVALIDATED_UNVERIFIED":
        issues.append("Legacy 36% CAGR has not been explicitly invalidated.")
    if not REQUIRED_MARKETS.issubset(set(report.get("markets_tested") or [])):
        issues.append("Incomplete three-market point-in-time universe, including OMXS30.")
    if report.get("markets_missing"):
        issues.append("Missing markets: " + ", ".join(report["markets_missing"]))
    if report.get("price_source", "").lower().find("unverified") >= 0:
        issues.append("Historical/delisted price coverage is not independently verified.")
    if report.get("membership_source", "").find("thuningxu") >= 0:
        issues.append("Community-maintained membership has not been independently audited.")
    if not report.get("independent_point_in_time_price_audit", False):
        issues.append("No independent point-in-time and delisting price audit.")
    if not report.get("untouched_out_of_sample_validation", False):
        issues.append("No genuinely untouched out-of-sample validation.")
    if not report.get("benchmark_dividends_independently_verified", False):
        issues.append("Investor total-return benchmark is provisional.")
    if not report.get("costs_independently_verified", False):
        issues.append("Execution/FX costs remain assumptions.")
    if report.get("trading_authorized"):
        issues.append("Unexpected trading_authorized=true: manual approval is always required.")

    summary = {}
    for key, entry in sorted(results.items()):
        months = entry.get("monthly") or []
        valid = sum(row.get("status") == "DIAGNOSTIC_ONLY" for row in months)
        total = len(months)
        streak = longest_valid_streak(months)
        summary[key] = {
            "total_months": total,
            "valid_months": valid,
            "failed_months": total - valid,
            "longest_reported_valid_streak": streak,
            "full_sample_metrics_available": entry.get("full_sample_diagnostic") is not None,
            "holdout_metrics_available": entry.get("holdout_2023plus_diagnostic") is not None,
        }
        if total != entry.get("total_months") or valid != entry.get("valid_months"):
            issues.append(key + ": monthly row counts disagree with report summary.")
        if streak < MIN_CONSECUTIVE_MONTHS:
            issues.append(key + ": fewer than 60 consecutive usable months (" + str(streak) + ").")
        if total != valid and entry.get("full_sample_diagnostic") is not None:
            issues.append(key + ": annualized metrics present despite gaps.")
    if not summary:
        issues.append("No strategy results present.")
    # A report may be statistically complete yet still fail due to PIT source risk.
    approved = len(issues) == 0 and report.get("validated_edge") is True
    if report.get("validated_edge") is True and issues:
        issues.append("Report claims validated_edge despite blocking audit failures.")
    return {
        "generated_at": report.get("generated_at"),
        "approved_for_research_claim": approved,
        "trading_authorized": False,
        "issues": issues,
        "strategies": summary,
    }


def main():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    output = audit(report)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["approved_for_research_claim"] else 2


if __name__ == "__main__":
    sys.exit(main())
