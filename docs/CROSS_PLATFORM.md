# Cross-platform and browser preparation

The working Windows 0.20.0 package and its published checksum are unchanged. The separately developed [Browser CAD preview 0.1.0](../browser-cad/README.md) is now [available on the existing website](https://www.intactsimulation.com/browser-cad/). It supports a smaller mesh-modeling subset with manual ChatGPT recipe exchange. It is not native macOS support or browser-only full-tool parity.

## Product requirement

The requested audience includes Windows, macOS, Linux, phones, tablets and browser-only ChatGPT use. The publisher will not supply a CAD computation server. A ChatGPT login provides access to the AI service; it does not install or execute Intact's native CAD engines on every device.

The current [65 tools](TOOLS.md) combine Python CAD programs, OpenCASCADE native solids, FreeCAD sketch/feature rebuilds, native export checks, meshing, numerical studies, files and a local viewer. Browser viewing and native CAD execution are separate responsibilities.

## Evidence collected

| Target | Preparation check | What remains unverified |
| --- | --- | --- |
| Windows x86-64 | Existing native 0.20.0 runtime, FreeCAD, CAD and tool discovery were exercised; user confirmed the installation works. | Fresh-account coverage and the documented Windows SDK viewer shutdown limitation. |
| Linux x86-64 | Source route uses bubblewrap. Python 3.12 CAD dependency resolution with prebuilt wheels passed on 13 November 2026. | A new portable first-use package and its clean-install regression matrix. |
| macOS Apple Silicon | Python 3.12 CAD dependency resolution with prebuilt wheels passed. Official FreeCAD 1.1.4 arm64 DMG is available. | Native worker isolation, paths, FreeCAD bridge, packaging/signing, UI integration and real Mac execution. |
| macOS Intel | Python 3.12 CAD dependency resolution with prebuilt wheels passed. Official FreeCAD 1.1.4 x86-64 DMG is available. | The same native implementation and execution checks as Apple Silicon. |
| Phone/tablet/browser | Browser CAD 0.1.0 builds new primitive/Boolean meshes on-device. Live Chromium desktop and phone/tablet viewport checks passed, including STL and recipe round-trip. | Real iOS/Android hardware and Safari validation; native STEP, FreeCAD and full 65-tool parity are not implemented. |

Dependency checks used `uv pip compile backend/pyproject.toml --extra cad --python-version 3.12 --python-platform TARGET --no-build` for `x86_64-unknown-linux-gnu`, `aarch64-apple-darwin` and `x86_64-apple-darwin`. Resolver success means packages can be selected; it is not a CAD, solver, sandbox or installation test.

FreeCAD asset availability was checked through the official 1.1.4 release metadata: `FreeCAD_1.1.4-macOS-arm64-py311.dmg` and `FreeCAD_1.1.4-macOS-x86_64-py311.dmg`. Neither was installed or tested on a Mac in this preparation turn.

## Execution designs that preserve no publisher-hosted CAD compute

### Browser edition

Run a suitable WebAssembly CAD engine in the user's browser and use the existing website hosting for static assets. This is a new edition with its own supported-operation list and device/memory limits. Python/FreeCAD/Gmsh tools do not become browser-compatible by changing the plugin manifest.

Start with explicit, validated geometry instructions and a deliberately bounded set of operations. Investigate browser workers, kernel licensing, STEP generation, mobile memory behavior, origin isolation and export verification before promising any operation. Direct ChatGPT tool integration still needs a supported host/connection design; signing in alone does not allow ChatGPT to call arbitrary JavaScript in another browser tab. Do not claim the existing website's prebuilt examples perform new CAD generation.

### Mobile/browser access to a user's own computer

Keep native CAD computation on the user's supported, online computer and add an authenticated private connection from supported ChatGPT surfaces. No publisher CAD machine is required, but the user must provide and keep their own compute host online.

OpenAI's Secure MCP Tunnel documents private MCP connections, including local stdio servers. It requires tunnel setup, a runtime API key and the relevant Platform/workspace permissions. It is not a public plugin distribution route or a guarantee of availability on every account/device. Desktop-only local plugins themselves cannot be installed in ordinary mobile/browser-only sessions.

A tunnel is also not sufficient by itself for the current viewer/download workflow: localhost URLs on the host computer are not reachable from a phone. An authenticated viewer/artifact transport and data-size handling must be designed and tested. Do not expose the existing private-token localhost viewer as a public multi-user server or weaken worker isolation.

## Selected route and implementation

The user selected **browser-only CAD, accepting a smaller feature set and existing website hosting**. Browser CAD 0.1.0 implements a bounded data-only JSON recipe interpreter over Manifold WASM, a Three.js touch viewer, measured reports and STL/recipe export. The existing WordPress page embeds the self-contained app in an opaque-origin sandboxed iframe; computation runs in a cancelable browser worker. No user Python/JavaScript is evaluated. No publisher CAD compute, runtime API key, private tunnel or user-hosted desktop computer is required for this preview.

ChatGPT interaction is manual copy/paste of modeling instructions, JSON recipes and reports. A ChatGPT login does not automatically connect tools to this browser tab. Direct public ChatGPT tool integration is not implemented or approved. All current Windows tools, models, revisions and the published 0.20.0 artifact remain intact. The alternate private-computer route above is background research, not a requirement introduced into the chosen edition.

## References

- [OpenAI desktop-only plugins](https://developers.openai.com/plugins/deploy/desktop-only)
- [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels/)
- [Apple App Sandbox](https://developer.apple.com/documentation/security/app-sandbox)
- [Official FreeCAD 1.1.4 release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4)
- [Current release verification](QA_0_20.md)
