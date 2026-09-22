from pathlib import Path
import bpy, json, math, sys
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
component_counts = {
    "dougong": sum("dougong_" in o.name.lower() for o in mesh_objects),
    "hanging_plaque": sum("hanging_plaque" in o.name.lower() for o in mesh_objects),
    "rain_chain": sum("rain_chain" in o.name.lower() for o in mesh_objects),
}
required = {"dougong": 20, "hanging_plaque": 5, "rain_chain": 10}
missing = {k: (component_counts[k], v) for k, v in required.items() if component_counts[k] < v}
if missing:
    raise SystemExit(f"Authoritative components missing after GLB import: {missing}")

# Lighting: blue-hour ambient + warm entrance/courtyard accents.
world = bpy.data.worlds.new("CI_BlueHour")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.17, 0.22, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.45
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

for idx, (x, y, z) in enumerate(((9, -1.2, 2.2), (6, 6.0, 3.0), (12, 8.0, 3.0))):
    ld = bpy.data.lights.new(f"CI_Warm_{idx}", "AREA")
    ld.energy = 180
    ld.color = (1.0, 0.48, 0.22)
    ld.shape = "DISK"
    ld.size = 2.0
    lo = bpy.data.objects.new(f"CI_Warm_{idx}", ld)
    scene.collection.objects.link(lo)
    lo.location = (x, y, z)

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

scene.render.resolution_x = 720
scene.render.resolution_y = 480
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
    ("01_overview", (31, -29, 22), (9, 5.0, 2.6), 52, []),
    ("02_south_arrival", (9, -15, 4.2), (9, 0.5, 2.2), 52, []),
    ("03_courtyard", (9, -3.5, 7.5), (9, 7.0, 2.2), 48, ["roof"]),
    ("04_moon_gate", (-10, 1.0, 4.8), (-1.2, 5.0, 1.7), 55, []),
    ("05_bridge_waterfront", (28, -16, 8.0), (15, -4.8, 1.1), 55, []),
    ("06_tree_clearance", (17, 1.5, 5.5), (8.4, 7.0, 2.6), 58, ["roof"]),
    ("07_upper_veranda", (20, 1.0, 7.8), (10.5, 6.8, 4.7), 58, ["roof"]),
    ("08_eave_column_plinth", (16.5, 3.0, 6.2), (13.3, 5.4, 4.7), 62, []),
    ("09_roof_wall_plate", (23, -2.0, 8.4), (13.0, 1.5, 5.3), 60, []),
    ("10_canal_arrival", (3.5, -13, 3.5), (6.5, -2.2, 1.0), 52, []),
]

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
    "engine": engine_set,
    "resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "views": [v[0] for v in views],
    "view_count": len(views),
    "mesh_objects_after_import": len([o for o in scene.objects if o.type == "MESH"]),
    "component_counts": component_counts,
    "input_glb": str(INPUT),
    "blend": str(blend_path),
}
(OUT / "render_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
