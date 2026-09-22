from pathlib import Path
import json

P = Path(".ci_work")
validation = json.loads((P / "review" / "validation.json").read_text(encoding="utf-8"))
report = json.loads((P / "review" / "report.json").read_text(encoding="utf-8"))
errors = []
if validation.get("status") != "passed":
    errors.append("GLB validation did not pass")
if validation.get("embedded_images", 0) < 10:
    errors.append(f"expected >=10 embedded images, got {validation.get('embedded_images', 0)}")
required = {"paper_screen.png", "black_tile_wet.png", "blue_limestone_wet.png", "lacquer_black_gold.png", "brass_aged.png"}
actual = set(report.get("textures", {}))
missing = sorted(required - actual)
if missing:
    errors.append("missing material payloads: " + ", ".join(missing))
out = {"pass": not errors, "errors": errors, "embedded_images": validation.get("embedded_images"), "texture_files": sorted(actual)}
(P / "review" / "ci-contract.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
