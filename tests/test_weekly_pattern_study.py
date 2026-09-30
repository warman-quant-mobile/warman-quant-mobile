import unittest
import pandas as pd
from weekly_pattern_study import outcome

class WeeklyOutcomeTests(unittest.TestCase):
    def frame(self, rows):
        return pd.DataFrame(rows, columns=["Open","High","Low","Close"])

    def test_stop_exits_immediately(self):
        d=self.frame([[100,101,94,95],[95,130,94,125]])
        r=outcome(d,0,100,95,50,"LONG",2,0)
        self.assertEqual(r["exit_reason"],"STOP")
        self.assertAlmostEqual(r["realized_r"],-1.0,places=6)
        self.assertFalse(r["fixed_r_before_stop"]["3"])

    def test_same_bar_stop_wins_over_target(self):
        d=self.frame([[100,121,94,110]])
        r=outcome(d,0,100,95,20,"LONG",1,0)
        self.assertEqual(r["exit_reason"],"STOP")
        self.assertFalse(r["fixed_r_before_stop"]["3"])

    def test_fixed_r_only_before_stop(self):
        d=self.frame([[100,116,99,115],[115,116,94,95]])
        r=outcome(d,0,100,95,50,"LONG",2,0)
        self.assertTrue(r["fixed_r_before_stop"]["3"])
        self.assertFalse(r["fixed_r_before_stop"]["5"])
        self.assertEqual(r["exit_reason"],"STOP")

if __name__=="__main__":
    unittest.main()
