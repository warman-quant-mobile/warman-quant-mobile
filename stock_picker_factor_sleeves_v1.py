#!/usr/bin/env python3
"""Research-window factor sleeve audit. Never reads 2022+.
Tests frozen economic families independently and equal-weight composites.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
def ann(c,k,asof):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.items())
def l1(c,k,d):
 x=ann(c,k,d);return x[-1][1] if x else None
def l2(c,k,d):
 x=ann(c,k,d);return (x[-1][1],x[-2][1]) if len(x)>1 else (None,None)
def pct(a,b):return a/b-1 if a is not None and b not in (None,0) else np.nan
def rank(s):return s.rank(pct=True)
def perf(rs):
 w=np.cumprod(1+np.array(rs));n=len(rs)
 return {"cagr":float(w[-1]**(1/n)-1),"cumulative":float(w[-1]-1)} if n else {}
def main():
 p=argparse.ArgumentParser();p.add_argument("--pit",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2012-01-01",end="2022-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>24:px[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);pr=px.get(t)
  if pr is None:continue
  for y in range(2014,2021):
   dt=f"{y}-06-30";h=pr.loc[:dt];f=pr.loc[dt:f"{y+1}-06-30"]
   if len(h)<13 or len(f)<10:continue
   rev,r0=l2(c,"revenue",dt);op,o0=l2(c,"operating_income",dt);gp,g0=l2(c,"gross_profit",dt);ni=l1(c,"net_income",dt);ass=l1(c,"assets",dt);cfo=l1(c,"cfo",dt);cap=l1(c,"capex",dt);debt=l1(c,"debt",dt);sh,s0=l2(c,"shares",dt)
   if rev is None or ass in (None,0):continue
   rows.append({"ticker":t,"year":y,"ret":float(f.iloc[-1]/h.iloc[-1]-1),"rg":pct(rev,r0),"og":pct(op,o0),"gg":pct(gp,g0),"roa":ni/ass if ni is not None else np.nan,"fcfm":((cfo-cap)/rev if cfo is not None and cap is not None and rev else np.nan),"lev":debt/ass if debt is not None else np.nan,"dil":pct(sh,s0),"mom":float(h.iloc[-1]/h.iloc[-13]-1)})
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 for y,ix in df.groupby("year").groups.items():
  g=df.loc[ix];q=(rank(g.roa).fillna(.5)+rank(g.fcfm).fillna(.5)+rank(-g.lev).fillna(.5)+rank(-g.dil).fillna(.5))/4;gr=(rank(g.rg).fillna(.5)+rank(g.og).fillna(.5)+rank(g.gg).fillna(.5))/3;m=rank(g.mom).fillna(.5)
  df.loc[ix,"quality"]=q.values;df.loc[ix,"growth"]=gr.values;df.loc[ix,"momentum"]=m.values;df.loc[ix,"qgm_equal"]=((q+gr+m)/3).values;df.loc[ix,"qg_equal"]=((q+gr)/2).values
 out={"status":"RESEARCH_ONLY_FACTOR_SLEEVE_AUDIT","window":"2014-2020","warning":"Current-survivor universe; never use this as delisting-complete evidence.","results":{}}
 for fac in ["quality","growth","momentum","qg_equal","qgm_equal"]:
  out["results"][fac]={}
  for k in [10,20,40]:
   s=[];b=[];wo=[]
   for y,g in df.groupby("year"):
    top=g.nlargest(min(k,len(g)),fac);s.append(float(top.ret.mean()-.005));b.append(float(g.ret.mean()-.005));x=top.drop(top.ret.idxmax()) if len(top)>1 else top;wo.append(float(x.ret.mean()-.005))
   ps,pb,pw=perf(s),perf(b),perf(wo);out["results"][fac][f"top{k}"]={"cagr":ps["cagr"],"active_cagr":ps["cagr"]-pb["cagr"],"winner_removed_cagr":pw["cagr"],"winner_removed_active":pw["cagr"]-pb["cagr"]}
 Path(a.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
