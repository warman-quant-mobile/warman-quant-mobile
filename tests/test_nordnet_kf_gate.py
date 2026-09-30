import unittest
from nordnet_kf_gate import promotion_gate, execution_requirements

class NordnetKFGateTests(unittest.TestCase):
    def test_sensors_are_never_trade_candidates(self):
        for symbol in ("VIX","OVX","GVZ","US30Y_YIELD","US10Y_YIELD"):
            self.assertFalse(promotion_gate(symbol)["eligible"])
    def test_unknown_underlying_fails_closed(self):
        self.assertEqual(promotion_gate("OBSCURE_RATE")["status"],"NO_NORDNET_KF_MAPPING")
    def test_mapped_underlying_still_requires_product_quote(self):
        g=promotion_gate("SP500")
        self.assertTrue(g["eligible"])
        self.assertEqual(g["status"],"NORDNET_PRODUCT_AND_QUOTE_REQUIRED")
        self.assertIn("specific Nordnet instrument verified available in KF",execution_requirements())
        self.assertTrue(any(">=10" in x for x in execution_requirements()))

if __name__=="__main__": unittest.main()
