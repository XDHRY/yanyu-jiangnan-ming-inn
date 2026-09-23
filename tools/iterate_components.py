"""Continuous Component Iteration & Adjustment Pipeline.
Loops through reference images, manufactures/adjusts 3D components, binds PBR materials,
rebuilds master scene, validates contracts, runs Blender diagnostics, and prepares GitHub Pages.
"""
from pathlib import Path
import os, sys, json, subprocess, argparse

ROOT = Path(__file__).resolve().parents[1]

def run_step(title, cmd, cwd=ROOT):
    print(f"\n==========================================")
    print(f"▶ {title}")
    print(f"==========================================")
    res = subprocess.run(cmd, cwd=cwd)
    if res.returncode != 0:
        print(f"❌ FAILED: {title} (exit code {res.returncode})")
        sys.exit(res.returncode)
    print(f"✔ PASSED: {title}")

def main():
    parser = argparse.ArgumentParser(description="Continuous Ming component iteration pipeline")
    parser.add_argument("--skip-render", action="store_true", help="Skip native Blender diagnostic rendering")
    parser.add_argument("--blender-path", default=r"D:\blender-portable\blender.exe", help="Path to Blender executable")
    args = parser.parse_args()

    # Step 1: Manufacture / update all standalone 3D components from asset library specs
    run_step("1. Manufacture Standalone Components",
             [sys.executable, str(ROOT / "source" / "component_factory.py")])

    # Copy new models to asset_library/models/ for WebGL / GitHub Pages access
    models_src = ROOT / "generated_assets" / "models"
    models_dst = ROOT / "asset_library" / "models"
    models_dst.mkdir(parents=True, exist_ok=True)
    for glb_file in models_src.glob("*.glb"):
        (models_dst / glb_file.name).write_bytes(glb_file.read_bytes())
    print(f"✔ Copied {len(list(models_src.glob('*.glb')))} models to asset_library/models/")

    # Step 2: Prepare CI workspace
    run_step("2. Prepare CI Workspace",
             [sys.executable, str(ROOT / "ci" / "prepare_workspace.py")])

    # Step 3: Build latest procedural scene
    work_dir = ROOT / ".ci_work"
    run_step("3. Build Procedural Scene",
             [sys.executable, "build_scene.py"], cwd=work_dir)

    # Step 4: Refine Ming joinery & bind PBR materials
    run_step("4. Refine Ming Materials and Joinery",
             [sys.executable, "refine_ming.py"], cwd=work_dir)

    # Step 5: Validate generated GLB
    run_step("5. Validate GLB Structure & Geometries",
             [sys.executable, "validate_ming.py"], cwd=work_dir)

    # Step 6: Validate PBR material contracts
    run_step("6. Validate PBR Material Contracts",
             [sys.executable, str(ROOT / "ci" / "validate_review_contract.py")])

    # Step 7: Native Blender 10-camera diagnostic render
    if not args.skip_render and Path(args.blender_path).exists():
        run_step("7. Native Blender EEVEE Diagnostic Renders",
                 [args.blender_path, "--background", "--python",
                  str(ROOT / "ci" / "blender_diagnostic.py"), "--",
                  "--input", str(work_dir / "ming_review.glb"),
                  "--output", str(ROOT / "diagnostics")])

        # Step 8: Validate diagnostic renders
        run_step("8. Validate Diagnostic Outputs",
                 [sys.executable, str(ROOT / "ci" / "validate_diagnostics.py"), "diagnostics"])

        # Step 9: Build contact sheet
        run_step("9. Build Diagnostic Contact Sheet",
                 [sys.executable, str(ROOT / "ci" / "make_contact_sheet.py"), "diagnostics"])
    else:
        print("\n⏩ Skipped native Blender render step.")

    print("\n🎉 Component Iteration Pipeline Completed Successfully!")
    print(f"Public Live Preview: https://xdhry.github.io/yanyu-jiangnan-ming-inn/")

if __name__ == "__main__":
    main()
