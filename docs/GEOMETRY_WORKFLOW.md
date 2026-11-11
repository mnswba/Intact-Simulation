# Intact geometry editing · desktop plugin 0.8.0

Intact now supports **select geometry → attach a reference or sketch → ask AI for an edit → rebuild → refresh the viewer** with actual OpenCASCADE geometry. The application runs locally on this computer. ChatGPT is the agent for plugin tools; the optional direct model route uses LiteLLM.

## Use it

1. Open a model in the Intact viewer. Import STEP from Files & exports when needed.
2. Choose Parts, Faces, Edges or All geometry, then click the model. Ctrl/Cmd-click adds geometry. The assembly tree also exposes native faces and edges grouped by geometric type.
3. Open Ask AI and describe the change. Attach up to four PNG/JPEG references. Draw an arrow, outline or note with Draw / annotate. Include annotated viewport adds a real rendered PNG.
4. Press **Run AI edit**. The connected AI proposes and validates the CAD change in the background. You can orbit the view or reload the page while it works. Use Cancel to stop it.
5. When validation succeeds, Intact saves a new revision and refreshes the viewer. Errors and cancellation preserve the previous model. Revision history remains available.

On this private PC, installation connects the existing signed-in Codex client through a custom LiteLLM transport. No API key is copied from Codex or entered in chat. The CLI performs inference only, with shell, apps, browser, computer use, subagents and hooks disabled; the bounded Intact agent dispatches structured CAD tools through the existing isolated CAD worker. Account limits still apply. A hosted provider configured through INTACT_LLM_MODEL and the optional server-side API key/base takes precedence. If the connection expires, Ask AI exposes Connect / Check Codex sign-in.

An optional ChatGPT handoff section retains Save edit request / Copy prompt for users who prefer an agent in their ChatGPT conversation. This is separate from the direct Run workflow and requires explicitly sending that prompt to ChatGPT.

**Grid lines:** click **Grid: On/Off** in the top toolbar, or **Settings → Edges & guides → Grid**. Both controls synchronize and save immediately. Hiding works even in the Grid display preset.

## Viewer controls

- Native part, face and edge picking; exact volume, surface/face area, bounds, radius/diameter, center, normal and curve length; multi-selection and reference copying.
- Snap to vertices, edges or faces; persistent point distances, CAD XYZ deltas and angle from the CAD X axis; delete individual dimensions. Native vertices, straight lines, circles, planes and cylinders use analytic geometry. Other preview surface/curve picks are explicitly approximate.
- Component groups, text filter, per-part color/visibility, isolate selection and show all. Face/edge groups describe surface/curve types; they do not recreate a designer's feature history.
- Interactive orientation cube with face/edge/corner directions, six named axial views, isometric fit, perspective/orthographic projection, orbit/pan/zoom and auto-orbit with speed.
- Solid, Render, X-ray, Hidden line, Wireframe and Grid modes; shaded/flat/hidden/off surfaces; original/single/per-part colors, editable palette (1–50), opacity, visible/all edges and edge color.
- Light (default), Medium Light, Medium and Dark neutral UI/background themes; independent grid/axes and colors; lighting, exposure EV, rotation, softbox size, fill ratio; background, floor/shadows, colors and floor at origin/lowest point. Preview/Final changes raster and shadow resolution; no path tracing is claimed.
- CAD X/Y/Z section with position, cap and reverse; assembly explosion; parameter rebuilds, history restore, PNG and STEP/STL/GLB/3MF/Python/project downloads.
- Drawing selection/orbit, pan, move, pen, line, arrow, rectangle, ellipse, text, translucent highlight, eraser, color/width, undo/redo/clear and drawing clipboard.

Settings, dimensions and drawings persist locally without incrementing the CAD revision. Measurements use assembled coordinates even when the display is exploded. Clipping/explosion do not alter exported solids. No anonymous analytics are collected.

## Geometry and recovery

Worker tessellation records a native face ID for every triangle range. A separate topology artifact stores native face/edge/vertex measurements in CAD XYZ millimeters. IDs are local to a part in one artifact; they are **not permanent topological names**. Edit requests include the model ID, revision and artifact checksum. A stale request is rejected. Successful geometry changes clear old selections, dimensions and sketches. Failed builds leave the saved CAD unchanged and record the error for repair. Saved revisions remain restorable.

STEP imports retain an immutable, checksum-addressed source asset. The isolated worker injects `input_shape` and `imported_parts` so an agent can revise imported solids without filesystem access. Project JSON embeds its STEP asset and rebuilds geometry on import rather than trusting mesh/measurement claims. Download `input.step` beside `program.py` for external execution. Original source STEP files are never overwritten.

CAD Python continues to run in the rootless filesystem/network sandbox. Selection data, attachments and display preferences do not grant code access to the host. Saved projects created before this version receive native topology on first open while retaining applicable reference studies.

## Verification

`backend/tests/test_geometry_workflow.py` covers native topology/triangle mapping, analytic dimensions, strict preferences, MCP image delivery, failure/repair and stale protection, imported STEP edits and portable asset round trips. The complete backend suite passes 44 tests, including the direct-run connection, transport, cancellation and recovery tests in `backend/tests/test_direct_ai.py`.

`scripts/test-geometry-workflow.py` runs a real browser and official MCP client against a separate copy of the user's 23-part iPhone. It verifies actual face/edge ray picking, a 71.50 mm vertex-snapped width, grouped navigation, all six view modes and settings persistence, drawing undo/redo, reference attachments, queued edit images, isolated STEP modification and automatic refresh. It enlarged one Ø1.3 mm speaker bore to Ø1.8 mm, checked 3.1651546 mm³ of removed material against the analytic annulus volume, confirmed the other 22 parts' native measurements stayed identical, rejected stale references and rendered an MCP PNG. Results and screenshots are in `outputs/workflow-audit/`.

General 3D FEA/CFD remains outside the implemented analysis scope. Existing reduced rectangular beam and cooling-fin results are retained; this viewer update does not add a general simulation solver.


## Live direct AI verification

`scripts/test-direct-ai.py` uses a disposable plate, a real Chromium browser and the actual signed-in model through LiteLLM. The user-style instruction adds four Ø3 mm mounting holes, preserving a Ø6 mm center bore and a 60 × 30 × 6 mm plate. Native topology and the independently calculated removed volume verify the result. The audit reloads the page during inference, waits for automatic refresh, then cancels a second edit and checks the saved revision stays intact. It also exercises the grid toolbar, Settings synchronization, reload persistence and the Grid display preset. Reports and PNGs are stored under `outputs/direct-ai-audit/`.

Official integration references: [Codex non-interactive inference and saved authentication](https://learn.chatgpt.com/docs/non-interactive-mode), [Codex command-execution feature controls](https://learn.chatgpt.com/docs/config-file/config-reference), [LiteLLM custom providers](https://docs.litellm.ai/docs/providers/custom_llm_server).
