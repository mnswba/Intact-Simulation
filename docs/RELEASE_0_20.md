# Intact Simulation 0.20.0 — Windows submission candidate

**Current distribution:** use the 15.8 MB **Windows-Local** ZIP. It includes the Intact wheel and uv launcher and installs the pinned runtime on each user's laptop at first use. The UV-managed runtime passed a real 65-tool/CAD/STEP/snapshot check. No publisher-hosted CAD backend is required. The superseded large runtime and manual connector upload artifacts have been removed from the local delivery files. See the [current submission guide](CHATGPT_SUBMISSION_0_20.md) for the separate eligibility and review requirements.

This release adds native Windows x86-64 execution. Generated CAD remains isolated in a unique AppContainer with a bounded Job Object. Linux source installations retain bubblewrap isolation. Existing WSL projects are not moved or deleted.

- Review and Ask AI discover the installed OpenAI client on the execution platform and explain missing setup accurately. The Windows distribution includes the official standalone client; users sign in with their own ChatGPT account when needed.
- Reset view sits immediately beside Zoom to fit.
- The floor no longer fills or hides bottom views. Grid lines remain visible; the shadow receiver is transparent and faces upward.
- First startup installs Python 3.12.16, pinned CAD/numerical dependencies, FreeCAD 1.1.4, a headless Chromium runtime and, when needed, the official OpenAI local client 0.167.2. These larger components stay in the user's local runtime cache.
- The ZIP root contains `plugin.json`, `mcp.json`, `skills/intact-cad/SKILL.md`, assets and the server. It excludes lifecycle hooks, app references, developer profiles and private projects.
- Support, privacy and Terms listing URLs point to published product pages. The publisher approved the Terms with Abdul Samad as provider; publication and public access were verified on 13 November 2026. The ZIP's existing Terms URL is correct.

The built-in TPMS engine is included. Optional Linux PicoGK and GNU LibreDWG are not bundled; DXF remains available. Native macOS execution is unsupported. This candidate is not a directory approval or proof that an account is eligible for local MCP submissions.

The portable launcher uses the host-supported contained command `./bin/uv.exe`. The installed local build is identified as `0.20.0+local.1` to refresh the desktop version cache; its CAD runtime reports 0.20.0. The actual desktop loader connected all 65 tools, and the native viewer's Tutorial displayed 0.20.0. A native viewer shortcut avoids reopening an old WSL viewer link. The user confirmed the latest version is working.

See [verification](QA_0_20.md) and [submission steps](CHATGPT_LAUNCH.md).
