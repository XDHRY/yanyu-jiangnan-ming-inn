from pathlib import Path
import json, shutil, io
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".ci_work"
if WORK.exists():
    shutil.rmtree(WORK)
(WORK / "textures").mkdir(parents=True)
(WORK / "review").mkdir(parents=True)

copies = {
    "source/roof_sweep.py": "roof_sweep.py",
    "source/courtyard_craft.py": "courtyard_craft.py",
    "source/build_scene_roof_tree_revision.py": "build_scene.py",
    "source/refine_ming.py": "refine_ming.py",
    "source/component_factory.py": "component_factory.py",
    "source/garden_pavilion.py": "garden_pavilion.py",
    "asset_library_hires/materials_20260929/leaf_albedo.png": "textures/leaf_albedo.png",
    "source/material_uv.py": "material_uv.py",
    "asset_library_hires/materials_20260929/provenance.json": "material-provenance.json",
    "source/architecture_detail.py": "architecture_detail.py",
    "source/landscape_detail.py": "landscape_detail.py",
    "source_export_review_glb.py": "export_review_glb.py",
    "source_validate_ming.py": "validate_ming.py",
    "data_ground.json": "ground.json",
    "data_upper.json": "upper.json",
    "texture_teal_brocade.png": "textures/teal_brocade.png",
    "texture_lime_plaster.png": "textures/lime_plaster.png",
    "texture_lotus_panel.png": "textures/lotus_panel.png",
}
derived = {
    "asset_library_hires/textures/tex_lacquer_black_gold.jpg": "textures/lacquer_black_gold.png",
    "asset_library_hires/textures/tex_brass_aged.jpg": "textures/brass_aged.png",
    "asset_library_hires/textures/tex_paper_screen.jpg": "textures/paper_screen.png",
    "asset_library_hires/materials_20260929/clay_albedo.jpg": "textures/black_tile_wet.png",
    "asset_library_hires/materials_20260929/huanghuali_albedo.jpg": "textures/huanghuali.png",
    "asset_library_hires/materials_20260929/limestone_albedo.jpg": "textures/blue_limestone.png",
}

missing = [src for src in list(copies) + list(derived) if not (ROOT / src).exists()]
if missing:
    raise SystemExit("Missing CI inputs: " + ", ".join(missing))

for src, dst in copies.items():
    target = WORK / dst
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / src, target)

for src, dst in derived.items():
    target = WORK / dst
    target.parent.mkdir(parents=True, exist_ok=True)
    # Encode fully before replacing an existing output; reject incomplete PNGs.
    buffer = io.BytesIO()
    Image.open(ROOT / src).convert("RGB").save(buffer, format="PNG", optimize=True)
    encoded = buffer.getvalue()
    Image.open(io.BytesIO(encoded)).load()
    temporary = target.with_suffix(".png.tmp")
    temporary.write_bytes(encoded)
    temporary.replace(target)
    Image.open(target).load()

shutil.copy2(WORK / "textures/blue_limestone.png", WORK / "textures/blue_limestone_wet.png")

manifest = {
    "workspace": str(WORK),
    "source_count": len(copies) + len(derived),
    "derived_textures": list(derived.values()),
    "authoritative_geometry": "source/build_scene_roof_tree_revision.py",
    "authoritative_refinement": "source/refine_ming.py",
}
(WORK / "ci-input-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(manifest, ensure_ascii=False))
