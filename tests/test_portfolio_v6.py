import csv,json,tempfile,unittest
from pathlib import Path
from datetime import date,timedelta
from portfolio_v6 import run
class CryptoPortfolioTests(unittest.TestCase):
 def test_mark_to_market_and_cash(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);start=date(2025,1,1)
   symbols={}
   for s in ('BITCOIN','ETHEREUM','SOLANA'):
    name=s+'_1d.csv';symbols[s]={'1d':{'file':name}}
    with (p/name).open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=['session_date','Open','High','Low','Close']);w.writeheader()
     for i in range(80):
      x=100+i*2
      w.writerow(dict(session_date=(start+timedelta(days=i)).isoformat(),Open=x,High=x+1,Low=x-1,Close=x+.5))
   (p/'manifest.json').write_text(json.dumps({'symbols':symbols}))
   r=run(p)
   self.assertTrue(0<r['final_marked_equity'])
   with (p/'portfolio_v6_equity.csv').open() as f:rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),80)
   self.assertTrue(all(float(x['cash'])>=-0.01 for x in rows))
   self.assertTrue(all(int(x['open_positions'])<=2 for x in rows))
   self.assertTrue(any(int(x['open_positions'])>0 for x in rows), 'Test must reach the position sizing code')
if __name__=='__main__':unittest.main()
