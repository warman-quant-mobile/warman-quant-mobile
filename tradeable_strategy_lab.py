#!/usr/bin/env python3
"""Tradeable strategy validation lab: pooled liquid/Nordnet-searchable underlyings, chronological OOS."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from research_safety import stamp

SYMS=("SP500","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","INVESTOR_B","VOLVO_B","ATLAS_A","ABB",
"NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META")
BPS=20; H=60; RULES=("turtle55","rsi2","failed20")
STOPS=(1.0,1.5,2.0)

def load(folder,m,s):
 d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date").reset_index(drop=True)
 for c in ("Open","High","Low","Close"):d[c]=pd.to_numeric(d[c],errors="raise")
 return d

def atr(df,i):
 p=df.iloc[:i];c=p.Close.shift()
 return float(pd.concat([p.High-p.Low,(p.High-c).abs(),(p.Low-c).abs()],axis=1).max(axis=1).tail(20).mean())

def signal(df,i,rule):
 p=df.iloc[:i];c=p.Close;h=p.High;l=p.Low;last=float(c.iloc[-1]);prev=float(c.iloc[-2]);ma200=float(c.tail(200).mean())
 if rule=="turtle55":
  return "LONG" if last>float(h.iloc[-56:-1].max()) and last>ma200 else ("SHORT" if last<float(l.iloc[-56:-1].min()) and last<ma200 else None)
 if rule=="rsi2":
  ret=c.diff();g=ret.clip(lower=0).tail(2).mean();loss=(-ret.clip(upper=0)).tail(2).mean();rsi=100 if loss==0 else 100-100/(1+g/loss)
  return "LONG" if rsi<10 and last>ma200 else None
 if rule=="failed20":
  hi=float(h.iloc[-21:-1].max());lo=float(l.iloc[-21:-1].min())
  return "SHORT" if float(h.iloc[-1])>hi and last<hi and last<prev else ("LONG" if float(l.iloc[-1])<lo and last>lo and last>prev else None)

def sim(df,i,side,a,mult):
 entry=float(df.Open.iloc[i]);fr=entry*BPS/10000;dist=mult*a;sgn=1 if side=="LONG" else -1;stop=entry-sgn*dist;risk=dist+fr
 if entry<=0 or stop<=0 or risk<=0:return None
 mfe=0.;exitp=None;reason="TIMEOUT"
 for j in range(i,min(i+H,len(df))):
  q=df.iloc[j];o,h,l=map(float,(q.Open,q.High,q.Low))
  mfe=max(mfe,(h-entry if sgn==1 else entry-l)/risk)
  if (l<=stop if sgn==1 else h>=stop):
   exitp=min(o,stop) if sgn==1 else max(o,stop);reason="STOP";break
  if j>=i+20:
   trail=float(df.Low.iloc[j-20:j].min()) if sgn==1 else float(df.High.iloc[j-20:j].max())
   if (l<=trail if sgn==1 else h>=trail):
    exitp=min(o,trail) if sgn==1 else max(o,trail);reason="TRAIL";break
 if exitp is None:exitp=float(df.Close.iloc[min(i+H-1,len(df)-1)])
 return {"r":((exitp-entry)*sgn-fr)/risk,"mfe":mfe,"reason":reason}

def stats(xs):
 if not xs:return {"n":0}
 rs=[x["r"] for x in xs]
 return {"n":len(xs),"mean_r":round(sum(rs)/len(rs),3),"median_r":round(float(pd.Series(rs).median()),3),
 "win_rate":round(sum(r>0 for r in rs)/len(rs),3),"hit3":sum(x["mfe"]>=3 for x in xs),"hit5":sum(x["mfe"]>=5 for x in xs),
 "stops":sum(x["reason"]=="STOP" for x in xs)}

def study(folder):
 folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());rows=[];current=[]
 for s in SYMS:
  if s not in m.get("symbols",{}):continue
  d=load(folder,m,s)
  if len(d)<500:continue
  for rule in RULES:
   for mult in STOPS:
    ev=[];nextok=0
    for i in range(254,len(d)-H):
     if i<nextok:continue
     side=signal(d,i,rule)
     if not side:continue
     a=atr(d,i)
     if not math.isfinite(a) or a<=0:continue
     z=sim(d,i,side,a,mult)
     if z: ev.append({"date":str(d.session_date.iloc[i].date()),"symbol":s,"rule":rule,"stop_atr":mult,**z});nextok=i+H
    rows.extend(ev)
   # current signal is rule-level; stop choice comes only from training/validation, never current data
   i=len(d);side=signal(d,i,rule)
   if side:current.append({"symbol":s,"rule":rule,"side":side,"signal_date":str(d.session_date.iloc[-1].date())})
 # Global chronological split avoids per-symbol tiny OOS slices.
 rows.sort(key=lambda x:(x["date"],x["symbol"],x["rule"],x["stop_atr"]))
 dates=sorted(set(x["date"] for x in rows));a=dates[int(len(dates)*.6)] if dates else "";b=dates[int(len(dates)*.8)] if dates else ""
 combos={}
 for rule in RULES:
  combos[rule]={}
  for mult in STOPS:
   q=[x for x in rows if x["rule"]==rule and x["stop_atr"]==mult]
   combos[rule][str(mult)]={"train":stats([x for x in q if x["date"]<a]),"validation":stats([x for x in q if a<=x["date"]<b]),
    "final_test":stats([x for x in q if x["date"]>=b])}
 return {"status":"RESEARCH_ONLY","version":"tradeable-validation-v1","split_dates":{"validation_start":a,"final_test_start":b},
 "universe":SYMS,"rules":RULES,"stop_atr":STOPS,"results":combos,"current_rule_signals":current,
 "note":"Predeclared pooled validation. 20bps proxy friction, next-open entry, conservative stop-first, 20-day trailing exit after day 20, 60-day horizon. Current rule signals are NOT trade proposals; Nordnet execution gate remains mandatory."}

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/tradeable_strategy_lab.json");a=p.parse_args()
 r=stamp(study(a.folder),"tradeable_strategy_lab",a.folder,model_version="v1")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n")
 print("TRADEABLE_LAB",json.dumps(r["results"],separators=(",",":")))
