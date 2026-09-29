import unittest
from extreme_event_study import direction

class ExtremeOutcomeTests(unittest.TestCase):
    def test_gap_directions(self):
        e=[dict(type="GAP",direction="UP")]
        self.assertEqual(direction(e,"GAP_CONTINUATION"),"LONG")
        self.assertEqual(direction(e,"GAP_FADE"),"SHORT")
    def test_shock_directions(self):
        e=[dict(type="EXTREME_DAILY_RETURN",direction="DOWN")]
        self.assertEqual(direction(e,"SHOCK_CONTINUATION"),"SHORT")
        self.assertEqual(direction(e,"SHOCK_FADE"),"LONG")
    def test_range_close(self):
        self.assertEqual(direction([dict(type="EXTREME_RANGE",close_location=.9)],"RANGE_CONTINUATION"),"LONG")
        self.assertEqual(direction([dict(type="EXTREME_RANGE",close_location=.1)],"RANGE_CONTINUATION"),"SHORT")
        self.assertIsNone(direction([],"GAP_FADE"))
if __name__=="__main__":unittest.main()
