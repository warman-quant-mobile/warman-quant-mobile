#!/usr/bin/env python3
import json,math
from pathlib import Path
import yfinance as yf
from yfinance import EquityQuery
REG={"us":["NMS","NYQ","ASE","NGM","NCM","PCX"],"se":["STO"]}
F={"quality":["returnonequity.lasttwelvemonths","returnonassets.lasttwelvemonths","returnontotalcapital.lasttwelvemonths","ebitdamargin.lasttwelvemonths"],"value":["lastclosepriceearnings.lasttwelvemonths","pricebookratio.quarterly","lastclosetevebitda.lasttwelvemonths"],"growth":["epsgrowth.lasttwelvemonths","totalrevenues1yrgrowth.lasttwelvemonths","ebitda1yrgrowth.lasttwelvemonths","leveredfreecashflow1yrgrowth.lasttwelvemonths"],"momentum":["fiftytwowkpercentchange"]}
W={"quality":.30,"value":.25,"growth":.25,"momentum":.20}
def num(x,k):
 try:
  v=float(x.get(k));return v if math.isfinite(v) else None
 except:return None
def rows(region,exs):
 d={}
 for ex in exs:
  q=EquityQuery("and",[EquityQuery("eq",["region",region]),EquityQuery("eq",["exchange",ex])])
  off=0
  while True:
   a=yf.screen(q,offset=off,size=250,sortField="ticker",sortAsc=True).get("quotes",[])
   if not a:break
   for x in a:
    if x.get("quoteType")=="EQUITY" and x.get("symbol"):d[x["symbol"]]=x
   if len(a)<250:break
   off+=len(a)
 return list(d.values())
def rank(region,a):
 floor=5e8 if region=="us" else 1e9
 a=[x for x in a if (num(x,"marketCap") or num(x,"intradaymarketcap") or 0)>=floor]
 ranks={}
 for fam,keys in F.items():
  ranks[fam]=[]
  for k in keys:
   z=[(i,num(x,k)) for i,x in enumerate(a) if num(x,k) is not None and not(fam=="value" and num(x,k)<=0)]
   z.sort(key=lambda q:q[1],reverse=(fam=="value"));n=max(1,len(z)-1)
   ranks[fam].append({i:j/n for j,(i,v) in enumerate(z)})
 out=[]
 for i,x in enumerate(a):
  fs={}
  for fam,rr in ranks.items():
   v=[r[i] for r in rr if i in r]
   if v:fs[fam]=sum(v)/len(v)
  if len(fs)<3:continue
  den=sum(W[k] for k in fs);s=sum(W[k]*v for k,v in fs.items())/den
  out.append({"ticker":x["symbol"],"name":x.get("shortName"),"region":region,"score":round(s,6),"families":{k:round(v,6) for k,v in fs.items()},"market_cap":x.get("marketCap")})
 return sorted(out,key=lambda x:x["score"],reverse=True)
def main():
 out=[];counts={}
 for r,e in REG.items():
  a=rows(r,e);counts[r]=len(a);q=rank(r,a)
  for j,x in enumerate(q):x["region_percentile"]=round(1-j/max(1,len(q)-1),6)
  out+=q
 final=sorted(out,key=lambda x:(x["region_percentile"],x["score"]),reverse=True)
 p={"status":"exploratory_current_snapshot_not_OOS","weights":W,"raw_counts":counts,"top":final[:50]}
 Path("signals/stock_picker_prototype_v1.json").write_text(json.dumps(p,indent=2))
 print(json.dumps({"counts":counts,"top":final[:10]}))
if __name__=="__main__":main()
