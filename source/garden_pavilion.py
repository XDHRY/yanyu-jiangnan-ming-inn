"""East tea pavilion: subordinate, open-sided, walkable diagnostic extension."""
import math
import numpy as np
import trimesh
from architecture_detail import build_column_foot, build_knee_pair, prism, place, box_mesh
from landscape_detail import _taper

PAVILION = {
    'id':'east-tea-pavilion', 'units':'metres',
    'platform_bounds':[[19.1,4.0,0.0],[23.3,8.0,.24]],
    'roof_bounds':[[18.85,3.75,3.25],[23.55,8.25,4.35]],
    'entry_reserve':[[20.25,3.0,.25],[22.15,5.1,2.35]],
    'circulation':'bridge landing to south steps; open south bay; seats face tea table',
    'symmetry':'bilateral about x=21.2; north bench is intentional functional asymmetry',
    'runtime_status':'diagnostic review, not navigable-runtime certified',
}


def build(b):
    b.layer='pavilion'
    def add(name,m,mat):return b.add('pavilion_'+name,m,mat)
    def box(name,c,d,mat='wood'):return b.box('pavilion_'+name,c,d,mat)
    def rod(name,a,c,r=.03,mat='wood',n=12):return b.beam('pavilion_'+name,a,c,r,mat,n)
    def lathe(name,c,profile,mat='wood',n=24):return b.lathe('pavilion_'+name,c,profile,mat,n)
    box('stone_platform',(21.2,6,.105),(4.2,4,.21),'stone')
    # Thin caps in a disciplined grid, each part supported by the platform.
    for x in np.linspace(19.4,23.0,7):
        for y in np.linspace(4+1/3,8-1/3,6):box('floor_paver',(x,y,.225),(.592,.658,.03),'paving')
    for cy,top,depth in [(3.37,.08,.38),(3.66,.16,.40),(3.93,.24,.36)]:
        box('entry_step',(21.2,cy,top/2),(2.05,depth,top),'stone')
    for y in np.arange(-.55,3.15,.53):box('approach_paver',(21.2,y,.025),(1.55,.50,.05),'paving')
    # Four continuous columns carry four perimeter beams.
    for x in [19.35,23.05]:
        for y in [4.3,7.7]:
            build_column_foot(add,x,y,.24)
            add('tapered_column',_taper((x,y,.398),(x,y,3.30),.095,.079,16),'wood')
            build_knee_pair(add,x,y,3.17,left=x>21.2,right=x<21.2)
            build_knee_pair(add,x,y,3.17,left=y>6,right=y<6,angle=math.pi/2)
    for y in [4.3,7.7]:box('bearing_beam',(21.2,y,3.17),(3.86,.18,.22))
    for x in [19.35,23.05]:box('bearing_beam',(x,6,3.17),(.18,3.56,.22))
    # Perimeter transoms stay above 2.60m clear; no walls pretend to be open bays.
    for y in [4.3,7.7]:
        box('transom_lower_rail',(21.2,y,2.90),(3.7,.075,.055))
        for x in np.linspace(19.55,22.85,12):box('transom_mullion',(x,y,3.03),(.022,.045,.24))
    # Raised hipped roof with a modest curved silhouette and actual thickness.
    # Each slope has a quadrilateral or triangular footprint. Shared boundaries meet.
    slopes=[((20.35,6),(22.05,6),(18.85,3.75),(23.55,3.75)),
            ((22.05,6),(20.35,6),(23.55,8.25),(18.85,8.25)),
            ((22.05,6),(22.05,6),(23.55,3.75),(23.55,8.25)),
            ((20.35,6),(20.35,6),(18.85,8.25),(18.85,3.75))]
    roof_parts=[];tiles=[];rafters=[];fascia=[]
    def pt(s,u,t):
        ra,rb,ea,eb=map(np.array,s)
        high=ra*(1-u)+rb*u;low=ea*(1-u)+eb*u
        xy=high*(1-t)+low*t
        return np.array([*xy,4.35-1.22*t+.12*t**4+.12*abs(2*u-1)**6*t**4])
    def cylinder(a,c,r,n=8):
        d=c-a;m=trimesh.creation.cylinder(radius=r,height=np.linalg.norm(d),sections=n)
        m.apply_transform(trimesh.geometry.align_vectors([0,0,1],d/np.linalg.norm(d)));m.apply_translation((a+c)/2);return m
    for s in slopes:
        N,M=16,8;v=[];f=[]
        for off in [0,-.055]:
            for j in range(M+1):
                for i in range(N+1):v.append(pt(s,i/N,j/M)+[0,0,off])
        size=(M+1)*(N+1)
        for j in range(M):
            for i in range(N):
                a=j*(N+1)+i;c=a+N+1
                f.extend([(a,a+1,c+1),(a,c+1,c),(size+a,size+c+1,size+a+1),(size+a,size+c,size+c+1)])
        boundary=list(range(N+1))+[j*(N+1)+N for j in range(1,M+1)]+[M*(N+1)+i for i in range(N-1,-1,-1)]+[j*(N+1) for j in range(M-1,0,-1)]
        for a,c in zip(boundary,boundary[1:]+boundary[:1]):f.extend([(a,size+a,size+c),(a,size+c,c)])
        m=trimesh.Trimesh(vertices=v,faces=f,process=True);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();m.fix_normals();roof_parts.append(m)
        for u in np.linspace(.02,.98,22):
            for j in range(8):tiles.append(cylinder(pt(s,u,j/8)+[0,0,.025],pt(s,u,(j+1)/8)+[0,0,.025],.026,6))
        for u in np.linspace(.04,.96,12):
            # Rafters extend from top ridge support to the perimeter bearing lines.
            for j in range(4):
                a=.02+.96*j/4; c=.02+.96*(j+1)/4
                rafters.append(cylinder(pt(s,u,a)+[0,0,-.09],pt(s,u,c)+[0,0,-.09],.032,8))
        for i in range(16):fascia.append(cylinder(pt(s,i/16,1)+[0,0,-.08],pt(s,(i+1)/16,1)+[0,0,-.08],.062,8))
    for n,parts,mat in [('roof_shell',roof_parts,'tile'),('tile_rolls',tiles,'tile'),('rafters',rafters,'woodlight'),('fascia',fascia,'wood')]:add(n,trimesh.util.concatenate(parts),mat)
    # Fit purlin tops to the underside of the actual generated roof triangles.
    roof_mesh=trimesh.util.concatenate(roof_parts)
    triangles=roof_mesh.vertices[roof_mesh.faces]
    aa=triangles[:,0,:2];d1=triangles[:,1,:2]-aa;d2=triangles[:,2,:2]-aa
    det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0];valid=abs(det)>1e-9
    def underside(x,y):
        q=np.array([x,y])-aa;u=np.zeros(len(det));v=u.copy()
        u[valid]=(q[valid,0]*d2[valid,1]-q[valid,1]*d2[valid,0])/det[valid]
        v[valid]=(d1[valid,0]*q[valid,1]-d1[valid,1]*q[valid,0])/det[valid]
        hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)
        zz=triangles[hit,0,2]+u[hit]*(triangles[hit,1,2]-triangles[hit,0,2])+v[hit]*(triangles[hit,2,2]-triangles[hit,0,2])
        return float(zz.min())
    for origin,length,angle in [((19.35,4.3,0),3.7,0),((19.35,7.7,0),3.7,0),((19.35,4.3,0),3.4,math.pi/2),((23.05,4.3,0),3.4,math.pi/2)]:
        samples=np.linspace(0,length,13)
        top=[(t,underside(origin[0]+t*math.cos(angle),origin[1]+t*math.sin(angle))+.002) for t in samples]
        profile=[(0,3.255),(length,3.255)]+list(reversed(top))
        place(add,'seated_purlin',prism(profile,.10),origin,angle)
    # Visible pendant suspension meets the ridge underside above the tea table.
    b.sphere('pavilion_tea_lantern_shade',(21.2,6,2.56),(.16,.16,.24),'glow',2)
    for z in [2.32,2.80]:box('tea_lantern_cap',(21.2,6,z),(.23,.23,.03))
    rod('tea_lantern_cable',(21.2,6,2.815),(21.2,6,4.30),.008,'metal',8)
    rod('ridge_cap',(20.3,6,4.365),(22.1,6,4.365),.072,'tile')
    for x in [20.35,22.05]:
        box('ridge_king_post',(x,6,3.79),(.11,.11,.98))
        box('tie_beam',(x,6,3.31),(.15,3.6,.14))
    # Continuous safe edges at north and sides. South bay remains the entrance.
    for x in [19.35,23.05]:
        for z in [.51,1.13]:rod('side_rail',(x,4.3,z),(x,7.7,z),.035)
        for y in np.linspace(4.3,7.7,12):rod('side_baluster',(x,y,.47),(x,y,1.13),.018)
    for z in [.51,1.13]:rod('north_rail',(19.35,7.7,z),(23.05,7.7,z),.035)
    for x in np.linspace(19.35,23.05,13):rod('north_baluster',(x,7.7,.47),(x,7.7,1.13),.018)
    # Long rear bench, plus paired stools: use leg/apron contacts, no floating props.
    box('bench_seat',(21.2,7.40,.705),(2.9,.43,.07),'woodlight')
    for x in [19.95,21.2,22.45]:
        for y in [7.25,7.55]:box('bench_leg',(x,y,.455),(.055,.055,.43))
    for y in [7.245,7.555]:box('bench_apron',(21.2,y,.625),(2.75,.035,.10))
    box('tea_table_top',(21.2,6.25,1.015),(1.25,.74,.07),'woodlight')
    box('tea_table_inset',(21.2,6.25,1.052),(1.10,.59,.008))
    for x in [20.69,21.71]:
        for y in [5.99,6.51]:
            add('tea_table_leg',_taper((x,y,.24),(21.2+(x-21.2)*.97,6.25+(y-6.25)*.97,.99),.025,.021,10),'wood')
    for y in [5.99,6.51]:box('tea_table_apron',(21.2,y,.92),(1.05,.035,.13))
    for x in [20.13,22.27]:
        lathe('stool_seat',(x,6.25,.665),[(0,0),(0,.23),(.045,.23),(.058,.21),(.058,0)],'woodlight')
        for a in np.arange(3)*math.tau/3:
            rod('stool_leg',(x+.18*math.cos(a),6.25+.18*math.sin(a),.24),(x+.145*math.cos(a),6.25+.145*math.sin(a),.67),.024)
    lathe('tea_tray',(21.2,6.25,1.056),[(0,0),(0,.25),(.022,.25),(.03,.23),(.03,0)],'wood')
    for x in [21.02,21.38]:lathe('tea_cup',(x,6.25,1.086),[(0,0),(.008,.03),(.065,.045),(.065,.035),(.013,.025)],'fabric')
