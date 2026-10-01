#!/usr/bin/env python3
"""Current frozen inflection screen. Rule discovered 2014-17; no refit on current data."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
E={"m12":-0.05699946030433661,"cfo":-0.04540120817653459,"cfo_acc":-0.021434054818817605,"ni":-0.015507855455789421,"gross":0.014525050023221353,"gross_acc":-0.01364667132800823}
F=list(E)
def S(c,k,d):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=d and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));q={}
 for z in x:q[z["end"]]=float(z["val"])
 return list(q.values())
def g3(c,k,d):
 x=S(c,k,d)
 if len(x)<3:return np.nan,np.nan
 p=lambda a,b:a/b-1 if b else np.nan
 return p(x[-1],x[-2]),p(x[-2],x[-3])
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];ticks=list(mp.values());P={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,period="3y",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>=14:P[t]=s
    except:pass
  except:pass
 R=[];today=pd.Timestamp.utcnow().strftime("%Y-%m-%d")
 for cik,c in d["companies"].items():
  t=mp.get(cik);px=P.get(t)
  if px is None:continue
  rv,r0=g3(c,"revenue",today);op,o0=g3(c,"operating_income",today);gp,g0=g3(c,"gross_profit",today);ni,n0=g3(c,"net_income",today);cf,c0=g3(c,"cfo",today)
  m12=float(px.iloc[-1]/px.iloc[-13]-1)
  R.append(dict(ticker=t,m12=m12,cfo=cf,cfo_acc=cf-c0,ni=ni,gross=gp,gross_acc=gp-g0))
 df=pd.DataFrame(R).replace([np.inf,-np.inf],np.nan)
 for v in F:df[v+"p"]=pd.to_numeric(df[v],errors="coerce").rank(pct=True).fillna(.5)
 df["score"]=sum(np.sign(E[v])*(df[v+"p"]-.5)*abs(E[v]) for v in F)
 df["pct"]=df.score.rank(pct=True)
 cols=["ticker","score","pct"]+F
 out={"status":"CURRENT_FROZEN_INFLECTION_SCREEN","rule":"2014-17 discovery frozen; 2018-21 OOS; current survivor proxy","n":len(df),"top20":df.sort_values("score",ascending=False)[cols].head(20).replace({np.nan:None}).to_dict("records")}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+chr(10));print(json.dumps(out))
if __name__=="__main__":main()
