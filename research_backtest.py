"""Exploratory research only: fixed-rule 1H trend continuation, next-bar fills.
Not an executable Nordnet ETP backtest; no leverage, KO, overnight funding or product spread.
"""
import argparse,io,json,zipfile
import numpy as np,pandas as pd
ap=argparse.ArgumentParser();ap.add_argument('snapshot');ap.add_argument('--cost-bps-roundtrip',type=float,default=20)
a=ap.parse_args()
z=zipfile.ZipFile(a.snapshot)
m=json.loads(z.read('manifest.json'))
out=[]
for name,info in m['symbols'].items():
    if '1h' not in info:continue
    d=pd.read_csv(io.BytesIO(z.read(info['1h']['file'])))
    d['t']=pd.to_datetime(d.timestamp_utc,utc=True)
    cutoff=pd.Timestamp(m['generated_at_utc']).floor('h')
    d=d[d.t<cutoff].sort_values('t').reset_index(drop=True)
    if len(d)<100:continue
    close=d.Close;ema20=close.ewm(span=20,adjust=False).mean()
    ema50=close.ewm(span=50,adjust=False).mean()
    # Signal on CLOSED bar i, trade at OPEN of next available bar i+1.
    # Exit at OPEN of i+7 (six-bar holding period); gap between sessions included.
    trades=[]
    for i in range(55,len(d)-7):
        direction=1 if ema20.iloc[i]>ema50.iloc[i] and close.iloc[i]>d.High.iloc[i-20:i].max() else (
          -1 if ema20.iloc[i]<ema50.iloc[i] and close.iloc[i]<d.Low.iloc[i-20:i].min() else 0)
        if not direction:continue
        entry=float(d.Open.iloc[i+1]);exit_=float(d.Open.iloc[i+7])
        if entry<=0 or exit_<=0:continue
        gross=direction*(exit_/entry-1)
        net=gross-a.cost_bps_roundtrip/10000
        trades.append((i,net))
    if not trades:
        out.append((name,0,None,None,None,None));continue
    split=int(len(d)*.7)
    ins=[v for i,v in trades if i<split];oos=[v for i,v in trades if i>=split]
    out.append((name,len(trades),len(oos),round(np.mean(ins)*100,3) if ins else None,
      round(np.mean(oos)*100,3) if oos else None,
      round(sum(v>0 for v in oos)/len(oos)*100,1) if oos else None))
r=pd.DataFrame(out,columns=['symbol','trades','OOS_trades','IS_avg_net_pct','OOS_avg_net_pct','OOS_win_pct'])
print('Exploratory only. 1H ~60d, fixed rule, 20bp assumed round-trip cost, overlapping signals, no product simulation.')
print(r.to_string(index=False))
