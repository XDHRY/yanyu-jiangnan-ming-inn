"""Reusable Ming-inspired joinery. Metres, Z-up, seeded-free geometry.
Profiles are artistic interpretations, not a surveyed historical reconstruction.
"""
import math
import numpy as np
import trimesh


def prism(profile, depth):
    """Extrude a simple CCW x/z polygon along Y using ear triangulation."""
    p = np.asarray(profile, float)
    signed = sum(p[i,0]*p[(i+1)%len(p),1]-p[(i+1)%len(p),0]*p[i,1] for i in range(len(p)))
    if signed < 0: p = p[::-1]
    n=len(p); ids=list(range(n)); triangles=[]
    cross=lambda a,b: a[0]*b[1]-a[1]*b[0]
    while len(ids)>3:
        found=False
        for j,i in enumerate(ids):
            a,c=ids[j-1],ids[(j+1)%len(ids)]
            if cross(p[i]-p[a],p[c]-p[i]) <= 1e-10: continue
            def inside(k):
                return min(cross(p[i]-p[a],p[k]-p[a]),cross(p[c]-p[i],p[k]-p[i]),cross(p[a]-p[c],p[k]-p[c])) >= -1e-10
            if any(inside(k) for k in ids if k not in (a,i,c)): continue
            triangles.append((a,i,c));ids.pop(j);found=True;break
        if not found: raise ValueError('Invalid joinery profile')
    triangles.append(tuple(ids))
    v=[[x,y,z] for y in [-depth/2,depth/2] for x,z in p]
    f=list(triangles)+[(n+c,n+b,n+a) for a,b,c in triangles]
    for i in range(n):
        j=(i+1)%n;f.extend([(i,n+i,n+j),(i,n+j,j)])
    mesh=trimesh.Trimesh(vertices=v,faces=f,process=True)
    mesh.fix_normals()
    return mesh


def box_mesh(c,d):
    m=trimesh.creation.box(extents=d);m.apply_translation(c);return m


def place(add,name,mesh,origin,angle=0,mat='wood'):
    mesh.apply_transform(trimesh.transformations.rotation_matrix(angle,[0,0,1]))
    mesh.apply_translation(origin);add(name,mesh,mat)


def build_column_foot(add,x,y,z):
    # Layered octagonal plinth, torus-like drum profile and a recessed neck.
    place(add,'column_plinth_step',box_mesh((0,0,.032),(.31,.31,.068)),(x,y,z),mat='stone')
    profile=[(0,.057),(.141,.057),(.145,.074),(.135,.09),(.121,.101),(.115,.141),(.103,.157),(0,.157)]
    # Lathe coordinates radius,height; duplicate final axis points are handled by trimesh.
    m=trimesh.creation.revolve(np.asarray(profile),sections=24)
    place(add,'column_plinth_drum',m,(x,y,z),mat='stone')
    place(add,'column_plinth_neck',box_mesh((0,0,.166),(.174,.174,.022)),(x,y,z),mat='stone')


def build_knee_pair(add,x,y,beam_z,left=True,right=True,angle=0):
    # Top is let into the underside of the beam. Inner heel meets the column.
    profile=[(.055,-.035),(.64,-.035),(.62,-.10),(.52,-.14),(.43,-.155),(.34,-.205),(.255,-.30),(.18,-.415),(.055,-.48)]
    for sign,enabled in [(-1,left),(1,right)]:
        if enabled:
            m=prism([(sign*a,b) for a,b in profile],.105)
            place(add,'queti_curved_knee',m,(x,y,beam_z),angle)
            # Small rounded bead on the exposed concave edge, carried by the same body.
            for yy in [-.054,.054]:
                for a,b in zip(profile[2:-1],profile[3:]):
                    v0=np.array([sign*a[0],yy,a[1]+.018]);v1=np.array([sign*b[0],yy,b[1]+.018]);delta=v1-v0
                    m=trimesh.creation.cylinder(radius=.008,height=np.linalg.norm(delta),sections=6)
                    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],delta/np.linalg.norm(delta)));m.apply_translation((v0+v1)/2)
                    place(add,'queti_edge_bead',m,(x,y,beam_z),angle,'woodlight')


def build_bracket(add,x,y,z,axis='x'):
    angle=0 if axis=='x' else math.pi/2
    profile=[(-.38,.075),(.38,.075),(.36,.015),(.25,-.005),(.16,-.065),(-.16,-.065),(-.25,-.005),(-.36,.015)]
    place(add,'dougong_profile_arm',prism(profile,.19),(x,y,z+.045),angle)
    place(add,'dougong_seat',box_mesh((0,0,-.01),(.22,.22,.14)),(x,y,z),angle)
    for a in [-.28,.28]:
        place(add,'dougong_bearing_block',box_mesh((a,0,.15),(.18,.245,.085)),(x,y,z),angle,'woodlight')
    place(add,'dougong_cross_arm',prism([(a*.69,b*.7) for a,b in profile],.17),(x,y,z+.21),angle+math.pi/2)
    # Cap bridges to the reviewed roof plate; no unsupported decorative tips.
    place(add,'dougong_cap',box_mesh((0,0,.285),(.84,.19,.075)),(x,y,z),angle)


def build_eave_detail(add,lo,hi,edge,along,side):
    def point(a,inward,z):
        return (a,edge-side*inward,z) if along=='x' else (edge-side*inward,a,z)
    fascia=[];rafters=[];tile_ends=[]
    dims=(hi-lo,.07,.13) if along=='x' else (.07,hi-lo,.13)
    fascia.append(box_mesh(point((lo+hi)/2,0,5.39),dims))
    for a in np.arange(lo+.14,hi-.10,.44):
        dims=(.072,.46,.068) if along=='x' else (.46,.072,.068)
        rafters.append(box_mesh(point(a,.15,5.40),dims))
    outward=np.array([0,side,0] if along=='x' else [side,0,0])
    for a in np.arange(lo+.08,hi,.22):
        disk=trimesh.creation.cylinder(radius=.040,height=.018,sections=12)
        disk.apply_transform(trimesh.geometry.align_vectors([0,0,1],outward))
        disk.apply_translation(np.array(point(a,-.018,5.515)))
        tile_ends.append(disk)
    for name,parts,mat in [('eave_fascia_molding',fascia,'wood'),('eave_exposed_rafter_tails',rafters,'woodlight'),('eave_round_tile_ends',tile_ends,'tile')]:
        add(name,trimesh.util.concatenate(parts),mat)
