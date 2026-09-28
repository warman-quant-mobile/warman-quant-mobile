"""Research-only hourly paper engine. Never sends orders."""
import argparse,csv,json,math
from datetime import datetime,timezone,timedelta
from pathlib import Path
RISK=.02; COST=.002; INITIAL=100000.; MAX_POS=2; N=20
def bars(path,now):
 with open(path,newline='') as f: rows=list(csv.DictReader(f))
 out=[]
 for r in rows:
  try:
   t=datetime.fromisoformat(r['timestamp_utc'].replace('Z','+00:00'))
   o,h,l,c=[float(r[k]) for k in ('Open','High','Low','Close')]
   if t+timedelta(hours=1)<=now and all(map(math.isfinite,(o,h,l,c))) and l>0 and l<=min(o,c)<=max(o,c)<=h:
    out.append(dict(t=t,o=o,h=h,l=l,c=c))
  except (ValueError,KeyError): continue
 return sorted(out,key=lambda x:x['t'])
def process(folder,statepath,now):
 q=json.loads((folder/'quality.json').read_text());m=json.loads((folder/'manifest.json').read_text())
 s=json.loads(statepath.read_text()) if statepath.exists() else dict(equity=INITIAL,seen={},pending=[],positions=[],trades=[],events=[])
 new=[]
 for sym in q['eligible_symbols']:
  if '1h' not in m['symbols'][sym]:continue
  a=bars(folder/m['symbols'][sym]['1h']['file'],now)
  if len(a)<N+2:continue
  if sym not in s['seen']:
   s['seen'][sym]=a[-1]['t'].isoformat();continue # No retrospective invented fills.
  for i,b in enumerate(a):
   ts=b['t'].isoformat()
   if ts<=s['seen'][sym] or i<N:continue
   for p in list(s['pending']):
    if p['symbol']!=sym:continue
    if ts<p['due']:continue
    s['pending'].remove(p)
    if ts!=p['due'] or len(s['positions'])>=MAX_POS:
     new.append(dict(**p,status='MISSED_OR_CAPACITY'));continue
    entry=b['o'];risk=abs(entry-p['stop'])
    if risk<=0 or (p['side']=='LONG' and entry<=p['stop']) or (p['side']=='SHORT' and entry>=p['stop']):
     new.append(dict(**p,status='INVALID_GAP'));continue
    qty=min(s['equity']*RISK/risk,s['equity']/entry)
    if qty<=0:continue
    target=entry+(3*risk if p['side']=='LONG' else -3*risk)
    pos=dict(**p,status='ACTIVE',entry_time=ts,entry=entry,qty=qty,target=target,risk=qty*risk)
    s['positions'].append(pos);new.append(pos.copy())
   for p in list(s['positions']):
    if p['symbol']!=sym or ts<p['entry_time']:continue
    long=p['side']=='LONG'
    stophit=b['l']<=p['stop'] if long else b['h']>=p['stop']
    targethit=b['h']>=p['target'] if long else b['l']<=p['target']
    if not (stophit or targethit):continue
    price=(min(b['o'],p['stop']) if long else max(b['o'],p['stop'])) if stophit else p['target']
    pnl=(price-p['entry'])*p['qty']*(1 if long else -1)-COST*(price+p['entry'])*p['qty']/2
    s['equity']+=pnl;s['positions'].remove(p)
    trade=dict(**p,status='CLOSED',exit_time=ts,exit=price,reason='STOP' if stophit else 'TARGET',pnl=round(pnl,2),multiple=round(pnl/p['risk'],3))
    s['trades'].append(trade);new.append(trade.copy())
   if any(p['symbol']==sym for p in s['pending']+s['positions']):continue
   prior=a[i-N:i];hi=max(x['h'] for x in prior);lo=min(x['l'] for x in prior)
   side='LONG' if b['c']>hi else 'SHORT' if b['c']<lo else None
   if side:
    due=b['t']+timedelta(hours=1)
    sig=dict(id=sym+':'+ts+':'+side,symbol=sym,side=side,signal_time=ts,due=due.isoformat(),stop=lo if side=='LONG' else hi,status='TRIGGERED')
    s['pending'].append(sig);new.append(sig.copy())
  s['seen'][sym]=a[-1]['t'].isoformat()
 s['events'].extend(new);statepath.parent.mkdir(parents=True,exist_ok=True)
 statepath.write_text(json.dumps(s,indent=2),encoding='utf-8')
 (folder/'paperdesk_report.json').write_text(json.dumps(dict(asof=now.isoformat(),equity=round(s['equity'],2),positions=s['positions'],pending=s['pending'],new_events=new,closed=len(s['trades']),limitations='Research-only Yahoo data; next-hour open; stop-first; 20bps assumed costs; unleveraged; no broker fills.'),indent=2),encoding='utf-8')
 with (folder/'paperdesk_trades.csv').open('w',newline='') as f:
  keys=['id','symbol','side','signal_time','entry_time','entry','stop','target','qty','risk','exit_time','exit','reason','pnl','multiple']
  w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(s['trades'])
 print('paperdesk:',len(new),'events;',len(s['positions']),'open; equity',round(s['equity'],2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--folder',default='output');p.add_argument('--state',default='state/paperdesk.json');a=p.parse_args()
 process(Path(a.folder),Path(a.state),datetime.now(timezone.utc))
