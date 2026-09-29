"""Connected roof-roll sweep: preserve all eight curve spans, omit buried caps."""
import numpy as np
import trimesh

def sweep(points,radius=.038,sections=6):
    p=np.asarray(points,float);v=[];f=[]
    for j,c in enumerate(p):
        t=p[min(j+1,len(p)-1)]-p[max(j-1,0)];t/=np.linalg.norm(t)
        u=np.cross(t,[0,0,1]);u/=np.linalg.norm(u);w=np.cross(t,u)
        for a in np.arange(sections)*2*np.pi/sections:v.append(c+radius*(u*np.cos(a)+w*np.sin(a)))
    for j in range(len(p)-1):
        for k in range(sections):
            a=j*sections+k;b=j*sections+(k+1)%sections
            f.extend([(a,b,b+sections),(a,b+sections,a+sections)])
    for ring,flip in [(0,True),((len(p)-1)*sections,False)]:
        center=len(v);v.append(p[0 if flip else -1])
        for k in range(sections):
            a=ring+k;b=ring+(k+1)%sections
            f.append((center,b,a) if flip else (center,a,b))
    m=trimesh.Trimesh(vertices=v,faces=f,process=False);m.fix_normals();return m
