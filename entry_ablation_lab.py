#!/usr/bin/env python3
"""Frozen entry-information ablation under identical convex exit. Research only."""
import argparse,json,math,random
from pathlib import Path
import pandas as pd
from research_safety import stamp,set_reproducible
SEEDS=(101,307,911,1729,4099,7919,12011,18013,25013,32003)
SYMS=("SP500","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","INVESTOR_B","VOLVO_B","ATLAS_A","ABB","NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META")
MODES=("random_side","long_only","trend200")
BPS=(20,50);H=120;SPACING=20;STOP_ATR=1.5
def load(folder,m,s):
 d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date").reset_index(drop=True)
 for c in ("Open","High","Low","Close"):d[c]=pd.to_numeric(d[c],errors="raise")
 return d
def atr(d,i):
 p=d.iloc[:i];c=p.Close.shift();return float(pd.concat([p.High-p.Low,(p.High-c).abs(),(p.Low-c).abs()],axis=1).max(axis=1).tail(20).mean())
def side_for(d,i,mode,rng):
 if mode=="random_side":return "LONG" if rng.random()<.5 else "SHORT"
 if mode=="long_only":return "LONG"
 ma=float(d.Close.iloc[i-200:i].mean())
 return "LONG" if float(d.Close.iloc[i-1])>ma else "SHORT"
def sim(d,i,side,a,bps):
 e=float(d.Open.iloc[i]);sgn=1 if side=="LONG" else -1;fr=e*bps/10000;dist=STOP_ATR*a;risk=dist+fr
 if e<=0 or risk<=0:return None
 stop=e-sgn*dist;exitp=None
 for j in range(i,min(i+H,len(d))):
  q=d.iloc[j];o,h,l=map(float,(q.Open,q.High,q.Low))
  if (l<=stop if sgn==1 else h>=stop):exitp=min(o,stop) if sgn==1 else max(o,stop);break
  if j>=i+20:
   tr=float(d.Low.iloc[j-20:j].min()) if sgn==1 else float(d.High.iloc[j-20:j].max())
   stop=max(stop,tr) if sgn==1 else min(stop,tr)
 if exitp is None:exitp=float(d.Close.iloc[min(i+H-1,len(d)-1)])
 return ((exitp-e)*sgn-fr)/risk
def avg(x):return round(sum(x)/len(x),3) if x else None
def study(folder):
 set_reproducible(1729);folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());data={}
 for s in SYMS:
  if s in m.get("symbols",{}):
   d=load(folder,m,s)
   if len(d)>=800:data[s]=d
 dates=sorted(set(str(x.date()) for d in data.values() for x in d.session_date.iloc[260:-H]));te=dates[int(len(dates)*.8)]
 rows=[]
 for seed in SEEDS:
  for si,(s,d) in enumerate(data.items()):
   base=random.Random(seed+si*1009);off=base.randrange(SPACING)
   for i in range(260+off,len(d)-H,SPACING):
    if str(d.session_date.iloc[i].date())<te:continue
    a=atr(d,i)
    if not math.isfinite(a) or a<=0:continue
    for mode in MODES:
     rng=random.Random(seed+si*1009+i*17+MODES.index(mode))
     side=side_for(d,i,mode,rng)
     for b in BPS:
      r=sim(d,i,side,a,b)
      if r is not None:rows.append({"seed":seed,"symbol":s,"mode":mode,"bps":b,"r":r})
 out={}
 for b in BPS:
  out[str(b)]={}
  for mode in MODES:
   sm=[avg([x["r"] for x in rows if x["bps"]==b and x["mode"]==mode and x["seed"]==z]) for z in SEEDS]
   q=[x["r"] for x in rows if x["bps"]==b and x["mode"]==mode]
   out[str(b)][mode]={"n":len(q),"pooled_mean_r":avg(q),"seed_means":sm,"positive_seeds":sum(v>0 for v in sm)}
 bysym={mode:{s:avg([x["r"] for x in rows if x["bps"]==20 and x["mode"]==mode and x["symbol"]==s]) for s in data} for mode in MODES}
 return {"status":"RESEARCH_ONLY","hypothesis_version":"entry-ablation-v1-frozen-2026-09-30","final_test_start":te,
 "preregistered":{"modes":MODES,"seeds":SEEDS,"bps":BPS,"exit":"20-session trailing","stop_atr":STOP_ATR,"horizon":H,"spacing":SPACING},
 "results":out,"symbol_attribution_20bps":bysym,
 "note":"Entry-information ablation. Same convex exit for all modes. Frozen before results; no execution."}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/entry_ablation_lab.json");a=p.parse_args()
 r=stamp(study(a.folder),"entry_ablation_lab",a.folder,model_version="entry-ablation-v1-frozen-2026-09-30")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(json.dumps(r["results"],separators=(",",":")))
