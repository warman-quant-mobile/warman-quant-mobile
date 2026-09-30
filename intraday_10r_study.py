#!/usr/bin/env python3
"""Research summary for hourly watch events; never an order."""
import argparse,json
from pathlib import Path
import pandas as pd
import math

def evaluate(df,i,side,atr,horizon=48):
    if i+1>=len(df): return None
    entry=float(df.iloc[i+1].Open); friction=entry*.002; risk=2*atr+friction
    sign=1 if side=="LONG" else -1; stop=entry-sign*2*atr; target=entry+sign*10*risk
    if entry<=0 or stop<=0 or target<=0: return None
    outcome="TIMEOUT"; pnl=None; mfe=0.
    for j in range(i+1,min(i+1+horizon,len(df))):
        b=df.iloc[j]; o,h,l=map(float,(b.Open,b.High,b.Low))
        mfe=max(mfe,h-entry if sign==1 else entry-l)
        if (l<=stop if sign==1 else h>=stop):
            fill=min(o,stop) if sign==1 else max(o,stop); pnl=(fill-entry)*sign-friction; outcome="STOP"; break
        if (h>=target if sign==1 else l<=target):
            pnl=(target-entry)*sign-friction; outcome="TARGET"; break
    if pnl is None: pnl=(float(df.iloc[min(i+horizon,len(df)-1)].Close)-entry)*sign-friction
    return {"outcome":outcome,"realized_r":round(pnl/risk,3),"mfe_r":round(mfe/risk,3)}

def study(folder):
    folder=Path(folder)
    manifest=json.loads((folder/"manifest.json").read_text())
    quality=json.loads((folder/"quality.json").read_text())
    results={}
    for symbol in quality.get("eligible_symbols",[]):
        meta=manifest["symbols"][symbol]["1h"]
        df=pd.read_csv(folder/meta["file"])
        for k in ("Open","High","Low","Close"): df[k]=pd.to_numeric(df[k],errors="raise")
        tr=pd.concat([df.High-df.Low,(df.High-df.Close.shift()).abs(),(df.Low-df.Close.shift()).abs()],axis=1).max(axis=1)
        buckets={"FAILED_HIGH_20H":[],"FAILED_LOW_20H":[],"SHOCK_CONT":[],"SHOCK_FADE":[]}
        for i in range(21,len(df)-49):
            atr=float(tr.iloc[i-20:i].mean())
            if not math.isfinite(atr) or atr<=0: continue
            b=df.iloc[i]; p=df.iloc[i-1]; hi=float(df.High.iloc[i-20:i].max()); lo=float(df.Low.iloc[i-20:i].min())
            events=[]
            if float(b.High)>hi and float(b.Close)<hi: events.append(("FAILED_HIGH_20H","SHORT"))
            if float(b.Low)<lo and float(b.Close)>lo: events.append(("FAILED_LOW_20H","LONG"))
            move=float(b.Close-p.Close)
            if abs(move)>=2.5*atr:
                side="LONG" if move>0 else "SHORT"; events.extend([("SHOCK_CONT",side),("SHOCK_FADE","SHORT" if side=="LONG" else "LONG")])
            for kind,side in events:
                x=evaluate(df,i,side,atr)
                if x: buckets[kind].append(x)
        summaries={}
        for kind,xs in buckets.items():
            summaries[kind]={"events":len(xs),"targets_10r":sum(x["outcome"]=="TARGET" for x in xs),
                "stops":sum(x["outcome"]=="STOP" for x in xs),"reached_10r_mfe":sum(x["mfe_r"]>=10 for x in xs),
                "mean_realized_r":round(sum(x["realized_r"] for x in xs)/len(xs),3) if xs else None,
                "max_mfe_r":max((x["mfe_r"] for x in xs),default=None)}
        results[symbol]={"hourly_bars":len(df),"sample_gate_passed":len(df)>=1000,"setups":summaries}
    return {"status":"RESEARCH_ONLY","results":results,
            "promotion_rule":"No hourly setup can be promoted unless sample_gate_passed is true; study metrics remain research-only.",
            "methodology":"Signal on completed hour; hypothetical next-hour open; 2ATR stop; 10R target; 20bps friction; 48-bar horizon; stop wins same-bar ambiguity.",
            "warning":"Short hourly history is observation-only, not evidence of a 10R edge."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/intraday_10r_study.json")
    a=p.parse_args();r=study(a.folder);out=Path(a.result);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2)+"
");print("INTRADAY_SAMPLE_GATE",sum(x["sample_gate_passed"] for x in r["results"].values()))
