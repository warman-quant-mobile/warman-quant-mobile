"""Rotation research: fixed rules, one position, walk-forward reporting. No orders."""
import csv,json,math,statistics
from pathlib import Path
from datetime import datetime,timezone
UNIVERSE=('INVESTOR_B','VOLVO_B','ATLAS_A','ABB')
def read(path):
 d={}
 with open(path,newline='') as f:
  for r in csv.DictReader(f):
   try:
    day=r.get('session_date') or r['timestamp_utc'][:10];c=float(r['Close'])
    if c>0:d[day]=c
   except (ValueError,KeyError):pass
 return d
def run(folder):
 p=Path(folder);m=json.loads((p/'manifest.json').read_text());data={}
 for s in (*UNIVERSE,'OMXS30'):
  a=m['symbols'].get(s,{})
  if '1d' in a:data[s]=read(p/a['1d']['file'])
 symbols=[s for s in UNIVERSE if s in data]
 dates=sorted(set.intersection(*(set(data[s]) for s in symbols))) if symbols else []
 dates=[d for d in dates if d<datetime.now(timezone.utc).date().isoformat()]
 split=dates[int(.7*len(dates))] if len(dates)>250 else None
 variants={}
 for lookback in (63,126):
  for gate in ('absolute','relative','always'):
   capital=100000.;position=None;equity=[];switches=0;hold_days=0
   for i,d in enumerate(dates):
    if i>=lookback+1 and (i-(lookback+1))%21==0:
     prev=dates[i-1];past=dates[i-1-lookback]
     scores={s:data[s][prev]/data[s][past]-1 for s in symbols}
     chosen=max(scores,key=scores.get)
     if gate=='absolute' and scores[chosen]<=0:chosen=None
     if gate=='relative' and 'OMXS30' in data and prev in data['OMXS30'] and past in data['OMXS30']:
      idx=data['OMXS30'][prev]/data['OMXS30'][past]-1
      if scores[chosen]<=idx:chosen=None
     if chosen!=position:
      # 10bps sell and 10bps buy when applicable, no same-day lookahead.
      if position is not None:capital*=.999
      if chosen is not None:capital*=.999
      switches+=1;position=chosen
    if i and position is not None:
     capital*=data[position][d]/data[position][dates[i-1]]
     hold_days+=1
    equity.append((d,capital))
   if not split:continue
   hold=[(d,v) for d,v in equity if d>=split]
   start,end=hold[0][1],hold[-1][1];pk=start;dd=0
   for _,v in hold:pk=max(pk,v);dd=max(dd,1-v/pk)
   bm={}
   for s in ('INVESTOR_B','OMXS30'):
    if s in data:
     arr=[(d,data[s][d]) for d in dates if d>=split and d in data[s]]
     if len(arr)>1:bm[s]=arr[-1][1]/arr[0][1]-1
   variants[f'{lookback}_{gate}']={'holdout_return':round(end/start-1,4),'holdout_max_drawdown':round(dd,4),'benchmarks_price_only':{k:round(v,4) for k,v in bm.items()},'switches_total':switches,'days_in_position_total':hold_days,'total_days':len(dates)}
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'validated_edge':False,'research_only':True,'split_date':split,'symbols':symbols,'assumptions':'21-session rotation, prior-close signals, close-to-close next-session returns, 10bps per side switch, no leverage','limitations':['Close-to-close execution assumes position changes at prior close, but signal at prior close is not executable at that price: requires next-open fills for a valid strategy','No dividends or total-return adjustment','Fixed surviving universe','Model selection on holdout invalidates independence','No actual instrument costs'],'variants':variants}
 (p/'rotation_research_report.json').write_text(json.dumps(report,indent=2))
 print('ROTATION RESEARCH',[(k,v['holdout_return']) for k,v in variants.items()])
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--folder',default='output');run(a.parse_args().folder)
