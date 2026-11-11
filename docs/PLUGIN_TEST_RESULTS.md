# Intact Simulation plugin validation — 10 November 2026

The installed plugin's core CAD workflow was tested through the official MCP client and a real Chromium browser. This is a local desktop development release, not a claim of complete feature parity with the entire text-to-CAD toolkit.

## Failures found and fixed

- The installed viewer expected model metadata in an export response whose format had changed. It rendered zero canvases. The viewer now reads a separate state endpoint; the portable project export has its own stable contract.
- The handwritten MCP connection did not implement normal negotiation, cancellation or argument validation reliably. The plugin now uses the pinned official MCP SDK and is tested in both modern discovery and legacy initialize modes.
- Expected CAD errors were hidden by the SDK's generic error handler, preventing AI repair. Tool errors now include the actual bounded CAD validation detail.
- Viewer URLs disappeared when the ChatGPT tool process stopped. A persistent loopback viewer now survives normal tool reconnections and reuses its URL after an installation refresh.
- Editing dimensions previously required resending all source code. The plugin and viewer now rebuild saved named parameters, preserve the model name and appearance, reject stale revisions and keep the last successful model on errors/cancellation.
- Earlier edits had no recovery interface. Saved revisions can now be listed and restored as a new revision.
- Colors and view settings were temporary. Per-part colors, visibility, clipping, explosion and camera settings now persist locally.
- Fit used the assembled bounds during explosion. It now fits the visible, displayed geometry.
- An incomplete artifact cache could be reported as a successful build. Missing exports now trigger a rebuild; the old cache is retained in a stale directory until the rebuilt outputs are validated.

## Checks

- **39 backend tests passed**, including real kernel builds, sandbox refusal, numerical reference cases, persistence, API authentication, cancellation and both MCP protocol modes. The changed cache recovery path has an additional targeted real-kernel rerun.
- The installed-plugin audit built a six-hole flange assembly, filleted bracket, revolved pulley, lofted hollow duct and swept hollow elbow. Flange and elbow volumes were compared with independent formulae. STEP, STL, GLB, 3MF, executable Python and project JSON were downloaded and checked. STEP exports are reopened to check topology and volume.
- A real browser exercised actual mesh rendering, capped X/Y/Z cuts and reverse, persisted colors/visibility/explosion, parameter changes, failed-edit preservation, external MCP edits appearing live, revision restoration, PNG download, mobile layout and all five model viewers. It also checked actual thermal field samples and balance/refinement/agreement results.
- The agent's snapshot tool returned real PNG image content through MCP. Saved user camera settings stayed unchanged during those captures. Images were visually reviewed.
- The installed Windows plugin manifest, WSL launch command, personal marketplace entry and enabled setting were inspected. Windows binary execution/UI control is unavailable in this session; activation inside a fresh ChatGPT desktop UI is **not verified**. A new desktop session is required to load changed tools.

Reproducible test code is in `scripts/test-installed-plugin.py`, `scripts/test-plugin-viewer.mjs` and `backend/tests/`. Audit exports, PNGs and the detailed JSON report are kept under `outputs/plugin-audit/` and excluded from Git.

## Current scope

The core workflow supports source-generated solid CAD, assemblies, measurements, parameters, revisions, project import, visualization, six export choices and AI-readable snapshots. Project import rebuilds the CAD program; it does not trust an imported preview mesh.

Direct STL import, engineering drawings, vendor catalogs, robotics formats and printer/service integrations are not implemented here. Simulation covers a new rectangular beam or cooling-fin reference model with reduced 1D methods. General generated-shape 3D FEA, CFD and multiphysics remain unfinished.


## Geometry workflow and neutral themes · 0.6.0

The Windows and WSL personal plugin installations and stable runtime were updated to 0.6.0. The installed manifest exposes native-reference resolution, STEP import, queued edit inspection with real image content and atomic edit application. Source hashes match the installed Python/viewer modules and plugin skill copies.

A separate real-browser/installed-MCP audit of the 23-part iPhone passed native face and edge ray picking, 71.50 mm vertex snapping, grouped assembly navigation, six display modes, settings persistence, arrow sketch undo/redo, image attachments, copied ChatGPT prompt, queued request inspection and rebuilding. It enlarged one speaker bore from 1.3 to 1.8 mm, checked 3.1651545985 mm³ of material removal against the analytic volume, preserved the other 22 components, rejected stale references and refreshed the open viewer. The actual installed snapshot tool returned a PNG.

The original browser audit also passed again for saved colors, all capped cut axes and reversal, persisted explosion/visibility, parameter builds and failure recovery, an external MCP edit, history restoration, PNG export, mobile layout, all five free-form models and the existing thermal result plot. A delayed preference save during rapid reload was fixed with immediate visibility saves and a final preference flush when the page closes.

Light (Default), Medium Light, Medium and Dark are four neutral interface/background themes. All four were rendered in a real browser, their background colors checked, and Light verified after reload. Custom viewport colors remain available. The user's prepared workspace defaults to Light. See `outputs/workflow-audit/` for screenshots and the installed-workflow report.

STEP assemblies now import with stored names and colors; their checksum-addressed source assets survive edits and portable project round trips. The direct LiteLLM edit route was tested with a simulated provider response, including image and geometry delivery. No hosted provider account is configured, so a live hosted response has not been tested. The ChatGPT handoff uses an explicitly copied prompt.


## Direct Run AI and grid control · 0.7.0

The installed Windows/WSL plugin and persistent viewer are updated to 0.7.0. Ask AI now provides a primary Run AI edit button, local connection status, background progress and cancellation. The prior Save/Copy workflow remains in an optional ChatGPT handoff section. The toolbar has a Grid: On/Off button synchronized with Settings, with persistence even in the Grid display preset.

This PC's actual saved Codex ChatGPT sign-in was tested successfully and connected as a custom LiteLLM inference transport. Intact never reads or copies the stored tokens. The inference child disables shell, apps, browser, computer, subagents and hooks; the bounded host agent alone dispatches CAD to the isolated Python worker. A configured hosted LiteLLM model takes precedence. This connection is local to the private PC.

All **44 backend tests pass**, including model-connection metadata permissions, actual LiteLLM custom-provider dispatch, image attachment transport, background cancellation without a revision change and interrupted-job recovery. The SDK emits ten non-failing Pydantic TypedDict qualifier warnings during its first custom-provider schema initialization.

A **live browser/model test against the installed persistent viewer** described four new Ø3 mm mounting holes in a 60 × 30 × 6 mm plate with an existing Ø6 mm center bore. The real model generated and validated CAD; the browser reloaded during inference and then refreshed automatically. OpenCASCADE confirmed four new R1.5 cylindrical faces and the preserved center bore. Removed volume was **169.6460032938 mm³**, matching four cylindrical bores independently. A second live request was cancelled and the saved revision remained unchanged. Grid toolbar/settings synchronization, persistence and the Grid preset also passed. Results and screenshots are in `outputs/direct-ai-audit/`.

The existing installed-viewer regression suite passed again for actual meshes, saved colors, X/Y/Z caps and reversal, visibility/explosion persistence, parameters, failed-edit preservation, external MCP updates, revision restore, PNG, mobile, five model types and thermal-result samples/checks. Installation hashes match the source for the new transport, connection, background jobs, agent and viewer modules, and both platform plugin caches.
