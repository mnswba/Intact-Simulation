# Native references, imports and recovery

Read the current model before editing. A request binds model ID, revision, artifact checksum and references such as `titanium_frame.f11` or `base.e4`. Resolve only against that exact revision and artifact. Faces expose surface type, area, center, bounds, planar normal and available radii/axes; edges expose curve type, length, endpoints and available radius/axis. These are CAD XYZ mm facts. Mesh positions are separately normalized for the viewer; do not confuse those coordinates.

`read_edit_request` returns instructions, native context, current Python and actual PNG/JPEG image content. Inspect every image. Measurement context includes assembled endpoints and a provenance note: viewer annotations are useful intent, while native geometry remains the dimensional authority. Sketches and images do not authorize unrelated operations. Stale requests need a fresh selection; never guess that an old face ID still identifies the same surface.

Use `apply_edit_request` for the request so the viewer records success/failure. Use `expected_revision` for ordinary source or parameter edits. Failed rebuilds keep the prior model. Revision numbers are positive integers, not booleans or strings.

Imported STEP retains its immutable source asset. The build worker injects `imported_parts` and `input_shape`:

```python
import build123d as bd
def build(params):
    parts = dict(imported_parts)
    cutter = bd.Pos(-24,-73.6,0)*bd.Rot(-90,0,0)*bd.Cylinder(
        params['speaker_diameter']/2,2.7,
        align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    parts['titanium_frame'] = parts['titanium_frame']-cutter
    return parts
```

The numbers above are one tested iPhone bore, not defaults for other models. Derive each cutter location, axis and depth from the selected geometry. Preserve all unrelated imported parts and openings. Changing a bore's diameter should not lengthen it, erase another hole or replace the assembly with a placeholder.

Use `revisions` to list history, then `get_model(revision=...)`, `open_viewer(revision=...)` or `snapshot_model(revision=...)` for read-only inspection. Restore only on an explicit recovery request; selecting a revision is not an instruction to create a new revision. Saved project import rebuilds source, verifies embedded STEP checksums, preserves disabled components/appearance/settings and validates before creating a document. Keep `input.step` next to downloaded Python when running an imported design outside Intact.


Windows drive paths such as `C:\Users\User\Downloads\part.step` and Linux paths such as `/mnt/c/Users/User/Downloads/part.step` are both accepted by import tools on this WSL installation. Network shares need an accessible local mount.
