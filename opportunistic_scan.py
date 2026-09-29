#!/usr/bin/env python3
"""Conservative research-only 10R opportunity gate; never emits executable orders."""
import argparse, json, math
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd

def scan(folder, now=None):
    folder=Path(folder); now=now or datetime.now(timezone.utc)
    manifest=json.loads((folder/"manifest.json").read_text())
    quality=json.loads((folder/"quality.json").read_text())
    created=datetime.fromisoformat(manifest["generated_at_utc"].replace("Z","+00:00"))
    if now-created>timedelta(hours=8) or created>now+timedelta(minutes=5):
        raise ValueError("STALE_EXPORT: manifest must be generated within eight hours")
    results=[]; rejected={}
    for symbol in quality["eligible_symbols"]:
        try:
            meta=manifest["symbols"][symbol]["1d"]
            df=pd.read_csv(folder/meta["file"],parse_dates=["session_date"])
            # Current UTC date may contain an incomplete session: never use it.
            df=df[df.session_date.dt.date<now.date()].sort_values("session_date")
            if len(df)<270: raise ValueError("less than 270 complete daily bars")
            last=df.iloc[-1]; date=last.session_date.date()
            if (now.date()-date).days>4: raise ValueError("stale daily bar")
            close=df.Close.astype(float); high=df.High.astype(float); low=df.Low.astype(float)
            tr=pd.concat([high-low,(high-close.shift()).abs(),(low-close.shift()).abs()],axis=1).max(axis=1)
            atr=tr.rolling(20).mean().iloc[-1]
            if not math.isfinite(atr) or atr<=0: raise ValueError("bad ATR")
            price=float(close.iloc[-1]); ma50=float(close.tail(50).mean()); ma200=float(close.tail(200).mean())
            prev20h=float(high.iloc[-21:-1].max()); prev20l=float(low.iloc[-21:-1].min())
            # Prior year's extremes are independent, historical reference levels, not promised targets.
            prior_high=float(high.iloc[-253:-21].max()); prior_low=float(low.iloc[-253:-21].min())
            direction=("LONG" if price>prev20h and price>ma50>ma200 else
                       "SHORT" if price<prev20l and price<ma50<ma200 else None)
            if direction is None: continue
            stop=(price-2*atr if direction=="LONG" else price+2*atr)
            # Conservative historical reference target; breakout beyond 20d often has no validated 10R target.
            target=(prior_high if direction=="LONG" else prior_low)
            reward=(target-price if direction=="LONG" else price-target)
            risk=abs(price-stop)
            rr=reward/risk
            if rr<10: continue
            results.append(dict(symbol=symbol,direction=direction,session_date=str(date),
                proxy_close=round(price,6),atr20=round(float(atr),6),trigger=round(price,6),
                invalidation=round(stop,6),historical_reference_target=round(target,6),
                indicative_reward_risk=round(rr,2),status="RESEARCH_CANDIDATE_NOT_ORDER",
                required_checks=["independent thesis and 10R plausibility","Nordnet ISIN/quotes",
                "knockout margin","spread/financing/FX","gap and correlation risk"]))
        except Exception as exc: rejected[symbol]=str(exc)
    return dict(schema_version=1,generated_at_utc=now.isoformat(),source_manifest_utc=manifest["generated_at_utc"],
        status="CANDIDATES_REQUIRE_MANUAL_VERIFICATION" if results else "NO_QUALIFIED_CANDIDATES",
        candidates=results,rejected=rejected,
        warning="Historical reference targets are NOT forecasts. A 10R geometric ratio is not proven expected value. No automatic trading.")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/latest.json")
    args=p.parse_args();result=scan(args.folder);path=Path(args.result);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(result["status"],len(result["candidates"]),"candidates")
