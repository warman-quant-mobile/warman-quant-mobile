#!/usr/bin/env python3
"""Frozen weekly triangle + weekly-context/daily-entry research. No orders."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from research_safety import stamp

WINDOWS=(20,40,60); PIVOT=2; MIN_TOUCH=3; MIN_R2=.65; MAX_COMPRESSION=.70
FRICTION_BPS=20; WEEK_HORIZON=26; DAILY_HORIZON=130
UNIVERSE=("OMXS30","DAX","SP500","NASDAQ100","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","INVESTOR_B","VOLVO_B","ATLAS_A","ABB","NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META","BITCOIN","ETHEREUM","SOLANA")

def load(folder,m,s):
    d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date")
    for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="raise")
    return d.drop_duplicates("session_date").reset_index(drop=True)

def weekly(d):
    # W-FRI labels completed weeks only; caller drops the current/incomplete week.
    x=d.set_index("session_date").resample("W-FRI").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
    return x

def atr(d,n=20):
    c=d.Close
    return pd.concat([d.High-d.Low,(d.High-c.shift()).abs(),(d.Low-c.shift()).abs()],axis=1).max(axis=1).rolling(n).mean()

def piv(d,end,w):
    a=max(0,end-w); hs=[];ls=[]
    for i in range(a+PIVOT,end-PIVOT):
        if d.High.iloc[i]>=d.High.iloc[i-PIVOT:i+PIVOT+1].max(): hs.append(i)
        if d.Low.iloc[i]<=d.Low.iloc[i-PIVOT:i+PIVOT+1].min(): ls.append(i)
    return hs[-6:],ls[-6:]

def fit(idx,v):
    if len(idx)<MIN_TOUCH:return None
    x=pd.Series(idx[-MIN_TOUCH:],dtype=float); y=pd.Series([v.iloc[i] for i in idx[-MIN_TOUCH:]],dtype=float)
    den=((x-x.mean())**2).sum()
    if den<=0:return None
    s=float(((x-x.mean())*(y-y.mean())).sum()/den); b=float(y.mean()-s*x.mean())
    ss=((y-y.mean())**2).sum(); r2=1. if ss==0 else 1-float(((y-(s*x+b))**2).sum()/ss)
    return s,b,r2

def detect(wd,i,a,w):
    hs,ls=piv(wd,i,w); u=fit(hs,wd.High); l=fit(ls,wd.Low)
    if not u or not l or u[2]<MIN_R2 or l[2]<MIN_R2:return None
    start=max(0,i-w); u0=u[0]*start+u[1]; l0=l[0]*start+l[1]; u1=u[0]*(i-1)+u[1]; l1=l[0]*(i-1)+l[1]
    width0=u0-l0; width1=u1-l1
    if width0<=0 or width1<=0 or width1/width0>MAX_COMPRESSION:return None
    av=float(a.iloc[i-1])
    if not math.isfinite(av) or av<=0:return None
    su=u[0]/av; sl=l[0]/av
    if not ((su<-.03 and sl>.03) or (abs(su)<=.08 and sl>.03) or (su<-.03 and abs(sl)<=.08)):return None
    return {"upper":u[0]*i+u[1],"lower":l[0]*i+l[1],"height":width0,"compression":width1/width0,"r2_high":u[2],"r2_low":l[2],"window":w}

def outcome(d,e,price,stop,height,side,horizon,friction):
    sign=1 if side=="LONG" else -1; risk=abs(price-stop)+friction
    if risk<=0:return None
    mfe=0.; mae=0.; first={str(k):False for k in (3,5,10,15,20)}; stop_before={str(k):False for k in (3,5,10,15,20)}; stopped=False
    end=min(e+horizon,len(d))
    for j in range(e,end):
        q=d.iloc[j]; fav=(float(q.High)-price if side=="LONG" else price-float(q.Low))-friction
        adv=(price-float(q.Low) if side=="LONG" else float(q.High)-price)+friction
        mfe=max(mfe,fav/risk); mae=max(mae,adv/risk)
        hitstop=float(q.Low)<=stop if side=="LONG" else float(q.High)>=stop
        for k in (3,5,10,15,20):
            if not first[str(k)] and mfe>=k: first[str(k)]=True; stop_before[str(k)]=not stopped
        if hitstop: stopped=True
    close=float(d.Close.iloc[end-1]); rr=((close-price)*sign-friction)/risk
    return {"risk":risk,"realized_r":round(rr,3),"mfe_r":round(mfe,3),"mae_r":round(mae,3),"hit_before_stop":stop_before}

def study(folder):
    folder=Path(folder); m=json.loads((folder/"manifest.json").read_text()); obs=[]
    manifest_time=pd.to_datetime(m.get("generated_at_utc") or m.get("generated_at"),utc=True,errors="coerce")
    for sym in UNIVERSE:
        if sym not in m.get("symbols",{}) or "1d" not in m["symbols"][sym]:continue
        d=load(folder,m,sym)
        if len(d)<600:continue
        wd=weekly(d)
        # Never use an unfinished final week: retain only weekly labels <= last daily date's prior Friday.
        last=pd.Timestamp(d.session_date.iloc[-1]); completed_friday=last-pd.Timedelta(days=(last.weekday()-4)%7)
        if last.weekday()!=4: completed_friday-=pd.Timedelta(days=7)
        wd=wd[wd.session_date<=completed_friday].reset_index(drop=True); wa=atr(wd,14)
        last_event=-999
        for i in range(65,len(wd)-1):
            candidates=[detect(wd,i,wa,w) for w in WINDOWS]; candidates=[p for p in candidates if p]
            if not candidates:continue
            p=min(candidates,key=lambda z:z["window"]) # frozen deterministic tie-break
            b=wd.iloc[i]; prev=wd.iloc[i-1]; side=None; boundary=None
            if b.Close>p["upper"] and prev.Close<=p["upper"]:side="LONG";boundary=p["upper"]
            elif b.Close<p["lower"] and prev.Close>=p["lower"]:side="SHORT";boundary=p["lower"]
            if not side or i-last_event<8:continue
            e=i+1; price=float(wd.Open.iloc[e]); av=float(wa.iloc[i]); sign=1 if side=="LONG" else -1
            stop=max(float(b.Low),boundary-.5*av) if side=="LONG" else min(float(b.High),boundary+.5*av)
            friction=price*FRICTION_BPS/10000
            ow=outcome(wd,e,price,stop,p["height"],side,WEEK_HORIZON,friction)
            if not ow:continue
            # Daily entry variant: only daily bars strictly after the completed breakout week.
            after=d.index[d.session_date>pd.Timestamp(b.session_date)].tolist()
            mt=None
            if after:
                de=after[0]; da=atr(d,20); dav=float(da.iloc[de-1]) if de>0 else float("nan")
                if math.isfinite(dav) and dav>0:
                    # Objective next-day entry, daily structural risk; no future daily trigger information.
                    dp=float(d.Open.iloc[de]); ds=dp-sign*dav
                    mt=outcome(d,de,dp,ds,p["height"],side,DAILY_HORIZON,dp*FRICTION_BPS/10000)
            obs.append({"symbol":sym,"breakout_week":str(pd.Timestamp(b.session_date).date()),"side":side,
              "window":p["window"],"compression":round(p["compression"],3),"r2_high":round(p["r2_high"],3),"r2_low":round(p["r2_low"],3),
              "weekly":ow,"weekly_context_daily_entry":mt})
            last_event=i
    obs.sort(key=lambda x:(x["breakout_week"],x["symbol"]))
    n=len(obs); cut1=int(n*.6); cut2=int(n*.8)
    def summary(a,key):
        xs=[x[key] for x in a if x.get(key)]
        if not xs:return {"n":0}
        return {"n":len(xs),"mean_r":round(sum(x["realized_r"] for x in xs)/len(xs),3),
          "median_r":round(float(pd.Series([x["realized_r"] for x in xs]).median()),3),
          "hit_5r_before_stop":sum(x["hit_before_stop"]["5"] for x in xs),
          "hit_10r_before_stop":sum(x["hit_before_stop"]["10"] for x in xs),
          "hit_15r_before_stop":sum(x["hit_before_stop"]["15"] for x in xs),
          "hit_20r_before_stop":sum(x["hit_before_stop"]["20"] for x in xs)}
    return {"status":"RESEARCH_ONLY","hypothesis_version":"weekly-triangle-mtf-v1-frozen-2026-09-30",
      "rules":{"windows_weeks":WINDOWS,"pivot":PIVOT,"min_touches":MIN_TOUCH,"min_r2":MIN_R2,"max_compression":MAX_COMPRESSION,
       "weekly_entry":"next completed week open after close-confirmed breakout","daily_variant":"first daily open strictly after completed breakout week; 1 ATR structural research stop",
       "friction_bps":FRICTION_BPS,"weekly_horizon":WEEK_HORIZON,"daily_horizon":DAILY_HORIZON},
      "splits":{"train":{"start":0,"end":cut1},"validation":{"start":cut1,"end":cut2},"final_test":{"start":cut2,"end":n}},
      "summary":{"weekly":{"train":summary(obs[:cut1],"weekly"),"validation":summary(obs[cut1:cut2],"weekly"),"final_test":summary(obs[cut2:],"weekly")},
       "weekly_context_daily_entry":{"train":summary(obs[:cut1],"weekly_context_daily_entry"),"validation":summary(obs[cut1:cut2],"weekly_context_daily_entry"),"final_test":summary(obs[cut2:],"weekly_context_daily_entry")}},
      "observations":obs,"note":"Frozen deterministic baseline. Final test is reported once and must not be used for tuning."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/weekly_pattern_study.json");a=p.parse_args()
    r=stamp(study(a.folder),"weekly_pattern_mtf_v1",a.folder,model_version="rules-v1-frozen-2026-09-30")
    o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n")
    print("WEEKLY_PATTERN",len(r["observations"]),"observations")
