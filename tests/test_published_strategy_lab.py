import unittest
import pandas as pd
from published_strategy_lab import RULES, signals, simulate

class PublishedStrategyLabTests(unittest.TestCase):
    def bars(self, n=400):
        close=[100+i*.2 for i in range(n)]
        return pd.DataFrame({"Open":close,"High":[x+1 for x in close],
                             "Low":[x-1 for x in close],"Close":close})
    def test_all_rules_present(self):
        found=signals(self.bars(),300,1.5)
        self.assertEqual(set(found),set(RULES))
        self.assertTrue(all(x in (None,"LONG","SHORT") for x in found.values()))
    def test_no_future_data_in_signal(self):
        a=self.bars();b=a.copy()
        b.loc[300:,"Close"]=99999
        self.assertEqual(signals(a,300,1.5),signals(b,300,1.5))
    def test_stop_gap_fills_at_worse_open(self):
        a=self.bars();a.loc[300,["Open","High","Low","Close"]]=[90,91,89,90]
        a.loc[301,["Open","High","Low","Close"]]=[80,81,79,80]
        result=simulate(a,300,"LONG",1.5)
        self.assertEqual(result["outcome"],"STOP")
        self.assertLess(result["realized_r"],-1)
    def test_invalid_short_10r_target_rejected(self):
        a=self.bars();self.assertIsNone(simulate(a,300,"SHORT",30))
if __name__=="__main__":
    unittest.main()
