import unittest
from pilot_risk import size
class PilotRiskTests(unittest.TestCase):
 def test_limits(self):
  r=size(entry=136.67,stop=130)
  self.assertLessEqual(r['notional'],12500)
  self.assertLessEqual(r['max_theoretical_planned_loss'],125)
  self.assertFalse(r['orders_enabled'])
 def test_no_zero_or_bad_stop(self):
  for x in (0,-1,136.67,140):
   with self.assertRaises(ValueError):size(entry=136.67,stop=x)
 def test_cannot_raise_limits(self):
  with self.assertRaises(ValueError):size(entry=136.67,stop=130,risk_fraction=.01)
  with self.assertRaises(ValueError):size(entry=136.67,stop=130,exposure_fraction=.75)
if __name__=='__main__':unittest.main()
