import json
from pathlib import Path
r=json.loads(Path('reports/momentum_leaders_report.json').read_text())
for k,v in r['results'].items():
 rows=v['monthly_returns']
 low=sum(x.get('eligible',0)<500 for x in rows)
 print(k,'months',len(rows),'below_500',low)
