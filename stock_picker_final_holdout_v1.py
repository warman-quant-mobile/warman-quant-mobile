#!/usr/bin/env python3
"""ONE-SHOT final holdout evaluation of the frozen Stock Picker Q/G/M score.
Do not tune weights or concentration from this output. Uses PIT SEC filing dates and
2022-2025 annual cohorts. Current-survivor limitation remains explicit.
"""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,yfinance as yf
def ann(c,k,asof):
 x=[z for z in c.get("facts",{}).get(k,{}).get("facts",[]) if z.get("filed","")<=asof and z.get("form")=="10-K" and z.get("val") is not None and z.get("end")]
 x.sort(key=lambda z:(z["end"],z["filed"]));d={}
 for z in x:d[z["end"]]=float(z["val"])
 return list(d.items())
def l1(c,k,d):x=ann(c,k,d);return x[-1][1] if x else None
def l2(c,k,d):x=ann(c,k,d);return (x[-1][1],x[-2][1]) if len(x)>1 else (None,None)
def pct(a,b):return a/b-1 if a is not None and b not in (None,0) else np.nan
def rk(s):return s.rank(pct=True)
def perf(rs):
 w=np.cumprod(1+np.array(rs));n=len(rs)
 return {"years":n,"cumulative":float(w[-1]-1),"cagr":float(w[-1]**(1/n)-1),"max_drawdown":float(np.min(w/np.maximum.accumulate(w)-1))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--pit",default="output/sec_point_in_time_broad.json");ap.add_argument("--out",default="signals/stock_picker_final_holdout_v1.json");a=ap.parse_args()
 d=json.load(open(a.pit));mp=d["selection"]["ticker_by_cik"];cs=d["companies"];ticks=list(dict.fromkeys(mp.values()));px={}
 for i in range(0,len(ticks),100):
  b=ticks[i:i+100]
  try:
   q=yf.download(b,start="2020-01-01",end="2026-10-01",interval="1mo",auto_adjust=True,progress=False,threads=True,group_by="ticker")
   for t in b:
    try:
     s=(q[t]["Close"] if len(b)>1 else q["Close"]).dropna()
     if len(s)>12:px[t]=s
    except:pass
  except:pass
 rows=[]
 for cik,c in cs.items():
  t=mp.get(cik);p=px.get(t)
  if p is None:continue
  for y in range(2022,2026):
   dt=f"{y}-06-30";h=p.loc[:dt];f=p.loc[dt:f"{y+1}-06-30"]
   if len(h)<13 or len(f)<10:continue
   rev,r0=l2(c,"revenue",dt);op,o0=l2(c,"operating_income",dt);gp,g0=l2(c,"gross_profit",dt);ni=l1(c,"net_income",dt);ass=l1(c,"assets",dt);cfo=l1(c,"cfo",dt);cap=l1(c,"capex",dt);debt=l1(c,"debt",dt);sh,s0=l2(c,"shares",dt)
   if rev is None or ass in (None,0):continue
   e=float(h.iloc[-1]);fcf=(cfo-cap) if cfo is not None and cap is not None else np.nan
   rows.append(dict(ticker=t,year=y,ret=float(f.iloc[-1])/e-1,rev_growth=pct(rev,r0),op_growth=pct(op,o0),gross_growth=pct(gp,g0),roa=(ni/ass if ni is not None else np.nan),fcf_margin=(fcf/rev if rev else np.nan),debt_assets=(debt/ass if debt is not None else np.nan),dilution=pct(sh,s0),momentum=e/float(h.iloc[-13])-1))
 df=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)
 for _,ix in df.groupby("year").groups.items():
  g=df.loc[ix];q=(rk(g.roa).fillna(.5)+rk(g.fcf_margin).fillna(.5)+rk(-g.debt_assets).fillna(.5)+rk(-g.dilution).fillna(.5))/4;gr=(rk(g.rev_growth).fillna(.5)+rk(g.op_growth).fillna(.5)+rk(g.gross_growth).fillna(.5))/3;m=rk(g.momentum).fillna(.5);df.loc[ix,"score"]=(.35*q+.35*gr+.30*m).values
 drag=.005;outres={}
 for k in [5,10,20]:
  s=[];b=[];wr=[];annual=[]
  for y,g in df.groupby("year"):
   top=g.nlargest(min(k,len(g)),"score");sr=float(top.ret.mean()-drag);br=float(g.ret.mean()-drag);wo=top.drop(top.ret.idxmax()) if len(top)>1 else top;wor=float(wo.ret.mean()-drag);s.append(sr);b.append(br);wr.append(wor);annual.append({"year":int(y),"n":len(top),"net_return":sr,"equal_weight_net":br,"winner_removed_net":wor,"best_ticker":str(top.loc[top.ret.idxmax(),"ticker"]),"best_return":float(top.ret.max()),"selected":[{"ticker":str(r.ticker),"score":float(r.score),"ret":float(r.ret)} for _,r in top.iterrows()]})
  ps,pb,pw=perf(s),perf(b),perf(wr);outres[f"top{k}"]={"strategy":ps,"equal_weight":pb,"winner_removed":pw,"active_cagr":ps["cagr"]-pb["cagr"],"winner_removed_active_cagr":pw["cagr"]-pb["cagr"],"annual":annual}
 out={"status":"FINAL_HOLDOUT_OPENED_ONCE","warning":"Weights/concentration were frozen before this run. Current-survivor bias remains; this is not delisting-complete certification.","window":"2022-2025 cohorts","cost_drag":drag,"coverage":{"priced":len(px),"observations":len(df)},"frozen_score":"35% quality + 35% growth + 30% momentum","results":outres}
 Path(a.out).write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out))
if __name__=="__main__":main()

# frozen holdout trigger\n# diagnostics only: exact frozen scores/concentrations; no refit
