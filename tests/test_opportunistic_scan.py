import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from opportunistic_scan import scan

class ScanTests(unittest.TestCase):
    def test_stale_manifest_fails_closed(self):
        with TemporaryDirectory() as d:
            p=Path(d)
            (p/"manifest.json").write_text(json.dumps({"generated_at_utc":(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()}))
            (p/"quality.json").write_text(json.dumps({"eligible_symbols":[]}))
            with self.assertRaisesRegex(ValueError,"STALE_EXPORT"): scan(p)
    def test_no_candidates_is_valid(self):
        with TemporaryDirectory() as d:
            p=Path(d);now=datetime.now(timezone.utc)
            (p/"manifest.json").write_text(json.dumps({"generated_at_utc":now.isoformat()}))
            (p/"quality.json").write_text(json.dumps({"eligible_symbols":[]}))
            self.assertEqual(scan(p,now)["status"],"NO_QUALIFIED_CANDIDATES")

if __name__=="__main__": unittest.main()
