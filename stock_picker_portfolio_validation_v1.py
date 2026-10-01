#!/usr/bin/env python3
"""Portfolio-level validation for Warman Stock Picker.
Uses only the development/OOS-research window through 2021. 2022+ is intentionally
not read for model selection, preserving a later final holdout.
This is a robustness layer, not a survivorship-free certification: PIT fundamentals
are SEC filing-timestamped, but the available ticker cohort can still omit historical
delistings. Results are therefore fail-closed and explicitly labelled.
"""
import argparse,json,math
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf

F=["rev_growth","op_growth","gross_growth","roa","fcf_margin","debt_assets","dilution","momentum"]
def ann(c,k,asof):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"])); d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.items())
def l1(c,k,d):
 x=ann(c,k,d);return x[-1][1] if x else None
def l2(c,k,d):
 x=ann(c,k,d);return (x[-1][1],x[-2][1]) if len(x)>1 else (None,None)
def pct(a,b):return a/b-1 if a is not None and b not in (None,0) else np.nan
def rnk(s,hi=True):return s.rank(pct=True,ascending=hi)
def perf(rs):
 if not rs:return {}
 w=np.cumprod(1+np.array(rs)); years=len(rs)
 return {"years":years,"cumulative":float(w[-1]-1),"cagr":float(w[-1]**(1/years)-1),"max_drawdown":float(np.min(w/np.maximum.accumulate(w)-1))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",default="output/sec_point_in_time_broad.json");ap.add_argument("--out",default="signals/stock_picker_portfolio_validation_v1.json");a=ap.parse_args()
 d=json.load(open(a.pit)); mp=d.get("selection",{}).get("ticker_by_cik",{}); cs=d["companies"]; ticks=list(dict.fromkeys(mp.values()))
 px={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2012-01-01",end="2022-01-10",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
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
   dt=f"{y}-06-30"; h=p.loc[:dt]; fut=p.loc[dt:f"{y+1}-06-30"]
   if len(h)<13 or len(fut)<10:continue
   rev,r0=l2(c,"revenue",dt);op,o0=l2(c,"operating_income",dt);gp,g0=l2(c,"gross_profit",dt)
   ni=l1(c,"net_income",dt);ass=l1(c,"assets",dt);cfo=l1(c,"cfo",dt);cap=l1(c,"capex",dt);debt=l1(c,"debt",dt);sh,s0=l2(c,"shares",dt)
   if rev is None or ass in (None,0):continue
   entry=float(h.iloc[-1]); exit=float(fut.iloc[-1]); fcf=(cfo-cap) if cfo is not None and cap is not None else np.nan
   rows.append(dict(ticker=t,year=y,date=dt,ret=exit/entry-1,rev_growth=pct(rev,r0),op_growth=pct(op,o0),gross_growth=pct(gp,g0),roa=(ni/ass if ni is not None else np.nan),fcf_margin=(fcf/rev if rev else np.nan),debt_assets=(debt/ass if debt is not None else np.nan),dilution=pct(sh,s0),momentum=entry/float(h.iloc[-13])-1))
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 # frozen, simple composite; no tuning on later years
 for dt,ix in df.groupby("date").groups.items():
  g=df.loc[ix]
  quality=(rnk(g.roa).fillna(.5)+rnk(g.fcf_margin).fillna(.5)+rnk(-g.debt_assets).fillna(.5)+rnk(-g.dilution).fillna(.5))/4
  growth=(rnk(g.rev_growth).fillna(.5)+rnk(g.op_growth).fillna(.5)+rnk(g.gross_growth).fillna(.5))/3
  mom=rnk(g.momentum).fillna(.5)
  df.loc[ix,"score"]=(.35*quality+.35*growth+.30*mom).values
 costs={"us_roundtrip_bps":30,"fx_roundtrip_bps":20}; drag=(costs["us_roundtrip_bps"]+costs["fx_roundtrip_bps"])/10000
 results={}
 for k in [5,10,20]:
  strat=[];ew=[];abl=[]
  details=[]
  for y,g in df.groupby("year"):
   g=g.dropna(subset=["ret","score"]); top=g.nlargest(min(k,len(g)),"score")
   sr=float(top.ret.mean()-drag); br=float(g.ret.mean()-drag)
   # winner dependence: remove best realized stock AFTER selection only as a stress diagnostic
   wo=top.drop(top.ret.idxmax()) if len(top)>1 else top
   strat.append(sr);ew.append(br);abl.append(float(wo.ret.mean()-drag))
   details.append({"year":int(y),"n":len(top),"net_return":sr,"equal_weight_net":br,"winner_removed_net":abl[-1]})
  ps,pe,pa=perf(strat),perf(ew),perf(abl)
  results[f"top{k}"]={"strategy":ps,"equal_weight":pe,"winner_removed":pa,"active_cagr":ps.get("cagr",0)-pe.get("cagr",0),"annual":details}
 out={"status":"RESEARCH_WINDOW_PORTFOLIO_VALIDATION_NOT_FINAL_OOS","research_window":"2014-2020 annual cohorts; data download hard-stops before 2022","final_holdout_policy":"2022+ untouched by this validator; do not tune against final holdout","survivorship_warning":"SEC PIT fields respect filing dates, but ticker cohort is not certified survivorship-free/delisting-complete. Do not promote to production until historical exits are addressed or sensitivity bounds are acceptable.","costs":costs,"coverage":{"companies":len(cs),"mapped":len(ticks),"priced":len(px),"observations":len(df)},"frozen_score":"35% quality + 35% fundamental growth + 30% 12m momentum; cross-sectional percentile ranks","results":results}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
