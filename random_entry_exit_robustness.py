#!/usr/bin/env python3
"""Pre-registered robustness attack on random-entry exit result. Research only."""
import argparse,json,math,random
from pathlib import Path
import pandas as pd
from research_safety import stamp,set_reproducible

SEEDS=(101,307,911,1729,4099,7919,12011,18013,25013,32003)
SYMS=("SP500","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","INVESTOR_B","VOLVO_B","ATLAS_A","ABB",
"NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META")
EXITS=("trail20","be2_trail20")
FRICTIONS=(20,50,100)
H=120;SPACING=20;STOP_ATR=1.5

def load(folder,m,s):
 d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date").reset_index(drop=True)
 for c in ("Open","High","Low","Close"):d[c]=pd.to_numeric(d[c],errors="raise")
 return d
def atr(d,i):
 p=d.iloc[:i];c=p.Close.shift();return float(pd.concat([p.High-p.Low,(p.High-c).abs(),(p.Low-c).abs()],axis=1).max(axis=1).tail(20).mean())
def sim(d,i,side,a,ex,bps):
 e=float(d.Open.iloc[i]);sgn=1 if side=="LONG" else -1;fr=e*bps/10000;dist=STOP_ATR*a;risk=dist+fr
 if e<=0 or risk<=0:return None
 stop=e-sgn*dist;exitp=None
 for j in range(i,min(i+H,len(d))):
  q=d.iloc[j];o,h,l=map(float,(q.Open,q.High,q.Low));fav=(h-e if sgn==1 else e-l)/risk
  if (l<=stop if sgn==1 else h>=stop):exitp=min(o,stop) if sgn==1 else max(o,stop);break
  if ex=="be2_trail20" and fav>=2:stop=max(stop,e) if sgn==1 else min(stop,e)
  if j>=i+20:
   tr=float(d.Low.iloc[j-20:j].min()) if sgn==1 else float(d.High.iloc[j-20:j].max())
   stop=max(stop,tr) if sgn==1 else min(stop,tr)
 if exitp is None:exitp=float(d.Close.iloc[min(i+H-1,len(d)-1)])
 return ((exitp-e)*sgn-fr)/risk

def mean(xs):return round(sum(xs)/len(xs),3) if xs else None
def study(folder):
 set_reproducible(1729);folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());data={}
 for s in SYMS:
  if s in m.get("symbols",{}):
   d=load(folder,m,s)
   if len(d)>=800:data[s]=d
 # Freeze common chronological boundaries from available history, independent of outcomes.
 alldates=sorted(set(str(x.date()) for d in data.values() for x in d.session_date.iloc[260:-H]))
 va=alldates[int(len(alldates)*.6)];te=alldates[int(len(alldates)*.8)]
 rows=[]
 for seed in SEEDS:
  for si,(s,d) in enumerate(data.items()):
   rng=random.Random(seed+si*1009);off=rng.randrange(SPACING)
   for i in range(260+off,len(d)-H,SPACING):
    date=str(d.session_date.iloc[i].date())
    if date<te:continue
    a=atr(d,i)
    if not math.isfinite(a) or a<=0:continue
    side="LONG" if rng.random()<.5 else "SHORT"
    for bps in FRICTIONS:
     for ex in EXITS:
      r=sim(d,i,side,a,ex,bps)
      if r is not None:rows.append({"seed":seed,"symbol":s,"side":side,"bps":bps,"exit":ex,"r":r})
 summary={}
 for bps in FRICTIONS:
  summary[str(bps)]={}
  for ex in EXITS:
   seedmeans=[]
   for seed in SEEDS:
    q=[x["r"] for x in rows if x["bps"]==bps and x["exit"]==ex and x["seed"]==seed];seedmeans.append(mean(q))
   q=[x["r"] for x in rows if x["bps"]==bps and x["exit"]==ex]
   summary[str(bps)][ex]={"n":len(q),"pooled_mean_r":mean(q),"seed_mean_r":seedmeans,
    "positive_seeds":sum(x>0 for x in seedmeans if x is not None),"min_seed":min(seedmeans),"max_seed":max(seedmeans)}
 by_side={};by_symbol={}
 for ex in EXITS:
  by_side[ex]={side:mean([x["r"] for x in rows if x["bps"]==20 and x["exit"]==ex and x["side"]==side]) for side in ("LONG","SHORT")}
  by_symbol[ex]={s:mean([x["r"] for x in rows if x["bps"]==20 and x["exit"]==ex and x["symbol"]==s]) for s in data}
 return {"status":"RESEARCH_ONLY","hypothesis_version":"random-exit-robustness-v1-frozen-2026-09-30",
 "preregistered":{"seeds":SEEDS,"exits":EXITS,"friction_bps":FRICTIONS,"spacing":SPACING,"stop_atr":STOP_ATR,"horizon":H},
 "final_test_start":te,"robustness":summary,"side_attribution_20bps":by_side,"symbol_attribution_20bps":by_symbol,
 "note":"Falsification pass only. Parameters frozen before inspection. No execution or candidate promotion."}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/random_entry_exit_robustness.json");a=p.parse_args()
 r=stamp(study(a.folder),"random_entry_exit_robustness",a.folder,model_version="robustness-v1-frozen-2026-09-30")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(json.dumps(r["robustness"],separators=(",",":")))
