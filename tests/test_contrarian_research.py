import unittest
import pandas as pd
from contrarian_research import detect

class ContrarianTests(unittest.TestCase):
    def history(self):
        return pd.DataFrame([dict(Open=100.,High=101.,Low=99.,Close=100.) for _ in range(259)])
    def test_no_crash_no_signal(self):
        df=self.history()
        df.loc[len(df)]=dict(Open=100.,High=101.,Low=99.,Close=100.)
        self.assertIsNone(detect(df))
    def test_crash_without_reclaim_is_not_entry(self):
        df=self.history()
        df.loc[len(df)]=dict(Open=75.,High=76.,Low=73.,Close=74.)
        result=detect(df)
        self.assertEqual(result["stage"],"CRASH_ONLY_NO_ENTRY")
    def test_crash_reclaim_is_watch_only(self):
        df=self.history()
        df.loc[239:258,["Open","High","Low","Close"]]=[75.,76.,72.,75.]
        df.loc[len(df)]=dict(Open=73.,High=77.,Low=70.,Close=76.)
        result=detect(df)
        self.assertEqual(result["stage"],"REVERSAL_WATCH")
        self.assertNotIn("order",result)

if __name__=="__main__":unittest.main()
