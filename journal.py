"""Fail-closed paper journal integrity. Hash-chain snapshots, never silently bootstrap."""
import hashlib,json,os,tempfile
from pathlib import Path
def canonical(s):return json.dumps(s,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(s):return hashlib.sha256(canonical(s).encode()).hexdigest()
def verify(state,ledger):
 state=Path(state);ledger=Path(ledger)
 if not state.exists() or not ledger.exists():raise RuntimeError('JOURNAL_MISSING: recovery required; refusing paperdesk')
 s=json.loads(state.read_text());l=json.loads(ledger.read_text())
 if not isinstance(l,list) or not l:raise RuntimeError('JOURNAL_EMPTY')
 previous='GENESIS'
 for item in l:
  if item['previous']!=previous:raise RuntimeError('JOURNAL_CHAIN_BROKEN')
  expected=digest(dict(previous=item['previous'],snapshot=item['snapshot'],sequence=item['sequence']))
  if item['hash']!=expected:raise RuntimeError('JOURNAL_HASH_MISMATCH')
  previous=item['hash']
 if digest(s)!=l[-1]['snapshot']:raise RuntimeError('JOURNAL_STATE_MISMATCH')
 return s
def record(state,ledger):
 state=Path(state);ledger=Path(ledger)
 s=json.loads(state.read_text());l=json.loads(ledger.read_text()) if ledger.exists() else []
 if l:verify(state,ledger) # Existing journal must match BEFORE a state mutation; use commit() instead.
 else:commit(state,ledger,s,bootstrap=True)
def commit(state,ledger,s,bootstrap=False):
 state=Path(state);ledger=Path(ledger)
 if bootstrap:
  if state.exists() or ledger.exists():raise RuntimeError('BOOTSTRAP_REQUIRES_EMPTY_PATHS')
  l=[]
 else:
  old=verify(state,ledger);l=json.loads(ledger.read_text())
  if s['equity']<=0:raise RuntimeError('INVALID_EQUITY')
 prev=l[-1]['hash'] if l else 'GENESIS'
 item=dict(previous=prev,snapshot=digest(s),sequence=len(l))
 item['hash']=digest(item);l.append(item)
 state.parent.mkdir(parents=True,exist_ok=True);ledger.parent.mkdir(parents=True,exist_ok=True)
 for path,obj in ((state,s),(ledger,l)):
  fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.journal-')
  with os.fdopen(fd,'w') as f:
   json.dump(obj,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 # A crash between replacements intentionally fails closed, requiring artifact recovery.
def bootstrap(state,ledger):
 from paperdesk import INITIAL
 commit(state,ledger,dict(equity=INITIAL,seen={},pending=[],positions=[],trades=[],events=[]),bootstrap=True)
