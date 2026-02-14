# projekt_001 – Involute gear visual test

Place **involute_gear_test.FCStd** in this folder (same directory as `metafile.yaml`).

Then create or update reference images:

- **First time / missing references:**  
  `pixi run create-references` (or set `VISUAL_TEST_REFERENCE_MODE=create_missing` and run `pixi run test-visual`).
- **Update all references (e.g. after FreeCAD/OCC change):**  
  `pixi run create-references`.

Run visual tests: `pixi run test-visual` (requires a display, or use xvfb in CI).
