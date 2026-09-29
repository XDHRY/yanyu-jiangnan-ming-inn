"""Validate new low-relief surfaces and the connected roof-roll contract."""
from pathlib import Path
import json,numpy as np,trimesh
records=json.loads(Path('.ci_work/review/scene_objects.json').read_text())
errors=[]
rolls=[r for r in records if '/tile_roll_' in r['name']]
if not rolls or any(r['triangles']!=108 for r in rolls):errors.append('Roof roll topology differs from eight-span closed sweep')
scene=trimesh.load_scene('.ci_work/scene.glb',process=False)
for r in rolls:
    m=scene.geometry[r['name']].copy();m.merge_vertices()
    if not m.is_watertight or not m.is_winding_consistent:errors.append('Roof roll not closed: '+r['name'])
pavers=[r for r in records if 'craft_courtyard_bond' in r['name']]
if len(pavers)<300:errors.append('Courtyard paving field incomplete')
for r in pavers:
    b=np.asarray(r['bounds'])
    if not (np.all(b[0]>=[5.61,5.61,.035]) and np.all(b[1]<=[12.39,8.39,.0501])):errors.append('Paver leaves flush courtyard reserve')
grates=[r for r in records if 'craft_drain_grate' in r['name']]
if len(grates)<150:errors.append('Drain grates incomplete')
if any(r['bounds'][1][2]>.0501 for r in grates):errors.append('Drain cover creates a trip edge')
if len([r for r in records if 'craft_cleat_foot' in r['name']])!=6:errors.append('Six pile-mounted cleats required')
west=[r for r in records if r['layer']=='west_shelter']
columns=[r for r in west if 'west_shelter_column_' in r['name'] and 'base' not in r['name']]
if len(columns)!=4:errors.append('West shelter needs four continuous columns')
reserve=np.array([[-3.6,2.05,.23],[-3.10,3.35,2.2]])
for r in west:
    bb=np.asarray(r['bounds'])
    if np.all(np.minimum(bb[1],reserve[1])-np.maximum(bb[0],reserve[0])>1e-4):errors.append('West shelter east entry blocked: '+r['name'])
    if bb[0,0]<-7.10 or bb[1,0]>-1.9 or bb[1,2]>3.7:errors.append('West shelter exceeds reserved site envelope')
for col in columns:
    cb=np.asarray(col['bounds'])
    bases=[r for r in west if 'column_base' in r['name'] and np.linalg.norm(np.mean(r['bounds'],axis=0)[:2]-cb.mean(axis=0)[:2])<.001]
    if len(bases)!=1 or cb[0,2]>bases[0]['bounds'][1][2]:errors.append('West column not seated')
report={'west_shelter_parts':len(west),'pass':not errors,'errors':errors,'continuous_roof_rolls':len(rolls),'roof_triangles_saved':len(rolls)*84,'courtyard_pavers':len(pavers),'drain_grates':len(grates),'scope':'roof topology and authored hardscape; not full collision or drainage engineering'}
Path('.ci_work/review/courtyard-craft-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
