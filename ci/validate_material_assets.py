"""Verify new material provenance, decoded pixels, embedding and wrap modes."""
import json,hashlib,struct
from pathlib import Path
import numpy as np
from PIL import Image
root=Path('.');work=root/'.ci_work'
manifest=json.loads((root/'asset_library_hires/materials_20260929/provenance.json').read_text())
errors=[];stats=[]
for asset in manifest['assets']:
    p=root/asset['file'];raw=p.read_bytes();im=Image.open(p).convert('RGB');a=np.asarray(im,dtype=float)
    if hashlib.sha256(raw).hexdigest()!=asset['sha256']:errors.append('Source hash mismatch: '+str(p))
    if list(im.size)!=asset['size'] or min(im.size)<1024:errors.append('Unexpected texture dimensions')
    if np.std(a)<3:errors.append('Texture appears flat')
    stats.append({'id':asset['id'],'size':list(im.size),'border_mean_abs_difference':float((np.mean(abs(a[0]-a[-1]))+np.mean(abs(a[:,0]-a[:,-1])))/2),'source_sha256':asset['sha256']})
b=(work/'ming_review.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);start=28+n
expected={'wood':'huanghuali.png','woodlight':'huanghuali.png','tile':'black_tile_wet.png','stone':'blue_limestone.png','paving':'blue_limestone_wet.png','foliage':'leaf_albedo.png','foliage2':'leaf_albedo.png'}
for m in d['materials']:
    if m['name'] not in expected:continue
    tx=d['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]
    sampler=d['samplers'][tx['sampler']]
    wrap=33071 if m['name'].startswith('foliage') else 33648
    if sampler['wrapS']!=wrap or sampler['wrapT']!=wrap:errors.append('Incorrect material sampler')
    if m['name'].startswith('foliage') and (m.get('alphaMode')!='MASK' or m.get('alphaCutoff')!=.45 or not m.get('doubleSided')):errors.append('Foliage lost alpha-cutout or double-sided rendering')
    im=d['images'][tx['source']];view=d['bufferViews'][im['bufferView']]
    raw=b[start+view.get('byteOffset',0):start+view.get('byteOffset',0)+view['byteLength']]
    if im['name']!=expected[m['name']] or raw!=(work/'textures'/im['name']).read_bytes():errors.append('Texture embedding mismatch: '+m['name'])
leaf=Image.open(work/'textures/leaf_albedo.png')
if leaf.mode!='RGBA' or leaf.getchannel('A').getextrema()!=(0,255):errors.append('Foliage transparency lost')
foliage_ids={i for i,m in enumerate(d['materials']) if m['name'].startswith('foliage')}
leaf_count=sum(d['accessors'][p['attributes']['POSITION']]['count']//12 for m in d['meshes'] for p in m['primitives'] if p['material'] in foliage_ids)
if leaf_count!=6204:errors.append('Expected 6204 textured tree and pot leaves')
report={'pass':not errors,'errors':errors,'generated_assets':stats,'textured_leaves':leaf_count,'materials_using_new_assets':list(expected),'measured_pbr':False,'exact_seamless_edges_verified':False,'boundary_strategy':'mirrored repeat for surfaces; clamp for cutout foliage'}
(work/'review/material-assets-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
