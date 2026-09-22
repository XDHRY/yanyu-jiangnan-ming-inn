from pathlib import Path
import sys,io
import json,base64,math
import numpy as np
import moderngl
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
ctx=moderngl.create_standalone_context(backend='egl');W,H=1600,1100
vs='''#version 330
in vec3 pos;in vec3 nor;in vec3 col;uniform mat4 mvp;out vec3 n;out vec3 c;out vec3 p;void main(){gl_Position=mvp*vec4(pos,1);n=nor;c=col;p=pos;}'''
fs='''#version 330
in vec3 n;in vec3 c;in vec3 p;uniform vec3 eye;uniform float clay;out vec4 color;
void main(){vec3 N=normalize(n);if(!gl_FrontFacing)N=-N;vec3 L=normalize(vec3(-.5,-.7,1.0));float diffuse=max(dot(N,L),0.);float noise=fract(sin(dot(floor(p*100.),vec3(12.9,78.2,37.3)))*43758.5);vec3 C=mix(c,vec3(.73),clay);float lit=.45+.52*diffuse+.08*max(N.z,0.);vec3 outc=C*lit*(.97+.06*noise);if(c.r>.9&&c.g>.55&&c.b<.6&&clay<.5)outc=c*1.12;float fog=clamp((distance(eye,p)-23.)*.008,0.,.27);outc=mix(outc,vec3(.57,.66,.68),fog);color=vec4(outc,1);}'''
prog=ctx.program(vertex_shader=vs,fragment_shader=fs)
vao=[]
for d in json.loads((P/'viewer-data.json').read_text()):
 b=ctx.buffer(base64.b64decode(d['buffer']));vao.append((d,ctx.vertex_array(prog,[(b,'3f 3f 3f','pos','nor','col')])))
fbo=ctx.simple_framebuffer((W,H));fbo.use();ctx.enable(moderngl.DEPTH_TEST)
def norm(v):return v/np.linalg.norm(v)
def matrix(eye,target,ortho=25):
 e=np.array(eye);t=np.array(target);f=norm(t-e);s=norm(np.cross(f,[0,0,1]));u=np.cross(s,f)
 v=np.eye(4);v[:3,:3]=np.array([s,u,-f]);v[:3,3]=-v[:3,:3]@e
 r=ortho;top=r*H/W;n=.1;far=160
 q=np.array([[1/r,0,0,0],[0,1/top,0,0],[0,0,-2/(far-n),-(far+n)/(far-n)],[0,0,0,1]])
 return (q@v).astype('f4').T.tobytes()
views=[('overview',(34,-33,28),(8,2,2),23,[],False),('courtyard',(26,-14,28),(9,6,1),15,['roof'],False),('moon_gate',(-13,-12,10),(0,3,1),11,[],False),('bridge_boat',(32,-20,12),(14,-4,0),14,[],False),('ground_plan',(9,5.999,50),(9,6,0),15,['roof','upper'],False)]
for name,eye,target,scale,hide,clay in views:
 if len(sys.argv)>1 and name!=sys.argv[1]:continue
 fbo.clear(.57,.65,.67,1,depth=1);prog['mvp'].write(matrix(eye,target,scale));prog['eye'].value=eye;prog['clay'].value=float(clay)
 for d,v in vao:
  if d['layer'] not in hide:v.render()
 img=Image.frombytes('RGB',(W,H),fbo.read(components=3)).transpose(Image.Transpose.FLIP_TOP_BOTTOM);img=img.convert('L').convert('RGB') if name=='ground_plan' else img;out=io.BytesIO();img.save(out,format='PNG');(P/(name+'.png')).write_bytes(out.getvalue());print(name,flush=True)
