# Intact 0.9: workflow comparison and iPhone-log review

Reviewed 10 November 2026. This is a capability/workflow review, not a controlled quality ranking. Product documentation describes capabilities; it does not prove how well a particular model is built.

## Your iPhone log

The attached `iphone logs.txt` records 40 numbered actions. Many concern missing cadgen/uv, a failed pip install, an incomplete virtual environment, checking installation progress, stalled dependency tracking, blocked loopback networking and two incorrect paths. More commands did not add more geometric detail.

The important successful checks were action 32 (reopen the saved STEP, verify 23 solids, validity and frame dimensions 71.5 × 147 × 7.8 mm at 0.001 mm tolerance), actions 38/40 (render and inspect front/rear images), and returning actual editable source and STEP/GLB files. The log describes a detailed **exterior concept**, not a dimensionally verified internal phone assembly. It contains evidence of successful checks, not evidence that either plugin is universally more reliable.

Intact's build tool performs isolation, source validation, native solid checks, tessellation, topology inspection and multiple exports internally. One tool call can therefore represent many operations. Its new `validate_model` tool reopens the physical saved export, compares requested per-part bounds/IDs and reports native curved-face radii/axes/centers. The updated skill requires design-specific checks and actual snapshots; multi-sided phone models receive front and rear review. Generic validity alone cannot establish that every intended feature exists.

## Capability comparison

| Workflow | Documented strengths | What Intact should learn or disclose |
| --- | --- | --- |
| [text-to-CAD](https://github.com/earthtojake/text-to-cad) | Agent-driven Python CAD, assemblies, STEP/mesh exports; also drawings, manufacturing/printing, robotics and stress workflows | Keep editable source, useful part labels, artifact reopening and visual review. Intact does not yet match the breadth of its manufacturing/robotics integrations. |
| [Zoo Design Studio](https://zoo.dev/docs/faq) | AI B-rep generation/editing, KCL, sketches/feature workflows and assemblies; modeling uses cloud services | Preserve explicit parameters and edit intent. Intact's grouped topology is not a recovered sketch/feature tree, and has no mate solver. |
| [CadQuery](https://cadquery.readthedocs.io/en/latest/importexport.html) | Script-based CAD and assemblies with STEP and mesh exchanges | A CAD library is not itself an AI agent. Reopening exports and preserving occurrence labels matter independently of the conversation model. |
| [nTop's TPMS functions](https://support.ntop.com/hc/en-us/articles/360053267814-What-equations-are-used-to-create-the-TPMS-types) | Published implicit lattice equations and specialist lattice workflows | Intact implements six sampled nodal families, clipped/capped meshes and measured density; it does not claim nTop's optimization, manufacturing or analysis feature set. |
| Intact 0.9 | ChatGPT conversation tools, isolated native CAD, geometry-aware edit requests, viewer, immutable history previews, dimensional/export validation and TPMS generation | Current implemented features are evaluated locally. No claim of universal superiority, unlimited complexity, constant TPMS wall thickness, general CFD or 3D FEA. |

The practical reliability target is: requested dimensions and components → actual geometry → saved-file reopening → appropriate native facts → useful visual views → recoverable edits. Neither the number of shell commands nor the number of test fixtures is a substitute for checking the requested design.

## What “training” means here

`evals/intact-cad-200.jsonl` contains 200 authored regression configurations: 50 CAD families, 144 combinations of TPMS family/mode/envelope/parameters, and six additional assemblies. These exercise tools, exports and instructions. They do not mean 200 independently AI-generated designs, 200 distinct design families, or a fine-tuned ChatGPT model. Open-ended generation still comes from the model selected in the user's ChatGPT conversation.

## Implemented expansion and retained boundaries

Native CAD supports 128 named parts (formerly 32), 150 numeric parameters (50), 120 KB source (40 KB), 1.2 million preview triangles (500,000), 100 seconds CPU, 120 seconds wall time, 4 GiB address space and 64 MiB per artifact. TPMS sampling is bounded at 2.5 million grid points, 12–64 samples/cell. Isolation and resource limits remain enforced.

TPMS has six families, box/cylinder/sphere envelopes, sheet/solid modes, phase, level, band, gradient and editable resolution. Band is dimensionless; it is not constant mm wall thickness. Volume/area/density are mesh estimates. All-mesh or mixed native/mesh assemblies export STL/GLB/3MF rather than claiming exact STEP. GLB uses meters and Y-up; STL/3MF use CAD XYZ millimeters, following the [glTF coordinate specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#coordinate-system-and-units).

The separate LiteLLM/provider integration, keys/settings, autonomous model jobs and viewer connection controls have been removed. In a standalone browser, Ask AI prepares an attached request and prompt for the user's ChatGPT conversation. It cannot silently submit a message into the desktop app. The user sends the prompt; ChatGPT calls the local tools and the viewer refreshes. This uses the [documented local MCP/plugin architecture](https://developers.openai.com/plugins/build/plugins), with [surface-specific availability](https://learn.chatgpt.com/docs/extend/mcp).
