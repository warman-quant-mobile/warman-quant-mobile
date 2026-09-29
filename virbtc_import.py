"""Fail-closed importer for authentic exchange-traded VIRBTC daily CSV (not BTC spot).

Required CSV: date,open,high,low,close,volume; dates YYYY-MM-DD, SEK prices,
source/ISIN attestation via explicit CLI arguments. No synthetic filling.
"""
import argparse,csv,hashlib,json,math
from datetime import date
from pathlib import Path
ISIN='SE0020845709'
FIRST=date.fromisoformat('2023-09-12')
def ingest(path,out,*,isin,source,currency='SEK'):
 if isin!=ISIN or currency!='SEK' or not source.strip() or source.strip().lower() in ('yahoo crypto spot','synthetic','proxy'):
  raise ValueError('Require attested VIRBTC ISIN, SEK and actual traded-product source')
 raw=Path(path).read_bytes()
 if not raw:raise ValueError('Empty file')
 rows=[];prev=None
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  required={'date','open','high','low','close','volume'}
  if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):raise ValueError('Missing canonical CSV columns')
  for row in reader:
   d=date.fromisoformat(row['date'])
   if d<FIRST or (prev is not None and d<=prev) or d.weekday()>4:raise ValueError('Invalid date, ordering, or weekend')
   vals=[float(row[k]) for k in ('open','high','low','close','volume')]
   o,h,l,c,v=vals
   if not all(math.isfinite(x) for x in vals) or not (0<l<=min(o,c)<=max(o,c)<=h) or v<0:raise ValueError('Invalid OHLCV')
   rows.append(dict(date=d.isoformat(),open=o,high=h,low=l,close=c,volume=v))
   prev=d
 if not rows:raise ValueError('No bars')
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with (out/'virbtc_daily.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 manifest=dict(isin=isin,ticker='VIRBTC',currency=currency,source=source,raw_sha256=hashlib.sha256(raw).hexdigest(),
  first_date=rows[0]['date'],last_date=rows[-1]['date'],rows=len(rows),
  status='IMPORTED_NOT_INDEPENDENTLY_VERIFIED',no_synthetic_bars=True,
  warning='Source attestation is caller-provided; exchange calendar, splits, spreads and product price authenticity require independent verification.')
 (out/'virbtc_manifest.json').write_text(json.dumps(manifest,indent=2))
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--out',default='output/virbtc');p.add_argument('--isin',required=True);p.add_argument('--source',required=True);p.add_argument('--currency',default='SEK')
 a=p.parse_args();print(json.dumps(ingest(a.csv,a.out,isin=a.isin,source=a.source,currency=a.currency),indent=2))
