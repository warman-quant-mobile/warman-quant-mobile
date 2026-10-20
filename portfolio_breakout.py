"""Research-only, one-position cash-backed breakout portfolio. No trade authorization."""
import csv,json,math,statistics
from datetime import datetime,timezone
from pathlib import Path
SYMS=('INVESTOR_B','VOLVO_B','ATLAS_A','ABB')
def load(p):
 out={}
 with open(p,newline='') as f:
  for r in csv.DictReader(f):
   try:
    day=r.get('session_date') or r['timestamp_utc'][:10]
    o,h,l,c=[float(r[k]) for k in ('Open','High','Low','Close')]
    if l>0 and l<=min(o,c)<=max(o,c)<=h:out[day]=(o,h,l,c)
   except (ValueError,KeyError):pass
 return out
def run(folder):
 folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
 data={s:load(folder/m['symbols'][s]['1d']['file']) for s in SYMS if s in m['symbols'] and '1d' in m['symbols'][s]}
 for b in ('INVESTOR_B','OMXS30'):
  if b in m['symbols'] and '1d' in m['symbols'][b]:data[b]=load(folder/m['symbols'][b]['1d']['file'])
 dates=sorted(set().union(*(set(x) for x in data.values())))
 dates=[d for d in dates if d<datetime.now(timezone.utc).date().isoformat()]
 split=dates[int(.7*len(dates))] if dates else None
 results={}
 for stop_mult in (2.0,3.0):
  cash=100000.;pos=None;trades=[];equity=[];peak=cash
  for i,d in enumerate(dates):
   # Signals from previous completed daily bar; today's opening fills.
   if pos and d in data[pos['symbol']]:
    o,h,l,c=data[pos['symbol']][d]
    if o<=pos['stop']:
     px=o;reason='gap_stop'
    elif l<=pos['stop']:
     px=pos['stop'];reason='intraday_stop_assumed'
    else:px=None;reason=None
    if px is not None:
     cash+=pos['qty']*px*(1-.001)
     trades.append({'symbol':pos['symbol'],'entry_date':pos['date'],'exit_date':d,'entry':pos['entry'],'exit':px,'reason':reason,'net_return':px/pos['entry']*(1-.001)/(1+.001)-1,'pnl':cash-pos['cash_before']})
     pos=None
   if pos is None and i>=23:
    candidates=[]
    for s in SYMS:
     if s not in data or d not in data[s]:continue
     prior=[data[s].get(t) for t in dates[i-21:i]]
     if any(x is None for x in prior):continue
     signal=prior[-1][3]>max(x[1] for x in prior[:-1])
     if not signal:continue
     tr=[max(x[1]-x[2],abs(x[1]-prior[j-1][3]),abs(x[2]-prior[j-1][3])) for j,x in enumerate(prior[1:],1)]
     atr=statistics.mean(tr)
     if atr<=0:continue
     strength=prior[-1][3]/max(x[1] for x in prior[:-1])-1
     candidates.append((-strength,s,atr))
    if candidates:
     _,s,atr=sorted(candidates)[0]
     o,h,l,c=data[s][d]
     stop=o-stop_mult*atr
     if stop>0:
      before=cash;qty=cash/(o*1.001);cash-=qty*o*1.001
      pos={'symbol':s,'entry':o,'date':d,'qty':qty,'stop':stop,'cash_before':before,'peak_close':o}
   if pos and d in data[pos['symbol']]:
    o,h,l,c=data[pos['symbol']][d]
    # Stop is updated after close; never uses current close to stop out earlier today.
    pos['peak_close']=max(pos['peak_close'],c)
    # ATR fixed at entry; stop never loosens.
    pos['stop']=max(pos['stop'],pos['peak_close']-stop_mult*(pos['entry']-pos['stop'])/stop_mult) if False else pos['stop']
    # trailing via entry ATR, not recalculated lookahead
    if 'atr' not in pos:pos['atr']=(pos['entry']-pos['stop'])/stop_mult
    pos['stop']=max(pos['stop'],pos['peak_close']-stop_mult*pos['atr'])
   marked=cash+(pos['qty']*data[pos['symbol']][d][3] if pos and d in data[pos['symbol']] else (pos['qty']*pos['entry'] if pos else 0))
   peak=max(peak,marked);equity.append({'date':d,'equity':round(marked,2),'drawdown':round(1-marked/peak,6)})
  def metrics(sub):
   rets=[t['net_return'] for t in sub];wins=sum(max(0,x) for x in rets);loss=-sum(min(0,x) for x in rets)
   return {'n':len(rets),'profit_factor':round(wins/loss,3) if loss else None,'mean_net_pct':round(100*statistics.mean(rets),3) if rets else None,'win_rate':round(sum(x>0 for x in rets)/len(rets),3) if rets else None}
  hold=[t for t in trades if t['entry_date']>=split]
  eq_hold=[x for x in equity if x['date']>=split]
  start=eq_hold[0]['equity'] if eq_hold else None;end=eq_hold[-1]['equity'] if eq_hold else None
  maxdd=0;pk=0
  for x in eq_hold:
   pk=max(pk,x['equity']);maxdd=max(maxdd,1-x['equity']/pk)
  benchmarks={}
  for s in ('INVESTOR_B','OMXS30'):
   arr=[(d,data[s][d][3]) for d in dates if s in data and d in data[s] and d>=split]
   if len(arr)>1:benchmarks[s]=round(arr[-1][1]/arr[0][1]-1,4)
  results[str(stop_mult)]={'train':metrics([t for t in trades if t['exit_date']<split]),'holdout':metrics(hold),'holdout_portfolio_return':round(end/start-1,4) if start and end else None,'holdout_max_drawdown':round(maxdd,4),'holdout_benchmarks_price_only':benchmarks,'trades':trades,'equity':equity}
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'research_only':True,'validated_edge':False,'capital':100000,'universe':list(data),'split_date':split,'rules':'Prior-close 20-day breakout; next-open entry; one long position; strongest breakout; 2/3 ATR trailing stop after close; full cash allocation; gap-aware stops; 20bp total costs','limitations':'Survivorship, no ETP financing, no intraday stop execution proof, selection bias; benchmark excludes dividends; stop parameter comparison is exploratory','results':results}
 (folder/'portfolio_breakout_report.json').write_text(json.dumps(report,indent=2))
 for mult,r in results.items():
  with (folder/('portfolio_breakout_trades_'+mult.replace('.','_')+'.csv')).open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=['symbol','entry_date','exit_date','entry','exit','reason','net_return','pnl']);w.writeheader();w.writerows(r['trades'])
 print('PORTFOLIO BREAKOUT',[(k,v['holdout']) for k,v in results.items()])
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--folder',default='output');run(p.parse_args().folder)
