# Viewer refinements — v0.14.1

- Workspace labels are **Design** and **Simulation**.
- The **Selection** menu sits immediately after Grid. Choose Body, Part, Face, Edge or All geometry. Double-click selects the clicked named part; triple-click selects the clicked solid body. Ctrl/Cmd-click retains multi-selection. A part may contain several solid bodies.
- Native body membership comes from the saved STEP in the existing isolated CAD worker. A hollow solid is one body, including its inner faces. Ambiguous membership fails explicitly. The cache is bound to the CAD artifact; it does not rebuild or change a saved design revision. Mesh-only components expose a whole-component mesh body and identify that provenance.
- Selecting a body highlights only its faces, shows its native volume/bounds and includes the body reference and face membership in Ask AI context.
- A camera-aligned CAD **X/Y/Z** indicator remains at the top right of the viewport, including fullscreen. It is separate from the optional world axes in Settings and the existing view cube.
- Simulation initially shows analysis/component choice, representative material choice, relevant boundary conditions, Run and Ask AI. Run saves the setup automatically. Material values remain explicit assumptions rather than certified properties.
- Mesh controls, extra loads, detailed properties and study JSON are under **Advanced settings**. Save and Reset are also there. Motion bodies and joints expand individually. Previous results stay collapsed; active or failed jobs and the current numerical result remain accessible.

Verification uses disposable models: native single/multiple/hollow solids, body references in Ask AI, double/triple-click selection, XYZ location, compact visible-control counts, material persistence, actual thermal/motion jobs, scalar fields, downloads, face conditions, playback, fullscreen and narrow layouts. Existing numerical solvers and their limits are unchanged. See [Simulation guide](SIMULATION_0_14.md).

Validation for this update: 19 backend tests (including multi-solid and hollow-solid membership and Ask AI regression checks), 31 JavaScript tests, and three browser groups covering compact simulation, real thermal/structural/motion jobs, selection gestures, native body references, camera-following XYZ orientation and installed-runtime behavior. The installed main viewer reports v0.14.1; all 41 existing saved user model records were hash-checked unchanged.
