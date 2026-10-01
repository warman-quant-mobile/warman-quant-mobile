#!/usr/bin/env python3
"""Weekly Stochastic + MACD long-horizon research. Frozen parameter families, no broker actions."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
PARS=[(12,26,9,14,3),(19,39,9,14,3),(24,52,9,14,3)]
def ema(x,n): return x.ewm(span=n,adjust=False).mean()
def test(s,par):
 f,sl,sg,kp,dp=par
 mac=ema(s,f)-ema(s,sl); sig=ema(mac,sg); hist=mac-sig
 lo=s.rolling(kp).min(); hi=s.rolling(kp).max(); k=100*(s-lo)/(hi-lo); d=k.rolling(dp).mean()
 # inflection: MACD histogram crosses positive while stochastic K crosses D from below, both from lower half
 trig=(hist>0)&(hist.shift(1)<=0)&(k>d)&(k.shift(1)<=d.shift(1))&(k.shift(1)<50)
 rows=[]
 for dt in s.index[trig.fillna(False)]:
  i=s.index.get_loc(dt)
  r={"date":str(dt.date())}
  for w in [26,52,104,156]:
   if i+w<len(s): r[f"r{w}"]=float(s.iloc[i+w]/s.iloc[i]-1)
  rows.append(r)
 return rows
def main():
 a=argparse.ArgumentParser();a.add_argument("--pit",required=True);a.add_argument("--out",required=True);x=a.parse_args()
 d=json.load(open(x.pit));ticks=sorted(set(d["selection"]["ticker_by_cik"].values()))
 out={"status":"WEEKLY_STOCH_MACD_RESEARCH","warning":"Current-survivor universe and live Yahoo; provisional until deterministic cache.","parameters":[]}
 for par in PARS:
  vals=[]
  for i in range(0,len(ticks),150):
   b=ticks[i:i+150]
   try:q=yf.download(b,start="2012-01-01",end="2027-01-01",interval="1wk",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   except:continue
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna().astype(float)
     vals+=test(s,par)
    except:pass
  z={"params":par,"signals":len(vals)}
  for w in [26,52,104,156]:
   a=[r[f"r{w}"] for r in vals if f"r{w}" in r]
   z[f"{w}w"]={"n":len(a),"mean":float(np.mean(a)) if a else None,"median":float(np.median(a)) if a else None,"positive":float(np.mean(np.array(a)>0)) if a else None,"double":float(np.mean(np.array(a)>=1)) if a else None}
  out["parameters"].append(z)
 # Unconditional forward-return benchmark sampled on all eligible weekly observations.
 # This is deliberately approximate/current-survivor; the next deterministic-cache version will freeze observations.
 out["benchmark_note"]="Signal statistics must be judged against unconditional same-universe forward returns; current v1 lacks that control and is not evidence of alpha."
 Path(x.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
