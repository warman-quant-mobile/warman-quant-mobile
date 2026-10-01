#!/usr/bin/env python3
"""SEC EDGAR point-in-time fundamentals collector for Stock Picker. Research only."""
import argparse,json,time,urllib.request,os
from pathlib import Path
UA=os.environ.get("SEC_USER_AGENT","WarmanQuant/1.0 warman-quant-mobile GitHub research").strip().replace("\\r"," ").replace("\\n"," ").replace("\r"," ").replace("\n"," ")
BASE="https://data.sec.gov"
TAGS={
 "revenue":["RevenueFromContractWithCustomerExcludingAssessedTax","Revenues","SalesRevenueNet"],
 "net_income":["NetIncomeLoss"],
 "assets":["Assets"],"equity":["StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
 "cash":["CashAndCashEquivalentsAtCarryingValue"],"cfo":["NetCashProvidedByUsedInOperatingActivities"],
 "capex":["PaymentsToAcquirePropertyPlantAndEquipment"],"shares":["CommonStockSharesOutstanding","WeightedAverageNumberOfDilutedSharesOutstanding"],
 "gross_profit":["GrossProfit"],"operating_income":["OperatingIncomeLoss"],
 "debt":["LongTermDebtAndFinanceLeaseObligationsCurrent","LongTermDebtCurrent","LongTermDebtNoncurrent","LongTermDebt","DebtCurrent"]
}
def get(url):
 last=None
 for attempt in range(4):
  try:
   q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
   with urllib.request.urlopen(q,timeout=45) as r:return json.load(r)
  except Exception as e:
   last=e; time.sleep(1.5*(attempt+1))
 raise last
def facts(cik):
 return get(f"{BASE}/api/xbrl/companyfacts/CIK{int(cik):010d}.json")
def choose(usgaap,names):
 for n in names:
  if n in usgaap:return n,usgaap[n]
 return None,None
def collect(ciks):
 out={"schema_version":1,"source":"SEC EDGAR companyfacts","point_in_time_rule":"fact usable no earlier than filed date","companies":{}}
 for cik in ciks:
  j=facts(cik); g=j.get("facts",{}).get("us-gaap",{}); rows={}
  for key,names in TAGS.items():
   tag,x=choose(g,names)
   if not x:continue
   units=x.get("units",{})
   arr=units.get("USD") or units.get("shares") or units.get("USD/shares") or []
   clean=[]
   for z in arr:
    if z.get("form") not in ("10-Q","10-K"):continue
    if not z.get("filed") or z.get("val") is None:continue
    clean.append({k:z.get(k) for k in ("start","end","val","accn","fy","fp","form","filed","frame")})
   rows[key]={"tag":tag,"facts":clean}
  out["companies"][str(cik)]={"entity":j.get("entityName"),"facts":rows}
  time.sleep(.12)
 return out
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--ciks",required=True,help="comma separated CIKs");p.add_argument("--out",default="output/sec_point_in_time.json");a=p.parse_args()
 r=collect([x.strip() for x in a.ciks.split(",") if x.strip()]);o=Path(a.out);o.parent.mkdir(parents=True,exist_ok=True);o.write_text(json.dumps(r,separators=(",",":"))+"\n")
 print(json.dumps({"companies":len(r["companies"]),"source":r["source"],"point_in_time_rule":r["point_in_time_rule"]}))
