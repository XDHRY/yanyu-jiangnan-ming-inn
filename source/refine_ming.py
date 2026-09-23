"""Reproducible Ming-inspired material and joinery review, metre units, no paid APIs.
Run: python refine_ming.py. Generated texture sources remain unmodified.
This is an art-direction review, not historical reconstruction or final approval.
"""
from pathlib import Path
import json, math, base64, gzip, hashlib
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial as BasePBRMaterial
class PBRMaterial(BasePBRMaterial):
 def __hash__(self):
  if not hasattr(self,"_fixed_hash"):self._fixed_hash=super().__hash__()
  return self._fixed_hash
import types
b=types.ModuleType('base_geometry');b.__file__=str(Path(__file__).with_name('build_scene.py'))
exec(Path(b.__file__).read_text().split('# Site and water.')[0],b.__dict__)
loaded=trimesh.load_scene(Path(__file__).with_name('scene.glb'),process=False)
b.records=json.loads(Path(__file__).with_name('scene_objects.json').read_text())['objects']
for rec in b.records:
 m=loaded.geometry[rec['name']]
 b.S.add_geometry(m,node_name=rec['name'],geom_name=rec['name'])
print('Loaded existing geometry',len(b.records),flush=True)

P=Path(__file__).resolve().parent
source={k:Image.open(P/'textures'/v).convert('RGB') for k,v in {
 'wood':'huanghuali.png','woodlight':'huanghuali.png','fabric':'teal_brocade.png',
 'plaster':'lime_plaster.png','stone':'blue_limestone.png','paving':'blue_limestone_wet.png','tile':'black_tile_wet.png',
 'lotus':'lotus_panel.png','lacquer':'lacquer_black_gold.png','metal':'brass_aged.png','paper':'paper_screen.png'}.items()}
# Wet architectural surfaces use broad, restrained highlights rather than mirror-like bands.
# The cool factors keep the stone/tile family blue-black without washing to neutral gray.
base_factors={
 'tile':[185,198,208,255],
 'paving':[198,214,224,255],
 # Warm, slightly muted paper keeps the screen distinct from plaster without reading as opaque plastic.
 'paper':[248,242,232,255],
}
for k,im in source.items():
 b.M[k]=PBRMaterial(name=k,baseColorTexture=im,baseColorFactor=base_factors.get(k,[255,255,255,255]),
  roughnessFactor={'wood':.43,'woodlight':.45,'fabric':.8,'lotus':.42,'lacquer':.31,'metal':.41,'paper':.76,'tile':.34,'paving':.42}.get(k,.73),
  metallicFactor=.68 if k=='metal' else 0)
b.COL['lotus']='875324';b.COL['brass']='b39a59';b.COL['celadon']='92bab0'
# A slightly deeper aged-brass response keeps gold marks separate from pale paper and plaster.
b.M['brass']=PBRMaterial(name='brass',baseColorFactor=[158,121,57,255],roughnessFactor=.40,metallicFactor=.70)
b.M['celadon']=PBRMaterial(name='celadon',baseColorFactor=[146,186,176,255],roughnessFactor=.24,metallicFactor=0)

# Remove draft chair parts, tea counters and window sticks before inserting fitted joinery.
# Keep the exact source room boundaries, existing actual skywell and stair cutout.
removed=[]
for rec in list(b.records):
 n=rec['name'];bounds=np.array(rec['bounds']);center=bounds.mean(axis=0)
 tea=(0<center[0]<6 and 0<center[1]<4)
 if any(t in n for t in ['window_lattice','bamboo_blind']) or (tea and any(t in n for t in ['counter_','table_surface','chair_surface','chair_back','furniture_leg','teapot_'])):
  b.S.delete_geometry(n);b.records.remove(rec);removed.append(n)

def box(name,c,d,mat='wood'):return b.box(name,c,d,mat)
def rod(name,a,c,r=.012,mat='wood',sections=12):return b.beam(name,a,c,r,mat,sections)
def frame(name,x,y,z,w,h,t=.035,depth=.065,mat='wood'):
 for xx in [x-w/2+t/2,x+w/2-t/2]:box(name+'_stile',(xx,y,z+h/2),(t,depth,h),mat)
 for zz in [z+t/2,z+h-t/2]:box(name+'_rail',(x,y,zz),(w-2*t,depth,t),mat)
def ring(name,c,r,t=.008,mat='brass'):
 v=trimesh.creation.torus(major_radius=r,minor_radius=t,major_sections=32,minor_sections=8)
 v.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));v.apply_translation(c);return b.add(name,v,mat)
def curved(name,points,r=.02,mat='wood'):
 for a,c in zip(points[:-1],points[1:]):rod(name,a,c,r,mat)
def transform_new(start,T):
 for rec in b.records[start:]:
  m=b.S.geometry[rec['name']];m.apply_transform(T);rec['bounds']=m.bounds.round(5).tolist()

def lattice(x,y,z,w,h):
 frame('lattice_frame',x,y,z,w,h,.038,.075)
 # A small repeated square-and-cross vocabulary, with real depth and open cells.
 cols=max(2,round(w/.25));rows=max(2,round(h/.28));dx=(w-.10)/cols;dz=(h-.10)/rows
 for i in range(cols+1):
  xx=x-(w-.10)/2+i*dx;rod('lattice_mullion',(xx,y,z+.05),(xx,y,z+h-.05),.010)
 for j in range(rows+1):
  zz=z+.05+j*dz;rod('lattice_transom',(x-w/2+.05,y,zz),(x+w/2-.05,y,zz),.010)
 for i in range(cols):
  for j in range(rows):
   if (i+j)%2:continue
   cx=x-(w-.10)/2+(i+.5)*dx;cz=z+.05+(j+.5)*dz
   frame('step_pattern',cx,y-.004,cz-dz*.26,dx*.52,dz*.52,.014,.025)
   for side in [-1,1]:rod('pattern_attachment',(cx+side*dx*.26,y,cz),(cx+side*dx*.5,y,cz),.007)

def lotus_motif(x,y,z,w,h):
 # One restrained lotus medallion gives the central upper entrance window a
 # period cue while keeping the surrounding lattice open.
 cx=x;cy=y-.052;cz=z+h*.53
 for side in [-1,1]:
  dx=side*.19
  curved('lotus_petal',[(cx,cy,cz),(cx+dx*.58,cy,cz+.105),(cx+dx,cy,cz),(cx+dx*.58,cy,cz-.105),(cx,cy,cz)],.010,'woodlight')
 curved('lotus_center',[(cx,cy,cz-.02),(cx,cy,cz+.13),(cx,cy,cz+.24),(cx,cy,cz+.13),(cx,cy,cz-.02)],.011,'woodlight')
 curved('lotus_cup',[(cx-.24,cy,cz-.09),(cx,cy,cz-.17),(cx+.24,cy,cz-.09)],.011,'woodlight')
 ring('lotus_seed',(cx,cy-.006,cz+.015),.025,.006,'brass')

def panel(x,y,z,w,h):
 box('lotus_panel_solid',(x,y,z+h/2),(w,.034,h),'lotus')
 frame('panel_molding',x,y-.019,z,w,h,.025,.025)
 frame('fine_brass_inlay',x,y-.034,z+.035,w-.07,h-.07,.0035,.004,'brass')

def screen_leaf(x,y,z,w=.78,h=2.26):
 frame('screen_main_frame',x,y,z,w,h,.048,.095)
 panel(x,y-.008,z+.048,w-.085,.54)
 lattice(x,y,z+.588,w-.085,h-.636)
 for zz in [z+.4,z+1.85]:
  box('screen_hinge',(x+w/2-.012,y-.057,zz),(.045,.016,.105),'brass')
  rod('hinge_pin',(x+w/2+.007,y-.062,zz-.063),(x+w/2+.007,y-.062,zz+.063),.008,'brass')

def plaque_glyphs(x,y,z):
 # Three restrained seal-script-like marks keep the lacquer plaque legible at 720 px
 # without pretending to be a text renderer or adding a modern signboard.
 for dx in [-.58, 0.0, .58]:
  rod('plaque_glyph_stroke',(x+dx-.07,y-.064,z-.18),(x+dx+.06,y-.064,z+.18),.014,'brass',8)
  rod('plaque_glyph_cross',(x+dx-.13,y-.064,z+.015),(x+dx+.13,y-.064,z+.015),.012,'brass',8)
  rod('plaque_glyph_base',(x+dx-.09,y-.064,z-.20),(x+dx+.09,y-.064,z-.20),.010,'brass',8)
 ring('plaque_seal',(x,y-.066,z+.12),.06,.010,'brass')

def chair(x,y,z,angle=0):
 start=len(b.records)
 box('chair_seat',(0,0,z+.46),(.55,.49,.055))
 box('brocade_cushion',(0,-.015,z+.501),(.46,.40,.035),'fabric')
 for xx in [-.22,.22]:
  for yy in [-.18,.18]:rod('tapered_chair_leg',(xx*1.09,yy*1.08,z),(xx,yy,z+.46),.023)
 for yy in [-.18,.18]:rod('chair_stretcher',(-.225,yy,z+.18),(.225,yy,z+.18),.016)
 for xx in [-.22,.22]:rod('side_stretcher',(xx,-.18,z+.22),(xx,.18,z+.22),.016)
 pts=[(.285*math.cos(t),.225*math.sin(t)-.02,z+.79+.09*math.sin(t)) for t in np.linspace(-.18,math.pi+.18,33)]
 curved('horseshoe_arm',pts,.024)
 for xx in [-.26,.26]:rod('arm_support',(xx,-.025,z+.46),(xx,-.025,z+.8),.019)
 for xx in [-.20,.20]:rod('back_support',(xx,.17,z+.46),(xx,.17,z+.86),.020)
 # S-curved back splat with a small brass medallion.
 pts=[(0,.20+.02*math.sin(t*math.pi*2),z+.48+t*.37) for t in np.linspace(0,1,16)]
 for a,c in zip(pts[:-1],pts[1:]):
  box('curved_back_splat',((a[0]+c[0])/2,(a[1]+c[1])/2,(a[2]+c[2])/2),(.105,.026,.03))
 ring('back_medallion',(0,.175,z+.73),.032,.004)
 T=trimesh.transformations.rotation_matrix(angle,[0,0,1]);T[:2,3]=[x,y];transform_new(start,T)

def tea_set(x,y,z):
 box('tea_table',(x,y,z+.75),(1.85,.83,.065))
 box('table_inset',(x,y,z+.786),(1.65,.64,.008),'woodlight')
 for dx in [-.79,.79]:
  for dy in [-.30,.30]:
   rod('table_leg',(x+dx,y+dy,z),(x+dx*.98,y+dy*.98,z+.72),.034)
 for dy in [-.31,.31]:box('table_apron',(x,y+dy,z+.65),(1.57,.035,.13))
 box('tea_tray',(x,y,z+.808),(.62,.38,.033),'woodlight')
 b.lathe('celadon_teapot',(x,y,z+.825),[(0,0),(.01,.06),(.08,.105),(.13,.07),(.15,.065),(.155,0)],'celadon',48)
 rod('teapot_spout',(x+.07,y,z+.89),(x+.17,y,z+.96),.024,'celadon',24)
 ring('teapot_handle',(x-.095,y,z+.91),.052,.01,'celadon')
 for dx,dy in [(-.22,-.11),(.22,-.11),(.22,.11),(-.22,.11)]:
  b.lathe('celadon_cup',(x+dx,y+dy,z+.825),[(0,0),(.008,.028),(.047,.036),(.047,.03),(.012,.024)],'celadon',32)
 # Small aged-brass incense burner: a near-field material anchor with negligible scene cost.
 b.lathe('bronze_incense_burner',(x+.48,y,z+.825),[(0,0),(.012,.05),(.055,.075),(.10,.07),(.125,.045),(.13,0)],'metal',32)
 for ang in [0,math.pi]:
  rod('incense_burner_handle',(x+.48+math.cos(ang)*.055,y+math.sin(ang)*.055,z+.90),(x+.48+math.cos(ang)*.11,y+math.sin(ang)*.11,z+.94),.012,'metal',12)

plaque_glyphs(9,-.34,2.50)

for level,filename in enumerate(['ground.json','upper.json']):
 b.layer='ground' if level==0 else 'upper';z=.2+level*2.7
 data=json.loads((P/filename).read_text())
 for o in data['openings']:
  if o['kind']!='window':continue
  w=next(w for w in data['walls'] if w['id']==o['wall']);a=np.array(w['from']);c=np.array(w['to']);u=(c-a)/np.linalg.norm(c-a)
  start=len(b.records);lattice(0,0,z+o['sillM']+.04,o['widthM']-.08,o['heightM']-.08)
  if level==1 and abs(o['at'][0]-9)<.1 and abs(o['at'][1])<.1:
   lotus_motif(0,0,z+o['sillM']+.04,o['widthM']-.08,o['heightM']-.08)
  T=trimesh.transformations.rotation_matrix(math.atan2(u[1],u[0]),[0,0,1]);T[:2,3]=o['at'];transform_new(start,T)
 for x in [1.2,1.98,2.76,3.54,4.32]:screen_leaf(x,3.78,z+.03)
 tea_set(2.75,2,z)
 for x in [2.22,3.28]:
  chair(x,1.14,z,math.pi);chair(x,2.86,z,0)
 for f in data['fixtures']:
  if f['kind'] not in ['wardrobe','dresser']:continue
  start=len(b.records);w=f['widthM'];d=f['depthM'];h=1.8 if f['kind']=='wardrobe' else .8
  for xx in [-w*.25,w*.25]:
   panel(xx,-d/2-.02,z+.14,w*.46,min(.42,h-.25))
  if h>1:frame('cabinet_raised_panel',xx,-d/2-.03,z+.65,w*.46,.99,.024,.022)
  T=trimesh.transformations.rotation_matrix(math.radians(f['rotDeg']),[0,0,1]);T[:2,3]=f['at'];transform_new(start,T)

# Integrate manufactured Ming components from component_factory
import component_factory as cf
bridge = cf.ComponentBuilderBridge(b, layer='ornament')

# 1. Altar table with scholar rock, porcelain vase, brush pot and scroll basket in the tea room
b.layer = 'ornament'
cf.build_altar_table(bridge, x=2.75, y=3.68, z=0.22, rotDeg=0, length=2.0, width=0.46, height=0.84)
cf.build_scholar_rock(bridge, x=2.35, y=3.68, z=0.22 + 0.84, scale=0.85)
cf.build_porcelain_vase(bridge, x=3.15, y=3.68, z=0.22 + 0.84, scale=0.85)
cf.build_brush_pot(bridge, x=1.95, y=3.68, z=0.22 + 0.84, scale=0.85)
cf.build_bamboo_scroll_basket(bridge, x=1.55, y=3.65, z=0.22, scale=0.90)

# 2. Four-panel folding screen providing atmospheric division in reception area
cf.build_four_panel_screen(bridge, x=4.85, y=2.0, z=0.22, rotDeg=90, angle_deg=8, width=2.1, height=1.85)

# 3. Jiangnan bamboo clusters framing garden walls and moon gate
b.layer = 'garden'
cf.build_bamboo_cluster(bridge, x=-2.8, y=2.6, z=0.0, count=5, height=2.8, seed=42)
cf.build_bamboo_cluster(bridge, x=-2.8, y=5.4, z=0.0, count=5, height=3.0, seed=108)

# 4. Upper floor lounge daybed with lacquer chest
b.layer = 'upper'
cf.build_ming_daybed(bridge, x=3.0, y=12.2, z=2.92, rotDeg=0, length=2.0, depth=1.0, height=0.74)
cf.build_lacquer_chest(bridge, x=1.75, y=12.2, z=2.92, rotDeg=90, scale=0.85)

# 5. Upper veranda Meirengkao balustrade
cf.build_veranda_balustrade(bridge, x0=5.4, x1=7.6, y=5.35, z=2.92)
cf.build_veranda_balustrade(bridge, x0=10.5, x1=12.6, y=5.35, z=2.92)

# 6. Waterfront stone lotus basins alongside the quay
b.layer = 'waterfront'
cf.build_lotus_pot(bridge, x=3.2, y=-1.1, z=0.05, scale=0.95)
cf.build_lotus_pot(bridge, x=6.8, y=-1.1, z=0.05, scale=0.95)

# 7. Roof ridge Chiwen terminal crests
b.layer = 'roof'
cf.build_roof_ridge_cap(bridge, x=0.10, y=2.0, z=6.58, rotDeg=90, scale=0.90)
cf.build_roof_ridge_cap(bridge, x=17.90, y=2.0, z=6.58, rotDeg=-90, scale=0.90)

# 8. Scholar painting desk, hand fan, wardrobe cabinet & footstool in upper chamber
b.layer = 'upper'
cf.build_scholar_desk(bridge, x=15.2, y=12.2, z=2.92, rotDeg=0, length=1.8, width=0.8, height=0.82)
cf.build_hand_fan(bridge, x=15.2, y=12.2, z=2.92 + 0.82, rotDeg=25, scale=0.9)
cf.build_huanghuali_cabinet(bridge, x=17.2, y=11.5, z=2.92, rotDeg=-90, width=1.1, depth=0.55, height=2.0)
cf.build_footstool(bridge, x=3.0, y=11.5, z=2.92, rotDeg=0, length=0.6, width=0.3, height=0.22)

# 9. Garden stone lantern and entrance reflective rain puddle
b.layer = 'garden'
cf.build_moon_lamp(bridge, x=-1.0, y=8.2, z=0.03, scale=1.0)
b.layer = 'site'
cf.build_rain_puddle(bridge, x=9.0, y=-1.1, z=0.03, rx=0.9, ry=0.55)

# 10. Architectural joinery: carved corbel brackets on colonnade posts
b.layer = 'ornament'
for cx in [4.7, 13.3]:
    for cy in [5.35, 8.65]:
        cf.build_carved_beam_end(bridge, x=cx, y=cy, z=5.22, rotDeg=0, scale=0.8)

# 11. Waterfront mooring bollard caps and wild reeds
b.layer = 'waterfront'
for bx in [-6.0, 1.5, 12.0, 22.0]:
    cf.build_dock_pile_cap(bridge, x=bx, y=-1.75, z=-0.46, scale=0.9)
for rx in [-5.5, 2.5, 17.5]:
    cf.build_reed_bundle(bridge, x=rx, y=-7.8, z=-0.75, count=12, height=1.8)

print('Geometry assembled',len(b.records),flush=True)
# Assign face-safe planar UVs. Continuous wood grain follows the longest component axis.
payload=[];stats={};texture_files={'wood':'huanghuali.png','woodlight':'huanghuali.png','fabric':'teal_brocade.png','plaster':'lime_plaster.png','stone':'blue_limestone.png','paving':'blue_limestone_wet.png','tile':'black_tile_wet.png','lotus':'lotus_panel.png','lacquer':'lacquer_black_gold.png','metal':'brass_aged.png','paper':'paper_screen.png'}
for rec in b.records:
 m=b.S.geometry[rec['name']];v=m.vertices[m.faces].reshape(-1,3);n=np.repeat(m.face_normals,3,axis=0);k=rec['material'];ext=np.ptp(v,axis=0);axis=int(np.argmax(ext))
 uv=np.empty((len(v),2));normaxis=np.argmax(abs(n),axis=1)
 for ax in range(3):
  ids=normaxis==ax;axes=[i for i in range(3) if i!=ax]
  if k in ['wood','woodlight'] and axis in axes:axes=[i for i in axes if i!=axis]+[axis]
  uv[ids]=v[ids][:,axes]/({'wood':1.0,'woodlight':1.,'fabric':.65,'plaster':1.5,'stone':1.,'paving':1.,'tile':.7,'paper':.8}.get(k,1.))
 if k=='lotus':
  horizontal=int(np.argmax(ext[:2]));uv[:,0]=(v[:,horizontal]-v[:,horizontal].min())/max(ext[horizontal],1e-6);uv[:,1]=(v[:,2]-v[:,2].min())/max(ext[2],1e-6)
 mm=trimesh.Trimesh(vertices=v,faces=np.arange(len(v)).reshape(-1,3),process=False)
 mm.visual=trimesh.visual.TextureVisuals(uv=uv,material=b.M[k]);b.S.geometry[rec['name']]=mm
 col=np.ones(3) if k in source else np.array(list(bytes.fromhex(b.COL[k])))/255
 arr=np.concatenate([v,n,np.broadcast_to(col,v.shape),uv],axis=1).astype('<f4')
 payload.append({'name':rec['name'],'layer':rec['layer'],'material':k,'texture':texture_files.get(k),'n':len(v),'buffer':base64.b64encode(arr.tobytes()).decode()})
 stats[k]=stats.get(k,0)+len(m.faces)

print('UV assignment complete',flush=True)
# Review mesh is portable; production approval remains explicitly pending.
print('Exporting GLB',flush=True)
from export_review_glb import write_glb
write_glb(P/'ming_review.glb',payload,P/'textures',b.COL)
(P/'review/viewer-data.json.gz').write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0))
report={'status':'review_candidate_not_final','source_building':'adc0ebe5c8134af780ea7a','objects':len(b.records),'triangles':sum(len(m.faces) for m in b.S.geometry.values()),'material_triangles':stats,'removed_draft_parts':len(removed),'textures':{},'limitations':['Texture sources are AI-generated, not measured PBR scans.','Panel relief in source image is not reconstructed geometry.','No Blender executable available; native Cycles render pending.','Roof and vegetation remain draft quality.','Original structural shell preserved; not a structural engineering certification.']}
for name in set(texture_files.values()):
 path=P/'textures'/name;im=Image.open(path);report['textures'][name]={'size':list(im.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seamless_verified':False,'source':'built-in image generation; unmodified original pixels'}
(P/'review/report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(P/'review/scene_objects.json').write_text(json.dumps(b.records,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))