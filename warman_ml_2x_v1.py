#!/usr/bin/env python3
"""Warman ML 2X: chronological ensemble classifier for >=2x within 5y; secondary 3x/5x."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from sklearn.ensemble import HistGradientBoostingClassifier,RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
from tenbagger_broad_oos_v1 import annual_series,last,last2,pct

FEATS=["rev_growth","rev_accel","op_growth","gross_growth","roa","fcf_margin","debt_assets","dilution","momentum12","momentum6","drawdown","log_assets","sales_assets"]
def row(c,t,dt,px):
 rev=annual_series(c,"revenue",dt); op=annual_series(c,"operating_income",dt); gp=annual_series(c,"gross_profit",dt)
 rv=rev[-1][1] if rev else None; rv0=rev[-2][1] if len(rev)>1 else None; rv1=rev[-3][1] if len(rev)>2 else None
 ov=op[-1][1] if op else None;ov0=op[-2][1] if len(op)>1 else None;gv=gp[-1][1] if gp else None;gv0=gp[-2][1] if len(gp)>1 else None
 assets=last(c,"assets",dt);ni=last(c,"net_income",dt);cfo=last(c,"cfo",dt);capex=last(c,"capex",dt);debt=last(c,"debt",dt);sh,sh0=last2(c,"shares",dt)
 h=px.loc[:dt]
 if h.empty or rv is None or assets in (None,0):return None
 p=float(h.iloc[-1]); fcf=(cfo-capex) if cfo is not None and capex is not None else np.nan
 rg=pct(rv,rv0); prev=pct(rv0,rv1)
 return dict(ticker=t,date=dt,price=p,rev_growth=rg,rev_accel=(rg-prev if np.isfinite(rg) and np.isfinite(prev) else np.nan),
  op_growth=pct(ov,ov0),gross_growth=pct(gv,gv0),roa=(ni/assets if ni is not None else np.nan),fcf_margin=(fcf/rv if rv else np.nan),
  debt_assets=(debt/assets if debt is not None else 0),dilution=pct(sh,sh0),
  momentum12=(p/float(h.iloc[-13])-1 if len(h)>=13 else np.nan),momentum6=(p/float(h.iloc[-7])-1 if len(h)>=7 else np.nan),
  drawdown=(p/float(h.tail(36).max())-1 if len(h)>=12 else np.nan),log_assets=np.log(max(assets,1)),sales_assets=rv/assets)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",default="output/sec_point_in_time_broad.json");ap.add_argument("--out",default="signals/warman_ml_2x_v1.json");a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(mp.values());prices={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2011-01-01",end="2027-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=q[t]["Close"].dropna()
     if len(s)>20:prices[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);px=prices.get(t)
  if px is None:continue
  for y in range(2014,2022):
   dt=f"{y}-06-30";r=row(c,t,dt,px)
   if not r:continue
   fut=px.loc[dt:f"{y+5}-06-30"]
   if len(fut)<24:continue
   mx=float(fut.max())/r["price"];r.update(year=y,max5=mx,hit2=int(mx>=2),hit3=int(mx>=3),hit5=int(mx>=5));rows.append(r)
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 train=df[df.year<=2017];test=df[df.year>=2018]
 def fit(label):
  g=make_pipeline(SimpleImputer(strategy="median"),HistGradientBoostingClassifier(max_iter=200,max_leaf_nodes=15,learning_rate=.05,l2_regularization=2,random_state=7))
  r=make_pipeline(SimpleImputer(strategy="median"),RandomForestClassifier(n_estimators=350,max_depth=6,min_samples_leaf=15,max_features=.7,class_weight="balanced",n_jobs=-1,random_state=11))
  g.fit(train[FEATS],train[label]);r.fit(train[FEATS],train[label]);return g,r
 models={};metrics={}
 for lab in ["hit2","hit3","hit5"]:
  g,r=fit(lab);models[lab]=(g,r);p=(g.predict_proba(test[FEATS])[:,1]+r.predict_proba(test[FEATS])[:,1])/2
  z=test.copy();z["p"]=p;base=float(z[lab].mean());metrics[lab]={"auc":float(roc_auc_score(z[lab],p)),"base":base}
  for q in [.10,.05,.01]:
   top=z[z.p>=z.groupby("date").p.transform(lambda s:s.quantile(1-q))];rate=float(top[lab].mean());metrics[lab][f"top{int(q*100)}"]=rate;metrics[lab][f"lift{int(q*100)}"]=rate/base if base else None
 # refit through 2021, current PIT feature snapshot, ensemble probability + asymmetric bonus
 current=[]
 today="2026-10-01"
 for cik,c in cs.items():
  t=mp.get(cik);px=prices.get(t)
  if px is None:continue
  rr=row(c,t,today,px)
  if rr: current.append(rr)
 cur=pd.DataFrame(current).replace([np.inf,-np.inf],np.nan)
 for lab in ["hit2","hit3","hit5"]:
  g=make_pipeline(SimpleImputer(strategy="median"),HistGradientBoostingClassifier(max_iter=200,max_leaf_nodes=15,learning_rate=.05,l2_regularization=2,random_state=7))
  r=make_pipeline(SimpleImputer(strategy="median"),RandomForestClassifier(n_estimators=350,max_depth=6,min_samples_leaf=15,max_features=.7,class_weight="balanced",n_jobs=-1,random_state=11))
  g.fit(df[FEATS],df[lab]);r.fit(df[FEATS],df[lab]);cur["p"+lab[-1]]=(g.predict_proba(cur[FEATS])[:,1]+r.predict_proba(cur[FEATS])[:,1])/2
 cur["score"]=.60*cur.p2+.25*cur.p3+.15*cur.p5
 cols=["ticker","score","p2","p3","p5"]+FEATS
 cand=cur.sort_values("score",ascending=False)[cols].head(50).replace({np.nan:None}).to_dict("records")
 out={"status":"ML_CURRENT_SURVIVOR_DIAGNOSTIC","method":"mean HistGradientBoosting + RandomForest; chronological OOS; PIT SEC features","warning":"US SEC cohort is current-survivor biased; probabilities are model scores, not guaranteed calibrated real-world probabilities","coverage":{"observations":len(df),"train":len(train),"oos":len(test),"current_scored":len(cur)},"oos":metrics,"candidates":cand}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
