#!/usr/bin/env python3
"""Fail-closed research artifact contract. No broker/execution functionality."""
import hashlib,json,os,random
from pathlib import Path

SCHEMA_VERSION=1
RESEARCH_STATUSES={"RESEARCH_ONLY","RESEARCH_WARNING_ONLY","NO_10R_PROPOSALS"}

def dataset_fingerprint(folder="output"):
    p=Path(folder)/"manifest.json"
    if not p.exists(): raise RuntimeError("BLOCKED: missing dataset manifest")
    b=p.read_bytes()
    return {"manifest_sha256":hashlib.sha256(b).hexdigest(),"manifest_bytes":len(b)}

def stamp(payload,engine,folder="output",model_version=None):
    if not isinstance(payload,dict): raise RuntimeError("BLOCKED: artifact must be object")
    status=payload.get("status")
    if status not in RESEARCH_STATUSES: raise RuntimeError(f"BLOCKED: non-research status {status!r}")
    out=dict(payload)
    out["research_contract"]={"schema_version":SCHEMA_VERSION,"engine":engine,
      "dataset":dataset_fingerprint(folder),"model_version":model_version,
      "reproducibility":{"pythonhashseed":os.environ.get("PYTHONHASHSEED","0"),"random_seed":1729},
      "execution":"BLOCKED_RESEARCH_ONLY","human_approval_required":True}
    return out

def validate_artifact(payload):
    c=payload.get("research_contract") if isinstance(payload,dict) else None
    if not c or c.get("schema_version")!=SCHEMA_VERSION: raise RuntimeError("BLOCKED: schema/version mismatch")
    if c.get("execution")!="BLOCKED_RESEARCH_ONLY" or c.get("human_approval_required") is not True:
        raise RuntimeError("BLOCKED: execution isolation violated")
    ds=c.get("dataset",{})
    if len(ds.get("manifest_sha256",""))!=64: raise RuntimeError("BLOCKED: missing dataset fingerprint")
    return True

def set_reproducible(seed=1729):
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError: pass
