"""Fail-closed instrument-level promotion assessment. Research outputs NEVER authorize orders."""
import argparse,json
from pathlib import Path
REQUIRED=('isin','ticker','venue','currency','first_trade_date','kf_eligibility_evidence','price_source','spread_source','fee_schedule','session_calendar','independent_forward_start','ledger_replay_evidence','cost_stress_evidence','benchmark_evidence')
def assess(item):
 missing=[k for k in REQUIRED if not item.get(k)]
 if item.get('price_source') in ('Yahoo crypto spot','synthetic','proxy'):missing.append('actual_traded_product_history')
 if item.get('kf_eligibility_evidence') in ('assumed','unverified'):missing.append('verified_company_KF_eligibility')
 if not item.get('independent_forward_passed'):missing.append('independent_forward_passed')
 if not item.get('ledger_replay_passed'):missing.append('ledger_replay_passed')
 if not item.get('cost_stress_passed'):missing.append('cost_stress_passed')
 if not item.get('benchmark_passed'):missing.append('benchmark_passed')
 return dict(status='RESEARCH_ONLY_BLOCKED' if missing else 'REVIEW_ELIGIBLE_NOT_TRADE_AUTHORIZED',missing=sorted(set(missing)),orders_enabled=False,trade_instruction_enabled=False)
def run(folder):
 p=Path(folder);items=json.loads((p/'nordnet_candidates.json').read_text())
 report={k:assess(v) for k,v in items.items()}
 (p/'promotion_gate.json').write_text(json.dumps(report,indent=2))
 print('NORDNET PROMOTION GATE:',', '.join(k+'='+v['status'] for k,v in report.items()))
 return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--folder',default='output');a=ap.parse_args();run(a.folder)
