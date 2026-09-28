"""Offline deterministic regression tests: python -m unittest discover -s tests."""
import csv,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from paperdesk import process
class DeskTests(unittest.TestCase):
 def test_bootstrap_trigger_fill_and_idempotence(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);out=root/'output';out.mkdir();state=root/'state.json'
   start=datetime(2026,1,5,tzinfo=timezone.utc)
   path=out/'TEST_1h.csv'
   def write(n,breakout=False):
    with path.open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=['timestamp_utc','Open','High','Low','Close']);w.writeheader()
     for i in range(n):
      o=100.;h=101.;l=99.;close=100.
      if breakout and i==22:o=101;h=104;l=100;close=103
      if breakout and i==23:o=104;h=105;l=103;close=104
      w.writerow(dict(timestamp_utc=(start+timedelta(hours=i)).isoformat(),Open=o,High=h,Low=l,Close=close))
   (out/'quality.json').write_text(json.dumps({'eligible_symbols':['TEST']}))
   (out/'manifest.json').write_text(json.dumps({'symbols':{'TEST':{'1h':{'file':path.name}}}}))
   write(22);process(out,state,start+timedelta(hours=22))
   self.assertEqual(json.loads(state.read_text())['trades'],[])
   write(23,True);process(out,state,start+timedelta(hours=23))
   s=json.loads(state.read_text());self.assertEqual(len(s['pending']),1)
   self.assertEqual(len(s['positions']),0)
   write(24,True);process(out,state,start+timedelta(hours=24))
   s=json.loads(state.read_text());self.assertEqual(len(s['positions']),1)
   process(out,state,start+timedelta(hours=24))
   self.assertEqual(len(json.loads(state.read_text())['positions']),1)
if __name__=='__main__':unittest.main()
