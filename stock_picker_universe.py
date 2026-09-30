#!/usr/bin/env python3
"""Build broad current US equity universe from SEC official ticker maps.
Current membership only: never treat this file as historical PIT membership."""
import argparse,json,os,urllib.request
from pathlib import Path
URLS=["https://www.sec.gov/files/company_tickers_exchange.json","https://www.sec.gov/files/company_tickers.json"]
UA=os.environ.get("SEC_USER_AGENT","WarmanQuant/1.0 warman-quant-mobile GitHub research")
def load():
 errors=[]
 for url in URLS:
  try:
   req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
   with urllib.request.urlopen(req,timeout=60) as r:return url,json.load(r)
  except Exception as e: errors.append(f"{url}: {e!r}")
 raise RuntimeError("all SEC universe sources failed: "+" | ".join(errors))
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",default="output/us_universe_current.json");a=p.parse_args()
 source,d=load()
 if "fields" in d:
  rows=[dict(zip(d["fields"],x)) for x in d["data"]]
  allowed={"Nasdaq","NYSE","NYSE Arca","NYSE American"}
  rows=[x for x in rows if x.get("exchange") in allowed and x.get("ticker") and x.get("cik")]
 else:
  rows=[{"cik":x.get("cik_str"),"ticker":x.get("ticker"),"name":x.get("title"),"exchange":None} for x in d.values()]
  rows=[x for x in rows if x.get("ticker") and x.get("cik")]
 out={"schema_version":2,"source":source,"warning":"Current SEC ticker universe only; historical membership/delistings require PIT reconstruction.","count":len(rows),"companies":rows}
 q=Path(a.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps({"count":len(rows),"source":source}))
if __name__=="__main__":main()
