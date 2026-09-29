import tempfile,unittest
from pathlib import Path
from promotion_gate import assess,run
class PromotionGateTests(unittest.TestCase):
 def test_missing_data_blocks(self):
  a=assess({'isin':'SE0020845709','price_source':'Yahoo crypto spot','kf_eligibility_evidence':'unverified'})
  self.assertEqual(a['status'],'RESEARCH_ONLY_BLOCKED')
  self.assertIn('actual_traded_product_history',a['missing'])
  self.assertFalse(a['orders_enabled'])
 def test_complete_evidence_is_still_not_trade_authorization(self):
  from promotion_gate import REQUIRED
  a=assess(dict({k:'evidence' for k in REQUIRED},independent_forward_passed=True,ledger_replay_passed=True,cost_stress_passed=True,benchmark_passed=True))
  self.assertEqual(a['status'],'REVIEW_ELIGIBLE_NOT_TRADE_AUTHORIZED')
  self.assertFalse(a['orders_enabled'])
 def test_current_register_is_blocked(self):
  with tempfile.TemporaryDirectory() as d:
   r=run(d)
   self.assertTrue(all(x['status']=='RESEARCH_ONLY_BLOCKED' for x in r.values()))
   self.assertTrue((Path(d)/'promotion_gate.json').exists())
if __name__=='__main__':unittest.main()
