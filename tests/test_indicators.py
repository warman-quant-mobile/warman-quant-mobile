import unittest
from datetime import datetime,timezone,timedelta
from indicators import HOURLY,DAILY,rsi,ema,atr,decide,simulate
class IndicatorTests(unittest.TestCase):
 def test_ranges(self):
  self.assertEqual(rsi(list(range(20)),2),100)
  self.assertEqual(len(ema(list(range(20)),12)),20)
  self.assertEqual(len(HOURLY),8)
  self.assertEqual(len(DAILY),2)
 def test_no_future_bar_in_signal(self):
  t=datetime(2026,1,1,tzinfo=timezone.utc)
  a=[(t+timedelta(hours=i),100+i,101+i,99+i,100.5+i) for i in range(250)]
  self.assertEqual(decide(a,220,'turtle_20'),1)
  self.assertIsInstance(simulate(a,'turtle_20'),list)
if __name__=='__main__':unittest.main()
