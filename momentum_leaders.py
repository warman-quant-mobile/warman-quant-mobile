"""Monthly cross-sectional momentum: research only, never creates orders.
US PIT membership is reconstructed from dated community snapshots. OMXS30 excluded
until verified historical membership and delisted-price coverage are available.
"""
import io,json,requests,pandas as pd,numpy as np,yfinance as yf
from pathlib import Path
from datetime import datetime,timezone
BASE='https://raw.githubusercontent.com/thuningxu/sp500nq100/main/'
FILES={'sp500':'sp500_components_history.csv','nasdaq100':'nasdaq100_components_history.csv'}
START='2016-01-01'; END='2026-10-01'; FEE=0.002
def snapshots(name):
 r=requests.get(BASE+FILES[name],timeout=45);r.raise_for_status()
 df=pd.read_csv(io.StringIO(r.text));df['date']=pd.to_datetime(df['date'])
 return df.sort_values('date')
def get_prices(tickers):
 frames={}
 for start in range(0,len(tickers),35):
  batch=tickers[start:start+35]
  try:
   d=yf.download(batch,start=START,end=END,auto_adjust=True,progress=False,threads=True,group_by='ticker',timeout=35)
   for sym in batch:
    try:
     a=d[sym] if isinstance(d.columns,pd.MultiIndex) else d
     if a['Close'].notna().sum()>100:frames[sym]=a['Close'].astype(float)
    except (KeyError,TypeError):pass
  except Exception as exc:print('batch failed',start,str(exc)[:120])
  print('prices loaded',len(frames),'/',len(tickers),flush=True)
 return pd.DataFrame(frames).sort_index()
def main():
 out=Path('reports');out.mkdir(exist_ok=True)
 hist={k:snapshots(k) for k in FILES}
 # Conservative PIT: only constituents known at each month-end.
 months=pd.date_range('2017-01-31','2026-08-31',freq='ME')
 universes={}
 for dt in months:
  names=set()
  for df in hist.values():
   prior=df.loc[df.date<=dt]
   if not prior.empty:
    names.update(str(prior.iloc[-1]['tickers']).split(','))
  universes[str(dt.date())]=sorted(s.strip().replace('.','-') for s in names if s.strip())
 all_names=sorted(set().union(*[set(x) for x in universes.values()]))
 prices=get_prices(all_names+['SPY','QQQ','INVE-B.ST'])
 # Must retain missing-data diagnostics; never claim survivor-free if prices unavailable.
 def close_at(sym,date):
  if sym not in prices:return np.nan
  x=prices[sym].loc[:date].dropna()
  return float(x.iloc[-1]) if len(x) else np.nan
 outputs={}
 for lookback in (1,3,6,12):
  for n in (5,10):
   equity=1.;records=[];prev=[]
   for j in range(lookback,len(months)-1):
    d0=months[j];d1=months[j+1];past=months[j-lookback]
    pool=universes[str(d0.date())];rank=[]
    for s in pool:
     a,b=close_at(s,past),close_at(s,d0)
     if np.isfinite(a) and np.isfinite(b) and a>0:rank.append((b/a-1,s))
    rank.sort(reverse=True)
    chosen=[s for _,s in rank[:n]]
    # Require complete forward prices; missing delisted names make results unreliable.
    valid=[s for s in chosen if np.isfinite(close_at(s,d1)) and close_at(s,d0)>0]
    if len(valid)!=n:records.append({'month':str(d0.date()),'status':'missing_forward_price','eligible':len(rank)});continue
    turnover=1-len(set(chosen)&set(prev))/n if prev else 1
    r=np.mean([close_at(s,d1)/close_at(s,d0)-1 for s in chosen])-FEE*turnover
    equity*=1+r;prev=chosen
    records.append({'month':str(d0.date()),'return':float(r),'equity':float(equity),'holdings':chosen,'eligible':len(rank)})
   completed=[x for x in records if 'return' in x]
   vals=np.array([x['return'] for x in completed])
   if len(vals):
    curve=np.cumprod(1+vals);peak=np.maximum.accumulate(np.r_[1,curve])[1:]
    dd=float(np.min(curve/peak-1))
    cagr=float(np.prod(1+vals)**(12/len(vals))-1)
   else:dd=cagr=None
   outputs[f'{lookback}m_top{n}']={'months_tested':len(completed),'months_missing':len(records)-len(completed),'cagr':cagr,'max_drawdown':dd,'monthly_returns':records}
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'research_only':True,'validated_edge':False,'universe':'US S&P 500 and Nasdaq 100 PIT snapshots; OMXS30 NOT included','lookback_months':[1,3,6,12],'portfolio_sizes':[5,10],'monthly_cost_assumption':FEE,'price_source':'Yahoo auto_adjust','membership_source':BASE,'critical_limitations':['Missing delisted price series can create survivorship bias','Month-end close signals and close-to-close fills are not fully executable','Historical constituent reconstruction is community-maintained and requires audit','OMXS30 not included','Investor total-return comparison pending reliable adjusted history and FX treatment','Missing forward prices skipped, causing selection bias'],'results':outputs}
 (out/'momentum_leaders_report.json').write_text(json.dumps(report,indent=2))
 print('RESULT',[(k,v['cagr'],v['months_missing']) for k,v in outputs.items()])
if __name__=='__main__':main()
