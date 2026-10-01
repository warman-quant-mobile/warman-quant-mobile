#!/usr/bin/env python3
"""Tenbagger historical PIT pilot. Frozen protocol; diagnostic until historical universe includes failures/delistings."""
import argparse,json,math
from pathlib import Path
import pandas as pd
import yfinance as yf

def facts_asof(company, date):
    out={}
    for key,blob in company.get("facts",{}).items():
        xs=[x for x in blob.get("facts",[]) if x.get("filed") and x["filed"]<=date and x.get("val") is not None]
        if xs:
            xs.sort(key=lambda x:(x.get("filed",""),x.get("end","")))
            out[key]=xs[-1]["val"]
    return out

def growth(a,b):
    if b in (None,0) or a is None:return None
    return a/b-1

def main():
    a=argparse.ArgumentParser();a.add_argument("--pit",default="output/sec_point_in_time.json");a.add_argument("--out",default="signals/tenbagger_pit_pilot_v1.json");x=a.parse_args()
    d=json.load(open(x.pit)); cik_ticker={"320193":"AAPL","789019":"MSFT","1045810":"NVDA","1018724":"AMZN","1326801":"META","1318605":"TSLA"}
    rows=[]
    for cik,t in cik_ticker.items():
        c=d["companies"].get(cik)
        if not c:continue
        px=yf.download(t,start="2011-01-01",auto_adjust=True,progress=False)
        if px.empty:continue
        close=px["Close"]; close=close.iloc[:,0] if hasattr(close,"columns") else close
        for y in range(2013,2022):
            dt=f"{y}-06-30"; hist=close.loc[:dt]
            if hist.empty:continue
            p=float(hist.iloc[-1]); f=facts_asof(c,dt)
            rev=f.get("revenue"); ni=f.get("net_income"); assets=f.get("assets"); eq=f.get("equity"); cfo=f.get("cfo"); capex=f.get("capex")
            q=(ni/assets if ni is not None and assets not in (None,0) else None)
            fcf=(cfo-capex if cfo is not None and capex is not None else None)
            mom=None
            if len(hist)>252:
                mom=p/float(hist.iloc[-252])-1
            fut=close.loc[dt:]
            labels={}
            for yrs in (3,5):
                z=fut.loc[:f"{y+yrs}-06-30"]
                if len(z)>1:
                    mx=float(z.max())/p
                    term=float(z.iloc[-1])/p
                    labels[str(yrs)+"y"]={"max_multiple":round(mx,3),"terminal_multiple":round(term,3),"2x":mx>=2,"3x":mx>=3,"5x":mx>=5,"10x":mx>=10}
            rows.append({"cik":cik,"ticker":t,"date":dt,"price":round(p,4),"quality_roa_proxy":q,"fcf":fcf,"momentum_12m":mom,"labels":labels})
    # Pure PIT pilot score uses only rankable fields present across cohort/date; no outcome fitting.
    df=pd.DataFrame(rows)
    for col in ["quality_roa_proxy","momentum_12m"]:
        df[col+"_pct"]=df.groupby("date")[col].rank(pct=True)
    df["pilot_score"]=0.5*df["quality_roa_proxy_pct"].fillna(.5)+0.5*df["momentum_12m_pct"].fillna(.5)
    rows=df.sort_values(["date","pilot_score"],ascending=[True,False]).to_dict("records")
    summary={}
    for h in ("3y","5y"):
        valid=[r for r in rows if h in r["labels"]]
        for lab in ("2x","3x","5x","10x"):
            base=sum(r["labels"][h][lab] for r in valid)/len(valid) if valid else None
            top=[]
            for date,g in pd.DataFrame(valid).groupby("date"):
                top.extend(g.sort_values("pilot_score",ascending=False).head(2).to_dict("records"))
            hit=sum(r["labels"][h][lab] for r in top)/len(top) if top else None
            summary[f"{h}_{lab}"]={"base_rate":base,"top2_rate":hit,"lift":hit/base if base and hit is not None else None,"n":len(valid)}
    out={"status":"DIAGNOSTIC_PIT_PILOT_NOT_VALIDATION","universe":"six large US control companies; survivor biased","rule":"facts usable only after SEC filed date; price data through ranking date","summary":summary,"rows":rows}
    Path(x.out).parent.mkdir(parents=True,exist_ok=True);Path(x.out).write_text(json.dumps(out,indent=2,default=str)+"\n")
    print(json.dumps(summary))
if __name__=="__main__":main()
