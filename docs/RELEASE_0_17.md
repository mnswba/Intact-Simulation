# Intact Simulation 0.17.0

Interactive workflows, implemented in Intact’s existing Python CAD engine and original viewer. This is an implementation inspired by reviewed behavior, not an embedded copy of either Rust CAD application.

## AI and viewer additions

- `list_commands` / `describe_command`: discover the installed MCP tool catalog and exact schemas. The catalog uses the actual registered tools, filters Ask AI permissions, and calls remain ordinary named MCP tools rather than a shell or an unguarded execution wrapper.
- `control_view`: read/update viewer settings, save/list/restore/delete named views. Supports section planes, explosion, projection, camera, visibility, display colors and grid. View operations preserve CAD revisions. A separate view revision rejects stale writes; the open viewer refreshes AI changes in Design. Saved views reject geometry changes rather than apply stale anchors.
- `preview_parameters`: rebuild candidate scalar parameters in a temporary isolated project, returning actual part bounds and volumes without adding project history. Imported source assets are copied into the temporary root. No preview files are retained.
- `parameter_configuration`: save/list/delete up to 30 named numeric parameter snapshots. `apply_configuration` requires the expected CAD revision and rebuilds through the normal sandbox pipeline, committing only after success.
- Parameter inputs and `update_parameters` accept bounded arithmetic using existing parameter names, parentheses and `+ - * /`, for example `length = width * 3`. No Python eval, calls, attribute/index access, exponentiation or unit inference. Expressions resolve for this operation; they are not a persistent constraint solver. Sketch constraints remain the tool for persistent design intent.
- **Commands** in Settings, or **Ctrl/Cmd+K**, opens a searchable command palette and named-view controls. The same view settings and bookmark service are available through MCP.

Example AI requests:

> Show a Z section at 50%, hide the lid, use an orthographic camera, and save the view as Interior.

> Preview length = width * 3 without changing the model. Report its actual dimensions and volume.

> Save that parameter set as Long. Apply it to the current revision after checking the preview.

The AI must read the current model and view revision first. Native part/face identities and geometry validation still apply. View cameras use viewer coordinates in mm (CAD X,Z,-Y). Named configurations contain numeric snapshots, not formulas or material/style rules. There is no AI model retraining or promise that arbitrary designs/analyses are supported.

## Upstream review and licensing

Reviewed [CADCraft](https://github.com/storytold/cadcraft/tree/ca87680fb0f9d7803d3e64c808d0a3f7a196fdaa) and [SolidCraft](https://github.com/tangency-labs/solidcraft/tree/2220e049bc34f9def2ee011887cd8c9ace125f3d): command discovery, named views and noncommitting parameter checks informed this design. Their cores offer MIT/Apache-2.0 licenses. Their branding and, for SolidCraft, UI-kit/look/theme/interface material have separate restrictions. No upstream source code, brand, UI assets or restricted interface material was copied. Intact’s implementation remains Apache-2.0 and uses its existing dependencies.

## Website showcase

Twenty original models: five robotics, five powertrain, five product concepts and five sampled TPMS structures. Public source lives under `models/showcase/`. The Finished Work gallery offers search/category filters, measured envelopes, interactive component previews and downloadable example packages. Native concepts include STEP; sampled TPMS packages provide GLB/STL/3MF without an exact STEP claim. The website remains a prebuilt demonstration; custom AI CAD and simulation use the local plugin.
