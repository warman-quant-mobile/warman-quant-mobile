#!/usr/bin/env python3
"""Cross-market current ML transfer rank: US+Sweden, using features available consistently from Yahoo.
Learns price-path winner/failure relationships on US PIT labels, applies same feature space to both markets."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from sklearn.ensemble import HistGradientBoostingClassifier,RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

F=["mom12","mom6","dd36","vol12","vol36","reversal3","trend","log_mcap"]
def pf(px,mcap=np.nan):
 if px is None or len(px)<14:return None
 p=float(px.iloc[-1]);ret=px.pct_change()
 def rr(n): return p/float(px.iloc[-n])-1 if len(px)>=n else np.nan
 ma10=float(px.tail(10).mean()) if len(px)>=10 else np.nan
 return dict(mom12=rr(13),mom6=rr(7),dd36=p/float(px.tail(36).max())-1,
  vol12=float(ret.tail(12).std()*np.sqrt(12)),vol36=float(ret.tail(36).std()*np.sqrt(12)),
  reversal3=rr(4),trend=(p/ma10-1 if ma10 else np.nan),log_mcap=(np.log(mcap) if mcap and mcap>0 else np.nan))
def dl(ticks,start="2011-01-01"):
 out={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start=start,end="2027-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>15:out[t]=s
    except:pass
  except:pass
 return out
def model():
 return [make_pipeline(SimpleImputer(strategy="median"),HistGradientBoostingClassifier(max_iter=220,max_leaf_nodes=15,learning_rate=.04,l2_regularization=3,random_state=17)),
 make_pipeline(SimpleImputer(strategy="median"),RandomForestClassifier(n_estimators=400,max_depth=6,min_samples_leaf=20,max_features=.75,class_weight="balanced",n_jobs=-1,random_state=19))]
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--us",default="output/us_universe_current.json");ap.add_argument("--se",default="output/se_universe_current.json");ap.add_argument("--out",default="signals/warman_ml_crossmarket_v1.json");a=ap.parse_args()
 us=json.load(open(a.us))["companies"];se=json.load(open(a.se))["companies"]; um={x["ticker"]:x.get("market_cap") for x in us}; sm={x["ticker"]:x.get("market_cap") for x in se}
 # Broad but practical current set: every listed equity with market cap known and >= $50m / SEK 500m; plus all missing-cap names for scoring if price exists.
 ticks=list(dict.fromkeys(list(um)+list(sm))); P=dl(ticks)
 # Historical training from US names with current membership: diagnostic, chronological OOS.
 rows=[]
 for t in um:
  px=P.get(t)
  if px is None:continue
  for y in range(2014,2022):
   h=px.loc[:f"{y}-06-30"]; fut=px.loc[f"{y}-06-30":f"{y+5}-06-30"]
   if len(h)<14 or len(fut)<24:continue
   x=pf(h,um[t]); entry=float(h.iloc[-1]); mx=float(fut.max())/entry; terminal=float(fut.iloc[-1])/entry
   x.update(ticker=t,year=y,date=f"{y}-06-30",hit2=int(mx>=2),hit3=int(mx>=3),hit5=int(mx>=5),terminal=terminal,loss=int(terminal<=.5));rows.append(x)
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan);tr=df[df.year<=2017];te=df[df.year>=2018]
 metrics={};mods={}
 for lab in ["hit2","hit3","hit5","loss"]:
  ms=model()
  for m in ms:m.fit(tr[F],tr[lab])
  p=sum(m.predict_proba(te[F])[:,1] for m in ms)/len(ms);z=te.copy();z["p"]=p;base=float(z[lab].mean());d={"auc":float(roc_auc_score(z[lab],p)),"base":base}
  for q in [.10,.05]:
   top=z[z.p>=z.groupby("date").p.transform(lambda s:s.quantile(1-q))];rate=float(top[lab].mean());d[f"top{int(q*100)}"]=rate;d[f"lift{int(q*100)}"]=rate/base if base else None
  metrics[lab]=d
  # final fit all historical observations
  ms=model()
  for m in ms:m.fit(df[F],df[lab])
  mods[lab]=ms
 cur=[]
 for region,mp in [("us",um),("se",sm)]:
  for t,mc in mp.items():
   px=P.get(t)
   if px is None:continue
   # investability floor
   floor=50_000_000 if region=="us" else 500_000_000
   if mc is not None and mc<floor:continue
   x=pf(px,mc)
   if x:x.update(ticker=t,region=region,market_cap=mc);cur.append(x)
 C=pd.DataFrame(cur).replace([np.inf,-np.inf],np.nan)
 for lab,ms in mods.items():C["p_"+lab]=sum(m.predict_proba(C[F])[:,1] for m in ms)/len(ms)
 # two sleeves: compounder avoids deep distress; recovery permits it but penalizes terminal-loss probability.
 C["compounder_score"]=.50*C.p_hit2+.30*C.p_hit3+.20*C.p_hit5-.45*C.p_loss-.20*np.maximum(0,-C.dd36-.55)
 C["recovery_score"]=.45*C.p_hit2+.30*C.p_hit3+.25*C.p_hit5-.60*C.p_loss
 C["score"]=np.maximum(C.compounder_score,C.recovery_score)
 C["sleeve"]=np.where(C.compounder_score>=C.recovery_score,"compounder","recovery")
 cols=["ticker","region","market_cap","score","sleeve","compounder_score","recovery_score","p_hit2","p_hit3","p_hit5","p_loss"]+F
 top=C.sort_values("score",ascending=False)[cols].head(100).replace({np.nan:None}).to_dict("records")
 out={"status":"CROSS_MARKET_ML_DIAGNOSTIC","warning":"Historical training uses current US survivors; Swedish scores are transfer scores, not Sweden-specific calibrated probabilities.","coverage":{"historical_obs":len(df),"oos":len(te),"current_us":int((C.region=="us").sum()),"current_se":int((C.region=="se").sum())},"oos":metrics,"candidates":top}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps({"coverage":out["coverage"],"oos":metrics,"top":top[:20]}))
if __name__=="__main__":main()
