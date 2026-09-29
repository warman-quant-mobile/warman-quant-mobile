#!/usr/bin/env python3
"""Published-rule-inspired daily OHLC research. NOT a reproduction of published returns.
Signals use completed previous sessions; entries at next open; conservative stop-first
daily OHLC simulation. No broker orders or promotion eligibility.
"""
import argparse
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd

RULES = ("turtle_55", "volatility_contraction", "failed_breakout", "momentum_ignition",
         "time_series_momentum", "rsi2_reversal")
def signals(df, i, atr):
    p=df.iloc[:i]
    c=p.Close.astype(float); h=p.High.astype(float); l=p.Low.astype(float)
    last=float(c.iloc[-1]); prev=float(c.iloc[-2]); high20=float(h.iloc[-21:-1].max())
    low20=float(l.iloc[-21:-1].min()); ma200=float(c.tail(200).mean())
    ret=c.diff(); gain=ret.clip(lower=0).tail(2).mean(); loss=(-ret.clip(upper=0)).tail(2).mean()
    rsi=100 if loss==0 else 100-100/(1+gain/loss)
    width=(h.tail(20).max()-l.tail(20).min())/last
    past_widths=((h.rolling(20).max()-l.rolling(20).min())/c).iloc[-120:-20].dropna()
    contraction=len(past_widths)>=50 and width<=past_widths.quantile(.1)
    gap_up=last>high20 and prev<=float(h.iloc[-22:-2].max())
    gap_down=last<low20 and prev>=float(l.iloc[-22:-2].min())
    return {
      "turtle_55": "LONG" if last>float(h.iloc[-56:-1].max()) else ("SHORT" if last<float(l.iloc[-56:-1].min()) else None),
      "volatility_contraction": "LONG" if contraction and last>=float(h.tail(20).max())*.999 and last>ma200 else None,
      "failed_breakout": "SHORT" if float(h.iloc[-1])>high20 and last<high20 else ("LONG" if float(l.iloc[-1])<low20 and last>low20 else None),
      "momentum_ignition": "LONG" if last-prev>2*atr and last>high20 else ("SHORT" if prev-last>2*atr and last<low20 else None),
      "time_series_momentum": "LONG" if last>float(c.iloc[-253]) and last>ma200 else ("SHORT" if last<float(c.iloc[-253]) and last<ma200 else None),
      "rsi2_reversal": "LONG" if rsi<10 and last>ma200 else None
    }
def simulate(df, i, side, atr, horizon=60, bps=20):
    entry=float(df.iloc[i].Open)
    if entry<=0 or not math.isfinite(entry): return None
    dist=2*atr; friction=entry*bps/10000; risk=dist+friction
    sign=1 if side=="LONG" else -1
    stop=entry-sign*dist
    if stop<=0 or (side=="SHORT" and entry-10*risk<=0): return None
    mfe=0.; mae=0.; outcome="TIMEOUT"; exit_price=None
    for j in range(i,min(i+horizon,len(df))):
        b=df.iloc[j]; o,h,l=map(float,(b.Open,b.High,b.Low))
        if not all(math.isfinite(v) for v in (o,h,l)) or l<=0 or not l<=o<=h: return None
        mfe=max(mfe, (h-entry) if sign==1 else (entry-l))
        mae=max(mae, (entry-l) if sign==1 else (h-entry))
        if (l<=stop if sign==1 else h>=stop):
            exit_price=min(o,stop) if sign==1 else max(o,stop)
            outcome="STOP";break
        # Trailing exit based ONLY on completed prior bars; evaluated at current bar.
        if j>=i+20:
            trailing=(float(df.iloc[j-20:j].Low.min()) if sign==1 else float(df.iloc[j-20:j].High.max()))
            if (l<=trailing if sign==1 else h>=trailing):
                exit_price=min(o,trailing) if sign==1 else max(o,trailing)
                outcome="TRAIL";break
    if exit_price is None: exit_price=float(df.iloc[min(i+horizon-1,len(df)-1)].Close)
    return dict(realized_r=round(((exit_price-entry)*sign-friction)/risk,3),
                mfe_r=round(mfe/risk,3),mae_r=round(mae/risk,3),outcome=outcome)
def study(folder, now=None):
    folder=Path(folder); now=now or datetime.now(timezone.utc)
    manifest=json.loads((folder/"manifest.json").read_text())
    quality=json.loads((folder/"quality.json").read_text())
    if manifest.get("generated_at_utc")!=quality.get("generated_at_utc"): raise ValueError("MISMATCHED_EXPORT")
    created=datetime.fromisoformat(manifest["generated_at_utc"].replace("Z","+00:00"))
    if created>now+timedelta(minutes=5) or now-created>timedelta(hours=8): raise ValueError("STALE_EXPORT")
    if len(quality.get("eligible_symbols",[]))<18: raise ValueError("INSUFFICIENT_COVERAGE")
    results={}; excluded={}
    for symbol in quality["eligible_symbols"]:
        try:
            meta=manifest["symbols"][symbol]["1d"]
            df=pd.read_csv(folder/meta["file"],parse_dates=["session_date"])
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date").reset_index(drop=True)
            if len(df)<400 or df.session_date.duplicated().any(): raise ValueError("INSUFFICIENT_HISTORY")
            if (now.date()-df.iloc[-1].session_date.date()).days>4: raise ValueError("STALE_DAILY_HISTORY")
            for col in ("Open","High","Low","Close"): df[col]=pd.to_numeric(df[col],errors="raise")
            if not ((df.Low>0)&(df.High>=df[["Open","Low","Close"]].max(axis=1))&(df.Low<=df[["Open","High","Close"]].min(axis=1))).all(): raise ValueError("INVALID_OHLC")
            by_rule={}; next_allowed={k:0 for k in RULES}
            for k in RULES: by_rule[k]=[]
            for i in range(254,len(df)-60):
                p=df.iloc[:i]; previous=p.Close.shift()
                tr=pd.concat([p.High-p.Low,(p.High-previous).abs(),(p.Low-previous).abs()],axis=1).max(axis=1)
                atr=float(tr.tail(20).mean())
                if not math.isfinite(atr) or atr<=0: continue
                found=signals(df,i,atr)
                for rule,side in found.items():
                    if side is None or i<next_allowed[rule]:continue
                    event=simulate(df,i,side,atr)
                    if event:
                        by_rule[rule].append(event);next_allowed[rule]=i+60
            results[symbol]={}
            for rule,events in by_rule.items():
                n=len(events);rs=[e["realized_r"] for e in events]
                results[symbol][rule]=dict(events=n,mean_realized_r=round(sum(rs)/n,3) if n else None,
                    reached_5r_mfe=sum(e["mfe_r"]>=5 for e in events),
                    reached_10r_mfe=sum(e["mfe_r"]>=10 for e in events),
                    reached_15r_mfe=sum(e["mfe_r"]>=15 for e in events),
                    realized_10r=sum(e["realized_r"]>=10 for e in events),
                    max_mfe_r=max((e["mfe_r"] for e in events),default=None),
                    insufficient_sample=n<100)
        except Exception as exc: excluded[symbol]=str(exc)
    return dict(schema_version=1,status="RESEARCH_ONLY",generated_at_utc=now.isoformat(),
        rules=list(RULES),results=results,excluded=excluded,
        deferred={"opening_range_breakout":"Requires validated intraday session bars",
                  "post_earnings_drift":"Requires point-in-time earnings surprise/calendar data"},
        assumptions="Prior-close signals, next-open hypothetical fills, ATR20 x2 initial stop, trailing 20-session channel after 20 bars, 60-session horizon, 20bps proxy round-trip cost, adverse opening gap fill, non-overlapping observations per rule and symbol. MFE diagnostic is not an executable profit target.",
        warning="Exploratory in-sample screen only; not validated expected value, independently verified execution costs, broker instrument model or live trading signal.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/published_strategy_lab.json")
    a=p.parse_args();result=study(a.folder);dest=Path(a.result);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PUBLISHED_STRATEGY_RESEARCH_ONLY",len(result["results"]),"instruments",len(result["excluded"]),"excluded")
