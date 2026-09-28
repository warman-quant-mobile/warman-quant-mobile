"""Fail-closed packaging validation; data freshness is judged again at scan time."""
import csv,json,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1]); m=json.loads((p/'manifest.json').read_text())
assert m['symbols'], 'No symbols collected'
checks={}
for name,info in m['symbols'].items():
    checks[name]={}
    for interval in ('1h','1d'):
        if interval not in info:
            checks[name][interval]='MISSING';continue
        f=p/info[interval]['file']
        with f.open(newline='') as h:
            r=csv.DictReader(h); rows=list(r)
        required={'timestamp_utc','Open','High','Low','Close','Volume'}
        assert required.issubset(r.fieldnames),f'{f}: missing columns'
        assert rows, f'{f}: empty'
        times=[x['timestamp_utc'] for x in rows]
        assert times==sorted(set(times)),f'{f}: unordered/duplicate timestamps'
        checks[name][interval]={'rows':len(rows),'last':times[-1],'volume_available':info[interval]['volume_nonzero_rows']>0}
(p/'quality.json').write_text(json.dumps({'source':m['source'],'generated_at_utc':m['generated_at_utc'],'checks':checks,'download_errors':m['errors'],'note':'Index volume may be unavailable; stale data or missing intervals disqualify live signal.'},indent=2))
with zipfile.ZipFile(p/'SCANNA.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(p.glob('*.csv')):z.write(f,f.name)
    for n in ('manifest.json','quality.json'):z.write(p/n,n)
print('Validated',len(checks),'instruments; generated SCANNA.zip')
