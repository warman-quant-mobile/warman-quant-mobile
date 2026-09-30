import unittest
import pandas as pd
from intraday_10r_study import evaluate
class Intraday10RTests(unittest.TestCase):
    def test_target(self):
        rows=[{"Open":100,"High":101,"Low":99,"Close":100} for _ in range(60)]
        rows[22]={"Open":100,"High":125,"Low":100,"Close":120}
        x=evaluate(pd.DataFrame(rows),20,"LONG",1,horizon=5)
        self.assertEqual(x["outcome"],"TARGET")
        self.assertGreaterEqual(x["realized_r"],9)
    def test_stop_first(self):
        rows=[{"Open":100,"High":101,"Low":99,"Close":100} for _ in range(60)]
        rows[21]={"Open":100,"High":125,"Low":97,"Close":100}
        x=evaluate(pd.DataFrame(rows),20,"LONG",1,horizon=5)
        self.assertEqual(x["outcome"],"STOP")
if __name__=="__main__":unittest.main()
