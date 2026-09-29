#!/usr/bin/env python3
"""Research-only extreme price event detector; not a trading signal."""
import argparse,json,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pandas as pd

def classify(df, gap_threshold=.03, daily_threshold=.05, atr_threshold=2.5):
    if len(df)<45:return []
    p=df.iloc[-2]; b=df.iloc[-1]
    o,h,l,c,pc=map(float,(b.Open,b.High,b.Low,b.Close,p.Close))
    if not all(map(math.isfinite,(o,h,l,c,pc))) or min(o,l,pc)<=0 or not l<=min(o,c)<=max(o,c)<=h:return []
    close=df.Close.astype(float);high=df.High.astype(float);low=df.Low.astype(float)
    tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
    atr=float(tr.iloc[-21:-1].mean())
    if not math.isfinite(atr) or atr<=0:return []
    gap=o/pc-1;move=c/pc-1;range_atr=(h-l)/atr
    events=[]
    if abs(gap)>=gap_threshold:
        direction="UP" if gap>0 else "DOWN"
        # A gap is not necessarily news/earnings; attribution requires a timestamped external source.
        events.append(dict(type="GAP",direction=direction,magnitude_pct=round(gap*100,2),
            subtype="GAP_FADE_WATCH" if (c-o)*gap<0 else "GAP_CONTINUATION_WATCH",
            note="Requires independently verified catalyst and actual bid/ask; never infer earnings from price."))
    if abs(move)>=daily_threshold:
        events.append(dict(type="EXTREME_DAILY_RETURN",direction="UP" if move>0 else "DOWN",
            magnitude_pct=round(move*100,2),note="Magnitude alone is not an entry signal."))
    if range_atr>=atr_threshold:
        events.append(dict(type="EXTREME_RANGE",range_atr=round(range_atr,2),
            close_location=round((c-l)/(h-l),3) if h>l else None,
            note="Possible exhaustion or acceleration; requires follow-through confirmation."))
    return events

def scan(folder,now=None):
    folder=Path(folder);now=now or datetime.now(timezone.utc)
    m=json.loads((folder/"manifest.json").read_text());q=json.loads((folder/"quality.json").read_text())
    if m.get("generated_at_utc")!=q.get("generated_at_utc"):raise ValueError("MISMATCHED_EXPORT")
    created=datetime.fromisoformat(m["generated_at_utc"].replace("Z","+00:00"))
    if created>now+timedelta(minutes=5) or now-created>timedelta(hours=8):raise ValueError("STALE_EXPORT")
    if len(q.get("eligible_symbols",[]))<18:raise ValueError("INSUFFICIENT_COVERAGE")
    found={};rejected={}
    for sym in q["eligible_symbols"]:
        try:
            df=pd.read_csv(folder/m["symbols"][sym]["1d"]["file"],parse_dates=["session_date"])
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date")
            if len(df)<45 or df.session_date.duplicated().any() or (now.date()-df.iloc[-1].session_date.date()).days>4:
                raise ValueError("invalid completed daily history")
            events=classify(df)
            if events:found[sym]=dict(session_date=str(df.iloc[-1].session_date.date()),events=events)
        except Exception as exc:rejected[sym]=str(exc)
    return dict(schema_version=1,generated_at_utc=now.isoformat(),status="RESEARCH_ONLY",
        parameters=dict(gap_abs_pct=3,daily_return_abs_pct=5,daily_range_atr=2.5),
        observations=found,rejected=rejected,
        warning="Research diagnostics only; no 10R qualification, product check, or order. Market-specific gap thresholds require out-of-sample validation.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/extreme_events.json")
    a=p.parse_args();r=scan(a.folder);dest=Path(a.result);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("EXTREME_EVENT_RESEARCH",len(r["observations"]),"instruments")
