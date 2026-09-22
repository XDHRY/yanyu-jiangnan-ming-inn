from pathlib import Path
import hashlib, json, os, sys
from PIL import Image, ImageDraw, ImageStat

out = Path(sys.argv[1] if len(sys.argv) > 1 else "diagnostics")
out.mkdir(parents=True, exist_ok=True)
pngs = sorted(p for p in out.glob("*.png") if p.name != "diagnostic_contact_sheet.png")
entries = []

thumb_w, thumb_h, label_h = 360, 240, 24
cols = 2
rows = max(1, (len(pngs) + cols - 1) // cols)
sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (28, 28, 28))
draw = ImageDraw.Draw(sheet)

for i, path in enumerate(pngs):
    im = Image.open(path).convert("RGB")
    stat = ImageStat.Stat(im)
    hist = im.convert("L").histogram()
    total = max(1, sum(hist))
    dark = sum(hist[:16]) / total
    bright = sum(hist[240:]) / total
    thumb = im.copy()
    thumb.thumbnail((thumb_w, thumb_h))
    x = (i % cols) * thumb_w
    y = (i // cols) * (thumb_h + label_h)
    px = x + (thumb_w - thumb.width) // 2
    py = y + (thumb_h - thumb.height) // 2
    sheet.paste(thumb, (px, py))
    draw.text((x + 6, y + thumb_h + 4), path.stem, fill=(235,235,235))
    entries.append({
        "file": path.name,
        "size": list(im.size),
        "mean_rgb": [round(v, 2) for v in stat.mean],
        "stddev_rgb": [round(v, 2) for v in stat.stddev],
        "dark_clip_fraction": round(dark, 5),
        "bright_clip_fraction": round(bright, 5),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    })

contact = out / "diagnostic_contact_sheet.jpg"
sheet.save(contact, quality=90, optimize=True)

root = Path(__file__).resolve().parents[1]
tracked = [
    root / "source" / "build_scene_roof_tree_revision.py",
    root / "source" / "refine_ming.py",
    root / "ci" / "review_matrix.json",
]
source_hashes = {
    str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in tracked if p.exists()
}
metadata = {
    "schema": "jiangnan.diagnostic-iteration.v1",
    "github": {
        "sha": os.getenv("GITHUB_SHA", ""),
        "run_id": os.getenv("GITHUB_RUN_ID", ""),
        "run_number": os.getenv("GITHUB_RUN_NUMBER", ""),
        "event_name": os.getenv("GITHUB_EVENT_NAME", ""),
        "ref": os.getenv("GITHUB_REF", ""),
    },
    "render_count": len(pngs),
    "contact_sheet": contact.name,
    "renders": entries,
    "source_hashes": source_hashes,
    "review_matrix": "ci/review_matrix.json",
    "review_policy": "Inspect contact sheet first, then P0 views 02/03/06/08/09, then P1 views.",
}
(out / "diagnostic_index.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps({"render_count": len(pngs), "contact_sheet": str(contact)}, ensure_ascii=False))
