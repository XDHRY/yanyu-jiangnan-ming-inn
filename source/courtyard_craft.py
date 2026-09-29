"""Low-relief courtyard masonry and practical waterfront hardware, in metres."""
import math
import numpy as np
import trimesh
from roof_sweep import sweep

def build(b):
    b.layer='courtyard_craft'
    def box(n,c,d,mat='paving'):return b.box('craft_'+n,c,d,mat)
    # Flush stone bond: 5 mm mortar gaps, surface stays at the existing 50 mm datum.
    for row,y in enumerate(np.arange(5.70,8.34,.16)):
        for x in np.arange(5.65+(row%2)*.16,12.4,.32):
            lo=max(x-.1575,5.61);hi=min(x+.1575,12.39)
            if hi-lo>.03:box('courtyard_bond',((lo+hi)/2,y,.0425),(hi-lo,.155,.015))
    # Perimeter edge stones bound a narrow recessed drain rather than raised obstacles.
    for y in [5.455,8.545]:
        for x in np.arange(5.625,12.6,.45):box('border_stone',(x,y,.0425),(.442,.105,.015),'stone')
    for x in [5.455,12.545]:
        for y in np.arange(5.675,8.45,.35):box('border_stone',(x,y,.0425),(.105,.342,.015),'stone')
    for y in [5.55,8.45]:
        box('drain_recess',(9,y,.036),(7.05,.06,.002),'metal')
        for x in np.arange(5.51,12.5,.12):box('drain_grate',(x,y,.044),(.025,.06,.012),'stone')
    for x in [5.55,12.45]:
        box('drain_recess',(x,7,.036),(.06,2.8,.002),'metal')
        for y in np.arange(5.65,8.4,.12):box('drain_grate',(x,y,.044),(.06,.025,.012),'stone')
    # Water lies inside the existing thick-walled jar, below its rim.
    b.lathe('craft_jar_water',(10.65,7.45,.63),[(0,0),(0,.322),(.003,.322),(.003,0)],'water',40)
    for r in [.10,.20]:
        m=trimesh.creation.torus(major_radius=r,minor_radius=.0015,major_sections=32,minor_sections=4)
        m.apply_translation([10.65,7.45,.634]);b.add('craft_jar_ripple',m,'water')
    # Copings weather the existing west enclosure; modules meet the wall top.
    b.layer='garden_craft'
    for y in np.arange(5.48,12.51,.28):
        box('wall_coping',(-2,y,1.94),(.40,.274,.08),'tile')
    for x in np.arange(-1.85,-.05,.28):box('wall_coping',(x,12.6,1.94),(.274,.40,.08),'tile')
    # Dock piles gain collars, cleats and restrained rope coils. Walkway stays open.
    b.layer='waterfront_craft'
    for x in [3.45,5.55]:
        for y in [-4.65,-3.1,-1.55]:
            for z in [.18,.32]:
                b.lathe('craft_pile_collar',(x,y,z),[(0,.11),(0,.118),(.028,.118),(.028,.11)],'metal',16)
            box('cleat_foot',(x,y,.414),(.13,.09,.028),'metal')
            b.beam('craft_cleat_horn',(x-.14,y,.456),(x+.14,y,.456),.019,'metal',8)
            box('cleat_stem',(x,y,.439),(.044,.044,.035),'metal')
    for x,y in [(3.65,-4.45),(5.35,-1.92)]:
        pts=[]
        for t in np.linspace(0,6*math.pi,97):
            r=.045+.0065*t;pts.append([x+r*math.cos(t),y+r*math.sin(t),.021])
        b.add('craft_rope_coil',sweep(pts,.009,5),'woodlight')
    # Countersunk nail heads at plank/pile intersections sit flush on the deck.
    for y in np.arange(-4.8,-1.35,.18):
        for x in [3.48,5.52]:
            b.lathe('craft_dock_nail',(x,y,.010),[(0,0),(0,.012),(.002,.012),(.002,0)],'metal',8)
    # West-side resting shelter: subordinate to the inn, open eastward to moon gate.
    b.layer='west_shelter'
    def wb(n,c,d,mat='wood'):return b.box('west_shelter_'+n,c,d,mat)
    def wr(n,a,c,r=.035,mat='wood'):return b.beam('west_shelter_'+n,a,c,r,mat,10)
    wb('platform',(-5.1,1.9,.10),(3.4,3.6,.20),'stone')
    for x in np.arange(-6.5,-3.6,.4):
        for y in np.arange(.4,3.5,.4):wb('floor_tile',(x,y,.21),(.393,.393,.02),'paving')
    for x in [-6.55,-3.65]:
        for y in [.3,3.5]:
            wb('column_base',(x,y,.27),(.26,.26,.10),'stone')
            wr('column',(x,y,.31),(x,y,2.79),.075)
    for y in [.3,3.5]:wb('bearing_beam',(-5.1,y,2.75),(3.05,.14,.14))
    for x in [-6.55,-3.65]:
        wb('cross_beam',(x,1.9,2.78),(.14,3.34,.14))
        wb('king_post',(x,1.9,3.11),(.10,.10,.72))
        for y,sgn in [(.3,1),(3.5,-1)]:
            wr('knee_brace',(x,y,2.28),(x,y+sgn*.48,2.76),.040)
    wb('ridge_support',(-5.1,1.9,3.47),(3.08,.12,.14))
    def roofpoint(x,t,side):return np.array([x,1.9+side*2*t,3.55-.88*t+.05*t**4])
    for side in [-1,1]:
        # Closed thick roof shell; bent rafters and tile rolls share its curve.
        vs=[];fs=[]
        for off in [0,-.045]:
            for x in [-6.95,-3.25]:
                for t in np.linspace(0,1,9):vs.append(roofpoint(x,t,side)+[0,0,off])
        for i in range(8):
            fs.extend([(i,i+1,10+i),(i,10+i,9+i),(18+i,28+i,19+i),(18+i,27+i,28+i)])
        rim=list(range(9))+list(range(17,8,-1))
        for a,c in zip(rim,rim[1:]+rim[:1]):fs.extend([(a,c,c+18),(a,c+18,a+18)])
        m=trimesh.Trimesh(vertices=vs,faces=fs,process=True);m.fix_normals();b.add('west_shelter_roof',m,'tile')
        for x in np.arange(-6.88,-3.27,.16):
            b.add('west_shelter_tile',sweep([roofpoint(x,t,side)+[0,0,.024] for t in np.linspace(0,1,9)],.027,6),'tile')
        for x in np.linspace(-6.7,-3.5,10):
            b.add('west_shelter_rafter',sweep([roofpoint(x,t,side)+[0,0,-.067] for t in np.linspace(0,1,9)],.025,6),'woodlight')
        wr('fascia',roofpoint(-6.95,1,side)+[0,0,-.055],roofpoint(-3.25,1,side)+[0,0,-.055],.055)
    wr('ridge',(-7,1.9,3.57),(-3.2,1.9,3.57),.065,'tile')
    # A single north bench leaves the rest of the platform for circulation.
    wb('bench_seat',(-5.1,3.18,.66),(2.45,.45,.065),'woodlight')
    for x in [-6.14,-5.1,-4.06]:
        for y in [3.04,3.32]:wb('bench_leg',(x,y,.43),(.065,.065,.42))
    for y in [3.02,3.34]:wb('bench_apron',(-5.1,y,.58),(2.32,.04,.12))
    for z in [.50,1.10]:
        wr('rear_rail',(-6.55,3.5,z),(-3.65,3.5,z),.03)
        wr('west_rail',(-6.55,.3,z),(-6.55,3.5,z),.03)
    for x in np.linspace(-6.5,-3.7,11):wr('rear_baluster',(x,3.5,.48),(x,3.5,1.1),.017)
    for y in np.linspace(.35,3.45,12):wr('west_baluster',(-6.55,y,.48),(-6.55,y,1.1),.017)
    wb('entry_step',(-3.26,2.7,.055),(.30,1.40,.11),'stone')
    for x,y in [(-2.96,2.8),(-2.58,3.05),(-2.2,3.3)]:wb('gate_path',(x,y,.025),(.38,.55,.05),'paving')
