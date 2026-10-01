#!/usr/bin/env python3
"""Sequential inflection study: frozen 2014-17 rule, 2018-21 OOS.\nResearch run trigger v2."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
def S(c,k,d):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=d and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));q={}
 for z in x:q[z["end"]]=float(z["val"])
 return list(q.values())
def g3(c,k,d):
 x=S(c,k,d)
 if len(x)<3:return (np.nan,np.nan)
 def p(a,b):return a/b-1 if b else np.nan
 return p(x[-1],x[-2]),p(x[-2],x[-3])
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];ticks=list(mp.values());P={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2011-01-01",end="2027-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>30:P[t]=s
    except:pass
  except:pass
 R=[]
 for cik,c in d["companies"].items():
  t=mp.get(cik);px=P.get(t)
  if px is None:continue
  for y in range(2014,2022):
   dt=f"{y}-06-30";h=px.loc[:dt]
   if len(h)<25:continue
   p=float(h.iloc[-1]);f=px.loc[dt:f"{y+5}-06-30"]
   if len(f)<24:continue
   rv,r0=g3(c,"revenue",dt);op,o0=g3(c,"operating_income",dt);gp,g0=g3(c,"gross_profit",dt);ni,n0=g3(c,"net_income",dt);cf,c0=g3(c,"cfo",dt)
   m12=p/float(h.iloc[-13])-1;m24=p/float(h.iloc[-25])-1
   R.append(dict(ticker=t,year=y,date=dt,rev=rv,rev_acc=rv-r0,op=op,op_acc=op-o0,gross=gp,gross_acc=gp-g0,ni=ni,ni_acc=ni-n0,cfo=cf,cfo_acc=cf-c0,m12=m12,mom_acc=m12-(m24+1)**.5+1,max5=float(f.max())/p))
 df=pd.DataFrame(R).replace([np.inf,-np.inf],np.nan)
 F=["rev","rev_acc","op","op_acc","gross","gross_acc","ni","ni_acc","cfo","cfo_acc","m12","mom_acc"]
 for dt,ix in df.groupby("date").groups.items():
  for v in F:\n   s=pd.to_numeric(df.loc[ix,v],errors="coerce").astype(float)\n   df.loc[ix,v+"p"]=s.rank(pct=True).fillna(.5).values
 dev=df[df.year<2018].copy();oos=df[df.year>=2018].copy()
 # Discovery only: effect direction/strength among dev 5x winners vs non-winners.
 eff={}
 for v in F:
  x=v+"p";e=float(dev.loc[dev.max5>=5,x].mean()-dev.loc[dev.max5<5,x].mean());eff[v]=e
 keep=sorted(F,key=lambda v:abs(eff[v]),reverse=True)[:6]
 for z in [dev,oos]:
  score=np.zeros(len(z))
  for v in keep:score+=np.sign(eff[v])*(z[v+"p"].values-.5)*abs(eff[v])
  z["score"]=score
 cuts=[.10,.20,.30,.40]
 def E(z):
  out={"n":len(z)}
  for q in cuts:
   sel=z.score>=z.groupby("date").score.transform(lambda s:s.quantile(1-q));r={"selected_share":float(sel.mean())}
   for m in [2,3,5,10]:
    hit=z.max5>=m;base=float(hit.mean());rate=float(hit[sel].mean());r[f"hit{m}"]={"base":base,"rate":rate,"lift":rate/base if base else None,"recall":float(sel[hit].mean()) if hit.any() else None}
   out[f"top{int(q*100)}"]=r
  return out
 out={"status":"SEQUENTIAL_INFLECTION_DEV_FROZEN_OOS","split":"2014-17 discovery; 2018-21 OOS","warning":"Current survivors/live Yahoo; diagnostic.","dev_effects":eff,"frozen_features":keep,"dev":E(dev),"oos":E(oos)}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
