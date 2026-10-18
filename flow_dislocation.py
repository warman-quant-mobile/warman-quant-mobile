"""Daily research-only flow dislocation; not an executable portfolio."""
import csv,json,statistics
from pathlib import Path
from datetime import datetime,timezone
PAIRS={'INVESTOR_B':'OMXS30','VOLVO_B':'OMXS30','ATLAS_A':'OMXS30','ABB':'OMXS30','NVIDIA':'NASDAQ100','MICROSOFT':'NASDAQ100','APPLE':'NASDAQ100','META':'NASDAQ100','AMAZON':'NASDAQ100'}
def load(p):
 d={}
 with open(p,newline='') as f:
  for r in csv.DictReader(f):
   try:
    date=r.get('session_date') or r['timestamp_utc'][:10]
    o,h,l,c,v=[float(r[k]) for k in ('Open','High','Low','Close','Volume')]
    if l>0 and l<=min(o,c)<=max(o,c)<=h:d[date]=(o,h,l,c,v)
   except (KeyError,ValueError):pass
 return d
def stats(ts):
 x=[t['net'] for t in ts];wins=sum(max(v,0) for v in x);loss=-sum(min(v,0) for v in x)
 return {'n':len(x),'mean_net_pct':round(statistics.mean(x)*100,4) if x else None,'profit_factor':round(wins/loss,3) if loss else None,'win_rate':round(sum(v>0 for v in x)/len(x),3) if x else None}
def run(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text());bars={}
 for s,m in manifest['symbols'].items():
  if '1d' in m:bars[s]=load(folder/m['1d']['file'])
 rows=[];today=datetime.now(timezone.utc).date().isoformat()
 for s,benchmark in PAIRS.items():
  if s not in bars or benchmark not in bars:continue
  a,b=bars[s],bars[benchmark];days=[d for d in sorted(set(a)&set(b)) if d<today]
  if len(days)<260:continue
  split=days[int(.7*len(days))]
  for family in ('relative_reversal','relative_momentum','weekly_close_reversal','breakout'):
   for hold in (3,5,10):
    trades=[];i=26
    while i+hold+1<len(days):
     d=days[i];prev=days[i-5];p=days[i-20:i]
     rel=a[d][3]/a[prev][3]-b[d][3]/b[prev][3]
     vols=[a[t][4] for t in p if a[t][4]>0]
     rv=a[d][4]/statistics.mean(vols) if len(vols)>=15 and a[d][4]>0 else 0
     hi=max(a[t][1] for t in p);lo=min(a[t][2] for t in p)
     loc=(a[d][3]-lo)/(hi-lo) if hi>lo else .5
     trigger=(family=='relative_reversal' and rel<-.06 and rv>1.5) or (family=='relative_momentum' and rel>.05 and rv>2 and loc>.8) or (family=='weekly_close_reversal' and rel<-.04 and loc<.2) or (family=='breakout' and a[d][3]>hi)
     if trigger:
      entryday=days[i+1];exitday=days[i+1+hold];entry=a[entryday][0]
      if entry>0:
       trades.append({'entry':entryday,'exit':exitday,'net':a[exitday][0]/entry-1-.002})
       i+=hold+2;continue
     i+=1
    train=[t for t in trades if t['exit']<split];test=[t for t in trades if t['entry']>=split]
    rows.append({'symbol':s,'benchmark_proxy':benchmark,'family':family,'hold_sessions':hold,'train':stats(train),'holdout':stats(test),'sufficient_sample':len(train)>=30 and len(test)>=12})
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'research_only':True,'validated_edge':False,'roundtrip_cost_bps':20,'split':'chronological 70/30, boundary trades excluded','limitations':['Broad index proxies not actual industry portfolios','Survivorship bias; fixed selected stocks','No actual ETP prices, funding or spreads','Multiple hypotheses and no independent validation','Per-symbol results are not an executable portfolio'],'results':rows}
 (folder/'flow_dislocation_report.json').write_text(json.dumps(report,indent=2))
 import csv as csvmod
 with (folder/'flow_dislocation_summary.csv').open('w',newline='') as f:
  w=csvmod.writer(f);w.writerow(['symbol','family','hold','train_n','train_avg_pct','holdout_n','holdout_avg_pct','holdout_pf','sufficient'])
  for r in rows:w.writerow([r['symbol'],r['family'],r['hold_sessions'],r['train']['n'],r['train']['mean_net_pct'],r['holdout']['n'],r['holdout']['mean_net_pct'],r['holdout']['profit_factor'],r['sufficient_sample']])
 print('Flow Dislocation tested',len(rows),'hypotheses; adequate sample',sum(r['sufficient_sample'] for r in rows))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--folder',default='output');run(p.parse_args().folder)
