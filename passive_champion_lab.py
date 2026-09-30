#!/usr/bin/env python3
"""Passive champion vs long-only convex challenger. Frozen before inspection. Research only."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from research_safety import stamp,set_reproducible
SYMS=("SP500","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","INVESTOR_B","VOLVO_B","ATLAS_A","ABB","NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META")
BPS=(20,50); STOP_ATR=1.5; TRAIL=20; H=120; COOLDOWN=0
def load(folder,m,s):
 d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date").reset_index(drop=True)
 for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="raise")
 return d
def atr(d,i):
 p=d.iloc[:i]; pc=p.Close.shift()
 tr=pd.concat([p.High-p.Low,(p.High-pc).abs(),(p.Low-pc).abs()],axis=1).max(axis=1)
 return float(tr.tail(20).mean())
def maxdd(eq):
 peak=eq.cummax(); dd=eq/peak-1; return float(dd.min())
def passive(d,start,bps):
 e=float(d.Open.iloc[start]); x=float(d.Close.iloc[-1]); f=bps/10000
 net=(x*(1-f))/(e*(1+f))-1
 eq=d.Close.iloc[start:].astype(float)/e
 return {"return":net,"max_drawdown":maxdd(eq),"exposure":1.0,"trades":1}
def convex(d,start,bps):
 f=bps/10000; cash=1.0; eq=[]; inpos=False; entry=stop=None; entry_i=None; trades=0; exposed=0
 i=start
 while i<len(d):
  if not inpos:
   a=atr(d,i)
   if not math.isfinite(a) or a<=0: eq.append(cash); i+=1; continue
   entry=float(d.Open.iloc[i]); stop=entry-STOP_ATR*a; entry_i=i; inpos=True; trades+=1
   cash*=1-f
  q=d.iloc[i]; o,h,l,c=map(float,(q.Open,q.High,q.Low,q.Close)); exposed+=1
  exitp=None
  if l<=stop: exitp=min(o,stop)
  elif i-entry_i>=H-1: exitp=c
  if exitp is not None:
   cash*=exitp/entry; cash*=1-f; inpos=False; entry=stop=entry_i=None; eq.append(cash); i+=1+COOLDOWN; continue
  if i-entry_i>=TRAIL:
   stop=max(stop,float(d.Low.iloc[i-TRAIL:i].min()))
  eq.append(cash*c/entry); i+=1
 if inpos:
  cash*=float(d.Close.iloc[-1])/entry; cash*=1-f
  if eq: eq[-1]=cash
 s=pd.Series(eq if eq else [1.0])
 return {"return":cash-1,"max_drawdown":maxdd(s),"exposure":exposed/max(1,len(d)-start),"trades":trades}
def cagr(ret,years): return (1+ret)**(1/years)-1 if ret>-1 and years>0 else None
def study(folder):
 set_reproducible(1729); folder=Path(folder); m=json.loads((folder/"manifest.json").read_text()); rows=[]
 for s in SYMS:
  if s not in m.get("symbols",{}): continue
  d=load(folder,m,s)
  if len(d)<800: continue
  start=max(260,int(len(d)*.8)); years=max((d.session_date.iloc[-1]-d.session_date.iloc[start]).days/365.25,.25)
  for b in BPS:
   p=passive(d,start,b); q=convex(d,start,b)
   rows.append({"symbol":s,"bps":b,"start":str(d.session_date.iloc[start].date()),"end":str(d.session_date.iloc[-1].date()),
    "passive_return":round(p["return"],4),"passive_cagr":round(cagr(p["return"],years),4),"passive_maxdd":round(p["max_drawdown"],4),
    "convex_return":round(q["return"],4),"convex_cagr":round(cagr(q["return"],years),4),"convex_maxdd":round(q["max_drawdown"],4),
    "convex_exposure":round(q["exposure"],4),"convex_trades":q["trades"],"cagr_delta":round(cagr(q["return"],years)-cagr(p["return"],years),4)})
 out={}
 for b in BPS:
  z=[x for x in rows if x["bps"]==b]
  out[str(b)]={"n":len(z),"convex_beats_passive_cagr":sum(x["cagr_delta"]>0 for x in z),
   "median_cagr_delta":round(pd.Series([x["cagr_delta"] for x in z]).median(),4),
   "mean_cagr_delta":round(pd.Series([x["cagr_delta"] for x in z]).mean(),4),
   "median_passive_cagr":round(pd.Series([x["passive_cagr"] for x in z]).median(),4),
   "median_convex_cagr":round(pd.Series([x["convex_cagr"] for x in z]).median(),4),
   "median_passive_maxdd":round(pd.Series([x["passive_maxdd"] for x in z]).median(),4),
   "median_convex_maxdd":round(pd.Series([x["convex_maxdd"] for x in z]).median(),4),
   "median_convex_exposure":round(pd.Series([x["convex_exposure"] for x in z]).median(),4)}
 return {"status":"RESEARCH_ONLY","hypothesis_version":"passive-champion-v1-frozen-2026-09-30",
 "preregistered":{"bps":BPS,"stop_atr":STOP_ATR,"trail_sessions":TRAIL,"max_horizon":H,"entry":"immediate long re-entry after exit","test":"last 20% per instrument"},
 "summary":out,"by_symbol":rows,"note":"Direct economic challenger test. No tuning from these results; no execution."}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/passive_champion_lab.json");a=p.parse_args()
 r=stamp(study(a.folder),"passive_champion_lab",a.folder,model_version="passive-champion-v1-frozen-2026-09-30")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(json.dumps(r["summary"],separators=(",",":")))
