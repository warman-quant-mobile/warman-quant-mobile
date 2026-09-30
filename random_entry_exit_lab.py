#!/usr/bin/env python3
"""Frozen random-entry / exit-engine control experiment. Research only; never executes orders."""
import argparse,json,math,random
from pathlib import Path
import pandas as pd
from research_safety import stamp,set_reproducible

SEED=1729
SYMS=("SP500","GOLD_FUT","SILVER_FUT","WTI_FUT","BRENT_FUT","INVESTOR_B","VOLVO_B","ATLAS_A","ABB",
"NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META")
BPS=20
H=120
SPACING=20
STOP_ATR=1.5
EXITS=("fixed5","fixed10","trail20","be2_trail20","partial3_trail20")

def load(folder,m,s):
 d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date").reset_index(drop=True)
 for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="raise")
 return d

def atr(df,i):
 p=df.iloc[:i]; c=p.Close.shift()
 tr=pd.concat([p.High-p.Low,(p.High-c).abs(),(p.Low-c).abs()],axis=1).max(axis=1)
 return float(tr.tail(20).mean())

def simulate(df,i,side,a,exit_rule):
 entry=float(df.Open.iloc[i]); sgn=1 if side=="LONG" else -1
 friction=entry*BPS/10000; dist=STOP_ATR*a; risk=dist+friction
 if entry<=0 or risk<=0:return None
 stop=entry-sgn*dist; initial_stop=stop; peak=0.; trough=0.; partial=False; banked=0.
 exitp=None; reason="TIMEOUT"
 for j in range(i,min(i+H,len(df))):
  q=df.iloc[j]; o,h,l=map(float,(q.Open,q.High,q.Low))
  fav=(h-entry if sgn==1 else entry-l)/risk; adv=(entry-l if sgn==1 else h-entry)/risk
  peak=max(peak,fav); trough=max(trough,adv)
  stop_hit=(l<=stop if sgn==1 else h>=stop)
  if stop_hit:
   exitp=min(o,stop) if sgn==1 else max(o,stop); reason="STOP"; break
  if exit_rule=="fixed5" and fav>=5: exitp=entry+sgn*5*risk;reason="TARGET5";break
  if exit_rule=="fixed10" and fav>=10: exitp=entry+sgn*10*risk;reason="TARGET10";break
  if exit_rule=="be2_trail20" and fav>=2:
   stop=max(stop,entry) if sgn==1 else min(stop,entry)
  if exit_rule=="partial3_trail20" and fav>=3 and not partial:
   partial=True;banked=1.5 # half position banked at +3R
   stop=max(stop,entry) if sgn==1 else min(stop,entry)
  if exit_rule in ("trail20","be2_trail20","partial3_trail20") and j>=i+20:
   trail=float(df.Low.iloc[j-20:j].min()) if sgn==1 else float(df.High.iloc[j-20:j].max())
   stop=max(stop,trail) if sgn==1 else min(stop,trail)
 if exitp is None: exitp=float(df.Close.iloc[min(i+H-1,len(df)-1)])
 raw=((exitp-entry)*sgn-friction)/risk
 r=banked+0.5*raw if partial else raw
 return {"r":r,"mfe":peak,"mae":trough,"reason":reason}

def stats(xs):
 if not xs:return {"n":0}
 rs=[x["r"] for x in xs]
 return {"n":len(xs),"mean_r":round(sum(rs)/len(rs),3),"median_r":round(float(pd.Series(rs).median()),3),
 "win_rate":round(sum(r>0 for r in rs)/len(rs),3),"loss_rate":round(sum(r<0 for r in rs)/len(rs),3),
 "hit3_mfe":round(sum(x["mfe"]>=3 for x in xs)/len(xs),3),"hit5_mfe":round(sum(x["mfe"]>=5 for x in xs)/len(xs),3),
 "hit10_mfe":round(sum(x["mfe"]>=10 for x in xs)/len(xs),3),
 "p10_r":round(float(pd.Series(rs).quantile(.1)),3),"p90_r":round(float(pd.Series(rs).quantile(.9)),3)}

def study(folder):
 set_reproducible(SEED); folder=Path(folder);m=json.loads((folder/"manifest.json").read_text());rows=[]
 # Pre-registered deterministic pseudo-random control: one entry per 20 completed sessions,
 # symbol-specific RNG, random side. Entry is next open and never depends on future bars.
 for si,s in enumerate(SYMS):
  if s not in m.get("symbols",{}):continue
  d=load(folder,m,s)
  if len(d)<800:continue
  rng=random.Random(SEED+si*1009); offset=rng.randrange(SPACING)
  for i in range(260+offset,len(d)-H,SPACING):
   a=atr(d,i)
   if not math.isfinite(a) or a<=0:continue
   side="LONG" if rng.random()<.5 else "SHORT"
   for ex in EXITS:
    z=simulate(d,i,side,a,ex)
    if z:rows.append({"date":str(d.session_date.iloc[i].date()),"symbol":s,"side":side,"exit":ex,**z})
 dates=sorted(set(x["date"] for x in rows)); va=dates[int(len(dates)*.6)];te=dates[int(len(dates)*.8)]
 out={}
 for ex in EXITS:
  q=[x for x in rows if x["exit"]==ex]
  out[ex]={"train":stats([x for x in q if x["date"]<va]),"validation":stats([x for x in q if va<=x["date"]<te]),
           "final_test":stats([x for x in q if x["date"]>=te])}
 return {"status":"RESEARCH_ONLY","hypothesis_version":"random-entry-exit-v1-frozen-2026-09-30","seed":SEED,
 "rules":{"entry":"deterministic pseudo-random side every 20 sessions; next-open; no signal features","stop_atr":STOP_ATR,
 "horizon_days":H,"friction_bps":BPS,"exit_families":EXITS},
 "split_dates":{"validation_start":va,"final_test_start":te},"results":out,
 "note":"Control experiment for entry-vs-exit attribution. Exit family frozen before results. Final test is descriptive and must not be used to tune v1."}

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/random_entry_exit_lab.json");a=p.parse_args()
 r=stamp(study(a.folder),"random_entry_exit_lab",a.folder,model_version="exit-v1-frozen-2026-09-30")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n")
 print("RANDOM_EXIT_LAB",json.dumps(r["results"],separators=(",",":")))
