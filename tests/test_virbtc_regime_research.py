import csv
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta
from virbtc_regime_research import run


class RegimeResearchTests(unittest.TestCase):
    def fixture(self):
        d=Path(tempfile.mkdtemp())/'daily.csv'
        day=date(2024,1,1)
        with d.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['date','open','high','low','close','volume'])
            w.writeheader()
            for i in range(700):
                while day.weekday()>4:day+=timedelta(days=1)
                price=100+i*.1+(i%25)*.2
                w.writerow(dict(date=day.isoformat(),open=price,high=price+2,low=price-2,close=price+1,volume=1000))
                day+=timedelta(days=1)
        return d

    def test_research_only_and_all_costs(self):
        r=run(self.fixture())
        self.assertFalse(r['orders_enabled'])
        self.assertEqual(len(r['strategies']),6)
        for x in r['strategies'].values():
            self.assertLessEqual(x['60bps_roundtrip']['final_equity'],x['20bps_roundtrip']['final_equity']+0.01)

    def test_future_bars_cannot_change_completed_evaluation(self):
        p=self.fixture()
        baseline=run(p,end='2026-06-30')
        with p.open('a',newline='') as f:
            w=csv.writer(f)
            w.writerow(['2030-01-01',1000000,1000001,999999,1000000,1000])
        changed=run(p,end='2026-06-30')
        self.assertEqual(baseline['strategies'],changed['strategies'])
        self.assertEqual(baseline['buy_hold_net_mark_to_close'],changed['buy_hold_net_mark_to_close'])

    def test_reject_missing_warmup(self):
        with self.assertRaises(ValueError):run(self.fixture(),start='2024-01-02',end='2024-01-31')


if __name__=='__main__':unittest.main()
