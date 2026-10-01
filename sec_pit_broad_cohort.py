#!/usr/bin/env python3
"""Build full SEC PIT cohort from SEC companyfacts bulk archive. Current-survivor diagnostic universe."""
import argparse,json,os,urllib.request,zipfile,tempfile
from pathlib import Path
from sec_fundamentals_collector import TAGS,choose
UA=os.environ.get("SEC_USER_AGENT","WarmanQuant/1.0 research").strip().replace("\r"," ").replace("\n"," ")
def get_json(url):
 q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
 with urllib.request.urlopen(q,timeout=90) as r:return json.load(r)
def transform(j):
 g=j.get("facts",{}).get("us-gaap",{}); rows={}
 for key,names in TAGS.items():
  tag,x=choose(g,names)
  if not x: continue
  units=x.get("units",{})
  arr=units.get("USD") or units.get("shares") or units.get("USD/shares") or []
  clean=[]
  for z in arr:
   if z.get("form") not in ("10-Q","10-K"): continue
   if not z.get("filed") or z.get("val") is None: continue
   clean.append({k:z.get(k) for k in ("start","end","val","accn","fy","fp","form","filed","frame")})
  rows[key]={"tag":tag,"facts":clean}
 return {"entity":j.get("entityName"),"facts":rows}
def main():
 p=argparse.ArgumentParser();p.add_argument("--universe",default="output/us_universe_current.json");p.add_argument("--limit",type=int,default=999999);p.add_argument("--out",default="output/sec_point_in_time_broad.json");a=p.parse_args()
 u=json.load(open(a.universe)); raw=u.get("companies") or []
 syms=[(z if isinstance(z,str) else z.get("ticker") or z.get("symbol")).upper().replace(".","-") for z in raw if (z if isinstance(z,str) else z.get("ticker") or z.get("symbol"))]
 mp=get_json("https://www.sec.gov/files/company_tickers.json"); tm={v["ticker"].upper():str(v["cik_str"]) for v in mp.values()}
 selected=[]; seen=set()
 for s in syms:
  cik=tm.get(s)
  if cik and cik not in seen:
   selected.append((s,cik));seen.add(cik)
  if len(selected)>=a.limit: break
 if len(selected)<100: raise RuntimeError(f"SEC mapping unexpectedly small: {len(selected)} from {len(syms)}")
 url="https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
 out={"schema_version":2,"source":"SEC EDGAR companyfacts bulk ZIP","point_in_time_rule":"fact usable no earlier than filed date","companies":{}}
 missing=[]; errors=[]
 with tempfile.NamedTemporaryFile(suffix=".zip") as t:
  with urllib.request.urlopen(req,timeout=300) as r:
   while True:
    b=r.read(1024*1024)
    if not b: break
    t.write(b)
  t.flush()
  with zipfile.ZipFile(t.name) as z:
   names=set(z.namelist())
   for ticker,cik in selected:
    name=f"CIK{int(cik):010d}.json"
    if name not in names:
     missing.append({"ticker":ticker,"cik":cik});continue
    try:
     j=json.loads(z.read(name));out["companies"][cik]=transform(j)
    except Exception as e: errors.append({"ticker":ticker,"cik":cik,"error":str(e)[:160]})
 out["selection"]={"requested":len(selected),"available":len(out["companies"]),"ticker_by_cik":{c:t for t,c in selected if c in out["companies"]},"missing":len(missing),"errors":len(errors),"missing_sample":missing[:50],"error_sample":errors[:20],"note":"current US universe survivor-biased diagnostic cohort"}
 if len(out["companies"])<100: raise RuntimeError(f"SEC PIT cohort unexpectedly small: {len(out['companies'])}")
 q=Path(a.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(out,separators=(",",":"))+"\n")
 print(json.dumps({"mapped":len(selected),"companies":len(out["companies"]),"missing":len(missing),"errors":len(errors)}))
if __name__=="__main__": main()
