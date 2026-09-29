"""Manual-only pilot risk calculator; never emits an order or overrides promotion gate."""
import argparse,json,math
def size(capital=25000,risk_fraction=.005,exposure_fraction=.5,entry=None,stop=None,fee_bps=20):
 if not all(math.isfinite(float(x)) for x in (capital,risk_fraction,exposure_fraction,entry,stop,fee_bps)):
  raise ValueError('Nonfinite input')
 if not (capital>0 and 0<risk_fraction<=.005 and 0<exposure_fraction<=.5 and entry>stop>0 and fee_bps>=0):
  raise ValueError('Invalid or out-of-policy risk inputs')
 unit_risk=entry-stop+entry*fee_bps/10000
 qty=max(0,math.floor(min(capital*risk_fraction/unit_risk,capital*exposure_fraction/(entry*(1+fee_bps/20000)))))
 return dict(status='ILLUSTRATIVE_ONLY_NOT_TRADE_AUTHORIZATION',orders_enabled=False,
  max_theoretical_planned_loss=round(qty*unit_risk,2),quantity=qty,notional=round(qty*entry,2),
  pilot_drawdown_halt=round(capital*.05,2),
  caveat='Stops are not guaranteed: gaps, spreads, issuer risk and slippage can exceed planned loss.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--entry',type=float,required=True);p.add_argument('--stop',type=float,required=True);a=p.parse_args()
 print(json.dumps(size(entry=a.entry,stop=a.stop),indent=2))
