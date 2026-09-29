import unittest
from datetime import datetime,timedelta,timezone
from indicators import decide
from asymmetry import NAMES,simulate
class AuditTests(unittest.TestCase):
 def test_rsi_combo_is_reachable(self):
  t=datetime(2026,1,1,tzinfo=timezone.utc)
  a=[(t+timedelta(hours=i),100+i*.02,101+i*.02,99+i*.02,100+i*.02) for i in range(220)]
  self.assertEqual(decide(a,210,'rsi2_macd'),0)
 def test_asymmetric_simulator_cost_stress(self):
  t=datetime(2026,1,1,tzinfo=timezone.utc)
  a=[(t+timedelta(hours=i),100+i*.04,101+i*.04,99+i*.04,100+i*.04) for i in range(300)]
  for name in NAMES:
   base=simulate(a,name,cost=.002)
   stress=simulate(a,name,cost=.006,slip=.001)
   self.assertIsInstance(base,list)
   self.assertIsInstance(stress,list)
   self.assertEqual(len(base),len(stress))
   for x,y in zip(base,stress):self.assertLess(y[2],x[2])
if __name__=='__main__':unittest.main()
