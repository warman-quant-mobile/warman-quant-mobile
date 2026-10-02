#!/usr/bin/env python3
"""Current Graham candidates from Yahoo screener fields themselves, then frozen QGM-style ranking."""
import json
from pathlib import Path
import yfinance as yf
from yfinance import EquityQuery
REG={"us":["NMS","NYQ","ASE","NGM","NCM","PCX"],"se":["STO"]}
def fetch(reg,exs,sort):
 q=EquityQuery("and",[EquityQuery("eq",["region",reg]),EquityQuery("is-in",["exchange"]+exs),
 EquityQuery("gte",["intradaymarketcap",500000000 if reg=="us" else 1000000000]),
 EquityQuery("gt",["peratio.lasttwelvemonths",0]),EquityQuery("lte",["peratio.lasttwelvemonths",30]),
 EquityQuery("gt",["pricebookratio.quarterly",0]),EquityQuery("lte",["pricebookratio.quarterly",4])])
 return yf.screen(q,size=250,sortField=sort,sortAsc=True).get("quotes",[])
def val(x,*ks):
 for k in ks:
  v=x.get(k)
  if isinstance(v,(int,float)):return float(v)
 return None
def main():
 rows={}
 for reg,exs in REG.items():
  # Union sorts reduces 250-result truncation bias.
  xs=[]
  for sort in ["peratio.lasttwelvemonths","pricebookratio.quarterly","intradaymarketcap"]:
   try:xs+=fetch(reg,exs,sort)
   except Exception:pass
  for x in xs:
   t=x.get("symbol")
   if not t or x.get("quoteType")!="EQUITY":continue
   pe=val(x,"peratio.lasttwelvemonths","trailingPE","peRatio")
   pb=val(x,"pricebookratio.quarterly","priceToBook","priceBookRatio")
   if pe is None or pb is None:continue
   prod=pe*pb
   if pe<=0 or pb<=0 or prod>22.5:continue
   z=rows.setdefault(t,{"ticker":t,"name":x.get("shortName") or x.get("longName"),"region":reg,"pe":pe,"pb":pb,"graham_product":prod,"market_cap":x.get("marketCap") or x.get("intradaymarketcap"),"quality":[],"growth":[],"momentum":[]})
   for fam,keys in [("quality",["returnonequity.lasttwelvemonths","returnonassets.lasttwelvemonths","returnontotalcapital.lasttwelvemonths"]),("growth",["epsgrowth.lasttwelvemonths","totalrevenues1yrgrowth.lasttwelvemonths","ebitda1yrgrowth.lasttwelvemonths","leveredfreecashflow1yrgrowth.lasttwelvemonths"]),("momentum",["fiftytwowkpercentchange"])]:
    for k in keys:
     v=val(x,k)
     if v is not None:z[fam].append(v)
 # Enrich candidates directly; screen response may omit non-sort fields.
 for t,z in rows.items():
  try:
   info=yf.Ticker(t).get_info()
   z["quality"]=[v for v in [info.get("returnOnEquity"),info.get("returnOnAssets")] if isinstance(v,(int,float))]
   z["growth"]=[v for v in [info.get("earningsGrowth"),info.get("revenueGrowth")] if isinstance(v,(int,float))]
   z["momentum"]=[v for v in [info.get("52WeekChange")] if isinstance(v,(int,float))]
   z["current_ratio"]=info.get("currentRatio");z["debt_to_equity"]=info.get("debtToEquity")
  except Exception:pass
 arr=list(rows.values())
 # Deduplicate share classes / near-identical companies by normalized name, keep cheaper Graham product.
 ded={}
 for z in arr:
  nm=(z.get("name") or z["ticker"]).lower().replace(" ser. a","").replace(" ser. c","").replace(" class a","").replace(" class c","")
  if nm not in ded or z["graham_product"]<ded[nm]["graham_product"]:ded[nm]=z
 arr=list(ded.values())
 for reg in REG:
  g=[z for z in arr if z["region"]==reg]
  for fam in ["quality","growth","momentum"]:
   vals=[sum(z[fam])/len(z[fam]) for z in g if z[fam]]
   for z in g:
    if not z[fam]:z[fam+"_pct"]=.5;continue
    v=sum(z[fam])/len(z[fam]);
    # Winsorized percentile: extreme accounting jumps must not dominate rank.
    lo,hi=(sorted(vals)[max(0,int(.05*len(vals))-1)],sorted(vals)[min(len(vals)-1,int(.95*len(vals)))]) if vals else (v,v)
    v=min(max(v,lo),hi);z[fam+"_pct"]=sum(min(max(q,lo),hi)<=v for q in vals)/max(1,len(vals))
  for z in g:
   base=.35*z["quality_pct"]+.35*z["growth_pct"]+.30*z["momentum_pct"]
   cr=z.get("current_ratio");de=z.get("debt_to_equity")
   penalty=(.08 if isinstance(cr,(int,float)) and cr<1 else 0)+(.08 if isinstance(de,(int,float)) and de>100 else 0)
   z["balance_penalty"]=penalty;z["rank_score"]=base-penalty
 arr.sort(key=lambda z:z["rank_score"],reverse=True)
 out={"status":"CURRENT_GRAHAM_PRODUCT_SCREEN_ROBUST_V2","rule":"positive PE/PB and PE*PB<=22.5; market cap floors US $500m / SE SEK1bn; QGM current proxy only ranks survivors","n":len(arr),"candidates":arr}
 Path("signals/stock_picker_graham_current_fixed_v1.json").write_text(json.dumps(out,indent=2,default=str)+"
");print(json.dumps(out,default=str))
if __name__=="__main__":main()
