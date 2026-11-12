# Intact Simulation 0.16.0

Ask AI now starts work without opening Annotation. The viewer first persists selected geometry, references and the description. A supported ChatGPT component bridge receives the saved request when available; otherwise the signed-in local OpenAI client starts a separate model-scoped task automatically. Bridge failures remain retryable without starting a duplicate task. The localhost fallback does not insert messages into the current ChatGPT conversation. Live current-chat delivery in Windows ChatGPT was not verified; no connected document-control session was available.

Mechanical Analysis now has one **Ask AI** button. It configures and runs the study once physical inputs are sufficient, rather than only preparing it for another button. It asks for missing material/support/load scope, preserves CAD and reports actual solver results. Deflection requests cannot be configured as thermal or flow studies. Top-down loading uses native CAD Z, with total force expressed in N. The solver still supports one native solid; whole-assembly contact is not implemented.

Prepared studies, running/failed jobs and automatic result overlays now match the current user description. Editing that description clears unrelated results. Both asynchronous jobs and direct 3D solver reports can refresh the viewer. The visible Simulation panel shows AI progress, errors, replies and cancellation. A prepared study or answer without solver evidence is not marked as a successful analysis; failed or nonconverged studies require review.

The viewer header now uses the authored blue Intact cube/letter-I logo. The same SVG is included in portable plugin metadata. Current help, skill instructions and privacy/data-flow documentation describe the automatic request behavior.

## Verification

- **37 JavaScript tests passed**, including persistence-before-send, supported host bridge dispatch, annotation-only browser fallback and prevention of duplicate execution on errors.
- **34 distinct targeted backend tests passed** across simulation, automatic meshing, Ask AI permissions/cancellation, revision-bound conversations and optional PicoGK. This includes the new structural-intent and evidence-based-completion regressions.
- **Live signed-in local AI → numerical solver → viewer** tested on a disposable 10 × 10 × 20 mm native solid: E=10 GPa, nu=0, fixed bottom, total 1000 N downward on top. Computed deflection **0.020000000000000122 mm**, peak element-average von Mises stress **10 MPa**, Z reaction **999.9999999999994 N**. Final mesh: **208 nodes / 588 tetrahedra**, residual approximately **1.02e-14**, force-balance error approximately **6.47e-16**. Displacement and stress refinement passed; native CAD and revision remained unchanged.
- The result agrees with the independent compression solution `u=FL/(EA)`: 100 mm² area, 20 mm height, 1000 N and 10 GPa give 0.020 mm. This benchmark verifies load/sign/units, not the deflection of the user's vehicle.
- A separate softer E=1 GPa live case produced 0.200 mm and correctly required review at the small-strain acceptance boundary. Acceptance criteria were not relaxed.
- A regression with an initially excessive 0.1 mm mesh request recovered through automatic sizing within the existing 18,000-cell / 6,000-node budget while preserving geometry.
- Source and installed-runtime Chromium transport audits passed: selected context, direct bridge contract, clarification reply, retry using the existing request ID, 4000-character description, automatic local fallback and historical read-only controls. Host bridge behavior was mocked; the separate local-client analysis above was real.
- Installed stdio MCP client confirmed **version 0.16.0 / 57 tools** and ran the same real 1000 N structural study with verified convergence.
- Vehicle browser regression passed part/body selection gestures, fullscreen presentation/orbit, named-part driving, pause/scrub/replay and exact restoration. The existing render loop and native export coordinates remain unchanged.

Private browser evidence and solver outputs are retained locally under ignored `outputs/ask-ai-016`; user projects, credentials and CAD binaries are not included in this release.

## Publishing

Follow the [complete ChatGPT launch procedure](CHATGPT_LAUNCH.md). The repository includes logo assets and [eight proposed reviewer scenarios](launch-review-cases.json). Public directory approval has not been requested or granted. Desktop-only submissions currently require OpenAI partner approval/organization allowlisting. Publisher verification, working product/support/privacy/terms pages, a packaged runtime with dependencies and a clean-machine desktop test remain release-to-public prerequisites. The source archive is not a self-contained public plugin distribution.
