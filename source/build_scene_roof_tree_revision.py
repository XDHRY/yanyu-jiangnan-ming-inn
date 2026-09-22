"""Deterministic, metre-scale editable Jiangnan inn mesh. Python + numpy + trimesh."""
from pathlib import Path
import json, math, random, base64
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
P=Path(__file__).resolve().parent
random.seed(27)
S=trimesh.Scene(); records=[]; layer='site'
COL={'plaster':'ded9c8','wood':'493324','woodlight':'796047','tile':'303d42','stone':'777e79','paving':'999e91','water':'34616b','leaf':'47664d','leaf2':'64734b','red':'a95531','glow':'f6bf69','fabric':'b5b1a0','soil':'4c4938','metal':'454943','lacquer':'171411','paper':'d7cfb8'}
M={k:PBRMaterial(name=k,baseColorFactor=[*bytes.fromhex(v),255],roughnessFactor=.23 if k in ['water','tile','paving'] else .76,metallicFactor=0,emissiveFactor=[.5,.23,.06] if k=='glow' else [0,0,0],doubleSided=True) for k,v in COL.items()}
def add(name,m,mat):
 m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();m.visual=trimesh.visual.TextureVisuals(material=M[mat]); n=f'{layer}/{name}_{len(records):05d}'; S.add_geometry(m,node_name=n,geom_name=n);records.append({'name':n,'layer':layer,'material':mat,'bounds':m.bounds.round(4).tolist(),'vertices':len(m.vertices),'triangles':len(m.faces)})
 return m

def box(name,c,d,mat='wood'):
 if min(d)<.00001:return
 m=trimesh.creation.box(extents=d);m.apply_translation(c);return add(name,m,mat)
def beam(name,a,b,r=.06,mat='wood',sections=8):
 a=np.array(a);b=np.array(b);d=b-a;length=np.linalg.norm(d)
 if length<.001:return
 m=trimesh.creation.cylinder(radius=r,height=length,sections=sections); m.apply_transform(trimesh.geometry.align_vectors([0,0,1],d/length));m.apply_translation((a+b)/2);return add(name,m,mat)
def sphere(name,c,scale,mat='leaf',sub=1):
 m=trimesh.creation.icosphere(subdivisions=sub);m.apply_scale(scale);m.apply_translation(c);return add(name,m,mat)
def mesh(name,v,f,mat):return add(name,trimesh.Trimesh(vertices=v,faces=f,process=False),mat)
def lathe(name,c,profile,mat='stone',N=20):
 v=[];f=[]
 for z,r in profile:
  for i in range(N):
   t=i*math.tau/N;v.append([c[0]+r*math.cos(t),c[1]+r*math.sin(t),c[2]+z])
 for j in range(len(profile)-1):
  for i in range(N):
   a=j*N+i;b=j*N+(i+1)%N;d=(j+1)*N+i;e=(j+1)*N+(i+1)%N;f.extend([[a,b,e],[a,e,d]])
 return mesh(name,v,f,mat)
def railing(a,b,z):
 a=np.array(a,float);b=np.array(b,float);d=b-a
 for h in [.18,.94]:beam('balcony_rail',list(a)+[z+h],list(b)+[z+h],.045)
 for t in np.linspace(0,1,max(2,int(np.linalg.norm(d)/.24)+1)):
  q=a+d*t;beam('baluster',list(q)+[z+.12],list(q)+[z+.94],.024)

def doorframe(a,b,z,h,mat='wood'):
 for p in [a,b]:beam('jamb',list(p)+[z],list(p)+[z+h],.06,mat)
 beam('lintel',list(a)+[z+h],list(b)+[z+h],.07,mat)

def wall(w,opens,z):
 a=np.array(w['from'],float);b=np.array(w['to'],float);L=np.linalg.norm(b-a);u=(b-a)/L;th=w['thickM'];H=2.52
 cuts=[]
 for o in opens:
  t=np.dot(np.array(o['at'])-a,u);cuts.append((max(0,t-o['widthM']/2),min(L,t+o['widthM']/2),o))
 cuts.sort();cursor=0
 def segment(s,e,lo,hi,mat='plaster'):
  if e-s<.001 or hi-lo<.001:return
  c=a+u*(s+e)/2;m=trimesh.creation.box(extents=[e-s,th,hi-lo]);T=trimesh.transformations.rotation_matrix(math.atan2(u[1],u[0]),[0,0,1]);m.apply_transform(T);m.apply_translation([*c,z+(lo+hi)/2]);add('wall',m,mat)
 for s,e,o in cuts:
  segment(cursor,s,0,H);lo=o['sillM'];hi=min(H,lo+o['heightM']);segment(s,e,0,lo);segment(s,e,hi,H)
  p=a+u*s;q=a+u*e;doorframe(p,q,z+lo,hi-lo)
  if o['kind']=='window':
   beam('window_sill',list(p)+[z+lo],list(q)+[z+lo],.07)
   for t in np.arange(s+.22,e,.28):
    r=a+u*t;beam('window_lattice',list(r)+[z+lo],list(r)+[z+hi],.018)
   for h in [lo+.35,hi-.3]:beam('window_lattice',list(p)+[z+h],list(q)+[z+h],.018)
   # Removable bamboo shade stays above the clear window area.
   for h in np.arange(hi-.22,hi,.06):beam('bamboo_blind',list(p)+[z+h],list(q)+[z+h],.024,'woodlight')
  cursor=e
 segment(cursor,L,0,H)

def roof(x0,x1,y0,y1,along='x'):
 # Compact gabled roofs. The eave is deliberately registered to the upper wall
 # plate so the second-floor junction reads as a continuous Ming timber frame.
 def pt(a,t,side):
  # Upper wall top is z=5.42m. 5.48m at the eave lets the fascia overlap it
  # by roughly 40mm while keeping the ridge restrained rather than oversized.
  height=6.58-1.18*t+.08*t**5
  if along=='x':return [a,(y0+y1)/2+side*(y1-y0)/2*t,height]
  return [(x0+x1)/2+side*(x1-x0)/2*t,a,height]
 lo,hi=(x0,x1) if along=='x' else (y0,y1)
 for side in [-1,1]:
  v=[];faces=[];N=12
  for a in [lo,hi]:
   for t in np.linspace(0,1,N+1):v.append(pt(a,t,side))
  for j in range(N):faces.extend([[j,j+1,N+2+j],[j,N+2+j,N+1+j]])
  mm=trimesh.Trimesh(v,faces,process=False);add('roof_substrate',mm,'tile')
  for a in np.arange(lo+.08,hi,.22):
   # one complete raised tile roll per row, eight curved segments
   for j in range(8):
    p=pt(a,j/8,side);q=pt(a,(j+1)/8,side);p[2]+=.035;q[2]+=.035;beam('tile_roll',p,q,.038,'tile',6)
  for t in np.linspace(.12,1,8):beam('tile_course',pt(lo,t,side),pt(hi,t,side),.012,'tile',5)
  beam('eave_beam',pt(lo,1,side),pt(hi,1,side),.105,'wood')
  beam('roof_wall_plate',pt(lo,1,side),pt(hi,1,side),.072,'woodlight')
 beam('roof_ridge',pt(lo,0,1),pt(hi,0,1),.11,'tile')
 # end gable closure, no empty triangular attic
 for a in [lo+.4,hi-.4]:
   A=pt(a,1,-1);B=pt(a,0,1);C=pt(a,1,1);A[2]=5.43;C[2]=5.43;mesh('gable',[A,B,C],[[0,1,2]],'plaster')

def table(x,y,z):
 box('table_top',(x,y,z+.75),(1.3,.8,.09),'woodlight')
 for dx in [-.5,.5]:
  for dy in [-.26,.26]:box('table_leg',(x+dx,y+dy,z+.36),(.07,.07,.72))
 for dy in [-.85,.85]:
  box('chair_seat',(x,y+dy,z+.44),(.5,.48,.07),'woodlight')
  for dx in [-.18,.18]:
   for sy in [-.16,.16]:box('chair_leg',(x+dx,y+dy+sy,z+.21),(.055,.055,.42))
  box('chair_back',(x,y+dy+(.2 if dy>0 else -.2),z+.71),(.5,.055,.5))
 lathe('teapot',(x,y,z+.8),[(0,0),(.02,.09),(.14,.12),(.19,.07),(.21,0)],'red',12)
 for dx in [-.3,.3]:lathe('teacup',(x+dx,y,z+.8),[(0,0),(.01,.05),(.08,.07),(.08,.05),(.02,.035)],'fabric',10)

def lantern(x,y,z):
 beam('lantern_hanger',(x,y,z+.35),(x,y,z+.7),.015,'metal')
 sphere('lantern_shade',(x,y,z),(.2,.2,.29),'glow',2)
 for h in [-.28,.28]:box('lantern_cap',(x,y,z+h),(.28,.28,.035),'wood')
 beam('lantern_tassel',(x,y,z-.3),(x,y,z-.49),.018,'red')

def tree(x,y,z,s=1):
 # Layered courtyard tree: tapered trunk, readable branch forks, and small
 # irregular foliage clusters. This replaces the previous eight oversized
 # spheres that read like decorative balloons.
 beam('tree_trunk_base',(x,y,z),(x+.03*s,y,z+.85*s),.15*s,'woodlight',10)
 beam('tree_trunk_mid',(x+.03*s,y,z+.82*s),(x-.02*s,y+.015*s,z+1.65*s),.11*s,'woodlight',10)
 beam('tree_trunk_top',(x-.02*s,y+.015*s,z+1.62*s),(x+.02*s,y-.015*s,z+2.12*s),.075*s,'woodlight',10)
 branch_specs=[(-2.55,.72,2.10),(-1.55,.86,2.32),(-.45,.68,2.48),(.62,.74,2.30),(1.72,.83,2.18),(2.65,.64,2.42)]
 for i,(ang,reach,top) in enumerate(branch_specs):
  start=(x-.01*s,y,z+(1.35+0.05*(i%2))*s)
  mid=(x+math.cos(ang)*reach*.48*s,y+math.sin(ang)*reach*.48*s,z+(1.72+0.08*(i%3))*s)
  end=(x+math.cos(ang)*reach*s,y+math.sin(ang)*reach*s,z+top*s)
  beam('tree_branch_primary',start,mid,.052*s,'woodlight',8)
  beam('tree_branch_secondary',mid,end,.034*s,'woodlight',8)
  # Two offset leaf clusters per branch create a hand-pruned, asymmetrical
  # canopy without losing the restrained radial rhythm.
  for j,off in enumerate([-.12,.16]):
   px=end[0]+math.cos(ang+off)*.22*s;py=end[1]+math.sin(ang+off)*.22*s;pz=end[2]+(.12 if j else -.04)*s
   mat='leaf2' if (i+j)%3==0 else 'leaf'
   sphere('tree_leaf_cluster',(px,py,pz),(.24*s,.18*s,.22*s),mat,1)
 # Small upright crown keeps the tree legible in the open skywell and avoids a
 # flat ring of equal-sized blobs.
 sphere('tree_leaf_crown',(x+.02*s,y-.01*s,z+2.56*s),(.30*s,.24*s,.25*s),'leaf2',1)

def dougong(x,y,z,axis='x'):
 # Compact, readable Ming-style bracket cluster: stacked bearing blocks first,
 # ornament second. Kept intentionally economical so silhouette does the work.
 major=(.72,.24,.10) if axis=='x' else (.24,.72,.10)
 cross=(.26,.48,.09) if axis=='x' else (.48,.26,.09)
 cap=(.96,.18,.08) if axis=='x' else (.18,.96,.08)
 box('dougong_base',(x,y,z),major,'wood')
 box('dougong_cross',(x,y,z+.105),cross,'woodlight')
 box('dougong_cap',(x,y,z+.205),cap,'wood')
 for side in [-1,1]:
  if axis=='x':box('dougong_arm',(x+side*.32,y,z+.29),(.22,.34,.08),'wood')
  else:box('dougong_arm',(x,y+side*.32,z+.29),(.34,.22,.08),'wood')

def paper_screen(x,y,z,w=.9,h=1.95):
 # Low-cost high-impact screen: real paper plane with a restrained timber frame.
 box('paper_screen_panel',(x,y,z+h/2),(w-.10,.018,h-.10),'paper')
 for dx in [-w/2+.035,w/2-.035]:box('paper_screen_stile',(x+dx,y-.015,z+h/2),(.07,.055,h),'wood')
 for zz in [z+.035,z+h-.035]:box('paper_screen_rail',(x,y-.015,zz),(w,.055,.07),'wood')
 # A quiet 2 x 3 timber grid keeps the paper panel legible at diagnostic scale.
 box('paper_screen_muntin',(x,y-.035,z+h/2),(.026,.026,h-.14),'woodlight')
 for zz in [z+h*.34,z+h*.66]:
  box('paper_screen_muntin',(x,y-.035,zz),(w-.14,.026,.026),'woodlight')

def hanging_plaque(x,y,z):
 box('hanging_plaque_body',(x,y,z),(2.2,.10,.58),'lacquer')
 for dx in [-1.02,1.02]:box('hanging_plaque_trim_v',(x+dx,y-.055,z),(.035,.018,.52),'metal')
 for dz in [-.25,.25]:box('hanging_plaque_trim_h',(x,y-.055,z+dz),(2.02,.018,.035),'metal')
 for dx in [-.68,.68]:beam('hanging_plaque_chain',(x+dx,y,z+.29),(x+dx,y,z+.62),.012,'metal',6)

def rain_chain(x,y,z_top,count=10,step=.24):
 for i in range(count):
  z1=z_top-i*step;z2=z1-step*.72
  beam('rain_chain_link',(x,y,z1),(x,y,z2),.012,'metal',6)

# Site and water. Main facade faces south (negative Y).
box('north_bank',(8,7,-.48),(32,18,.96),'soil');box('south_bank',(8,-10,-.48),(32,4,.96),'soil')
box('canal',(8,-5,-.81),(32,6,.06),'water')
for y in [-1.7,-8.3]:
 box('quay_substrate',(8,y,-.46),(32,.6,.9),'stone')
 for x in np.arange(-7.5,24,.85):
  for z in [-.65,-.3]:box('quay_block',(x,y,z),(.81,.63,.32),'stone')
for x in np.arange(-7.6,24,1.1):
 for y in [-1.1,-.45,-9.0,-9.7]:box('wet_paving',(x,y,.025),(1.065,.61,.05),'paving')
# Building floor foundations, floors, ring verandas; central sky well has no upper slab.
for level in [0,1]:
 layer='ground' if level==0 else 'upper';z=.2+level*2.7
 for c,d in [((9,2,z-.1),(18,4,.2)),((9,12,z-.1),(18,4,.2)),((2,7,z-.1),(4,6,.2)),((16,7,z-.1),(4,6,.2))]:
  if level and c[1]==2:
   # Upper stair opening: x12.8..17.2, y2.25..3.55.
   for cc,dd in [((6.4,2,z-.1),(12.8,4,.2)),((17.6,2,z-.1),(.8,4,.2)),((15,1.125,z-.1),(4.4,2.25,.2)),((15,3.775,z-.1),(4.4,.45,.2))]:box('upper_floor_stair_cut',cc,dd,'woodlight')
  else:box('floor_slab',c,d,'woodlight' if level else 'paving')
 for c,d in [((9,4.7,z-.07),(10,1.4,.14)),((9,9.3,z-.07),(10,1.4,.14)),((4.7,7,z-.07),(1.4,3.2,.14)),((13.3,7,z-.07),(1.4,3.2,.14))]:box('continuous_veranda',c,d,'woodlight')
 data=json.loads((P/('ground.json' if not level else 'upper.json')).read_text())
 for w in data['walls']:wall(w,[o for o in data['openings'] if o['wall']==w['id']],z)
 # Timber sill and upper beam courses; clear passage doors remain open.
 for yy in [0,4,10,14]:beam('structural_beam',(0,yy,z+2.48),(18,yy,z+2.48),.105)
 for xx in [0,4,14,18]:beam('structural_beam',(xx,4,z+2.48),(xx,10,z+2.48),.105)
 for xx in [4.7,7.6,10.5,13.3]:
  for yy in [5.35,8.65]:
   beam('colonnade_post',(xx,yy,z),(xx,yy,z+2.7),.08)
   box('post_stone_base',(xx,yy,z+.075),(.25,.25,.15),'stone')
 for yy in [5.35,8.65]:beam('veranda_beam',(4.7,yy,z+2.52),(13.3,yy,z+2.52),.095)
 if level:
  for a,b in [((5.4,5.4),(12.6,5.4)),((5.4,8.6),(12.6,8.6)),((5.4,5.4),(5.4,8.6)),((12.6,5.4),(12.6,8.6))]:railing(a,b,z)
  railing((12.8,2.25),(17.2,2.25),z)
 # Use the checked online fixture positions, including rotations and widths.
 for f in data['fixtures']:
  k=f['kind']
  if k in ['tree','plant']:continue
  before=len(records);w=f.get('widthM') or 1;d=f.get('depthM') or .6;h=f.get('heightM') or .8
  if k=='bed':
   box('bed_frame',(0,0,z+.22),(w,d,.44));box('mattress',(0,0,z+.49),(w-.06,d-.06,.12),'fabric');box('pillow',(0,d/2-.3,z+.6),(w*.7,.35,.12),'fabric');box('headboard',(0,d/2-.04,z+.65),(w,.08,1.1))
  elif k in ['wardrobe','dresser','counter']:
   hh=1.8 if k=='wardrobe' else h
   box(k,(0,0,z+hh/2),(w,d,hh),'woodlight')
   for xx in [-w*.22,w*.22]:beam('cabinet_handle',(xx,-d/2-.02,z+hh*.53),(xx,-d/2-.02,z+hh*.65),.014,'metal')
  elif k in ['table','chair','sofa','armchair']:
   hh=.75 if k=='table' else .44
   box(k+'_surface',(0,0,z+hh),(w,d,.09),'woodlight')
   for xx in [-w*.38,w*.38]:
    for yy in [-d*.35,d*.35]:box('furniture_leg',(xx,yy,z+hh/2),(.055,.055,hh))
   if k!='table':box(k+'_back',(0,d/2-.035,z+.69),(w,.07,.48))
   else:lathe('teapot',(0,0,z+.80),[(0,0),(.03,.07),(.12,.09),(.16,0)],'red',12)
  T=trimesh.transformations.rotation_matrix(math.radians(f['rotDeg']),[0,0,1]);T[:2,3]=f['at']
  for rec in records[before:]:
   mm=S.geometry[rec['name']];mm.apply_transform(T);rec['bounds']=mm.bounds.round(4).tolist()
 for xx in [4.7,7.6,10.5,13.3]:
  for yy in [4.85,9.15]:lantern(xx,yy,z+1.94)
 for xx in [1.2,5.4,12.6,16.8]:lantern(xx,-.3,z+1.95)
# Stair with head clearance and landing, 16 risers.
layer='ground'
for i in range(16):
 h=(i+1)*2.7/16;box('stair_tread',(12.9+(i+.5)*4.2/16,2.9,.2+h-.055),(4.2/16,1.15,.11),'woodlight')
beam('stair_stringer',(12.9,2.38,.25),(17.1,2.38,2.82),.075);beam('stair_stringer',(12.9,3.42,.25),(17.1,3.42,2.82),.075)
for y in [2.35,3.45]:
 beam('stair_handrail',(12.9,y,1.15),(17.1,y,3.8),.04)
 for i in range(0,17,2):beam('stair_spindle',(12.9+i*4.2/16,y,.2+i*2.7/16),(12.9+i*4.2/16,y,1.1+i*2.7/16),.023)
# Entry steps.
for i in range(2):box('entry_step',(9,-.75+i*.3,.05+i*.1),(2.8,.6,.1),'stone')
# Central planted sky well; tree entirely within the open 7.2 x 3.2 m aperture.
# Tighten the soil island and pull the jar/rocks into one readable courtyard
# rhythm: tree as primary, wet stone as connector, jar as secondary anchor.
layer='courtyard'
box('courtyard_paving',(9,7,.025),(7.2,3.2,.05),'paving')
# A low organic mound avoids a rectangular slab reading in the courtyard view.
lathe('tree_bed',(8.4,7,.02),[(0,0),(.02,.48),(.08,.62),(.14,.52),(.14,0)],'soil',24)
tree(8.4,7,.15,.9)
lathe('stone_water_jar',(10.65,7.45,.05),[(0,0),(.05,.38),(.3,.5),(.65,.47),(.75,.43),(.75,.34),(.18,.3)],'stone')
# Bring a small moss-capped stone pair into the sightline between tree and jar.
sphere('moss_stone',(9.52,7.05,.16),(.30,.22,.16),'stone',1)
sphere('moss_cap',(9.52,7.05,.30),(.22,.16,.05),'leaf2',1)
sphere('moss_stone',(9.92,7.20,.11),(.16,.12,.10),'stone',1)
for x,y in [(6.3,6.5),(11.1,8.05),(10.95,6.25)]:
 lathe('terracotta_pot',(x,y,.05),[(0,0),(.03,.2),(.38,.32),(.43,.34),(.43,.27),(.1,.15)],'red',16)
 for i in range(7):sphere('pot_leaves',(x+random.uniform(-.15,.15),y+random.uniform(-.15,.15),.55+random.random()*.3),(.18,.18,.27),'leaf',1)
# Roofs: four compact wings, central courtyard remains open. The 0.25m
# overhang is enough for rain protection without visually separating the roof
# from the second-floor wall line.
layer='roof';roof(-.25,18.25,-.25,4.25);roof(-.25,18.25,9.75,14.25);roof(-.25,4.25,4.75,9.25,'y');roof(13.75,18.25,4.75,9.25,'y')
# Covered upper ring veranda: eaves meet the colonnade; open sky well remains clear.
for x0,x1,y0,y1,axis in [(4,14,4,5.45,'south'),(4,14,8.55,10,'north'),(4,5.45,5.45,8.55,'west'),(12.55,14,5.45,8.55,'east')]:
 def hz(x,y):
  t=(y-4)/1.45 if axis=='south' else (10-y)/1.45 if axis=='north' else (x-4)/1.45 if axis=='west' else (14-x)/1.45
  return 5.58-.14*t
 vv=[[x0,y0,hz(x0,y0)],[x1,y0,hz(x1,y0)],[x1,y1,hz(x1,y1)],[x0,y1,hz(x0,y1)]]
 mesh('veranda_roof',vv,[[0,1,2],[0,2,3]],'tile')
 if axis in ['south','north']:
  for xx in np.arange(x0,x1,.22):beam('veranda_tiles',(xx,y0,hz(xx,y0)+.03),(xx,y1,hz(xx,y1)+.03),.034,'tile',6)
 else:
  for yy in np.arange(y0,y1,.22):beam('veranda_tiles',(x0,yy,hz(x0,yy)+.03),(x1,yy,hz(x1,yy)+.03),.034,'tile',6)
# High-leverage ornament pass: real scene geometry, not diagnostic overlays.
layer='ornament'
for xx in [1.2,5.4,12.6,16.8]:dougong(xx,-.02,5.18,'x')
# One explicit wall-plate tenon is kept in the 09 focal bay so the eave-to-frame
# relationship reads as joinery rather than as one continuous brown strip.
box('wall_plate_joint',(16.8,-.04,5.43),(.18,.28,.20),'woodlight')
box('wall_plate_tenon',(16.8,-.20,5.34),(.30,.10,.08),'wood')
for xx in [4.7,7.6,10.5,13.3]:
 dougong(xx,5.35,5.10,'x');dougong(xx,8.65,5.10,'x')
hanging_plaque(9,-.34,2.50)
# Bring the paired paper screens to the facade edge so the south arrival
# reads as a layered threshold; their x positions remain outside the 2.4 m
# clear passage tested by the Blender diagnostic.
paper_screen(7.0,-.08,.22,.72,1.78);paper_screen(11.0,-.08,.22,.72,1.78)
for xx in [.55,17.45]:rain_chain(xx,-.28,5.34)

# Moon gate in the west side garden: actual hole through a thick wall.
layer='garden'
x=-2;y0=3.3;cz=1.35;r=1.25;V=[];F=[];N=72
for xx in [x-.15,x+.15]:
 for ring in [0,1]:
  for i in range(N):
   t=math.tau*i/N;dy=math.cos(t);dz=math.sin(t)
   R=r if ring==0 else min(2/max(abs(dy),1e-9),(1.55 if dz>0 else 1.35)/max(abs(dz),1e-9))
   V.append([xx,y0+R*dy,cz+R*dz])
for i in range(N):
 j=(i+1)%N
 for a,b,c,d in [(i,j,N+j,N+i),(2*N+i,3*N+i,3*N+j,2*N+j),(i,2*N+i,2*N+j,j),(N+i,N+j,3*N+j,3*N+i)]:F.extend([[a,b,c],[a,c,d]])
mesh('moon_gate_wall',V,F,'plaster')
for i in range(N):
 t=math.tau*i/N;u=math.tau*(i+1)/N
 for xx in [x-.18,x+.18]:beam('moon_gate_stone_ring',(xx,y0+r*math.cos(t),cz+r*math.sin(t)),(xx,y0+r*math.cos(u),cz+r*math.sin(u)),.065,'stone',6)
box('garden_enclosure',(-2,9,.95),(.3,7.4,1.9),'plaster');box('garden_end',(-1,12.6,.95),(2,.3,1.9),'plaster')
for y in np.arange(.8,12,.55):box('side_garden_path',(-1,y,.03),(1.5,.51,.06),'paving')
for xx,yy,s in [(-4.2,6,1.1),(-3.8,10,.8),(21,10,1.2),(21,13,.85)]:tree(xx,yy,0,s)
# Dock and piles connected to quay; boat has a hollow hull and canopy.
layer='waterfront'
for yy in np.arange(-4.8,-1.35,.18):box('dock_plank',(4.5,yy,-.05),(2.4,.165,.12),'woodlight')
for xx in [3.45,5.55]:
 for yy in [-4.65,-3.1,-1.55]:beam('dock_pile',(xx,yy,-1.2),(xx,yy,.4),.11,'wood')
# Boat hull: two nested pointed elliptical rings joined at gunwale.
V=[];F=[];N=32;cx=9;cy=-5.5
for z,rx,ry in [(-.95,2,.38),(-.48,2.5,.78),(-.48,2.36,.65),(-.8,1.95,.32)]:
 for i in range(N):
  t=math.tau*i/N;V.append([cx+rx*math.cos(t),cy+ry*math.sin(t),z])
for j in range(3):
 for i in range(N):
  k=(i+1)%N;a=j*N+i;b=j*N+k;c=(j+1)*N+k;d=(j+1)*N+i;F.extend([[a,b,c],[a,c,d]])
mesh('hollow_boat_hull',V,F,'woodlight');box('boat_floor',(cx,cy,-.77),(3.5,.6,.06),'wood')
for xx in [7.7,10.3]:box('boat_seat',(xx,cy,-.51),(.3,1.0,.09),'woodlight')
for xx in np.arange(8.05,10.05,.25):
 for i in range(10):
  t=i*math.pi/10;u=(i+1)*math.pi/10;beam('wupeng_canopy_rib',(xx,cy+.61*math.cos(t),-.45+.65*math.sin(t)),(xx,cy+.61*math.cos(u),-.45+.65*math.sin(u)),.03,'woodlight',5)
V=[];F=[]
for xx in [8.02,10.07]:
 for t in np.linspace(0,math.pi,17):V.append([xx,cy+.63*math.cos(t),-.44+.67*math.sin(t)])
for i in range(16):F.extend([[i,i+1,18+i],[i,18+i,17+i]])
mesh('wupeng_canopy',V,F,'tile');beam('oar',(7.1,-5.8,-.35),(5.5,-6.8,-.68),.025,'woodlight')
beam('mooring_rope',(6.5,-5.5,-.4),(5.55,-4.65,.22),.017,'fabric',5)
# Stone arch bridge on east side, deck meets both banks, open arch beneath.
layer='bridge';x=20.5;ya=-8.3;yb=-1.7;N=30;V=[];F=[]
def bz(t):return .1+1.45*math.sin(math.pi*t)
for xx in [x-1.1,x+1.1]:
 for offset in [0,-.36]:
  for i in range(N+1):t=i/N;V.append([xx,ya+(yb-ya)*t,bz(t)+offset])
for i in range(N):
 n=N+1
 for a,b,c,d in [(i,i+1,2*n+i+1,2*n+i),(n+i,3*n+i,3*n+i+1,n+i+1),(i,n+i,n+i+1,i+1),(2*n+i,2*n+i+1,3*n+i+1,3*n+i)]:F.extend([[a,b,c],[a,c,d]])
mesh('stone_arch_bridge',V,F,'stone')
for i in range(N):
 t=(i+.5)/N;yy=ya+(yb-ya)*t;box('bridge_tread',(x,yy,bz(t)+.035),(2.2,(yb-ya)/N,.075),'paving')
for xx in [x-1.06,x+1.06]:
 for i in range(11):
  t=i/10;yy=ya+(yb-ya)*t;box('bridge_post',(xx,yy,bz(t)+.48),(.14,.14,.95),'stone');sphere('stone_post_cap',(xx,yy,bz(t)+.99),(.115,.115,.115),'stone',1)
  if i<10:
   u=(i+1)/10
   for h in [.28,.87]:beam('bridge_rail',(xx,yy,bz(t)+h),(xx,ya+(yb-ya)*u,bz(u)+h),.055,'stone')
# Save portable geometry and authoritative object index.
G=S.copy();G.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0]));(P/'scene.glb').write_bytes(G.export(file_type='glb'))
(P/'scene_objects.json').write_text(json.dumps({'units':'metres','up':'Z','seed':27,'objects':records},ensure_ascii=False,indent=2))
# Triangle buffers shared with the offline WebGL viewer; flat normals preserve construction detail.
data=[]
for rec in records:
 m=S.geometry[rec['name']];v=m.vertices[m.faces].astype('float32');n=np.repeat(m.face_normals[:,None,:],3,axis=1).astype('float32');c=np.array(list(bytes.fromhex(COL[rec['material']])),dtype='float32')/255
 a=np.concatenate([v,n,np.broadcast_to(c,v.shape)],axis=2).astype('<f4')
 data.append({'name':rec['name'],'layer':rec['layer'],'material':rec['material'],'n':a.shape[0]*3,'buffer':base64.b64encode(a.tobytes()).decode()})
(P/'viewer-data.json').write_text(json.dumps(data,separators=(',',':')))
summary={'objects':len(records),'triangles':sum(r['triangles'] for r in records),'layers':{l:sum(r['layer']==l for r in records) for l in sorted(set(r['layer'] for r in records))},'bounds':S.bounds.tolist(),'source':'procedural geometry; no reference image was provided','native_blender_render':False}
(P/'build-report.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
