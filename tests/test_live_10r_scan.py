import unittest
from unittest.mock import patch
from live_10r_scan import scan
class TenRGatingTests(unittest.TestCase):
    def test_no_fabricated_ten_r_from_unverified_data(self):
        # A failed data-quality gate must never return a paper proposal.
        with self.assertRaises(FileNotFoundError):
            scan("/this-folder-does-not-exist")
    def test_no_bypass_for_bad_coverage(self):
        import json,tempfile
        from pathlib import Path
        from datetime import datetime,timezone
        with tempfile.TemporaryDirectory() as t:
            stamp=datetime.now(timezone.utc).isoformat()
            Path(t,"manifest.json").write_text(json.dumps({"generated_at_utc":stamp}))
            Path(t,"quality.json").write_text(json.dumps({"generated_at_utc":stamp,"eligible_symbols":[]}))
            with self.assertRaisesRegex(ValueError,"INSUFFICIENT_COVERAGE"):scan(t)
if __name__=="__main__":unittest.main()
