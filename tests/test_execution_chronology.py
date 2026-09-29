import unittest
from execution_chronology import Position,session
class Chronology(unittest.TestCase):
 def test_scheduled_exit_at_open_precedes_low_stop(self):
  r=session(0,Position(10,90),opening=100,low=80,scheduled_exit=True,fee_rate=0)
  self.assertEqual(r['cash'],1000)
  self.assertEqual(r['events'][0]['reason'],'scheduled_open')
 def test_gap_stop_fills_at_open_not_stop(self):
  r=session(0,Position(10,90),opening=80,low=70,fee_rate=0)
  self.assertEqual(r['cash'],800)
  self.assertEqual(r['events'][0]['reason'],'stop_gap_open')
 def test_future_intraday_stop_proceeds_cannot_fund_open_entry(self):
  with self.assertRaises(ValueError):
   session(0,Position(10,90),opening=100,low=80,entry_units=1,entry_stop=90,fee_rate=0)
 def test_intraday_stop_after_entry(self):
  r=session(1000,None,opening=100,low=89,entry_units=5,entry_stop=90,fee_rate=0)
  self.assertEqual(r['cash'],950)
  self.assertEqual([e['phase'] for e in r['events']],['open','intraday'])
 def test_scheduled_exit_can_fund_open_entry(self):
  r=session(0,Position(10,90),opening=100,low=95,scheduled_exit=True,entry_units=5,entry_stop=90,fee_rate=0)
  self.assertEqual(r['cash'],500)
  self.assertIsNotNone(r['position'])
if __name__=='__main__':unittest.main()
