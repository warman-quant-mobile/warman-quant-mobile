#!/usr/bin/env python3
"""Frozen matched-control extension for weekly MTF v2. Research only."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from research_safety import stamp,set_reproducible
from weekly_pattern_study import load,atr,outcome,FRICTION_BPS,DAILY_HORIZON
H=20; LOOK=10
def daily_only(d,label):
    idx=d.index[d.session_date>=pd.Timestamp(label)].tolist()[:LOOK]
    a=atr(d,20)
    for j in idx:
        if j<H+1 or j+1>=len(d): continue
        hi=float(d.High.iloc[j-H:j].max()); lo=float(d.Low.iloc[j-H:j].min()); q=d.iloc[j]
        side="LONG" if float(q.Close)>hi else ("SHORT" if float(q.Close)<lo else None)
        if not side: continue
        av=float(a.iloc[j-1])
        if not math.isfinite(av) or av<=0: continue
        e=j+1; p=float(d.Open.iloc[e]); stop=(float(q.Low)-.5*av if side=="LONG" else float(q.High)+.5*av)
        return outcome(d,e,p,stop,4*av,side,DAILY_HORIZON,p*FRICTION_BPS/10000)
    return None
def reclaim(d,label,boundary,side,height):
    idx=d.index[d.session_date>pd.Timestamp(label)].tolist()[:LOOK]; a=atr(d,20); failed=False; extreme=None
    for j in idx:
        if j<21 or j+1>=len(d):continue
        q=d.iloc[j]; av=float(a.iloc[j-1])
        if not math.isfinite(av) or av<=0:continue
        inside=float(q.Close)<boundary if side=="LONG" else float(q.Close)>boundary
        if inside:
            failed=True; extreme=float(q.Low) if side=="LONG" else float(q.High) if extreme is None else extreme
            extreme=min(extreme,float(q.Low)) if side=="LONG" else max(extreme,float(q.High))
            continue
        if failed:
            rec=float(q.Close)>boundary and float(q.Close)>float(d.High.iloc[j-1]) if side=="LONG" else float(q.Close)<boundary and float(q.Close)<float(d.Low.iloc[j-1])
            if rec:
                e=j+1;p=float(d.Open.iloc[e]);stop=min(extreme,boundary-.5*av) if side=="LONG" else max(extreme,boundary+.5*av)
                return outcome(d,e,p,stop,height,side,DAILY_HORIZON,p*FRICTION_BPS/10000)
    return None
def summ(xs):
    xs=[x for x in xs if x]
    if not xs:return {"n":0}
    r=[x["realized_r"] for x in xs]
    return {"n":len(xs),"mean_r":round(sum(r)/len(r),3),"median_r":round(float(pd.Series(r).median()),3),"positive":sum(v>0 for v in r),"stops":sum(x["exit_reason"]=="STOP" for x in xs)}
def main(folder,base):
    set_reproducible(1729); folder=Path(folder); m=json.loads((folder/"manifest.json").read_text()); b=json.loads(Path(base).read_text())
    rows=[]
    for o in b["observations"]:
        s=o["symbol"]
        if s not in m.get("symbols",{}):continue
        d=load(folder,m,s); label=o["breakout_week"]; side=o["side"]
        # Recover the frozen weekly boundary/height from its risk geometry only for reclaim context.
        # Boundary is approximated by breakout-week close; this extension is therefore a separate frozen challenger, not v2 baseline evidence.
        q=d[d.session_date<=pd.Timestamp(label)]
        if q.empty:continue
        boundary=float(q.Close.iloc[-1]); height=max(float(q.High.tail(100).max()-q.Low.tail(100).min()),1e-9)
        rows.append({"symbol":s,"date":label,"daily_only":daily_only(d,label),"false_break_reclaim":reclaim(d,label,boundary,side,height)})
    n=len(rows);a=int(n*.6);c=int(n*.8)
    return {"status":"RESEARCH_ONLY","hypothesis_version":"weekly-mtf-matched-controls-v1-frozen-2026-09-30",
      "design":"Same weekly-eligible event histories as frozen weekly v2. Daily-only ignores weekly direction and uses 20-session close breakout. False-break/reclaim is a separate challenger.",
      "splits":{"train":[0,a],"validation":[a,c],"final_test":[c,n]},
      "summary":{k:{"train":summ([x[k] for x in rows[:a]]),"validation":summ([x[k] for x in rows[a:c]]),"final_test":summ([x[k] for x in rows[c:]])} for k in ("daily_only","false_break_reclaim")},
      "rows":rows,"caveat":"Reclaim v1 uses completed breakout-week close as boundary proxy; do not compare its R magnitude directly with v2 structural-boundary variant. Frozen before inspection."}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--baseline",default="signals/weekly_pattern_study.json");p.add_argument("--result",default="signals/weekly_mtf_controls.json");a=p.parse_args()
 r=stamp(main(a.folder,a.baseline),"weekly_mtf_controls",a.folder,model_version="matched-controls-v1-frozen-2026-09-30")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(json.dumps(r["summary"],separators=(",",":")))
