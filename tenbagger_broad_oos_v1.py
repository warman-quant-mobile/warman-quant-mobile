#!/usr/bin/env python3
"""Broad PIT tenbagger validation on SEC cohort. Current-survivor diagnostic; chronological OOS."""
import argparse,json,math
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf

def annual_series(c,key,asof):
 b=c.get("facts",{}).get(key,{}).get("facts",[])
 x=[z for z in b if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]))
 d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.items())
def last2(c,key,asof):
 x=annual_series(c,key,asof);return (x[-1][1],x[-2][1]) if len(x)>=2 else (None,None)
def last(c,key,asof):
 x=annual_series(c,key,asof);return x[-1][1] if x else None
def pct(a,b):
 return a/b-1 if a is not None and b not in (None,0) else np.nan
def rank(s,high=True): return s.rank(pct=True,ascending=high)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",default="output/sec_point_in_time_broad.json");ap.add_argument("--out",default="signals/tenbagger_broad_oos_v1.json");a=ap.parse_args()
 d=json.load(open(a.pit)); mp=d.get("selection",{}).get("ticker_by_cik",{}); companies=d["companies"]
 tickers=list(mp.values()); prices={}
 for i in range(0,len(tickers),200):
  batch=tickers[i:i+200]
  try:
   q=yf.download(batch,start="2012-01-01",end="2027-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in batch:
    try:
     s=q[t]["Close"].dropna() if len(batch)>1 else q["Close"].dropna()
     if len(s)>20: prices[t]=s
    except: pass
  except: pass
 rows=[]
 for cik,c in companies.items():
  t=mp.get(cik); px=prices.get(t)
  if px is None: continue
  for y in range(2014,2022):
   dt=f"{y}-06-30"; h=px.loc[:dt]
   if h.empty:continue
   p=float(h.iloc[-1]); rev,rev0=last2(c,"revenue",dt); op,op0=last2(c,"operating_income",dt); gp,gp0=last2(c,"gross_profit",dt)
   ni=last(c,"net_income",dt); assets=last(c,"assets",dt); eq=last(c,"equity",dt); cfo=last(c,"cfo",dt); capex=last(c,"capex",dt); debt=last(c,"debt",dt); sh,sh0=last2(c,"shares",dt)
   if rev is None or assets in (None,0):continue
   fcf=(cfo-capex) if cfo is not None and capex is not None else np.nan
   mom=(p/float(h.iloc[-13])-1) if len(h)>=13 else np.nan
   fut=px.loc[dt:f"{y+5}-06-30"]
   if len(fut)<24:continue
   mx=float(fut.max())/p
   rows.append(dict(ticker=t,cik=cik,date=dt,year=y,price=p,rev_growth=pct(rev,rev0),op_growth=pct(op,op0),gross_growth=pct(gp,gp0),roa=(ni/assets if ni is not None else np.nan),fcf_margin=(fcf/rev if rev else np.nan),debt_assets=(debt/assets if debt is not None else 0),dilution=pct(sh,sh0),momentum=mom,max5=mx,hit2=mx>=2,hit3=mx>=3,hit5=mx>=5,hit10=mx>=10))
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 # Scores frozen before OOS: growth/inflection vs value/recovery proxies using only PIT fields.
 for dt,gidx in df.groupby("date").groups.items():
  ix=list(gidx);g=df.loc[ix]
  growth=(rank(g.rev_growth).fillna(.5)+rank(g.op_growth).fillna(.5)+rank(g.gross_growth).fillna(.5)+rank(g.roa).fillna(.5)+rank(g.fcf_margin).fillna(.5)+rank(-g.dilution).fillna(.5)+rank(-g.debt_assets).fillna(.5)+rank(g.momentum).fillna(.5))/8
  recovery=(rank(g.rev_growth).fillna(.5)+rank(g.op_growth).fillna(.5)+rank(g.fcf_margin).fillna(.5)+rank(-g.debt_assets).fillna(.5)+rank(-g.dilution).fillna(.5)+rank(-abs(g.momentum)).fillna(.5))/6
  df.loc[ix,"growth_score"]=growth.values;df.loc[ix,"recovery_score"]=recovery.values
 split=2018; dev=df[df.year<split];test=df[df.year>=split]
 def stats(z,score):
  o={"n":len(z)}
  for lab in ["hit2","hit3","hit5","hit10"]:
   base=float(z[lab].mean());o[lab]={"base":base}
   for q in [.10,.05,.01]:
    top=z[z[score]>=z.groupby("date")[score].transform(lambda s:s.quantile(1-q))]
    rate=float(top[lab].mean()) if len(top) else None;o[lab][f"top{int(q*100)}"]=rate;o[lab][f"lift{int(q*100)}"]=(rate/base if base and rate is not None else None)
  return o
 # Contrast profiles: development only. Effect size is winner mean minus loser mean after within-date percentile ranks.
 feats=["rev_growth","op_growth","gross_growth","roa","fcf_margin","debt_assets","dilution","momentum"]
 D=dev.copy()
 for dt,ix in D.groupby("date").groups.items():
  for v in feats:D.loc[ix,v+"_pct"]=D.loc[ix,v].rank(pct=True).fillna(.5)
 contrast={}
 for lab in ["hit3","hit5","hit10"]:
  w=D[D[lab]];lo=D[D.max5<1.0];contrast[lab]={v:{"winner_mean":float(w[v+"_pct"].mean()),"loser_mean":float(lo[v+"_pct"].mean()),"spread":float(w[v+"_pct"].mean()-lo[v+"_pct"].mean())} for v in feats}
 out={"status":"BROAD_PIT_CURRENT_SURVIVOR_OOS_DIAGNOSTIC","split":"2014-2017 development; 2018-2021 untouched chronological OOS","price_interval":"monthly adjusted","coverage":{"pit_companies":len(companies),"mapped_tickers":len(tickers),"price_tickers":len(prices),"observations":len(df)},"contrast_dev_only":contrast,"growth_inflection":{"dev":stats(dev,"growth_score"),"oos":stats(test,"growth_score")},"value_recovery":{"dev":stats(dev,"recovery_score"),"oos":stats(test,"recovery_score")}}
 # Current candidate proxy = latest available observation per ticker scored by OOS-better hypothesis, not a calibrated probability.
 latest=df.sort_values("date").groupby("ticker").tail(1);out["historical_top_profiles"]=latest.sort_values("growth_score",ascending=False)[["ticker","date","growth_score","recovery_score"]].head(30).to_dict("records")
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
