"""Texture-aware offline WebGL viewer and reproducible EGL review images."""
from pathlib import Path
import json,gzip,base64,io,collections
import numpy as np
import moderngl
from PIL import Image
P=Path(__file__).resolve().parent
data=json.loads(gzip.decompress((P/'review/viewer-data.json.gz').read_bytes()))
original=data
groups=collections.defaultdict(list)
for d in data:groups[(d['layer'],d['material'],d['texture'])].append(base64.b64decode(d['buffer']))
data=[dict(layer=k[0],material=k[1],texture=k[2],n=sum(len(b) for b in a)//44,buffer=base64.b64encode(b''.join(a)).decode()) for k,a in groups.items()]
for mode in ['tea','detail']:
 selected=collections.defaultdict(list)
 for d in original:
  if d['layer']!='ground':continue
  arr=np.frombuffer(base64.b64decode(d['buffer']),dtype='<f4').reshape(-1,11);c=arr[:,:3].mean(axis=0)
  if not (.1<c[0]<5.5 and .1<c[1]<3.96):continue
  if any(t in d['name'] for t in ['wall_','structural_beam','floor_slab','jamb','lintel','window_']):continue
  if mode=='detail' and c[1]<3.6:continue
  selected[(d['material'],d['texture'])].append(arr.tobytes())
 for k,a in selected.items():data.append(dict(layer='ground',material=k[0],texture=k[1],reviewMode=mode,n=sum(len(v) for v in a)//44,buffer=base64.b64encode(b''.join(a)).decode()))
texnames={d['texture'] for d in data if d['texture']}
images={n:'data:image/png;base64,'+base64.b64encode((P/'textures'/n).read_bytes()).decode() for n in texnames}
vs='''#version 330
in vec3 pos;in vec3 nor;in vec3 col;in vec2 uv;uniform mat4 mvp;out vec3 n;out vec3 c;out vec3 p;out vec2 t;
void main(){gl_Position=mvp*vec4(pos,1.0);n=nor;c=col;p=pos;t=uv;}'''
fs='''#version 330
in vec3 n;in vec3 c;in vec3 p;in vec2 t;uniform vec3 eye;uniform float clay;uniform float textured;uniform sampler2D albedo;out vec4 color;
void main(){vec3 N=normalize(n);if(!gl_FrontFacing)N=-N;vec3 L=normalize(vec3(-.5,-.7,1.0));float diff=max(dot(N,L),0.0);vec3 C=c;if(textured>.5)C*=texture(albedo,t).rgb;C=mix(C,vec3(.73),clay);vec3 outc=C*(.5+.47*diff+.08*max(N.z,0.0));float spec=pow(max(dot(N,normalize(L+normalize(eye-p))),0.0),40.0);outc+=vec3(.035)*spec*(1.0-clay);float fog=clamp((distance(eye,p)-30.0)*.002,0.0,.12);color=vec4(mix(outc,vec3(.36,.42,.43),fog),1.0);}'''

html=(P/'viewer-template.html').read_text()
start=html.index('const vs=');end=html.index('function shader',start)
html=html[:start]+'const vs=`'+vs.replace('#version 330','#version 300 es')+'`;\nconst fs=`'+fs.replace('#version 330','#version 300 es\nprecision highp float;')+'`;\n'+html[end:]
html=html.replace("const PAYLOAD='__PAYLOAD__';","const PAYLOAD='"+base64.b64encode(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0)).decode()+"';\nconst TEXTURES="+json.dumps(images,separators=(',',':'))+";let texcache={};")
html=html.replace("gl.bindVertexArray(o.vao);gl.drawArrays", "gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texcache[o.texture]||texcache.white);gl.uniform1i(gl.getUniformLocation(program,'albedo'),0);gl.uniform1f(gl.getUniformLocation(program,'textured'),o.texture?1:0);gl.bindVertexArray(o.vao);gl.drawArrays")
html=html.replace("gl.enable(gl.DEPTH_TEST);const stream", """gl.enable(gl.DEPTH_TEST);
const white=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,white);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));texcache.white=white;
await Promise.all(Object.entries(TEXTURES).map(([name,url])=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{const tx=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tx);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);texcache[name]=tx;resolve();};im.onerror=()=>reject(Error('贴图加载失败：'+name));im.src=url;})));
const stream""")
html=html.replace("['pos','nor','col'].forEach((a,i)=>{", "['pos','nor','col','uv'].forEach((a,i)=>{")
html=html.replace("gl.vertexAttribPointer(loc,3,gl.FLOAT,false,36,i*12)","gl.vertexAttribPointer(loc,i===3?2:3,gl.FLOAT,false,44,i*12)")
html=html.replace('<option value="court">','<option value="tea">茶室近景</option><option value="detail">隔扇与木作</option><option value="court">')
html=html.replace('const presets={overview:', 'const presets={tea:[-1.57,.72,3.6,[2.75,2,1.1],false,false],detail:[-1.57,.12,2.25,[2.76,3.78,1.42],false,false],overview:')
html=html.replace('Math.max(4,','Math.max(.65,')
html=html.replace('for(const o of items){',"for(const o of items){const mode=document.getElementById('view').value;if(['tea','detail'].includes(mode)){if(o.reviewMode!==mode)continue;}else if(o.reviewMode)continue;")
html=html.replace('场景初版 · 几何预览','明式精细化 v0.2 · 材质与构件审阅，非最终光追渲染')
html=html.replace('两层庭院建筑 / 月洞门 / 石拱桥 / 乌篷船','黄花梨木作 / 步步锦窗棂 / 圈椅 / 缠枝莲裙板 / 孔雀青织锦')
(P/'ming_review.html').write_text(html)

ctx=moderngl.create_standalone_context(backend='egl');W,H=1600,1100
prog=ctx.program(vertex_shader=vs,fragment_shader=fs);prog['albedo'].value=0
textures={}
for name in texnames:
 im=Image.open(P/'textures'/name).convert('RGB').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 tx=ctx.texture(im.size,3,im.tobytes());tx.build_mipmaps();textures[name]=tx
white=ctx.texture((1,1),3,bytes([255,255,255]));textures[None]=white
vaos=[]
for d in data:
 buf=ctx.buffer(base64.b64decode(d['buffer']));vao=ctx.vertex_array(prog,[(buf,'3f 3f 3f 2f','pos','nor','col','uv')]);vaos.append((d,vao))
fbo=ctx.simple_framebuffer((W,H));fbo.use();ctx.enable(moderngl.DEPTH_TEST)
def norm(v):return v/np.linalg.norm(v)
def matrix(eye,target,r):
 e=np.array(eye);f=norm(np.array(target)-e);s=norm(np.cross(f,[0,0,1]));u=np.cross(s,f)
 view=np.eye(4);view[:3,:3]=[s,u,-f];view[:3,3]=-view[:3,:3]@e
 top=r*H/W;n=.1;far=180
 proj=np.array([[1/r,0,0,0],[0,1/top,0,0],[0,0,-2/(far-n),-(far+n)/(far-n)],[0,0,0,1]])
 return (proj@view).astype('f4').T.tobytes()
# For the tea review hide surrounding meshes that obstruct an orthographic sectional view.
raw=data
views=[('overview',(34,-33,28),(8,2,2),23,[],None),('courtyard',(26,-14,28),(9,6,1),15,['roof'],None),('tea_room',(6,-4,7),(2.75,2.5,1.4),4.4,['roof','upper'], 'tea'),('joinery',(3,-5,2.8),(2.76,3.78,1.4),2.25,['roof','upper'],'joinery')]
for name,eye,target,scale,hide,mode in views:
 fbo.clear(.36,.42,.43,1,depth=1);prog['mvp'].write(matrix(eye,target,scale));prog['eye'].value=eye;prog['clay'].value=0
 for d,vao in vaos:
  if d.get('reviewMode') or d['layer'] in hide:continue
  if mode:
   # Mesh-based clipping is handled by a separate per-object selection below.
   continue
  textures[d['texture']].use(0);prog['textured'].value=float(bool(d['texture']));vao.render()
 if mode:
  original=json.loads(gzip.decompress((P/'review/viewer-data.json.gz').read_bytes()))
  for d in original:
   if d['layer']!='ground':continue
   arr=np.frombuffer(base64.b64decode(d['buffer']),dtype='<f4').reshape(-1,11);c=arr[:,:3].mean(axis=0)
   if not (.1<c[0]<5.5 and .1<c[1]<3.96):continue
   if any(s in d['name'] for s in ['wall_','structural_beam','floor_slab','jamb','lintel','window_']):continue
   if mode=='joinery' and c[1]<3.6:continue
   buf=ctx.buffer(arr.tobytes());va=ctx.vertex_array(prog,[(buf,'3f 3f 3f 2f','pos','nor','col','uv')]);textures[d['texture']].use(0);prog['textured'].value=float(bool(d['texture']));va.render();va.release();buf.release()
 img=Image.frombytes('RGB',(W,H),fbo.read(components=3)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 img.save(P/'review'/f'{name}.png');print(name,flush=True)
print('Review viewer written',flush=True)
