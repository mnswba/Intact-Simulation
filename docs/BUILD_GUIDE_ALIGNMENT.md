# Build guide alignment — 10 November 2026

Source: the user's `Intact Simulation — Build Guide.docx`. The document supplies product requirements and recommendations. Its paper comparisons, timing estimates, licensing statements and model-performance claims are not adopted as verified facts. The user's explicit choice of **LiteLLM** determines the AI integration in this implementation.

## Decisions adopted

1. Keep the design as a validated, versioned JSON spec. UI parameters, guided edits and AI tool patches refer to the same data. Imports migrate old projects; undo/redo restores previous specs. Results are invalidated by changed geometry or study settings.
2. Use build123d/OpenCASCADE first. Support tested templates and generated build123d Python in an isolated worker. Kernel validation, named-face selection by rule and exact STEP exports live in Python; the browser is a preview, not an exact kernel measurement service.
3. Implement the agent as a small state machine through LiteLLM. Tool results supply measurements; the model does not become a physics solver. Atomic edits, bounded attempts and deterministic summaries limit unsupported output.
4. Show materials and boundary conditions before solving. A design/study edit clears approval. The service binds approval and cached results to a spec hash.
5. Compare independent analytical and numerical methods without averaging them. Temperature comparisons use rise above ambient. Confidence remains limited by reduced physics and material provenance.
6. Keep Tier C explicitly unavailable until a surrogate has training data and held-out validation. Keep CFD planned rather than presenting convection as a flow solution.

## Measured implementation status

| Area | Current implementation | Remaining work |
| --- | --- | --- |
| Spec | Pydantic backend, typed browser schema, atomic patches, hashes, undo/redo, old-project migration | A generated schema bridge and richer feature/placement/joint contracts |
| CAD | Real B-rep templates plus sandboxed Python CAD, measured meshes, kernel validation and STEP/STL | CadQuery fallback when justified, import/healing, placement/joint assembly editor |
| Agent | Installed LiteLLM SDK, bounded tools, clarification/repair logic, server-side provider configuration | Provider/model selection and live prompt evaluation; no model is connected yet |
| Viewer | Five preview templates plus a three-component enclosure; part selection/editing, capped X/Y/Z cuts, colors, opacity, hide/show and exploded view | Exact kernel probes, face picking, isolate shortcut, mate/placement tools |
| Simulation | User review table; analytical and numerical 1D beam/fin comparisons; balance/refinement checks | Radiation, sourced material catalog, Gmsh and real 3D FEA, then thermoelasticity |
| Results | Separate Tier A/B values, spread and conservative screening confidence; Tier C unavailable | Full 3D fields, singularity handling, validated improvement suggestions |
| Storage | Browser projects and portable spec files; SQLite backend versions/results/job status | Cloud project sync, account partitioning, multi-user quotas and distributed worker recovery |
| ChatGPT plugin | Local stdio MCP tools, saved CAD programs, viewer, STEP/STL, private personal marketplace registration | Desktop restart/activation; remote web/mobile hosting |
| Hosting | Updated private website; Python service prepared on disk | Deploy Python service on a separate compute host and configure its connection |

The Python service and its tests are code artifacts, not a hosted solver connection. Assembly visualization is supported; assembly numerical analysis remains unavailable. The browser's existing reduced models remain available while backend hosting and a model service are absent. Production hosting is still private to the owner.
