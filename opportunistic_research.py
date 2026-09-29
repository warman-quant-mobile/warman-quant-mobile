#!/usr/bin/env python3
"""Exploratory event study, not a validated strategy or execution backtest.

Only completed sessions; signal at close, hypothetical entry next session open.
Same-bar target/stop collision counts as stop; stop gaps fill at worse open.
Fixed 60-session horizon and non-overlapping observations per symbol/side.
"""
import argparse, json, math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

def evaluate(df, side, i, horizon=60, atr_mult=2.0, friction_bps=20):
    row=df.iloc[i]
    prev=df.iloc[:i]
    close=prev.Close.astype(float)
    high=prev.High.astype(float); low=prev.Low.astype(float)
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    atr=float(tr.tail(20).mean())
    if not math.isfinite(atr) or atr<=0 or i+horizon>=len(df): return None
    price=float(row.Open)
    if not math.isfinite(price) or price<=0: return None
    risk=atr_mult*atr+price*friction_bps/10000
    if side=="SHORT" and price-10*risk<=0: return None  # impossible negative price target
    stop=price-atr_mult*atr if side=="LONG" else price+atr_mult*atr
    target=price+10*risk if side=="LONG" else price-10*risk
    sign=1 if side=="LONG" else -1
    outcome="TIMEOUT"; pnl=None; mfe=0.; mae=0.
    for j in range(i,min(i+horizon,len(df))):
        bar=df.iloc[j]
        o,h,l=map(float,(bar.Open,bar.High,bar.Low))
        if not all(map(math.isfinite,(o,h,l))) or l<=0 or not(l<=o<=h): return None
        mfe=max(mfe,sign*(h-price) if sign==1 else price-l)
        mae=max(mae,price-l if sign==1 else h-price)
        # Gaps and ambiguous intrabar sequence resolved against the strategy.
        stopped=(l<=stop if sign==1 else h>=stop)
        won=(h>=target if sign==1 else l<=target)
        if stopped:
            fill=min(o,stop) if sign==1 else max(o,stop)
            pnl=(fill-price)*sign-price*friction_bps/10000
            outcome="STOP";break
        if won:
            fill=target
            pnl=(fill-price)*sign-price*friction_bps/10000
            outcome="TARGET";break
    if pnl is None:
        pnl=(float(df.iloc[min(i+horizon-1,len(df)-1)].Close)-price)*sign-price*friction_bps/10000
    return dict(outcome=outcome,realized_r=round(pnl/risk,3),
                mfe_r=round(mfe/risk,3),mae_r=round(mae/risk,3))

def study(folder, now=None):
    folder=Path(folder);now=now or datetime.now(timezone.utc)
    manifest=json.loads((folder/"manifest.json").read_text())
    quality=json.loads((folder/"quality.json").read_text())
    if quality.get("generated_at_utc")!=manifest.get("generated_at_utc"):
        raise ValueError("MISMATCHED_EXPORT")
    created=datetime.fromisoformat(manifest["generated_at_utc"].replace("Z","+00:00"))
    if now-created>timedelta(hours=8) or created>now+timedelta(minutes=5):
        raise ValueError("STALE_EXPORT")
    if len(quality.get("eligible_symbols",[]))<18: raise ValueError("INSUFFICIENT_COVERAGE")
    summary={};errors={}
    for symbol in quality["eligible_symbols"]:
        try:
            meta=manifest["symbols"][symbol]["1d"]
            df=pd.read_csv(folder/meta["file"],parse_dates=["session_date"])
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date").reset_index(drop=True)
            if df.session_date.duplicated().any() or len(df)<400: raise ValueError("insufficient clean history")
            if (now.date()-df.iloc[-1].session_date.date()).days>4: raise ValueError("stale daily history")
            by_side={}
            for side in ("LONG","SHORT"):
                observations=[]; i=251
                while i<len(df)-60:
                    history=df.iloc[:i]
                    c=history.Close.astype(float); h=history.High.astype(float); l=history.Low.astype(float)
                    ma50=float(c.tail(50).mean());ma200=float(c.tail(200).mean())
                    trigger=(float(c.iloc[-1])>float(h.tail(21).iloc[:-1].max()) and c.iloc[-1]>ma50>ma200) if side=="LONG" else (float(c.iloc[-1])<float(l.tail(21).iloc[:-1].min()) and c.iloc[-1]<ma50<ma200)
                    # Signal is generated at the prior close, next open is hypothetical entry.
                    if trigger:
                        result=evaluate(df,side,i)
                        if result:
                            observations.append(result);i+=60;continue
                    i+=1
                n=len(observations)
                by_side[side]=dict(events=n,targets=sum(x["outcome"]=="TARGET" for x in observations),
                    stops=sum(x["outcome"]=="STOP" for x in observations),
                    timeouts=sum(x["outcome"]=="TIMEOUT" for x in observations),
                    mean_realized_r=round(sum(x["realized_r"] for x in observations)/n,3) if n else None,
                    maximum_favorable_excursion_r=max((x["mfe_r"] for x in observations),default=None),
                    note="Exploratory overlapping-market selection bias; not independently validated.")
            summary[symbol]=by_side
        except Exception as exc:errors[symbol]=str(exc)
    return dict(schema_version=1,generated_at_utc=now.isoformat(),status="RESEARCH_ONLY",
        methodology="251-session warmup; prior-close 20-day breakout plus MA50/MA200; next open; ATR20 x2; 10R gross-risk target; 20bps roundtrip friction; 60 sessions; stop first if same bar; worse gap fill; disjoint 60-session windows per side.",
        results=summary,excluded=errors,warning="Exploratory event study, not an unbiased out-of-sample test, expected return forecast, Nordnet product simulation or executable order.")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/research_lab.json")
    args=p.parse_args();result=study(args.folder);dest=Path(args.result);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("RESEARCH_ONLY",len(result["results"]),"instruments",len(result["excluded"]),"excluded")
