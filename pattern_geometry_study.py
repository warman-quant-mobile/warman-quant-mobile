#!/usr/bin/env python3
"""Objective triangle geometry research. Fixed rules, no optimizer, no orders."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from nordnet_kf_gate import promotion_gate
from research_safety import stamp

UNIVERSE=("OMXS30","DAX","SP500","NASDAQ100","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT",
          "INVESTOR_B","VOLVO_B","ATLAS_A","ABB","NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META",
          "BITCOIN","ETHEREUM","SOLANA")
WINDOW=40; PIVOT=3; MIN_TOUCH=3; FRICTION_BPS=20; HORIZON=60

def load(folder,m,s):
    d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date")
    for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="raise")
    return d.drop_duplicates("session_date").reset_index(drop=True)

def atr20(d):
    c=d.Close
    return pd.concat([d.High-d.Low,(d.High-c.shift()).abs(),(d.Low-c.shift()).abs()],axis=1).max(axis=1).rolling(20).mean()

def pivots(d,end):
    # Only pivots confirmable by end: right-hand PIVOT bars are already known.
    a=max(0,end-WINDOW); hs=[];ls=[]
    for i in range(a+PIVOT,end-PIVOT):
        if d.High.iloc[i]>=d.High.iloc[i-PIVOT:i+PIVOT+1].max(): hs.append(i)
        if d.Low.iloc[i]<=d.Low.iloc[i-PIVOT:i+PIVOT+1].min(): ls.append(i)
    return hs[-6:],ls[-6:]

def line_fit(idx,vals):
    if len(idx)<MIN_TOUCH:return None
    x=pd.Series(idx[-MIN_TOUCH:],dtype=float);y=pd.Series([vals.iloc[i] for i in idx[-MIN_TOUCH:]],dtype=float)
    xm=x.mean();ym=y.mean();den=((x-xm)**2).sum()
    if den<=0:return None
    slope=float(((x-xm)*(y-ym)).sum()/den);inter=float(ym-slope*xm)
    ss=((y-ym)**2).sum();r2=1.0 if ss==0 else 1-float(((y-(slope*x+inter))**2).sum()/ss)
    return slope,inter,r2

def detect(d,i,atr):
    hs,ls=pivots(d,i)
    uh=line_fit(hs,d.High);ll=line_fit(ls,d.Low)
    if not uh or not ll or uh[2]<.65 or ll[2]<.65:return None
    u0=uh[0]*(i-WINDOW)+uh[1];l0=ll[0]*(i-WINDOW)+ll[1];u1=uh[0]*(i-1)+uh[1];l1=ll[0]*(i-1)+ll[1]
    w0=u0-l0;w1=u1-l1
    if w0<=0 or w1<=0 or w1/w0>.70:return None
    a=float(atr.iloc[i-1])
    if not math.isfinite(a) or a<=0:return None
    su=uh[0]/a;sl=ll[0]/a;flat=.08
    if su<-.03 and sl>.03: typ="SYMMETRICAL"
    elif abs(su)<=flat and sl>.03: typ="ASCENDING"
    elif su<-.03 and abs(sl)<=flat: typ="DESCENDING"
    elif su<0 and sl<0 and su<sl: typ="FALLING_WEDGE"
    elif su>0 and sl>0 and su<sl: typ="RISING_WEDGE"
    else:return None
    upper=uh[0]*i+uh[1];lower=ll[0]*i+ll[1]
    return dict(type=typ,upper=upper,lower=lower,height=w0,compression=w1/w0,r2_high=uh[2],r2_low=ll[2],
        slope_high_atr=su,slope_low_atr=sl,touches_high=len(hs),touches_low=len(ls))

def evaluate(d,i,p,atr):
    b=d.iloc[i]; prev=d.iloc[i-1]; side=None; boundary=None
    # Close-confirmed breakout; entry next session open prevents same-bar lookahead.
    if b.Close>p["upper"] and prev.Close<=p["upper"]:side="LONG";boundary=p["upper"]
    elif b.Close<p["lower"] and prev.Close>=p["lower"]:side="SHORT";boundary=p["lower"]
    if not side or i+1>=len(d):return None
    e=i+1;price=float(d.Open.iloc[e]);a=float(atr.iloc[i]);sign=1 if side=="LONG" else -1
    prev_close=float(d.Close.iloc[i-1]); breakout_strength=((float(b.Close)-boundary)*sign/a)
    trend20=((float(d.Close.iloc[i-1])/float(d.Close.iloc[i-21])-1)*sign) if i>=21 else 0.0
    gap_atr=((price-float(b.Close))*sign/a)
    # Structural stop: opposite side of breakout bar OR 0.5 ATR beyond boundary, whichever is tighter but valid.
    if side=="LONG": stop=max(float(b.Low),boundary-.5*a); risk0=price-stop
    else: stop=min(float(b.High),boundary+.5*a); risk0=stop-price
    friction=price*FRICTION_BPS/10000;risk=risk0+friction
    if risk<=0:return None
    target=price+sign*p["height"]; geom_r=(p["height"]-friction)/risk
    if target<=0:return None
    pnl=None;mfe=0.;out="TIMEOUT"
    for j in range(e,min(e+HORIZON,len(d))):
        q=d.iloc[j];o,h,l=map(float,(q.Open,q.High,q.Low))
        fav=(h-price if side=="LONG" else price-l)-friction;mfe=max(mfe,fav/risk)
        stopped=l<=stop if side=="LONG" else h>=stop;won=h>=target if side=="LONG" else l<=target
        if stopped:
            fill=min(o,stop) if side=="LONG" else max(o,stop);pnl=(fill-price)*sign-friction;out="STOP";break
        if won:pnl=(target-price)*sign-friction;out="MEASURED_TARGET";break
    if pnl is None:pnl=(float(d.Close.iloc[min(e+HORIZON-1,len(d)-1)])-price)*sign-friction
    return {"date":str(d.session_date.iloc[i].date()),"type":p["type"],"side":side,"geometric_r":round(geom_r,3),
            "realized_r":round(pnl/risk,3),"mfe_r":round(mfe,3),"outcome":out,
            "compression":round(p["compression"],3),"r2_high":round(p["r2_high"],3),"r2_low":round(p["r2_low"],3),
            "slope_high_atr":round(p["slope_high_atr"],4),"slope_low_atr":round(p["slope_low_atr"],4),
            "touches_high":p["touches_high"],"touches_low":p["touches_low"],
            "breakout_strength_atr":round(breakout_strength,4),"trend20_signed":round(trend20,4),
            "gap_atr":round(gap_atr,4),"atr_pct":round(a/price,5)}

def summarize(xs):
    if not xs:return {"n":0}
    split=max(1,int(len(xs)*.6))
    def s(a):
        if not a:return {"n":0}
        return {"n":len(a),"mean_r":round(float(pd.Series([x["realized_r"] for x in a]).mean()),3),
          "median_r":round(float(pd.Series([x["realized_r"] for x in a]).median()),3),
          "mean_geometric_r":round(float(pd.Series([x["geometric_r"] for x in a]).mean()),3),
          "target_hits":sum(x["outcome"]=="MEASURED_TARGET" for x in a),
          "mfe_5r":sum(x["mfe_r"]>=5 for x in a),"mfe_10r":sum(x["mfe_r"]>=10 for x in a),
          "max_mfe_r":round(max(x["mfe_r"] for x in a),3)}
    return {"all":s(xs),"train":s(xs[:split]),"oos":s(xs[split:])}

def study(folder):
    folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());results={};latest=[];observations=[]
    for sym in UNIVERSE:
        if sym not in m["symbols"]:continue
        d=load(folder,m,sym)
        if len(d)<350:continue
        atr=atr20(d);obs=[];last_event=-999
        for i in range(260,len(d)-1):
            p=detect(d,i,atr)
            if not p:continue
            r=evaluate(d,i,p,atr)
            if r and i-last_event>=20:
                r["symbol"]=sym;obs.append(r);observations.append(r);last_event=i
                if i>=len(d)-5:latest.append(r)
        results[sym]={"summary":summarize(obs),"by_type":{t:summarize([x for x in obs if x["type"]==t]) for t in sorted(set(x["type"] for x in obs))}}
    return {"status":"RESEARCH_ONLY","rules":{"window":WINDOW,"pivot":PIVOT,"min_touches_each_side":MIN_TOUCH,
      "max_final_width_ratio":.70,"min_line_r2":.65,"entry":"next session open after close-confirmed breakout",
      "stop":"structural breakout-bar/opposite-boundary 0.5ATR rule","target":"formation initial height projected from entry",
      "friction_bps":FRICTION_BPS,"horizon_sessions":HORIZON},
      "results":results,"observations":observations,"recent_patterns":latest,
      "note":"Frozen first-pass geometry. No parameter optimization. Results must survive OOS/robustness and Nordnet-KF execution checks before promotion."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/pattern_geometry_study.json")
    a=p.parse_args();r=study(a.folder);r=stamp(r,"pattern_geometry_v2",a.folder,model_version="rules-v2-frozen-2026-09-30");o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n")
    print("PATTERN_GEOMETRY",len(r["results"]),"markets",len(r["recent_patterns"]),"recent")
