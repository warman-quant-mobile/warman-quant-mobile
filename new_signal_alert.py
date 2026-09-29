#!/usr/bin/env python3
"""Idempotent new 10R candidate notification payload. No outbound service assumed."""
import argparse,json
from pathlib import Path
def build(current,previous):
    candidates=current.get("proposals",[])
    if current.get("minimum_net_r")!=10:raise ValueError("TEN_R_GATE_MISSING")
    if any(x.get("indicative_net_r",0)<10 for x in candidates):raise ValueError("SUB_10R_PROPOSAL")
    old={x["id"]:x for x in previous.get("proposals",[])}
    changed=[x for x in candidates if x["id"] not in old or
             (x.get("indicative_net_r"),x.get("indicative_stop")) !=
             (old[x["id"]].get("indicative_net_r"),old[x["id"]].get("indicative_stop"))]
    return dict(status="NEW_10R_PAPER_CANDIDATES" if changed else "NO_NEW_10R_CANDIDATES",
                new_or_changed=changed,count=len(changed),
                note="GitHub artifact notification payload only; no push/email provider configured.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--current",default="signals/live_10r.json");p.add_argument("--previous",default="signals/live_10r_previous.json");p.add_argument("--result",default="signals/new_10r.json")
    a=p.parse_args();current=json.loads(Path(a.current).read_text());prior=json.loads(Path(a.previous).read_text()) if Path(a.previous).exists() else {}
    result=build(current,prior);out=Path(a.result);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],result["count"])
