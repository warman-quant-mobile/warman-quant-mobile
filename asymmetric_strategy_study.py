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
        if not xs:return {"n":0,"mean_r":None,"median_r":None,"hit_5r":0,"hit_10r":0,"hit_15r":0,"hit_20r":0,"p50_mfe":None,"p75_mfe":None,"p90_mfe":None,"max_mfe":None}
        r=[x["realized_r"] for x in xs]; mf=[x["mfe_r"] for x in xs]
        return {"n":len(xs),"mean_r":round(sum(r)/len(r),3),"median_r":round(float(pd.Series(r).median()),3),
          "hit_5r":sum(x["mfe_r"]>=5 for x in xs),"hit_10r":sum(x["mfe_r"]>=10 for x in xs),
          "hit_15r":sum(x["mfe_r"]>=15 for x in xs),"hit_20r":sum(x["mfe_r"]>=20 for x in xs),
          "p50_mfe":round(float(pd.Series(mf).quantile(.5)),3),"p75_mfe":round(float(pd.Series(mf).quantile(.75)),3),
          "p90_mfe":round(float(pd.Series(mf).quantile(.9)),3),"max_mfe":round(float(max(mf)),3)}
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
        atrpct=atr.rolling(252).rank(pct=True);rng=hi-lo
        expansion=(atrpct.shift(1)<=.25)&(rng>=2*atr)&((cl>=lo+.75*rng)|(cl<=lo+.25*rng))
        exp_side=lambda i:"LONG" if cl.iloc[i]>=lo.iloc[i]+.75*rng.iloc[i] else "SHORT"
        results[s]={"SHOCK_TREND_CONTINUATION":events(d,shock&trend,trend_side),
                    "FAILED_20D_EXTREME":events(d,fail_hi|fail_lo,fail_side),
                    "CONTRACTION_EXPANSION":events(d,expansion,exp_side)}
    return {"status":"RESEARCH_ONLY","families":results,"minimum_r":10,
      "design":"Fixed hypotheses; no grid search. 60-session non-overlap, next-session open, 2ATR stop, 20bps friction, 10R target, chronological 60/40 split.",
      "promotion_rule":"Require >=30 non-overlapping events, >=10 OOS events, positive OOS mean and non-negative OOS median, then Nordnet-KF product/quote verification and recomputed net R >=10."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/asymmetric_strategy_study.json")
    a=p.parse_args();r=study(a.folder);o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(r,indent=2)+"\n");print(r["status"],len(r["families"]))
