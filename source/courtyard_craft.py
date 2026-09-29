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
