"""Conservative pre-trade economics calculator. Inputs are assumptions, never market quotes."""
import argparse,json,math
p=argparse.ArgumentParser()
p.add_argument('--equity',type=float,default=100000)
p.add_argument('--risk-pct',type=float,default=1)
p.add_argument('--ask',type=float,required=True,help='Verified product ask SEK')
p.add_argument('--bid',type=float,required=True,help='Verified product bid SEK')
p.add_argument('--stop-bid',type=float,required=True,help='Estimated executable bid at underlying stop SEK')
p.add_argument('--target-bid',type=float,required=True,help='Estimated executable bid at target SEK')
p.add_argument('--fees',type=float,default=0,help='Round-trip fixed fees SEK')
p.add_argument('--carry',type=float,default=0,help='Estimated total financing/FX drag SEK')
p.add_argument('--max-allocation-pct',type=float,default=25)
a=p.parse_args()
if not (a.equity>0 and a.ask>0 and 0<=a.bid<=a.ask and 0<=a.stop_bid<a.bid and a.target_bid>a.ask and a.fees>=0 and a.carry>=0):p.error('Invalid prices, target, or costs; verify inputs')
risk=a.equity*a.risk_pct/100; unitrisk=a.ask-a.stop_bid
n=max(0,min(math.floor((risk-a.fees-a.carry)/unitrisk),math.floor(a.equity*a.max_allocation_pct/100/a.ask)))
loss=n*unitrisk+a.fees+a.carry;gain=n*(a.target_bid-a.ask)-a.fees-a.carry
out={'DEMO_NOT_ORDER':True,'quantity':n,'capital_sek':round(n*a.ask,2),'estimated_loss_sek':round(loss,2),'estimated_net_gain_sek':round(gain,2),'net_reward_risk':round(gain/loss,2) if loss>0 else None,'spread_pct':round(100*(a.ask-a.bid)/a.ask,2),'risk_budget_sek':risk,'warning':'Stop is not guaranteed; knockout/gaps may cause total stake loss. Prices must be contract-matched, current and executable. No trade recommendation.'}
print(json.dumps(out,indent=2))
