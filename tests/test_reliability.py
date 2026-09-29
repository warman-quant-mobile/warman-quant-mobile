import json,tempfile,unittest
from pathlib import Path
from journal import bootstrap,verify,commit
from portfolio_audit import audit
class ReliabilityTests(unittest.TestCase):
 def test_journal_chain_and_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'state.json';l=Path(d)/'ledger.json'
   bootstrap(p,l);s=verify(p,l);s['equity']=100010
   commit(p,l,s);self.assertEqual(verify(p,l)['equity'],100010)
   s['equity']=90000;p.write_text(json.dumps(s))
   with self.assertRaises(RuntimeError):verify(p,l)
 def test_missing_journal_fails(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(RuntimeError):verify(Path(d)/'a',Path(d)/'b')
 def test_capacity_and_risk(self):
  trades=[dict(entry_time=1,exit_time=3,symbol=x,entry=100,exit=120,stop=95,side='LONG') for x in ('A','B','C')]
  r=audit(trades,max_positions=2)
  self.assertEqual(r['closed'],2);self.assertEqual(len(r['rejected']),1)
  self.assertEqual(r['realized_equity'],107960)
if __name__=='__main__':unittest.main()
