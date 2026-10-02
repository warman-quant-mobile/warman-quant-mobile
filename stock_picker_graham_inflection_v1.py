#!/usr/bin/env python3
"""Frozen Graham -> Inflection hybrid research control. NEVER reads 2022+."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
E={"m12":-0.05703464962796956,"cfo":-0.04539953236387423,"cfo_acc":-0.021440458793486827,"ni":-0.015539326373346707,"gross":0.01453170106730639,"gross_acc":-0.013643605731961328}
FEATS=list(E)
def ann(c,k,asof):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.items())
def l1(c,k,d):x=ann(c,k,d);return x[-1][1] if x else None
def l2(c,k,d):x=ann(c,k,d);return (x[-1][1],x[-2][1]) if len(x)>1 else (None,None)
def pct(a,b):return a/b-1 if a is not None and b not in (None,0) else np.nan
def perf(rs):
 if not rs:return {}
 w=np.cumprod(1+np.array(rs));n=len(rs)
 return {"years":n,"cumulative":float(w[-1]-1),"cagr":float(w[-1]**(1/n)-1),"max_drawdown":float(np.min(w/np.maximum.accumulate(w)-1))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2011-01-01",end="2022-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>30:px[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);p=px.get(t)
  if p is None:continue
  for y in range(2018,2021):
   dt=f"{y}-06-30";h=p.loc[:dt];f=p.loc[dt:f"{y+1}-06-30"]
   if len(h)<25 or len(f)<10:continue
   ni,n0=l2(c,"net_income",dt);eq=l1(c,"equity",dt);sh=l1(c,"shares",dt);debt=l1(c,"debt",dt)
   cfo,c0=l2(c,"cfo",dt);gp,g0=l2(c,"gross_profit",dt)
   if ni is None or eq is None or sh in (None,0) or ni<=0 or eq<=0:continue
   price=float(h.iloc[-1]);eps=ni/sh;bvps=eq/sh
   if eps<=0 or bvps<=0:continue
   pe=price/eps;pb=price/bvps
   if not(pe<=15 and pb<=1.5 and pe*pb<=22.5):continue
   vals={"m12":price/float(h.iloc[-13])-1,"cfo":cfo,"cfo_acc":(cfo-c0 if cfo is not None and c0 is not None else np.nan),"ni":ni,"gross":gp,"gross_acc":(gp-g0 if gp is not None and g0 is not None else np.nan)}
   rows.append({"ticker":t,"year":y,"ret":float(f.iloc[-1]/price-1),**vals})
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 # Frozen direction only; percentile ranks within each year's Graham-qualified set.
 for y,ix in df.groupby("year").groups.items():
  g=df.loc[ix];score=pd.Series(0.,index=ix)
  for z in FEATS:
   r=g[z].rank(pct=True).fillna(.5); score += (r if E[z]>0 else 1-r).values
  df.loc[ix,"score"]=(score/len(FEATS)).values
 drag=.005;out={"status":"FROZEN_GRAHAM_TO_INFLECTION_RESEARCH_ONLY","window":"2018-2020 OOS relative to inflection discovery; 2022+ never read","rules":"Graham core PE<=15, PB<=1.5, product<=22.5 then frozen corrected inflection directions","cost_drag":drag,"results":{}}
 for k in [5,10,20]:
  hy=[];gr=[];wr=[];annual=[]
  for y,g in df.groupby("year"):
   top=g.nlargest(min(k,len(g)),"score");sr=float(top.ret.mean()-drag);br=float(g.ret.mean()-drag);x=top.drop(top.ret.idxmax()) if len(top)>1 else top;wor=float(x.ret.mean()-drag)
   hy.append(sr);gr.append(br);wr.append(wor);annual.append({"year":int(y),"graham_n":len(g),"n":len(top),"hybrid_net":sr,"graham_net":br,"winner_removed_net":wor,"best_ticker":str(top.loc[top.ret.idxmax(),"ticker"]),"best_return":float(top.ret.max()),"selected":[{"ticker":str(r.ticker),"score":float(r.score),"ret":float(r.ret)} for _,r in top.iterrows()]})
  ph,pg,pw=perf(hy),perf(gr),perf(wr);out["results"][f"top{k}"]={"hybrid":ph,"graham":pg,"winner_removed":pw,"active_vs_graham":ph["cagr"]-pg["cagr"],"winner_removed_active":pw["cagr"]-pg["cagr"],"annual":annual}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
