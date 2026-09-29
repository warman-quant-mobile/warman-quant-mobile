import csv,json,tempfile,unittest
from datetime import date,timedelta
from pathlib import Path
from virbtc_research import run
class ProductResearchTests(unittest.TestCase):
 def setup(self,p):
  p.mkdir(exist_ok=True)
  days=[];d=date(2023,9,12)
  while len(days)<75:
   if d.weekday()<5:days.append(d)
   d+=timedelta(days=1)
  with (p/'virbtc_daily.csv').open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['date','open','high','low','close','volume'])
   for i,d in enumerate(days):
    price=100+i*.5
    w.writerow([d.isoformat(),price,price+2,price-2,price+1,1000])
  (p/'virbtc_manifest.json').write_text(json.dumps(dict(isin='SE0020845709',currency='SEK',status='IMPORTED_NOT_INDEPENDENTLY_VERIFIED',raw_sha256='a'*64)))
 def test_research_never_authorizes_orders(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.setup(p);r=run(p)
   self.assertFalse(r['orders_enabled']);self.assertEqual(r['sessions'],75)
   self.assertEqual(r['status'],'RESEARCH_ONLY_BLOCKED')
   self.assertTrue((p/'virbtc_research_equity.csv').exists())
 def test_reject_wrong_instrument(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.setup(p);m=json.loads((p/'virbtc_manifest.json').read_text());m['isin']='BAD'
   (p/'virbtc_manifest.json').write_text(json.dumps(m))
   with self.assertRaises(ValueError):run(p)
 def test_reject_short_history(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.setup(p);lines=(p/'virbtc_daily.csv').read_text().splitlines()
   (p/'virbtc_daily.csv').write_text('\n'.join(lines[:10])+'\n')
   with self.assertRaises(ValueError):run(p)
if __name__=='__main__':unittest.main()
