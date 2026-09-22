"""glTF 2.0 writer: named meshes, interleaved vertices, shared embedded PNGs."""
import json,struct,base64,math
import numpy as np
def write_glb(path,payload,texture_dir,colors):
 j={'asset':{'version':'2.0','generator':'Jiangnan Ming review v0.2'},'scene':0,'scenes':[{'nodes':[0]}],
 'nodes':[{'name':'Z_up_to_Y_up','rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':[]}],
 'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],
 'accessors':[],'bufferViews':[],'buffers':[]}
 binary=bytearray();material_ids={};texture_ids={}
 def append(blob,**kw):
  binary.extend(b'\0'*((-len(binary))%4));idx=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(blob),**kw});binary.extend(blob);return idx
 for d in payload:
  k=d['material'];tx=d['texture']
  if k not in material_ids:
   # Keep the GLB export contract aligned with refine_ming.py. These values
   # deliberately use broad wet-surface highlights instead of mirror-like bands.
   tint={'tile':[220/255,228/255,235/255,1],
         'paving':[208/255,222/255,230/255,1]}
   factor=tint.get(k,[1,1,1,1]) if tx else [v/255 for v in bytes.fromhex(colors[k])]+[1]
   rough={'wood':.43,'woodlight':.45,'fabric':.80,'lotus':.42,'lacquer':.31,
          'metal':.38,'paper':.76,'tile':.34,'paving':.44,'brass':.38,
          'celadon':.24,'stone':.58}.get(k,.65)
   metallic=.74 if k=='brass' else .72 if k=='metal' else 0.
   pbr={'baseColorFactor':factor,'metallicFactor':metallic,'roughnessFactor':rough}
   if tx:
    if tx not in texture_ids:
     v=append((texture_dir/tx).read_bytes());im=len(j['images']);j['images'].append({'name':tx,'bufferView':v,'mimeType':'image/png'})
     texture_ids[tx]=len(j['textures']);j['textures'].append({'sampler':0,'source':im})
    pbr['baseColorTexture']={'index':texture_ids[tx]}
   material_ids[k]=len(j['materials']);mat={'name':k,'pbrMetallicRoughness':pbr,'doubleSided':True}
   if k=='glow':mat['emissiveFactor']=[.5,.23,.06]
   j['materials'].append(mat)
  a=np.frombuffer(base64.b64decode(d['buffer']),dtype='<f4').reshape(-1,11).copy();a[:,10]=1-a[:,10]
  view=append(a.tobytes(),byteStride=44,target=34962);attrs={}
  for name,offset,typ in [('POSITION',0,'VEC3'),('NORMAL',12,'VEC3'),('TEXCOORD_0',36,'VEC2')]:
   acc={'bufferView':view,'byteOffset':offset,'componentType':5126,'count':len(a),'type':typ}
   if name=='POSITION':acc.update(min=a[:,:3].min(axis=0).tolist(),max=a[:,:3].max(axis=0).tolist())
   attrs[name]=len(j['accessors']);j['accessors'].append(acc)
  mi=len(j['meshes']);j['meshes'].append({'name':d['name'],'primitives':[{'attributes':attrs,'material':material_ids[k],'mode':4}]})
  ni=len(j['nodes']);j['nodes'].append({'name':d['name'],'mesh':mi,'extras':{'layer':d['layer']}});j['nodes'][0]['children'].append(ni)
 j['buffers']=[{'byteLength':len(binary)}];js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary.extend(b'\0'*((-len(binary))%4))
 path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)
