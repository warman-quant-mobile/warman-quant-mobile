#!/usr/bin/env python3
import json
from pathlib import Path
import yfinance as yf
from yfinance import EquityQuery
REG={"us":["NMS","NYQ","ASE","NGM","NCM","PCX"],"se":["STO"]}
SCREENS=[
 ("quality","returnonequity.lasttwelvemonths",False),
 ("quality","returnonassets.lasttwelvemonths",False),
 ("quality","returnontotalcapital.lasttwelvemonths",False),
 ("value","lastclosepriceearnings.lasttwelvemonths",True),
 ("value","pricebookratio.quarterly",True),
 ("value","lastclosetevebitda.lasttwelvemonths",True),
 ("growth","epsgrowth.lasttwelvemonths",False),
 ("growth","totalrevenues1yrgrowth.lasttwelvemonths",False),
 ("growth","ebitda1yrgrowth.lasttwelvemonths",False),
 ("growth","leveredfreecashflow1yrgrowth.lasttwelvemonths",False),
 ("momentum","fiftytwowkpercentchange",False)]
W={"quality":.30,"value":.25,"growth":.25,"momentum":.20}
def screen(region,exs,fld,asc):
 q=EquityQuery("and",[EquityQuery("eq",["region",region]),EquityQuery("is-in",["exchange"]+exs),
   EquityQuery("gte",["intradaymarketcap",500000000 if region=="us" else 1000000000])])
 return yf.screen(q,size=250,sortField=fld,sortAsc=asc).get("quotes",[])
def main():
 allout=[]
 for region,exs in REG.items():
  pool={}
  for fam,fld,asc in SCREENS:
   for j,x in enumerate(screen(region,exs,fld,asc)):
    s=x.get("symbol")
    if not s or x.get("quoteType")!="EQUITY":continue
    z=pool.setdefault(s,{"ticker":s,"name":x.get("shortName") or x.get("longName"),"region":region,"market_cap":x.get("marketCap") or x.get("intradaymarketcap"),"families":{}})
    z["families"].setdefault(fam,[]).append(1-j/249)
  for z in pool.values():
   fs={k:sum(v)/len(v) for k,v in z["families"].items()}
   if len(fs)<3:continue
   den=sum(W[k] for k in fs);z["score"]=sum(W[k]*v for k,v in fs.items())/den
   z["families"]={k:round(v,4) for k,v in fs.items()};allout.append(z)
 for region in REG:
  q=sorted([x for x in allout if x["region"]==region],key=lambda x:x["score"],reverse=True)
  for j,x in enumerate(q):x["region_percentile"]=1-j/max(1,len(q)-1)
 final=sorted(allout,key=lambda x:(x["region_percentile"],x["score"]),reverse=True)
 out={"status":"exploratory_current_snapshot_not_OOS","method":"union of full-market Yahoo factor screens","weights":W,"top":final[:50]}
 Path("signals/stock_picker_prototype_v2.json").write_text(json.dumps(out,indent=2))
 print(json.dumps({"eligible":len(allout),"top":final[:12]}))
if __name__=="__main__":main()
