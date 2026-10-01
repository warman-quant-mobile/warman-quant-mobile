#!/usr/bin/env python3
"""Tenbagger archetypes v1: discover clusters on 2014-17 winners, freeze, validate 2018-21."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def ser(c,k,asof):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.values())
def l2(c,k,d):
 x=ser(c,k,d);return (x[-1],x[-2]) if len(x)>1 else (None,None)
def last(c,k,d):
 x=ser(c,k,d);return x[-1] if x else None
def pct(a,b): return a/b-1 if a is not None and b not in (None,0) else np.nan
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(mp.values());prices={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2012-01-01",end="2027-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>20:prices[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);px=prices.get(t)
  if px is None:continue
  for y in range(2014,2022):
   dt=f"{y}-06-30";h=px.loc[:dt]
   if len(h)<13:continue
   p=float(h.iloc[-1]);rv,r0=l2(c,"revenue",dt);op,o0=l2(c,"operating_income",dt);gp,g0=l2(c,"gross_profit",dt)
   ni=last(c,"net_income",dt);ass=last(c,"assets",dt);cfo=last(c,"cfo",dt);cap=last(c,"capex",dt);debt=last(c,"debt",dt);sh,s0=l2(c,"shares",dt)
   if rv is None or ass in (None,0):continue
   fut=px.loc[dt:f"{y+5}-06-30"]
   if len(fut)<24:continue
   fcf=(cfo-cap) if cfo is not None and cap is not None else np.nan;mx=float(fut.max())/p
   rows.append(dict(ticker=t,date=dt,year=y,rev=pct(rv,r0),op=pct(op,o0),gross=pct(gp,g0),roa=(ni/ass if ni is not None else np.nan),fcfm=(fcf/rv if rv else np.nan),lev=(debt/ass if debt is not None else 0),dil=pct(sh,s0),mom=p/float(h.iloc[-13])-1,max5=mx))
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 F=["rev","op","gross","roa","fcfm","lev","dil","mom"]
 for dt,ix in df.groupby("date").groups.items():
  for v in F:df.loc[ix,v+"p"]=df.loc[ix,v].rank(pct=True).fillna(.5)
 P=[x+"p" for x in F];dev=df[df.year<2018].copy();oos=df[df.year>=2018].copy()
 winners=dev[dev.max5>=5].copy();X=winners[P].fillna(.5)
 scaler=StandardScaler().fit(X);k=4;km=KMeans(n_clusters=k,random_state=42,n_init=50).fit(scaler.transform(X))
 centers=km.cluster_centers_
 def dist_scores(z):
  zz=scaler.transform(z[P].fillna(.5));dist=np.sqrt(((zz[:,None,:]-centers[None,:,:])**2).mean(axis=2))
  return dist
 dd=dist_scores(dev);thresholds=np.quantile(dd,.10,axis=0)
 def evaluate(z):
  ds=dist_scores(z);match=(ds<=thresholds).any(axis=1);out={"n":len(z),"selected_share":float(match.mean())}
  for m in [2,3,5,10]:
   hit=z.max5.values>=m;base=float(hit.mean());sel=float(hit[match].mean()) if match.any() else None;rec=float(match[hit].mean()) if hit.any() else None
   out[f"hit{m}"]={"base":base,"selected":sel,"lift":sel/base if base and sel is not None else None,"recall":rec}
  return out
 profiles=[]
 for i in range(k):
  w=winners.iloc[np.where(km.labels_==i)[0]]
  profiles.append({"id":i,"n_dev_winners":len(w),"median":{v:float(w[v].median()) for v in F}})
 out={"status":"ARCHETYPE_DISCOVERY_DEV_ONLY_OOS_DIAGNOSTIC","split":"2014-17 discovery; 2018-21 frozen OOS","warning":"Current-survivor universe and live Yahoo prices; diagnostic until price snapshot is frozen.","features":F,"archetypes":profiles,"dev":evaluate(dev),"oos":evaluate(oos)}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
