#!/usr/bin/env python3
"""Research-only loser exclusion audit. Never reads 2022+."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
def ann(c,k,d):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=d and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")];x.sort(key=lambda z:(z["end"],z["filed"]));q={}
 for z in x:q[z["end"]]=float(z["val"])
 return list(q.items())
def l1(c,k,d):
 x=ann(c,k,d);return x[-1][1] if x else None
def l2(c,k,d):
 x=ann(c,k,d);return (x[-1][1],x[-2][1]) if len(x)>1 else (None,None)
def pct(a,b):return a/b-1 if a is not None and b not in (None,0) else np.nan
def rk(s):return s.rank(pct=True)
def wealth(rs):
 w=np.cumprod(1+np.asarray(rs,float));return {"cagr":float(w[-1]**(1/len(rs))-1),"terminal_multiple":float(w[-1])}
def main():
 p=argparse.ArgumentParser();p.add_argument("--pit",required=True);p.add_argument("--out",required=True);a=p.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={}
 for i in range(0,len(ticks),200):
  b=ticks[i:i+200]
  try:
   q=yf.download(b,start="2011-01-01",end="2022-01-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>36:px[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);pr=px.get(t)
  if pr is None:continue
  for y in range(2014,2021):
   dt=f"{y}-06-30";h=pr.loc[:dt];f=pr.loc[dt:f"{y+1}-06-30"]
   if len(h)<25 or len(f)<10:continue
   rev=l1(c,"revenue",dt);ni=l1(c,"net_income",dt);ass=l1(c,"assets",dt);cfo=l1(c,"cfo",dt);cap=l1(c,"capex",dt);debt=l1(c,"debt",dt);sh,s0=l2(c,"shares",dt)
   if rev is None or ass in (None,0):continue
   rr=h.pct_change().dropna().iloc[-12:]
   rows.append({"ticker":t,"year":y,"ret":float(f.iloc[-1]/h.iloc[-1]-1),"roa":ni/ass if ni is not None else np.nan,"fcfm":((cfo-cap)/rev if cfo is not None and cap is not None and rev else np.nan),"lev":debt/ass if debt is not None else np.nan,"dil":pct(sh,s0),"mom":float(h.iloc[-1]/h.iloc[-13]-1),"vol":float(rr.std()*np.sqrt(12)),"earnings_yield":(ni/(float(h.iloc[-1])*sh) if ni is not None and sh not in (None,0) and float(h.iloc[-1])>0 else np.nan),"loss_firm":1.0 if ni is not None and ni<=0 else 0.0})
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 for y,ix in df.groupby("year").groups.items():
  g=df.loc[ix];bad=(rk(-g.roa).fillna(.5)+rk(-g.fcfm).fillna(.5)+rk(g.lev).fillna(.5)+rk(g.dil).fillna(.5)+rk(-g.mom).fillna(.5)+rk(g.vol).fillna(.5))/6;valbad=(rk(-g.earnings_yield).fillna(.5)+g.loss_firm)/2
  df.loc[ix,"bad"]=bad.values;df.loc[ix,"valbad"]=valbad.values;df.loc[ix,"bad_plus_value"]=((bad+valbad)/2).values
 base=[float(g.ret.mean()-.005) for _,g in df.groupby("year")];bp=wealth(base)
 out={"status":"RESEARCH_ONLY_LOSER_EXCLUSION_AUDIT","window":"2014-2020","warning":"Current-survivor universe; delisted losers underrepresented.","benchmark":bp,"results":{}}
 for model in ["bad","valbad","bad_plus_value"]:
  out["results"][model]={}
  for cut in [.05,.10,.20,.30,.40,.50]:
  rs=[];cap={2:[],3:[],5:[]};dr=[]
  for _,g in df.groupby("year"):
   n=max(1,int(len(g)*cut));drop=set(g.nlargest(n,"bad").index);keep=g.loc[~g.index.isin(drop)];rs.append(float(keep.ret.mean()-.005));dr.append(float(g.loc[list(drop)].ret.mean()))
   for m in [2,3,5]:
    win=set(g.index[g.ret>=m-1]);cap[m].append(1.0 if not win else len(win-drop)/len(win))
  pp=wealth(rs);out["results"][f"exclude_{int(cut*100)}pct"]={"cagr":pp["cagr"],"active_cagr":pp["cagr"]-bp["cagr"],"terminal_multiple":pp["terminal_multiple"],"avg_removed_return":float(np.mean(dr)),"winner_capture_2x":float(np.mean(cap[2])),"winner_capture_3x":float(np.mean(cap[3])),"winner_capture_5x":float(np.mean(cap[5]))}
 Path(a.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out))
if __name__=="__main__":main()
