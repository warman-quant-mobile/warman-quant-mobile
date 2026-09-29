"""Product-specific, cash-backed VIRBTC daily research; no order instructions.

Actual imported product CSV only; next-open fills, scheduled exit before entries,
opening gaps, intraday stop AFTER opening orders, all costs explicit. No 2R target.
"""
import argparse,csv,json,math
from pathlib import Path
from execution_chronology import Position,session
ISIN='SE0020845709'
def run(folder,initial=25000,risk=.005,max_exposure=.5,fee_bps=20,lookback=20,exit_lookback=10,atr_mult=2):
 p=Path(folder);m=json.loads((p/'virbtc_manifest.json').read_text())
 if m.get('isin')!=ISIN or m.get('currency')!='SEK' or m.get('status')!='IMPORTED_NOT_INDEPENDENTLY_VERIFIED':raise ValueError('Actual product import manifest required')
 rows=list(csv.DictReader((p/'virbtc_daily.csv').open()))
 if len(rows)<lookback+22:raise ValueError('Insufficient genuine product bars')
 bars=[dict(date=x['date'],**{k:float(x[k]) for k in ('open','high','low','close','volume')}) for x in rows]
 cash=initial;position=None;due=False;entry_cost=0;entry_price=0;entry_date=None;history=[];trades=[];peak=initial
 fee=fee_bps/20000 # per side, bps round-trip
 for i,b in enumerate(bars):
  o,l,c=b['open'],b['low'],b['close'];events=[]
  # Exits at open settle before any new entry.
  if position and (due or o<=position.stop):
   r=session(cash,position,opening=o,low=o,scheduled_exit=due,fee_rate=fee)
   cash,position=r['cash'],r['position'];events+=r['events']
   proceeds=events[-1]['units']*o*(1-fee)
   trades.append(dict(entry_date=entry_date,exit_date=b['date'],entry=entry_price,exit=o,qty=events[-1]['units'],pnl=round(proceeds-entry_cost,2),reason=events[-1]['reason']))
   due=False
  if position is None and i>=lookback+21:
   prev=bars[i-1];prior=bars[i-lookback-1:i-1]
   if prev['close']>max(x['high'] for x in prior):
    tr=[]
    for j in range(i-20,i):
     x=bars[j];last=bars[j-1]['close']
     tr.append(max(x['high']-x['low'],abs(x['high']-last),abs(x['low']-last)))
    atr=sum(tr)/len(tr);stop=o-atr_mult*atr
    if 0<stop<o:
     unitrisk=o-stop+o*fee_bps/10000
     qty=max(0,math.floor(min(initial*risk/unitrisk,initial*max_exposure/(o*(1+fee)),cash/(o*(1+fee)))))
     if qty:
      r=session(cash,None,opening=o,low=o,entry_units=qty,entry_stop=stop,fee_rate=fee)
      cash,position=r['cash'],r['position'];events+=r['events']
      entry_cost=qty*o*(1+fee);entry_price=o;entry_date=b['date']
  # Stops occur AFTER all opening actions. No proceeds finance today's opening entry.
  if position:
   qty=position.units;stop=position.stop
   r=session(cash,position,opening=o,low=l,fee_rate=fee)
   cash,position=r['cash'],r['position'];events+=r['events']
   if position is None:
    proceeds=qty*stop*(1-fee)
    trades.append(dict(entry_date=entry_date,exit_date=b['date'],entry=entry_price,exit=stop,qty=qty,pnl=round(proceeds-entry_cost,2),reason='INTRADAY_STOP_ASSUMED'))
   elif i>=exit_lookback and c<min(x['low'] for x in bars[i-exit_lookback:i]):due=True
  equity=cash+(position.units*c if position else 0)
  peak=max(peak,equity)
  history.append(dict(date=b['date'],equity=round(equity,2),cash=round(cash,2),drawdown=round(1-equity/peak,6),units=position.units if position else 0))
 benchmark=initial*bars[-1]['close']/bars[0]['open']
 report=dict(status='RESEARCH_ONLY_BLOCKED',orders_enabled=False,isin=ISIN,source_sha256=m['raw_sha256'],
  source_status=m['status'],first_date=bars[0]['date'],last_date=bars[-1]['date'],sessions=len(bars),
  initial=initial,final_equity=round(history[-1]['equity'],2),buy_hold_gross_reference=round(benchmark,2),
  max_drawdown=max(x['drawdown'] for x in history),closed_trades=len(trades),
  assumptions='Real product CSV claimed by importer, next open, 20bps nominal round trip, conservative gap stop, no 2R profit target. Product fee already embedded in traded price; no double counting.',
  limitations='UNVERIFIED source attestation, spreads and broker commissions; daily OHLC stop fill assumed; no independent forward period, liquidity or issuer risk. Not live eligible.')
 (p/'virbtc_research_report.json').write_text(json.dumps(report,indent=2))
 for name,data in [('virbtc_research_equity.csv',history),('virbtc_research_trades.csv',trades)]:
  with (p/name).open('w',newline='') as f:
   if data:
    w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
 return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--folder',required=True);x=a.parse_args();print(json.dumps(run(x.folder),indent=2))
