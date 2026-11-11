# Intact Simulation in ChatGPT · 0.12

The plugin name is **Intact Simulation**, ID `intact-simulation`. Its portable manifest, local MCP server and bundled skill work together; the ChatGPT conversation supplies the AI. There is no separate provider setup, API-key requirement or LiteLLM routing. Viewer AI tasks start only when the user clicks Ask AI.

Install with `python3 scripts/install-chatgpt-plugin.py --windows-home /mnt/c/Users/User`, restart ChatGPT desktop and start a new conversation with Intact enabled. Existing other plugins and CAD projects are preserved. The local viewer stays available between tool connections.

Ask ChatGPT to create the design. It should build geometry, call `validate_model` with dimensions from the brief, inspect snapshots from useful views and return viewer/export links. For selected geometry in the viewer, **Ask AI** directly starts a model-scoped task using the signed-in OpenAI local client. The answer and rebuilt model appear in the viewer without a generated prompt or clipboard handoff. This is a separate task; it does not insert messages into the current desktop conversation.

History clicks are read-only previews. Use **Restore** only to make a historical design current. Current/identical restores and artifact-cache repairs do not add revisions. Historical previews disable editing and export their own geometry.

TPMS tools support six nodal families with clipped/capped, watertight mesh exports. They report resolution and mesh-based measurements. Lattice band is not constant wall thickness; mesh geometry is not an exact STEP solid. General CFD and 3D FEA are outside the implemented scope.

No foundation-model training or public directory submission is performed by this installer. Windows plugin files can be validated from WSL, but direct Windows ChatGPT window control is unavailable in this executor.

Official sources: [plugin packaging](https://developers.openai.com/plugins/build/plugins), [local MCP availability](https://learn.chatgpt.com/docs/extend/mcp).

## Constrained design workflow in 0.10

The plugin exposes 33 tools, including saved design requirements, FreeCAD constrained sketches with actual solver diagnostics, explicit editable feature graphs, named references, exported-solid acceptance checks and requested accuracy/mesh convergence checks. Existing Python models and TPMS remain supported. Imported/opaque CAD does not automatically acquire an editable feature tree.

The viewer’s **Design intent & features** panel edits dimensions and supported feature properties, suppresses steps, rebuilds, and displays verification. New sketch drafts open as 2D sketches until geometry is built. Native FCStd and standalone FreeCAD Python exports are available for structured projects; the Intact feature graph drives rebuilding.

The installer also prepares a checksum-verified FreeCAD 1.1.4 runtime. See [the structured modeling contract](../plugin/skills/intact-cad/references/structured-modeling.md) and [open-source inventory](PRIORITY1_OPEN_SOURCE.md).

## Ask AI in 0.11

Description → Ask AI → answer or rebuilt model, with progress, cancellation, revision guards and a read-only question mode. Requires an installed OpenAI local client signed in on this computer; no LiteLLM or additional API key is added. Only the selected model and request are exposed to the task. Concentric constraints, native bounding-box placement checks and structured component/material/interface intent extend the priority-1 workflow.

See [priority 2/3 release scope and measured test results](PRIORITY23_RELEASE.md) for the 53-tool engineering release.
