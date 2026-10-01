#!/usr/bin/env python3
"""Build a broader SEC PIT research cohort from the current US universe. Diagnostic: current-survivor biased."""
import argparse,json,os,time,urllib.request
from pathlib import Path
from sec_fundamentals_collector import collect
UA=os.environ.get("SEC_USER_AGENT","WarmanQuant/1.0 research").strip().replace("\r"," ").replace("\n"," ")
def get(url):
 q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
 with urllib.request.urlopen(q,timeout=45) as r:return json.load(r)
def main():
 p=argparse.ArgumentParser();p.add_argument("--universe",default="output/us_universe_current.json");p.add_argument("--limit",type=int,default=120);p.add_argument("--out",default="output/sec_point_in_time_broad.json");a=p.parse_args()
 u=json.load(open(a.universe)); raw=u.get("tickers") or u.get("symbols") or u.get("universe") or u.get("data") or u.get("companies") or []
 syms=[]
 for z in raw:
  s=z if isinstance(z,str) else z.get("ticker") or z.get("symbol")
  if s:syms.append(s.upper().replace(".","-"))
 mp=get("https://www.sec.gov/files/company_tickers.json")
 tm={v["ticker"].upper():str(v["cik_str"]) for v in mp.values()}
 ciks=[]; picked=[]
 for s in syms:
  if s in tm and tm[s] not in ciks:
   ciks.append(tm[s]);picked.append(s)
  if len(ciks)>=a.limit:break
 if len(ciks)<100: raise RuntimeError(f"SEC mapping unexpectedly small: {len(ciks)} mapped from {len(syms)} universe tickers")
 out=collect(ciks)
 if len(out.get("companies",{}))<100: raise RuntimeError(f"SEC PIT cohort unexpectedly small: {len(out.get('companies',{}))}")
 out["selection"]={"tickers":picked,"note":"current universe survivor-biased diagnostic cohort"}
 Path(a.out).write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps({"companies":len(out["companies"]),"tickers":len(picked)}))
if __name__=="__main__":main()
