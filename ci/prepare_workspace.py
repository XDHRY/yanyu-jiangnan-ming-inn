from pathlib import Path
import json, shutil

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
missing = [src for src in copies if not (ROOT / src).exists()]
if missing:
    raise SystemExit("Missing CI inputs: " + ", ".join(missing))

for src, dst in copies.items():
    target = WORK / dst
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / src, target)

manifest = {
    "workspace": str(WORK),
    "source_count": len(copies),
    "authoritative_geometry": "source/build_scene_roof_tree_revision.py",
    "authoritative_refinement": "source/refine_ming.py",
}
(WORK / "ci-input-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(manifest, ensure_ascii=False))
