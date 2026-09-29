"""Frozen exploratory VIRBTC trend regime, research only. No orders.

Signal: prior close > SMA of preceding N closes, executed next session open.
Do not select a winning N using the evaluation period as a holdout.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

HORIZONS = (40, 50, 60, 80, 100, 200)
COST_BPS = (20, 40, 60)


def run(path, start='2026-01-02', end='2026-09-28', capital=25000):
    raw = Path(path).read_bytes()
    bars = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    for bar in bars:
        for field in ('open', 'high', 'low', 'close', 'volume'):
            bar[field] = float(bar[field])
        if not all(math.isfinite(bar[field]) for field in ('open', 'high', 'low', 'close', 'volume')):
            raise ValueError('Non-finite bar')
        if not (0 < bar['low'] <= min(bar['open'], bar['close']) <= max(bar['open'], bar['close']) <= bar['high']):
            raise ValueError('Invalid OHLC')
    if any(bars[i-1]['date'] >= bars[i]['date'] for i in range(1, len(bars))):
        raise ValueError('Dates must be ascending and unique')
    period = [bar for bar in bars if start <= bar['date'] <= end]
    if not period:
        raise ValueError('No evaluation bars')

    def sim(n, roundtrip_bps):
        side = roundtrip_bps / 20000
        cash = float(capital)
        units = 0
        peak = capital
        dd = 0
        turns = 0
        curve = []
        for i, bar in enumerate(bars):
            if bar['date'] < start:
                continue
            if bar['date'] > end:
                break
            if i < n + 1:
                raise ValueError('Insufficient prior warmup')
            signal = bars[i-1]['close'] > sum(x['close'] for x in bars[i-n-1:i-1]) / n
            if units and not signal:
                cash += units * bar['open'] * (1-side)
                units = 0
                turns += 1
            elif not units and signal:
                buy = math.floor(cash / (bar['open'] * (1+side)))
                if buy:
                    cash -= buy * bar['open'] * (1+side)
                    units = buy
                    turns += 1
            equity = cash + units * bar['close']
            peak = max(peak, equity)
            dd = max(dd, 1-equity/peak)
            curve.append(dict(date=bar['date'], equity=round(equity, 2), units=units))
        return dict(final_equity=round(curve[-1]['equity'], 2), max_drawdown_pct=round(100*dd, 2), one_way_transactions=turns, open_units=units)

    side = COST_BPS[0]/20000
    hold_units = math.floor(capital / (period[0]['open']*(1+side)))
    hold_cash = capital-hold_units*period[0]['open']*(1+side)
    hold_net = hold_cash + hold_units*period[-1]['close']
    return dict(status='EXPLORATORY_RESEARCH_ONLY', orders_enabled=False,
        source_sha256=hashlib.sha256(raw).hexdigest(), start=start, end=end,
        sessions=len(period), initial=capital, buy_hold_net_mark_to_close=round(hold_net, 2),
        warnings=['2026 inspected before this code was frozen; not independent OOS',
                  'No independent source/spread/broker verification; no live eligibility',
                  'Research on VIRBTC only; cross-market test still required'],
        strategies={str(n):{str(bps)+'bps_roundtrip':sim(n,bps) for bps in COST_BPS} for n in HORIZONS})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv')
    parser.add_argument('--out', default='virbtc_regime_robustness.json')
    args = parser.parse_args()
    Path(args.out).write_text(json.dumps(run(args.csv), indent=2))
