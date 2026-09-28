"""Warman Quant v0.5 research scan. Never generates executable orders."""
import argparse, json, zipfile, io
from datetime import timedelta
import pandas as pd
import numpy as np

def scan(path):
    z=zipfile.ZipFile(path)
    m=json.loads(z.read('manifest.json'))
    q=json.loads(z.read('quality.json'))
    generated=pd.Timestamp(m['generated_at_utc']).tz_convert('UTC')
    out=[]
    for symbol in q.get('eligible_symbols',[]):
        info=m['symbols'][symbol]
        h=pd.read_csv(io.BytesIO(z.read(info['1h']['file'])))
        d=pd.read_csv(io.BytesIO(z.read(info['1d']['file'])))
        h['t']=pd.to_datetime(h.timestamp_utc,utc=True)
        h=h[h.t < generated.floor('h')].sort_values('t').copy() # discard forming 1h
        d['session_date']=pd.to_datetime(d.session_date)
        # discard today's daily candle (source exchange session date may differ from UTC)
        d=d[d.session_date.dt.date < generated.date()].sort_values('session_date').copy()
        reasons=[]
        if len(h)<65 or len(d)<210:reasons.append('insufficient history')
        if reasons:
            out.append({'symbol':symbol,'status':'EXCLUDE','reason':'; '.join(reasons)});continue
        # Avoid mistaking weekend/overnight US closures for a signal; this is an age warning, not an exchange calendar.
        age=(generated-h.t.iloc[-1]).total_seconds()/3600
        if age>4 and generated.weekday()<5:reasons.append(f'last hourly bar {age:.1f}h old; verify market session')
        hc=h.Close; dc=d.Close
        ema20=hc.ewm(span=20,adjust=False).mean();ema50=hc.ewm(span=50,adjust=False).mean()
        dema50=dc.ewm(span=50,adjust=False).mean();dema200=dc.ewm(span=200,adjust=False).mean()
        tr=pd.concat([h.High-h.Low,(h.High-hc.shift()).abs(),(h.Low-hc.shift()).abs()],axis=1).max(axis=1)
        atr=float(tr.rolling(14).mean().iloc[-1]);price=float(hc.iloc[-1]);
        longreg=dc.iloc[-1]>dema50.iloc[-1]>dema200.iloc[-1]
        shortreg=dc.iloc[-1]<dema50.iloc[-1]<dema200.iloc[-1]
        hi=float(h.High.iloc[-21:-1].max());lo=float(h.Low.iloc[-21:-1].min())
        direction='LONG' if longreg and ema20.iloc[-1]>ema50.iloc[-1] and price>hi else ('SHORT' if shortreg and ema20.iloc[-1]<ema50.iloc[-1] and price<lo else 'NONE')
        if not np.isfinite(atr) or atr<=0:reasons.append('invalid ATR')
        if info['1h'].get('rejected_rows_file') or info['1d'].get('rejected_rows_file'):reasons.append('source rejected rows; audit')
        status='WATCH' if direction!='NONE' and not reasons else ('BLOCKED' if reasons else 'NO SIGNAL')
        out.append({'symbol':symbol,'status':status,'direction':direction,'close':round(price,5),'atr14':round(atr,5),
          'daily_regime':'UP' if longreg else ('DOWN' if shortreg else 'MIXED'),
          'hourly_ema20':round(float(ema20.iloc[-1]),5),'hourly_ema50':round(float(ema50.iloc[-1]),5),
          'breakout_high20':round(hi,5),'breakdown_low20':round(lo,5),'last_closed_bar_start_utc':str(h.t.iloc[-1]),
          'age_hours':round(age,2),'reason':'; '.join(reasons)})
    return {'generated_at_utc':m['generated_at_utc'],'disclaimer':'Research candidates only. No trade without exchange calendar, executable Nordnet bid/ask, spread, KO, FX, size and stop verification.', 'candidates':out}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('snapshot');a.add_argument('--output');args=a.parse_args()
    report=scan(args.snapshot)
    print(json.dumps(report,indent=2,default=str))
    if args.output:open(args.output,'w').write(json.dumps(report,indent=2,default=str))
