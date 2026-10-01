#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
def cg(rs):
 w=np.prod([1+r for r in rs]); return float(w**(1/len(rs))-1) if len(rs) and w>0 else -1.0
def one(x):
 a=x["annual"]; s=[z["net_return"] for z in a]; b=[z["equal_weight_net"] for z in a]; bc=cg(b)
 grid={}
 for h in [0,.01,.02,.03,.04,.05,.075,.10]:
  v=cg([r-h for r in s]);grid[str(h)]={"cagr":v,"active":v-bc}
 lo,hi=0.,.25
 for _ in range(50):
  m=(lo+hi)/2
  if cg([r-m for r in s])>bc:lo=m
  else:hi=m
 return {"strategy_cagr":cg(s),"benchmark_cagr":bc,"active_cagr":cg(s)-bc,"break_even_annual_haircut":(lo+hi)/2,"haircuts":grid}
def main():
 p=argparse.ArgumentParser();p.add_argument("--research",required=True);p.add_argument("--holdout",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 r=json.load(open(a.research));h=json.load(open(a.holdout))
 o={"status":"FROZEN_ADVERSARIAL_SENSITIVITY","note":"No refit. Annual haircut is applied only to selected portfolio as an adverse bound for omitted delisting/survivorship/model friction.","research":{},"holdout":{}}
 for k in ("top5","top10","top20"):
  o["research"][k]=one(r["results"][k]);o["holdout"][k]=one(h["results"][k])
 Path(a.out).write_text(json.dumps(o,indent=2)+"\n");print(json.dumps(o))
if __name__=="__main__":main()
