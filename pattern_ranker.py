#!/usr/bin/env python3
"""Interpretable chronological ranker for pattern right-tail research. No orders."""
import argparse,json,math
from pathlib import Path
import pandas as pd
from research_safety import stamp,set_reproducible

FEATURES=("geometric_r","compression","r2_high","r2_low","slope_high_atr","slope_low_atr",
          "touches_high","touches_low","breakout_strength_atr","trend20_signed","gap_atr","atr_pct")
TARGETS=(5,10,15)
SEED=1729

def sigmoid(z): return 1/(1+math.exp(-max(-30,min(30,z))))

def fit_logit(X,y,epochs=500,lr=.05,l2=.02):
    n=len(y); p=len(FEATURES); w=[0.0]*(p+1)
    for _ in range(epochs):
        g=[0.0]*(p+1)
        for row,t in zip(X,y):
            pr=sigmoid(w[0]+sum(w[j+1]*row[j] for j in range(p))); e=pr-t;g[0]+=e
            for j in range(p):g[j+1]+=e*row[j]
        w[0]-=lr*g[0]/n
        for j in range(p):w[j+1]-=lr*(g[j+1]/n+l2*w[j+1])
    return w

def standardize(train, rows):
    mu=[];sd=[]
    for f in FEATURES:
        s=pd.Series([float(x[f]) for x in train]);mu.append(float(s.mean()));sd.append(max(float(s.std(ddof=0)),1e-9))
    return [[(float(x[f])-mu[j])/sd[j] for j,f in enumerate(FEATURES)] for x in rows],mu,sd

def metrics(rows,probs,k):
    if not rows:return {"n":0}
    y=[1 if x["mfe_r"]>=k else 0 for x in rows]
    b=sum((p-t)**2 for p,t in zip(probs,y))/len(y)
    ranked=sorted(zip(probs,rows),key=lambda z:z[0],reverse=True); q=max(1,len(ranked)//4);top=[x for _,x in ranked[:q]]
    return {"n":len(rows),"base_rate":round(sum(y)/len(y),4),"brier":round(b,4),
      "top_quartile_n":q,"top_quartile_hit_rate":round(sum(x["mfe_r"]>=k for x in top)/q,4),
      "top_quartile_mean_realized_r":round(sum(x["realized_r"] for x in top)/q,3),
      "top_quartile_median_realized_r":round(float(pd.Series([x["realized_r"] for x in top]).median()),3)}

def main(inp):
    d=json.loads(Path(inp).read_text());obs=sorted(d.get("observations",[]),key=lambda x:(x["date"],x["symbol"]))
    # Final 20% is never used for fitting or threshold/model selection. This script has one frozen model family.
    n=len(obs);a=int(n*.6);b=int(n*.8);train,val,test=obs[:a],obs[a:b],obs[b:]
    if len(train)<50:raise RuntimeError("BLOCKED: insufficient chronological training sample")
    Xtr,mu,sd=standardize(train,train)
    def transform(rows):return [[(float(x[f])-mu[j])/sd[j] for j,f in enumerate(FEATURES)] for x in rows]
    out={"status":"RESEARCH_ONLY","model":"fixed L2 logistic ranker","seed":SEED,"features":FEATURES,
         "split":{"train":len(train),"validation":len(val),"final_test":len(test),"rule":"60/20/20 chronological; final test untouched by fitting"},
         "targets":{},"warning":"Exploratory ranking only. Small tail-event counts; no execution or promotion."}
    for k in TARGETS:
        y=[1 if x["mfe_r"]>=k else 0 for x in train]
        if sum(y)<3 or sum(y)==len(y):out["targets"][str(k)]={"status":"INSUFFICIENT_POSITIVES","positives":sum(y)};continue
        w=fit_logit(Xtr,y)
        pred=lambda rows:[sigmoid(w[0]+sum(w[j+1]*z[j] for j in range(len(FEATURES)))) for z in transform(rows)]
        out["targets"][str(k)]={"train_positives":sum(y),"validation":metrics(val,pred(val),k),
          "final_test":metrics(test,pred(test),k),"coefficients":dict(zip(("intercept",)+FEATURES,[round(x,4) for x in w]))}
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--input",default="signals/pattern_geometry_study.json");p.add_argument("--folder",default="output");p.add_argument("--result",default="signals/pattern_ranker.json");a=p.parse_args()
    set_reproducible(SEED);r=stamp(main(a.input),"pattern_ranker",a.folder,model_version="logit-v1-frozen-2026-09-30")
    Path(a.result).write_text(json.dumps(r,indent=2)+"\n");print("PATTERN_RANKER",r["split"])
