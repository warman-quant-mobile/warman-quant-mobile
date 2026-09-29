import unittest
import pandas as pd
from extreme_event_research import classify

class ExtremeEventTests(unittest.TestCase):
    def history(self):
        return pd.DataFrame([dict(Open=100.,High=101.,Low=99.,Close=100.) for _ in range(44)])
    def test_gap_continuation(self):
        d=self.history();d.loc[len(d)]=dict(Open=104.,High=108.,Low=103.,Close=107.)
        events=classify(d)
        self.assertTrue(any(e["type"]=="GAP" and e["subtype"]=="GAP_CONTINUATION_WATCH" for e in events))
    def test_gap_fade(self):
        d=self.history();d.loc[len(d)]=dict(Open=104.,High=105.,Low=99.,Close=100.)
        events=classify(d)
        self.assertTrue(any(e["type"]=="GAP" and e["subtype"]=="GAP_FADE_WATCH" for e in events))
    def test_quiet_day_no_event(self):
        d=self.history();d.loc[len(d)]=dict(Open=100.,High=101.,Low=99.,Close=100.)
        self.assertEqual(classify(d),[])
    def test_invalid_ohlc_rejected(self):
        d=self.history();d.loc[len(d)]=dict(Open=104.,High=103.,Low=99.,Close=100.)
        self.assertEqual(classify(d),[])
if __name__=="__main__":unittest.main()
