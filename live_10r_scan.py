#!/usr/bin/env python3
"""Live-on-completed-daily-bars strategy scanner; strictly 10R paper proposals only."""
import argparse, hashlib, json, math
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
from published_strategy_lab import signals, RULES

def scan(folder, now=None):
    folder=Path(folder); now=now or datetime.now(timezone.utc)
    manifest=json.loads((folder/"manifest.json").read_text())
    quality=json.loads((folder/"quality.json").read_text())
    if manifest.get("generated_at_utc")!=quality.get("generated_at_utc"): raise ValueError("MISMATCHED_EXPORT")
    created=datetime.fromisoformat(manifest["generated_at_utc"].replace("Z","+00:00"))
    if created>now+timedelta(minutes=5) or now-created>timedelta(hours=8): raise ValueError("STALE_EXPORT")
    if len(quality.get("eligible_symbols",[]))<18: raise ValueError("INSUFFICIENT_COVERAGE")
    proposals=[]; counts={k:0 for k in RULES}; excluded={}
    for symbol in quality["eligible_symbols"]:
        try:
            meta=manifest["symbols"][symbol]["1d"]
            df=pd.read_csv(folder/meta["file"],parse_dates=["session_date"])
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date").reset_index(drop=True)
            if len(df)<400 or df.session_date.duplicated().any(): raise ValueError("INSUFFICIENT_HISTORY")
            if (now.date()-df.iloc[-1].session_date.date()).days>4: raise ValueError("STALE_DAILY_HISTORY")
            for col in ("Open","High","Low","Close"):df[col]=pd.to_numeric(df[col],errors="raise")
            if not ((df.Low>0)&(df.High>=df[["Open","Low","Close"]].max(axis=1))&(df.Low<=df[["Open","High","Close"]].min(axis=1))).all(): raise ValueError("INVALID_OHLC")
            close=df.Close; high=df.High; low=df.Low
            tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
            atr=float(tr.tail(20).mean()); entry=float(close.iloc[-1])
            if not math.isfinite(atr) or atr<=0 or entry<=0:raise ValueError("BAD_ATR_OR_PRICE")
            active=signals(df,len(df),atr)
            for rule,side in active.items():
                if side is None:continue
                counts[rule]+=1
                sign=1 if side=="LONG" else -1
                # The last completed close is a reference, NOT a promised next-open execution price.
                stop=entry-sign*2*atr
                if stop<=0:continue
                # A pre-existing, independently observable level is mandatory; never fabricate 10R.
                # Exclude the most recent 21 bars so the reference precedes the setup.
                historical=df.iloc[-253:-21]
                target=float(historical.High.max() if sign==1 else historical.Low.min())
                friction=entry*.002
                risk=abs(entry-stop)+friction
                reward=(target-entry)*sign-friction
                if sign==-1 and target<=0:continue
                if risk<=0 or reward/risk<10:continue
                rr=reward/risk
                date=str(df.iloc[-1].session_date.date())
                proposal_id=hashlib.sha256(f"{symbol}|{rule}|{side}|{date}".encode()).hexdigest()[:20]
                proposals.append(dict(id=proposal_id,symbol=symbol,strategy=rule,direction=side,
                    signal_session=date,reference_close=round(entry,6),
                    indicative_entry="NEXT_AVAILABLE_QUOTE_REQUIRED",
                    indicative_stop=round(stop,6),historical_reference_level=round(target,6),
                    indicative_net_r=round(rr,2),risk_per_unit_proxy=round(risk,6),
                    status="BLOCKED_UNTIL_EXECUTABLE_QUOTE_VERIFIED",execution_ready=False,
                    instrument_isin=None,verified_bid=None,verified_ask=None,verified_spread=None,
                    verified_financing=None,verified_knockout_distance=None,
                    required_checks=["actual tradable instrument and quote","recalculate R from executable entry and spread",
                    "gap and stop feasibility","liquidity, financing, FX, knockout distance and position sizing",
                    "independent strategy validation; no live execution"]))
        except Exception as exc:excluded[symbol]=str(exc)
    return dict(schema_version=1,status="REVIEW_10R_PAPER_PROPOSALS" if proposals else "NO_10R_PROPOSALS",
        generated_at_utc=now.isoformat(),minimum_net_r=10,proposals=sorted(proposals,key=lambda x:-x["indicative_net_r"]),
        raw_signal_counts=counts,excluded=excluded,
        note="Completed daily bars only. 20bps underlying friction proxy; NOT verified mini-future costs. Historical reference level is not a price forecast. Indicative R MUST be recomputed from executable quote before any paper order. No broker orders.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/live_10r.json")
    a=p.parse_args();r=scan(a.folder);out=Path(a.result);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print(r["status"],len(r["proposals"]),"10R paper proposals")
