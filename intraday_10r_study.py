#!/usr/bin/env python3
"""Research summary for hourly watch events; never an order."""
import argparse,json
from pathlib import Path
import pandas as pd

def study(folder):
    folder=Path(folder)
    manifest=json.loads((folder/"manifest.json").read_text())
    quality=json.loads((folder/"quality.json").read_text())
    results={}
    for symbol in quality.get("eligible_symbols",[]):
        meta=manifest["symbols"][symbol]["1h"]
        df=pd.read_csv(folder/meta["file"])
        results[symbol]={"hourly_bars":len(df),"sample_gate_passed":len(df)>=1000}
    return {"status":"RESEARCH_ONLY","results":results,
            "promotion_rule":"No hourly setup can be promoted unless sample_gate_passed is true.",
            "warning":"Short hourly history is observation-only, not evidence of a 10R edge."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/intraday_10r_study.json")
    a=p.parse_args();r=study(a.folder);out=Path(a.result);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2)+"\n");print("INTRADAY_SAMPLE_GATE",sum(x["sample_gate_passed"] for x in r["results"].values()))
