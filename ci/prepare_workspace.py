from pathlib import Path
import json, shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".ci_work"
if WORK.exists():
    shutil.rmtree(WORK)
(WORK / "textures").mkdir(parents=True)
(WORK / "review").mkdir(parents=True)

copies = {
    "source/build_scene_roof_tree_revision.py": "build_scene.py",
    "source/refine_ming.py": "refine_ming.py",
    "source_export_review_glb.py": "export_review_glb.py",
    "source_validate_ming.py": "validate_ming.py",
    "data_ground.json": "ground.json",
    "data_upper.json": "upper.json",
    "texture_huanghuali.png": "textures/huanghuali.png",
    "texture_teal_brocade.png": "textures/teal_brocade.png",
    "texture_lime_plaster.png": "textures/lime_plaster.png",
    "texture_blue_limestone.png": "textures/blue_limestone.png",
    "texture_lotus_panel.png": "textures/lotus_panel.png",
}
derived = {
    "asset_library_hires/textures/tex_lacquer_black_gold.jpg": "textures/lacquer_black_gold.png",
    "asset_library_hires/textures/tex_brass_aged.jpg": "textures/brass_aged.png",
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
    Image.open(ROOT / src).convert("RGB").save(target, format="PNG", optimize=True)

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
