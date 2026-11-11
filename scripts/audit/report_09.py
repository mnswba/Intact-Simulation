"""Summarize completed release evidence without conflating fixtures and live AI tests."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/0.9-audit'
def read(name):return json.loads((OUT/name).read_text())
models=read('models-report.json');renders=read('renders-report.json');tools=read('tools-report.json');viewer=read('viewer-report.json');controls=read('viewer-controls-report.json');host=read('host/report.json');install=read('installation-report.json')
assert models['passed']==200 and models['failed']==0 and all(c.get('validation_version')==2 for c in models['cases'].values())
assert renders['passed']==200 and not renders['browser_errors']
assert tools['tool_count']==21 and tools['status']=='passed'
assert viewer['status']=='passed' and not viewer['browser_errors']
assert not controls['failures'] and not controls['browser_errors']
assert host['exit_code']==0 and host['independent_phone_checks']['speaker_cylindrical_faces']==8
assert install['status']=='passed' and not install['litellm_installed']
suite=ET.parse(OUT/'backend-tests.xml').getroot().find('testsuite');assert suite is not None and not any(int(suite.get(k,0)) for k in ('errors','failures','skipped'))
count=int(suite.get('tests'))
summary={'version':'0.9.0','date':'2026-11-10','authored_configurations_passed':200,'native_families':50,'tpms_configurations':144,'additional_assemblies':6,'actual_rendered_models':200,'installed_mcp_tools_passed':21,'backend_tests_passed':count,'website_tests_passed':26,'typescript':'passed','live_conversation_generated_models':['phone exterior','gyroid sheet lattice'],'chatgpt_windows_gui':'not directly controlled','foundation_model_training':False,'external_model_service':False,'litellm_installed':False}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
text=f'''# Intact Simulation 0.9 · release audit

10 November 2026 · private local installation on this computer

**200/200 authored configurations, 200/200 actual viewer renders, 21/21 installed MCP tools and {count} backend tests passed.** All 26 website tests and the TypeScript check passed. A fresh OpenAI local client loaded the installed personal plugin and generated a phone exterior and a gyroid lattice from natural-language requests, then validated, previewed and exported them.

## Changes requested

1. **ChatGPT-only AI.** Removed LiteLLM, the provider transport, model-connection settings and autonomous inference jobs from current runtime code/dependencies. The conversation model calls Intact's local CAD tools. No second provider account or API key is used. Standalone viewer Ask AI saves selected geometry, measurements, drawings and images, then copies a prompt to send in ChatGPT. It does not silently submit messages to the desktop conversation. Successful tool application refreshes the viewer.
2. **History preview.** Clicking a revision opens its own geometry read-only without changing the saved model or history. Restore is a separate action. Restoring current/identical content is a no-op. Cache repairs/migrations no longer count as design revisions. Historical downloads refer to historical geometry; mutation requests in historical mode are rejected. Geometry-bound requests become stale when their artifact changes, even if revision stays fixed.
3. **Design verification.** Added `validate_model` to reopen actual STEP/STL, check labels/solid counts/volume/area/checksums and compare requested per-part bounds/IDs. Native curved-face facts expose radii, axes and centers for hole checks. Native meshes and exact curved CAD have different volumes; mixed TPMS/native assemblies are compared with their sampled export geometry instead of falsely requiring exact B-rep volume from a triangle file.
4. **Expanded modeling.** Added six implicit TPMS families and increased bounded part/source/parameter/mesh budgets. Updated the modeling skill and 200-example evaluation corpus. These are tool/instruction/regression improvements, **not foundation-model training**.

Further fixes found by the audit: clipping-plane/sample alignment and near-zero mesh edges could create nonmanifold lattice boundaries; corrected grid placement and bounded field regularization prevent these failures. Reused/located native shapes could lose distinct STEP labels; exported occurrences now have independent identities. Mesh GLB output now follows meter/Y-up conventions while STL/3MF stay CAD XYZ millimeters. Initial colors should be set in source to avoid a separate appearance revision for every component.

## What the counts mean

The 200 configurations comprise 50 native CAD families, 144 combinations of six TPMS families × two modes × three envelopes × four parameter sets, and six assemblies. Additional assemblies include a 23-part phone exterior fixture, 128-component locator array, 65-part bolted panel, indexing transmission concept and two mixed lattice/native assemblies. Fixtures are authored regression examples, not 200 AI-generated designs or 200 distinct design families.

Every configuration ran in the isolated geometry worker, passed reopened-export checks and produced actual exported artifacts. Native analytic volumes were independently compared where provided. Lattice STL, GLB and 3MF were reopened and checked for closed positive volume; GLB volumes were converted from cubic meters for comparison. All 200 viewer renders checked actual camera direction, all component bounding-box corners inside the viewport, and browser errors. The local gallery is `outputs/0.9-audit/gallery.html`.

The separate live-client phone used 22 named parts. Its exported frame measures 71.5 × 147 × 7.8 mm (CAD XYZ is 71.5 × 7.8 × 147 because the model stands upright). Eight native cylindrical speaker faces have diameter 1.2 mm. Actual front, back and bottom snapshots were reviewed. The model is a conceptual exterior with stated assumptions, not a commercial phone's internal construction. The live gyroid uses 20 mm bounds, 8 mm cells, band 0.4 and 20 samples/cell; its mesh export and actual isometric snapshot passed. See `outputs/0.9-audit/host/gallery.html` for these two live generated examples.

## Tool and viewer checks

All 21 tools passed success cases, with expected-failure checks for invalid arguments, paths, revisions, imports, failed CAD, unsupported exports and stale references. Modern and legacy MCP connection modes passed. The suite exercised all six native export formats and the five appropriate mesh/project formats, physical saved colors, executable Python, imported STEP/project round trips, geometry/image edit handoffs, cancellation preserving geometry and both reduced reference solvers.

Browser checks passed the four themes; render/surface/color/projection modes; grid, axes, lights, quality, palettes, floor/background and saved preferences; section/cap/reverse, explosion, assembly filtering/isolation/visibility; sketch primitives, pan/drag restoration, undo/redo, PNG/clipboard; snapped dimensions and annotated exports; retry after transient load failure; mobile layout; immutable history browsing; explicit/duplicate restore; and ChatGPT request application with automatic refresh.

## Current limits and comparison

Limits: 128 named parts, 150 numeric parameters, 120 KB source, 1.2 million preview triangles, worker CPU 100 seconds/wall 120 seconds/address space 4 GiB, artifact 64 MiB. TPMS sampling is bounded at 2.5 million points with 12–64 samples/cell. Resource limits and filesystem/network isolation remain active.

TPMS results are sampled nodal approximations. Band is dimensionless and does **not** specify a constant mm wall thickness. Area, volume and relative density are mesh estimates. STEP is unavailable when an assembly contains implicit mesh geometry; STL/GLB/3MF and standalone Python are provided. No general 3D FEA, CFD, optimization, manufacturing certification, mate solver or recovered feature history is claimed. High-resolution convergence and application-specific checks are needed for engineering use.

The supplied iPhone log's extra commands largely diagnosed missing packages, stalled dependency tracking and restricted networking. Its useful evidence was saved STEP validation and front/rear visual review. Command count does not rank model quality. [The capability comparison](AI_CAD_COMPARISON.md) documents text-to-CAD, Zoo, CadQuery and nTop, including gaps where Intact has fewer integrations. There is no defensible claim that these tests establish universal superiority.

## Installation evidence and desktop boundary

The Windows and WSL personal plugin copies and their active caches are 0.9.0; runtime files were checked against source hashes, all 21 tools are discoverable, and LiteLLM is absent from the installed environment. Existing unrelated plugins, ChatGPT authentication and original user designs are preserved. A live OpenAI local-client test used the actual personal plugin loader and no shell or secondary model-service tools for generation.

**The Windows ChatGPT GUI was not directly controlled in this executor.** Restart ChatGPT desktop and start a new conversation with Intact enabled to load updated tools/instructions. The app's current conversation/model provides reasoning; no fine-tuning, public directory submission or website publication was performed.

## Reproduce

Use the installed runtime Python with `scripts/audit/release_09.py`, `gallery_09.py`, `tools_09.py`, `viewer_09.py`, `viewer_controls_09.py` and `host_09.py`. Geometry fixtures run in isolated workers; the live host test uses the signed-in account's normal model usage. Run the backend suite with pytest dev dependencies installed, and `node --experimental-strip-types --test tests/*.test.ts` for the website tests. Evidence JSON, JUnit XML, real screenshots, CAD files and editable Python are in `outputs/0.9-audit/`.

Official references: [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins), [MCP surfaces](https://learn.chatgpt.com/docs/extend/mcp), [TPMS equations](https://support.ntop.com/hc/en-us/articles/360053267814-What-equations-are-used-to-create-the-TPMS-types), [glTF units](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#coordinate-system-and-units).
'''
(OUT/'AI_CAD_COMPARISON.md').write_text((REPO/'docs/AI_CAD_COMPARISON.md').read_text());(OUT/'AUDIT_REPORT.md').write_text(text);(REPO/'docs/RELEASE_0_9_AUDIT.md').write_text(text)
print(json.dumps(summary,indent=2))
