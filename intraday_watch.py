#!/usr/bin/env python3
"""Completed hourly bar event watch; observations, never executable orders."""
import argparse,json,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pandas as pd
def scan(folder,now=None):
    folder=Path(folder);now=now or datetime.now(timezone.utc)
    m=json.loads((folder/"manifest.json").read_text());q=json.loads((folder/"quality.json").read_text())
    if m["generated_at_utc"]!=q["generated_at_utc"]:raise ValueError("MISMATCHED_EXPORT")
    created=datetime.fromisoformat(m["generated_at_utc"].replace("Z","+00:00"))
    if created>now+timedelta(minutes=5) or now-created>timedelta(hours=8):raise ValueError("STALE_EXPORT")
    if len(q.get("eligible_symbols",[]))<18:raise ValueError("INSUFFICIENT_COVERAGE")
    observations=[];excluded={}
    # 1h timestamps denote bar START. Exclude current, unfinished UTC hour.
    cutoff=now.replace(minute=0,second=0,microsecond=0)
    for sym in q["eligible_symbols"]:
        try:
            df=pd.read_csv(folder/m["symbols"][sym]["1h"]["file"],parse_dates=["timestamp_utc"])
            df=df[df.timestamp_utc<cutoff].sort_values("timestamp_utc").reset_index(drop=True)
            if len(df)<45 or df.timestamp_utc.duplicated().any():raise ValueError("INVALID_HISTORY")
            if cutoff-df.iloc[-1].timestamp_utc.to_pydatetime()>timedelta(hours=76):raise ValueError("STALE_HOURLY")
            for k in ("Open","High","Low","Close"):df[k]=pd.to_numeric(df[k],errors="raise")
            if not ((df.Low>0)&(df.High>=df[["Open","Low","Close"]].max(axis=1))&(df.Low<=df[["Open","High","Close"]].min(axis=1))).all():raise ValueError("INVALID_OHLC")
            b=df.iloc[-1];p=df.iloc[-2];h=float(df.High.iloc[-21:-1].max());l=float(df.Low.iloc[-21:-1].min())
            gap=float(b.Open/p.Close-1);move=float(b.Close/p.Close-1)
            atr=float(pd.concat([df.High-df.Low,(df.High-df.Close.shift()).abs(),(df.Low-df.Close.shift()).abs()],axis=1).max(axis=1).iloc[-21:-1].mean())
            events=[]
            if abs(gap)>=.03:events.append("GAP_3PCT")
            if atr>0 and abs(float(b.Close-p.Close))>=2.5*atr:events.append("HOURLY_SHOCK_2_5ATR")
            if float(b.High)>h and float(b.Close)<h:events.append("FAILED_HIGH_20H")
            if float(b.Low)<l and float(b.Close)>l:events.append("FAILED_LOW_20H")
            if events:observations.append(dict(symbol=sym,bar_start_utc=b.timestamp_utc.isoformat(),events=events,
                gap_pct=round(gap*100,2),hourly_move_pct=round(move*100,2),status="INTRADAY_WATCH_NOT_ORDER"))
        except Exception as exc:excluded[sym]=str(exc)
    return dict(status="RESEARCH_WATCH_ONLY",generated_at_utc=now.isoformat(),observations=observations,excluded=excluded,
        note="Hourly data may be delayed; market sessions vary. Events require a separate validated 10R target and executable instrument quote before proposal.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/intraday_watch.json")
    a=p.parse_args();r=scan(Path(a.folder));dest=Path(a.result);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,indent=2)+"\n");print("INTRADAY_WATCH",len(r["observations"]),"observations")
