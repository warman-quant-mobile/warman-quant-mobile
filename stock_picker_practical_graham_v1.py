#!/usr/bin/env python3
"""Practical concentrated Graham monthly-deployment simulation + current candidates.
Research window ends 2021; current screen is descriptive, never used to tune rules.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from yfinance import EquityQuery
E={"m12":-0.05703464962796956,"cfo":-0.04539953236387423,"cfo_acc":-0.021440458793486827,"ni":-0.015539326373346707,"gross":0.01453170106730639,"gross_acc":-0.013643605731961328}
def ann(c,k,d):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=d and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));q={}
 for z in x:q[z["end"]]=float(z["val"])
 return list(q.items())
def l1(c,k,d):x=ann(c,k,d);return x[-1][1] if x else None
def l2(c,k,d):x=ann(c,k,d);return (x[-1][1],x[-2][1]) if len(x)>1 else (None,None)
def rankscore(g):
 s=pd.Series(0.,index=g.index)
 for z,v in E.items():
  r=g[z].rank(pct=True).fillna(.5);s+=(r if v>0 else 1-r)
 return s/len(E)
def perf_monthly(rs):
 if not rs:return {}
 w=np.cumprod(1+np.array(rs));n=len(rs)
 return {"months":n,"cumulative":float(w[-1]-1),"cagr":float(w[-1]**(12/n)-1),"max_drawdown":float(np.min(w/np.maximum.accumulate(w)-1))}
def hist(pit):
 d=json.load(open(pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2012-01-01",end="2022-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>30:px[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);p=px.get(t)
  if p is None:continue
  for y in range(2018,2021):
   dt=f"{y}-06-30";h=p.loc[:dt]
   if len(h)<25:continue
   ni,_=l2(c,"net_income",dt);eq=l1(c,"equity",dt);sh=l1(c,"shares",dt);cfo,c0=l2(c,"cfo",dt);gp,g0=l2(c,"gross_profit",dt)
   if ni is None or eq is None or sh in (None,0) or ni<=0 or eq<=0:continue
   pr=float(h.iloc[-1]);pe=pr/(ni/sh);pb=pr/(eq/sh)
   if not(pe<=15 and pb<=1.5 and pe*pb<=22.5):continue
   rows.append({"ticker":t,"year":y,"m12":pr/float(h.iloc[-13])-1,"cfo":cfo,"cfo_acc":cfo-c0 if cfo is not None and c0 is not None else np.nan,"ni":ni,"gross":gp,"gross_acc":gp-g0 if gp is not None and g0 is not None else np.nan})
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan); picks={}
 for y,g in df.groupby("year"):
  g=g.copy();g["score"]=rankscore(g);picks[y]=g.nlargest(10,"score").ticker.tolist()
 # Practical proxy: max 10 holdings, annual frozen membership, monthly 70k contributions allocated to best 3 current holdings.
 # Return metric is time-weighted portfolio proxy; cashflow wealth path also reported for 70k/month.
 months=pd.date_range("2018-07-31","2021-06-30",freq="ME");rets=[];wealth=0.;invested=0.
 for dt in months:
  y=dt.year if dt.month>=7 else dt.year-1
  names=picks.get(y,[])[:10]; rr=[]
  for t in names:
   p=px.get(t)
   if p is None:continue
   z=p[p.index<=dt]
   if len(z)>=2:rr.append(float(z.iloc[-1]/z.iloc[-2]-1))
  r=float(np.mean(rr)) if rr else 0.; r-=.005/12; rets.append(r)
  wealth=(wealth+70000)*(1+r);invested+=70000
 return {"status":"PRACTICAL_CONCENTRATED_PROXY_RESEARCH_ONLY","period":"2018-07 through 2021-06","construction":"annual frozen Graham core; inflection top10; max 10 holdings; 70k SEK monthly contribution; practical proxy","performance":perf_monthly(rets),"wealth_sek":wealth,"contributed_sek":invested,"gain_sek":wealth-invested,"annual_top10":picks}
def current():
 fields=["trailingPE","priceToBook","marketCap","returnOnEquity","revenueGrowth","earningsGrowth","fiftyTwoWeekChange"]
 out=[]
 for reg,exs in [("us",["NMS","NYQ","ASE","NGM","NCM","PCX"]),("se",["STO"])]:
  q=EquityQuery("and",[EquityQuery("eq",["region",reg]),EquityQuery("is-in",["exchange"]+exs),EquityQuery("gte",["intradaymarketcap",500000000 if reg=="us" else 1000000000]),EquityQuery("gt",["peratio.lasttwelvemonths",0]),EquityQuery("lte",["peratio.lasttwelvemonths",15]),EquityQuery("gt",["pricebookratio.quarterly",0]),EquityQuery("lte",["pricebookratio.quarterly",1.5])])
  try:
   xs=yf.screen(q,size=250,sortField="peratio.lasttwelvemonths",sortAsc=True).get("quotes",[])
  except Exception:xs=[]
  for x in xs:
   pe=x.get("trailingPE") or x.get("peRatio");pb=x.get("priceToBook") or x.get("priceBookRatio")
   if pe and pb and pe*pb<=22.5:out.append({"ticker":x.get("symbol"),"name":x.get("shortName"),"region":reg,"pe":pe,"pb":pb,"graham_product":pe*pb,"market_cap":x.get("marketCap")})
 return out
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 o={"historical":hist(a.pit),"current_graham_candidates":current()};Path(a.out).write_text(json.dumps(o,indent=2,default=str)+"\n");print(json.dumps(o,default=str))
