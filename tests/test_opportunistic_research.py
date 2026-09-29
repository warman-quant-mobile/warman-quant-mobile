import unittest
import pandas as pd
from opportunistic_research import evaluate

class EventStudyTests(unittest.TestCase):
    def bars(self, future):
        prior=[dict(Open=100.,High=101.,Low=99.,Close=100.) for _ in range(40)]
        return pd.DataFrame(prior+future+[dict(Open=100.,High=101.,Low=99.,Close=100.)]*61)
    def test_same_bar_target_and_stop_is_stop(self):
        df=self.bars([dict(Open=100.,High=160.,Low=95.,Close=110.)])
        result=evaluate(df,"LONG",40)
        self.assertEqual(result["outcome"],"STOP")
        self.assertLess(result["realized_r"],0)
    def test_gap_beyond_stop_fills_worse(self):
        df=self.bars([dict(Open=100.,High=101.,Low=99.,Close=100.),
                      dict(Open=90.,High=91.,Low=89.,Close=90.)])
        result=evaluate(df,"LONG",40)
        self.assertEqual(result["outcome"],"STOP")
        self.assertLess(result["realized_r"],-1)
    def test_short_cannot_target_negative_price(self):
        df=self.bars([dict(Open=1.,High=1.1,Low=0.9,Close=1.)])
        self.assertIsNone(evaluate(df,"SHORT",40))

if __name__=="__main__": unittest.main()
