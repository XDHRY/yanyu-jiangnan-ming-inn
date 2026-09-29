# Material refinement — 2026-09-29

Four new built-in image_gen assets at native 1254 × 1254 pixels: huanghuali wood, fired dark clay, blue limestone, and an RGBA leaf. Prompts and SHA256 provenance accompany the source files. The three opaque assets use JPEG quality 95 without resizing or recoloring; the leaf retains original RGBA pixels.

Wood UVs align with each member’s principal axis, including separated rafter components. Surface maps use mirrored repeat to handle unmatched image borders; no exact seamlessness claim is made. The foliage map uses clamped sampling, double-sided alpha masking, and covers 6,204 existing individual leaves. Existing geometry remains 448,796 triangles across 10,984 mesh parts.

Blender adds subtle artistic bump from albedo to wood, clay, and stone. These are generated appearance assets, not measured PBR scans. Ten 720 × 480 Eevee diagnostic views remain the review gate. Geometry/UV integrity, embedding/provenance, foliage alpha, landscape, and joinery checks pass locally. Runtime budget and full structural/collision certification remain open.
