import unittest
from new_signal_alert import build
class AlertTests(unittest.TestCase):
    def test_no_repeat(self):
        x={"minimum_net_r":10,"proposals":[{"id":"a","indicative_net_r":11,"indicative_stop":100}]}
        self.assertEqual(build(x,x)["count"],0)
    def test_new(self):
        x={"minimum_net_r":10,"proposals":[{"id":"a","indicative_net_r":11,"indicative_stop":100}]}
        self.assertEqual(build(x,{})["count"],1)
    def test_changed(self):
        x={"minimum_net_r":10,"proposals":[{"id":"a","indicative_net_r":11,"indicative_stop":99}]}
        old={"proposals":[{"id":"a","indicative_net_r":11,"indicative_stop":100}]}
        self.assertEqual(build(x,old)["count"],1)
    def test_sub10_rejected(self):
        with self.assertRaisesRegex(ValueError,"SUB_10R"):build({"minimum_net_r":10,"proposals":[{"id":"b","indicative_net_r":9}]},{})
if __name__=="__main__":unittest.main()
