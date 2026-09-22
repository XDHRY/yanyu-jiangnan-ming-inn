from pathlib import Path
import json,math
import numpy as np
import trimesh
from PIL import Image
P=Path(__file__).resolve().parent
s=trimesh.load(P/'scene.glb',force='scene');s.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
errors=[]
for name,m in s.geometry.items():
 if not np.isfinite(m.vertices).all():errors.append('Nonfinite '+name)
 if (m.area_faces<1e-12).any():errors.append('Degenerate '+name)
# Projected triangle hit test: no optional spatial acceleration dependency needed.
def hits(namepart,axis,uv):
 count=0
 for name,m in s.geometry.items():
  if namepart not in name:continue
  dims=[i for i in range(3) if i!=axis];t=m.vertices[m.faces][:,:,dims];v0=t[:,1]-t[:,0];v1=t[:,2]-t[:,0];v2=np.array(uv)-t[:,0];den=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];mask=np.abs(den)>1e-10;den=np.where(mask,den,1);a=(v2[:,0]*v1[:,1]-v2[:,1]*v1[:,0])/den;b=(v0[:,0]*v2[:,1]-v0[:,1]*v2[:,0])/den;count+=int(np.sum(mask&(a>=-1e-7)&(b>=-1e-7)&(a+b<=1+1e-7)))
 return count
checks={'glb_roundtrip_meshes':len(s.geometry),'finite_and_nondegenerate':not errors,'moon_gate_center_clear':hits('moon_gate_wall',0,[3.3,1.35])==0,'upper_floor_courtyard_clear':hits('upper/floor',2,[10.5,7])==0 and hits('upper/continuous_veranda',2,[10.5,7])==0,'stair_hole_clear':hits('upper/upper_floor_stair_cut',2,[15,2.9])==0,'pngs_nonblank':all(np.asarray(Image.open(P/(n+'.png'))).std()>8 for n in ['overview','courtyard','moon_gate','bridge_boat','ground_plan'])}
for k,v in checks.items():
 if v is False:errors.append(k)
report={'checks':checks,'errors':errors,'pass':not errors,'not_tested':['Full-scene BVH collision','Blender execution','Browser interaction','Formal Function/Form/Runtime approvals']};(P/'geometry-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));raise SystemExit(bool(errors))
