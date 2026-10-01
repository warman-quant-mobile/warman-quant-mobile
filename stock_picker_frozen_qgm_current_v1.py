#!/usr/bin/env python3
"""Current cross-sectional rank matching the frozen, final-tested Q/G/M family weights.
No value factor; no post-holdout weight tuning. Yahoo screen percentiles are used as
current proxies for the same three economic families."""
import json
from pathlib import Path
import yfinance as yf
from yfinance import EquityQuery
REG={"us":["NMS","NYQ","ASE","NGM","NCM","PCX"],"se":["STO"]}
SC=[("quality","returnonequity.lasttwelvemonths"),("quality","returnonassets.lasttwelvemonths"),
("quality","returnontotalcapital.lasttwelvemonths"),("growth","epsgrowth.lasttwelvemonths"),
("growth","totalrevenues1yrgrowth.lasttwelvemonths"),("growth","ebitda1yrgrowth.lasttwelvemonths"),
("growth","leveredfreecashflow1yrgrowth.lasttwelvemonths"),("momentum","fiftytwowkpercentchange")]
W={"quality":.35,"growth":.35,"momentum":.30}
def scr(region,exs,f):
 q=EquityQuery("and",[EquityQuery("eq",["region",region]),EquityQuery("is-in",["exchange"]+exs),
 EquityQuery("gte",["intradaymarketcap",500000000 if region=="us" else 1000000000])])
 return yf.screen(q,size=250,sortField=f,sortAsc=False).get("quotes",[])
def main():
 out=[]
 for reg,exs in REG.items():
  pool={}
  for fam,f in SC:
   for j,x in enumerate(scr(reg,exs,f)):
    t=x.get("symbol")
    if not t or x.get("quoteType")!="EQUITY":continue
    z=pool.setdefault(t,{"ticker":t,"name":x.get("shortName") or x.get("longName"),"region":reg,"market_cap":x.get("marketCap") or x.get("intradaymarketcap"),"families":{}})
    z["families"].setdefault(fam,[]).append(1-j/249)
  for z in pool.values():
   fs={k:sum(v)/len(v) for k,v in z["families"].items()}
   if len(fs)<3:continue
   z["score"]=sum(W[k]*fs[k] for k in W);z["families"]={k:round(v,4) for k,v in fs.items()};out.append(z)
 for reg in REG:
  q=sorted([x for x in out if x["region"]==reg],key=lambda x:x["score"],reverse=True)
  for j,x in enumerate(q):x["region_percentile"]=1-j/max(1,len(q)-1)
 final=sorted(out,key=lambda x:(x["region_percentile"],x["score"]),reverse=True)
 o={"status":"CURRENT_PROXY_FOR_FROZEN_FINAL_TESTED_QGM","weights":W,"warning":"Current Yahoo family proxies are not identical SEC PIT variables; no weights were retuned.","top20":final[:20],"top50":final[:50],"eligible":len(final)}
 Path("signals/stock_picker_frozen_qgm_current_v1.json").write_text(json.dumps(o,indent=2)+"\n");print(json.dumps(o))
if __name__=="__main__":main()

# trigger
