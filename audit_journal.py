"""Report-only continuity audit. Never bootstrap, mutate, or claim paperdesk continuity."""
import argparse,json
from pathlib import Path
from journal import verify
def audit(state,ledger,report):
 try:
  s=verify(state,ledger)
  result=dict(status='VERIFIED_LOCAL_SNAPSHOT_ONLY',paperdesk_enabled=False,equity=s['equity'],events=len(s['events']),
   warning='Local snapshot verification cannot prove continuity across workflow runs; paperdesk deliberately quarantined.')
 except (RuntimeError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
  result=dict(status='QUARANTINED',paperdesk_enabled=False,reason=str(e),
   warning='No paperdesk run or implicit reset. Research collection may continue.')
 p=Path(report);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2))
 print('JOURNAL AUDIT:',result['status']);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--ledger',required=True);p.add_argument('--report',required=True);a=p.parse_args()
 audit(a.state,a.ledger,a.report)
