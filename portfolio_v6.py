"""Research-only chronological DAILY multi-asset Turtle portfolio; no broker integration.
Signals use prior completed daily close; next session open entry. Stop first and gap-aware.
Prices are proxies, not executable contracts. Long-only by default, no borrowing.
"""
import csv,json,math
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
def load(path):
 out=[]
 with open(path,newline='') as f:
  for r in csv.DictReader(f):
   try:
    day=r.get('session_date') or r['timestamp_utc'][:10]
    o,h,l,c=(float(r[k]) for k in ('Open','High','Low','Close'))
    if all(math.isfinite(x) for x in (o,h,l,c)) and 0<l<=min(o,c)<=max(o,c)<=h:
     out.append((day,o,h,l,c))
   except (KeyError,ValueError):continue
 return sorted(dict((x[0],x) for x in out).values())
def run(folder,initial=100000,risk=.01,gross_cap=1.,max_positions=2,cost=.002,lookback=20):
 folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
 crypto=('BITCOIN','ETHEREUM','SOLANA')
 bars={s:load(folder/meta['1d']['file']) for s,meta in m['symbols'].items() if s in crypto and '1d' in meta}
 dates=sorted({x[0] for series in bars.values() for x in series if x[0]<datetime.now(timezone.utc).date().isoformat()})
 lookup={s:{x[0]:x for x in a} for s,a in bars.items()}
 indices={s:{x[0]:i for i,x in enumerate(a)} for s,a in bars.items()}
 cash=initial;positions={};history=[];trades=[];rejections=[];peak=initial
 for day in dates:
  # All exits are evaluated before new entries. Missing bars do not imply a zero price.
  for s,p in list(positions.items()):
   b=lookup[s].get(day)
   if not b:continue
   _,o,h,l,c=b
   stop=p['stop']
   if l<=stop:
    exitprice=min(o,stop);pnl=(exitprice-p['entry'])*p['qty']-cost*.5*(exitprice+p['entry'])*p['qty']
    cash+=p['reserved']+pnl
    trades.append(dict(symbol=s,entry_day=p['day'],exit_day=day,entry=p['entry'],exit=exitprice,qty=p['qty'],pnl=round(pnl,2),reason='STOP'))
    del positions[s];continue
   # Prior completed bars only: channel exit at close is filled at NEXT available open.
   if p.get('exit_due'):
    exitprice=o;pnl=(exitprice-p['entry'])*p['qty']-cost*.5*(exitprice+p['entry'])*p['qty']
    cash+=p['reserved']+pnl
    trades.append(dict(symbol=s,entry_day=p['day'],exit_day=day,entry=p['entry'],exit=exitprice,qty=p['qty'],pnl=round(pnl,2),reason='CHANNEL'))
    del positions[s];continue
   i=indices[s][day];a=bars[s]
   if i>=10 and c<min(x[3] for x in a[i-10:i]):p['exit_due']=True
  equity=cash+sum(p['reserved']+p['qty']*(p['mark']-p['entry']) for p in positions.values()) # Prior completed marks only; never size at today's close.
  # Signal from previous completed bar only. Fill at current open. Rank deterministically.
  candidates=[]
  for s,a in bars.items():
   i=indices[s].get(day)
   if i is None or i<lookback+2 or s in positions:continue
   prev=a[i-1];prior=a[i-lookback-1:i-1]
   if prev[4]>max(x[2] for x in prior):
    ranges=[max(x[2]-x[3],abs(x[2]-a[j-1][4]),abs(x[3]-a[j-1][4])) for j,x in enumerate(a[i-21:i-1],start=i-21)]
    vol=sum(ranges)/len(ranges)
    if vol>0:candidates.append((s,a[i][1],vol))
  for s,entry,vol in sorted(candidates):
   if len(positions)>=max_positions:break
   stop=entry-2*vol
   if stop<=0:continue
   # cash-backed spot only; gross exposure <= equity, no margin, no shorting.
   qty=min(max(0,equity*risk/(entry-stop)),max(0,cash)/entry,max(0,equity*gross_cap-sum(p['reserved'] for p in positions.values()))/entry)
   if qty<=0:rejections.append(dict(day=day,symbol=s,reason='NO_CAPITAL'));continue
   reserved=qty*entry;cash-=reserved
   b=lookup[s][day]
   if b[3]<=stop:
    exitprice=stop # Entry at open; same-bar stop-first, no gap before entry.
    pnl=(exitprice-entry)*qty-cost*.5*(exitprice+entry)*qty
    cash+=reserved+pnl
    trades.append(dict(symbol=s,entry_day=day,exit_day=day,entry=entry,exit=exitprice,qty=qty,pnl=round(pnl,2),reason='ENTRY_BAR_STOP'))
   else:positions[s]=dict(day=day,entry=entry,qty=qty,reserved=reserved,stop=stop,mark=entry,exit_due=False)
  for s,p in positions.items():
   if day in lookup[s]:p['mark']=lookup[s][day][4]
  equity=cash+sum(p['reserved']+p['qty']*(p['mark']-p['entry']) for p in positions.values())
  peak=max(peak,equity)
  history.append(dict(date=day,equity=round(equity,2),cash=round(cash,2),open_positions=len(positions),drawdown=round(1-equity/peak,5)))
 report=dict(research_only=True,universe=list(bars),initial=initial,final_marked_equity=history[-1]['equity'] if history else initial,
             closed_trades=len(trades),max_drawdown=max((x['drawdown'] for x in history),default=0),
             assumptions='Daily long-only crypto spot proxy, next open, no leverage, cash backed, 20bps round-trip, gap stops, close signal next open; no shorting, funding or margin',
             limitations='Exploratory; same daily Yahoo history already inspected; no independent holdout, venue quotes, volume impact, delistings, custody or taxes')
 (folder/'portfolio_v6_report.json').write_text(json.dumps(report,indent=2))
 for name,rows in (('portfolio_v6_equity.csv',history),('portfolio_v6_trades.csv',trades)):
  with (folder/name).open('w',newline='') as f:
   if rows:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 print('PORTFOLIO V6:',report['final_marked_equity'],'trades',len(trades))
 return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--folder',default='output');args=p.parse_args();run(args.folder)
