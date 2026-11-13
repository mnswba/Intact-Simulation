# Working on Intact Simulation

Read README.md and CONTRIBUTING.md before changes. The primary local plugin is in plugin/, its Python/MCP implementation is in backend/intact_backend/, and the viewer source is scripts/plugin-viewer.mjs plus scripts/viewer/.

Preserve user projects, stable part IDs, revision guards and unrelated geometry. Never run generated CAD outside the Linux bubblewrap or Windows AppContainer sandbox, guess ambiguous geometry references, fabricate numerical results or weaken verification criteria to hide failures. Distinguish native solids, sampled meshes and faceted STEP.

Use the relevant backend tests for engine/tool changes; run npm test for website geometry changes. Rebuild viewer.js with node scripts/build-plugin-viewer.mjs after changing its source. Installer-dependent, FreeCAD and browser checks require their documented host prerequisites. Never commit runtime state, credentials, generated outputs or third-party binaries.

A new GitHub checkout is not automatically a public plugin-directory listing. Do not claim live client, solver or GUI verification when only a contract/mock was tested. Keep README, VERSION and plugin manifests consistent when changing releases.
