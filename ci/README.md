# Blender diagnostic CI

This directory turns the Ming-style Jiangnan inn into a reproducible low-cost review loop.

The workflow intentionally uses the latest corrected geometry source:
`source/build_scene_roof_tree_revision.py`, then regenerates the GLB from source data instead of trusting stale generated files.

Pipeline:
1. Normalize legacy file names into an isolated `.ci_work/` directory.
2. Rebuild procedural geometry.
3. Reapply Ming refinement and embedded textures.
4. Validate GLB structure and geometry.
5. Import the GLB into native Blender.
6. Verify authoritative scene components (dougong clusters, lacquered entrance plaque and rain chains) survived rebuild, material binding and GLB import.
7. Render ten 720x480 Eevee viewpoints.
8. Validate nonblank outputs and upload PNGs plus the packed `.blend` as a GitHub Actions artifact.

High-leverage components now live in the authoritative procedural generator. The diagnostic layer no longer duplicates them; it verifies their presence and renders them from ten spatial viewpoints.
