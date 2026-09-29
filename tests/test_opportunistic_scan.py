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
            (p/"quality.json").write_text(json.dumps({"eligible_symbols":[],"generated_at_utc":now.isoformat()}))
            with self.assertRaisesRegex(ValueError,"STALE_EXPORT"): scan(p)
    def test_insufficient_coverage_fails_closed(self):
        with TemporaryDirectory() as d:
            p=Path(d);now=datetime.now(timezone.utc)
            (p/"manifest.json").write_text(json.dumps({"generated_at_utc":now.isoformat()}))
            (p/"quality.json").write_text(json.dumps({"eligible_symbols":[]}))
            with self.assertRaisesRegex(ValueError,"INSUFFICIENT_COVERAGE"): scan(p,now)

    def test_mismatched_manifest_fails_closed(self):
        with TemporaryDirectory() as d:
            p=Path(d);now=datetime.now(timezone.utc)
            (p/"manifest.json").write_text(json.dumps({"generated_at_utc":now.isoformat()}))
            (p/"quality.json").write_text(json.dumps({"eligible_symbols":["A"]*18,"generated_at_utc":(now-timedelta(hours=1)).isoformat()}))
            with self.assertRaisesRegex(ValueError,"MISMATCHED_EXPORT"): scan(p,now)

if __name__=="__main__": unittest.main()
