"""Exploratory research only. No orders, no strategy promotion."""
import argparse,csv,json,math,statistics
from datetime import datetime,timezone,timedelta
from pathlib import Path
from indicators import HOURLY,DAILY,simulate as indicator_simulate
FAMILIES=('breakout','momentum','reversion')
WINDOWS=(12,20,36)
COST=.002
def read(path,now):
 out={}
 with path.open(newline='') as f:
  for r in csv.DictReader(f):
   try:
    t=datetime.fromisoformat(r['timestamp_utc'].replace('Z','+00:00'))
    o,h,l,c=(float(r[k]) for k in ('Open','High','Low','Close'))
    if t+timedelta(hours=1)<=now and all(map(math.isfinite,(o,h,l,c))) and 0<l<=min(o,c)<=max(o,c)<=h:out[t]=(t,o,h,l,c)
   except (KeyError,ValueError):pass
 return sorted(out.values())
def signal(a,i,f,n):
 p=a[i-n:i];c=a[i][4];hi=max(x[2] for x in p);lo=min(x[3] for x in p)
 if f=='breakout':return 1 if c>hi else -1 if c<lo else 0
 if f=='momentum':
  move=c/p[0][4]-1
  return 1 if move>.025 else -1 if move<-.025 else 0
 mean=statistics.mean(x[4] for x in p);sd=statistics.pstdev(x[4] for x in p)
 return -1 if sd and c>mean+1.5*sd else 1 if sd and c<mean-1.5*sd else 0
def simulate(a,f,n):
 trades=[];i=n
 while i<len(a)-2:
  side=signal(a,i,f,n)
  if not side:i+=1;continue
  entry=a[i+1][1];unit=statistics.mean(x[2]-x[3] for x in a[i-n:i])
  if unit<=0 or entry<=0:i+=1;continue
  stop=entry-side*2*unit;target=entry+side*4*unit
  if stop<=0:i+=1;continue
  end=min(i+12,len(a)-1);exitprice=a[end][4];exitindex=end
  for j in range(i+1,end+1):
   _,o,h,l,c=a[j]
   if (l<=stop if side>0 else h>=stop):
    exitprice=min(o,stop) if side>0 else max(o,stop);exitindex=j;break
   if (h>=target if side>0 else l<=target):
    exitprice=target;exitindex=j;break
  r=(side*(exitprice-entry)-entry*COST)/(2*unit)
  trades.append((a[i+1][0],a[exitindex][0],r,side*(exitprice-entry)/entry-COST))
  i=exitindex+1
 return trades
def stats(ts):
 if not ts:return dict(n=0,mean_r=None,win_rate=None,max_drawdown=None,net_return=None)
 eq=peak=1.;dd=0.
 for _,_,_,ret in ts:
  eq*=max(.00001,1+ret);peak=max(peak,eq);dd=max(dd,1-eq/peak)
 return dict(n=len(ts),mean_r=round(statistics.mean(x[2] for x in ts),4),
             win_rate=round(sum(x[2]>0 for x in ts)/len(ts),4),
             max_drawdown=round(dd,4),net_return=round(eq-1,4))
def run(folder,now):
 q=json.loads((folder/'quality.json').read_text());m=json.loads((folder/'manifest.json').read_text());rows=[]
 for sym in sorted(q['eligible_symbols']):
  meta=m['symbols'].get(sym,{})
  if '1h' not in meta:continue
  a=read(folder/meta['1h']['file'],now)
  if len(a)<180:continue
  split=a[int(.7*len(a))][0]
  for f in FAMILIES:
   for n in WINDOWS:
    trades=simulate(a,f,n)
    train=[t for t in trades if t[1]<split]
    test=[t for t in trades if t[0]>=split]
    tr=stats(train);te=stats(test)
    rows.append(dict(symbol=sym,family=f,lookback=n,interval='1h',train=tr,holdout=te,
                     sufficient_sample=tr['n']>=30 and te['n']>=12))
 # Indicator candidates: preserve original control models, add independent experiments.
 for sym in sorted(q['eligible_symbols']):
  meta=m['symbols'].get(sym,{})
  for interval,names in (('1h',HOURLY),('1d',DAILY)):
   if interval not in meta:continue
   a=read(folder/meta[interval]['file'],now if interval=='1h' else now+timedelta(hours=23))
   # Daily source dates are session labels. Exclude current UTC date as provisional.
   if interval=='1d':a=[x for x in a if x[0].date()<now.date()]
   if len(a)<220:continue
   split=a[int(.7*len(a))][0]
   for name in names:
    trades=indicator_simulate(a,name)
    train=[t for t in trades if t[1]<split]
    test=[t for t in trades if t[0]>=split]
    tr=stats(train);te=stats(test)
    rows.append(dict(symbol=sym,family=name,lookback=None,interval=interval,train=tr,holdout=te,
                     sufficient_sample=tr['n']>=30 and te['n']>=12))
 report=dict(asof=now.isoformat(),research_only=True,holdout='chronological 70/30; boundary trades excluded',
             cost_round_trip_bps=20,assumptions='next-bar open; 12-bar max hold; stop-first; no leverage; no funding/borrow; independent hypothetical trades, NOT portfolio',
             limitations='Yahoo historical data, unverified executable prices; no selection using holdout; results do not establish edge',
             candidates=len(rows),sufficient_sample=sum(r['sufficient_sample'] for r in rows),results=rows)
 (folder/'research_report.json').write_text(json.dumps(report,indent=2))
 with (folder/'research_summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['symbol','family','lookback','train_n','train_mean_r','holdout_n','holdout_mean_r','holdout_drawdown','sufficient_sample']);w.writeheader()
  for r in rows:w.writerow(dict(symbol=r['symbol'],family=r['family'],lookback=r['lookback'],train_n=r['train']['n'],train_mean_r=r['train']['mean_r'],holdout_n=r['holdout']['n'],holdout_mean_r=r['holdout']['mean_r'],holdout_drawdown=r['holdout']['max_drawdown'],sufficient_sample=r['sufficient_sample']))
 print('RESEARCH',len(rows),'hypotheses; adequate sample:',report['sufficient_sample'])
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--folder',default='output');args=p.parse_args()
 run(Path(args.folder),datetime.now(timezone.utc))
