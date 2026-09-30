#!/usr/bin/env python3
"""Fixed-family asymmetric research; no parameter optimizer and no orders."""
import argparse,json
from pathlib import Path
import pandas as pd
from opportunistic_research import evaluate

TARGETS=(5,10,15,20)

def evaluate_target(df,side,i,target_r,horizon=60,atr_mult=2.0,friction_bps=20):
    """Same frozen entry/stop model as evaluate(), with a fixed R target."""
    import math
    prev=df.iloc[:i]; close=prev.Close.astype(float); high=prev.High.astype(float); low=prev.Low.astype(float)
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    atr=float(tr.tail(20).mean())
    if not math.isfinite(atr) or atr<=0 or i+horizon>=len(df): return None
    price=float(df.iloc[i].Open); risk=atr_mult*atr+price*friction_bps/10000
    if not math.isfinite(price) or price<=0 or (side=="SHORT" and price-target_r*risk<=0): return None
    stop=price-atr_mult*atr if side=="LONG" else price+atr_mult*atr
    target=price+target_r*risk if side=="LONG" else price-target_r*risk; sign=1 if side=="LONG" else -1
    pnl=None; outcome="TIMEOUT"
    for j in range(i,min(i+horizon,len(df))):
        b=df.iloc[j]; o,h,l=map(float,(b.Open,b.High,b.Low))
        stopped=(l<=stop if sign==1 else h>=stop); won=(h>=target if sign==1 else l<=target)
        if stopped:
            fill=min(o,stop) if sign==1 else max(o,stop); pnl=(fill-price)*sign-price*friction_bps/10000; outcome="STOP"; break
        if won:
            pnl=(target-price)*sign-price*friction_bps/10000; outcome="TARGET"; break
    if pnl is None: pnl=(float(df.iloc[min(i+horizon-1,len(df)-1)].Close)-price)*sign-price*friction_bps/10000
    return {"outcome":outcome,"realized_r":round(pnl/risk,3)}
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
          "p90_mfe":round(float(pd.Series(mf).quantile(.9)),3),"max_mfe":round(float(max(mf)),3),
          "fixed_target_ev":{str(t):{"mean_r":round(float(pd.Series([x["target_exits"][str(t)]["realized_r"] for x in xs if x["target_exits"][str(t)] is not None]).mean()),3) if any(x["target_exits"][str(t)] is not None for x in xs) else None,"wins":sum(x["target_exits"][str(t)] is not None and x["target_exits"][str(t)]["outcome"]=="TARGET" for x in xs)} for t in TARGETS}}
    tr,oo=part(obs[:split]),part(obs[split:])
    return {"events":n,"sample_qualified":n>=30,"train":tr,"oos":oo,
      "oos_positive":oo["n"]>=10 and oo["mean_r"] is not None and oo["mean_r"]>0 and oo["median_r"]>=0,"all":part(obs)}

def events(df,cond,sidefn,gap=60):
    out=[];i=252
    while i<len(df)-60:
        if bool(cond.iloc[i-1]):
            r=evaluate(df,sidefn(i-1),i)
            if r:
                r["target_exits"]={str(t):evaluate_target(df,sidefn(i-1),i,t) for t in TARGETS}
                out.append(r);i+=gap;continue
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
