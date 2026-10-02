#!/usr/bin/env python3
"""Frozen Graham-style research-window control. NEVER reads 2022+.
Uses only fields available point-in-time in the SEC artifact.
This is NOT the full Graham Defensive Investor screen: historical dividend
continuity and current ratio are unavailable in the present PIT dataset.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf

def ann(c,k,asof):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"])); d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.items())
def l1(c,k,d):
 x=ann(c,k,d); return x[-1][1] if x else None
def hist(c,k,d,n=4):
 x=ann(c,k,d); return [v for _,v in x[-n:]]
def perf(rs):
 if not rs:return {}
 w=np.cumprod(1+np.array(rs)); n=len(rs)
 return {"years":n,"cumulative":float(w[-1]-1),"cagr":float(w[-1]**(1/n)-1),
         "max_drawdown":float(np.min(w/np.maximum.accumulate(w)-1))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2010-01-01",end="2022-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>24:px[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);p=px.get(t)
  if p is None:continue
  for y in range(2014,2021):
   dt=f"{y}-06-30";h=p.loc[:dt];f=p.loc[dt:f"{y+1}-06-30"]
   if len(h)<13 or len(f)<10:continue
   ni=l1(c,"net_income",dt);eq=l1(c,"equity",dt);sh=l1(c,"shares",dt);debt=l1(c,"debt",dt)
   if ni is None or eq is None or sh in (None,0) or ni<=0 or eq<=0:continue
   price=float(h.iloc[-1]);eps=ni/sh;bvps=eq/sh
   if eps<=0 or bvps<=0:continue
   pe=price/eps;pb=price/bvps;de=(debt/eq if debt is not None else np.nan)
   earn=hist(c,"net_income",dt,4); stable=len(earn)>=4 and all(v>0 for v in earn)
   core=(pe<=15 and pb<=1.5 and pe*pb<=22.5)
   strength=core and stable and (np.isnan(de) or de<=1.0)
   rows.append({"ticker":t,"year":y,"ret":float(f.iloc[-1]/price-1),"pe":pe,"pb":pb,"graham_product":pe*pb,"debt_equity":de,"earnings_4y_positive":stable,"core":core,"strength":strength})
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 drag=.005;out={"status":"FROZEN_GRAHAM_STYLE_CONTROL_RESEARCH_ONLY","window":"2014-2020; code hard-stops prices before 2022","final_holdout_policy":"2022+ is not read or used","limitations":["Current-survivor ticker cohort; not delisting-complete.","Full Graham Defensive screen cannot be reproduced: PIT current ratio and long dividend history are unavailable.","Share-count based per-share ratios inherit SEC share-tag comparability limitations."],"rules":{"core":"positive earnings/equity; PE<=15; PB<=1.5; PE*PB<=22.5","strength":"core + four latest annual net incomes positive + debt/equity<=1 when debt is available"},"cost_drag":drag,"coverage":{"priced":len(px),"observations":len(df)},"results":{}}
 for rule in ["core","strength"]:
  s=[];b=[];annual=[]
  for y,g in df.groupby("year"):
   sel=g[g[rule]]
   if len(sel)==0:continue
   sr=float(sel.ret.mean()-drag);br=float(g.ret.mean()-drag);s.append(sr);b.append(br)
   annual.append({"year":int(y),"n":len(sel),"net_return":sr,"eligible_equal_weight_net":br,"tickers":sel.ticker.tolist()})
  ps,pb=perf(s),perf(b)
  out["results"][rule]={"strategy":ps,"eligible_equal_weight":pb,"active_cagr":ps.get("cagr",0)-pb.get("cagr",0),"annual":annual}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
