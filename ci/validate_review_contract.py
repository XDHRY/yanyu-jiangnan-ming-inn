from pathlib import Path
import json, struct

P = Path(".ci_work")
validation = json.loads((P / "review" / "validation.json").read_text(encoding="utf-8"))
report = json.loads((P / "review" / "report.json").read_text(encoding="utf-8"))
errors = []
if validation.get("status") != "passed":
    errors.append("GLB validation did not pass")
if validation.get("embedded_images", 0) < 10:
    errors.append(f"expected >=10 embedded images, got {validation.get('embedded_images', 0)}")
# Read the GLB JSON chunk directly so texture presence and material response are both contractual.
glb = (P / "ming_review.glb").read_bytes()
json_len, json_type = struct.unpack_from("<II", glb, 12)
if json_type != 0x4E4F534A:
    errors.append("GLB first chunk is not JSON")
    materials = {}
else:
    doc = json.loads(glb[20:20+json_len].decode("utf-8"))
    materials = {m.get("name"): m.get("pbrMetallicRoughness", {}) for m in doc.get("materials", [])}
checks = {
    "lacquer": {"roughness_max": .35},
    "metal": {"metallic_min": .65, "roughness_max": .40},
    "tile": {"roughness_max": .35},
    "paving": {"roughness_max": .45},
    "paper": {"roughness_min": .70},
}
for name, rules in checks.items():
    p = materials.get(name)
    if not p:
        errors.append(f"missing GLB material: {name}")
        continue
    rough = p.get("roughnessFactor", 1.0)
    metal = p.get("metallicFactor", 0.0)
    if "roughness_max" in rules and rough > rules["roughness_max"]:
        errors.append(f"{name} roughness too high: {rough}")
    if "roughness_min" in rules and rough < rules["roughness_min"]:
        errors.append(f"{name} roughness too low: {rough}")
    if "metallic_min" in rules and metal < rules["metallic_min"]:
        errors.append(f"{name} metallic too low: {metal}")

required = {"paper_screen.png", "black_tile_wet.png", "blue_limestone_wet.png", "lacquer_black_gold.png", "brass_aged.png"}
actual = set(report.get("textures", {}))
missing = sorted(required - actual)
if missing:
    errors.append("missing material payloads: " + ", ".join(missing))
out = {"pass": not errors, "errors": errors, "embedded_images": validation.get("embedded_images"), "texture_files": sorted(actual), "material_pbr": materials}
(P / "review" / "ci-contract.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
