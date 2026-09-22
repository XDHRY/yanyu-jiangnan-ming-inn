"""Check exported buffer bounds, geometry, UVs, images and manifest parity."""
from pathlib import Path
import json,struct
import numpy as np
P=Path(__file__).resolve().parent
b=(P/'ming_review.glb').read_bytes();magic,version,length=struct.unpack_from('<III',b)
assert (magic,version,length)==(0x46546c67,2,len(b))
n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a
j=json.loads(b[20:20+n]);bn,bt=struct.unpack_from('<II',b,20+n);assert bt==0x004e4942
blob=memoryview(b)[28+n:];assert len(blob)==bn
tris=0
for view in j['bufferViews']:assert view.get('byteOffset',0)+view['byteLength']<=len(blob)
for mesh in j['meshes']:
 pr=mesh['primitives'][0];assert pr['mode']==4
 attrs=pr['attributes'];assert {'POSITION','NORMAL','TEXCOORD_0'}<=attrs.keys()
 a=j['accessors'][attrs['POSITION']];v=j['bufferViews'][a['bufferView']];count=a['count'];assert count%3==0
 arr=np.ndarray((count,11),dtype='<f4',buffer=blob,offset=v['byteOffset'],strides=(44,4))
 assert np.isfinite(arr).all()
 assert np.allclose(np.linalg.norm(arr[:,3:6],axis=1),1,atol=.001)
 pts=arr[:,:3].reshape(-1,3,3)
 area=np.linalg.norm(np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]),axis=1)
 assert np.all(area>1e-10),mesh['name']
 tris+=count//3
for im in j['images']:
 v=j['bufferViews'][im['bufferView']];start=v['byteOffset'];assert bytes(blob[start:start+8])==b'\x89PNG\r\n\x1a\n'
r=json.loads((P/'review/report.json').read_text());assert r['triangles']==tris;assert len(j['meshes'])==r['objects']
names=[m['name'] for m in j['meshes']];assert len(set(names))==len(names)
out={'status':'passed','checks':['glb header and buffer bounds','finite geometry and UVs','unit normals','nondegenerate triangles','embedded PNG signatures','unique object names','report parity'],
 'objects':len(j['meshes']),'triangles':tris,'embedded_images':len(j['images']),
 'not_checked':['full-scene collision','historical accuracy','seamless tiling','Blender render','browser execution (local navigation blocked by browser policy)']}
(P/'review/validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
