import json,tempfile,unittest
from pathlib import Path
from audit_journal import audit
class AuditGateTests(unittest.TestCase):
 def test_missing_cache_never_bootstraps(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s=p/'state.json';l=p/'ledger.json';r=p/'audit.json'
   result=audit(s,l,r)
   self.assertEqual(result['status'],'QUARANTINED')
   self.assertFalse(result['paperdesk_enabled'])
   self.assertFalse(s.exists());self.assertFalse(l.exists())
   self.assertEqual(json.loads(r.read_text())['status'],'QUARANTINED')
if __name__=='__main__':unittest.main()
