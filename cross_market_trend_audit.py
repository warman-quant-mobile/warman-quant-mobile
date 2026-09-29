"""Cross-market falsification audit for frozen SMA50/SMA60 rules.
Input: locally supplied Warman-Quant-Data 10.zip; raw data never committed.
NOT a tradable portfolio: index/futures/proxy/foreign currency series and
fractional research units; no broker, FX, dividends or rolls verified.
"""
import argparse,csv,hashlib,io,json,math,zipfile
from pathlib import Path
def run(archive):
 raw=Path(archive).read_bytes();z=zipfile.ZipFile(io.BytesIO(raw));out=[]
 for name in sorted(n for n in z.namelist() if n.endswith('_1d.csv') and '/' not in n and '_rejected' not in n):
  bars=[]
  for r in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))):
   if r['session_date']>'2026-09-28':continue
   try:
    o,h,l,c=[float(r[k]) for k in ('Open','High','Low','Close')]
    if all(math.isfinite(v) and v>0 for v in (o,h,l,c)) and l<=min(o,c)<=max(o,c)<=h:bars.append((r['session_date'],o,c))
   except (ValueError,KeyError):continue
  bars.sort()
  if len(bars)<210:continue
  start=next((i for i,b in enumerate(bars) if b[0]>='2025-01-02' and i>=201),None)
  if start is None or len(bars)-start<100:continue
  item=dict(instrument=name.removesuffix('_1d.csv'),start=bars[start][0],end=bars[-1][0],sessions=len(bars)-start,
   buy_hold_gross_pct=round(100*(bars[-1][2]/bars[start][1]-1),1))
  for n in (50,60):
   cash=25000.;units=0.;peak=25000.;dd=0.;turns=0
   for i in range(start,len(bars)):
    date,o,c=bars[i]
    signal=bars[i-1][2]>sum(v[2] for v in bars[i-n-1:i-1])/n
    if units and not signal:cash+=units*o*.999;units=0.;turns+=1
    elif not units and signal:units=cash/(o*1.001);cash=0.;turns+=1
    equity=cash+units*c;peak=max(peak, equity);dd=max(dd,1-equity/peak)
   item['sma'+str(n)+'_net_pct']=round(100*(equity/25000-1),1)
   item['sma'+str(n)+'_drawdown_pct']=round(100*dd,1)
   item['sma'+str(n)+'_transactions']=turns
  out.append(item)
 return dict(status='EXPLORATORY_ONLY',orders_enabled=False,source_sha256=hashlib.sha256(raw).hexdigest(),
  method='Prior close versus preceding N closes SMA; next open; 10bps per side; fractional research units; 2025 onward where 201 bars warmup; each asset independent.',
  limitations='Previously inspected, not untouched OOS. Different start dates. Source includes spot, futures proxies, indices and different currencies. No FX, dividends, roll, brokerage, spread or real product mapping. Not an investable portfolio.',
  instruments=out,beat_gross_hold={str(n):sum(r['sma'+str(n)+'_net_pct']>r['buy_hold_gross_pct'] for r in out) for n in (50,60)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--out',default='cross_market_trend_audit.json');a=p.parse_args()
 result=run(a.archive);Path(a.out).write_text(json.dumps(result,indent=2));print('Eligible:',len(result['instruments']),'beat gross hold:',result['beat_gross_hold'])
