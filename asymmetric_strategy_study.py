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

def study(folder):
    folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());results={}
    universe=("SP500","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT")
    for s in [x for x in universe if x in m["symbols"] and promotion_gate(x)["eligible"]]:
        d=load(folder,m,s);cl=d.Close.astype(float);hi=d.High.astype(float);lo=d.Low.astype(float)
        tr=pd.concat([hi-lo,(hi-cl.shift()).abs(),(lo-cl.shift()).abs()],axis=1).max(axis=1);atr=tr.rolling(20).mean()
        r20=cl.pct_change(20);r60=cl.pct_change(60)
        shock=(cl-cl.shift(5)).abs()>=3*atr
        trend=((r60>0)&(r20>0))|((r60<0)&(r20<0))
        trend_side=lambda i:"LONG" if r60.iloc[i]>0 else "SHORT"
        ph=hi.shift(1).rolling(20).max();pl=lo.shift(1).rolling(20).min()
        fail_hi=(hi>ph)&(cl<ph);fail_lo=(lo<pl)&(cl>pl)
        fail_side=lambda i:"SHORT" if fail_hi.iloc[i] else "LONG"
        results[s]={"SHOCK_TREND_CONTINUATION":events(d,shock&trend,trend_side),
                    "FAILED_20D_EXTREME":events(d,fail_hi|fail_lo,fail_side)}
    return {"status":"RESEARCH_ONLY","families":results,"minimum_r":10,
      "design":"Fixed hypotheses; no grid search. 60-session non-overlap, next-session open, 2ATR stop, 20bps friction, 10R target, chronological 60/40 split.",
      "promotion_rule":"Require >=30 non-overlapping events, >=10 OOS events, positive OOS mean and non-negative OOS median, then Nordnet-KF product/quote verification and recomputed net R >=10."}
