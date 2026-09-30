#!/usr/bin/env python3
"""Fail-closed Nordnet-KF promotion policy.

Research sensors may trigger a thesis, but only mapped underlyings can proceed to
instrument verification. This module never claims that a specific ETP is live,
liquid or executable; those facts require a current Nordnet product/quote check.
"""
SENSORS = {
    "VIX": "VOLATILITY_SENSOR_ONLY",
    "OVX": "VOLATILITY_SENSOR_ONLY",
    "GVZ": "VOLATILITY_SENSOR_ONLY",
    "US30Y_YIELD": "RATE_SENSOR_ONLY",
    "US10Y_YIELD": "RATE_SENSOR_ONLY",
}
# Underlyings for which the strategy may search for a Nordnet-KF product.
# This is deliberately an allow-list, not an assertion that a product is currently available.
UNDERLYING_ALLOWLIST = {
    "SP500": {"product_search": "S&P 500", "preferred_types": ["MINI_FUTURE", "TURBO"]},
    "WTI_FUT": {"product_search": "WTI oil", "preferred_types": ["MINI_FUTURE", "TURBO"]},
    "BRENT_FUT": {"product_search": "Brent oil", "preferred_types": ["MINI_FUTURE", "TURBO"]},
    "GOLD_FUT": {"product_search": "Gold", "preferred_types": ["MINI_FUTURE", "TURBO"]},
    "SILVER_FUT": {"product_search": "Silver", "preferred_types": ["MINI_FUTURE", "TURBO"]},
    "US30Y_BOND_FUT": {"product_search": "US Treasury bond", "preferred_types": ["MINI_FUTURE", "TURBO"]},
    "INVESTOR_B": {"product_search": "Investor B", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "VOLVO_B": {"product_search": "Volvo B", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "ATLAS_A": {"product_search": "Atlas Copco A", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "ABB": {"product_search": "ABB", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "NVIDIA": {"product_search": "NVIDIA", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "MICROSOFT": {"product_search": "Microsoft", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "APPLE": {"product_search": "Apple", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "TESLA": {"product_search": "Tesla", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "AMAZON": {"product_search": "Amazon", "preferred_types": ["SHARE", "MINI_FUTURE"]},
    "META": {"product_search": "Meta", "preferred_types": ["SHARE", "MINI_FUTURE"]},
}

def promotion_gate(symbol):
    if symbol in SENSORS:
        return {"eligible": False, "status": SENSORS[symbol], "reason": "research sensor is not a trade instrument"}
    mapping = UNDERLYING_ALLOWLIST.get(symbol)
    if mapping is None:
        return {"eligible": False, "status": "NO_NORDNET_KF_MAPPING", "reason": "underlying not on explicit Nordnet-KF search allow-list"}
    return {"eligible": True, "status": "NORDNET_PRODUCT_AND_QUOTE_REQUIRED", **mapping}

def execution_requirements():
    return [
        "specific Nordnet instrument verified available in KF",
        "ISIN and product type verified",
        "live executable bid/ask verified",
        "spread and slippage included",
        "financing and FX included where applicable",
        "knockout/stop-loss distance compatible with strategy stop",
        "R recomputed from executable product economics and remains >=10",
        "position size and gap risk checked",
    ]
