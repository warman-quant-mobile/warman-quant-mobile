#!/usr/bin/env python3
"""Broad current US equity universe. Yahoo first; SEC is optional enrichment.
Current membership only -- historical PIT membership is a separate validation layer."""
import argparse,json
from pathlib import Path
import yfinance as yf
from yfinance import EquityQuery

EXCHANGES=["NMS","NYQ","ASE","NGM","NCM","PCX"]
def yahoo_universe():
 rows={}
 # Pagination per exchange avoids Yahoo's 250-result ceiling per call.
 for ex in EXCHANGES:
  q=EquityQuery("and",[EquityQuery("eq",["region","us"]),EquityQuery("eq",["exchange",ex])])
  offset=0
  while True:
   r=yf.screen(q,offset=offset,size=250,sortField="ticker",sortAsc=True)
   quotes=r.get("quotes",[])
   if not quotes: break
   for x in quotes:
    sym=x.get("symbol")
    qt=x.get("quoteType")
    if sym and qt=="EQUITY":
     rows[sym]={"ticker":sym,"name":x.get("shortName") or x.get("longName"),"exchange":ex,
                "market_cap":x.get("marketCap"),"currency":x.get("currency")}
   if len(quotes)<250: break
   offset+=len(quotes)
   if offset>=10000: break
 return list(rows.values())
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",default="output/us_universe_current.json");a=p.parse_args()
 rows=yahoo_universe()
 if len(rows)<3000: raise RuntimeError(f"Yahoo US equity universe unexpectedly small: {len(rows)}")
 out={"schema_version":3,"source":"Yahoo Finance via yfinance EquityQuery",
      "warning":"Current-list universe only; historical membership/delistings require PIT reconstruction.",
      "count":len(rows),"companies":rows}
 q=Path(a.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps({"count":len(rows),"exchanges":EXCHANGES}))
if __name__=="__main__":main()
