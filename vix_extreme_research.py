#!/usr/bin/env python3
"""VIX/SP500 extreme-regime research. Signals are research observations, never orders."""
import argparse,json
from pathlib import Path
import pandas as pd

def load(folder,manifest,name):
    df=pd.read_csv(Path(folder)/manifest["symbols"][name]["1d"]["file"])
    for k in ("Open","High","Low","Close"): df[k]=pd.to_numeric(df[k],errors="raise")
    df["session_date"]=pd.to_datetime(df["session_date"])
    return df.set_index("session_date").sort_index()

def study(folder):
    folder=Path(folder); m=json.loads((folder/"manifest.json").read_text())
    if "VIX" not in m["symbols"] or "SP500" not in m["symbols"]:
        return {"status":"DATA_UNAVAILABLE","setups":[]}
    v=load(folder,m,"VIX"); s=load(folder,m,"SP500")
    x=s[["Close"]].rename(columns={"Close":"spx"}).join(v[["Close"]].rename(columns={"Close":"vix"}),how="inner")
    x["spx_rsi2_gain"]=x.spx.diff().clip(lower=0).rolling(2).mean()
    x["spx_rsi2_loss"]=(-x.spx.diff().clip(upper=0)).rolling(2).mean()
    rs=x.spx_rsi2_gain/x.spx_rsi2_loss.replace(0,float("nan")); x["rsi2"]=100-100/(1+rs)
    x["vix_pct252"]=x.vix.rolling(252).rank(pct=True)
    x["vix_ma20"]=x.vix.rolling(20).mean(); x["vix_spike"]=x.vix/x.vix_ma20
    x["spx_dd20"]=x.spx/x.spx.rolling(20).max()-1
    rows=[]
    for d,r in x.iloc[252:].iterrows():
        tags=[]
        if r.vix_pct252>=.95: tags.append("VIX_TOP_5PCT")
        if r.vix_spike>=1.5: tags.append("VIX_1_5X_MA20")
        if r.spx_dd20<=-.08: tags.append("SPX_DRAWDOWN_8PCT_20D")
        if r.rsi2<=10: tags.append("SPX_RSI2_LE_10")
        if tags: rows.append({"date":d.strftime("%Y-%m-%d"),"vix":round(r.vix,2),"spx":round(r.spx,2),"tags":tags})
    return {"status":"RESEARCH_ONLY","setups":rows[-100:],
      "note":"VIX measures expected 30-day SPX volatility, not direction. These are regime/extreme observations; 10R outcome study required before promotion."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/vix_extremes.json")
    a=p.parse_args();r=study(a.folder);o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n")
    print(r["status"],len(r.get("setups",[])))
