from pathlib import Path
import bpy, json, math, sys, hashlib
from mathutils import Vector

def arg(name, default=None):
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if name in args:
        i = args.index(name)
        return args[i + 1]
    return default

ROOT = Path(__file__).resolve().parents[1]
INPUT = Path(arg("--input", str(ROOT / ".ci_work" / "ming_review.glb"))).resolve()
OUT = Path(arg("--output", str(ROOT / "diagnostics"))).resolve()
OUT.mkdir(parents=True, exist_ok=True)
if not INPUT.exists():
    raise SystemExit(f"Missing GLB: {INPUT}")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(INPUT))
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

mesh_objects = [o for o in scene.objects if o.type == "MESH"]
# Remove faceting from rotational craft surfaces while preserving UV seams.
# glTF review buffers are face-expanded, so merge coincident vertices first.
import bmesh
smooth_tokens = ('lantern_shade', 'column_plinth_drum', 'pavilion_tapered_column',
                 'celadon_teapot', 'celadon_cup', 'pavilion_tea_cup', 'pavilion_stool_seat')
for obj in mesh_objects:
    if any(token in obj.name for token in smooth_tokens):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(obj.data)
        bm.free()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
# Water uses authored shallow waves plus small normal variation. No external
# texture or opaque blue overlay is needed for the canal surface.
for obj in mesh_objects:
    if "canal_ripple_surface" in obj.name:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
water = bpy.data.materials.get("water")
if water and water.use_nodes:
    nodes, links = water.node_tree.nodes, water.node_tree.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Roughness"].default_value = .24
        bsdf.inputs["Base Color"].default_value = (.025, .082, .076, 1)
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 4.5
        noise.inputs["Detail"].default_value = 2.0
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .24
        bump.inputs["Distance"].default_value = .018
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bark = bpy.data.materials.get("bark")
if bark and bark.use_nodes:
    nodes, links = bark.node_tree.nodes, bark.node_tree.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        bsdf.inputs["Roughness"].default_value = .92
        tex = nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 8
        tex.inputs["Detail"].default_value = 3
        mapping = nodes.new("ShaderNodeVectorMath")
        mapping.operation = "MULTIPLY"
        mapping.inputs[1].default_value = (2.5, 2.5, .32)
        geometry = nodes.new("ShaderNodeNewGeometry")
        links.new(geometry.outputs["Position"], mapping.inputs[0])
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (.028, .020, .014, 1)
        ramp.color_ramp.elements[1].color = (.14, .105, .065, 1)
        links.new(tex.outputs["Fac"], ramp.inputs[0])
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .30
        bump.inputs["Distance"].default_value = .012
        links.new(tex.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
component_counts = {
    "dougong": sum("dougong_" in o.name.lower() for o in mesh_objects),
    "hanging_plaque": sum("hanging_plaque" in o.name.lower() for o in mesh_objects),
    "rain_chain": sum("rain_chain" in o.name.lower() for o in mesh_objects),
    "paper_screen": sum("paper_screen" in o.name.lower() for o in mesh_objects),
    "incense_burner": sum("incense_burner" in o.name.lower() for o in mesh_objects),
    "altar_table": sum("altar_" in o.name.lower() for o in mesh_objects),
    "folding_screen": sum("screen_" in o.name.lower() and "paper_screen" not in o.name.lower() for o in mesh_objects),
    "scholar_rock": sum("rock_" in o.name.lower() for o in mesh_objects),
    "bamboo": sum("bamboo_" in o.name.lower() for o in mesh_objects),
    "meirengkao": sum("meirengkao_" in o.name.lower() for o in mesh_objects),
    "daybed": sum("daybed_" in o.name.lower() for o in mesh_objects),
    "brush_pot": sum("brush_" in o.name.lower() for o in mesh_objects),
    "scroll_basket": sum("scroll_" in o.name.lower() for o in mesh_objects),
    "lotus_pot": sum("lotus_basin" in o.name.lower() or "floating_lotus" in o.name.lower() for o in mesh_objects),
    "chiwen": sum("chiwen_" in o.name.lower() for o in mesh_objects),
    "scholar_desk": sum("desk_" in o.name.lower() for o in mesh_objects),
    "cabinet": sum("cabinet_" in o.name.lower() for o in mesh_objects),
    "footstool": sum("footstool_" in o.name.lower() for o in mesh_objects),
    "moon_lamp": sum("moon_lamp" in o.name.lower() or "lamp_" in o.name.lower() for o in mesh_objects),
    "hand_fan": sum("fan_" in o.name.lower() for o in mesh_objects),
    "corbel": sum("corbel_" in o.name.lower() for o in mesh_objects),
    "bollard": sum("bollard_" in o.name.lower() for o in mesh_objects),
    "reed": sum("reed_" in o.name.lower() for o in mesh_objects),
    "puddle": sum("puddle_" in o.name.lower() or "rain_water" in o.name.lower() for o in mesh_objects),
}
required = {
    "dougong": 20, "hanging_plaque": 5, "rain_chain": 10, "paper_screen": 10, "incense_burner": 2,
    "altar_table": 5, "folding_screen": 10, "scholar_rock": 2, "bamboo": 20, "meirengkao": 10,
    "daybed": 10, "brush_pot": 5, "scroll_basket": 10, "lotus_pot": 5, "chiwen": 4,
    "scholar_desk": 10, "cabinet": 15, "footstool": 5, "moon_lamp": 5, "hand_fan": 4,
    "corbel": 10, "bollard": 4, "reed": 20, "puddle": 2
}
missing = {k: (component_counts[k], v) for k, v in required.items() if component_counts[k] < v}
if missing:
    raise SystemExit(f"Authoritative components missing after GLB import: {missing}")

# Main south-arrival corridor must remain visually and physically open.
def world_bounds(obj):
    pts = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))

entry_steps = [o for o in mesh_objects if "entry_step" in o.name.lower() and "pavilion_" not in o.name.lower()]
if len(entry_steps) < 2:
    raise SystemExit("Coordinate-frame anchor missing: expected two entry steps")
entry_centers = []
for obj in entry_steps:
    x0,x1,y0,y1,z0,z1 = world_bounds(obj)
    entry_centers.append(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
if not all(abs(x-9.0) < .35 and y < -.25 and -.1 < z < .35 for x,y,z in entry_centers):
    raise SystemExit(f"Unexpected Blender coordinate frame at entry steps: {entry_centers}")

clearance_violations = []
for obj in mesh_objects:
    if "paper_screen" not in obj.name.lower():
        continue
    x0, x1, y0, y1, z0, z1 = world_bounds(obj)
    intersects_entry = x1 > 7.55 and x0 < 10.45 and y1 > -0.20 and y0 < 1.20 and z1 > 0.0 and z0 < 2.6
    if intersects_entry:
        clearance_violations.append({"object": obj.name, "bounds": [x0,x1,y0,y1,z0,z1]})
if clearance_violations:
    raise SystemExit(f"Paper screens intrude into primary arrival clearance: {clearance_violations}")

# Lighting: blue-hour ambient + warm entrance/courtyard accents.
world = bpy.data.worlds.new("CI_BlueHour")
world.use_nodes = True
bg_node = next((n for n in world.node_tree.nodes if n.type == "BACKGROUND"), None) or world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.12, 0.17, 0.22, 1)
    bg_node.inputs[1].default_value = 0.45
scene.world = world

sun_data = bpy.data.lights.new("CI_SoftSun", "SUN")
sun_data.energy = 1.5
sun_data.angle = 0.35
sun = bpy.data.objects.new("CI_SoftSun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.65, -0.25, -0.55)

area_data = bpy.data.lights.new("CI_SkyFill", "AREA")
area_data.energy = 1800
area_data.shape = "DISK"
area_data.size = 18
area = bpy.data.objects.new("CI_SkyFill", area_data)
scene.collection.objects.link(area)
area.location = (8, -4, 18)

# A neutral interior fill keeps the structural P0 views readable under the deep roof
# without flattening the blue-hour contrast used by the arrival views.
fill_data = bpy.data.lights.new("CI_StructureFill", "AREA")
fill_data.energy = 900
fill_data.shape = "DISK"
fill_data.size = 5.5
fill = bpy.data.objects.new("CI_StructureFill", fill_data)
scene.collection.objects.link(fill)
fill.location = (13.0, 6.2, 8.0)
fill.rotation_euler = (Vector((13.0, 5.6, 2.8)) - fill.location).to_track_quat("-Z", "Y").to_euler()

for idx, (x, y, z) in enumerate(((9, -1.2, 2.2), (6, 6.0, 3.0), (12, 8.0, 3.0))):
    ld = bpy.data.lights.new(f"CI_Warm_{idx}", "AREA")
    ld.energy = 180
    ld.color = (1.0, 0.48, 0.22)
    ld.shape = "DISK"
    ld.size = 2.0
    lo = bpy.data.objects.new(f"CI_Warm_{idx}", ld)
    scene.collection.objects.link(lo)
    lo.location = (x, y, z)

# The new pavilion sits in the inn's shadow. A broad neutral diagnostic fill
# reveals the structure, while a warm point source belongs to its visible pendant.
pd = bpy.data.lights.new("CI_PavilionSky", "AREA")
pd.energy = 450
pd.shape = "DISK"
pd.size = 4
po = bpy.data.objects.new("CI_PavilionSky", pd)
scene.collection.objects.link(po)
po.location = (24.8, 2.4, 5.4)
po.rotation_euler = (Vector((21.2, 6.0, 1.7)) - po.location).to_track_quat("-Z", "Y").to_euler()
ld = bpy.data.lights.new("Pavilion_Pendant", "POINT")
ld.energy = 65
ld.color = (1.0, .69, .40)
ld.shadow_soft_size = .35
lo = bpy.data.objects.new("Pavilion_Pendant", ld)
scene.collection.objects.link(lo)
lo.location = (21.2, 6.0, 2.28)

engine_set = None
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = engine
        engine_set = engine
        break
    except Exception:
        pass
if engine_set is None:
    raise SystemExit("No Eevee render engine available")

scene.render.resolution_x = int(arg("--width", "720"))
scene.render.resolution_y = round(scene.render.resolution_x * 2 / 3)
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "AgX"
if hasattr(scene, "eevee"):
    try:
        scene.eevee.taa_render_samples = 16
    except Exception:
        pass

def make_camera(name, loc, target, lens=48):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj

views = [
    ("01_overview", (34, -32, 23), (10.5, 5.0, 2.5), 48, []),
    ("02_south_arrival", (9, -15, 4.2), (9, 0.5, 2.2), 52, []),
    ("03_courtyard", (8.4, 5.3, 4.6), (9.2, 7.0, 1.0), 35, ["roof"]),
    ("04_east_pavilion", (28.6, -1.5, 5.3), (21.2, 6.1, 2.15), 36, []),
    ("05_bridge_waterfront", (28, -16, 8.0), (15, -4.8, 1.1), 55, []),
    ("06_tree_clearance", (13.0, 5.5, 5.0), (8.4, 7.0, 2.4), 40, ["roof"]),
    ("07_pavilion_joinery", (21.2, 3.10, 1.75), (21.2, 6.2, 1.95), 22, []),
    ("08_eave_column_plinth", (7.0, 7.5, 2.9), (13.3, 5.35, 2.6), 24, ["roof_substrate", "tile_roll", "veranda_roof", "veranda_tiles", "balcony_rail", "baluster", "tree"]),
    ("09_roof_wall_plate", (20.5, -2.8, 5.55), (15.8, 0.15, 5.18), 54, []),
    ("10_canal_arrival", (3.5, -13, 3.5), (6.5, -2.2, 1.0), 52, []),
]

selected = arg("--views")
if selected:
    requested = set(selected.split(","))
    known = {v[0] for v in views}
    if requested - known:
        raise SystemExit(f"Unknown diagnostic views: {sorted(requested - known)}")
    views = [v for v in views if v[0] in requested]

for name, loc, target, lens, hide_tokens in views:
    for obj in mesh_objects:
        low = obj.name.lower()
        obj.hide_render = any(tok in low for tok in hide_tokens)
    cam = make_camera("CAM_" + name, loc, target, lens)
    scene.camera = cam
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

for obj in mesh_objects:
    obj.hide_render = False

bpy.ops.file.pack_all()
blend_path = OUT / "jiangnan_diagnostic.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

manifest = {
    "blender_version": bpy.app.version_string,
    "blender_version_tuple": list(bpy.app.version),
    "engine": engine_set,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "views": [v[0] for v in views],
    "view_count": len(views),
    "mesh_objects_after_import": len([o for o in scene.objects if o.type == "MESH"]),
    "triangles_after_import": sum(len(o.data.polygons) for o in mesh_objects),
    "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    "view_cutaways": {v[0]: v[4] for v in views},
    "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted((ROOT / "source").glob("*.py"))},
    "component_counts": component_counts,
    "primary_arrival_clear": not clearance_violations,
    "coordinate_anchor_entry_steps": entry_centers,
    "input_glb": str(INPUT),
    "blend": str(blend_path),
}
(OUT / "render_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
