"""Conservative independent-trade portfolio audit. Not a live execution engine."""
from collections import defaultdict
def audit(trades,initial=100000,risk_fraction=.01,max_positions=2,gross_cap=1.):
 """Trades: dict(entry_time,exit_time,symbol,entry,exit,stop,side,cost).
 Events ordered chronologically; exits processed before entries at equal timestamps.
 No simultaneous overlapping positions on the same symbol; no borrowing.
 """
 cash=initial;active={};closed=[];rejected=[];peak=initial;maxdd=0
 events=[]
 for k,t in enumerate(trades):
  if t['exit_time']<=t['entry_time']:raise ValueError('invalid chronology')
  if t['entry']<=0 or t['stop']<=0 or t['exit']<=0:raise ValueError('invalid price')
  events.extend([(t['entry_time'],1,k,t),(t['exit_time'],0,k,t)])
 for ts,kind,k,t in sorted(events,key=lambda x:(x[0],x[1],x[2])):
  if not kind:
   if k not in active:continue
   p=active.pop(k);direction=1 if t['side']=='LONG' else -1
   pnl=direction*(t['exit']-t['entry'])*p['qty']-t.get('cost',.002)*t['entry']*p['qty']
   cash+=pnl;closed.append(dict(symbol=t['symbol'],pnl=round(pnl,2),time=ts))
   peak=max(peak,cash);maxdd=max(maxdd,1-cash/peak)
   continue
  if len(active)>=max_positions or any(x['symbol']==t['symbol'] for x in active.values()):
   rejected.append(dict(symbol=t['symbol'],reason='CAPACITY_OR_DUPLICATE',time=ts));continue
  stopdistance=abs(t['entry']-t['stop'])
  if stopdistance<=0 or (t['side']=='LONG' and t['stop']>=t['entry']) or (t['side']=='SHORT' and t['stop']<=t['entry']):
   rejected.append(dict(symbol=t['symbol'],reason='INVALID_STOP',time=ts));continue
  exposure=sum(x['qty']*x['entry'] for x in active.values())
  room=max(0,cash*gross_cap-exposure)
  qty=min(cash*risk_fraction/stopdistance,room/t['entry'])
  if qty<=0:rejected.append(dict(symbol=t['symbol'],reason='NO_CAPITAL',time=ts));continue
  active[k]=dict(symbol=t['symbol'],qty=qty,entry=t['entry'])
 return dict(initial=initial,realized_equity=round(cash,2),closed=len(closed),
             rejected=rejected,max_realized_drawdown=round(maxdd,4),
             warning='Exploratory realized-only audit: no mark-to-market, margin, futures rolls, borrow or financing; do not treat as validated performance')
