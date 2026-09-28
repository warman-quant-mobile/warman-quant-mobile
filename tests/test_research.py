import csv,json,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from research import read,run
class ResearchTests(unittest.TestCase):
 def test_future_bar_excluded_and_report_generated(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);path=root/'TEST_1h.csv';start=datetime(2026,1,1,tzinfo=timezone.utc)
   with path.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['timestamp_utc','Open','High','Low','Close']);w.writeheader()
    for i in range(240):
     o=100+i*.03;c=o+.1
     w.writerow(dict(timestamp_utc=(start+timedelta(hours=i)).isoformat(),Open=o,High=c+.2,Low=o-.2,Close=c))
   self.assertEqual(len(read(path,start+timedelta(hours=100))),100)
   (root/'quality.json').write_text(json.dumps(dict(eligible_symbols=['TEST'])))
   (root/'manifest.json').write_text(json.dumps(dict(symbols=dict(TEST={'1h':{'file':path.name}}))))
   report=run(root,start+timedelta(hours=240))
   self.assertEqual(report['candidates'],9)
   self.assertTrue((root/'research_summary.csv').exists())
   self.assertTrue(report['research_only'])
if __name__=='__main__':unittest.main()
