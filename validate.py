"""Fail-closed structural checks. Freshness/session suitability checked at scan time."""
import argparse,csv,json,math,zipfile
from datetime import datetime,timezone
from pathlib import Path
p0=argparse.ArgumentParser();p0.add_argument('folder',nargs='?',default='output');p0.add_argument('--min-symbols',type=int,default=18)
args=p0.parse_args();p=Path(args.folder)
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
checks={};fail=[];eligible=[];excluded={}
for name,info in m['symbols'].items():
    checks[name]={};issues=[]
    for interval in ('1h','1d'):
        if interval not in info:
            issues.append(f'{interval}: missing');continue
        f=p/info[interval]['file']
        try:
            with f.open(newline='') as h:
                reader=csv.DictReader(h);rows=list(reader);fields=set(reader.fieldnames or [])
            required={'timestamp_utc','Open','High','Low','Close','Volume'}
            if interval=='1d':required.add('session_date')
            assert required <= fields, 'missing columns'
            assert len(rows)>= (40 if interval=='1h' else 100),'insufficient history'
            times=[r['session_date'] if interval=='1d' else r['timestamp_utc'] for r in rows]
            assert times==sorted(set(times)),'unordered or duplicate timestamps'
            for row in rows:
                o,h,l,c=(float(row[k]) for k in ('Open','High','Low','Close'))
                assert all(map(math.isfinite,(o,h,l,c))) and l>0 and l<=min(o,c)<=max(o,c)<=h,'invalid OHLC'
            checks[name][interval]={'rows':len(rows),'last':times[-1],
              'volume_available':info[interval]['volume_nonzero_rows']>0,
              'last_bar_provisional':info[interval].get('last_bar_provisional',False)}
        except Exception as e:issues.append(f'{interval}: {e}')
    if issues: excluded[name]=issues
    elif all(k in checks[name] for k in ('1h','1d')): eligible.append(name)
quality={'source':m['source'],'generated_at_utc':m['generated_at_utc'],
 'checks':checks,'download_errors':m['errors'],'failures':fail,
 'eligible_symbols':eligible,'excluded_symbols':excluded,
 'note':'Research data only. 1h timestamps are bar STARTS. Drop current partial bar at scan time. Daily is session date.'}
(p/'quality.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
complete=len(eligible)
if complete<args.min_symbols:
    raise SystemExit(f'QUALITY FAIL: {complete} complete instruments (<{args.min_symbols}); excluded: {excluded}')
with zipfile.ZipFile(p/'SCANNA.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(p.glob('*.csv')):z.write(f,f.name)
    for n in ('manifest.json','quality.json'):z.write(p/n,n)
print(f'QUALITY PASS: {complete} complete instruments; excluded: {excluded}. SCANNA.zip created.')
