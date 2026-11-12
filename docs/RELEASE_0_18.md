# Intact Simulation 0.18.0

## Edge selection

Edge mode picks native geometry within a configurable **16 CSS pixel** radius, independent of zoom. It works just outside a solid silhouette and shows a thick amber hover preview, reference and length. Click selects; Ctrl/Cmd-click adds. While hovering, Tab/Shift+Tab cycles nearby candidates. Settings → Edges & guides → Edge pick radius px supports 4–32 pixels. Visible-edge mode checks occlusion at the candidate’s projected point; all-edge/X-ray/wireframe views allow hidden edges deliberately. Selected edges use thick lines. Native references, measurements, part/body click gestures and export coordinates remain intact. Mesh-only TPMS does not acquire native CAD edges.

## Mandatory geometry audit and design V&V

Before a new CAD revision is published, the isolated worker checks native B-rep validity, positive finite solid volumes, dimensions and tessellation, or watertight/winding/finite mesh geometry. Export checks include GLB structure, 3MF integrity and native STEP reopening, part identities, volumes and dimensions.

Invalid native shapes may receive bounded OpenCASCADE healing or solid-orientation correction. Repairs must retain solid/face counts, bounds within 1e-6 mm, and volume/area within 1e-8 relative or 1e-6 absolute. Failed invariants or exports reject the build and preserve the previous revision. Saved native design requirements are checked before commit; known failures reject the proposal. Missing or unsupported criteria remain explicitly unverified. Source-repair instructions guide the AI without authorizing removal of required features or weaker checks. Downloaded Python includes the same bounded native repair checks.

Files & exports → **Geometry audit & V&V** shows the summary and audit download. The new read-only `audit_model` tool can recheck current saved requirements. There are **64 MCP tools**. This auditor uses deterministic geometry evidence, not another hosted AI model. It does not certify fits, manufacturing, fatigue, safety or physical simulation performance. Assembly interference, global thickness and arbitrary user intent are not inferred automatically.

## Thirty new industry models

The [Finished Work collection](https://www.intactsimulation.com/finished-work/) now contains 50 original concepts. The 30 new assemblies cover aerospace/marine, medical/laboratory, energy/infrastructure, automation, mobility and architecture/consumer technology, with 1,072 native named parts in total. Each has a prompt recorded before source creation, STEP/STL/GLB/3MF exports and a geometry audit in its public ZIP. Prompts appear on gallery cards and in the demo. The original 20 have clearly labelled reconstructed design briefs rather than invented verbatim transcripts.

All new geometry ran through Intact’s Linux sandbox. A combustor export-volume discrepancy was repaired by moving its hole pattern clear of cut-plane seams; the strict gate was retained. Gallery bounds use precise mesh vertices rather than transformed local bounding boxes. Native CAD checks are distinct from the approximation and visualization limits of GLB tessellation.
