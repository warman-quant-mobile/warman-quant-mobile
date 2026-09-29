import csv,tempfile,unittest
from pathlib import Path
from virbtc_import import ingest,ISIN
class ImportTests(unittest.TestCase):
 def write(self,folder,rows):
  p=Path(folder)/'data.csv'
  with p.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['date','open','high','low','close','volume']);w.writerows(rows)
  return p
 def test_valid_and_provenance(self):
  with tempfile.TemporaryDirectory() as t:
   p=self.write(t,[['2023-09-12',100,110,90,105,1000],['2023-09-13',105,111,99,108,900]])
   m=ingest(p,Path(t)/'out',isin=ISIN,source='Exchange-traded product CSV export')
   self.assertEqual(m['rows'],2);self.assertEqual(len(m['raw_sha256']),64)
   self.assertEqual(m['status'],'IMPORTED_NOT_INDEPENDENTLY_VERIFIED')
 def test_spot_and_wrong_isin_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=self.write(t,[['2023-09-12',100,110,90,105,1000]])
   for isin,source in [(ISIN,'Yahoo crypto spot'),('WRONG','issuer')]:
    with self.assertRaises(ValueError):ingest(p,Path(t)/'out',isin=isin,source=source)
 def test_no_prelaunch_weekend_duplicates_or_bad_ohlc(self):
  cases=[[['2023-09-11',100,110,90,105,1000]],[['2023-09-16',100,110,90,105,1000]],
   [['2023-09-12',100,110,90,105,1000],['2023-09-12',100,110,90,105,1000]],
   [['2023-09-12',100,99,90,105,1000]]]
  for rows in cases:
   with tempfile.TemporaryDirectory() as t:
    p=self.write(t,rows)
    with self.assertRaises(ValueError):ingest(p,Path(t)/'out',isin=ISIN,source='issuer')
if __name__=='__main__':unittest.main()
