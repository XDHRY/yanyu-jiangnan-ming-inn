"""Read exported object bounds: support continuity, headroom and detail budget."""
import json
from pathlib import Path
import numpy as np
records=json.loads(Path('.ci_work/review/scene_objects.json').read_text())
errors=[]
def find(token):return [r for r in records if token in r['name']]
def bounds(r):return np.asarray(r['bounds'])
columns=find('colonnade_post');feet=find('column_plinth_neck');knees=find('queti_curved_knee')
if len(columns)!=16 or len(feet)!=16 or len(knees)!=24:
    errors.append('Missing 16 supported colonnade posts or 24 fitted knee brackets')
for column in columns:
    cb=bounds(column);center=cb.mean(axis=0)
    matching=[p for p in feet if np.linalg.norm(bounds(p).mean(axis=0)[:2]-center[:2])<.001 and cb[0,2] <= bounds(p)[1,2] <= cb[0,2]+.20]
    if len(matching)!=1:errors.append('Column has no fitted stone neck: '+column['name'])
for r in knees:
    b=bounds(r)
    beam_candidates=find('veranda_beam')
    if not any(np.all(np.minimum(b[1],bounds(q)[1])-np.maximum(b[0],bounds(q)[0])>0) for q in beam_candidates):
        errors.append('Knee does not meet its beam: '+r['name'])
    expected_floor=.2 if b[1,2]<3 else 2.9
    if b[0,2]-expected_floor<2.0:errors.append('Knee enters circulation headroom')
for token,expected in [('dougong_profile_arm',12),('eave_round_tile_ends',8),('eave_exposed_rafter_tails',8)]:
    if len(find(token))!=expected:errors.append('Wrong architectural count '+token)
triangles=sum(r['triangles'] for r in records)
if triangles>450000:errors.append('Diagnostic scene exceeds 450k triangle working ceiling')
report={'pass':not errors,'errors':errors,'columns':len(columns),'knees':len(knees),'triangles':triangles,
        'scope':'additive diagnostic joinery only; not full structural certification or runtime budget approval'}
Path('.ci_work/review/architecture-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
