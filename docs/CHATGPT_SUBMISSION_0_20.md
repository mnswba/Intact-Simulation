# Submitting Intact Simulation 0.20.0

## Current package: local runtime loader

Use **Intact-Simulation-0.20.0-Windows-Local.zip**, not the earlier Submission, Connector or Offline-Runtime archives. It contains the Intact wheel, skills and pinned Windows uv launcher. Like the installed Text-to-CAD plugin (`uvx --from cadgen==0.7.10`), it installs version-pinned runtime dependencies on each user's own computer and runs a local MCP background process. No publisher-hosted CAD server, hosting account or separately provided computer is needed. The Intact wheel is included in the ZIP, so a separately published Intact PyPI package is not required.

The ZIP is 15,755,028 bytes, 33,116,367 bytes extracted and 25 entries. It passes the 100 MiB compressed, 512 MiB extracted, 100 MiB member and 5,000-entry checks. Runtime downloads are declared in the listing, skill and README; they are not lifecycle hooks. First startup requires internet access, local disk space and time for setup. The managed uv environment was tested: all 65 tools, native CAD generation, independent STEP verification and a bottom-view snapshot passed.

This replaces the manual separate-engine proposal below. Desktop-only organization eligibility, verified publisher identity and OpenAI review remain required. Technical packaging and runtime checks do not constitute public-directory approval. Do not deploy a hosted CAD backend for this product: the chosen design processes CAD on each user's Windows laptop.

Checked against official OpenAI documentation on 13 November 2026. Product: **Intact Simulation**, package `intact-simulation`, version **0.20.0**, native Windows x86-64 desktop. The screenshot shows an uploaded 0.16.1 draft marked **Needs attention / Not published**. An uploaded draft is not review approval.

## Historical upload-limit correction

The original full-engine ZIP was rejected at 1,416,915,420 bytes. It also exceeds the documented 512 MiB extracted-size, 5,000-entry and 100 MiB-per-entry limits. It has been renamed **Intact-Simulation-0.20.0-Windows-Offline-Runtime.zip** and must not be uploaded to the portal. Stronger compression or splitting files does not resolve the extracted-size/entry limits.

The earlier Windows-Connector ZIP used a manual engine prerequisite. That proposal is superseded by Windows-Local.zip, which includes the Intact server wheel and installs its pinned dependencies automatically at first use. Use only Windows-Local.zip for this submission.

## Package changes

The ZIP root contains `plugin.json`, `mcp.json`, `skills/intact-cad/SKILL.md`, assets, licenses, the Intact server wheel and a pinned Windows uv launcher. It includes no plugin lifecycle hooks or app references. The skill is at the portable discovery path. The stdio entry point uses `${PLUGIN_ROOT}` and uv-managed Python; it does not invoke WSL or depend on a developer checkout.

The listing supplies the website, support, privacy and Terms URLs. The publisher approved Abdul Samad as provider, and the approved Terms were published on 13 November 2026 at [Terms of Service](https://www.intactsimulation.com/terms-of-service/). Public HTTP 200, effective date, provider and all eight sections were checked. The approved source is [website/content/terms-of-service.html](../website/content/terms-of-service.html); the superseded draft was removed.

## Remaining portal finding

The latest 0.20.0 screenshot reports: **Command MCP Server detected** and directs the publisher to contact an OpenAI representative for command-line MCP submissions. This is the active blocker. Request desktop-only/local-MCP submission access for the existing organization and Intact plugin. Do not switch to hosted CAD: the chosen product runs on each user's Windows laptop. Wait for the skill scan to complete and resolve remaining review requirements before submission.

The corrected local ZIP uses `./bin/uv.exe`, validated through the actual desktop app-server. Reupload the corrected ZIP if the draft was uploaded before this launcher fix. The installed local build is `0.20.0+local.1`; its CAD runtime reports 0.20.0.

The screenshot says **“We are not accepting more skills-only submissions at this time.”** A package cannot grant account eligibility. Current official local-MCP instructions require approved-partner access, organization allowlisting and verified publisher identity. Confirm eligibility with OpenAI using the organization ID and existing plugin/draft ID. No representative has been contacted by these scripts.

Intact uses the desktop-only local MCP route. Do not declare a fabricated HTTPS endpoint or choose a hosted route without deploying a real service. Adding MCP to an existing skills-only plugin is not currently supported; ask OpenAI whether this earlier draft can be corrected or requires a new approved local-MCP draft.

## Upload steps

1. Check all four listing URLs publicly. The Terms approval and publication step is complete.
2. Confirm publisher verification and local-MCP submission eligibility with OpenAI.
3. In the existing Intact plugin, use **Upload new version** if OpenAI confirms its local-MCP type. Otherwise follow their instructions for a new approved local-MCP draft.
4. Upload **Intact-Simulation-0.20.0-Windows-Local.zip** for the desktop-only local-MCP route. Check **0.20.0**, **intact-cad**, all four listing URLs and the local MCP configuration. The launcher installs the runtime on the user's own Windows computer. Do not upload the earlier large or manual-connector archives.
5. Complete scans, review material and attestations. Submit when blocking findings are resolved; publish after approval.

The selected verified publisher identity determines directory attribution. A manifest product label does not verify a person or company.

## Runtime and validation

First startup installs Python 3.12.16, pinned CAD/numerical dependencies, FreeCAD 1.1.4, Chromium headless rendering and, when needed, the official OpenAI client 0.167.2. The package contains the Intact wheel and uv launcher; these larger runtime components are downloaded onto the user's laptop. Workers use AppContainer and Job Object limits. Projects and sign-in profiles stay outside the ZIP. Viewer Ask AI can run a separate scoped local task using the user's sign-in; it does not join the open ChatGPT conversation.

Built-in TPMS, CAD exports and bounded numerical studies are included. Optional Linux PicoGK and GNU LibreDWG are not bundled; DXF remains available. On this laptop, 43 previous WSL model records were copied into the Windows library with IDs and revisions preserved; the original library remains intact. Native macOS/web/mobile execution is unsupported.

Tests on this host do not establish clean-account installation, directory approval or physical certification. See [verification](QA_0_20.md) and the ZIP receipt for measured checks and limits.

## Official references

- [Desktop-only local MCP submission](https://developers.openai.com/plugins/deploy/desktop-only)
- [Package structure and skill discovery](https://developers.openai.com/plugins/build/plugins)
- [Submission requirements and updates](https://developers.openai.com/plugins/deploy/submission)
- [Finding reference](https://developers.openai.com/plugins/deploy/submission-errors)
