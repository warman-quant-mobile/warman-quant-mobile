#!/usr/bin/env python3
"""Fixed-family asymmetric research; no parameter optimizer and no orders."""
import argparse,json
from pathlib import Path
import pandas as pd
from opportunistic_research import evaluate
from nordnet_kf_gate import promotion_gate

def load(folder,m,name):
    d=pd.read_csv(Path(folder)/m["symbols"][name]["1d"]["file"],parse_dates=["session_date"])
    for k in ("Open","High","Low","Close"): d[k]=pd.to_numeric(d[k],errors="raise")
    return d.sort_values("session_date").drop_duplicates("session_date").reset_index(drop=True)

def stats(obs):
    n=len(obs); split=max(1,int(n*.6)) if n else 0
    def part(xs):
        if not xs:return {"n":0,"mean_r":None,"median_r":None,"hit_10r":0,"p90_mfe":None}
        r=[x["realized_r"] for x in xs]; mf=[x["mfe_r"] for x in xs]
        return {"n":len(xs),"mean_r":round(sum(r)/len(r),3),"median_r":round(float(pd.Series(r).median()),3),
          "hit_10r":sum(x["mfe_r"]>=10 for x in xs),"p90_mfe":round(float(pd.Series(mf).quantile(.9)),3)}
    tr,oo=part(obs[:split]),part(obs[split:])
    return {"events":n,"sample_qualified":n>=30,"train":tr,"oos":oo,
      "oos_positive":oo["n"]>=10 and oo["mean_r"] is not None and oo["mean_r"]>0 and oo["median_r"]>=0,"all":part(obs)}

def events(df,cond,sidefn,gap=60):
    out=[];i=252
    while i<len(df)-60:
        if bool(cond.iloc[i-1]):
            r=evaluate(df,sidefn(i-1),i)
            if r:out.append(r);i+=gap;continue
        i+=1
    return stats(out)
