"""Check the authored landscape against circulation and waterline contracts."""
from pathlib import Path
import json, struct
import numpy as np

work = Path('.ci_work')
records = json.loads((work / 'review/scene_objects.json').read_text())
errors = []
trees = [r for r in records if 'tree_tapered_branchwork' in r['name']]
leaves = [r for r in records if 'tree_individual_leaves' in r['name']]
water = [r for r in records if 'canal_ripple_surface' in r['name']]
ferns = [r for r in records if 'bank_fern_fronds' in r['name']]
if len(trees) != 5 or len(leaves) != 10:
    errors.append('Expected five branch assemblies and two leaf batches per tree')
if any('tree_leaf_cluster' in r['name'] or 'tree_leaf_crown' in r['name'] for r in records):
    errors.append('Legacy spherical tree foliage remains')
if len(water) != 1:
    errors.append('Canal must have exactly one authored ripple surface')
else:
    bounds = np.array(water[0]['bounds'])
    if not np.allclose(bounds[:, :2], [[-8, -8], [24, -2]], atol=.001):
        errors.append('Canal boundary moved away from its banks')
    if not (-.791 <= bounds[0, 2] < bounds[1, 2] <= -.769):
        errors.append('Canal wave height threatens the established boat waterline')
if len(ferns) != 7:
    errors.append('Expected seven bank-attached fern clumps')
for rec in leaves + trees + ferns:
    bounds = np.array(rec['bounds'])
    if not np.isfinite(bounds).all():
        errors.append('Nonfinite bounds: ' + rec['name'])
    if rec['layer'] == 'courtyard':
        # Skywell x=5.4..12.6, y=5.4..8.6; reserve 0.15m from the veranda.
        if bounds[0, 0] < 5.55 or bounds[1, 0] > 12.45 or bounds[0, 1] < 5.55 or bounds[1, 1] > 8.45:
            errors.append('Tree intrudes into veranda reserve: ' + rec['name'])
        if bounds[1, 2] > 2.85:
            errors.append('Tree exceeds reviewed height envelope')
    if 'bank_fern' in rec['name']:
        # Keep dock, bridge and centered 2.9m-wide arrival clear.
        for x0, x1 in [(3.2, 5.8), (7.55, 10.45), (19.15, 21.85)]:
            if bounds[1, 0] > x0 and bounds[0, 0] < x1:
                errors.append('Bank foliage crosses a landing route: ' + rec['name'])
# Verify the authored pot plants stay rooted and inside the courtyard reserve.
pot_branches = [r for r in records if 'pot_rooted_branchwork' in r['name']]
pot_leaves = [r for r in records if 'pot_individual_leaves' in r['name']]
pot_soils = [r for r in records if 'pot_soil_surface' in r['name']]
if (len(pot_branches), len(pot_leaves), len(pot_soils)) != (3, 6, 3):
    errors.append('Expected three rooted pot plants with soil and two leaf batches')
if any(r['name'].startswith('pot_leaves') for r in records):
    errors.append('Legacy spherical pot foliage remains')
for branch in pot_branches:
    b = np.array(branch['bounds'])
    if not .40 <= b[0, 2] <= .435:
        errors.append('Pot branch root does not meet soil')
for rec in pot_branches + pot_leaves:
    b = np.array(rec['bounds'])
    if b[0,0] < 5.55 or b[1,0] > 12.45 or b[0,1] < 5.55 or b[1,1] > 8.45 or b[1,2] > 1.05:
        errors.append('Pot plant exceeds courtyard clearance: ' + rec['name'])
# Check exported material values rather than the builder's unused PBR objects.
glb = (work / 'ming_review.glb').read_bytes()
n = struct.unpack_from('<I', glb, 12)[0]
doc = json.loads(glb[20:20+n])
materials = {m['name']: m['pbrMetallicRoughness'] for m in doc['materials']}
for name in ['leaf', 'leaf2']:
    color = materials[name]['baseColorFactor'][:3]
    if max(color) > .22 or color[1] <= color[0]:
        errors.append('Exported foliage color is not restrained linear green: ' + name)
if materials.get('bark', {}).get('roughnessFactor', 0) < .85:
    errors.append('Tree bark must stay rough in the GLB')
report = {'pass': not errors, 'errors': errors, 'trees': len(trees),
          'individual_leaves': sum(r['triangles'] for r in leaves) // 4,
          'bank_fern_clumps': len(ferns), 'rooted_pot_plants': len(pot_branches),
          'scene_triangles': sum(r['triangles'] for r in records),
          'scope': 'landscape envelope and waterline; not full building collision certification'}
(work / 'review/landscape-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['pass'] else 1)
