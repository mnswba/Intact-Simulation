# Constrained design, explicit history and acceptance checks

All lengths are mm, angles degrees, geometry axes CAD XYZ. FreeCAD 1.1.4 runs in a separate sandbox; its Python/OCCT libraries are never loaded into the build123d server process. Existing build_model programs remain supported and do not acquire an invented feature tree.

## Tested disk example

Start with `set_design_requirements` and omit model_id to create a draft. Save the user's intent and meaningful assumptions, then use the returned model_id throughout. An empty draft contains no substitute primitive.

```json
{
  "source_text": "40 mm disk, 8 mm thick, two 6 mm through holes at X ±10 mm",
  "checks": [
    {"id":"size","kind":"bounds","part_id":"disk","expected":{"length":40,"width":40,"height":8}},
    {"id":"bores","kind":"hole_pattern","part_id":"disk","expected":{"count":2,"diameter_mm":6,"depth_mm":8,"through":true,"centers_mm":[[10,0,0],[-10,0,0]],"axis":[0,0,1]}}
  ]
}
```

Pass this sketch to create_sketch with parameters `{"diameter":40,"thickness":8,"bore_diameter":6}`:

```json
{
  "id":"outline","plane":"XY",
  "geometry":[{"id":"circle","kind":"circle","center":[0,0],"radius":20}],
  "constraints":[
    {"id":"diameter","kind":"diameter","entities":["circle"],"value":{"parameter":"diameter"}},
    {"id":"cx","kind":"distance_x","entities":["circle"],"points":[3],"value":0},
    {"id":"cy","kind":"distance_y","entities":["circle"],"points":[3],"value":0}
  ]
}
```

Solve and inspect `solver_code`, `fully_constrained`, DoF and conflict/redundancy indices. Conflicts are diagnostic results, not a successful design. Zero DoF is required by default. An explicit lock is available for fixed construction geometry; do not lock an entire sketch merely to hide missing design constraints when dimensions should remain editable.

Pass these features to edit_feature_tree:

```json
[
  {"id":"pad","kind":"extrude","part_id":"disk","sketch_id":"outline","params":{"height":{"parameter":"thickness"}}},
  {"id":"bores","kind":"hole","base":"pad","part_id":"disk","params":{"diameter":{"parameter":"bore_diameter"},"centers":[[10,0,0],[-10,0,0]],"axis":[0,0,1],"through":true}}
]
```

Each feature's part_id names an output tip. Reusing it replaces that part's previous tip, not an additional component. Omit part_id for intermediate cutters or helper solids. References must point to earlier feature IDs; forward references/cycles fail. Upsert edits preserve other steps; replace edits replace the entire graph. Suppressing an operation aliases it to its base; suppressing a root can leave no geometry and must fail safely.

`update_parameters` rebuilds attached feature projects through FreeCAD. `set_sketch_constraints` stages constraint changes; solve and rebuild explicitly. `edit_feature_tree(rebuild=false)` stages a detached graph while preserving the prior solid. Do not describe staged changes as already present in CAD. Failed rebuilds preserve the last valid graph and geometry.

## Operation contracts

- Extrude: positive height, optional direction. Defaults: XY +Z, XZ −Y, YZ +X.
- Revolve: angle_deg in (0,360], origin and axis. The closed profile must not self-intersect around the axis.
- Hole: positive diameter, centers in assembled XYZ, axis, through boolean. A through cutter spans the complete part; a blind cutter starts at each center and extends along axis for depth. Do not start a blind cutter in empty space and claim its nominal depth is measured inside the solid.
- Fillet/chamfer: radius/distance plus explicit edge selectors. Select by geometry (`circle` or `line`), radius, point `at`, or direction. Multiple matches fail unless `all:true` is explicit. Example: `{"geometry":"circle","radius":20,"at":[20,0,8]}` selects a disk's upper rim.
- Boolean: base, tool, operation cut/fuse/common.
- Pattern: base, integer count 1–128, XYZ step, optional fuse. A single named output can contain several disconnected solids.
- Transform: translation, rotation axis, origin and angle_deg.

## Verification and stable references

`verify_design` checks the actual exported STEP, not feature labels. Through/blind state uses native axis intersections; cylindrical depth is the measured axial extent of the bore surface. Hole centers are points on the axis, compared transversely. Complex curved entries may need a more specific depth convention; do not infer a full drill-tip depth from a cylindrical face.

Clearance is native minimum part distance; interference uses common volume. Surface-normal wall rays report finite samples. Passing samples do not prove a global minimum; without explicit allow_sampled acceptance the result remains unverified. Missing/unknown criteria never pass. Requirements must be updated when the user intentionally changes a formerly required dimension.

`bind_reference` stores a stable:label for an inspected current entity. Hole anchors follow a named hole feature and its center index; changing that feature's center order changes the indexing convention. Other entities match unique geometric signatures. Same-artifact references retain exact identity. Unrelated Python source changes, deleted features and multiple candidates fail safely; select and bind again rather than guessing.

## Accuracy and exports

`set_accuracy` stores requested dimension/meshing/convergence targets and rebuilds. `check_accuracy` measures kernel tolerances, native-to-STL volume difference and two-resolution volume/area changes. Kernel tolerances are numerical metadata, not manufacturing accuracy. Two samples are not a proof of global surface deviation. Refinement that reaches a resource/resolution limit is unverified.

Structured projects save version 3 JSON with sketches, constraints, parameters, graph, intent and accuracy. Versions 2 and 3 remain importable. STEP/STL/GLB/3MF are generated by the existing native bridge. `design.FCStd` contains native solved sketches and recorded PartDesign feature steps; Intact's JSON graph drives parameter rebuilding. Python download is standalone FreeCAD 1.1.4 code with embedded graph and editable PARAMETERS, producing STEP and a native document. Imported STEP/Python projects still use their original workflow.

## Additional 0.11 contracts

`concentric` takes two circle/arc entity IDs; it constrains their centers using the native solver. `placement` checks a part’s bounding-box `center_mm`, `min_mm` or `max_mm` against XYZ arrays. This is not a general orientation/mating constraint. Requirements additionally record `components` (strings), `materials` (part ID to intent string) and `interfaces` (strings). These fields preserve the brief; physical material properties are not geometrically certified.

The viewer Ask AI button starts a scoped, user-triggered task using the signed-in OpenAI local client. The task first reads its request/images and current model, preserves a structured feature graph, applies revision guards, verifies actual exports and returns an answer. Read-only question tasks cannot change CAD. The current desktop conversation is not resumed or impersonated.
