#!/usr/bin/env python3
"""Cross-asset macro extreme outcome study. Research only; never emits orders."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from opportunistic_research import evaluate

def load(folder,m,name):
    d=pd.read_csv(Path(folder)/m["symbols"][name]["1d"]["file"],parse_dates=["session_date"])
    for k in ("Open","High","Low","Close"): d[k]=pd.to_numeric(d[k],errors="raise")
    return d.sort_values("session_date").drop_duplicates("session_date").set_index("session_date")

def summarize(obs):
    n=len(obs); vals=[x["realized_r"] for x in obs]; mfes=[x["mfe_r"] for x in obs]
    split=max(1,int(n*.6)) if n else 0
    train=obs[:split]; test=obs[split:]
    def part(xs):
        if not xs:return {"events":0,"mean_realized_r":None,"median_realized_r":None,"reached_10r_mfe":0}
        rv=[z["realized_r"] for z in xs]
        return {"events":len(xs),"mean_realized_r":round(sum(rv)/len(rv),3),
          "median_realized_r":round(float(pd.Series(rv).median()),3),
          "reached_10r_mfe":sum(z["mfe_r"]>=10 for z in xs)}
    return {"events":n,"sample_qualified":n>=30,"strong_sample":n>=100,
      "chronological_split_60_40":{"train":part(train),"oos":part(test)},
      "oos_positive":bool(test) and part(test)["mean_realized_r"] is not None and part(test)["mean_realized_r"]>0,
      "targets_10r":sum(x["outcome"]=="TARGET" for x in obs),
      "reached_5r_mfe":sum(x["mfe_r"]>=5 for x in obs),"reached_10r_mfe":sum(x["mfe_r"]>=10 for x in obs),
      "mean_realized_r":round(sum(vals)/n,3) if n else None,
      "median_realized_r":round(float(pd.Series(vals).median()),3) if n else None,
      "p75_mfe_r":round(float(pd.Series(mfes).quantile(.75)),3) if n else None,
      "p90_mfe_r":round(float(pd.Series(mfes).quantile(.90)),3) if n else None,
      "max_mfe_r":max(mfes,default=None)}

def run_events(asset, cond, sidefn, gap=60):
    obs=[]; dates=[]; i=252
    while i<len(asset)-60:
        if bool(cond.iloc[i-1]):
            side=sidefn(i-1); r=evaluate(asset.reset_index(),side,i)
            if r: obs.append(r);dates.append(str(asset.index[i-1].date()));i+=gap;continue
        i+=1
    return summarize(obs)|{"first_event":dates[0] if dates else None,"last_event":dates[-1] if dates else None}

def study(folder):
    folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());out={}
    # VIX + SPX: capitulation/rebound and crash continuation.
    if all(x in m["symbols"] for x in ("VIX","SP500")):
        s=load(folder,m,"SP500");v=load(folder,m,"VIX")[["Close"]].rename(columns={"Close":"vix"})
        x=s.join(v,how="inner"); x["vix_pct"]=x.vix.rolling(252).rank(pct=True)
        x["vix_spike"]=x.vix/x.vix.rolling(20).mean();x["dd20"]=x.Close/x.Close.rolling(20).max()-1
        cond=(x.vix_pct>=.95)&(x.vix_spike>=1.5)&(x.dd20<=-.08)
        out["VIX_SPX_CAPITULATION"]={
          "SPX_LONG":run_events(x[["Open","High","Low","Close"]],cond,lambda i:"LONG"),
          "SPX_SHORT":run_events(x[["Open","High","Low","Close"]],cond,lambda i:"SHORT")}
    # OVX + WTI: extreme vol plus large 5d oil displacement; test trend and fade.
    if all(x in m["symbols"] for x in ("OVX","WTI_FUT")):
        a=load(folder,m,"WTI_FUT");v=load(folder,m,"OVX")[["Close"]].rename(columns={"Close":"vol"})
        x=a.join(v,how="inner");x["vpct"]=x.vol.rolling(252).rank(pct=True);x["spike"]=x.vol/x.vol.rolling(20).mean();x["r5"]=x.Close.pct_change(5)
        cond=(x.vpct>=.95)&(x.spike>=1.5)&(x.r5.abs()>=.08)
        side=lambda i:"LONG" if x.r5.iloc[i]>0 else "SHORT"
        fade=lambda i:"SHORT" if x.r5.iloc[i]>0 else "LONG"
        asset=x[["Open","High","Low","Close"]]
        out["OVX_WTI_EXTREME"]={"CONTINUATION":run_events(asset,cond,side),"FADE":run_events(asset,cond,fade)}
    # Long-end rate extremes: 30Y yield percentile + 20d displacement, tested both ways.
    if "US30Y_YIELD" in m["symbols"]:
        y=load(folder,m,"US30Y_YIELD");x=y.copy();x["pct"]=x.Close.rolling(756).rank(pct=True);x["bp20"]=(x.Close-x.Close.shift(20))*100
        # Yahoo Treasury yield indices are percentage yields; x100 converts percentage-point change to bp.
        cond=((x.pct>=.95)|(x.pct<=.05))&(x.bp20.abs()>=20)
        trend=lambda i:"LONG" if x.bp20.iloc[i]>0 else "SHORT";fade=lambda i:"SHORT" if x.bp20.iloc[i]>0 else "LONG"
        out["US30Y_YIELD_EXTREME"]={"CONTINUATION":run_events(y,cond,trend),"FADE":run_events(y,cond,fade)}
    # Curve displacement: 30Y minus 10Y yield; trade 30Y bond future in direction implied by long-end move and opposite.
    if all(x in m["symbols"] for x in ("US30Y_YIELD","US10Y_YIELD","US30Y_BOND_FUT")):
        y30=load(folder,m,"US30Y_YIELD")[["Close"]].rename(columns={"Close":"y30"});y10=load(folder,m,"US10Y_YIELD")[["Close"]].rename(columns={"Close":"y10"})
        b=load(folder,m,"US30Y_BOND_FUT");z=y30.join(y10,how="inner");z["curve"]=z.y30-z.y10;z["chg20"]=z.curve-z.curve.shift(20)
        z["z"]=(z.curve-z.curve.rolling(252).mean())/z.curve.rolling(252).std()
        idx=b.index.intersection(z.index);bb=b.loc[idx];zz=z.loc[idx];cond=(zz.z.abs()>=2)&(zz.chg20.abs()>=.10)
        # Steepening with long-end pressure -> short bond; flattening -> long bond.
        trend=lambda i:"SHORT" if zz.chg20.iloc[i]>0 else "LONG";fade=lambda i:"LONG" if zz.chg20.iloc[i]>0 else "SHORT"
        out["30Y10Y_CURVE_EXTREME"]={"CONTINUATION":run_events(bb,cond,trend),"FADE":run_events(bb,cond,fade)}
    return {"status":"RESEARCH_ONLY","minimum_promotion_r":10,"results":out,
      "methodology":"Completed daily signal; next-session open; ATR20 x2 stop; 20bps friction; 10R target; 60-session horizon; non-overlapping 60-session events; stop first on same-bar ambiguity. Each setup also reports a chronological 60/40 train/OOS split. Rate displacement uses basis points, not relative yield returns.",
      "promotion_rule":"No setup is eligible for promotion unless sample_qualified=true, OOS is positive, and the trade maps to a Nordnet-KF-verifiable instrument. Yield/VIX/OVX/GVZ series are sensors only. A 10R hit alone is insufficient."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/macro_combo_study.json")
    a=p.parse_args();r=study(a.folder);o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(r["status"],len(r["results"]))
