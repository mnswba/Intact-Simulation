# Intact Simulation 0.8 · 50-model audit

10 November 2026 · Asia/Taipei · private local desktop installation

**50/50 CAD model families, 50/50 live AI edits, 50/50 post-fix release checks and 19/19 MCP tools passed.** The models also passed camera-framing checks and produced actual viewer PNGs. The fresh OpenAI local client loaded the installed plugin and created, repaired, previewed and exported a flange through its MCP tools.

## What was tested

The baseline designs were authored as explicit CAD regression fixtures and built through the installed plugin manifest. Each then received a separate natural-language edit through the real viewer Run API and connected LiteLLM/Codex model. They are 50 different design families with before/after versions; they are not presented as 50 designs generated from an empty prompt. A separate fresh-client test created a flange directly from the user's natural-language dimensions.

Every baseline passed OpenCASCADE validity, positive solid/volume measurements, native topology and mesh-index checks, six exports, STEP solid/volume/surface round trips and an actual MCP image snapshot. Analytic volumes were independently checked where a closed formula was supplied.

Every live AI result passed its requested public-parameter changes and preserved named parts, native volumes, surface areas and bounds against an independently rebuilt intended-edit fixture. The post-fix 0.8 audit preserved the AI source and additionally matched native face types, areas, centers and radii against that intended geometry. This checks hole positions and unchanged features as well as total size or volume.

All 50 release models exported STEP, STL, GLB, 3MF, executable Python and project JSON again. Artifact hashes were checked. Camera tests verified true isometric direction and that every assembly bounding-box corner fitted inside the viewport. Isometric, front, back, top, bottom, right, left and current snapshots were exercised.

The private gallery is `outputs/50-model-audit/gallery.html`; five review sheets cover every before/after pair. Each view is fitted independently, and dimensional comparisons use native CAD measurements.

## Fixed issues

| Issue observed | Resulting behavior |
| --- | --- |
| Linux portable MCP configuration used an absolute executable path rejected by the OpenAI plugin loader | Portable command is a contained `./server/launch.sh`; the installer prepares the durable runtime. Windows keeps a supported bare `wsl.exe` launcher. |
| A zero expected revision could bypass a stale-edit check; booleans could be interpreted as revisions | Positive strict integer revisions are enforced. |
| Invalid view settings in an imported project could leave an extra saved document | Import validates the complete project before its first commit. |
| Disabled component flags were lost on project import | Saved disabled flags, colors, labels, material and preferences survive validated rebuilds. |
| Present-but-damaged cache files could be reused | Output checksums and imported STEP checksums detect corruption and trigger repair or an actionable reimport error. |
| Restoring a revision with missing artifacts could leave an unusable preview | Restoration recreates its real CAD exports before committing. |
| Downloaded Python lost dictionary part names in its exported STEP | Executable exports retain stable part IDs; solid/list/builder outputs follow the same naming convention. |
| Saved viewer colors were absent from STEP exports | STEP/GLB/3MF and downloaded Python retain saved part colors. Display changes do not alter native geometry references. |
| Closing the sketch Pan tool left normal drag mapped to pan | Closing drawing mode restores orbit controls. |
| A transient mesh fetch failure could leave the viewer stuck | Viewer initialization and refresh retry incomplete loads. |
| Dimension IDs containing quotes could break selectors; measured intent was missing from edit context and PNGs | Identifiers are escaped, measured endpoints/provenance accompany edits, and annotated PNGs include dimension labels. |
| Forced clicks on hidden view buttons could select the view cube instead | Snapshots activate the intended button and check the actual camera direction. |
| Tall previews had inadequate framing clearance | Camera fit uses projected bounding-box corners with margin, including orthographic views and exact-axis cube selections. |
| The fresh-client model initially used a friendly label as a part ID | Tool descriptions and verified instructions explicitly show the lowercase ID contract and examples; actual tool errors remain repairable. |
| Generic template defaults could look like measured custom-model features | Measurement tools report actual geometric bounds and identify editable program parameters separately. |
| Windows drive paths were interpreted as Linux relative paths | STEP and project imports map Windows drive paths to the mounted WSL drive, including names with spaces. |

## Tools and UI coverage

All 19 installed MCP tools succeeded: status, list_models, get_model, build_model, update_parameters, set_appearance, revisions, restore_revision, open_viewer, measure_model, snapshot_model, export_model, import_project, import_cad, resolve_references, list_edit_requests, read_edit_request, apply_edit_request and analyze_reference.

Expected-failure checks covered invalid arguments, malformed IDs, stale/zero/boolean revisions, invalid colors, invalid imports, failed CAD, repeated edit application, unsupported or unapproved analysis and cancellation. Modern discovery and legacy MCP initialization both passed; viewer URLs survived tool reconnections.

Browser checks covered four neutral themes; all render/surface/color/projection modes; opacity, edge controls, grid/axes, lighting, exposure, fill, softbox, floor/background, quality and orbit; palette add/remove; saved settings; X/Y/Z sections/caps/reverse; explosion; tree filtering/visibility/isolation; view controls; every sketch primitive, move/erase, undo/redo/clear, widths/colors and clipboard/PNG; quoted dimension IDs, edit measurement context, annotated exports and deletion; transient-load recovery and mobile layout.

Separate live direct-Run tests added four mounting holes, verified independent removed volume, reloaded during inference, confirmed automatic refresh and cancelled another edit without changing the saved revision.

## ChatGPT installation and training scope

The installed Windows and WSL personal plugin copies are 0.8.0. The fresh OpenAI local-client test used the actual personal marketplace and plugin configuration. It successfully called the Intact build, viewer, snapshot and export tools. Windows binary interop/UI control is unavailable in this executor, so the installed ChatGPT desktop GUI was **not directly controlled or visually verified**. Restart ChatGPT desktop and start a new conversation with Intact enabled to load the updated tools and skill.

The skill now has concise workflow instructions, declared MCP dependency and verified modeling/editing/analysis references. The 50-case evaluation corpus is `evals/intact-cad-50.jsonl`; routing and unsupported-scope cases are in `evals/intact-cad-routing.json`. These improve plugin guidance and regression coverage. **No foundation-model fine-tuning job or model-weight training was performed.**

The plugin remains a private local desktop installation. General 3D FEA, CFD, multiphysics, engineering certification and arbitrary format/printer integrations are outside its implemented scope. Beam and fin tools create matching reduced 1D reference models and report their assumptions and numerical checks; they do not simulate arbitrary tested CAD assemblies.

Official references: [portable plugin packaging and desktop refresh](https://developers.openai.com/plugins/build/plugins), [complete plugin evaluation](https://developers.openai.com/plugins/deploy/connect-chatgpt), [skills as reusable instructions](https://developers.openai.com/plugins/concepts/skills).

## Fifty model families

| # | Model | Native CAD | Live AI edit | Fixed-release geometry/exports |
| --- | --- | --- | --- | --- |
| 1 | Four-hole mounting plate | PASS | PASS | PASS |
| 2 | Six-bolt pipe flange | PASS | PASS | PASS |
| 3 | Filleted L bracket | PASS | PASS | PASS |
| 4 | Clevis U bracket | PASS | PASS | PASS |
| 5 | Triangular gusset bracket | PASS | PASS | PASS |
| 6 | Long angle rail | PASS | PASS | PASS |
| 7 | T-section rail | PASS | PASS | PASS |
| 8 | I-section beam | PASS | PASS | PASS |
| 9 | Rectangular hollow tube | PASS | PASS | PASS |
| 10 | Round hollow tube | PASS | PASS | PASS |
| 11 | Revolved stepped shaft | PASS | PASS | PASS |
| 12 | Shaft with keyway | PASS | PASS | PASS |
| 13 | V-groove pulley | PASS | PASS | PASS |
| 14 | Two-groove pulley | PASS | PASS | PASS |
| 15 | Flanged cable spool | PASS | PASS | PASS |
| 16 | Radial-tooth indexing wheel | PASS | PASS | PASS |
| 17 | Conical control knob | PASS | PASS | PASS |
| 18 | Twelve-flute hand knob | PASS | PASS | PASS |
| 19 | Unthreaded hex nut blank | PASS | PASS | PASS |
| 20 | Unthreaded hex-head bolt blank | PASS | PASS | PASS |
| 21 | Socket-head screw blank | PASS | PASS | PASS |
| 22 | Annular washer | PASS | PASS | PASS |
| 23 | Split shaft collar | PASS | PASS | PASS |
| 24 | Ten-part ball bearing concept | PASS | PASS | PASS |
| 25 | Three-part hinge | PASS | PASS | PASS |
| 26 | Two-part electronics enclosure | PASS | PASS | PASS |
| 27 | Parallel-fin heat sink | PASS | PASS | PASS |
| 28 | Radial-fin heat sink | PASS | PASS | PASS |
| 29 | Slotted ventilation panel | PASS | PASS | PASS |
| 30 | Twelve-hole filter disk | PASS | PASS | PASS |
| 31 | Hollow 90-degree pipe elbow | PASS | PASS | PASS |
| 32 | Hollow pipe tee | PASS | PASS | PASS |
| 33 | Conical pipe reducer | PASS | PASS | PASS |
| 34 | Rectangular-to-round transition | PASS | PASS | PASS |
| 35 | Offset tapered duct | PASS | PASS | PASS |
| 36 | Helical compression spring | PASS | PASS | PASS |
| 37 | Coiled hollow tube | PASS | PASS | PASS |
| 38 | Toroidal sealing ring | PASS | PASS | PASS |
| 39 | Ball-ended control handle | PASS | PASS | PASS |
| 40 | Hemispherical cover | PASS | PASS | PASS |
| 41 | Funnel with outlet stem | PASS | PASS | PASS |
| 42 | Two-part dovetail slide | PASS | PASS | PASS |
| 43 | Cantilever snap-fit tab | PASS | PASS | PASS |
| 44 | C-shaped cable clip | PASS | PASS | PASS |
| 45 | Hollow hose barb | PASS | PASS | PASS |
| 46 | Three-part piston concept | PASS | PASS | PASS |
| 47 | Pinned two-link arm concept | PASS | PASS | PASS |
| 48 | Six-blade lofted impeller concept | PASS | PASS | PASS |
| 49 | Cross-drilled manifold block | PASS | PASS | PASS |
| 50 | Engraved identification plate | PASS | PASS | PASS |

## Reproduce

Use the installed runtime Python with `scripts/audit/native.py`, `scripts/audit/ai.py`, `scripts/audit/tools.py`, `scripts/audit/viewer.py`, `scripts/audit/host.py`, `scripts/audit/release.py` and `scripts/audit/renders.py`. The live AI audit uses the connected account and its normal usage limits. Audits use separate local state directories; the realistic fresh-client creation uses the client's normal plugin connection. Keep regression fixtures separate from user designs.

Run `PYTHONPATH=backend <runtime-python> -m pytest backend/tests -q` for the backend regression suite. Validate the plugin skill with the installed skill-creator validator. The scripts save detailed JSON evidence and real exports under `outputs/50-model-audit/` rather than claiming success from model prose.

Final backend regression suite: **59 passed**, no failures or skips. Ten warnings originate in the external LiteLLM/Pydantic integration. Machine-readable results: `outputs/50-model-audit/backend-tests.xml`.
