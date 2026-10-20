"""Warman Trap research. Daily-bar approximation, NOT Mikrit's proprietary rules."""
import csv,json,statistics
from pathlib import Path
from datetime import datetime,timezone
SYMS=('INVESTOR_B','VOLVO_B','ATLAS_A','ABB','NVIDIA','MICROSOFT','APPLE','TESLA','AMAZON','META')
def load(path):
 out={}
 with open(path,newline='') as f:
  for r in csv.DictReader(f):
   try:
    d=r.get('session_date') or r['timestamp_utc'][:10]
    o,h,l,c=[float(r[k]) for k in ('Open','High','Low','Close')]
    v=float(r.get('Volume') or 0)
    if 0<l<=min(o,c)<=max(o,c)<=h:out[d]=(o,h,l,c,v)
   except (ValueError,KeyError):pass
 return out
def run(folder):
 p=Path(folder);manifest=json.loads((p/'manifest.json').read_text())
 data={s:load(p/manifest['symbols'][s]['1d']['file']) for s in (*SYMS,'OMXS30') if s in manifest['symbols'] and '1d' in manifest['symbols'][s]}
 common=sorted(set.intersection(*(set(data[s]) for s in SYMS if s in data)))
 common=[d for d in common if d<datetime.now(timezone.utc).date().isoformat()]
 split=common[int(len(common)*.7)] if len(common)>300 else None
 results={}
 for window in (10,20):
  for hold in (2,5):
   trades=[]
   for s in SYMS:
    if s not in data:continue
    rows=data[s];days=sorted(rows)
    for i in range(window+2,len(days)-hold-1):
     d=days[i];o,h,l,c,v=rows[d]
     prior=[rows[x] for x in days[i-window:i]]
     support=min(x[2] for x in prior)
     # False downside break: trade BELOW prior support, close back ABOVE it.
     if not(l<support and c>support and c>o):continue
     # Signal known at close; enter at next session OPEN, not same close.
     ed=days[i+1];entry=rows[ed][0]
     if entry<=0:continue
     # Stop at signal low, with adverse gap fills; daily OHLC cannot determine intraday path.
     stop=l; risk=entry-stop
     if risk<=0 or risk/entry>.12:continue
     target=entry+3*risk
     exit_px=None;exit_day=None;reason=None
     for j in range(i+1,i+hold+1):
      x=days[j];xo,xh,xl,xc,_=rows[x]
      if xo<=stop:exit_px=xo;reason='gap_stop'
      elif xo>=target:exit_px=xo;reason='gap_target'
      elif xl<=stop:exit_px=stop;reason='stop'
      elif xh>=target:exit_px=target;reason='target'
      if exit_px is not None:exit_day=x;break
     if exit_px is None:exit_day=days[i+hold];exit_px=rows[exit_day][3];reason='time_exit_close'
     # 20bps round trip and 10bps additional stop/target slippage estimate.
     cost=.003 if reason in ('stop','target','gap_stop','gap_target') else .002
     ret=exit_px/entry-1-cost
     trades.append({'symbol':s,'signal_date':d,'entry_date':ed,'exit_date':exit_day,'return':ret,'R':ret/(risk/entry),'reason':reason})
   # Diagnostic signal pool, NOT a simultaneous executable single-position portfolio.
   def stats(arr):
    a=[t['return'] for t in arr];w=sum(max(x,0) for x in a);loss=-sum(min(x,0) for x in a)
    return {'n':len(a),'mean_net_pct':round(statistics.mean(a)*100,3) if a else None,'profit_factor':round(w/loss,3) if loss else None,'win_rate':round(sum(x>0 for x in a)/len(a),3) if a else None,'mean_R':round(statistics.mean(t['R'] for t in arr),3) if arr else None}
   results[f'{window}d_{hold}d']={'train':stats([t for t in trades if split and t['exit_date']<split]),'holdout':stats([t for t in trades if split and t['entry_date']>=split]),'holdout_trades':[t for t in trades if split and t['entry_date']>=split]}
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'validated_edge':False,'research_only':True,'split_date':split,'method':'Failed downside break and same-day reclaim of previous 10/20-session low, enter next open, stop at signal low, 3R target, 2/5 day timeout, adverse same-bar stop precedence, 20-30bp costs','results':results,'limitations':['Signal-level pooled trades, NOT a cash-constrained portfolio or benchmarkable portfolio return','Daily OHLC cannot resolve stop-target ordering; assumes stop first','Selection and survivorship bias; multiple hypotheses explored','Unadjusted OHLC, dividends/splits require verification','Stop execution and slippage approximate','No short interest data; this is a bull-trap reversal proxy, NOT proven short squeeze','Cross-market signal calendars differ','High conviction sizing must NOT be inferred from these statistics']}
 (p/'trap_research_report.json').write_text(json.dumps(report,indent=2))
 print('TRAP RESEARCH',[(k,v['holdout']) for k,v in results.items()])
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--folder',default='output');run(a.parse_args().folder)
