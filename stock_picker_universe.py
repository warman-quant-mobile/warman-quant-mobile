#!/usr/bin/env python3
"""Build a broad current US equity universe from SEC's official ticker map.
Research universe builder; current-list membership is NOT historical membership."""
import argparse,json,os,urllib.request
from pathlib import Path
URLS=["https://www.sec.gov/files/company_tickers_exchange.json","https://www.sec.gov/files/company_tickers.json"]
UA=os.environ.get("SEC_USER_AGENT","WarmanQuant/1.0 warman-quant-mobile GitHub research")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--out",default="output/us_universe_current.json"); a=p.parse_args()
 req=urllib.request.Request(URL,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
 with urllib.request.urlopen(req,timeout=60) as r:d=json.load(r)
 fields=d["fields"]; rows=[dict(zip(fields,x)) for x in d["data"]]
 allowed={"Nasdaq","NYSE","NYSE Arca","NYSE American"}
 rows=[x for x in rows if x.get("exchange") in allowed and x.get("ticker") and x.get("cik")]
 out={"schema_version":1,"source":URL,"warning":"Current SEC-listed universe only; do not use as historical membership without PIT reconstruction.","count":len(rows),"companies":rows}
 q=Path(a.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps({"count":len(rows),"exchanges":sorted(set(x["exchange"] for x in rows))}))
if __name__=="__main__":main()
