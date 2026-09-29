#!/usr/bin/env python3
"""Crash-reversal diagnostics; research-only, never executable orders."""
import argparse,json,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pandas as pd

def detect(df):
    """Use only completed daily bars, no forward-looking observations."""
    if len(df)<260:return None
    c=df.Close.astype(float);h=df.High.astype(float);l=df.Low.astype(float)
    if not all(math.isfinite(float(v)) for v in (c.iloc[-1],h.iloc[-1],l.iloc[-1])):return None
    peak=float(c.iloc[-253:].cummax().iloc[-1])
    drawdown=float(c.iloc[-1])/peak-1 if peak>0 else 0
    prev20low=float(l.iloc[-21:-1].min())
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr=float(tr.tail(20).mean())
    if not math.isfinite(atr) or atr<=0:return None
    # Crash must precede reversal; no buying a falling knife merely on drawdown.
    crash=drawdown<=-0.20
    reclaim=(float(l.iloc[-1])<prev20low and float(c.iloc[-1])>prev20low
             and float(c.iloc[-1])>float(df.Open.iloc[-1]))
    if not crash:return None
    price=float(c.iloc[-1]); stop=float(l.iloc[-1])-0.5*atr
    risk=price-stop
    if risk<=0 or stop<=0:return None
    # Recovery to former peak is an illustrative scenario, not a price target forecast.
    reference_r=(peak-price-price*0.002)/(risk+price*0.002)
    return dict(stage="REVERSAL_WATCH" if reclaim else "CRASH_ONLY_NO_ENTRY",
        drawdown_pct=round(drawdown*100,2),reclaim=bool(reclaim),
        proxy_close=round(price,6),invalidation_reference=round(stop,6),
        former_peak_reference=round(peak,6),recovery_reference_r_after_proxy_cost=round(reference_r,2),
        note="Historical peak is NOT a forecast; require independent thesis, confirmation and actual product checks.")

def scan(folder,now=None):
    folder=Path(folder);now=now or datetime.now(timezone.utc)
    m=json.loads((folder/"manifest.json").read_text());q=json.loads((folder/"quality.json").read_text())
    if q.get("generated_at_utc")!=m.get("generated_at_utc"):raise ValueError("MISMATCHED_EXPORT")
    created=datetime.fromisoformat(m["generated_at_utc"].replace("Z","+00:00"))
    if created>now+timedelta(minutes=5) or now-created>timedelta(hours=8):raise ValueError("STALE_EXPORT")
    if len(q.get("eligible_symbols",[]))<18:raise ValueError("INSUFFICIENT_COVERAGE")
    results={};rejected={}
    for sym in q["eligible_symbols"]:
        try:
            df=pd.read_csv(folder/m["symbols"][sym]["1d"]["file"],parse_dates=["session_date"])
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date")
            if df.session_date.duplicated().any():raise ValueError("duplicate sessions")
            if len(df)<260 or (now.date()-df.iloc[-1].session_date.date()).days>4:raise ValueError("stale/short history")
            result=detect(df)
            if result:results[sym]=result
        except Exception as exc:rejected[sym]=str(exc)
    return dict(schema_version=1,generated_at_utc=now.isoformat(),status="RESEARCH_ONLY",
        crash_threshold_pct=-20,results=results,rejected=rejected,
        warning="No executable signals. Reclaim is only a research condition. Crash regime, peak recovery and 10R must be independently validated.")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/contrarian_lab.json")
    a=p.parse_args();r=scan(a.folder);dest=Path(a.result);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("CONTRARIAN_RESEARCH",len(r["results"]),"crash observations")
