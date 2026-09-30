#!/usr/bin/env python3
"""Frozen price-first Stock Picker baseline. Research only.
Tests whether a simple investable cross-sectional momentum/quality-proxy selector
earns the right to justify deeper point-in-time fundamental data work.
"""
import argparse,json,math
from pathlib import Path
import pandas as pd, numpy as np
from research_safety import stamp,set_reproducible

SYMS=("SP500","INVESTOR_B","VOLVO_B","ATLAS_A","ABB","NVIDIA","MICROSOFT","APPLE","TESLA","AMAZON","META")
TOPK=(3,5); BPS=(20,50); LOOKBACK=252; SKIP=21; VOLWIN=63; REBAL=21

def load(folder,m,s):
 d=pd.read_csv(Path(folder)/m["symbols"][s]["1d"]["file"],parse_dates=["session_date"]).sort_values("session_date")
 d=d.set_index("session_date")
 return d[["Open","Close"]].astype(float)

def study(folder):
 set_reproducible(1729); folder=Path(folder); m=json.loads((folder/"manifest.json").read_text())
 px={s:load(folder,m,s) for s in SYMS if s in m.get("symbols",{})}
 close=pd.concat({s:d.Close for s,d in px.items()},axis=1).sort_index().ffill(limit=3)
 rets=close.pct_change()
 dates=close.index
 start=max(LOOKBACK+SKIP, int(len(dates)*.6))
 val=int(len(dates)*.8)
 out={}
 for bps in BPS:
  for k in TOPK:
   wealth=1.; bench=1.; curve=[]; turns=[]; prev=set()
   picks=[]; test_picks=[]
   for i in range(start,len(dates)-REBAL,REBAL):
    hist=close.iloc[:i+1]
    mom=hist.iloc[-SKIP-1]/hist.iloc[-LOOKBACK-1]-1
    vol=rets.iloc[max(1,i-VOLWIN):i].std()*np.sqrt(252)
    score=(mom.rank(pct=True)+(-vol).rank(pct=True))/2
    eligible=score.dropna().sort_values(ascending=False)
    chosen=list(eligible.head(k).index)
    if len(chosen)<k: continue
    entry=i+1; exit_i=min(i+REBAL,len(dates)-1)
    gross=(close.iloc[exit_i][chosen]/close.iloc[entry][chosen]-1).mean()
    turn=1 if not prev else len(set(chosen)^prev)/(2*k)
    cost=turn*(2*bps/10000)
    wealth*=1+gross-cost
    universe=list(eligible.index)
    bgross=(close.iloc[exit_i][universe]/close.iloc[entry][universe]-1).mean()
    bench*=1+bgross-(2*bps/10000 if not prev else 0)
    row={"date":str(dates[entry].date()),"picks":chosen,"score":{s:round(float(score[s]),4) for s in chosen},"turnover":round(turn,3)}
    picks.append(row)
    if entry>=val:test_picks.append(row)
    prev=set(chosen);curve.append((dates[exit_i],wealth,bench));turns.append(turn)
   df=pd.DataFrame(curve,columns=["date","strategy","benchmark"]).set_index("date")
   # untouched final-test recomputation from curve level
   if len(df):
    cut=dates[val]; q=df[df.index>=cut]
    if len(q)>1:
     sr=q.strategy.iloc[-1]/q.strategy.iloc[0]-1;br=q.benchmark.iloc[-1]/q.benchmark.iloc[0]-1
     sdd=(q.strategy/q.strategy.cummax()-1).min();bdd=(q.benchmark/q.benchmark.cummax()-1).min()
    else: sr=br=sdd=bdd=float("nan")
   else: sr=br=sdd=bdd=float("nan")
   out[f"top{k}_{bps}bps"]={"final_test_return":round(float(sr),4),"benchmark_return":round(float(br),4),
    "excess_return":round(float(sr-br),4),"strategy_maxdd":round(float(sdd),4),"benchmark_maxdd":round(float(bdd),4),
    "mean_turnover":round(float(np.mean(turns)),4) if turns else None,"final_test_rebalances":len(test_picks),
    "final_test_picks":test_picks}
 return {"status":"RESEARCH_ONLY","hypothesis_version":"stock-picker-price-v1-frozen-2026-09-30",
 "preregistered":{"signal":"equal percentile rank of 12-1 momentum and inverse 63d volatility","topk":TOPK,"rebalance_sessions":REBAL,
 "cost_bps":BPS,"universe":"available named liquid equity proxies; SP500 retained as control candidate","split":"60/20/20 chronological; final 20 untouched"},
 "results":out,"limitations":["Price-first feasibility baseline; NOT point-in-time fundamental stock picking.","Current universe is small and survivorship-biased; cannot promote candidates.","Benchmark is equal-weight eligible universe, not Investor/Berkshire."],
 "execution":"BLOCKED_RESEARCH_ONLY"}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/stock_picker_price_v1.json");a=p.parse_args()
 r=stamp(study(a.folder),"stock_picker_price_v1",a.folder,model_version="stock-picker-price-v1-frozen-2026-09-30")
 o=Path(a.result);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,indent=2)+"\n");print(json.dumps({k:{x:y for x,y in v.items() if x!="final_test_picks"} for k,v in r["results"].items()},separators=(",",":")))
