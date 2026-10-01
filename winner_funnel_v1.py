#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads(Path("signals/stock_picker_prototype_v2.json").read_text())
rows=[]
for x in d.get("top",[]):
 f=x.get("families",{})
 if not all(k in f for k in ("quality","value","growth","momentum")): continue
 if min(f.values())<.30 or f["quality"]<.55 or f["growth"]<.55 or f["momentum"]<.55: continue
 if float(x.get("market_cap") or 0)<2_000_000_000: continue
 breadth=sum(f[k]>=.70 for k in ("quality","value","growth","momentum"))
 core=.30*f["quality"]+.15*f["value"]+.30*f["growth"]+.25*f["momentum"]
 y=dict(x); y["winner_score"]=round(.8*core+.2*breadth/4,6); y["breadth"]=breadth; rows.append(y)
rows.sort(key=lambda x:x["winner_score"],reverse=True)
out={"status":"LIVE_CHALLENGER_NOT_OOS_VALIDATED","method":"complete Q/V/G/M + breadth + cap filter","candidates":rows[:20],"trade_shortlist":rows[:7]}
Path("signals/winner_funnel_v1.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"eligible":len(rows),"top7":[[x["ticker"],x["winner_score"]] for x in rows[:7]]}))
