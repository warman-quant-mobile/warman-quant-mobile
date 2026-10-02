#!/usr/bin/env python3
"""Audit Graham historical ratios with split-consistent SEC shares + robust current Yahoo screen."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
from yfinance import EquityQuery
def ann(c,k,d):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=d and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));q={}
 for z in x:q[z["end"]]=float(z["val"])
 return list(q.items())
def l1(c,k,d):x=ann(c,k,d);return x[-1][1] if x else None
def perf(rs):
 w=np.cumprod(1+np.array(rs));n=len(rs)
 return {"years":n,"cumulative":float(w[-1]-1),"cagr":float(w[-1]**(1/n)-1),"max_drawdown":float(np.min(w/np.maximum.accumulate(w)-1))} if n else {}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={};spl={}
 for i in range(0,len(ticks),100):
  b=ticks[i:i+100]
  try:
   q=yf.download(b,start="2010-01-01",end="2022-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>24:px[t]=s
    except:pass
  except:pass
 for t in px:
  try:spl[t]=yf.Ticker(t).splits
  except:spl[t]=pd.Series(dtype=float)
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);p=px.get(t)
  if p is None:continue
  for y in range(2014,2021):
   dt=f"{y}-06-30";h=p.loc[:dt];f=p.loc[dt:f"{y+1}-06-30"]
   if len(h)<13 or len(f)<10:continue
   ni=l1(c,"net_income",dt);eq=l1(c,"equity",dt);sh=l1(c,"shares",dt)
   if ni is None or eq is None or sh in (None,0) or ni<=0 or eq<=0:continue
   sf=1.
   ss=spl.get(t)
   if ss is not None and len(ss):
    for dd,v in ss.items():
     if pd.Timestamp(dd).tz_localize(None)>pd.Timestamp(dt) and float(v)>0:sf*=float(v)
   adjsh=sh*sf;pr=float(h.iloc[-1]);pe=pr/(ni/adjsh);pb=pr/(eq/adjsh)
   rows.append({"ticker":t,"year":y,"ret":float(f.iloc[-1]/pr-1),"split_factor_after_asof":sf,"pe":pe,"pb":pb,"core":pe<=15 and pb<=1.5 and pe*pb<=22.5})
 df=pd.DataFrame(rows);rs=[];annual=[]
 for y,g in df.groupby("year"):
  z=g[g.core]
  if len(z):rs.append(float(z.ret.mean()-.005));annual.append({"year":int(y),"n":len(z),"net_return":float(z.ret.mean()-.005),"tickers":z.ticker.tolist()})
 current=[]
 for reg,exs in [("us",["NMS","NYQ","ASE","NGM","NCM","PCX"]),("se",["STO"])]:
  q=EquityQuery("and",[EquityQuery("eq",["region",reg]),EquityQuery("is-in",["exchange"]+exs),EquityQuery("gte",["intradaymarketcap",500000000 if reg=="us" else 1000000000]),EquityQuery("gt",["peratio.lasttwelvemonths",0]),EquityQuery("lte",["peratio.lasttwelvemonths",15]),EquityQuery("gt",["pricebookratio.quarterly",0]),EquityQuery("lte",["pricebookratio.quarterly",1.5])])
  try:
   xs=yf.screen(q,size=250,sortField="peratio.lasttwelvemonths",sortAsc=True).get("quotes",[])
  except Exception:xs=[]
  for x in xs:
   pe=x.get("trailingPE") or x.get("peRatio") or x.get("peratio.lasttwelvemonths");pb=x.get("priceToBook") or x.get("priceBookRatio") or x.get("pricebookratio.quarterly")
   if pe is None or pb is None:
    try:
     info=yf.Ticker(x["symbol"]).fast_info; # quote fallback below
     qi=yf.Ticker(x["symbol"]).get_info();pe=pe or qi.get("trailingPE");pb=pb or qi.get("priceToBook")
    except:pass
   if pe and pb and pe>0 and pb>0 and pe<=15 and pb<=1.5 and pe*pb<=22.5:
    current.append({"ticker":x.get("symbol"),"name":x.get("shortName"),"region":reg,"pe":float(pe),"pb":float(pb),"product":float(pe*pb),"market_cap":x.get("marketCap") or x.get("intradaymarketcap")})
 current.sort(key=lambda z:z["product"])
 out={"status":"SPLIT_CONSISTENCY_AUDIT","historical":{"performance":perf(rs),"annual":annual,"observations":len(df)},"current_candidates":current,"current_n":len(current),"note":"Historical SEC shares multiplied by all subsequent Yahoo split ratios to match split-adjusted Yahoo price basis."}
 Path(a.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
