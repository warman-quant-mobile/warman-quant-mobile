#!/usr/bin/env python3
"""Frozen weekly triangle + weekly-context/daily-retest research. Research only; no orders."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from research_safety import stamp

WINDOWS=(20,40,60); PIVOT=2; MIN_TOUCH=3; MIN_R2=.65; MAX_COMPRESSION=.70
FRICTION_BPS=20; WEEK_HORIZON=26; DAILY_HORIZON=130; RETEST_LOOKAHEAD=10
FIXED_R=(3,5,10,15,20)
UNIVERSE=("OMXS30","DAX","SP500","NASDAQ100","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT",
"INVESTOR_B","VOLVO_B","ATLAS_A","ABB","NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META",
"BITCOIN","ETHEREUM","SOLANA")

def load(folder,m,s):
    d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date")
    for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="raise")
    return d.drop_duplicates("session_date").reset_index(drop=True)

def weekly(d):
    return d.set_index("session_date").resample("W-FRI").agg(
        {"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()

def atr(d,n=20):
    c=d.Close
    return pd.concat([d.High-d.Low,(d.High-c.shift()).abs(),(d.Low-c.shift()).abs()],axis=1).max(axis=1).rolling(n).mean()

def piv(d,end,w):
    a=max(0,end-w); hs=[];ls=[]
    for j in range(a+PIVOT,end-PIVOT):
        if d.High.iloc[j]>=d.High.iloc[j-PIVOT:j+PIVOT+1].max(): hs.append(j)
        if d.Low.iloc[j]<=d.Low.iloc[j-PIVOT:j+PIVOT+1].min(): ls.append(j)
    return hs[-6:],ls[-6:]

def fit(idx,v):
    if len(idx)<MIN_TOUCH:return None
    use=idx[-MIN_TOUCH:]; x=pd.Series(use,dtype=float); y=pd.Series([v.iloc[j] for j in use],dtype=float)
    den=((x-x.mean())**2).sum()
    if den<=0:return None
    s=float(((x-x.mean())*(y-y.mean())).sum()/den); b=float(y.mean()-s*x.mean())
    ss=((y-y.mean())**2).sum(); r2=1. if ss==0 else 1-float(((y-(s*x+b))**2).sum()/ss)
    return s,b,r2,use

def detect(wd,i,a,w):
    hs,ls=piv(wd,i,w); u=fit(hs,wd.High); l=fit(ls,wd.Low)
    if not u or not l or u[2]<MIN_R2 or l[2]<MIN_R2:return None
    # Height starts where the selected confirmed pivots actually begin; never extrapolate
    # the fitted lines backwards to an arbitrary window boundary.
    start=min(u[3]+l[3]); u0=u[0]*start+u[1]; l0=l[0]*start+l[1]
    u1=u[0]*(i-1)+u[1]; l1=l[0]*(i-1)+l[1]
    width0=u0-l0; width1=u1-l1
    if width0<=0 or width1<=0 or width1/width0>MAX_COMPRESSION:return None
    av=float(a.iloc[i-1])
    if not math.isfinite(av) or av<=0:return None
    su=u[0]/av; sl=l[0]/av
    if not ((su<-.03 and sl>.03) or (abs(su)<=.08 and sl>.03) or (su<-.03 and abs(sl)<=.08)):return None
    return {"upper":u[0]*i+u[1],"lower":l[0]*i+l[1],"height":width0,
      "compression":width1/width0,"r2_high":u[2],"r2_low":l[2],"window":w,
      "formation_start_index":start}

def outcome(d,e,price,stop,height,side,horizon,friction):
    sign=1 if side=="LONG" else -1; risk0=(price-stop)*sign; risk=risk0+friction
    if risk0<=0 or risk<=0:return None
    measured=price+sign*height
    if measured<=0:return None
    fixed={str(k):False for k in FIXED_R}; mfe=0.;mae=0.; realized=None; exit_reason="TIMEOUT"
    end=min(e+horizon,len(d))
    for j in range(e,end):
        q=d.iloc[j]; o=float(q.Open); h=float(q.High); l=float(q.Low)
        fav=(h-price if side=="LONG" else price-l)-friction
        adv=(price-l if side=="LONG" else h-price)+friction
        mfe=max(mfe,fav/risk);mae=max(mae,adv/risk)
        hitstop=l<=stop if side=="LONG" else h>=stop
        # Conservative ambiguity rule: stop wins whenever stop and any target occur in same bar.
        if hitstop:
            fill=min(o,stop) if side=="LONG" else max(o,stop)
            realized=((fill-price)*sign-friction)/risk;exit_reason="STOP";break
        for k in FIXED_R:
            target=price+sign*(k*risk+friction)
            hit=h>=target if side=="LONG" else l<=target
            if hit:fixed[str(k)]=True
        hit_measured=h>=measured if side=="LONG" else l<=measured
        if hit_measured:
            realized=((measured-price)*sign-friction)/risk;exit_reason="MEASURED_TARGET";break
    if realized is None:
        close=float(d.Close.iloc[end-1]);realized=((close-price)*sign-friction)/risk
    return {"risk":round(risk,6),"realized_r":round(realized,3),"mfe_r":round(mfe,3),
      "mae_r":round(mae,3),"fixed_r_before_stop":fixed,"exit_reason":exit_reason,
      "measured_target_r":round((height-friction)/risk,3)}

def daily_retest_entry(d,breakout_label,boundary,side,height):
    sign=1 if side=="LONG" else -1; da=atr(d,20)
    idx=d.index[d.session_date>pd.Timestamp(breakout_label)].tolist()[:RETEST_LOOKAHEAD]
    for j in idx:
        if j<21 or j+1>=len(d):continue
        av=float(da.iloc[j-1])
        if not math.isfinite(av) or av<=0:continue
        q=d.iloc[j]
        # Signal is known only at this daily close. Require a touch near the broken weekly
        # boundary followed by a close back on the breakout side.
        touched=float(q.Low)<=boundary+.25*av if side=="LONG" else float(q.High)>=boundary-.25*av
        reclaimed=float(q.Close)>boundary if side=="LONG" else float(q.Close)<boundary
        momentum=float(q.Close)>float(d.High.iloc[j-1]) if side=="LONG" else float(q.Close)<float(d.Low.iloc[j-1])
        if not (touched and reclaimed and momentum):continue
        e=j+1;price=float(d.Open.iloc[e])
        stop=min(float(q.Low),boundary-.5*av) if side=="LONG" else max(float(q.High),boundary+.5*av)
        return outcome(d,e,price,stop,height,side,DAILY_HORIZON,price*FRICTION_BPS/10000)
    return None

def summary(rows,key):
    xs=[x[key] for x in rows if x.get(key)]
    if not xs:return {"n":0}
    out={"n":len(xs),"mean_r":round(sum(x["realized_r"] for x in xs)/len(xs),3),
      "median_r":round(float(pd.Series([x["realized_r"] for x in xs]).median()),3),
      "stops":sum(x["exit_reason"]=="STOP" for x in xs),
      "measured_target_hits":sum(x["exit_reason"]=="MEASURED_TARGET" for x in xs)}
    for k in FIXED_R:out[f"hit_{k}r_before_stop"]=sum(x["fixed_r_before_stop"][str(k)] for x in xs)
    return out

def study(folder):
    folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());obs=[]
    for sym in UNIVERSE:
        if sym not in m.get("symbols",{}) or "1d" not in m["symbols"][sym]:continue
        d=load(folder,m,sym)
        if len(d)<600:continue
        wd=weekly(d)
        last=pd.Timestamp(d.session_date.iloc[-1])
        completed_friday=last-pd.Timedelta(days=(last.weekday()-4)%7)
        # If the source ends on Friday, that daily bar is treated as completed by the collector contract.
        wd=wd[wd.session_date<=completed_friday].reset_index(drop=True);wa=atr(wd,14)
        last_event=-999
        for i in range(65,len(wd)-1):
            cs=[detect(wd,i,wa,w) for w in WINDOWS];cs=[p for p in cs if p]
            if not cs:continue
            p=min(cs,key=lambda z:z["window"]);b=wd.iloc[i];prev=wd.iloc[i-1];side=None;boundary=None
            if b.Close>p["upper"] and prev.Close<=p["upper"]:side="LONG";boundary=p["upper"]
            elif b.Close<p["lower"] and prev.Close>=p["lower"]:side="SHORT";boundary=p["lower"]
            if not side or i-last_event<8:continue
            e=i+1;price=float(wd.Open.iloc[e]);av=float(wa.iloc[i])
            stop=max(float(b.Low),boundary-.5*av) if side=="LONG" else min(float(b.High),boundary+.5*av)
            ow=outcome(wd,e,price,stop,p["height"],side,WEEK_HORIZON,price*FRICTION_BPS/10000)
            if not ow:continue
            mt=daily_retest_entry(d,b.session_date,boundary,side,p["height"])
            obs.append({"symbol":sym,"breakout_week":str(pd.Timestamp(b.session_date).date()),"side":side,
              "window":p["window"],"compression":round(p["compression"],3),"r2_high":round(p["r2_high"],3),
              "r2_low":round(p["r2_low"],3),"weekly":ow,"weekly_context_daily_retest":mt})
            last_event=i
    obs.sort(key=lambda x:(x["breakout_week"],x["symbol"]))
    n=len(obs);a=int(n*.6);b=int(n*.8)
    return {"status":"RESEARCH_ONLY","hypothesis_version":"weekly-triangle-mtf-v2-corrected-2026-09-30",
      "rules":{"windows_weeks":WINDOWS,"pivot":PIVOT,"min_touches":MIN_TOUCH,"min_r2":MIN_R2,
       "max_compression":MAX_COMPRESSION,"weekly_entry":"next week open after close-confirmed breakout",
       "daily_variant":"within 10 sessions after completed weekly breakout: boundary retest + reclaim + one-day momentum; enter next daily open",
       "same_bar_ambiguity":"STOP_FIRST","friction_bps":FRICTION_BPS,"weekly_horizon":WEEK_HORIZON,
       "daily_horizon":DAILY_HORIZON,"formation_height":"fitted width at earliest selected confirmed pivot; no backward extrapolation"},
      "splits":{"train":{"start":0,"end":a},"validation":{"start":a,"end":b},"final_test":{"start":b,"end":n}},
      "summary":{"weekly":{"train":summary(obs[:a],"weekly"),"validation":summary(obs[a:b],"weekly"),"final_test":summary(obs[b:],"weekly")},
       "weekly_context_daily_retest":{"train":summary(obs[:a],"weekly_context_daily_retest"),
       "validation":summary(obs[a:b],"weekly_context_daily_retest"),"final_test":summary(obs[b:],"weekly_context_daily_retest")}},
      "observations":obs,
      "note":"Corrected frozen baseline. v1 is invalid and must not be used as evidence: it failed to exit at stops and could credit targets on ambiguous stop bars."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/weekly_pattern_study.json");a=p.parse_args()
    r=stamp(study(a.folder),"weekly_pattern_mtf_v2",a.folder,model_version="rules-v2-corrected-2026-09-30")
    o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n")
    print("WEEKLY_PATTERN",len(r["observations"]),"observations")
