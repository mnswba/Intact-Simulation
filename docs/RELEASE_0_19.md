# Intact Simulation 0.19.0 — design review and team presentations

The focus is fast visual inspection, useful alternatives and clear engineering discussion.

## Movable Commands

Ctrl/Cmd+K opens a **modeless** window. Drag its header, dock left/right, collapse it or close it while keeping the model interactive. Position persists locally and is clamped on resize. Focus the header and use arrow keys to reposition it (Shift moves faster). It also works inside viewport fullscreen.

## Review

The toolbar’s **Review** button, or **R**, opens a movable summary of the current revision, measured assembly envelope, component count and audit status. Actions submit read-only AI requests to check accuracy, propose three alternatives or prioritize realistic engineering details. Missing dimensions and references should be clarified; suggestions do not automatically change geometry. Evaluate an idea with a parameter preview or configuration before applying it.

This builds on the independently implemented CADCraft/SolidCraft-inspired workflows: searchable commands and schema discovery, saved views, AI display control, noncommitting parameter previews, named numeric configurations and bounded arithmetic expressions. Their Rust kernels and branded UI are not embedded.

## Headless auditor

CAD creation already audits topology, bounded repairs, native exports and saved acceptance checks before publishing a revision. Simulation now runs a geometry audit before solving and a consistent result audit before publishing its report. The audit checks finite coordinates/fields, residuals, conservation, refinement and supported regimes. Invalid numerical output is rejected; unrefined or out-of-regime results stay explicitly unverified/need review. No auditor window or separate hosted AI model is required. Geometry, solver convergence and physical suitability remain distinct claims.

## Professional PPTX

Design slide decks render five views in a separate headless browser at a 2240 × 1260 viewport (3360 × 1890 images at Final quality), without moving the live camera. A pinned CAD revision prevents mixed-revision images. Standard views use the assembled configuration; the first image retains the saved review display.

Decks include a styled cover, large actual model images, clear view captions, measured dimensions, audit status, discussion priorities, optional review notes and a complete paginated component register. Fonts, spacing, colors and slide numbering are consistent. No engineering results or approval claims are invented. Simulation-display exports retain a visual capture and include genuine saved numerical evidence when a matching mechanical report is active. Foreign or stale-geometry reports are rejected; unrefined results remain labelled unverified.

`create_presentation` makes the same headless deck through AI; the installed catalog contains **65 tools**. Project retains PNG, slide deck, BOM and DXF/DWG actions. Project JSON, native FreeCAD and source STEP live under Files & exports.

## Shortcuts

Tutorial → **Keyboard shortcuts** lists the actual shared shortcut registry. Examples: Ctrl/Cmd+K Commands, R Review, F Fit, Shift+F Full screen, G Grid, A Ask AI, M Measure, E Edges, V Parts, I Isolate, H Hide, Shift+H Show all, 1–4 standard views, S Settings, D Draw and ? Tutorial. Plain-letter shortcuts do not run while typing. Tab/Shift+Tab cycles edge candidates; Escape closes the active utility panel before leaving fullscreen.
