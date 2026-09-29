"""Chronological one-session cash/position transitions, research only.

Opening scheduled exits execute before new opening entries. Intraday stop proceeds
are never available to finance opening entries. Conservative gap stop fills.
This is an isolated audited primitive, NOT yet a replacement for portfolio_v6.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Position:
    units: int
    stop: float

def session(cash, position, *, opening, low, scheduled_exit=False,
            entry_units=0, entry_stop=None, fee_rate=0.001):
    vals=[cash,opening,low,fee_rate]
    if not all(math.isfinite(x) for x in vals) or cash<0 or opening<=0 or low<=0 or low>opening or not 0<=fee_rate<1:
        raise ValueError('Invalid bar or account')
    if position is not None and (position.units<=0 or position.stop<=0):
        raise ValueError('Invalid position')
    events=[]
    # Opening phase: exit due at open, then optional new entry using only cash available at open.
    if position is not None and (scheduled_exit or opening<=position.stop):
        reason='scheduled_open' if scheduled_exit else 'stop_gap_open'
        proceeds=position.units*opening*(1-fee_rate)
        cash+=proceeds
        events.append(dict(phase='open',action='exit',reason=reason,price=opening,units=position.units))
        position=None
    if entry_units:
        if position is not None or entry_units<0 or not isinstance(entry_units,int) or entry_stop is None or not 0<entry_stop<opening:
            raise ValueError('Invalid opening entry')
        cost=entry_units*opening*(1+fee_rate)
        if cost>cash+1e-9:
            raise ValueError('Insufficient opening cash; no intraday proceeds may fund this entry')
        cash-=cost
        position=Position(entry_units,entry_stop)
        events.append(dict(phase='open',action='entry',price=opening,units=entry_units))
    # Intraday phase: stop cannot be known or credited at the opening.
    if position is not None and low<=position.stop:
        cash+=position.units*position.stop*(1-fee_rate)
        events.append(dict(phase='intraday',action='exit',reason='stop_touch_assumed',price=position.stop,units=position.units))
        position=None
    return dict(cash=round(cash,8),position=position,events=events,
      warning='Daily OHLC cannot establish intraday sequencing or guarantee stop fills.')
