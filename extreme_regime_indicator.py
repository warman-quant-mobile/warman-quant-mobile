#!/usr/bin/env python3
"""Fat-tail / extreme-regime detector. Research warning system, never an order signal.

Design principle: do not estimate a precise Black-Swan probability. Detect observable
fragility, tail realization and cross-asset stress using robust ranks and fixed thresholds.
"""
import argparse,json,math
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd

CORE=("SP500","NASDAQ100","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","US30Y_BOND_FUT","EURUSD","USDSEK","BITCOIN")
SENSORS=("VIX","OVX","GVZ","US30Y_YIELD","US10Y_YIELD")

def load(folder,m,sym,now):
    p=Path(folder)/m["symbols"][sym]["1d"]["file"]
    d=pd.read_csv(p,parse_dates=["session_date"]).sort_values("session_date")
    d=d[d.session_date.dt.date<now.date()].copy()
    for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="raise")
    return d.reset_index(drop=True)

def metrics(d):
    c=d.Close.astype(float); r=c.pct_change()
    tr=pd.concat([d.High-d.Low,(d.High-c.shift()).abs(),(d.Low-c.shift()).abs()],axis=1).max(axis=1)
    atr20=tr.rolling(20).mean(); rv20=r.rolling(20).std()
    last=r.iloc[-1]; gap=d.Open.iloc[-1]/c.iloc[-2]-1
    hist_abs=r.abs().iloc[:-1].tail(1250); hist_rv=rv20.iloc[:-1].tail(1250)
    tail_rank=float((hist_abs<=abs(last)).mean()) if len(hist_abs)>=250 else None
    rv_rank=float((hist_rv<=rv20.iloc[-1]).mean()) if len(hist_rv.dropna())>=250 else None
    compression=float((hist_rv<=rv20.iloc[-2]).mean()) if len(hist_rv.dropna())>=250 else None
    atr_move=abs(c.iloc[-1]-c.iloc[-2])/atr20.iloc[-2] if atr20.iloc[-2]>0 else None
    dd20=c.iloc[-1]/c.iloc[-21:-1].max()-1 if len(c)>=21 else None
    return dict(ret1=float(last),gap=float(gap),tail_rank=tail_rank,rv_rank=rv_rank,
                prior_rv_rank=compression,atr_move=float(atr_move),dd20=float(dd20))

def scan(folder,now=None):
    folder=Path(folder); now=now or datetime.now(timezone.utc)
    m=json.loads((folder/"manifest.json").read_text()); rows={}; tags=[]; score=0
    available=[s for s in CORE+SENSORS if s in m.get("symbols",{}) and "1d" in m["symbols"][s]]
    for s in available:
        d=load(folder,m,s,now)
        if len(d)<300: continue
        x=metrics(d); rows[s]={k:(round(v,5) if isinstance(v,float) and math.isfinite(v) else v) for k,v in x.items()}
        local=[]
        if x["tail_rank"] is not None and x["tail_rank"]>=.995: local.append("TAIL_99_5PCT"); score+=2
        elif x["tail_rank"] is not None and x["tail_rank"]>=.99: local.append("TAIL_99PCT"); score+=1
        if abs(x["gap"])>=.03: local.append("GAP_3PCT"); score+=2
        if x["atr_move"] is not None and x["atr_move"]>=3: local.append("MOVE_3ATR"); score+=2
        if x["rv_rank"] is not None and x["rv_rank"]>=.95: local.append("VOL_TOP_5PCT"); score+=1
        if x["prior_rv_rank"] is not None and x["prior_rv_rank"]<=.20 and x["rv_rank"] is not None and x["rv_rank"]>=.70:
            local.append("CALM_TO_EXPANSION"); score+=2
        if s in ("SP500","NASDAQ100") and x["dd20"]<=-.08: local.append("INDEX_DRAWDOWN_8PCT"); score+=2
        if local: tags.append({"symbol":s,"tags":local})
    # Cross-asset stress: count independent core markets currently in their 99th percentile absolute daily move.
    n_tail=sum(1 for s in CORE if s in rows and rows[s].get("tail_rank") is not None and rows[s]["tail_rank"]>=.99)
    if n_tail>=3: tags.append({"symbol":"CROSS_ASSET","tags":["MULTI_ASSET_TAIL_CLUSTER"]}); score+=3
    vix=rows.get("VIX")
    if vix and vix.get("tail_rank") is not None and vix["tail_rank"]>=.99:
        tags.append({"symbol":"VIX","tags":["VOLATILITY_TAIL_SHOCK"]}); score+=2
    level="EXTREME" if score>=8 or n_tail>=4 else "ELEVATED" if score>=4 else "WATCH" if score>=1 else "NORMAL"
    return {"status":"RESEARCH_WARNING_ONLY","generated_at_utc":now.isoformat(),"level":level,
            "stress_score":score,"cross_asset_tail_count":n_tail,"events":tags,"metrics":rows,
            "interpretation":"Fragility/tail-state indicator, not a crash forecast and never an automatic trade.",
            "method":"Fixed robust empirical ranks + ATR/gap/drawdown thresholds; no Gaussian sigma probability assumptions."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/extreme_regime.json")
    a=p.parse_args();r=scan(a.folder);o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(r,indent=2)+"\n");print("EXTREME_REGIME",r["level"],r["stress_score"])
