from pathlib import Path
import json, sys
from PIL import Image, ImageStat

out = Path(sys.argv[1] if len(sys.argv) > 1 else "diagnostics")
pngs = sorted(out.glob("*.png"))
errors = []
if len(pngs) < 10:
    errors.append(f"expected >=10 PNGs, got {len(pngs)}")

stats = {}
for path in pngs:
    im = Image.open(path).convert("RGB")
    st = ImageStat.Stat(im)
    spread = sum(st.stddev) / 3.0
    stats[path.name] = {"size": list(im.size), "mean_stddev": round(spread, 3)}
    if im.size != (720, 480):
        errors.append(f"{path.name}: unexpected size {im.size}")
    if spread < 5.0:
        errors.append(f"{path.name}: likely blank/flat render (stddev={spread:.3f})")

manifest_path = out / "render_manifest.json"
if not manifest_path.exists():
    errors.append("render_manifest.json missing")
else:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("view_count") != 10:
        errors.append("render manifest view_count != 10")
    counts = manifest.get("component_counts", {})
    for key, minimum in {"dougong": 20, "hanging_plaque": 5, "rain_chain": 10}.items():
        if counts.get(key, 0) < minimum:
            errors.append(f"{key}: expected >= {minimum}, got {counts.get(key, 0)}")

blend = out / "jiangnan_diagnostic.blend"
if not blend.exists() or blend.stat().st_size < 1024 * 1024:
    errors.append("packed Blender file missing or unexpectedly small")

report = {
    "pass": not errors,
    "errors": errors,
    "renders": stats,
    "render_count": len(pngs),
    "blend_bytes": blend.stat().st_size if blend.exists() else 0,
}
(out / "diagnostic-validation.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
