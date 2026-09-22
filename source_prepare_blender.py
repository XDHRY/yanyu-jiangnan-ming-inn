"""Run with Blender 4.x: blender --background --python prepare_blender.py
Imports delivered metre-scale GLB, builds material/lighting/cameras, saves editable .blend.
This script has not been executed in the delivery environment (Blender unavailable).
"""
from pathlib import Path
import bpy,math,json
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'scene.glb'))
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
# Imported glTF Y-up is converted by Blender to the original Z-up coordinates.
collections={}
for o in list(s.objects):
 if o.type!='MESH':continue
 group=o.name.split('/')[0]
 if group not in collections:
  collections[group]=bpy.data.collections.new(group);s.collection.children.link(collections[group])
 for c in list(o.users_collection):c.objects.unlink(o)
 collections[group].objects.link(o)
# Fully procedural roughness/bump: no external texture dependencies.
for mat in bpy.data.materials:
 mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
 if p is None:continue
 if mat.name.startswith('glow'):
  p.inputs['Emission Color'].default_value=(1,.42,.09,1);p.inputs['Emission Strength'].default_value=2.5;continue
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=35 if mat.name.startswith(('stone','plaster')) else 8
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.018;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
 if mat.name.startswith('water'):
  p.inputs['Roughness'].default_value=.12;p.inputs['Metallic'].default_value=.32;noise.inputs['Scale'].default_value=3;bump.inputs['Distance'].default_value=.08
 elif mat.name.startswith(('tile','paving')):p.inputs['Roughness'].default_value=.26
# Weathered plaster remains subtle; structural details stay visible.
world=bpy.data.worlds.new('Blue hour');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.19,.28,.37,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35;s.world=world
ld=bpy.data.lights.new('Cool sky','AREA');lo=bpy.data.objects.new('Cool sky',ld);s.collection.objects.link(lo);lo.location=(4,-10,22);ld.energy=2600;ld.shape='DISK';ld.size=22
sun=bpy.data.lights.new('Soft evening','SUN');so=bpy.data.objects.new('Soft evening',sun);s.collection.objects.link(so);so.rotation_euler=(.5,-.35,-.4);sun.energy=1.2;sun.angle=.25
for z in [2.15,4.85]:
 for x,y in [(1.2,-.3),(5.4,-.3),(12.6,-.3),(16.8,-.3),(4.7,4.85),(10.5,4.85),(7.6,9.15),(13.3,9.15)]:
  d=bpy.data.lights.new('Lantern warm','POINT');d.energy=32;d.color=(1,.42,.12);d.shadow_soft_size=.28;o=bpy.data.objects.new('Lantern warm',d);s.collection.objects.link(o);o.location=(x,y,z)
for x,y in [(3,2),(9,12),(16,7),(2,7)]:
 d=bpy.data.lights.new('Interior warm','AREA');d.energy=65;d.color=(1,.52,.24);d.size=2;o=bpy.data.objects.new('Interior warm',d);s.collection.objects.link(o);o.location=(x,y,2.3)
def camera(name,loc,target,ortho):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ortho;return o
cams=[camera('01_overview',(34,-33,28),(8,2,2),46),camera('02_courtyard',(26,-14,28),(9,6,1),30),camera('03_moon_gate',(-13,-12,10),(0,3,1),22),camera('04_bridge',(32,-20,12),(14,-4,0),28)]
s.camera=cams[0];s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True;s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
s.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'jiangnan_inn.blend'))
# Optional render only when explicitly requested on the command line.
import sys
if '--render' in sys.argv:
 for cam in cams:
  s.camera=cam
  if 'roof' in collections:collections['roof'].hide_render=cam.name.startswith('02')
  s.render.filepath=str(P/('blender_'+cam.name+'.png'));bpy.ops.render.render(write_still=True)
