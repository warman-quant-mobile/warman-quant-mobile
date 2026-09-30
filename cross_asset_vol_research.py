#!/usr/bin/env python3
"""Cross-asset implied-volatility extreme research; observations, never orders."""
import argparse,json
from pathlib import Path
import pandas as pd

PAIRS={"OVX":"WTI_FUT","GVZ":"GOLD_FUT"}

def load(folder,m,name):
    d=pd.read_csv(Path(folder)/m["symbols"][name]["1d"]["file"])
    d["session_date"]=pd.to_datetime(d["session_date"]); d["Close"]=pd.to_numeric(d["Close"],errors="raise")
    return d.set_index("session_date").Close.sort_index()

def study(folder):
    folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());out={}
    for vol,asset in PAIRS.items():
        if vol not in m["symbols"] or asset not in m["symbols"]:
            out[vol]={"status":"DATA_UNAVAILABLE"};continue
        x=pd.concat([load(folder,m,vol).rename("vol"),load(folder,m,asset).rename("asset")],axis=1).dropna()
        x["pct252"]=x.vol.rolling(252).rank(pct=True);x["spike20"]=x.vol/x.vol.rolling(20).mean()
        x["asset_r5"]=x.asset.pct_change(5);x["asset_r20"]=x.asset.pct_change(20)
        rows=[]
        for d,r in x.iloc[252:].iterrows():
            tags=[]
            if r.pct252>=.95:tags.append("VOL_TOP_5PCT")
            if r.spike20>=1.5:tags.append("VOL_1_5X_MA20")
            if abs(r.asset_r5)>=.08:tags.append("ASSET_5D_MOVE_8PCT")
            if abs(r.asset_r20)>=.15:tags.append("ASSET_20D_MOVE_15PCT")
            if tags:rows.append({"date":d.strftime("%Y-%m-%d"),"vol":round(r.vol,2),"asset":round(r.asset,3),"tags":tags})
        out[vol]={"status":"RESEARCH_ONLY","underlying":asset,"observations":rows[-100:]}
    return {"status":"RESEARCH_ONLY","results":out,
      "note":"Implied-volatility indices are regime sensors, not directional signals. Separate out-of-sample 10R outcome qualification required."}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/cross_asset_vol.json")
    a=p.parse_args();r=study(a.folder);o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(r["status"])
