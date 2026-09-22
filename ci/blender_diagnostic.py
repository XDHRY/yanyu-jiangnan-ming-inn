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

def image_material(name, relpath, roughness=0.45, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    img_path = ROOT / relpath
    if img_path.exists():
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(img_path))
        tex.interpolation = "Linear"
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

wood = image_material("CI_Huanghuali", "asset_library_hires/textures/tex_huanghuali_warm.jpg", 0.36)
lacquer = image_material("CI_BlackGold", "asset_library_hires/textures/tex_lacquer_black_gold.jpg", 0.30)
brass = image_material("CI_AgedBrass", "asset_library_hires/textures/tex_brass_aged.jpg", 0.32, 0.65)
paper = image_material("CI_Paper", "asset_library_hires/textures/tex_paper_screen.jpg", 0.72)

augmented = []

def add_box(name, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    augmented.append(name)
    return obj

def bracket_cluster(x, y, z, rot=0.0):
    parts = [
        ((0, 0, 0), (0.72, 0.28, 0.11)),
        ((0, 0, 0.12), (0.46, 0.46, 0.10)),
        ((0, 0, 0.23), (0.92, 0.18, 0.09)),
        ((-0.28, 0, 0.31), (0.20, 0.34, 0.08)),
        ((0.28, 0, 0.31), (0.20, 0.34, 0.08)),
    ]
    for i, (off, dims) in enumerate(parts):
        ox, oy, oz = off
        c, s = math.cos(rot), math.sin(rot)
        rx, ry = ox * c - oy * s, ox * s + oy * c
        o = add_box(f"CI_Dougong_{x:.2f}_{y:.2f}_{i}", (x + rx, y + ry, z + oz), dims, wood)
        o.rotation_euler[2] = rot

for x in (4.7, 7.6, 10.5, 13.3):
    bracket_cluster(x, 5.35, 5.12, 0)
    bracket_cluster(x, 8.65, 5.12, math.pi)

# South-arrival plaque: deliberately simple, readable silhouette first.
plaque = add_box("CI_HangingPlaque", (9.0, -0.38, 2.43), (2.25, 0.10, 0.62), lacquer)
for dx in (-1.03, 1.03):
    add_box(f"CI_PlaqueTrimV_{dx}", (9.0 + dx, -0.445, 2.43), (0.035, 0.025, 0.56), brass)
for dz in (-0.27, 0.27):
    add_box(f"CI_PlaqueTrimH_{dz}", (9.0, -0.445, 2.43 + dz), (2.08, 0.025, 0.035), brass)

# Two translucent paper panels flank the entrance without blocking circulation.
for x in (7.05, 10.95):
    add_box(f"CI_PaperScreen_{x}", (x, -0.10, 1.35), (1.10, 0.035, 2.10), paper)

# Low-cost rain-chain proxies at the two south eave corners.
for x in (0.55, 17.45):
    for i in range(10):
        z = 5.35 - i * 0.24
        bpy.ops.mesh.primitive_torus_add(major_radius=0.055, minor_radius=0.010, major_segments=12, minor_segments=6,
                                        location=(x, -0.28, z), rotation=(math.pi/2, 0, (i % 2) * math.pi/2))
        obj = bpy.context.object
        obj.name = f"CI_RainChain_{x}_{i}"
        obj.data.materials.append(brass)
        augmented.append(obj.name)

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

mesh_objects = [o for o in scene.objects if o.type == "MESH"]
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
    "mesh_objects_after_import_and_augmentation": len([o for o in scene.objects if o.type == "MESH"]),
    "augmented_objects": augmented,
    "augmented_count": len(augmented),
    "input_glb": str(INPUT),
    "blend": str(blend_path),
}
(OUT / "render_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
