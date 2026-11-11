# Intact Simulation 0.11 — direct Ask AI

Select a part, face or edge, open **Ask AI**, choose **Change geometry** or **Ask about geometry · read-only**, and enter your description. Click **Ask AI**. The answer appears in the panel; successful changes rebuild and refresh the viewer. Optional reference images, annotated viewport, selected native references and dimensions remain attached. There is no generated prompt textarea or clipboard handoff.

The standalone viewer launches a separate, user-triggered task through the OpenAI local client already signed in on this computer. It uses existing account access and usage limits. It does not insert messages into, impersonate, or resume the current desktop ChatGPT conversation. No LiteLLM or additional model-service credentials are configured. If the local client is absent or not signed in, the task reports failure rather than pretending to run.

## Task behavior

Only the selected model and request are accessible through the dedicated MCP server. Question mode blocks geometry and design-metadata mutation. Edit tasks apply revision guards, prefer the existing structured feature graph, validate actual exported CAD, and inspect a snapshot. Independent post-run verification marks failed saved checks as **needs_review**. A successful AI response is not sufficient to declare invalid CAD verified.

The panel displays progress, answers, task history, errors and cancellation. One task runs at a time per project storage root. Cancel stops the task; completed atomic edits remain in revision history. A failed edit preserves the last valid model; if a task completed an edit before a later failure, that edit remains in history. Starting a request with stale geometry is rejected. Changes made outside an active task prevent its next mutation.

Local CAD execution remains sandboxed. The AI task has no shell, browser, computer-use, web search, apps or multi-agent tools, and installed plugins are disabled for the task. The task receives only the dedicated Intact MCP connection. User authentication files are not copied into the task or CAD sandbox. Existing normal ChatGPT plugin tools remain available outside this scoped task.

## Priority 1 status

| Area | Implemented behavior and limits |
| --- | --- |
| Structured requirements | Dimensions/checks, component intent, per-part material intent, interfaces and assumptions persist. Material/interface notes preserve intent; physical behavior is not certified by geometry. |
| Constrained sketches | Real FreeCAD solver, dimensions, parallel/perpendicular/equal/tangent/angle and now concentric circle/arc constraints; actual DoF/conflict diagnostics. |
| Editable history | Explicit sketch/feature graph; editable extrusion, revolution, holes, fillets, chamfers, booleans, linear patterns, transforms and suppression. Opaque imports do not automatically recover a graph. |
| Stable references | Immutable artifact identity, supported hole-feature anchors and unique geometric signatures; missing/ambiguous references require recovery. |
| Design verification | Native STEP bounds, part count, hole count/diameter/position/cylindrical depth/through state, clearance/interference and now component bounding-box placement. Finite wall samples do not prove a global minimum; placement is not a general assembly mate or orientation solver. |
| Accuracy/tolerances | Applied numerical/meshing targets; achieved kernel tolerances, volume approximation and two-resolution mesh measurements. No global surface-deviation or manufacturing-accuracy guarantee is claimed. TPMS remains sampled mesh geometry. |

Test evidence is under `outputs/ask-ai-audit/`: real browser question/edit workflow, isolated engine tests, scoped MCP tests, cancellation/failure tests, viewer regression, installed-tool audit and installation hashes. Earlier 0.10/0.9 evidence remains historical.

Official integration references: [OpenAI local non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) documents saved sign-in, machine-readable events and execution controls. [Plugin UI messaging](https://developers.openai.com/plugins/build/chatgpt-ui) documents messaging from hosted MCP Apps; the standalone loopback viewer uses the separate local-task route described above.

## Final results

Installed version 0.11.0: 104 full-suite tests and 11 focused task tests passed (108 distinct tests). All 33 installed MCP tools and 7 existing viewer groups passed. A real browser using the installed runtime completed both a selected-geometry question with unchanged revision and a 6-to-8 mm hole edit with preserved constrained history, STEP verification and automatic refresh. No browser errors were recorded. Installation hashes match 37 runtime files and six Linux/Windows plugin source/cache copies.

The initial source-run trial exposed an MCP subprocess import-path issue; the task launcher was fixed to supply its actual runtime module path, and the complete workflow was repeated successfully using the installed runtime. The Windows desktop GUI was not automated.
