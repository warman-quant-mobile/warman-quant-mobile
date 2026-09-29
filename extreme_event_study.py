"""Exploratory 10R outcomes following extreme events; never executable orders."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pandas as pd
from extreme_event_research import classify
from opportunistic_research import evaluate

STRATEGIES=("GAP_CONTINUATION","GAP_FADE","SHOCK_CONTINUATION","SHOCK_FADE","RANGE_CONTINUATION")

def direction(events,strategy):
    for e in events:
        kind=e["type"]
        if kind=="GAP" and strategy.startswith("GAP_"):
            up=e["direction"]=="UP"
            return ("LONG" if up else "SHORT") if strategy=="GAP_CONTINUATION" else ("SHORT" if up else "LONG")
        if kind=="EXTREME_DAILY_RETURN" and strategy.startswith("SHOCK_"):
            up=e["direction"]=="UP"
            return ("LONG" if up else "SHORT") if strategy=="SHOCK_CONTINUATION" else ("SHORT" if up else "LONG")
        if kind=="EXTREME_RANGE" and strategy=="RANGE_CONTINUATION":
            loc=e["close_location"]
            if loc is not None and loc>=.8:return "LONG"
            if loc is not None and loc<=.2:return "SHORT"
    return None

def study(folder,now=None):
    folder=Path(folder);now=now or datetime.now(timezone.utc)
    m=json.loads((folder/"manifest.json").read_text());q=json.loads((folder/"quality.json").read_text())
    if m.get("generated_at_utc")!=q.get("generated_at_utc"):raise ValueError("MISMATCHED_EXPORT")
    t=datetime.fromisoformat(m["generated_at_utc"].replace("Z","+00:00"))
    if t>now+timedelta(minutes=5) or now-t>timedelta(hours=8):raise ValueError("STALE_EXPORT")
    if len(q.get("eligible_symbols",[]))<18:raise ValueError("INSUFFICIENT_COVERAGE")
    results={};rejected={}
    for sym in q["eligible_symbols"]:
        try:
            df=pd.read_csv(folder/m["symbols"][sym]["1d"]["file"],parse_dates=["session_date"])
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date").reset_index(drop=True)
            if len(df)<400 or df.session_date.duplicated().any():raise ValueError("short/duplicate history")
            if (now.date()-df.iloc[-1].session_date.date()).days>4:raise ValueError("stale bars")
            summary={}
            for strategy in STRATEGIES:
                trades=[];i=251
                while i<len(df)-60:
                    side=direction(classify(df.iloc[:i]),strategy)
                    if side:
                        result=evaluate(df,side,i)
                        if result:
                            trades.append(result);i+=60;continue
                    i+=1
                n=len(trades)
                summary[strategy]=dict(events=n,targets_10r=sum(t["outcome"]=="TARGET" for t in trades),
                    stops=sum(t["outcome"]=="STOP" for t in trades),
                    timeouts=sum(t["outcome"]=="TIMEOUT" for t in trades),
                    mean_realized_r=round(sum(t["realized_r"] for t in trades)/n,3) if n else None,
                    insufficient_sample=n<30)
            results[sym]=summary
        except Exception as exc:rejected[sym]=str(exc)
    return dict(schema_version=1,generated_at_utc=now.isoformat(),status="EXPLORATORY_NOT_VALIDATED",
        methodology="Prior completed bar; next open; 2ATR stop; 10R target; 20bps proxy friction; 60 sessions; conservative gaps; nonoverlapping events per strategy.",
        results=results,rejected=rejected,warning="In-sample research only. Not a validated edge or Nordnet product simulation.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/extreme_event_study.json")
    a=p.parse_args();r=study(a.folder);dest=Path(a.result);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,indent=2)+"\n")
    print("EXTREME_STUDY",len(r["results"]),"instruments",len(r["rejected"]),"excluded")
